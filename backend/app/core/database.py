"""Connessione al database e gestione delle sessioni SQLAlchemy."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_impostazioni

impostazioni = get_impostazioni()

# Il motore gestisce un pool di connessioni riutilizzabili verso PostgreSQL.
# pool_pre_ping verifica che la connessione sia ancora viva prima di usarla.
engine = create_engine(impostazioni.database_url, pool_pre_ping=True)

SessioneLocale = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Classe base da cui derivano tutti i modelli (tabelle) del dominio."""


def get_db() -> Generator[Session, None, None]:
    """Dipendenza FastAPI: apre una sessione per ogni richiesta e la chiude alla fine."""
    db = SessioneLocale()
    try:
        yield db
    finally:
        db.close()
