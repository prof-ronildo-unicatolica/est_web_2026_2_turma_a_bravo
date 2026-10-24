def test_listar_tarifas_temporada(client):
    response = client.get("/api/v1/tarifas-temporada")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_criar_tarifa_temporada(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@hotel.com", "senha": "admin123"},
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cidade = client.post(
        "/api/v1/cidades",
        json={"nome": "Fortaleza", "uf": "CE"},
    )
    assert cidade.status_code == 201

    hotel = client.post(
        "/api/v1/hoteis",
        json={
            "nome": "Hotel Praia",
            "cidade_id": cidade.json()["id"],
            "endereco": "Av. Beira Mar, 100",
            "estrelas": 4,
            "diaria": "R$ 300",
        },
    )
    assert hotel.status_code == 201

    tarifa = client.post(
        "/api/v1/tarifas-temporada",
        headers=headers,
        json={
            "hotel_id": hotel.json()["id"],
            "nome": "Alta Temporada",
            "data_inicio": "2026-12-01",
            "data_fim": "2026-12-31",
            "percentual_ajuste": "20.00",
        },
    )

    assert tarifa.status_code == 201, tarifa.text
    assert tarifa.json()["nome"] == "Alta Temporada"
    assert tarifa.json()["percentual_ajuste"] == "20.00"

def test_consultar_tarifa_inexistente(client):
    tarifa_id = "00000000-0000-0000-0000-000000000001"

    response = client.get(
        f"/api/v1/tarifas-temporada/{tarifa_id}"
    )

    assert response.status_code == 404


def test_atualizar_tarifa_temporada(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@hotel.com", "senha": "admin123"},
    )
    assert login.status_code == 200
    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    cidade = client.post(
        "/api/v1/cidades",
        json={"nome": "Quixada", "uf": "CE"},
    )
    assert cidade.status_code == 201

    hotel = client.post(
        "/api/v1/hoteis",
        json={
            "nome": "Hotel Central",
            "cidade_id": cidade.json()["id"],
            "endereco": "Rua Principal, 100",
            "estrelas": 3,
            "diaria": "R$ 200",
        },
    )
    assert hotel.status_code == 201

    tarifa = client.post(
        "/api/v1/tarifas-temporada",
        headers=headers,
        json={
            "hotel_id": hotel.json()["id"],
            "nome": "Temporada Inicial",
            "data_inicio": "2026-12-01",
            "data_fim": "2026-12-31",
            "percentual_ajuste": "10.00",
        },
    )
    assert tarifa.status_code == 201

    tarifa_id = tarifa.json()["id"]

    atualizacao = client.put(
        f"/api/v1/tarifas-temporada/{tarifa_id}",
        headers=headers,
        json={
            "nome": "Alta Temporada Atualizada",
            "percentual_ajuste": "25.00",
        },
    )

    assert atualizacao.status_code == 200, atualizacao.text
    assert atualizacao.json()["nome"] == "Alta Temporada Atualizada"
    assert atualizacao.json()["percentual_ajuste"] == "25.00"


def test_excluir_tarifa_temporada(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@hotel.com", "senha": "admin123"},
    )
    assert login.status_code == 200
    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    cidade = client.post(
        "/api/v1/cidades",
        json={"nome": "Banabuiu", "uf": "CE"},
    )
    assert cidade.status_code == 201

    hotel = client.post(
        "/api/v1/hoteis",
        json={
            "nome": "Hotel Sertao",
            "cidade_id": cidade.json()["id"],
            "endereco": "Rua Central, 100",
            "estrelas": 3,
            "diaria": "R$ 180",
        },
    )
    assert hotel.status_code == 201

    tarifa = client.post(
        "/api/v1/tarifas-temporada",
        headers=headers,
        json={
            "hotel_id": hotel.json()["id"],
            "nome": "Temporada Especial",
            "data_inicio": "2026-11-01",
            "data_fim": "2026-11-30",
            "percentual_ajuste": "15.00",
        },
    )
    assert tarifa.status_code == 201

    tarifa_id = tarifa.json()["id"]

    exclusao = client.delete(
        f"/api/v1/tarifas-temporada/{tarifa_id}",
        headers=headers,
    )
    assert exclusao.status_code == 204

    consulta = client.get(
        f"/api/v1/tarifas-temporada/{tarifa_id}"
    )
    assert consulta.status_code == 404


def test_tarifa_com_periodo_invalido(client):
    response = client.post(
        "/api/v1/tarifas-temporada",
        json={
            "hotel_id": "00000000-0000-0000-0000-000000000001",
            "nome": "Periodo Invalido",
            "data_inicio": "2026-12-31",
            "data_fim": "2026-12-01",
            "percentual_ajuste": "20.00",
        },
    )

    assert response.status_code in (401, 403)

def test_rejeitar_tarifa_com_datas_invalidas(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@hotel.com", "senha": "admin123"},
    )
    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/tarifas-temporada",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "hotel_id": "00000000-0000-0000-0000-000000000001",
            "nome": "Periodo Invalido",
            "data_inicio": "2026-12-31",
            "data_fim": "2026-12-01",
            "percentual_ajuste": "20.00",
        },
    )

    assert response.status_code == 422, response.text


def test_rejeitar_tarifas_com_periodos_sobrepostos(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@hotel.com", "senha": "admin123"},
    )
    assert login.status_code == 200

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    cidade = client.post(
        "/api/v1/cidades",
        json={"nome": "Quixeramobim", "uf": "CE"},
    )
    assert cidade.status_code == 201

    hotel = client.post(
        "/api/v1/hoteis",
        json={
            "nome": "Hotel Central",
            "cidade_id": cidade.json()["id"],
            "endereco": "Rua Principal, 100",
            "estrelas": 3,
            "diaria": "R$ 200",
        },
    )
    assert hotel.status_code == 201

    hotel_id = hotel.json()["id"]

    primeira = client.post(
        "/api/v1/tarifas-temporada",
        headers=headers,
        json={
            "hotel_id": hotel_id,
            "nome": "Alta Temporada",
            "data_inicio": "2026-12-01",
            "data_fim": "2026-12-20",
            "percentual_ajuste": "20.00",
        },
    )
    assert primeira.status_code == 201

    segunda = client.post(
        "/api/v1/tarifas-temporada",
        headers=headers,
        json={
            "hotel_id": hotel_id,
            "nome": "Natal",
            "data_inicio": "2026-12-15",
            "data_fim": "2026-12-31",
            "percentual_ajuste": "30.00",
        },
    )

    assert segunda.status_code == 409, segunda.text