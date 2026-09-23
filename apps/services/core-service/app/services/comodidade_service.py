from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.comodidade_repository import ComodidadeRepository
from app.schemas.comodidade import ComodidadeCreateSchema, ComodidadeUpdateSchema


class ComodidadeService:
    def __init__(self, db: Session):
        self.repository = ComodidadeRepository(db)

    def listar(self):
        return self.repository.listar()

    def obter_por_id(self, comodidade_id: uuid.UUID):
        comodidade = self.repository.obter_por_id(comodidade_id)
        if comodidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comodidade nao encontrada",
            )
        return comodidade

    def criar(self, payload: ComodidadeCreateSchema):
        if self.repository.obter_por_nome(payload.nome):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ja existe uma comodidade com esse nome",
            )
        return self.repository.criar(nome=payload.nome, descricao=payload.descricao)

    def atualizar(self, comodidade_id: uuid.UUID, payload: ComodidadeUpdateSchema):
        comodidade = self.obter_por_id(comodidade_id)
        dados = payload.model_dump(exclude_unset=True)

        novo_nome = dados.get("nome")
        if novo_nome:
            existente = self.repository.obter_por_nome(novo_nome)
            if existente and existente.id != comodidade.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ja existe uma comodidade com esse nome",
                )

        return self.repository.atualizar(comodidade, dados)

    def excluir(self, comodidade_id: uuid.UUID) -> None:
        comodidade = self.obter_por_id(comodidade_id)
        self.repository.excluir(comodidade)


    def listar_comodidades_do_hotel(self, hotel_id: uuid.UUID):
        hotel = self.repository.obter_hotel_com_comodidades(hotel_id)
        if hotel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Hotel nao encontrado"
            )
        return hotel

    def definir_comodidades_do_hotel(
        self, hotel_id: uuid.UUID, comodidade_ids: list[uuid.UUID]
    ):
        hotel = self.repository.obter_hotel_com_comodidades(hotel_id)
        if hotel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Hotel nao encontrado"
            )

        comodidades = []
        for comodidade_id in comodidade_ids:
            comodidade = self.repository.obter_por_id(comodidade_id)
            if comodidade is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Comodidade {comodidade_id} nao encontrada",
                )
            comodidades.append(comodidade)

        return self.repository.definir_comodidades_do_hotel(hotel, comodidades)