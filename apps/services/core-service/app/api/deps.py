"""Dependencias de autenticacao e autorizacao."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.core.security import decode_access_token, hash_password, verify_password

# Fonte de usuarios provisoria; as senhas continuam armazenadas somente como hash.
USUARIOS_DEMO = {
    "admin@hotel.com": {
        "nome": "Administrador da Franquia",
        "senha_hash": hash_password("admin123"),
        "is_admin": True,
    },
    "cliente@hotel.com": {
        "nome": "Cliente Demonstracao",
        "senha_hash": hash_password("cliente123"),
        "is_admin": False,
    },
}

bearer_scheme = HTTPBearer(description="Use o token retornado por POST /auth/login")


def autenticar_credenciais(email: str, senha: str) -> dict | None:
    """Confere e-mail e senha usando o hash bcrypt armazenado."""
    usuario = USUARIOS_DEMO.get(email)
    if usuario is None or not verify_password(senha, usuario["senha_hash"]):
        return None
    return {
        "email": email,
        "nome": usuario["nome"],
        "is_admin": usuario["is_admin"],
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Valida o JWT e retorna os dados do usuario autenticado."""
    try:
        payload = decode_access_token(credentials.credentials)
        email = payload.get("sub")
    except InvalidTokenError:
        email = None

    usuario = USUARIOS_DEMO.get(email)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "email": email,
        "nome": usuario["nome"],
        "is_admin": usuario["is_admin"],
    }


def get_current_admin(usuario: dict = Depends(get_current_user)) -> dict:
    """Exige que o usuario autenticado tenha permissao administrativa."""
    if not usuario["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return usuario
