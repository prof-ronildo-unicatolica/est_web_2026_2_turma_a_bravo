import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.tutorial import Base


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
    ForeignKey("cidades.id"), nullable=False
  )
