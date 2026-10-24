
import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.tutorial import Base


class ServicoAdicional(Base):
    __tablename__ = "servicos_adicionais"

    __table_args__ = (
        CheckConstraint(
            "preco >= 0",
            name="ck_servicos_adicionais_preco",
        ),
        CheckConstraint(
            "tipo_cobranca IN ('por_pessoa_dia', 'por_diaria', 'por_servico')",
            name="ck_servicos_adicionais_tipo_cobranca",
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

    descricao: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    preco: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    tipo_cobranca: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
