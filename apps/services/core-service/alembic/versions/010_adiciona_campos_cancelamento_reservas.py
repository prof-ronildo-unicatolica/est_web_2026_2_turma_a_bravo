from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reservas",
        sa.Column(
            "nao_reembolsavel",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "reservas",
        sa.Column(
            "valor_diaria",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "reservas",
        sa.Column(
            "data_cancelamento",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "reservas",
        sa.Column("valor_multa", sa.Numeric(12, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reservas", "valor_multa")
    op.drop_column("reservas", "data_cancelamento")
    op.drop_column("reservas", "valor_diaria")
    op.drop_column("reservas", "nao_reembolsavel")