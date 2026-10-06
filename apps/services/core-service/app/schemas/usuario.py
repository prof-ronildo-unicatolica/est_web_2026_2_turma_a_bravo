from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str
    senha: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioPublic(BaseModel):
    """Perfil publico do usuario (nunca expoe senha)."""
    model_config = ConfigDict(from_attributes=True)

    email: str
    nome: str
    is_admin: bool


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=100)
    senha: str = Field(min_length=6, max_length=100)
