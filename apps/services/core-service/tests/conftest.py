
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db, get_mongo_db
from app.main import app
from app.models.tutorial import Base


# Banco SQLite separado para os testes.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    # Simula o MongoDB sem utilizar a conexao real.
    mongo_db_mock = MagicMock()
    colecao_mock = MagicMock()

    colecao_mock.bulk_write = AsyncMock()
    colecao_mock.delete_many = AsyncMock()
    colecao_mock.update_one = AsyncMock()
    colecao_mock.find_one = AsyncMock(return_value=None)

    mongo_db_mock.__getitem__.return_value = colecao_mock

    def override_get_mongo_db():
        return mongo_db_mock

    # Preserva os overrides existentes.
    overrides_anteriores = app.dependency_overrides.copy()

    # Utiliza SQLite e MongoDB simulado nos testes.
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_mongo_db] = override_get_mongo_db

    try:
        # Nao executa o lifespan da aplicacao.
        client = TestClient(
            app,
            raise_server_exceptions=False,
        )
        yield client
    finally:
        client.close()

        # Restaura a configuracao anterior.
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides_anteriores)
