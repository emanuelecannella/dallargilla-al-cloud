"""Funzioni di sicurezza: hash delle password e token di accesso JWT."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_impostazioni

impostazioni = get_impostazioni()


def calcola_hash_password(password: str) -> str:
    """Restituisce l'hash bcrypt della password.

    bcrypt aggiunge un "sale" casuale: due utenti con la stessa password
    ottengono hash diversi, e l'hash non si può invertire.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verifica_password(password: str, hash_salvato: str) -> bool:
    """Confronta una password in chiaro con l'hash memorizzato."""
    return bcrypt.checkpw(password.encode("utf-8"), hash_salvato.encode("utf-8"))


def crea_token_accesso(utente_id: int, ruolo: str) -> str:
    """Crea un token JWT firmato che identifica l'utente fino alla scadenza."""
    adesso = datetime.now(timezone.utc)
    contenuto = {
        "sub": str(utente_id),  # "subject": a chi appartiene il token
        "ruolo": ruolo,
        "iat": adesso,          # emesso il
        "exp": adesso + timedelta(minutes=impostazioni.jwt_scadenza_minuti),
    }
    return jwt.encode(contenuto, impostazioni.jwt_secret, algorithm=impostazioni.jwt_algoritmo)


def decodifica_token(token: str) -> dict:
    """Verifica firma e scadenza del token e ne restituisce il contenuto.

    Solleva jwt.PyJWTError se il token è falsificato, malformato o scaduto.
    """
    return jwt.decode(token, impostazioni.jwt_secret, algorithms=[impostazioni.jwt_algoritmo])
