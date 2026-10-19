"""Configurazione dell'applicazione.

I valori vengono letti dalle variabili d'ambiente (o dal file .env). I default
servono solo per lo sviluppo e i test: in produzione vanno sempre sovrascritti.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Impostazioni(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    nome_progetto: str = "Terracotta Viva – API"
    database_url: str = "postgresql+psycopg2://terracotta:cambiami@localhost:5432/terracotta_viva"

    jwt_secret: str = "chiave-di-sviluppo-da-non-usare-in-produzione"
    jwt_algoritmo: str = "HS256"
    jwt_scadenza_minuti: int = 60

    cors_origini: list[str] = ["http://localhost:5173"]


@lru_cache
def get_impostazioni() -> Impostazioni:
    """Restituisce le impostazioni, lette una sola volta e poi riutilizzate."""
    return Impostazioni()
