"""cria tabela quartos

Revision ID: 006
Revises: 005
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quartos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("hotel_id", sa.UUID(), nullable=False),
        sa.Column("tipo", sa.String(length=100), nullable=False),
        sa.Column("preco_diaria", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_adultos", sa.Integer(), nullable=False),
        sa.Column("max_criancas", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["hotel_id"], ["hoteis.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("quartos")