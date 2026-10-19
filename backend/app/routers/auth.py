"""Endpoint di registrazione e accesso."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import get_impostazioni
from app.core.database import get_db
from app.core.sicurezza import crea_token_accesso
from app.schemas.utente import LoginIn, RegistrazioneIn, TokenOut, UtenteOut
from app.services import utenti as servizio_utenti

router = APIRouter(prefix="/auth", tags=["autenticazione"])


@router.post("/registrazione", response_model=UtenteOut, status_code=status.HTTP_201_CREATED)
def registrazione(dati: RegistrazioneIn, db: Session = Depends(get_db)):
    """Crea un nuovo account cliente (RF05)."""
    return servizio_utenti.registra_utente(db, dati)


@router.post("/login", response_model=TokenOut)
def login(dati: LoginIn, db: Session = Depends(get_db)):
    """Verifica le credenziali e restituisce il token di accesso (RF06)."""
    utente = servizio_utenti.autentica(db, dati.email, dati.password)
    return TokenOut(
        access_token=crea_token_accesso(utente.id, utente.ruolo.value),
        scade_tra_minuti=get_impostazioni().jwt_scadenza_minuti,
    )
