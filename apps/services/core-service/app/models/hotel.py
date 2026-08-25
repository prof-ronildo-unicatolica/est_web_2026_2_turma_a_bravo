from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

# A MESMA Base do restante do projeto. Nao crie outra: uma segunda Base
# significa um segundo registro de metadados, e o Alembic nao enxergaria
# estas tabelas -- em silencio, sem erro.
from app.models.tutorial import Base

if TYPE_CHECKING:
    from app.models.cidade import Cidade

class Cidade(Base):
    __tablename__ = "cidades"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # unique=True: sem estado/UF no modelo, duas linhas "Fortaleza" seriam
    # indistinguiveis para quem for pendurar um hotel (decisao 5.3 da issue #18).
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Lado 1 da relacao: uma cidade tem VARIOS hoteis.
    # Nao vira coluna nenhuma no banco -- e navegacao em Python.
    hoteis: Mapped[List["Hotel"]] = relationship(
        back_populates="cidade", cascade="all, delete-orphan"
    )


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
