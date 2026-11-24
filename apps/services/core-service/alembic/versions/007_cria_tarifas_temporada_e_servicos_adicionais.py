from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tarifas_temporada",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("hotel_id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=False),
        sa.Column("percentual_ajuste", sa.Numeric(5, 2), nullable=False),
        sa.CheckConstraint(
            "data_fim >= data_inicio",
            name="ck_tarifas_temporada_periodo",
        ),
        sa.ForeignKeyConstraint(["hotel_id"], ["hoteis.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "servicos_adicionais",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("hotel_id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=True),
        sa.Column("preco", sa.Numeric(10, 2), nullable=False),
        sa.Column("tipo_cobranca", sa.String(length=30), nullable=False),
        sa.CheckConstraint(
            "preco >= 0",
            name="ck_servicos_adicionais_preco",
        ),
        sa.CheckConstraint(
            "tipo_cobranca IN ('por_pessoa_dia', 'por_diaria', 'por_servico')",
            name="ck_servicos_adicionais_tipo_cobranca",
        ),
        sa.ForeignKeyConstraint(["hotel_id"], ["hoteis.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("servicos_adicionais")
    op.drop_table("tarifas_temporada")