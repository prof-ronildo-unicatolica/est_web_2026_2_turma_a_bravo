
import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TarifaTemporadaCreateSchema(BaseModel):
    hotel_id: uuid.UUID
    nome: str = Field(min_length=1, max_length=100)
    data_inicio: date
    data_fim: date
    percentual_ajuste: Decimal = Field(ge=-100, le=999.99, decimal_places=2)

    @model_validator(mode="after")
    def validar_periodo(self):
        if self.data_fim < self.data_inicio:
            raise ValueError("A data final não pode ser anterior à inicial.")
        return self


class TarifaTemporadaUpdateSchema(BaseModel):
    hotel_id: uuid.UUID | None = None
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    data_inicio: date | None = None
    data_fim: date | None = None
    percentual_ajuste: Decimal | None = Field(
        default=None, ge=-100, le=999.99, decimal_places=2
    )


class TarifaTemporadaResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hotel_id: uuid.UUID
    nome: str
    data_inicio: date
    data_fim: date
    percentual_ajuste: Decimal
