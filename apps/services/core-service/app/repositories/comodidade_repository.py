from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.comodidade import Comodidade
from app.models.hotel import Hotel


class ComodidadeRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self) -> list[Comodidade]:
        return self.db.query(Comodidade).order_by(Comodidade.nome).all()

    def obter_por_id(self, comodidade_id: uuid.UUID) -> Optional[Comodidade]:
        return (
            self.db.query(Comodidade)
            .filter(Comodidade.id == comodidade_id)
            .first()
        )

    def obter_por_nome(self, nome: str) -> Optional[Comodidade]:
        return self.db.query(Comodidade).filter(Comodidade.nome == nome).first()

    def criar(self, nome: str, descricao: Optional[str] = None) -> Comodidade:
        comodidade = Comodidade(nome=nome, descricao=descricao)
        self.db.add(comodidade)
        self.db.commit()
        self.db.refresh(comodidade)
        return comodidade

    def atualizar(self, comodidade: Comodidade, dados: dict) -> Comodidade:
        for campo, valor in dados.items():
            setattr(comodidade, campo, valor)
        self.db.commit()
        self.db.refresh(comodidade)
        return comodidade

    def excluir(self, comodidade: Comodidade) -> None:
        self.db.delete(comodidade)
        self.db.commit()

    def obter_hotel_com_comodidades(self, hotel_id: uuid.UUID) -> Optional[Hotel]:
        return (
            self.db.query(Hotel)
            .options(joinedload(Hotel.comodidades))
            .filter(Hotel.id == hotel_id)
            .first()
        )

    def definir_comodidades_do_hotel(
        self, hotel: Hotel, comodidades: list[Comodidade]
    ) -> Hotel:
        hotel.comodidades = comodidades
        self.db.commit()
        self.db.refresh(hotel)
        return hotel