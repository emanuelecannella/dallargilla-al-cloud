"""Test del catalogo pubblico e della gestione da parte dell'amministratore (RF02–RF04, RF15–RF17)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.sicurezza import calcola_hash_password, crea_token_accesso
from app.models import Prenotazione, RuoloUtente, Sessione, StatoPrenotazione, Utente
from app.seed import popola


@pytest.fixture
def catalogo(db):
    popola(db)
    return db


@pytest.fixture
def token_admin(catalogo):
    admin = catalogo.query(Utente).filter_by(ruolo=RuoloUtente.admin).one()
    return crea_token_accesso(admin.id, "admin")


def h(token):
    return {"Authorization": f"Bearer {token}"}


def domani():
    return (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)


# --- Catalogo pubblico ------------------------------------------------------------

def test_elenco_servizi_pubblico(client, catalogo):
    risposta = client.get("/api/v1/servizi")
    assert risposta.status_code == 200
    slugs = {s["slug"] for s in risposta.json()}
    assert {"corso-tornio-base", "esperienza-tornio", "coworking"} <= slugs


def test_filtro_per_tipo(client, catalogo):
    corsi = client.get("/api/v1/servizi", params={"tipo": "corso"}).json()
    assert len(corsi) == 3 and all(s["tipo"] == "corso" for s in corsi)


def test_dettaglio_e_slug_inesistente(client, catalogo):
    assert client.get("/api/v1/servizi/corso-tornio-base").json()["prezzo_cent"] == 34000
    risposta = client.get("/api/v1/servizi/non-esiste")
    assert risposta.status_code == 404 and risposta.json()["codice"] == "NON_TROVATO"


def test_sessioni_future_con_posti_residui(client, catalogo):
    tornio = client.get("/api/v1/servizi/esperienza-tornio").json()
    sessioni = client.get(f"/api/v1/servizi/{tornio['id']}/sessioni").json()
    assert len(sessioni) == 8  # due turni al sabato per quattro settimane
    assert all(s["posti_residui"] == 6 for s in sessioni)
    date = [s["inizio"] for s in sessioni]
    assert date == sorted(date)  # dalla più vicina


def test_posti_residui_calano_con_le_prenotazioni(client, catalogo):
    sessione = catalogo.query(Sessione).order_by(Sessione.id).first()
    cliente = Utente(email="c@example.com", password_hash=calcola_hash_password("prova123"),
                     nome="C", cognome="D", data_nascita=datetime(2000, 1, 1).date(), consenso_privacy=True)
    catalogo.add(cliente)
    catalogo.flush()
    catalogo.add(Prenotazione(utente_id=cliente.id, sessione_id=sessione.id, prezzo_listino_cent=6000,
                              sconto_cent=0, prezzo_finale_cent=6000, stato=StatoPrenotazione.confermata))
    catalogo.commit()
    sessioni = client.get(f"/api/v1/servizi/{sessione.servizio_id}/sessioni").json()
    prima = next(s for s in sessioni if s["id"] == sessione.id)
    assert prima["posti_residui"] == sessione.capienza - 1


def test_pacchetto_mostra_il_risparmio(client, catalogo):
    pacchetto = client.get("/api/v1/pacchetti").json()[0]
    assert pacchetto["slug"] == "giornata-in-bottega"
    assert pacchetto["prezzo_cent"] == 8500
    assert pacchetto["prezzo_separato_cent"] == 9500
    assert pacchetto["risparmio_cent"] == 1000


def test_piani_membership(client, catalogo):
    piani = client.get("/api/v1/piani-membership").json()
    assert [p["ingressi"] for p in piani] == [8, 24]


def test_seed_idempotente(db):
    popola(db)
    popola(db)
    assert db.query(Utente).count() == 1
    assert db.query(Sessione).count() == 4 * 5 + 3


# --- Amministrazione ---------------------------------------------------------------

def test_admin_riservato(client, catalogo, token_giulia):
    assert client.get("/api/v1/admin/servizi").status_code == 401
    risposta = client.get("/api/v1/admin/servizi", headers=h(token_giulia))
    assert risposta.status_code == 403 and risposta.json()["codice"] == "PERMESSO_NEGATO"


def test_admin_crea_modifica_disattiva_servizio(client, token_admin):
    nuovo = {"tipo": "esperienza", "nome": "Raku al tramonto", "slug": "raku-al-tramonto",
             "durata_minuti": 180, "prezzo_cent": 9000, "capienza": 5}
    creato = client.post("/api/v1/admin/servizi", headers=h(token_admin), json=nuovo)
    assert creato.status_code == 201
    sid = creato.json()["id"]

    assert client.post("/api/v1/admin/servizi", headers=h(token_admin), json=nuovo).status_code == 409

    modificato = client.patch(f"/api/v1/admin/servizi/{sid}", headers=h(token_admin), json={"prezzo_cent": 9500})
    assert modificato.json()["prezzo_cent"] == 9500

    assert client.delete(f"/api/v1/admin/servizi/{sid}", headers=h(token_admin)).status_code == 204
    assert client.get("/api/v1/servizi/raku-al-tramonto").status_code == 404  # sparisce dal catalogo
    tutti = client.get("/api/v1/admin/servizi", headers=h(token_admin)).json()
    assert any(s["slug"] == "raku-al-tramonto" and not s["attivo"] for s in tutti)  # ma resta nello storico


def test_slug_non_valido(client, token_admin):
    dati = {"tipo": "corso", "nome": "X", "slug": "Con Spazi!", "durata_minuti": 60, "prezzo_cent": 0, "capienza": 2}
    assert client.post("/api/v1/admin/servizi", headers=h(token_admin), json=dati).status_code == 422


def test_admin_pubblica_sessione(client, catalogo, token_admin):
    tornio = client.get("/api/v1/servizi/esperienza-tornio").json()
    inizio = domani()
    risposta = client.post("/api/v1/admin/sessioni", headers=h(token_admin),
                           json={"servizio_id": tornio["id"], "inizio": inizio.isoformat()})
    assert risposta.status_code == 201
    corpo = risposta.json()
    assert corpo["capienza"] == 6 and corpo["posti_residui"] == 6
    durata = datetime.fromisoformat(corpo["fine"]) - datetime.fromisoformat(corpo["inizio"])
    assert durata == timedelta(minutes=120)  # fine ricavata dal servizio


def test_non_si_pubblica_una_data_passata(client, catalogo, token_admin):
    tornio = client.get("/api/v1/servizi/esperienza-tornio").json()
    ieri = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    risposta = client.post("/api/v1/admin/sessioni", headers=h(token_admin),
                           json={"servizio_id": tornio["id"], "inizio": ieri})
    assert risposta.status_code == 400 and risposta.json()["codice"] == "DATA_PASSATA"


def test_annullare_una_sessione_la_toglie_dal_calendario(client, catalogo, token_admin):
    sessione = catalogo.query(Sessione).order_by(Sessione.inizio).first()
    client.patch(f"/api/v1/admin/sessioni/{sessione.id}", headers=h(token_admin), json={"stato": "annullata"})
    ids = [s["id"] for s in client.get(f"/api/v1/servizi/{sessione.servizio_id}/sessioni").json()]
    assert sessione.id not in ids


def test_capienza_non_scende_sotto_i_prenotati_e_iscritti(client, catalogo, token_admin, token_giulia):
    sessione = catalogo.query(Sessione).order_by(Sessione.id).first()
    giulia = catalogo.query(Utente).filter_by(email="giulia.rossi@example.com").one()
    marco = Utente(email="marco@example.com", password_hash=calcola_hash_password("prova123"),
                   nome="Marco", cognome="Bianchi", data_nascita=datetime(1999, 3, 3).date(),
                   consenso_privacy=True)
    catalogo.add(marco)
    catalogo.flush()
    for utente in (giulia, marco):
        catalogo.add(Prenotazione(utente_id=utente.id, sessione_id=sessione.id, prezzo_listino_cent=6000,
                                  sconto_cent=0, prezzo_finale_cent=6000))
    catalogo.commit()

    risposta = client.patch(f"/api/v1/admin/sessioni/{sessione.id}", headers=h(token_admin), json={"capienza": 1})
    assert risposta.status_code == 409 and risposta.json()["codice"] == "CAPIENZA_INSUFFICIENTE"

    iscritti = client.get(f"/api/v1/admin/sessioni/{sessione.id}/iscritti", headers=h(token_admin)).json()
    assert [i["cognome"] for i in iscritti] == ["Bianchi", "Rossi"]  # in ordine alfabetico
