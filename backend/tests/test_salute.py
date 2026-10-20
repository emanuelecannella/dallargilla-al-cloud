"""Primo test: il server risponde e l'applicazione si avvia correttamente."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_salute_risponde_ok():
    risposta = client.get("/api/v1/salute")
    assert risposta.status_code == 200
    assert risposta.json()["stato"] == "ok"


def test_documentazione_api_disponibile():
    # FastAPI genera in automatico la specifica OpenAPI delle API
    risposta = client.get("/openapi.json")
    assert risposta.status_code == 200
    assert risposta.json()["info"]["version"] == "0.4.0"


def test_modelli_registrano_tutte_le_tabelle():
    import app.models  # noqa: F401
    from app.core.database import Base

    attese = {
        "utenti", "servizi", "sessioni", "pacchetti", "pacchetto_servizi", "piani_membership",
        "promozioni", "acquisti", "prenotazioni", "pagamenti", "valutazioni",
    }
    assert attese == set(Base.metadata.tables)
