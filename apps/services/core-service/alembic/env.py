
"""Configuração das migrações do banco de dados com Alembic."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Configurações da aplicação
from app.core.config import settings

# Modelos registrados no SQLAlchemy
from app.models.cidade import Cidade  # noqa: F401
from app.models.hotel import Hotel  # noqa: F401
from app.models.tarifa_temporada import TarifaTemporada  # noqa: F401
from app.models.servico_adicional import ServicoAdicional  # noqa: F401
from app.models.reserva import Reserva  # noqa: F401
from app.models.evento_outbox import EventoOutbox  # noqa: F401
from app.models.tutorial import Base
from app.models.usuario import Usuario  # noqa: F401

# Configuração do Alembic
config = context.config

# Configuração dos logs
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# URL do PostgreSQL
config.set_main_option(
    "sqlalchemy.url",
    settings.SQLALCHEMY_DATABASE_URI,
)

# Metadados utilizados nas migrações
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrações sem conexão direta com o banco."""
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrações com conexão ao banco."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
