"""Schemi Pydantic di valutazioni, promozioni e dashboard."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import RegolaPromozione


class ValutazioneCrea(BaseModel):
    prenotazione_id: int
    voto: int = Field(ge=1, le=5)
    commento: str = Field(default="", max_length=1000)


class ValutazioneOut(BaseModel):
    id: int
    voto: int
    commento: str
    autore: str          # solo il nome di battesimo, per rispetto della privacy
    servizio: str
    creata_il: datetime


class RiepilogoValutazioni(BaseModel):
    media: float | None
    numero: int
    valutazioni: list[ValutazioneOut]


class PromozioneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codice: str | None
    nome: str
    descrizione: str
    regola: RegolaPromozione
    percentuale: int
    valida_dal: date | None
    valida_al: date | None
    attiva: bool


class PromozioneCrea(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    descrizione: str = ""
    regola: RegolaPromozione = RegolaPromozione.codice
    codice: str | None = Field(default=None, min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    percentuale: int = Field(ge=1, le=100)
    valida_dal: date | None = None
    valida_al: date | None = None

    @model_validator(mode="after")
    def coerenza(self):
        if self.regola == RegolaPromozione.codice and not self.codice:
            raise ValueError("Una promozione a codice deve avere un codice")
        if self.valida_dal and self.valida_al and self.valida_al < self.valida_dal:
            raise ValueError("La data di fine validità precede quella di inizio")
        return self


class PromozioneAggiorna(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    descrizione: str | None = None
    percentuale: int | None = Field(default=None, ge=1, le=100)
    valida_dal: date | None = None
    valida_al: date | None = None
    attiva: bool | None = None


class ServizioPiuRichiesto(BaseModel):
    servizio: str
    prenotazioni: int


class DashboardOut(BaseModel):
    """Indicatori dell'attività della bottega in un periodo (RF19)."""

    dal: date
    al: date
    prenotazioni_confermate: int
    tasso_riempimento_medio: float          # tra 0 e 1
    incassi_totali_cent: int
    incassi_cent_per_tipo: dict[str, int]
    membership_attive: int
    nuovi_clienti: int
    valutazione_media: float | None
    servizi_piu_richiesti: list[ServizioPiuRichiesto]
