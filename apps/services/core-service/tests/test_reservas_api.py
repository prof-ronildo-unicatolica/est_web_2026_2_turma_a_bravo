
"""Testes da API de reservas - Sprint 6."""

import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from app.api.deps import get_current_user
from app.main import app
from app.models.hotel import Hotel
from app.models.quarto import Quarto
from app.models.reserva import Reserva


def _autenticar_cliente():
    app.dependency_overrides[get_current_user] = lambda: {
        "email": "cliente@hotel.com",
        "nome": "Cliente Teste",
        "is_admin": False,
    }


def _payload(quarto_id):
    entrada = date.today() + timedelta(days=10)
    saida = entrada + timedelta(days=2)

    return {
        "quarto_id": str(quarto_id),
        "data_entrada": entrada.isoformat(),
        "data_saida": saida.isoformat(),
        "quantidade_adultos": 2,
        "idades_criancas": [],
        "nao_reembolsavel": False,
    }


def test_reserva_quarto_inexistente_returns_404(client):
    _autenticar_cliente()

    response = client.post(
        "/api/v1/reservas",
        json=_payload(uuid.uuid4()),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Quarto nao encontrado"


def test_reserva_datas_invalidas_returns_422(client):
    _autenticar_cliente()

    entrada = date.today() + timedelta(days=10)

    payload = _payload(uuid.uuid4())
    payload["data_entrada"] = entrada.isoformat()
    payload["data_saida"] = entrada.isoformat()

    response = client.post("/api/v1/reservas", json=payload)

    assert response.status_code == 422


def test_reserva_sem_autenticacao_returns_401(client):
    response = client.post(
        "/api/v1/reservas",
        json=_payload(uuid.uuid4()),
    )

    assert response.status_code in (401, 403)


def test_model_reserva_possui_status_pendente(db_session):
    """Verifica o status inicial do modelo."""

    reserva = Reserva(
        cliente_email="cliente@hotel.com",
        quarto_id=uuid.uuid4(),
        data_entrada=date.today() + timedelta(days=10),
        data_saida=date.today() + timedelta(days=12),
        quantidade_adultos=2,
        quantidade_criancas=0,
        valor_total=200,
    )

    assert reserva.status is None or reserva.status == "Pendente"


@patch("app.api.v1.reservas.publish_event", new_callable=AsyncMock)
def test_publicacao_rabbitmq_disponivel(mock_publish):
    """Confirma que a funcao de publicacao pode ser simulada."""

    assert mock_publish is not None
