"""Dipendenze FastAPI condivise: utente autenticato e controllo del ruolo."""
import jwt
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errori import ErroreApplicativo
from app.core.sicurezza import decodifica_token
from app.models import RuoloUtente, Utente

# Legge l'intestazione "Authorization: Bearer <token>"; in Swagger compare il pulsante "Authorize"
schema_bearer = HTTPBearer(auto_error=False, description="Token ottenuto da /api/v1/auth/login")

NON_AUTENTICATO = ErroreApplicativo(
    status.HTTP_401_UNAUTHORIZED, "NON_AUTENTICATO", "Accesso richiesto o sessione scaduta"
)


def get_utente_corrente(
    credenziali: HTTPAuthorizationCredentials | None = Depends(schema_bearer),
    db: Session = Depends(get_db),
) -> Utente:
    """Restituisce l'utente a cui appartiene il token, oppure risponde 401."""
    if credenziali is None:
        raise NON_AUTENTICATO
    try:
        contenuto = decodifica_token(credenziali.credentials)
        utente_id = int(contenuto["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise NON_AUTENTICATO from None

    utente = db.get(Utente, utente_id)
    if utente is None:
        raise NON_AUTENTICATO
    return utente


def richiedi_admin(utente: Utente = Depends(get_utente_corrente)) -> Utente:
    """Lascia passare solo gli amministratori, altrimenti risponde 403."""
    if utente.ruolo != RuoloUtente.admin:
        raise ErroreApplicativo(
            status.HTTP_403_FORBIDDEN, "PERMESSO_NEGATO", "Funzione riservata all'amministratore"
        )
    return utente
