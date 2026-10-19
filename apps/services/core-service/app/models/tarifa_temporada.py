
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.tutorial import Base


class TarifaTemporada(Base):
    __tablename__ = "tarifas_temporada"

    __table_args__ = (
        CheckConstraint(
            "data_fim >= data_inicio",
            name="ck_tarifas_temporada_periodo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    hotel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hoteis.id", ondelete="CASCADE"),
        nullable=False,
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    data_inicio: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    data_fim: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    percentual_ajuste: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
