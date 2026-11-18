
"""Testes da Sprint 7 - Listagem e consulta de reservas."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.api.deps import get_current_user
from app.main import app
from app.models.reserva import Reserva
from app.models.cidade import Cidade
from app.models.hotel import Hotel
from app.models.quarto import Quarto


def autenticar(email="cliente@hotel.com"):
    """Simula um usuario autenticado."""
    app.dependency_overrides[get_current_user] = lambda: {
        "email": email,
        "nome": "Cliente Teste",
        "is_admin": False,
    }


def criar_quarto_teste(db_session):
    """Cria cidade, hotel e quarto para os testes."""
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


def criar_reserva(db_session, quarto_id, email="cliente@hotel.com"):
    """Cria uma reserva para os testes."""
    entrada = date.today() + timedelta(days=10)

    reserva = Reserva(
        id=uuid.uuid4(),
        cliente_email=email,
        quarto_id=quarto_id,
        data_entrada=entrada,
        data_saida=entrada + timedelta(days=2),
        quantidade_adultos=2,
        quantidade_criancas=0,
        valor_total=Decimal("400.00"),
        status="Pendente",
    )

    db_session.add(reserva)
    db_session.commit()
    db_session.refresh(reserva)

    return reserva


def test_listar_reservas_vazio(client):
    autenticar()

    response = client.get("/api/v1/reservas")

    assert response.status_code == 200
    assert response.json() == []


def test_listar_somente_reservas_do_usuario(client, db_session):
    autenticar()

    quarto = criar_quarto_teste(db_session)

    criar_reserva(db_session, quarto.id, "cliente@hotel.com")
    criar_reserva(db_session, quarto.id, "outro@hotel.com")

    response = client.get("/api/v1/reservas")

    assert response.status_code == 200
    dados = response.json()
    assert len(dados) == 1
    assert dados[0]["status"] == "Pendente"


def test_consultar_reserva_existente(client, db_session):
    autenticar()

    quarto = criar_quarto_teste(db_session)
    reserva = criar_reserva(db_session, quarto.id)

    response = client.get(f"/api/v1/reservas/{reserva.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(reserva.id)


def test_impedir_consulta_de_outro_usuario(client, db_session):
    autenticar("cliente@hotel.com")

    quarto = criar_quarto_teste(db_session)
    reserva = criar_reserva(
        db_session, quarto.id, "outro@hotel.com"
    )

    response = client.get(f"/api/v1/reservas/{reserva.id}")

    assert response.status_code == 404


def test_reserva_inexistente_retorna_404(client):
    autenticar()

    response = client.get(
        f"/api/v1/reservas/{uuid.uuid4()}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Reserva nao encontrada"


def test_listar_reservas_sem_autenticacao(client):
    response = client.get("/api/v1/reservas")

    assert response.status_code in (401, 403)
