from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.tutorial import Base
from app.models.comodidade import hotel_comodidade

if TYPE_CHECKING:
    from app.models.cidade import Cidade
    from app.models.comodidade import Comodidade

class Hotel(Base):
    __tablename__ = "hoteis"
    __table_args__ = (
        CheckConstraint("estrelas >= 1 AND estrelas <= 5", name="ck_hoteis_estrelas"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    endereco: Mapped[str] = mapped_column(String(150), nullable=False)
    estrelas: Mapped[int] = mapped_column(Integer, nullable=False)

    cidade_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cidades.id", ondelete="CASCADE"), nullable=False
    )

    cidade: Mapped["Cidade"] = relationship(back_populates="hoteis")  # noqa: F821

    comodidades: Mapped[List["Comodidade"]] = relationship(  # noqa: F821
        secondary=hotel_comodidade, back_populates="hoteis"
    )

    @property
    def categoria_estrelas(self) -> str:
        """Categoria textual derivada do numero de estrelas.

        Nao e uma coluna do banco -- e calculada em Python a partir de
        `estrelas`, entao nao precisa de migration nem ocupa espaco extra.
        """
        if self.estrelas <= 2:
            return "Economico"
        if self.estrelas == 3:
            return "Padrao"
        return "Luxo"
