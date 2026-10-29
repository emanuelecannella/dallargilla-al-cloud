"""Schemi Pydantic di prenotazioni, acquisti e pagamenti."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models import EsitoPagamento, StatoAcquisto, StatoPrenotazione


class PrenotazioneCrea(BaseModel):
    sessione_id: int
    codice_promo: str | None = Field(default=None, max_length=40)
    # Facoltativo: prenotazione coperta da un pacchetto già acquistato
    acquisto_id: int | None = None


class PrenotazioneOut(BaseModel):
    id: int
    stato: StatoPrenotazione
    sessione_id: int
    servizio: str
    servizio_slug: str
    inizio: datetime
    fine: datetime
    prezzo_listino_cent: int
    sconto_cent: int
    prezzo_finale_cent: int
    promozione: str | None
    acquisto_id: int | None
    # Codice dell'ultimo pagamento riuscito, per aprire la ricevuta dall'area personale
    codice_ricevuta: str | None
    # Vero se la prenotazione si può ancora annullare gratuitamente (RB05)
    annullabile: bool
    # Vero se l'attività è confermata, già svolta e non ancora valutata (RF13, RB07)
    valutabile: bool
    creata_il: datetime


class AcquistoCrea(BaseModel):
    pacchetto_id: int | None = None
    piano_id: int | None = None
    codice_promo: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def un_solo_prodotto(self):
        if (self.pacchetto_id is None) == (self.piano_id is None):
            raise ValueError("Indicare un pacchetto oppure un piano di membership, non entrambi")
        return self


class AcquistoOut(BaseModel):
    id: int
    tipo: Literal["pacchetto", "membership"]
    nome: str
    stato: StatoAcquisto
    prezzo_listino_cent: int
    sconto_cent: int
    prezzo_finale_cent: int
    promozione: str | None
    ingressi_residui: int | None
    scadenza: date | None
    # Solo per i pacchetti: i servizi inclusi non ancora prenotati, da usare con acquisto_id
    servizi_da_prenotare: list[str]
    creato_il: datetime


class PagamentoIn(BaseModel):
    """Pagamento simulato: nel prototipo l'esito si sceglie per poter provare entrambi i casi."""

    esito_simulato: EsitoPagamento = EsitoPagamento.riuscito


class PagamentoOut(BaseModel):
    codice_ricevuta: str
    esito: EsitoPagamento
    importo_cent: int
    pagato_il: datetime


class RicevutaOut(BaseModel):
    codice_ricevuta: str
    intestatario: str
    descrizione: str
    importo_cent: int
    metodo: str
    esito: EsitoPagamento
    pagato_il: datetime
