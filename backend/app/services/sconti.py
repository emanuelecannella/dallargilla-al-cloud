"""Calcolo degli sconti: promozione Under 26 e codici promozionali (RB03, RB08)."""
from datetime import date

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errori import ErroreApplicativo
from app.models import Promozione, RegolaPromozione, Utente

ETA_LIMITE_GIOVANI = 26


def eta(nascita: date, giorno: date) -> int:
    return giorno.year - nascita.year - ((giorno.month, giorno.day) < (nascita.month, nascita.day))


def importo_sconto(prezzo_cent: int, percentuale: int) -> int:
    """Sconto in centesimi, arrotondato al centesimo più vicino con aritmetica intera."""
    return (prezzo_cent * percentuale + 50) // 100


def _valida_oggi(promo: Promozione, oggi: date) -> bool:
    return (
        promo.attiva
        and (promo.valida_dal is None or promo.valida_dal <= oggi)
        and (promo.valida_al is None or oggi <= promo.valida_al)
    )


def migliore_sconto(
    db: Session,
    utente: Utente,
    prezzo_cent: int,
    codice: str | None,
    ammette_under26: bool,
    oggi: date | None = None,
) -> tuple[Promozione | None, int]:
    """Restituisce la promozione più vantaggiosa per il cliente e l'importo dello sconto.

    Gli sconti non si sommano: tra quelli applicabili vince il maggiore (RB08).
    Un codice inesistente o scaduto viene segnalato, così il cliente sa che non è stato applicato.
    """
    oggi = oggi or date.today()
    candidate: list[Promozione] = []

    if codice:
        promo = db.scalar(
            select(Promozione).where(
                func.upper(Promozione.codice) == codice.strip().upper(),
                Promozione.regola == RegolaPromozione.codice,
            )
        )
        if promo is None or not _valida_oggi(promo, oggi):
            raise ErroreApplicativo(
                status.HTTP_400_BAD_REQUEST, "CODICE_NON_VALIDO", "Codice promozionale non valido o scaduto"
            )
        candidate.append(promo)

    if ammette_under26 and eta(utente.data_nascita, oggi) < ETA_LIMITE_GIOVANI:
        for promo in db.scalars(select(Promozione).where(Promozione.regola == RegolaPromozione.under26)):
            if _valida_oggi(promo, oggi):
                candidate.append(promo)

    if not candidate or prezzo_cent == 0:
        return None, 0
    migliore = max(candidate, key=lambda p: importo_sconto(prezzo_cent, p.percentuale))
    return migliore, importo_sconto(prezzo_cent, migliore.percentuale)
