"""Rotas de autenticacao/autorizacao.

⚠️ /login, /me e /admin/verificacao ainda usam a versao BASICA (placeholder,
sem JWT, se apoiando em app.api.deps). /register ja usa a tabela real
`usuarios` do PostgreSQL, com senha em hash bcrypt.

A versao completa (JWT + login/me via banco) e a ATIVIDADE DA SPRINT 2:
    docs/02_engenharia_software/atividade_auth_sprint2.md
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import autenticar_credenciais, get_current_admin, get_current_user
from app.core.database import get_db
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, Token, UsuarioCreate, UsuarioPublic

router = APIRouter(prefix="/auth", tags=["Auth (basico)"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest):
    """Login basico: valida as credenciais e devolve um 'token'."""
    usuario = autenticar_credenciais(payload.email, payload.senha)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )
    # VERSAO BASICA: o "token" e apenas o e-mail. Na Sprint 2 sera um JWT.
    return Token(access_token=usuario["email"])


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
