import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db, get_mongo_db
from app.models.comodidades import Comodidade
from app.models.hotel import Hotel
from app.schemas.comodidade import (
    ComodidadeCreateSchema,
    ComodidadeResponseSchema,
    ComodidadeUpdateSchema,
    HotelComComodidadesResponseSchema,
    HotelComodidadesUpdateSchema,
)
from app.services.catalogo_hoteis import sincronizar_hoteis_por_ids
from app.services.comodidade_service import ComodidadeService

router = APIRouter(prefix="/comodidades", tags=["Comodidades"])

hotel_comodidades_router = APIRouter(tags=["Comodidades"])


def _hotel_ids_com_comodidade(db: Session, comodidade_id: uuid.UUID) -> set[uuid.UUID]:
    rows = (
        db.query(Hotel.id)
        .join(Hotel.comodidades)
        .filter(Comodidade.id == comodidade_id)
        .all()
    )
    return {row[0] for row in rows}


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
async def atualizar_comodidade(
    comodidade_id: uuid.UUID,
    payload: ComodidadeUpdateSchema,
    db: Session = Depends(get_db),
    mongo_db=Depends(get_mongo_db),
    admin: dict = Depends(get_current_admin),
):
    """Rota administrativa: edita uma comodidade existente."""
    hotel_ids = _hotel_ids_com_comodidade(db, comodidade_id)
    service = ComodidadeService(db)
    comodidade = service.atualizar(comodidade_id, payload)
    await sincronizar_hoteis_por_ids(db, mongo_db, hotel_ids)
    return comodidade


@router.delete("/{comodidade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_comodidade(
    comodidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    mongo_db=Depends(get_mongo_db),
    admin: dict = Depends(get_current_admin),
):
    """Rota administrativa: remove uma comodidade."""
    hotel_ids = _hotel_ids_com_comodidade(db, comodidade_id)
    service = ComodidadeService(db)
    service.excluir(comodidade_id)
    await sincronizar_hoteis_por_ids(db, mongo_db, hotel_ids)


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
async def definir_comodidades_do_hotel(
    hotel_id: uuid.UUID,
    payload: HotelComodidadesUpdateSchema,
    db: Session = Depends(get_db),
    mongo_db=Depends(get_mongo_db),
    admin: dict = Depends(get_current_admin),
):
    """Rota administrativa: substitui o conjunto de comodidades de um hotel."""
    service = ComodidadeService(db)
    hotel = service.definir_comodidades_do_hotel(hotel_id, payload.comodidade_ids)
    await sincronizar_hoteis_por_ids(db, mongo_db, {hotel.id})
    return hotel