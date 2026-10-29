"""Numero di telefono facoltativo per gli utenti.

Revisione: 0002
Precedente: 0001
Creata il: 2026-10-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("utenti", sa.Column("telefono", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("utenti", "telefono")
