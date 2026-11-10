
"""Modelo de reserva para o PostgreSQL - Sprint 6."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.tutorial import Base


class Reserva(Base):
    """Reserva criada como Pendente e processada pelo worker."""

    __tablename__ = "reservas"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    cliente_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    quarto_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quartos.id"),
        nullable=False,
        index=True,
    )

    data_entrada: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    data_saida: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    quantidade_adultos: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    quantidade_criancas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    valor_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Pendente",
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    quarto = relationship("Quarto")
