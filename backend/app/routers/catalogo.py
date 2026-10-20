"""Endpoint pubblici del catalogo: chiunque può consultarli, anche senza account."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import TipoServizio
from app.schemas.catalogo import PacchettoOut, PianoMembershipOut, ServizioOut, SessioneOut
from app.services import catalogo as servizio_catalogo

router = APIRouter(tags=["catalogo"])


@router.get("/servizi", response_model=list[ServizioOut])
def elenco_servizi(tipo: TipoServizio | None = None, db: Session = Depends(get_db)):
    """Servizi attivi, filtrabili per tipologia: corso, esperienza, coworking (RF02, RF03)."""
    return servizio_catalogo.elenca_servizi(db, tipo)


@router.get("/servizi/{slug}", response_model=ServizioOut)
def dettaglio_servizio(slug: str, db: Session = Depends(get_db)):
    """Scheda di un servizio, individuato dal suo indirizzo leggibile (RF02)."""
    return servizio_catalogo.servizio_per_slug(db, slug)


@router.get("/servizi/{servizio_id}/sessioni", response_model=list[SessioneOut])
def date_disponibili(servizio_id: int, db: Session = Depends(get_db)):
    """Date future di un servizio con i posti ancora liberi (RF04)."""
    return servizio_catalogo.sessioni_future(db, servizio_id)


@router.get("/pacchetti", response_model=list[PacchettoOut])
def elenco_pacchetti(db: Session = Depends(get_db)):
    """Pacchetti di esperienze, con il risparmio rispetto all'acquisto separato (RF02)."""
    return servizio_catalogo.elenca_pacchetti(db)


@router.get("/piani-membership", response_model=list[PianoMembershipOut])
def elenco_piani(db: Session = Depends(get_db)):
    """Piani di coworking disponibili (RF02)."""
    return servizio_catalogo.elenca_piani(db)
