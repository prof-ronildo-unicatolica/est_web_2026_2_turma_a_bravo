"""Rotas de CRUD de quartos.

A listagem (GET /quartos e GET /quartos/{id}) e publica.
Cadastrar, editar e excluir exigem permissao de administrador (is_admin).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.hotel import Hotel
from app.models.quarto import Quarto
from app.schemas.quarto import (
    QuartoCreateSchema,
    QuartoResponseSchema,
    QuartoUpdateSchema,
)

router = APIRouter(prefix="/quartos", tags=["Quartos"])


def _buscar_quarto_ou_404(quarto_id: uuid.UUID, db: Session) -> Quarto:
    quarto = db.query(Quarto).filter(Quarto.id == quarto_id).first()

    if quarto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quarto nao encontrado",
        )

    return quarto


def _verificar_hotel(hotel_id: uuid.UUID, db: Session) -> None:
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hotel informado nao existe",
        )


@router.get("", response_model=list[QuartoResponseSchema])
def listar_quartos(db: Session = Depends(get_db)):
    """Lista publica de quartos."""
    return db.query(Quarto).all()


@router.get("/{quarto_id}", response_model=QuartoResponseSchema)
def obter_quarto(
    quarto_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Consulta publica de um quarto."""
    return _buscar_quarto_ou_404(quarto_id, db)


@router.post(
    "",
    response_model=QuartoResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_quarto(
    payload: QuartoCreateSchema,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Cadastra um quarto. Restrito a administradores."""

    _verificar_hotel(payload.hotel_id, db)

    novo_quarto = Quarto(
        hotel_id=payload.hotel_id,
        tipo=payload.tipo,
        preco_diaria=payload.preco_diaria,
        max_adultos=payload.max_adultos,
        max_criancas=payload.max_criancas,
    )

    db.add(novo_quarto)
    db.commit()
    db.refresh(novo_quarto)

    return novo_quarto


@router.put("/{quarto_id}", response_model=QuartoResponseSchema)
def editar_quarto(
    quarto_id: uuid.UUID,
    payload: QuartoUpdateSchema,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Edita um quarto. Restrito a administradores."""

    quarto = _buscar_quarto_ou_404(quarto_id, db)

    dados = payload.model_dump(exclude_unset=True)

    if "hotel_id" in dados:
        _verificar_hotel(dados["hotel_id"], db)

    for campo, valor in dados.items():
        setattr(quarto, campo, valor)

    db.commit()
    db.refresh(quarto)

    return quarto


@router.delete(
    "/{quarto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_quarto(
    quarto_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Exclui um quarto. Restrito a administradores."""

    quarto = _buscar_quarto_ou_404(quarto_id, db)

    db.delete(quarto)
    db.commit()

    return None