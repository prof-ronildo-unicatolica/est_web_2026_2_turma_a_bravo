from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.tutorial import Base

if TYPE_CHECKING:
    from app.models.hotel import Hotel

hotel_comodidade = Table(
    "hotel_comodidade",
    Base.metadata,
    Column(
        "hotel_id",
        ForeignKey("hoteis.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "comodidade_id",
        ForeignKey("comodidades.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Comodidade(Base):
    __tablename__ = "comodidades"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=True)

    hoteis: Mapped[List["Hotel"]] = relationship(  # noqa: F821
        secondary=hotel_comodidade, back_populates="comodidades"
    )