"""Valutazioni lasciate dai clienti sulle attività svolte."""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Valutazione(Base):
    __tablename__ = "valutazioni"
    __table_args__ = (CheckConstraint("voto BETWEEN 1 AND 5", name="ck_valutazioni_voto"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id", ondelete="RESTRICT"), index=True)
    # unique: una sola valutazione per ogni attività svolta (RB07)
    prenotazione_id: Mapped[int] = mapped_column(
        ForeignKey("prenotazioni.id", ondelete="RESTRICT"), unique=True
    )
    voto: Mapped[int] = mapped_column(Integer)
    commento: Mapped[str] = mapped_column(Text, default="")
    creata_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prenotazione: Mapped["Prenotazione"] = relationship(back_populates="valutazione")  # noqa: F821
