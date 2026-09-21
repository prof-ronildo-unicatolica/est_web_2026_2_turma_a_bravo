import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db

# Importa o model Hotel para que o SQLAlchemy reconheça
# o relacionamento entre Cidade e Hotel.
from app.models.hotel import Hotel  # noqa: F401

from app.repositories.cidade_repository import CidadeRepository
from app.schemas.cidade import (
    CidadeCreateSchema,
    CidadeResponseSchema,
    CidadeUpdateSchema,
)

router = APIRouter(prefix="/cidades", tags=["Cidades"])


@router.get("/", response_model=list[CidadeResponseSchema])
def listar_cidades(db: Session = Depends(get_db)):
    repository = CidadeRepository(db)
    return repository.list()


@router.get("/{cidade_id}", response_model=CidadeResponseSchema)
def buscar_cidade(
    cidade_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repository = CidadeRepository(db)
    cidade = repository.get_by_id(cidade_id)

    if cidade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cidade nao encontrada",
        )

    return cidade


@router.post(
    "/",
    response_model=CidadeResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def criar_cidade(
    payload: CidadeCreateSchema,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    repository = CidadeRepository(db)

    return repository.create(
        nome=payload.nome,
        uf=payload.uf.upper(),
        limite_territorial=payload.limite_territorial,
    )


@router.put("/{cidade_id}", response_model=CidadeResponseSchema)
def atualizar_cidade(
    cidade_id: uuid.UUID,
    payload: CidadeUpdateSchema,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    repository = CidadeRepository(db)
    cidade = repository.get_by_id(cidade_id)

    if cidade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cidade nao encontrada",
        )

    uf = payload.uf.upper() if payload.uf is not None else None

    return repository.update(
        cidade=cidade,
        nome=payload.nome,
        uf=uf,
        limite_territorial=payload.limite_territorial,
    )


@router.delete(
    "/{cidade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_cidade(
    cidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    repository = CidadeRepository(db)
    cidade = repository.get_by_id(cidade_id)

    if cidade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cidade nao encontrada",
        )

    repository.delete(cidade)
    return None