from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password():
    senha = "senha123"
    senha_hash = hash_password(senha)

    assert senha_hash != senha


def test_verify_password():
    senha = "senha123"
    senha_hash = hash_password(senha)

    assert verify_password(senha, senha_hash) is True
    assert verify_password("senha_errada", senha_hash) is False


def test_create_access_token():
    token = create_access_token({"sub": "123"})

    assert isinstance(token, str)
    assert token


def test_decode_access_token():
    token = create_access_token({"sub": "123"})
    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert "exp" in payload