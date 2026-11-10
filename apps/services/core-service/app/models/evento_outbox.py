
"""Modelo de eventos pendentes para publicação no RabbitMQ - Sprint 6."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.tutorial import Base


class EventoOutbox(Base):
    """Armazena eventos para publicação assíncrona confiável."""

    __tablename__ = "eventos_outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    reserva_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reservas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fila: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="solicitacoes-reserva",
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Pendente",
        index=True,
    )

    tentativas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    ultimo_erro: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    publicado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
