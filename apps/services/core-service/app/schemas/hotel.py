import uuid

from pydantic import BaseModel, ConfigDict, Field

class CidadeResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str