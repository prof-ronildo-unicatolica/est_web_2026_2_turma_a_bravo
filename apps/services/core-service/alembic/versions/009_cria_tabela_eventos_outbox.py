
"""Cria tabela de eventos Outbox - Sprint 6.

Revision ID: 009
Revises: 008
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eventos_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reserva_id", sa.Uuid(), nullable=False),
        sa.Column("fila", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("tentativas", sa.Integer(), nullable=False),
        sa.Column("ultimo_erro", sa.Text(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "publicado_em",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["reserva_id"],
            ["reservas.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "tentativas >= 0",
            name="ck_eventos_outbox_tentativas",
        ),
    )

    op.create_index(
        "ix_eventos_outbox_reserva_id",
        "eventos_outbox",
        ["reserva_id"],
    )

    op.create_index(
        "ix_eventos_outbox_status",
        "eventos_outbox",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_eventos_outbox_status",
        table_name="eventos_outbox",
    )

    op.drop_index(
        "ix_eventos_outbox_reserva_id",
        table_name="eventos_outbox",
    )

    op.drop_table("eventos_outbox")
