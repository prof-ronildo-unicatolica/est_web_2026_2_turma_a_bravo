
"""Cria tabela de reservas - Sprint 6.

Revision ID: 008
Revises: 007
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reservas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cliente_email", sa.String(length=255), nullable=False),
        sa.Column("quarto_id", sa.Uuid(), nullable=False),
        sa.Column("data_entrada", sa.Date(), nullable=False),
        sa.Column("data_saida", sa.Date(), nullable=False),
        sa.Column("quantidade_adultos", sa.Integer(), nullable=False),
        sa.Column("quantidade_criancas", sa.Integer(), nullable=False),
        sa.Column("valor_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["quarto_id"],
            ["quartos.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "data_saida > data_entrada",
            name="ck_reservas_periodo",
        ),
        sa.CheckConstraint(
            "quantidade_adultos >= 1",
            name="ck_reservas_adultos",
        ),
        sa.CheckConstraint(
            "quantidade_criancas >= 0",
            name="ck_reservas_criancas",
        ),
    )

    op.create_index(
        "ix_reservas_cliente_email",
        "reservas",
        ["cliente_email"],
    )

    op.create_index(
        "ix_reservas_quarto_id",
        "reservas",
        ["quarto_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_reservas_quarto_id",
        table_name="reservas",
    )

    op.drop_index(
        "ix_reservas_cliente_email",
        table_name="reservas",
    )

    op.drop_table("reservas")
