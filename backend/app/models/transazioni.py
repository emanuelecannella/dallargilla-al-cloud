"""Prenotazioni, acquisti di pacchetti o membership, pagamenti."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enumerazioni import (
    EsitoPagamento,
    StatoAcquisto,
    StatoPrenotazione,
    tipo_enum,
)


class Acquisto(Base):
    """Acquisto di un pacchetto OPPURE di un piano di membership (mai entrambi)."""

    __tablename__ = "acquisti"
    __table_args__ = (
        CheckConstraint("num_nonnulls(pacchetto_id, piano_id) = 1", name="ck_acquisti_prodotto"),
        CheckConstraint("sconto_cent >= 0 AND prezzo_finale_cent >= 0", name="ck_acquisti_importi"),
        CheckConstraint(
            "prezzo_finale_cent = prezzo_listino_cent - sconto_cent", name="ck_acquisti_totale"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id", ondelete="RESTRICT"), index=True)
    pacchetto_id: Mapped[int | None] = mapped_column(
        ForeignKey("pacchetti.id", ondelete="RESTRICT"), nullable=True
    )
    piano_id: Mapped[int | None] = mapped_column(
        ForeignKey("piani_membership.id", ondelete="RESTRICT"), nullable=True
    )
    promozione_id: Mapped[int | None] = mapped_column(
        ForeignKey("promozioni.id", ondelete="RESTRICT"), nullable=True
    )
    prezzo_listino_cent: Mapped[int] = mapped_column(Integer)
    sconto_cent: Mapped[int] = mapped_column(Integer, default=0)
    prezzo_finale_cent: Mapped[int] = mapped_column(Integer)
    # Valorizzati solo per la membership di coworking
    ingressi_residui: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scadenza: Mapped[date | None] = mapped_column(Date, nullable=True)
    stato: Mapped[StatoAcquisto] = mapped_column(
        tipo_enum(StatoAcquisto, "stato_acquisto"), default=StatoAcquisto.in_attesa
    )
    creato_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    utente: Mapped["Utente"] = relationship(back_populates="acquisti")  # noqa: F821
    pacchetto: Mapped[Optional["Pacchetto"]] = relationship()  # noqa: F821
    piano: Mapped[Optional["PianoMembership"]] = relationship()  # noqa: F821
    prenotazioni: Mapped[list["Prenotazione"]] = relationship(back_populates="acquisto")


class Prenotazione(Base):
    """Posto prenotato da un cliente in una sessione."""

    __tablename__ = "prenotazioni"
    __table_args__ = (
        # Un cliente non può prenotare due volte la stessa data (RB02)
        UniqueConstraint("utente_id", "sessione_id", name="uq_prenotazioni_utente_sessione"),
        CheckConstraint("sconto_cent >= 0 AND prezzo_finale_cent >= 0", name="ck_prenotazioni_importi"),
        CheckConstraint(
            "prezzo_finale_cent = prezzo_listino_cent - sconto_cent", name="ck_prenotazioni_totale"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id", ondelete="RESTRICT"), index=True)
    sessione_id: Mapped[int] = mapped_column(
        ForeignKey("sessioni.id", ondelete="RESTRICT"), index=True
    )
    # Valorizzato se la prenotazione è coperta da un pacchetto o da una membership
    acquisto_id: Mapped[int | None] = mapped_column(
        ForeignKey("acquisti.id", ondelete="RESTRICT"), nullable=True
    )
    promozione_id: Mapped[int | None] = mapped_column(
        ForeignKey("promozioni.id", ondelete="RESTRICT"), nullable=True
    )
    # Gli importi vengono "fotografati" al momento della prenotazione
    prezzo_listino_cent: Mapped[int] = mapped_column(Integer)
    sconto_cent: Mapped[int] = mapped_column(Integer, default=0)
    prezzo_finale_cent: Mapped[int] = mapped_column(Integer)
    stato: Mapped[StatoPrenotazione] = mapped_column(
        tipo_enum(StatoPrenotazione, "stato_prenotazione"), default=StatoPrenotazione.in_attesa
    )
    creata_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    utente: Mapped["Utente"] = relationship(back_populates="prenotazioni")  # noqa: F821
    sessione: Mapped["Sessione"] = relationship(back_populates="prenotazioni")  # noqa: F821
    acquisto: Mapped[Acquisto | None] = relationship(back_populates="prenotazioni")
    pagamenti: Mapped[list["Pagamento"]] = relationship(back_populates="prenotazione")
    valutazione: Mapped[Optional["Valutazione"]] = relationship(back_populates="prenotazione")  # noqa: F821


class Pagamento(Base):
    """Pagamento (simulato) di una prenotazione OPPURE di un acquisto.

    Possono esistere più tentativi per la stessa prenotazione: uno fallito e poi
    uno riuscito. Il codice ricevuta identifica in modo univoco ogni pagamento.
    """

    __tablename__ = "pagamenti"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(prenotazione_id, acquisto_id) = 1", name="ck_pagamenti_oggetto"
        ),
        CheckConstraint("importo_cent >= 0", name="ck_pagamenti_importo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    prenotazione_id: Mapped[int | None] = mapped_column(
        ForeignKey("prenotazioni.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    acquisto_id: Mapped[int | None] = mapped_column(
        ForeignKey("acquisti.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    importo_cent: Mapped[int] = mapped_column(Integer)
    metodo: Mapped[str] = mapped_column(String(30), default="simulato")
    esito: Mapped[EsitoPagamento] = mapped_column(tipo_enum(EsitoPagamento, "esito_pagamento"))
    codice_ricevuta: Mapped[str] = mapped_column(String(20), unique=True)
    pagato_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prenotazione: Mapped[Prenotazione | None] = relationship(back_populates="pagamenti")
    acquisto: Mapped[Acquisto | None] = relationship()
