import uuid

from pydantic import BaseModel, ConfigDict, Field


class CidadeCreateSchema(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    uf: str = Field(..., min_length=2, max_length=2)
    status: str | None = Field(default="Ativa")


class CidadeUpdateSchema(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    uf: str = Field(..., min_length=2, max_length=2)
    status: str | None = Field(default="Ativa")


class CidadeResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    uf: str
    hoteis: int = 0
    status: str = "Ativa"


class HotelCreateSchema(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    endereco: str = Field(..., min_length=2, max_length=150)
    estrelas: int = Field(..., ge=1, le=5)
    cidade_id: uuid.UUID
    status: str | None = Field(default="Ativo")
    diaria: str | None = Field(default="R$ 0")


class HotelUpdateSchema(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    endereco: str = Field(..., min_length=2, max_length=150)
    estrelas: int = Field(..., ge=1, le=5)
    cidade_id: uuid.UUID
    status: str | None = Field(default="Ativo")
    diaria: str | None = Field(default="R$ 0")


class HotelResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    endereco: str
    estrelas: int
    cidade_id: uuid.UUID
    cidade_nome: str | None = None
    status: str = "Ativo"
    diaria: str = "R$ 0"