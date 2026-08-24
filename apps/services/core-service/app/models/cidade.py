from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.tutorial import Base

if TYPE_CHECKING:
    from app.models.hotel import Hotel

class Cidade(Base):
    __tablename__ = "cidades"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)

    hoteis: Mapped[List["Hotel"]] = relationship(  # noqa: F821
        back_populates="cidade", cascade="all, delete-orphan"
    )
