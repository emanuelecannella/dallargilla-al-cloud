"""Test funzionali di registrazione, accesso e profilo (RF05, RF06, RF07)."""
from datetime import date

from app.core.sicurezza import crea_token_accesso
from app.models import RuoloUtente, Utente
from tests.conftest import DATI_GIULIA

REGISTRAZIONE = "/api/v1/auth/registrazione"
LOGIN = "/api/v1/auth/login"
PROFILO = "/api/v1/utenti/me"


def intestazione(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Registrazione -------------------------------------------------------------

def test_registrazione_crea_un_cliente(client, db):
    risposta = client.post(REGISTRAZIONE, json=DATI_GIULIA)
    assert risposta.status_code == 201
    corpo = risposta.json()
    assert corpo["email"] == "giulia.rossi@example.com"  # salvata in minuscolo
    assert corpo["ruolo"] == "cliente"
    assert "password" not in corpo and "password_hash" not in corpo

    utente = db.query(Utente).one()
    assert utente.password_hash != DATI_GIULIA["password"]  # mai in chiaro
    assert utente.password_hash.startswith("$2b$")          # formato bcrypt


def test_email_duplicata_rifiutata(client):
    client.post(REGISTRAZIONE, json=DATI_GIULIA)
    altra = {**DATI_GIULIA, "email": "GIULIA.ROSSI@example.com"}
    risposta = client.post(REGISTRAZIONE, json=altra)
    assert risposta.status_code == 409
    assert risposta.json()["codice"] == "EMAIL_GIA_REGISTRATA"


def test_password_debole_rifiutata(client):
    risposta = client.post(REGISTRAZIONE, json={**DATI_GIULIA, "password": "solaparola"})
    assert risposta.status_code == 422


def test_consenso_privacy_obbligatorio(client):
    risposta = client.post(REGISTRAZIONE, json={**DATI_GIULIA, "consenso_privacy": False})
    assert risposta.status_code == 422


def test_eta_minima_14_anni(client):
    oggi = date.today()
    troppo_giovane = date(oggi.year - 10, 1, 1).isoformat()
    risposta = client.post(REGISTRAZIONE, json={**DATI_GIULIA, "data_nascita": troppo_giovane})
    assert risposta.status_code == 422


def test_non_ci_si_registra_come_admin(client, db):
    client.post(REGISTRAZIONE, json={**DATI_GIULIA, "ruolo": "admin"})
    assert db.query(Utente).one().ruolo == RuoloUtente.cliente


# --- Accesso -------------------------------------------------------------------

def test_login_restituisce_un_token(client):
    client.post(REGISTRAZIONE, json=DATI_GIULIA)
    risposta = client.post(LOGIN, json={"email": "giulia.rossi@example.com", "password": "argilla2026"})
    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["access_token"].count(".") == 2  # un JWT ha tre parti separate da punti


def test_login_password_errata(client):
    client.post(REGISTRAZIONE, json=DATI_GIULIA)
    risposta = client.post(LOGIN, json={"email": DATI_GIULIA["email"], "password": "sbagliata1"})
    assert risposta.status_code == 401
    assert risposta.json()["codice"] == "CREDENZIALI_ERRATE"


def test_login_email_inesistente_stesso_messaggio(client):
    risposta = client.post(LOGIN, json={"email": "nessuno@example.com", "password": "qualcosa1"})
    assert risposta.status_code == 401
    assert risposta.json()["detail"] == "Email o password non corretti"


# --- Profilo -------------------------------------------------------------------

def test_profilo_senza_token_rifiutato(client):
    risposta = client.get(PROFILO)
    assert risposta.status_code == 401
    assert risposta.json()["codice"] == "NON_AUTENTICATO"


def test_token_falsificato_rifiutato(client, token_giulia):
    manomesso = token_giulia[:-4] + "abcd"
    assert client.get(PROFILO, headers=intestazione(manomesso)).status_code == 401


def test_token_scaduto_rifiutato(client, token_giulia, monkeypatch):
    from app.core import sicurezza

    monkeypatch.setattr(sicurezza.impostazioni, "jwt_scadenza_minuti", -1)
    scaduto = crea_token_accesso(1, "cliente")
    assert client.get(PROFILO, headers=intestazione(scaduto)).status_code == 401


def test_lettura_profilo(client, token_giulia):
    risposta = client.get(PROFILO, headers=intestazione(token_giulia))
    assert risposta.status_code == 200
    assert risposta.json()["nome"] == "Giulia"


def test_modifica_profilo(client, token_giulia):
    risposta = client.patch(PROFILO, headers=intestazione(token_giulia), json={"nome": "Giulia Maria"})
    assert risposta.status_code == 200
    assert risposta.json()["nome"] == "Giulia Maria"


def test_cambio_password_richiede_quella_attuale(client, token_giulia):
    h = intestazione(token_giulia)
    sbagliato = client.patch(PROFILO, headers=h, json={"password_attuale": "nonlaso1", "nuova_password": "tornio2026"})
    assert sbagliato.status_code == 400

    giusto = client.patch(PROFILO, headers=h, json={"password_attuale": "argilla2026", "nuova_password": "tornio2026"})
    assert giusto.status_code == 200
    nuovo_login = client.post(LOGIN, json={"email": DATI_GIULIA["email"], "password": "tornio2026"})
    assert nuovo_login.status_code == 200


# --- Telefono facoltativo --------------------------------------------------------

def test_telefono_facoltativo(client):
    risposta = client.post(REGISTRAZIONE, json=DATI_GIULIA)
    assert risposta.status_code == 201
    assert risposta.json()["telefono"] is None


def test_telefono_salvato_senza_spazi_e_trattini(client):
    dati = {**DATI_GIULIA, "telefono": "+39 333-123 4567"}
    risposta = client.post(REGISTRAZIONE, json=dati)
    assert risposta.status_code == 201
    assert risposta.json()["telefono"] == "+393331234567"


def test_telefono_non_valido_rifiutato(client):
    for sbagliato in ["ciao", "12345", "+39 333 abc 4567"]:
        risposta = client.post(REGISTRAZIONE, json={**DATI_GIULIA, "telefono": sbagliato})
        assert risposta.status_code == 422, sbagliato


def test_telefono_aggiunto_e_cancellato_dal_profilo(client, token_giulia):
    h = intestazione(token_giulia)
    aggiunto = client.patch(PROFILO, headers=h, json={"telefono": "091 1234567"})
    assert aggiunto.json()["telefono"] == "0911234567"

    # Modificare un altro campo non tocca il telefono
    altro = client.patch(PROFILO, headers=h, json={"nome": "Giulia Maria"})
    assert altro.json()["telefono"] == "0911234567"

    # Un campo vuoto cancella il numero
    cancellato = client.patch(PROFILO, headers=h, json={"telefono": ""})
    assert cancellato.json()["telefono"] is None
