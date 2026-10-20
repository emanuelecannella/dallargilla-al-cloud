"""Endpoint dell'area personale per prenotazioni, acquisti e pagamenti (solo clienti autenticati)."""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dipendenze import get_utente_corrente
from app.models import Utente
from app.schemas.transazioni import (
    AcquistoCrea,
    AcquistoOut,
    PagamentoIn,
    PagamentoOut,
    PrenotazioneCrea,
    PrenotazioneOut,
    RicevutaOut,
)
from app.services import transazioni as servizio

router = APIRouter(tags=["prenotazioni e pagamenti"])


@router.post("/prenotazioni", response_model=PrenotazioneOut, status_code=status.HTTP_201_CREATED)
def prenota(dati: PrenotazioneCrea, utente: Utente = Depends(get_utente_corrente), db: Session = Depends(get_db)):
    """Prenota una data, applicando lo sconto più vantaggioso (RF08, RF14)."""
    return servizio.prenotazione_out(servizio.crea_prenotazione(db, utente, dati))


@router.get("/prenotazioni/mie", response_model=list[PrenotazioneOut])
def le_mie_prenotazioni(utente: Utente = Depends(get_utente_corrente), db: Session = Depends(get_db)):
    """Prenotazioni future e passate del cliente (RF11)."""
    return [servizio.prenotazione_out(p) for p in servizio.mie_prenotazioni(db, utente)]


@router.delete("/prenotazioni/{prenotazione_id}", status_code=status.HTTP_204_NO_CONTENT)
def annulla(prenotazione_id: int, utente: Utente = Depends(get_utente_corrente), db: Session = Depends(get_db)):
    """Annulla una prenotazione fino a 48 ore prima dell'inizio (RF12, RB05)."""
    servizio.annulla_prenotazione(db, utente, prenotazione_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/prenotazioni/{prenotazione_id}/pagamento", response_model=PagamentoOut,
             status_code=status.HTTP_201_CREATED)
def paga_prenotazione(prenotazione_id: int, dati: PagamentoIn,
                      utente: Utente = Depends(get_utente_corrente), db: Session = Depends(get_db)):
    """Pagamento simulato di una prenotazione (RF10)."""
    return servizio.paga_prenotazione(db, utente, prenotazione_id, dati.esito_simulato)


@router.post("/acquisti", response_model=AcquistoOut, status_code=status.HTTP_201_CREATED)
def acquista(dati: AcquistoCrea, utente: Utente = Depends(get_utente_corrente), db: Session = Depends(get_db)):
    """Acquisto di un pacchetto o di una membership di coworking (RF09)."""
    return servizio.acquisto_out(servizio.crea_acquisto(db, utente, dati))


@router.get("/acquisti/miei", response_model=list[AcquistoOut])
def i_miei_acquisti(utente: Utente = Depends(get_utente_corrente), db: Session = Depends(get_db)):
    """Pacchetti e membership del cliente, con gli ingressi residui (RF09)."""
    return [servizio.acquisto_out(a) for a in servizio.miei_acquisti(db, utente)]


@router.post("/acquisti/{acquisto_id}/pagamento", response_model=PagamentoOut,
             status_code=status.HTTP_201_CREATED)
def paga_acquisto(acquisto_id: int, dati: PagamentoIn,
                  utente: Utente = Depends(get_utente_corrente), db: Session = Depends(get_db)):
    """Pagamento simulato di un acquisto (RF10)."""
    return servizio.paga_acquisto(db, utente, acquisto_id, dati.esito_simulato)


@router.get("/pagamenti/{codice}/ricevuta", response_model=RicevutaOut)
def ricevuta(codice: str, utente: Utente = Depends(get_utente_corrente), db: Session = Depends(get_db)):
    """Ricevuta di un pagamento, visibile al titolare o all'amministratore (RF10)."""
    return servizio.ricevuta(db, utente, codice)
