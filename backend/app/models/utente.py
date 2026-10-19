"""Utenti della piattaforma: clienti e amministratori."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enumerazioni import RuoloUtente, tipo_enum


class Utente(Base):
    __tablename__ = "utenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Solo l'hash bcrypt: la password in chiaro non viene mai memorizzata
    password_hash: Mapped[str] = mapped_column(String(255))
    nome: Mapped[str] = mapped_column(String(80))
    cognome: Mapped[str] = mapped_column(String(80))
    # Serve per la promozione "Giovani in bottega" (RB03)
    data_nascita: Mapped[date] = mapped_column(Date)
    ruolo: Mapped[RuoloUtente] = mapped_column(
        tipo_enum(RuoloUtente, "ruolo_utente"), default=RuoloUtente.cliente
    )
    consenso_privacy: Mapped[bool] = mapped_column(Boolean, default=False)
    creato_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prenotazioni: Mapped[list["Prenotazione"]] = relationship(back_populates="utente")  # noqa: F821
    acquisti: Mapped[list["Acquisto"]] = relationship(back_populates="utente")  # noqa: F821
