"""Schemi Pydantic del catalogo: servizi, sessioni, pacchetti e piani di membership."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import StatoSessione, TipoServizio


class ServizioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoServizio
    nome: str
    slug: str
    descrizione: str
    durata_minuti: int
    numero_incontri: int
    prezzo_cent: int
    capienza: int
    attivo: bool


class ServizioCrea(BaseModel):
    tipo: TipoServizio
    nome: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    descrizione: str = ""
    durata_minuti: int = Field(gt=0, le=600)
    numero_incontri: int = Field(default=1, gt=0, le=52)
    prezzo_cent: int = Field(ge=0)
    capienza: int = Field(gt=0, le=50)


class ServizioAggiorna(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    descrizione: str | None = None
    durata_minuti: int | None = Field(default=None, gt=0, le=600)
    numero_incontri: int | None = Field(default=None, gt=0, le=52)
    prezzo_cent: int | None = Field(default=None, ge=0)
    capienza: int | None = Field(default=None, gt=0, le=50)
    attivo: bool | None = None


class SessioneOut(BaseModel):
    """Una data del calendario, con i posti ancora disponibili."""

    id: int
    servizio_id: int
    inizio: datetime
    fine: datetime
    capienza: int
    posti_residui: int
    stato: StatoSessione


class SessioneCrea(BaseModel):
    servizio_id: int
    inizio: datetime
    # Se non indicati, fine e capienza vengono ricavati dal servizio
    fine: datetime | None = None
    capienza: int | None = Field(default=None, gt=0, le=50)

    @model_validator(mode="after")
    def orari_coerenti(self):
        if self.inizio.tzinfo is None:
            raise ValueError("Indicare data e ora con il fuso orario (es. 2026-11-07T10:00:00+01:00)")
        if self.fine is not None and self.fine <= self.inizio:
            raise ValueError("L'orario di fine deve essere successivo a quello di inizio")
        return self


class SessioneAggiorna(BaseModel):
    inizio: datetime | None = None
    fine: datetime | None = None
    capienza: int | None = Field(default=None, gt=0, le=50)
    stato: StatoSessione | None = None


class IscrittoOut(BaseModel):
    prenotazione_id: int
    utente_id: int
    nome: str
    cognome: str
    email: str
    stato_prenotazione: str


class ServizioInPacchetto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    slug: str
    prezzo_cent: int


class PacchettoOut(BaseModel):
    id: int
    nome: str
    slug: str
    descrizione: str
    prezzo_cent: int
    prezzo_separato_cent: int   # quanto costerebbero i servizi acquistati uno per uno
    risparmio_cent: int
    servizi: list[ServizioInPacchetto]


class PianoMembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    ingressi: int
    durata_giorni: int
    prezzo_cent: int
