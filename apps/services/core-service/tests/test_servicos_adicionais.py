def test_listar_servicos_adicionais(client):
    response = client.get("/api/v1/servicos-adicionais")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_criar_servico_adicional(client):
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
            "nome": "Hotel Central",
            "cidade_id": cidade.json()["id"],
            "endereco": "Rua Principal, 100",
            "estrelas": 3,
            "diaria": "R$ 200",
        },
    )
    assert hotel.status_code == 201

    servico = client.post(
        "/api/v1/servicos-adicionais",
        headers=headers,
        json={
            "hotel_id": hotel.json()["id"],
            "nome": "Cafe da Manha",
            "descricao": "Cafe da manha completo",
            "preco": "25.00",
            "tipo_cobranca": "por_pessoa_dia",
        },
    )

    assert servico.status_code == 201, servico.text
    assert servico.json()["nome"] == "Cafe da Manha"
    assert float(servico.json()["preco"]) == 25.00


def test_consultar_servico_inexistente(client):
    response = client.get(
        "/api/v1/servicos-adicionais/00000000-0000-0000-0000-000000000001"
    )

    assert response.status_code == 404


def test_atualizar_servico_adicional(client):
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
            "nome": "Hotel Quixada",
            "cidade_id": cidade.json()["id"],
            "endereco": "Rua Central, 200",
            "estrelas": 3,
            "diaria": "R$ 180",
        },
    )
    assert hotel.status_code == 201

    servico = client.post(
        "/api/v1/servicos-adicionais",
        headers=headers,
        json={
            "hotel_id": hotel.json()["id"],
            "nome": "Cafe da Manha",
            "descricao": "Cafe completo",
            "preco": "25.00",
            "tipo_cobranca": "por_pessoa_dia",
        },
    )
    assert servico.status_code == 201

    servico_id = servico.json()["id"]

    atualizacao = client.put(
        f"/api/v1/servicos-adicionais/{servico_id}",
        headers=headers,
        json={
            "nome": "Cafe da Manha Especial",
            "preco": "35.00",
        },
    )

    assert atualizacao.status_code == 200, atualizacao.text
    assert atualizacao.json()["nome"] == "Cafe da Manha Especial"
    assert float(atualizacao.json()["preco"]) == 35.00


def test_excluir_servico_adicional(client):
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

    servico = client.post(
        "/api/v1/servicos-adicionais",
        headers=headers,
        json={
            "hotel_id": hotel.json()["id"],
            "nome": "Estacionamento",
            "descricao": "Vaga de estacionamento",
            "preco": "20.00",
            "tipo_cobranca": "por_diaria",
        },
    )
    assert servico.status_code == 201

    servico_id = servico.json()["id"]

    exclusao = client.delete(
        f"/api/v1/servicos-adicionais/{servico_id}",
        headers=headers,
    )
    assert exclusao.status_code == 204

    consulta = client.get(
        f"/api/v1/servicos-adicionais/{servico_id}"
    )
    assert consulta.status_code == 404

def test_rejeitar_servico_com_preco_negativo(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@hotel.com", "senha": "admin123"},
    )
    assert login.status_code == 200

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    response = client.post(
        "/api/v1/servicos-adicionais",
        headers=headers,
        json={
            "hotel_id": "00000000-0000-0000-0000-000000000001",
            "nome": "Estacionamento",
            "preco": "-10.00",
            "tipo_cobranca": "por_diaria",
        },
    )

    assert response.status_code == 422, response.text


def test_cliente_nao_pode_criar_servico(client):
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "cliente@hotel.com",
            "senha": "cliente123",
        },
    )
    assert login.status_code == 200

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    response = client.post(
        "/api/v1/servicos-adicionais",
        headers=headers,
        json={
            "hotel_id": "00000000-0000-0000-0000-000000000001",
            "nome": "Lavanderia",
            "preco": "30.00",
            "tipo_cobranca": "por_servico",
        },
    )

    assert response.status_code == 403, response.text