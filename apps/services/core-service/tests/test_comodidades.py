import uuid

from app.api.deps import get_current_admin, get_current_user
from app.main import app
from app.models.cidade import Cidade
from app.models.hotel import Hotel


ADMIN_USER = {"email": "admin@hotel.com", "nome": "Admin", "is_admin": True}
CLIENTE_USER = {"email": "cliente@hotel.com", "nome": "Cliente", "is_admin": False}


def _criar_hotel(db_session) -> Hotel:
    cidade = Cidade(nome="Quixadá", uf="CE")
    db_session.add(cidade)
    db_session.flush()

    hotel = Hotel(nome="Hotel Teste", endereco="Rua X, 1", estrelas=3, cidade_id=cidade.id)
    db_session.add(hotel)
    db_session.commit()
    db_session.refresh(hotel)
    return hotel


def test_listar_comodidades_e_publico(client):
    response = client.get("/api/v1/comodidades")
    assert response.status_code == 200
    assert response.json() == []


def test_criar_comodidade_sem_admin_returns_403(client):
    app.dependency_overrides[get_current_user] = lambda: CLIENTE_USER
    app.dependency_overrides[get_current_admin] = lambda: (_ for _ in ()).throw(
        __import__("fastapi").HTTPException(status_code=403, detail="Acesso restrito a administradores")
    )

    response = client.post("/api/v1/comodidades", json={"nome": "Wi-Fi"})
    assert response.status_code == 403
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_admin, None)


def test_criar_comodidade_como_admin_returns_201(client):
    app.dependency_overrides[get_current_admin] = lambda: ADMIN_USER

    response = client.post("/api/v1/comodidades", json={"nome": "Piscina"})
    assert response.status_code == 201
    assert response.json()["nome"] == "Piscina"

    app.dependency_overrides.pop(get_current_admin, None)


def test_criar_comodidade_duplicada_returns_409(client):
    app.dependency_overrides[get_current_admin] = lambda: ADMIN_USER

    client.post("/api/v1/comodidades", json={"nome": "Academia"})
    response = client.post("/api/v1/comodidades", json={"nome": "Academia"})
    assert response.status_code == 409

    app.dependency_overrides.pop(get_current_admin, None)


def test_definir_comodidades_do_hotel_returns_200(client, db_session):
    app.dependency_overrides[get_current_admin] = lambda: ADMIN_USER

    hotel = _criar_hotel(db_session)
    resp_comodidade = client.post("/api/v1/comodidades", json={"nome": "Café da manhã"})
    comodidade_id = resp_comodidade.json()["id"]

    response = client.put(
        f"/api/v1/hoteis/{hotel.id}/comodidades",
        json={"comodidade_ids": [comodidade_id]},
    )
    assert response.status_code == 200
    nomes = [c["nome"] for c in response.json()["comodidades"]]
    assert nomes == ["Café da manhã"]

    app.dependency_overrides.pop(get_current_admin, None)


def test_definir_comodidades_do_hotel_com_id_invalido_returns_404(client, db_session):
    app.dependency_overrides[get_current_admin] = lambda: ADMIN_USER

    hotel = _criar_hotel(db_session)
    response = client.put(
        f"/api/v1/hoteis/{hotel.id}/comodidades",
        json={"comodidade_ids": [str(uuid.uuid4())]},
    )
    assert response.status_code == 404

    app.dependency_overrides.pop(get_current_admin, None)