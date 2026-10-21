"""Endpoint di valutazioni (clienti e pubblico), promozioni e dashboard (amministratore)."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dipendenze import get_utente_corrente, richiedi_admin
from app.models import Utente
from app.schemas.amministrazione import (
    DashboardOut,
    PromozioneAggiorna,
    PromozioneCrea,
    PromozioneOut,
    RiepilogoValutazioni,
    ValutazioneCrea,
    ValutazioneOut,
)
from app.services import amministrazione as servizio

router = APIRouter(tags=["valutazioni"])
admin = APIRouter(prefix="/admin", tags=["amministrazione"], dependencies=[Depends(richiedi_admin)])


@router.post("/valutazioni", response_model=ValutazioneOut, status_code=status.HTTP_201_CREATED)
def valuta(dati: ValutazioneCrea, utente: Utente = Depends(get_utente_corrente), db: Session = Depends(get_db)):
    """Valutazione da 1 a 5 di un'attività svolta (RF13, RB07)."""
    return servizio.crea_valutazione(db, utente, dati)


@router.get("/servizi/{servizio_id}/valutazioni", response_model=RiepilogoValutazioni)
def valutazioni(servizio_id: int, db: Session = Depends(get_db)):
    """Recensioni pubbliche e voto medio di un servizio (RF13)."""
    return servizio.valutazioni_servizio(db, servizio_id)


@admin.get("/promozioni", response_model=list[PromozioneOut])
def promozioni(db: Session = Depends(get_db)):
    """Elenco delle promozioni, attive per prime (RF18)."""
    return servizio.elenca_promozioni(db)


@admin.post("/promozioni", response_model=PromozioneOut, status_code=status.HTTP_201_CREATED)
def nuova_promozione(dati: PromozioneCrea, db: Session = Depends(get_db)):
    """Crea un codice sconto o una promozione automatica (RF18)."""
    return servizio.crea_promozione(db, dati)


@admin.patch("/promozioni/{promozione_id}", response_model=PromozioneOut)
def modifica_promozione(promozione_id: int, dati: PromozioneAggiorna, db: Session = Depends(get_db)):
    """Modifica o disattiva una promozione (RF18)."""
    return servizio.aggiorna_promozione(db, promozione_id, dati)


@admin.get("/dashboard", response_model=DashboardOut)
def cruscotto(dal: date | None = None, al: date | None = None, db: Session = Depends(get_db)):
    """Indicatori del periodo; senza date, gli ultimi 30 giorni (RF19)."""
    al = al or date.today()
    dal = dal or al - timedelta(days=29)
    return servizio.dashboard(db, dal, al)
