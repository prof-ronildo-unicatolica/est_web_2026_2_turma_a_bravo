import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.schemas.comodidade import (
    ComodidadeCreateSchema,
    ComodidadeResponseSchema,
    ComodidadeUpdateSchema,
    HotelComComodidadesResponseSchema,
    HotelComodidadesUpdateSchema,
)
from app.services.comodidade_service import ComodidadeService

router = APIRouter(prefix="/comodidades", tags=["Comodidades"])

hotel_comodidades_router = APIRouter(tags=["Comodidades"])


@router.get("", response_model=list[ComodidadeResponseSchema])
def listar_comodidades(db: Session = Depends(get_db)):
    """Rota pública: lista todas as comodidades cadastradas."""
    service = ComodidadeService(db)
    return service.listar()


@router.get("/{comodidade_id}", response_model=ComodidadeResponseSchema)
def obter_comodidade(comodidade_id: uuid.UUID, db: Session = Depends(get_db)):
    """Rota pública: detalhe de uma comodidade."""
    service = ComodidadeService(db)
    return service.obter_por_id(comodidade_id)


@router.post(
    "", response_model=ComodidadeResponseSchema, status_code=status.HTTP_201_CREATED
)
def criar_comodidade(
    payload: ComodidadeCreateSchema,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Rota administrativa: cadastra uma nova comodidade."""
    service = ComodidadeService(db)
    return service.criar(payload)


@router.put("/{comodidade_id}", response_model=ComodidadeResponseSchema)
def atualizar_comodidade(
    comodidade_id: uuid.UUID,
    payload: ComodidadeUpdateSchema,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Rota administrativa: edita uma comodidade existente."""
    service = ComodidadeService(db)
    return service.atualizar(comodidade_id, payload)


@router.delete("/{comodidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_comodidade(
    comodidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Rota administrativa: remove uma comodidade."""
    service = ComodidadeService(db)
    service.excluir(comodidade_id)


@hotel_comodidades_router.get(
    "/hoteis/{hotel_id}/comodidades",
    response_model=HotelComComodidadesResponseSchema,
)
def listar_comodidades_do_hotel(hotel_id: uuid.UUID, db: Session = Depends(get_db)):
    """Rota pública: lista as comodidades de um hotel específico."""
    service = ComodidadeService(db)
    return service.listar_comodidades_do_hotel(hotel_id)


@hotel_comodidades_router.put(
    "/hoteis/{hotel_id}/comodidades",
    response_model=HotelComComodidadesResponseSchema,
)
def definir_comodidades_do_hotel(
    hotel_id: uuid.UUID,
    payload: HotelComodidadesUpdateSchema,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Rota administrativa: substitui o conjunto de comodidades de um hotel."""
    service = ComodidadeService(db)
    return service.definir_comodidades_do_hotel(hotel_id, payload.comodidade_ids)