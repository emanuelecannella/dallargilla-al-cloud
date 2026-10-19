"""Configurazione comune dei test.

I test usano un database separato (stesso nome con suffisso "_test"), creato
automaticamente se non esiste: i dati reali della bottega non vengono mai toccati.
Prima di ogni test le tabelle vengono svuotate, così ogni test parte da zero.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  (registra tutte le tabelle)
from app.core.config import get_impostazioni
from app.core.database import Base, get_db
from app.main import app

url_principale = make_url(get_impostazioni().database_url)
url_test = url_principale.set(database=f"{url_principale.database}_test")


def _crea_database_di_test() -> None:
    motore_admin = create_engine(url_principale, isolation_level="AUTOCOMMIT")
    with motore_admin.connect() as connessione:
        esiste = connessione.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :nome"), {"nome": url_test.database}
        )
        if not esiste:
            connessione.execute(text(f'CREATE DATABASE "{url_test.database}"'))
    motore_admin.dispose()


_crea_database_di_test()
motore_test = create_engine(url_test)
SessioneTest = sessionmaker(bind=motore_test, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def schema_di_test():
    Base.metadata.drop_all(motore_test)
    Base.metadata.create_all(motore_test)
    yield
    Base.metadata.drop_all(motore_test)


@pytest.fixture(autouse=True)
def tabelle_vuote():
    tabelle = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with motore_test.begin() as connessione:
        connessione.execute(text(f"TRUNCATE {tabelle} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db():
    sessione = SessioneTest()
    yield sessione
    sessione.close()


@pytest.fixture
def client():
    def get_db_test():
        sessione = SessioneTest()
        try:
            yield sessione
        finally:
            sessione.close()

    app.dependency_overrides[get_db] = get_db_test
    yield TestClient(app)
    app.dependency_overrides.clear()


DATI_GIULIA = {
    "email": "Giulia.Rossi@example.com",
    "password": "argilla2026",
    "nome": "Giulia",
    "cognome": "Rossi",
    "data_nascita": "2003-05-12",
    "consenso_privacy": True,
}


@pytest.fixture
def token_giulia(client) -> str:
    """Registra la cliente di prova e restituisce il suo token di accesso."""
    client.post("/api/v1/auth/registrazione", json=DATI_GIULIA)
    risposta = client.post(
        "/api/v1/auth/login",
        json={"email": DATI_GIULIA["email"], "password": DATI_GIULIA["password"]},
    )
    return risposta.json()["access_token"]
