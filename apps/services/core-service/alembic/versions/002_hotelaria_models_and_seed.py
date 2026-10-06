"""hotelaria models and seed

Revision ID: 002
Revises: 001
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
   
    # Tabela de usuários
    op.create_table(
        "usuarios",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("senha", sa.String(length=255), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Tabela de cidades
    op.create_table(
        "cidades",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Tabela de hotéis
    op.create_table(
        "hoteis",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("endereco", sa.String(length=150), nullable=False),
        sa.Column("estrelas", sa.Integer(), nullable=False),
        sa.Column("cidade_id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "estrelas >= 1 AND estrelas <= 5",
            name="ck_hoteis_estrelas",
        ),
        sa.ForeignKeyConstraint(["cidade_id"], ["cidades.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # IDs do seed
    admin_id = uuid.uuid4()
    fortaleza_id = uuid.uuid4()
    quixada_id = uuid.uuid4()
    canoa_id = uuid.uuid4()

    # Usuário administrador
    op.execute(
        sa.text(
            """
            INSERT INTO usuarios
                (id, nome, email, senha, ativo, is_admin)
            VALUES
                (:id, :nome, :email, :senha, :ativo, :is_admin)
            """
        ).bindparams(
            id=admin_id,
            nome="Administrador da Franquia",
            email="admin@hotel.com",
            senha="admin123",
            ativo=True,
            is_admin=True,
        )
    )

    # Cidades
    cidades = [
        (fortaleza_id, "Fortaleza", "CE"),
        (quixada_id, "Quixadá", "CE"),
        (canoa_id, "Canoa Quebrada", "CE"),
    ]

    for cidade_id, nome, uf in cidades:
        op.execute(
            sa.text(
                """
                INSERT INTO cidades (id, nome, uf)
                VALUES (:id, :nome, :uf)
                """
            ).bindparams(
                id=cidade_id,
                nome=nome,
                uf=uf,
            )
        )

    # Hotéis de 1 a 5 estrelas
    hoteis = [
        ("Hotel Econômico", "Rua Central, 100", 1, quixada_id),
        ("Hotel Sertão", "Av. Principal, 200", 2, quixada_id),
        ("Hotel Executivo", "Av. Beira Mar, 300", 3, fortaleza_id),
        ("Hotel Praia", "Av. das Dunas, 400", 4, canoa_id),
        ("Hotel Premium", "Av. Beira Mar, 500", 5, fortaleza_id),
    ]

    for nome, endereco, estrelas, cidade_id in hoteis:
        op.execute(
            sa.text(
                """
                INSERT INTO hoteis
                    (id, nome, endereco, estrelas, cidade_id)
                VALUES
                    (:id, :nome, :endereco, :estrelas, :cidade_id)
                """
            ).bindparams(
                id=uuid.uuid4(),
                nome=nome,
                endereco=endereco,
                estrelas=estrelas,
                cidade_id=cidade_id,
            )
        )


def downgrade() -> None:
    op.drop_table("hoteis")
    op.drop_table("cidades")
    op.drop_table("usuarios")