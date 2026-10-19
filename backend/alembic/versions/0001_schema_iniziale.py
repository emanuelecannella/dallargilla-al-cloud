"""Schema iniziale: le 11 tabelle del modello dei dati.

Revisione: 0001
Precedente: nessuna
Creata il: 2026-10-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Tipi ENUM di PostgreSQL (vedi app/models/enumerazioni.py)
ruolo_utente = sa.Enum("cliente", "admin", name="ruolo_utente")
tipo_servizio = sa.Enum("corso", "esperienza", "coworking", name="tipo_servizio")
stato_sessione = sa.Enum("programmata", "annullata", name="stato_sessione")
stato_prenotazione = sa.Enum("in_attesa", "confermata", "annullata", name="stato_prenotazione")
stato_acquisto = sa.Enum("in_attesa", "attivo", "scaduto", name="stato_acquisto")
esito_pagamento = sa.Enum("riuscito", "fallito", name="esito_pagamento")
regola_promozione = sa.Enum("codice", "under26", name="regola_promozione")

ADESSO = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "utenti",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nome", sa.String(80), nullable=False),
        sa.Column("cognome", sa.String(80), nullable=False),
        sa.Column("data_nascita", sa.Date, nullable=False),
        sa.Column("ruolo", ruolo_utente, nullable=False),
        sa.Column("consenso_privacy", sa.Boolean, nullable=False),
        sa.Column("creato_il", sa.DateTime(timezone=True), server_default=ADESSO, nullable=False),
    )
    op.create_index("ix_utenti_email", "utenti", ["email"], unique=True)

    op.create_table(
        "servizi",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tipo", tipo_servizio, nullable=False),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("descrizione", sa.Text, nullable=False),
        sa.Column("durata_minuti", sa.Integer, nullable=False),
        sa.Column("numero_incontri", sa.Integer, nullable=False),
        sa.Column("prezzo_cent", sa.Integer, nullable=False),
        sa.Column("capienza", sa.Integer, nullable=False),
        sa.Column("attivo", sa.Boolean, nullable=False),
        sa.CheckConstraint("prezzo_cent >= 0", name="ck_servizi_prezzo"),
        sa.CheckConstraint("capienza > 0", name="ck_servizi_capienza"),
        sa.CheckConstraint("numero_incontri > 0", name="ck_servizi_incontri"),
    )
    op.create_index("ix_servizi_slug", "servizi", ["slug"], unique=True)
    op.create_index("ix_servizi_tipo", "servizi", ["tipo"])

    op.create_table(
        "sessioni",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "servizio_id",
            sa.Integer,
            sa.ForeignKey("servizi.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("inizio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fine", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capienza", sa.Integer, nullable=False),
        sa.Column("stato", stato_sessione, nullable=False),
        sa.CheckConstraint("fine > inizio", name="ck_sessioni_orario"),
        sa.CheckConstraint("capienza > 0", name="ck_sessioni_capienza"),
    )
    op.create_index("ix_sessioni_servizio_id", "sessioni", ["servizio_id"])
    op.create_index("ix_sessioni_inizio", "sessioni", ["inizio"])

    op.create_table(
        "pacchetti",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("descrizione", sa.Text, nullable=False),
        sa.Column("prezzo_cent", sa.Integer, nullable=False),
        sa.Column("attivo", sa.Boolean, nullable=False),
        sa.CheckConstraint("prezzo_cent >= 0", name="ck_pacchetti_prezzo"),
    )
    op.create_index("ix_pacchetti_slug", "pacchetti", ["slug"], unique=True)

    op.create_table(
        "pacchetto_servizi",
        sa.Column(
            "pacchetto_id",
            sa.Integer,
            sa.ForeignKey("pacchetti.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "servizio_id",
            sa.Integer,
            sa.ForeignKey("servizi.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
    )

    op.create_table(
        "piani_membership",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("ingressi", sa.Integer, nullable=False),
        sa.Column("durata_giorni", sa.Integer, nullable=False),
        sa.Column("prezzo_cent", sa.Integer, nullable=False),
        sa.Column("attivo", sa.Boolean, nullable=False),
        sa.CheckConstraint("prezzo_cent >= 0", name="ck_piani_prezzo"),
        sa.CheckConstraint("ingressi > 0", name="ck_piani_ingressi"),
        sa.CheckConstraint("durata_giorni > 0", name="ck_piani_durata"),
    )

    op.create_table(
        "promozioni",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("codice", sa.String(40), nullable=True, unique=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("descrizione", sa.Text, nullable=False),
        sa.Column("regola", regola_promozione, nullable=False),
        sa.Column("percentuale", sa.Integer, nullable=False),
        sa.Column("valida_dal", sa.Date, nullable=True),
        sa.Column("valida_al", sa.Date, nullable=True),
        sa.Column("attiva", sa.Boolean, nullable=False),
        sa.CheckConstraint("percentuale BETWEEN 1 AND 100", name="ck_promozioni_percentuale"),
        sa.CheckConstraint("regola <> 'codice' OR codice IS NOT NULL", name="ck_promozioni_codice"),
    )

    op.create_table(
        "acquisti",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "utente_id", sa.Integer, sa.ForeignKey("utenti.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "pacchetto_id",
            sa.Integer,
            sa.ForeignKey("pacchetti.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "piano_id",
            sa.Integer,
            sa.ForeignKey("piani_membership.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "promozione_id",
            sa.Integer,
            sa.ForeignKey("promozioni.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("prezzo_listino_cent", sa.Integer, nullable=False),
        sa.Column("sconto_cent", sa.Integer, nullable=False),
        sa.Column("prezzo_finale_cent", sa.Integer, nullable=False),
        sa.Column("ingressi_residui", sa.Integer, nullable=True),
        sa.Column("scadenza", sa.Date, nullable=True),
        sa.Column("stato", stato_acquisto, nullable=False),
        sa.Column("creato_il", sa.DateTime(timezone=True), server_default=ADESSO, nullable=False),
        sa.CheckConstraint("num_nonnulls(pacchetto_id, piano_id) = 1", name="ck_acquisti_prodotto"),
        sa.CheckConstraint(
            "sconto_cent >= 0 AND prezzo_finale_cent >= 0", name="ck_acquisti_importi"
        ),
        sa.CheckConstraint(
            "prezzo_finale_cent = prezzo_listino_cent - sconto_cent", name="ck_acquisti_totale"
        ),
    )
    op.create_index("ix_acquisti_utente_id", "acquisti", ["utente_id"])

    op.create_table(
        "prenotazioni",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "utente_id", sa.Integer, sa.ForeignKey("utenti.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "sessione_id",
            sa.Integer,
            sa.ForeignKey("sessioni.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "acquisto_id",
            sa.Integer,
            sa.ForeignKey("acquisti.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "promozione_id",
            sa.Integer,
            sa.ForeignKey("promozioni.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("prezzo_listino_cent", sa.Integer, nullable=False),
        sa.Column("sconto_cent", sa.Integer, nullable=False),
        sa.Column("prezzo_finale_cent", sa.Integer, nullable=False),
        sa.Column("stato", stato_prenotazione, nullable=False),
        sa.Column("creata_il", sa.DateTime(timezone=True), server_default=ADESSO, nullable=False),
        sa.UniqueConstraint("utente_id", "sessione_id", name="uq_prenotazioni_utente_sessione"),
        sa.CheckConstraint(
            "sconto_cent >= 0 AND prezzo_finale_cent >= 0", name="ck_prenotazioni_importi"
        ),
        sa.CheckConstraint(
            "prezzo_finale_cent = prezzo_listino_cent - sconto_cent", name="ck_prenotazioni_totale"
        ),
    )
    op.create_index("ix_prenotazioni_utente_id", "prenotazioni", ["utente_id"])
    op.create_index("ix_prenotazioni_sessione_id", "prenotazioni", ["sessione_id"])

    op.create_table(
        "pagamenti",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "prenotazione_id",
            sa.Integer,
            sa.ForeignKey("prenotazioni.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "acquisto_id",
            sa.Integer,
            sa.ForeignKey("acquisti.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("importo_cent", sa.Integer, nullable=False),
        sa.Column("metodo", sa.String(30), nullable=False),
        sa.Column("esito", esito_pagamento, nullable=False),
        sa.Column("codice_ricevuta", sa.String(20), nullable=False, unique=True),
        sa.Column("pagato_il", sa.DateTime(timezone=True), server_default=ADESSO, nullable=False),
        sa.CheckConstraint(
            "num_nonnulls(prenotazione_id, acquisto_id) = 1", name="ck_pagamenti_oggetto"
        ),
        sa.CheckConstraint("importo_cent >= 0", name="ck_pagamenti_importo"),
    )
    op.create_index("ix_pagamenti_prenotazione_id", "pagamenti", ["prenotazione_id"])
    op.create_index("ix_pagamenti_acquisto_id", "pagamenti", ["acquisto_id"])

    op.create_table(
        "valutazioni",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "utente_id", sa.Integer, sa.ForeignKey("utenti.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "prenotazione_id",
            sa.Integer,
            sa.ForeignKey("prenotazioni.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("voto", sa.Integer, nullable=False),
        sa.Column("commento", sa.Text, nullable=False),
        sa.Column("creata_il", sa.DateTime(timezone=True), server_default=ADESSO, nullable=False),
        sa.CheckConstraint("voto BETWEEN 1 AND 5", name="ck_valutazioni_voto"),
    )
    op.create_index("ix_valutazioni_utente_id", "valutazioni", ["utente_id"])


def downgrade() -> None:
    # Le tabelle si eliminano in ordine inverso rispetto alle dipendenze
    for tabella in (
        "valutazioni",
        "pagamenti",
        "prenotazioni",
        "acquisti",
        "promozioni",
        "piani_membership",
        "pacchetto_servizi",
        "pacchetti",
        "sessioni",
        "servizi",
        "utenti",
    ):
        op.drop_table(tabella)

    bind = op.get_bind()
    for tipo in (
        regola_promozione,
        esito_pagamento,
        stato_acquisto,
        stato_prenotazione,
        stato_sessione,
        tipo_servizio,
        ruolo_utente,
    ):
        tipo.drop(bind, checkfirst=True)
