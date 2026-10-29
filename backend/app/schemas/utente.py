"""Schemi Pydantic: definiscono e validano i dati in ingresso e in uscita delle API utente."""
import re
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import RuoloUtente

ETA_MINIMA = 14  # in Italia è l'età minima per prestare da soli il consenso al trattamento dei dati


def _controlla_password(valore: str) -> str:
    if len(valore.encode("utf-8")) > 72:
        # bcrypt considera solo i primi 72 byte: oltre, la password verrebbe troncata
        raise ValueError("La password non può superare i 72 caratteri")
    if not any(c.isalpha() for c in valore) or not any(c.isdigit() for c in valore):
        raise ValueError("La password deve contenere almeno una lettera e un numero")
    return valore


def _controlla_data_nascita(valore: date) -> date:
    oggi = date.today()
    if valore >= oggi:
        raise ValueError("La data di nascita non è valida")
    eta = oggi.year - valore.year - ((oggi.month, oggi.day) < (valore.month, valore.day))
    if eta < ETA_MINIMA:
        raise ValueError(f"Per registrarsi servono almeno {ETA_MINIMA} anni")
    return valore


def _controlla_telefono(valore: str | None) -> str | None:
    """Accetta numeri come "+39 333 123 4567" o "091-1234567" e li salva senza spazi né trattini."""
    if valore is None:
        return None
    numero = re.sub(r"[\s\-./()]", "", valore)
    if numero == "":
        return None  # campo lasciato vuoto: il telefono è facoltativo
    if not re.fullmatch(r"\+?\d{6,15}", numero):
        raise ValueError("Il numero di telefono non è valido")
    return numero


# Tipi riutilizzabili: il validatore viene applicato ovunque il tipo è usato
Password = Annotated[str, Field(min_length=8), AfterValidator(_controlla_password)]
DataNascita = Annotated[date, AfterValidator(_controlla_data_nascita)]
Telefono = Annotated[str | None, Field(max_length=30), AfterValidator(_controlla_telefono)]


class RegistrazioneIn(BaseModel):
    email: EmailStr
    password: Password
    nome: str = Field(min_length=1, max_length=80)
    cognome: str = Field(min_length=1, max_length=80)
    data_nascita: DataNascita
    telefono: Telefono = None
    consenso_privacy: bool

    @field_validator("consenso_privacy")
    @classmethod
    def consenso_obbligatorio(cls, valore: bool) -> bool:
        if not valore:
            raise ValueError("Per registrarsi è necessario accettare l'informativa sulla privacy")
        return valore

    @field_validator("nome", "cognome")
    @classmethod
    def togli_spazi(cls, valore: str) -> str:
        valore = valore.strip()
        if not valore:
            raise ValueError("Il campo non può essere vuoto")
        return valore


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    scade_tra_minuti: int


class UtenteOut(BaseModel):
    """Dati dell'utente restituiti dalle API: la password non compare mai."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nome: str
    cognome: str
    data_nascita: date
    telefono: str | None
    ruolo: RuoloUtente
    creato_il: datetime


class UtenteAggiorna(BaseModel):
    """Modifica del profilo: tutti i campi sono facoltativi."""

    nome: str | None = Field(default=None, min_length=1, max_length=80)
    cognome: str | None = Field(default=None, min_length=1, max_length=80)
    data_nascita: DataNascita | None = None
    # Una stringa vuota cancella il numero: il telefono è facoltativo
    telefono: Telefono = None
    password_attuale: str | None = None
    nuova_password: Password | None = None
