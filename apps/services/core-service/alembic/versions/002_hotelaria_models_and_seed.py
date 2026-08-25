
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
    op.create_index("ix_hoteis_cidade_id", "hoteis", ["cidade_id"])

    admin_id = uuid.uuid4()
    fortaleza_id = uuid.uuid4()
    quixada_id = uuid.uuid4()
    canoa_id = uuid.uuid4()

    usuarios_table = sa.table(
        "usuarios",
        sa.column("id", sa.UUID()),
        sa.column("nome", sa.String()),
        sa.column("email", sa.String()),
        sa.column("senha", sa.String()),
        sa.column("ativo", sa.Boolean()),
        sa.column("is_admin", sa.Boolean()),
    )

    cidades_table = sa.table(
        "cidades",
        sa.column("id", sa.UUID()),
        sa.column("nome", sa.String()),
        sa.column("uf", sa.String()),
    )

    hoteis_table = sa.table(
        "hoteis",
        sa.column("id", sa.UUID()),
        sa.column("nome", sa.String()),
        sa.column("endereco", sa.String()),
        sa.column("estrelas", sa.Integer()),
        sa.column("cidade_id", sa.UUID()),
    )

    # Usuário administrador
    # NOTA: senha em texto puro serve apenas para seed local de dev.
    # Se o model de usuário já usa hashing (bcrypt/passlib), troque por
    # senha=<hash>; nunca deve ir para produção como texto puro.
    op.bulk_insert(
        usuarios_table,
        [
            {
                "id": admin_id,
                "nome": "Administrador da Franquia",
                "email": "admin@hotel.com",
                "senha": "admin123",
                "ativo": True,
                "is_admin": True,
            }
        ],
    )

    # Cidades
    op.bulk_insert(
        cidades_table,
        [
            {"id": fortaleza_id, "nome": "Fortaleza", "uf": "CE"},
            {"id": quixada_id, "nome": "Quixadá", "uf": "CE"},
            {"id": canoa_id, "nome": "Canoa Quebrada", "uf": "CE"},
        ],
    )

    # Hotéis de 1 a 5 estrelas
    op.bulk_insert(
        hoteis_table,
        [
            {
                "id": uuid.uuid4(),
                "nome": "Hotel Econômico",
                "endereco": "Rua Central, 100",
                "estrelas": 1,
                "cidade_id": quixada_id,
            },
            {
                "id": uuid.uuid4(),
                "nome": "Hotel Sertão",
                "endereco": "Av. Principal, 200",
                "estrelas": 2,
                "cidade_id": quixada_id,
            },
            {
                "id": uuid.uuid4(),
                "nome": "Hotel Executivo",
                "endereco": "Av. Beira Mar, 300",
                "estrelas": 3,
                "cidade_id": fortaleza_id,
            },
            {
                "id": uuid.uuid4(),
                "nome": "Hotel Praia",
                "endereco": "Av. das Dunas, 400",
                "estrelas": 4,
                "cidade_id": canoa_id,
            },
            {
                "id": uuid.uuid4(),
                "nome": "Hotel Premium",
                "endereco": "Av. Beira Mar, 500",
                "estrelas": 5,
                "cidade_id": fortaleza_id,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_hoteis_cidade_id", table_name="hoteis")
    op.drop_table("hoteis")
    op.drop_table("cidades")
    op.drop_table("usuarios")