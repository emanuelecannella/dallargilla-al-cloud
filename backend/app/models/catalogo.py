"""Offerta della bottega: servizi, date (sessioni), pacchetti e piani di membership."""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enumerazioni import StatoSessione, TipoServizio, tipo_enum

# Tabella ponte della relazione molti a molti fra pacchetti e servizi
pacchetto_servizi = Table(
    "pacchetto_servizi",
    Base.metadata,
    Column("pacchetto_id", ForeignKey("pacchetti.id", ondelete="CASCADE"), primary_key=True),
    Column("servizio_id", ForeignKey("servizi.id", ondelete="RESTRICT"), primary_key=True),
)


class Servizio(Base):
    """Cosa offre la bottega: un corso, un'esperienza giornaliera o il coworking."""

    __tablename__ = "servizi"
    __table_args__ = (
        CheckConstraint("prezzo_cent >= 0", name="ck_servizi_prezzo"),
        CheckConstraint("capienza > 0", name="ck_servizi_capienza"),
        CheckConstraint("numero_incontri > 0", name="ck_servizi_incontri"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[TipoServizio] = mapped_column(tipo_enum(TipoServizio, "tipo_servizio"), index=True)
    nome: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)  # usato negli URL
    descrizione: Mapped[str] = mapped_column(Text, default="")
    durata_minuti: Mapped[int] = mapped_column(Integer)          # durata di un singolo incontro
    numero_incontri: Mapped[int] = mapped_column(Integer, default=1)
    prezzo_cent: Mapped[int] = mapped_column(Integer)             # prezzo in centesimi di euro
    capienza: Mapped[int] = mapped_column(Integer)                # capienza predefinita delle sessioni
    attivo: Mapped[bool] = mapped_column(Boolean, default=True)

    sessioni: Mapped[list["Sessione"]] = relationship(back_populates="servizio")
    pacchetti: Mapped[list["Pacchetto"]] = relationship(
        secondary=pacchetto_servizi, back_populates="servizi"
    )


class Sessione(Base):
    """Quando si svolge un servizio: una data con orario e posti disponibili."""

    __tablename__ = "sessioni"
    __table_args__ = (
        CheckConstraint("fine > inizio", name="ck_sessioni_orario"),
        CheckConstraint("capienza > 0", name="ck_sessioni_capienza"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    servizio_id: Mapped[int] = mapped_column(
        ForeignKey("servizi.id", ondelete="RESTRICT"), index=True
    )
    inizio: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fine: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capienza: Mapped[int] = mapped_column(Integer)
    stato: Mapped[StatoSessione] = mapped_column(
        tipo_enum(StatoSessione, "stato_sessione"), default=StatoSessione.programmata
    )

    servizio: Mapped[Servizio] = relationship(back_populates="sessioni")
    prenotazioni: Mapped[list["Prenotazione"]] = relationship(back_populates="sessione")  # noqa: F821


class Pacchetto(Base):
    """Combinazione di servizi a prezzo scontato, ad esempio "Giornata in bottega"."""

    __tablename__ = "pacchetti"
    __table_args__ = (CheckConstraint("prezzo_cent >= 0", name="ck_pacchetti_prezzo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    descrizione: Mapped[str] = mapped_column(Text, default="")
    prezzo_cent: Mapped[int] = mapped_column(Integer)
    attivo: Mapped[bool] = mapped_column(Boolean, default=True)

    servizi: Mapped[list[Servizio]] = relationship(
        secondary=pacchetto_servizi, back_populates="pacchetti"
    )


class PianoMembership(Base):
    """Abbonamento al coworking: un numero di ingressi da usare entro una scadenza (RB06)."""

    __tablename__ = "piani_membership"
    __table_args__ = (
        CheckConstraint("prezzo_cent >= 0", name="ck_piani_prezzo"),
        CheckConstraint("ingressi > 0", name="ck_piani_ingressi"),
        CheckConstraint("durata_giorni > 0", name="ck_piani_durata"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    ingressi: Mapped[int] = mapped_column(Integer)
    durata_giorni: Mapped[int] = mapped_column(Integer)
    prezzo_cent: Mapped[int] = mapped_column(Integer)
    attivo: Mapped[bool] = mapped_column(Boolean, default=True)
