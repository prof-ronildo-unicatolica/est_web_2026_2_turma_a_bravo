import uuid

from sqlalchemy.orm import Session

from app.models.cidade import Cidade


class CidadeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        nome: str,
        uf: str,
        limite_territorial: dict | None = None,
    ) -> Cidade:
        cidade = Cidade(
            nome=nome,
            uf=uf,
            limite_territorial=limite_territorial,
        )

        self.db.add(cidade)
        self.db.commit()
        self.db.refresh(cidade)

        return cidade

    def list(self) -> list[Cidade]:
        return self.db.query(Cidade).order_by(Cidade.nome).all()

    def get_by_id(self, cidade_id: uuid.UUID) -> Cidade | None:
        return self.db.query(Cidade).filter(Cidade.id == cidade_id).first()

    def update(
        self,
        cidade: Cidade,
        nome: str | None = None,
        uf: str | None = None,
        limite_territorial: dict | None = None,
    ) -> Cidade:
        if nome is not None:
            cidade.nome = nome

        if uf is not None:
            cidade.uf = uf

        if limite_territorial is not None:
            cidade.limite_territorial = limite_territorial

        self.db.commit()
        self.db.refresh(cidade)

        return cidade

    def delete(self, cidade: Cidade) -> None:
        self.db.delete(cidade)
        self.db.commit()
