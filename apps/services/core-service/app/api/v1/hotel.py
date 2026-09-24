"""Rotas de CRUD de hoteis.

A listagem (GET /hoteis e GET /hoteis/{id}) e publica.
Cadastrar, editar e excluir exigem permissao de administrador (is_admin).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.cidade import Cidade
from app.models.hotel import Hotel
from app.schemas.hotel import HotelCreateSchema, HotelResponseSchema, HotelUpdateSchema

router = APIRouter(prefix="/hoteis", tags=["Hoteis"])


def _buscar_hotel_ou_404(hotel_id: uuid.UUID, db: Session) -> Hotel:
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel nao encontrado",
        )
    return hotel


@router.get("", response_model=list[HotelResponseSchema])
def listar_hoteis(db: Session = Depends(get_db)):
    """Lista publica de hoteis -- nao exige autenticacao."""
    return db.query(Hotel).all()


@router.get("/{hotel_id}", response_model=HotelResponseSchema)
def obter_hotel(hotel_id: uuid.UUID, db: Session = Depends(get_db)):
    """Detalhe publico de um hotel especifico."""
    return _buscar_hotel_ou_404(hotel_id, db)


@router.post("", response_model=HotelResponseSchema, status_code=status.HTTP_201_CREATED)
def cadastrar_hotel(
    payload: HotelCreateSchema,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Cadastra um novo hotel. Restrito a administradores."""
    cidade = db.query(Cidade).filter(Cidade.id == payload.cidade_id).first()
    if cidade is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cidade informada nao existe",
        )

    novo_hotel = Hotel(
        nome=payload.nome,
        endereco=payload.endereco,
        estrelas=payload.estrelas,
        cidade_id=payload.cidade_id,
    )
    db.add(novo_hotel)
    db.commit()
    db.refresh(novo_hotel)

    return novo_hotel


@router.put("/{hotel_id}", response_model=HotelResponseSchema)
def editar_hotel(
    hotel_id: uuid.UUID,
    payload: HotelUpdateSchema,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Edita um hotel existente (edicao parcial). Restrito a administradores."""
    hotel = _buscar_hotel_ou_404(hotel_id, db)

    dados = payload.model_dump(exclude_unset=True)

    if "cidade_id" in dados:
        cidade = db.query(Cidade).filter(Cidade.id == dados["cidade_id"]).first()
        if cidade is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cidade informada nao existe",
            )

    for campo, valor in dados.items():
        setattr(hotel, campo, valor)

    db.commit()
    db.refresh(hotel)

    return hotel


@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_hotel(
    hotel_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Exclui um hotel. Restrito a administradores."""
    hotel = _buscar_hotel_ou_404(hotel_id, db)
    db.delete(hotel)
    db.commit()