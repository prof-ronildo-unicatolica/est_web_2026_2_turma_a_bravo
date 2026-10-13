from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.cidade import Cidade
from app.models.comodidades import Comodidade, hotel_comodidade
from app.models.quarto import Quarto
from app.models.tutorial import Base


class Hotel(Base):
    __tablename__ = "hoteis"
    __table_args__ = (
        CheckConstraint(
            "estrelas >= 1 AND estrelas <= 5",
            name="ck_hoteis_estrelas",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    endereco: Mapped[str] = mapped_column(String(150), nullable=False)
    estrelas: Mapped[int] = mapped_column(Integer, nullable=False)
    diaria: Mapped[str] = mapped_column(String(50), nullable=False, default="R$ 0")
    cidade_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cidades.id", ondelete="CASCADE"), nullable=False
    )

    cidade: Mapped[Cidade] = relationship(back_populates="hoteis")
    quartos: Mapped[list[Quarto]] = relationship(
        back_populates="hotel",
        cascade="all, delete-orphan",
    )
    comodidades: Mapped[list[Comodidade]] = relationship(
        secondary=hotel_comodidade,
        back_populates="hoteis",
    )

    @property
    def categoria_estrelas(self) -> str:
        """Categoria textual derivada do numero de estrelas."""
        if self.estrelas <= 2:
            return "Economico"

        if self.estrelas == 3:
            return "Padrao"

        return "Luxo"
