"""comodidades model and hotel association

Revision ID: 003
Revises: 002
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "comodidades",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )

    op.create_table(
        "hotel_comodidade",
        sa.Column("hotel_id", sa.UUID(), nullable=False),
        sa.Column("comodidade_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["hotel_id"], ["hoteis.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["comodidade_id"], ["comodidades.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("hotel_id", "comodidade_id"),
    )

    comodidades = [
        "Wi-Fi gratuito",
        "Piscina",
        "Estacionamento",
        "Café da manhã incluso",
        "Ar-condicionado",
        "Academia",
    ]
    for nome in comodidades:
        op.execute(
            sa.text(
                "INSERT INTO comodidades (id, nome) VALUES (:id, :nome)"
            ).bindparams(id=uuid.uuid4(), nome=nome)
        )


def downgrade() -> None:
    op.drop_table("hotel_comodidade")
    op.drop_table("comodidades")