"""Rotas de autenticacao e autorizacao."""
"login e usuario logado"

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import autenticar_credenciais, get_current_admin, get_current_user
from app.core.security import create_access_token
from app.schemas.usuario import LoginRequest, Token, UsuarioPublic

router = APIRouter(prefix="/auth", tags=["Auth (basico)"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest):
    """Valida as credenciais e devolve um JWT de acesso."""
    usuario = autenticar_credenciais(payload.email, payload.senha)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )
    return Token(access_token=create_access_token({"sub": usuario["email"]}))


@router.get("/me", response_model=UsuarioPublic)
def get_me(usuario_atual: dict = Depends(get_current_user)):
    """Rota protegida: retorna o perfil do usuario autenticado."""
    return usuario_atual


@router.get("/admin/verificacao")
def somente_admin(admin: dict = Depends(get_current_admin)):
    """Rota administrativa de exemplo (autorizacao por is_admin)."""
    return {"mensagem": f"Acesso administrativo concedido para {admin['nome']}"}
