
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
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

    # Preserva eventuais overrides anteriores.
    overrides_anteriores = app.dependency_overrides.copy()

    # Substitui o banco da API pelo SQLite de testes.
    app.dependency_overrides[get_db] = override_get_db

    try:
        # Nao executa o lifespan da aplicacao.
        # Assim os testes de API nao inicializam o MongoDB
        # nem executam a sincronizacao com PostgreSQL.
        client = TestClient(
            app,
            raise_server_exceptions=False,
        )
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides_anteriores)
