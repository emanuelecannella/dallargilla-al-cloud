"""Endpoint di amministrazione del catalogo e del calendario (solo ruolo admin)."""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dipendenze import richiedi_admin
from app.models import TipoServizio
from app.schemas.catalogo import (
    IscrittoOut,
    ServizioAggiorna,
    ServizioCrea,
    ServizioOut,
    SessioneAggiorna,
    SessioneCrea,
    SessioneOut,
)
from app.services import catalogo as servizio_catalogo

# La dipendenza a livello di router protegge in un colpo solo tutti gli endpoint
router = APIRouter(prefix="/admin", tags=["amministrazione"], dependencies=[Depends(richiedi_admin)])


@router.get("/servizi", response_model=list[ServizioOut])
def tutti_i_servizi(tipo: TipoServizio | None = None, db: Session = Depends(get_db)):
    """Tutti i servizi, compresi quelli disattivati (RF15)."""
    return servizio_catalogo.elenca_servizi(db, tipo, solo_attivi=False)


@router.post("/servizi", response_model=ServizioOut, status_code=status.HTTP_201_CREATED)
def nuovo_servizio(dati: ServizioCrea, db: Session = Depends(get_db)):
    """Aggiunge un corso, un'esperienza o un servizio di coworking (RF15)."""
    return servizio_catalogo.crea_servizio(db, dati)


@router.patch("/servizi/{servizio_id}", response_model=ServizioOut)
def modifica_servizio(servizio_id: int, dati: ServizioAggiorna, db: Session = Depends(get_db)):
    """Modifica prezzo, descrizione, capienza o stato di un servizio (RF15)."""
    return servizio_catalogo.aggiorna_servizio(db, servizio_id, dati)


@router.delete("/servizi/{servizio_id}", status_code=status.HTTP_204_NO_CONTENT)
def disattiva_servizio(servizio_id: int, db: Session = Depends(get_db)):
    """Disattiva un servizio: non compare più nel catalogo, ma lo storico resta (RF15)."""
    servizio_catalogo.disattiva_servizio(db, servizio_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sessioni", response_model=SessioneOut, status_code=status.HTTP_201_CREATED)
def nuova_sessione(dati: SessioneCrea, db: Session = Depends(get_db)):
    """Pubblica una nuova data nel calendario (RF16)."""
    return servizio_catalogo.crea_sessione(db, dati)


@router.patch("/sessioni/{sessione_id}", response_model=SessioneOut)
def modifica_sessione(sessione_id: int, dati: SessioneAggiorna, db: Session = Depends(get_db)):
    """Sposta, ridimensiona o annulla una data (RF16)."""
    return servizio_catalogo.aggiorna_sessione(db, sessione_id, dati)


@router.get("/sessioni/{sessione_id}/iscritti", response_model=list[IscrittoOut])
def iscritti(sessione_id: int, db: Session = Depends(get_db)):
    """Elenco degli iscritti a una data (RF17)."""
    return servizio_catalogo.iscritti_sessione(db, sessione_id)
