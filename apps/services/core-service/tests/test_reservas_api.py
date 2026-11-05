
"""Testes da API de reservas - Sprint 6 com Transactional Outbox."""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from app.api.deps import get_current_user
from app.main import app
from app.models.cidade import Cidade
from app.models.hotel import Hotel
from app.models.quarto import Quarto
from app.models.reserva import Reserva
from app.models.evento_outbox import EventoOutbox


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


def _criar_quarto_teste(db_session):
    """Cria cidade, hotel e quarto com relacionamentos validos."""

    cidade = Cidade(
        id=uuid.uuid4(),
        nome="Banabuiu",
        uf="CE",
    )
    db_session.add(cidade)
    db_session.flush()

    hotel = Hotel(
        id=uuid.uuid4(),
        nome="Hotel Teste",
        endereco="Rua Principal, 100",
        estrelas=3,
        diaria="R$ 200",
        cidade_id=cidade.id,
    )
    db_session.add(hotel)
    db_session.flush()

    quarto = Quarto(
        id=uuid.uuid4(),
        hotel_id=hotel.id,
        tipo="Standard",
        preco_diaria=Decimal("200.00"),
        max_adultos=2,
        max_criancas=0,
    )
    db_session.add(quarto)
    db_session.commit()

    return quarto


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


def test_model_evento_outbox_possui_campos_necessarios(db_session):
    evento = EventoOutbox(
        reserva_id=uuid.uuid4(),
        fila="solicitacoes-reserva",
        payload={"reserva_id": str(uuid.uuid4())},
        status="Pendente",
        tentativas=0,
    )

    assert evento.fila == "solicitacoes-reserva"
    assert evento.status == "Pendente"
    assert evento.tentativas == 0
    assert isinstance(evento.payload, dict)


def test_reserva_e_outbox_na_mesma_transacao(client, db_session):
    """Confirma a persistencia conjunta da reserva e do evento."""

    _autenticar_cliente()
    quarto = _criar_quarto_teste(db_session)

    response = client.post(
        "/api/v1/reservas",
        json=_payload(quarto.id),
    )

    assert response.status_code == 202, response.text

    reservas = db_session.query(Reserva).all()
    eventos = db_session.query(EventoOutbox).all()

    assert len(reservas) == 1
    assert len(eventos) == 1

    reserva = reservas[0]
    evento = eventos[0]

    assert reserva.status == "Pendente"
    assert reserva.cliente_email == "cliente@hotel.com"

    assert evento.reserva_id == reserva.id
    assert evento.fila == "solicitacoes-reserva"
    assert evento.status == "Pendente"
    assert evento.tentativas == 0
    assert evento.payload["reserva_id"] == str(reserva.id)
    assert evento.payload["quarto_id"] == str(quarto.id)


def test_falha_na_transacao_retorna_503(client, db_session):
    """Confirma rollback quando o commit da reserva falha."""

    _autenticar_cliente()
    quarto = _criar_quarto_teste(db_session)

    with patch.object(
        db_session,
        "commit",
        side_effect=RuntimeError("Falha simulada no banco"),
    ):
        response = client.post(
            "/api/v1/reservas",
            json=_payload(quarto.id),
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Nao foi possivel registrar a reserva"
    )

    assert db_session.query(Reserva).count() == 0
    assert db_session.query(EventoOutbox).count() == 0
