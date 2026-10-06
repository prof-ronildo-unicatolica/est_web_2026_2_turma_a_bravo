"""add diaria to hoteis

Revision ID: 003
Revises: 002
Create Date: 2026-09-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "hoteis",
        sa.Column("diaria", sa.String(length=50), nullable=False, server_default="R$ 0"),
    )
    op.alter_column("hoteis", "diaria", server_default=None)


def downgrade() -> None:
    op.drop_column("hoteis", "diaria")
