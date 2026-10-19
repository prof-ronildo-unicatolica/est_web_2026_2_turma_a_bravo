
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TipoCobranca = Literal[
    "por_pessoa_dia",
    "por_diaria",
    "por_servico",
]


class ServicoAdicionalCreateSchema(BaseModel):
    hotel_id: uuid.UUID
    nome: str = Field(min_length=1, max_length=100)
    descricao: str | None = Field(default=None, max_length=255)
    preco: Decimal = Field(ge=0, decimal_places=2)
    tipo_cobranca: TipoCobranca


class ServicoAdicionalUpdateSchema(BaseModel):
    hotel_id: uuid.UUID | None = None
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = Field(default=None, max_length=255)
    preco: Decimal | None = Field(
        default=None, ge=0, decimal_places=2
    )
    tipo_cobranca: TipoCobranca | None = None


class ServicoAdicionalResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hotel_id: uuid.UUID
    nome: str
    descricao: str | None
    preco: Decimal
    tipo_cobranca: TipoCobranca
