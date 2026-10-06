def test_criar_e_listar_cidades(client):
    payload = {"nome": "Recife", "uf": "PE"}

    response = client.post("/api/v1/cidades", json=payload)
    assert response.status_code == 201
    assert response.json()["nome"] == "Recife"
    assert response.json()["uf"] == "PE"

    response = client.get("/api/v1/cidades")
    assert response.status_code == 200
    assert any(item["nome"] == "Recife" for item in response.json())


def test_criar_e_listar_hoteis(client):
    cidade_response = client.post("/api/v1/cidades", json={"nome": "Natal", "uf": "RN"})
    cidade_id = cidade_response.json()["id"]

    payload = {
        "nome": "Hotel do Sol",
        "endereco": "Av. das Dunas, 200",
        "estrelas": 4,
        "cidade_id": cidade_id,
        "diaria": "R$ 420",
    }

    response = client.post("/api/v1/hoteis", json=payload)
    assert response.status_code == 201
    assert response.json()["nome"] == "Hotel do Sol"
    assert response.json()["diaria"] == "R$ 420"

    response = client.get("/api/v1/hoteis")
    assert response.status_code == 200
    assert any(item["nome"] == "Hotel do Sol" and item["diaria"] == "R$ 420" for item in response.json())
