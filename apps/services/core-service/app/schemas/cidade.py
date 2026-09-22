import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CidadeCreateSchema(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    uf: str = Field(min_length=2, max_length=2)
    limite_territorial: dict[str, Any] | None = None


class CidadeUpdateSchema(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    uf: str | None = Field(default=None, min_length=2, max_length=2)
    limite_territorial: dict[str, Any] | None = None


class CidadeResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    uf: str
    limite_territorial: dict[str, Any] | None = None
