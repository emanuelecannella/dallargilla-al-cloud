"""Endpoint dell'area personale: profilo dell'utente autenticato."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dipendenze import get_utente_corrente
from app.models import Utente
from app.schemas.utente import UtenteAggiorna, UtenteOut
from app.services import utenti as servizio_utenti

router = APIRouter(prefix="/utenti", tags=["area personale"])


@router.get("/me", response_model=UtenteOut)
def leggi_profilo(utente: Utente = Depends(get_utente_corrente)):
    """Dati del profilo dell'utente autenticato (RF07)."""
    return utente


@router.patch("/me", response_model=UtenteOut)
def modifica_profilo(
    dati: UtenteAggiorna,
    utente: Utente = Depends(get_utente_corrente),
    db: Session = Depends(get_db),
):
    """Modifica dei dati personali e, se richiesto, della password (RF07)."""
    return servizio_utenti.aggiorna_profilo(db, utente, dati)
