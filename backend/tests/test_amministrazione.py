"""Test di valutazioni, gestione delle promozioni e dashboard (RF13, RF18, RF19, RB07)."""
from datetime import date, datetime, timedelta, timezone

import pytest

from app.core.sicurezza import crea_token_accesso
from app.models import Pagamento, Prenotazione, RuoloUtente, Sessione, StatoPrenotazione, Utente
from app.seed import popola
from tests.test_prenotazioni import h, nuova_sessione, nuovo_cliente

API = "/api/v1"


@pytest.fixture
def bottega(db):
    popola(db)
    return db


@pytest.fixture
def token_admin(bottega):
    admin = bottega.query(Utente).filter_by(ruolo=RuoloUtente.admin).one()
    return crea_token_accesso(admin.id, "admin")


def attivita_svolta(db, utente, slug="esperienza-tornio", stato=StatoPrenotazione.confermata):
    """Crea una sessione già conclusa con una prenotazione del cliente."""
    s = nuova_sessione(db, slug, tra_ore=-5)
    p = Prenotazione(utente_id=utente.id, sessione_id=s.id, prezzo_listino_cent=6000, sconto_cent=0,
                     prezzo_finale_cent=6000, stato=stato)
    db.add(p)
    db.commit()
    return s, p


# --- Valutazioni ------------------------------------------------------------------

def test_valutazione_di_un_attivita_svolta(client, bottega):
    utente, token = nuovo_cliente(bottega, "sara@example.com")
    s, p = attivita_svolta(bottega, utente)
    r = client.post(f"{API}/valutazioni", headers=h(token),
                    json={"prenotazione_id": p.id, "voto": 5, "commento": "Bellissima esperienza"})
    assert r.status_code == 201 and r.json()["autore"] == "Sara"

    pubblico = client.get(f"{API}/servizi/{s.servizio_id}/valutazioni").json()
    assert pubblico["numero"] == 1 and pubblico["media"] == 5.0
    assert "email" not in pubblico["valutazioni"][0]  # nessun dato personale esposto


def test_una_sola_valutazione_per_attivita(client, bottega):  # RB07
    utente, token = nuovo_cliente(bottega, "sara@example.com")
    _, p = attivita_svolta(bottega, utente)
    client.post(f"{API}/valutazioni", headers=h(token), json={"prenotazione_id": p.id, "voto": 4})
    r = client.post(f"{API}/valutazioni", headers=h(token), json={"prenotazione_id": p.id, "voto": 1})
    assert r.status_code == 409 and r.json()["codice"] == "GIA_VALUTATA"


def test_non_si_valuta_un_attivita_futura_o_non_pagata(client, bottega):
    utente, token = nuovo_cliente(bottega, "sara@example.com")
    futura = nuova_sessione(bottega, "esperienza-tornio", tra_ore=48)
    p = Prenotazione(utente_id=utente.id, sessione_id=futura.id, prezzo_listino_cent=6000, sconto_cent=0,
                     prezzo_finale_cent=6000, stato=StatoPrenotazione.confermata)
    bottega.add(p)
    bottega.commit()
    assert client.post(f"{API}/valutazioni", headers=h(token),
                       json={"prenotazione_id": p.id, "voto": 5}).json()["codice"] == "NON_VALUTABILE"

    _, non_pagata = attivita_svolta(bottega, utente, slug="esperienza-decorazione", stato=StatoPrenotazione.in_attesa)
    assert client.post(f"{API}/valutazioni", headers=h(token),
                       json={"prenotazione_id": non_pagata.id, "voto": 5}).json()["codice"] == "NON_VALUTABILE"


def test_non_si_valuta_l_attivita_di_un_altro_e_voto_fuori_scala(client, bottega):
    sara, _ = nuovo_cliente(bottega, "sara@example.com")
    _, token_marco = nuovo_cliente(bottega, "marco@example.com")
    _, p = attivita_svolta(bottega, sara)
    assert client.post(f"{API}/valutazioni", headers=h(token_marco),
                       json={"prenotazione_id": p.id, "voto": 5}).status_code == 404
    assert client.post(f"{API}/valutazioni", headers=h(token_marco),
                       json={"prenotazione_id": p.id, "voto": 6}).status_code == 422


# --- Promozioni ---------------------------------------------------------------------

def test_admin_crea_e_disattiva_un_codice(client, bottega, token_admin):
    r = client.post(f"{API}/admin/promozioni", headers=h(token_admin),
                    json={"nome": "Open day", "codice": "openday", "percentuale": 20})
    assert r.status_code == 201 and r.json()["codice"] == "OPENDAY"
    pid = r.json()["id"]

    utente, token = nuovo_cliente(bottega, "anna@example.com")
    s = nuova_sessione(bottega, "esperienza-tornio")
    con_codice = client.post(f"{API}/prenotazioni", headers=h(token),
                             json={"sessione_id": s.id, "codice_promo": "OpenDay"}).json()
    assert con_codice["sconto_cent"] == 1200  # 20% di 60,00 €

    client.patch(f"{API}/admin/promozioni/{pid}", headers=h(token_admin), json={"attiva": False})
    altra = nuova_sessione(bottega, "esperienza-tornio", tra_ore=100)
    r = client.post(f"{API}/prenotazioni", headers=h(token), json={"sessione_id": altra.id, "codice_promo": "OPENDAY"})
    assert r.json()["codice"] == "CODICE_NON_VALIDO"


def test_promozioni_non_valide_rifiutate(client, bottega, token_admin):
    senza_codice = client.post(f"{API}/admin/promozioni", headers=h(token_admin), json={"nome": "X", "percentuale": 10})
    assert senza_codice.status_code == 422
    date_invertite = client.post(f"{API}/admin/promozioni", headers=h(token_admin),
                                 json={"nome": "X", "codice": "XX1", "percentuale": 10,
                                       "valida_dal": "2026-12-10", "valida_al": "2026-12-01"})
    assert date_invertite.status_code == 422
    client.post(f"{API}/admin/promozioni", headers=h(token_admin), json={"nome": "A", "codice": "DOPPIO", "percentuale": 5})
    duplicato = client.post(f"{API}/admin/promozioni", headers=h(token_admin),
                            json={"nome": "B", "codice": "doppio", "percentuale": 5})
    assert duplicato.status_code == 409


def test_promozioni_riservate_all_admin(client, bottega):
    _, token = nuovo_cliente(bottega, "anna@example.com")
    assert client.get(f"{API}/admin/promozioni", headers=h(token)).status_code == 403


# --- Dashboard -----------------------------------------------------------------------

def test_dashboard_calcola_gli_indicatori(client, bottega, token_admin):
    """Scenario controllato: due clienti, una data da 6 posti, due pagamenti e una membership."""
    anna, token_anna = nuovo_cliente(bottega, "anna@example.com")
    luca, token_luca = nuovo_cliente(bottega, "luca@example.com")
    s = nuova_sessione(bottega, "esperienza-tornio", tra_ore=72, capienza=6)
    for token in (token_anna, token_luca):
        pid = client.post(f"{API}/prenotazioni", headers=h(token), json={"sessione_id": s.id}).json()["id"]
        client.post(f"{API}/prenotazioni/{pid}/pagamento", headers=h(token), json={})
    piano = client.get(f"{API}/piani-membership").json()[0]
    acquisto = client.post(f"{API}/acquisti", headers=h(token_anna), json={"piano_id": piano["id"]}).json()
    client.post(f"{API}/acquisti/{acquisto['id']}/pagamento", headers=h(token_anna), json={})

    giorno = s.inizio.astimezone().date()
    oggi = date.today()
    r = client.get(f"{API}/admin/dashboard", headers=h(token_admin),
                   params={"dal": min(oggi, giorno).isoformat(), "al": max(oggi, giorno).isoformat()})
    assert r.status_code == 200
    d = r.json()
    assert d["prenotazioni_confermate"] == 2
    assert d["incassi_cent_per_tipo"]["esperienza"] == 12000
    assert d["incassi_cent_per_tipo"]["membership"] == 12000
    assert d["incassi_totali_cent"] == 24000
    assert d["membership_attive"] == 1
    assert d["nuovi_clienti"] == 2
    assert d["servizi_piu_richiesti"][0] == {"servizio": "Esperienza giornaliera – tornio", "prenotazioni": 2}
    assert 0 < d["tasso_riempimento_medio"] <= 1


def test_dashboard_periodo_non_valido_e_accesso(client, bottega, token_admin):
    r = client.get(f"{API}/admin/dashboard", headers=h(token_admin), params={"dal": "2026-11-30", "al": "2026-11-01"})
    assert r.status_code == 400 and r.json()["codice"] == "PERIODO_NON_VALIDO"
    assert client.get(f"{API}/admin/dashboard").status_code == 401
    predefinita = client.get(f"{API}/admin/dashboard", headers=h(token_admin)).json()
    assert predefinita["al"] == date.today().isoformat()
