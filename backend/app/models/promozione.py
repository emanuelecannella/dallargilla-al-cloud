"""Promozioni e codici sconto."""
from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enumerazioni import RegolaPromozione, tipo_enum


class Promozione(Base):
    __tablename__ = "promozioni"
    __table_args__ = (
        CheckConstraint("percentuale BETWEEN 1 AND 100", name="ck_promozioni_percentuale"),
        # Una promozione "a codice" deve avere un codice
        CheckConstraint("regola <> 'codice' OR codice IS NOT NULL", name="ck_promozioni_codice"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codice: Mapped[str | None] = mapped_column(String(40), unique=True, nullable=True)
    nome: Mapped[str] = mapped_column(String(120))
    descrizione: Mapped[str] = mapped_column(Text, default="")
    regola: Mapped[RegolaPromozione] = mapped_column(tipo_enum(RegolaPromozione, "regola_promozione"))
    percentuale: Mapped[int] = mapped_column(Integer)
    valida_dal: Mapped[date | None] = mapped_column(Date, nullable=True)
    valida_al: Mapped[date | None] = mapped_column(Date, nullable=True)
    attiva: Mapped[bool] = mapped_column(Boolean, default=True)
