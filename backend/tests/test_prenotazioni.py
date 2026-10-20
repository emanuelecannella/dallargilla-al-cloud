"""Test di prenotazioni, sconti, cancellazioni, acquisti e pagamenti simulati.

Ogni test richiama la regola dei requisiti che verifica (RF = requisito funzionale, RB = regola di business).
"""
import threading
from datetime import date, datetime, timedelta, timezone

import pytest

from app.core.errori import ErroreApplicativo
from app.core.sicurezza import calcola_hash_password, crea_token_accesso
from app.models import (
    Pacchetto, Pagamento, PianoMembership, Prenotazione, Promozione, RegolaPromozione,
    Servizio, Sessione, StatoPrenotazione, TipoServizio, Utente,
)
from app.schemas.transazioni import PrenotazioneCrea
from app.seed import popola
from app.services.transazioni import crea_prenotazione
from tests.conftest import SessioneTest

API = "/api/v1"


def h(token):
    return {"Authorization": f"Bearer {token}"}


def nuovo_cliente(db, email, nascita=date(1990, 6, 1)):
    utente = Utente(email=email, password_hash=calcola_hash_password("prova123"), nome=email.split("@")[0].title(),
                    cognome="Test", data_nascita=nascita, consenso_privacy=True)
    db.add(utente)
    db.commit()
    return utente, crea_token_accesso(utente.id, "cliente")


def nuova_sessione(db, slug, tra_ore=72, capienza=None):
    servizio = db.query(Servizio).filter_by(slug=slug).one()
    inizio = datetime.now(timezone.utc) + timedelta(hours=tra_ore)
    sessione = Sessione(servizio_id=servizio.id, inizio=inizio, fine=inizio + timedelta(hours=2),
                        capienza=capienza or servizio.capienza)
    db.add(sessione)
    db.commit()
    return sessione


@pytest.fixture
def bottega(db):
    popola(db)
    return db


@pytest.fixture
def adulto(bottega):
    return nuovo_cliente(bottega, "anna@example.com", nascita=date(1990, 6, 1))


@pytest.fixture
def giovane(bottega):
    oggi = date.today()
    return nuovo_cliente(bottega, "luca@example.com", nascita=date(oggi.year - 20, 1, 15))


# --- Prenotazione e prezzi -----------------------------------------------------------

def test_prenotazione_prezzo_pieno(client, bottega, adulto):
    s = nuova_sessione(bottega, "esperienza-tornio")
    r = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id})
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["stato"] == "in_attesa"
    assert (corpo["prezzo_listino_cent"], corpo["sconto_cent"], corpo["prezzo_finale_cent"]) == (6000, 0, 6000)


def test_sconto_under26_automatico(client, bottega, giovane):  # RB03
    s = nuova_sessione(bottega, "esperienza-tornio")
    corpo = client.post(f"{API}/prenotazioni", headers=h(giovane[1]), json={"sessione_id": s.id}).json()
    assert corpo["sconto_cent"] == 600 and corpo["prezzo_finale_cent"] == 5400
    assert corpo["promozione"] == "Giovani in bottega"


def test_si_applica_lo_sconto_migliore(client, bottega, giovane):  # RB08
    bottega.add(Promozione(nome="Autunno", codice="AUTUNNO15", regola=RegolaPromozione.codice, percentuale=15))
    bottega.commit()
    s = nuova_sessione(bottega, "corso-tornio-base")
    corpo = client.post(f"{API}/prenotazioni", headers=h(giovane[1]),
                        json={"sessione_id": s.id, "codice_promo": "autunno15"}).json()
    assert corpo["promozione"] == "Autunno"          # 15% batte il 10% Under 26, non si sommano
    assert corpo["sconto_cent"] == 5100              # 15% di 340,00 €


def test_codice_promo_non_valido(client, bottega, adulto):
    s = nuova_sessione(bottega, "esperienza-tornio")
    r = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id, "codice_promo": "FALSO"})
    assert r.status_code == 400 and r.json()["codice"] == "CODICE_NON_VALIDO"


def test_codice_scaduto_non_valido(client, bottega, adulto):
    bottega.add(Promozione(nome="Estate", codice="ESTATE", regola=RegolaPromozione.codice, percentuale=20,
                           valida_al=date.today() - timedelta(days=1)))
    bottega.commit()
    s = nuova_sessione(bottega, "esperienza-tornio")
    r = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id, "codice_promo": "ESTATE"})
    assert r.json()["codice"] == "CODICE_NON_VALIDO"


def test_prenotazione_richiede_login(client, bottega):
    s = nuova_sessione(bottega, "esperienza-tornio")
    assert client.post(f"{API}/prenotazioni", json={"sessione_id": s.id}).status_code == 401


# --- Regole sui posti ------------------------------------------------------------------

def test_doppia_prenotazione_rifiutata(client, bottega, adulto):  # RB02
    s = nuova_sessione(bottega, "esperienza-tornio")
    client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id})
    r = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id})
    assert r.status_code == 409 and r.json()["codice"] == "GIA_PRENOTATO"


def test_posti_esauriti(client, bottega, adulto, giovane):  # RB01
    s = nuova_sessione(bottega, "esperienza-tornio", capienza=1)
    assert client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id}).status_code == 201
    r = client.post(f"{API}/prenotazioni", headers=h(giovane[1]), json={"sessione_id": s.id})
    assert r.status_code == 409 and r.json()["codice"] == "POSTI_ESAURITI"


def test_sessione_passata_non_prenotabile(client, bottega, adulto):
    s = nuova_sessione(bottega, "esperienza-tornio", tra_ore=-3)
    r = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id})
    assert r.json()["codice"] == "SESSIONE_NON_PRENOTABILE"


def test_ultimo_posto_conteso_da_richieste_simultanee(bottega):
    """Dieci clienti provano nello stesso istante a prendere i due posti rimasti.

    Grazie al blocco della riga (SELECT ... FOR UPDATE) le richieste vengono servite una
    alla volta: esattamente due riescono, le altre ricevono "posti esauriti" (RB01, RNF07).
    """
    sessione = nuova_sessione(bottega, "esperienza-tornio", capienza=2)
    clienti = [nuovo_cliente(bottega, f"cliente{i}@example.com")[0].id for i in range(10)]
    partenza = threading.Barrier(len(clienti))
    esiti = []

    def tenta(utente_id):
        db = SessioneTest()
        try:
            utente = db.get(Utente, utente_id)
            partenza.wait()  # tutti i thread partono insieme
            crea_prenotazione(db, utente, PrenotazioneCrea(sessione_id=sessione.id))
            esiti.append("ok")
        except ErroreApplicativo as e:
            db.rollback()
            esiti.append(e.codice)
        finally:
            db.close()

    thread = [threading.Thread(target=tenta, args=(uid,)) for uid in clienti]
    for t in thread:
        t.start()
    for t in thread:
        t.join()

    assert esiti.count("ok") == 2
    assert esiti.count("POSTI_ESAURITI") == 8
    bottega.expire_all()
    assert bottega.query(Prenotazione).filter_by(sessione_id=sessione.id).count() == 2


# --- Cancellazione -------------------------------------------------------------------

def test_cancellazione_entro_48_ore_libera_il_posto(client, bottega, adulto):  # RF12, RB05
    s = nuova_sessione(bottega, "esperienza-tornio", tra_ore=72, capienza=1)
    pid = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id}).json()["id"]
    assert client.delete(f"{API}/prenotazioni/{pid}", headers=h(adulto[1])).status_code == 204
    posti = client.get(f"{API}/servizi/{s.servizio_id}/sessioni").json()
    assert next(x for x in posti if x["id"] == s.id)["posti_residui"] == 1


def test_cancellazione_oltre_il_termine_rifiutata(client, bottega, adulto):  # RB05
    s = nuova_sessione(bottega, "esperienza-tornio", tra_ore=24)
    pid = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id}).json()["id"]
    r = client.delete(f"{API}/prenotazioni/{pid}", headers=h(adulto[1]))
    assert r.status_code == 400 and r.json()["codice"] == "FUORI_TERMINE"


def test_dopo_l_annullamento_si_puo_riprenotare(client, bottega, adulto):
    s = nuova_sessione(bottega, "esperienza-tornio")
    pid = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id}).json()["id"]
    client.delete(f"{API}/prenotazioni/{pid}", headers=h(adulto[1]))
    di_nuovo = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id})
    assert di_nuovo.status_code == 201 and di_nuovo.json()["id"] == pid


def test_non_si_tocca_la_prenotazione_di_un_altro(client, bottega, adulto, giovane):
    s = nuova_sessione(bottega, "esperienza-tornio")
    pid = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id}).json()["id"]
    assert client.delete(f"{API}/prenotazioni/{pid}", headers=h(giovane[1])).status_code == 404


# --- Pagamenti -------------------------------------------------------------------

def test_pagamento_conferma_e_ricevuta(client, bottega, adulto):  # RF10
    s = nuova_sessione(bottega, "esperienza-tornio")
    pid = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id}).json()["id"]
    pagamento = client.post(f"{API}/prenotazioni/{pid}/pagamento", headers=h(adulto[1]), json={})
    assert pagamento.status_code == 201
    codice = pagamento.json()["codice_ricevuta"]
    assert codice.startswith("TV-") and len(codice) == 11

    mie = client.get(f"{API}/prenotazioni/mie", headers=h(adulto[1])).json()
    assert mie[0]["stato"] == "confermata"

    ricevuta = client.get(f"{API}/pagamenti/{codice}/ricevuta", headers=h(adulto[1])).json()
    assert ricevuta["importo_cent"] == 6000 and ricevuta["intestatario"] == "Anna Test"
    assert client.post(f"{API}/prenotazioni/{pid}/pagamento", headers=h(adulto[1]), json={}).status_code == 409


def test_pagamento_rifiutato_si_puo_riprovare(client, bottega, adulto):
    s = nuova_sessione(bottega, "esperienza-tornio")
    pid = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id}).json()["id"]
    rifiutato = client.post(f"{API}/prenotazioni/{pid}/pagamento", headers=h(adulto[1]),
                            json={"esito_simulato": "fallito"})
    assert rifiutato.status_code == 402 and rifiutato.json()["codice"] == "PAGAMENTO_RIFIUTATO"
    riuscito = client.post(f"{API}/prenotazioni/{pid}/pagamento", headers=h(adulto[1]), json={})
    assert riuscito.status_code == 201
    assert bottega.query(Pagamento).count() == 2  # anche il tentativo fallito resta registrato


def test_ricevuta_di_un_altro_non_visibile(client, bottega, adulto, giovane):
    s = nuova_sessione(bottega, "esperienza-tornio")
    pid = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id}).json()["id"]
    codice = client.post(f"{API}/prenotazioni/{pid}/pagamento", headers=h(adulto[1]), json={}).json()["codice_ricevuta"]
    assert client.get(f"{API}/pagamenti/{codice}/ricevuta", headers=h(giovane[1])).status_code == 404


# --- Pacchetti e membership --------------------------------------------------------

def test_pacchetto_copre_i_suoi_servizi_una_volta(client, bottega, giovane):  # RF09, RB04
    pacchetto = bottega.query(Pacchetto).filter_by(slug="giornata-in-bottega").one()
    acquisto = client.post(f"{API}/acquisti", headers=h(giovane[1]), json={"pacchetto_id": pacchetto.id}).json()
    assert acquisto["prezzo_finale_cent"] == 8500  # niente Under 26 sul pacchetto: è già scontato
    s = nuova_sessione(bottega, "esperienza-tornio")

    non_pagato = client.post(f"{API}/prenotazioni", headers=h(giovane[1]),
                             json={"sessione_id": s.id, "acquisto_id": acquisto["id"]})
    assert non_pagato.json()["codice"] == "ACQUISTO_NON_ATTIVO"

    client.post(f"{API}/acquisti/{acquisto['id']}/pagamento", headers=h(giovane[1]), json={})
    coperta = client.post(f"{API}/prenotazioni", headers=h(giovane[1]),
                          json={"sessione_id": s.id, "acquisto_id": acquisto["id"]}).json()
    assert coperta["prezzo_finale_cent"] == 0 and coperta["stato"] == "confermata"

    altra = nuova_sessione(bottega, "esperienza-tornio", tra_ore=96)
    r = client.post(f"{API}/prenotazioni", headers=h(giovane[1]),
                    json={"sessione_id": altra.id, "acquisto_id": acquisto["id"]})
    assert r.json()["codice"] == "PACCHETTO_GIA_USATO"

    corso = nuova_sessione(bottega, "corso-tornio-base")
    r = client.post(f"{API}/prenotazioni", headers=h(giovane[1]),
                    json={"sessione_id": corso.id, "acquisto_id": acquisto["id"]})
    assert r.json()["codice"] == "SERVIZIO_NON_INCLUSO"


def test_coworking_consuma_e_restituisce_ingressi(client, bottega, adulto):  # RB06
    s = nuova_sessione(bottega, "coworking")
    r = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id})
    assert r.json()["codice"] == "MEMBERSHIP_RICHIESTA"

    piano = bottega.query(PianoMembership).filter_by(ingressi=8).one()
    acquisto = client.post(f"{API}/acquisti", headers=h(adulto[1]), json={"piano_id": piano.id}).json()
    client.post(f"{API}/acquisti/{acquisto['id']}/pagamento", headers=h(adulto[1]), json={})
    attivo = client.get(f"{API}/acquisti/miei", headers=h(adulto[1])).json()[0]
    assert attivo["stato"] == "attivo" and attivo["ingressi_residui"] == 8
    assert attivo["scadenza"] == (date.today() + timedelta(days=30)).isoformat()

    pid = client.post(f"{API}/prenotazioni", headers=h(adulto[1]), json={"sessione_id": s.id}).json()["id"]
    assert client.get(f"{API}/acquisti/miei", headers=h(adulto[1])).json()[0]["ingressi_residui"] == 7

    client.delete(f"{API}/prenotazioni/{pid}", headers=h(adulto[1]))
    assert client.get(f"{API}/acquisti/miei", headers=h(adulto[1])).json()[0]["ingressi_residui"] == 8


def test_acquisto_richiede_un_solo_prodotto(client, bottega, adulto):
    assert client.post(f"{API}/acquisti", headers=h(adulto[1]), json={}).status_code == 422
    assert client.post(f"{API}/acquisti", headers=h(adulto[1]),
                       json={"pacchetto_id": 1, "piano_id": 1}).status_code == 422
