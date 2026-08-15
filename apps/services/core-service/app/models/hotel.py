import uuid

from sqllchemy import Foreignkey, String
from slqalchemy.orm import Mapped, mapped_column

form app.models.tutorial import Base


class Hotel(Base):
  __tablename__ = "hoteis"
  
  id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
  nome: Mapped[str] = mapped_column(String(100), nullable=False)
  endereco: Mapped[str] = mapped_column(String(150), nullable=False)
  cidade_id: Mapped[uuid.UUID] = mapped_column(
    Foreignkey("cidades.id"), nullable=False
  )
