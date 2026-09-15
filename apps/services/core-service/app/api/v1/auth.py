"""Rotas de autenticacao/autorizacao.

/login gera um JWT de acesso apos validar as credenciais.
/me retorna o perfil do usuario autenticado via token.
/register cadastra um novo usuario, salvando a senha em hash bcrypt.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import autenticar_credenciais, get_current_admin, get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, Token, UsuarioCreate, UsuarioPublic

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


@router.post("/register", response_model=UsuarioPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UsuarioCreate, db: Session = Depends(get_db)):
    """Cadastra um novo usuario com senha em hash (bcrypt)."""
    # Verifica e-mail duplicado
    usuario_existente = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if usuario_existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail ja cadastrado",
        )

    novo_usuario = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha=hash_password(payload.senha),
        is_admin=False,
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return novo_usuario
