"""Insiemi di valori ammessi per alcuni campi (enumerazioni).

Ereditare da str fa sì che i valori vengano serializzati in JSON come semplici
stringhe, ad esempio "cliente" invece di "RuoloUtente.cliente".
"""
import enum

from sqlalchemy import Enum as SAEnum


class RuoloUtente(str, enum.Enum):
    cliente = "cliente"
    admin = "admin"


class TipoServizio(str, enum.Enum):
    corso = "corso"
    esperienza = "esperienza"
    coworking = "coworking"


class StatoSessione(str, enum.Enum):
    programmata = "programmata"
    annullata = "annullata"


class StatoPrenotazione(str, enum.Enum):
    in_attesa = "in_attesa"
    confermata = "confermata"
    annullata = "annullata"


class StatoAcquisto(str, enum.Enum):
    in_attesa = "in_attesa"
    attivo = "attivo"
    scaduto = "scaduto"


class EsitoPagamento(str, enum.Enum):
    riuscito = "riuscito"
    fallito = "fallito"


class RegolaPromozione(str, enum.Enum):
    codice = "codice"      # si applica inserendo un codice
    under26 = "under26"    # si applica in automatico in base all'età


def tipo_enum(classe: type[enum.Enum], nome: str) -> SAEnum:
    """Crea il tipo ENUM di PostgreSQL salvando i valori (non i nomi Python)."""
    return SAEnum(classe, name=nome, values_callable=lambda e: [m.value for m in e])
