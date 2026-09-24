from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.tutorial import Base

if TYPE_CHECKING:
    from app.models.hotel import Hotel


class Quarto(Base):
    __tablename__ = "quartos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    hotel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hoteis.id", ondelete="CASCADE"),
        nullable=False,
    )

    tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    preco_diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_adultos: Mapped[int] = mapped_column(Integer, nullable=False)
    max_criancas: Mapped[int] = mapped_column(Integer, nullable=False)

    hotel: Mapped["Hotel"] = relationship(back_populates="quartos")