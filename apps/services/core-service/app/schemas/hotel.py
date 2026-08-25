import uuid

from pydantic import BaseModel, ConfigDict, Field


class CidadeCreateSchema(BaseModel):
    """O que o cliente envia em POST /cidades.

    Nao tem 'id': quem gera o identificador e o servidor.
    """

    # min_length=1 barra string vazia; sem isso, {"nome": ""} passaria e
    # criaria uma cidade sem nome. O banco aceita '' -- ele so recusa NULL.
    nome: str = Field(min_length=1, max_length=100)


class CidadeResponseSchema(BaseModel):
    """O que a API devolve. Aqui o 'id' e obrigatorio: sem ele o frontend
    nao consegue vincular um hotel a esta cidade depois."""

    # from_attributes: permite construir o schema a partir de um objeto do
    # SQLAlchemy (lendo atributos), e nao so a partir de um dict.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str