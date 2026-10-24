
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.hotel import Hotel
from app.models.servico_adicional import ServicoAdicional
from app.schemas.servico_adicional import (
    ServicoAdicionalCreateSchema,
    ServicoAdicionalUpdateSchema,
    ServicoAdicionalResponseSchema,
)

router = APIRouter(
    prefix="/servicos-adicionais",
    tags=["Serviços Adicionais"],
)


def buscar_servico_ou_404(db: Session, servico_id: uuid.UUID):
    servico = db.query(ServicoAdicional).filter(
        ServicoAdicional.id == servico_id
    ).first()

    if servico is None:
        raise HTTPException(
            status_code=404,
            detail="Serviço adicional não encontrado.",
        )

    return servico


def verificar_hotel(db: Session, hotel_id: uuid.UUID):
    hotel = db.query(Hotel).filter(
        Hotel.id == hotel_id
    ).first()

    if hotel is None:
        raise HTTPException(
            status_code=400,
            detail="Hotel não encontrado.",
        )


@router.get("", response_model=list[ServicoAdicionalResponseSchema])
def listar_servicos(
    hotel_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    consulta = db.query(ServicoAdicional)

    if hotel_id is not None:
        consulta = consulta.filter(
            ServicoAdicional.hotel_id == hotel_id
        )

    return consulta.all()


@router.get(
    "/{servico_id}",
    response_model=ServicoAdicionalResponseSchema,
)
def consultar_servico(
    servico_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return buscar_servico_ou_404(db, servico_id)


@router.post(
    "",
    response_model=ServicoAdicionalResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def criar_servico(
    dados: ServicoAdicionalCreateSchema,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    verificar_hotel(db, dados.hotel_id)

    servico = ServicoAdicional(**dados.model_dump())

    db.add(servico)
    db.commit()
    db.refresh(servico)

    return servico


@router.put(
    "/{servico_id}",
    response_model=ServicoAdicionalResponseSchema,
)
def atualizar_servico(
    servico_id: uuid.UUID,
    dados: ServicoAdicionalUpdateSchema,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    servico = buscar_servico_ou_404(db, servico_id)
    alteracoes = dados.model_dump(exclude_unset=True)

    if "hotel_id" in alteracoes:
        if alteracoes["hotel_id"] is None:
            raise HTTPException(
                status_code=422,
                detail="O hotel não pode ser nulo.",
            )

        verificar_hotel(db, alteracoes["hotel_id"])

    for campo, valor in alteracoes.items():
        if valor is None and campo in (
            "nome",
            "preco",
            "tipo_cobranca",
        ):
            raise HTTPException(
                status_code=422,
                detail=f"O campo {campo} não pode ser nulo.",
            )

        setattr(servico, campo, valor)

    db.commit()
    db.refresh(servico)

    return servico


@router.delete(
    "/{servico_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_servico(
    servico_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    servico = buscar_servico_ou_404(db, servico_id)

    db.delete(servico)
    db.commit()
