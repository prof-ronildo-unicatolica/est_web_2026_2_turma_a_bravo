import uuid

from pydantic import BaseModel, ConfigDict, Field

class CidadeResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True) 

    id: uuid.UUID
    nome: str


class HotelCreateSchema(BaseModel):
    """O que o admin envia para cadastrar um hotel."""

    nome: str = Field(min_length=1, max_length=100)
    endereco: str = Field(min_length=1, max_length=150)
    estrelas: int = Field(ge=1, le=5)
    cidade_id: uuid.UUID


class HotelUpdateSchema(BaseModel):
    """Campos editaveis de um hotel. Todos opcionais (edicao parcial)."""

    nome: str | None = Field(default=None, min_length=1, max_length=100)
    endereco: str | None = Field(default=None, min_length=1, max_length=150)
    estrelas: int | None = Field(default=None, ge=1, le=5)
    cidade_id: uuid.UUID | None = None


class HotelResponseSchema(BaseModel):
    """O que a API devolve para cada hotel, incluindo a categoria calculada."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    endereco: str
    estrelas: int
    categoria_estrelas: str
    cidade_id: uuid.UUID