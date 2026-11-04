
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReservaCreateSchema(BaseModel):
    """Dados enviados pelo cliente para solicitar uma reserva."""

    quarto_id: uuid.UUID
    data_entrada: date
    data_saida: date
    quantidade_adultos: int = Field(ge=1)
    idades_criancas: list[int] = Field(default_factory=list)
    nao_reembolsavel: bool = False
    horario_checkin: time | None = None
    horario_checkout: time | None = None

    @model_validator(mode="after")
    def validar_reserva(self):
        if self.data_entrada < date.today():
            raise ValueError("A data de entrada nao pode estar no passado")

        if self.data_saida <= self.data_entrada:
            raise ValueError(
                "A data de saida deve ser posterior a data de entrada"
            )

        if any(idade < 0 or idade >= 18 for idade in self.idades_criancas):
            raise ValueError(
                "As idades das criancas devem estar entre 0 e 17 anos"
            )

        return self


class ReservaResponseSchema(BaseModel):
    """Dados retornados pela API ao registrar uma solicitacao."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quarto_id: uuid.UUID
    data_entrada: date
    data_saida: date
    quantidade_adultos: int
    quantidade_criancas: int
    valor_total: Decimal
    status: str
    criado_em: datetime
