import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ComodidadeBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str = Field(..., min_length=1, max_length=80)
    descricao: Optional[str] = Field(None, max_length=255)


class ComodidadeCreateSchema(ComodidadeBaseSchema):
    pass


class ComodidadeUpdateSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    nome: Optional[str] = Field(None, min_length=1, max_length=80)
    descricao: Optional[str] = Field(None, max_length=255)


class ComodidadeResponseSchema(ComodidadeBaseSchema):
    id: uuid.UUID


class HotelComodidadesUpdateSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    comodidade_ids: List[uuid.UUID]


class HotelComComodidadesResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    comodidades: List[ComodidadeResponseSchema]