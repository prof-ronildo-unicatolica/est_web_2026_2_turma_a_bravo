
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.hotel import Hotel
from app.models.tarifa_temporada import TarifaTemporada
from app.schemas.tarifa_temporada import (
    TarifaTemporadaCreateSchema,
    TarifaTemporadaUpdateSchema,
    TarifaTemporadaResponseSchema,
)

router = APIRouter(
    prefix="/tarifas-temporada",
    tags=["Tarifas de Temporada"],
)


def buscar_tarifa_ou_404(db: Session, tarifa_id: uuid.UUID):
    tarifa = (
        db.query(TarifaTemporada)
        .filter(TarifaTemporada.id == tarifa_id)
        .first()
    )

    if tarifa is None:
        raise HTTPException(
            status_code=404,
            detail="Tarifa de temporada não encontrada.",
        )

    return tarifa


def verificar_hotel(db: Session, hotel_id: uuid.UUID):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(
            status_code=400,
            detail="Hotel não encontrado.",
        )


def verificar_sobreposicao(
    db: Session,
    hotel_id: uuid.UUID,
    data_inicio,
    data_fim,
    tarifa_id: uuid.UUID | None = None,
):
    consulta = db.query(TarifaTemporada).filter(
        TarifaTemporada.hotel_id == hotel_id,
        TarifaTemporada.data_inicio <= data_fim,
        TarifaTemporada.data_fim >= data_inicio,
    )

    if tarifa_id is not None:
        consulta = consulta.filter(
            TarifaTemporada.id != tarifa_id
        )

    if consulta.first() is not None:
        raise HTTPException(
            status_code=409,
            detail="Já existe uma tarifa para esse hotel nesse período.",
        )


@router.get(
    "",
    response_model=list[TarifaTemporadaResponseSchema],
)
def listar_tarifas(db: Session = Depends(get_db)):
    return db.query(TarifaTemporada).all()


@router.get(
    "/{tarifa_id}",
    response_model=TarifaTemporadaResponseSchema,
)
def consultar_tarifa(
    tarifa_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return buscar_tarifa_ou_404(db, tarifa_id)


@router.post(
    "",
    response_model=TarifaTemporadaResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def criar_tarifa(
    dados: TarifaTemporadaCreateSchema,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    verificar_hotel(db, dados.hotel_id)

    verificar_sobreposicao(
        db,
        dados.hotel_id,
        dados.data_inicio,
        dados.data_fim,
    )

    tarifa = TarifaTemporada(**dados.model_dump())

    db.add(tarifa)
    db.commit()
    db.refresh(tarifa)

    return tarifa


@router.put(
    "/{tarifa_id}",
    response_model=TarifaTemporadaResponseSchema,
)
def atualizar_tarifa(
    tarifa_id: uuid.UUID,
    dados: TarifaTemporadaUpdateSchema,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    tarifa = buscar_tarifa_ou_404(db, tarifa_id)

    alteracoes = dados.model_dump(exclude_unset=True)

    # Impedir valores nulos nos campos obrigatórios.
    campos_obrigatorios = {
        "hotel_id",
        "nome",
        "data_inicio",
        "data_fim",
        "percentual_ajuste",
    }

    for campo in campos_obrigatorios:
        if campo in alteracoes and alteracoes[campo] is None:
            raise HTTPException(
                status_code=422,
                detail=f"O campo {campo} não pode ser nulo.",
            )

    # Utilizar os valores novos ou manter os existentes.
    hotel_id = alteracoes.get(
        "hotel_id",
        tarifa.hotel_id,
    )

    data_inicio = alteracoes.get(
        "data_inicio",
        tarifa.data_inicio,
    )

    data_fim = alteracoes.get(
        "data_fim",
        tarifa.data_fim,
    )

    # Verificar se o período é válido.
    if data_fim < data_inicio:
        raise HTTPException(
            status_code=422,
            detail="Período da tarifa inválido.",
        )

    # Confirmar a existência do hotel.
    verificar_hotel(db, hotel_id)

    # Impedir períodos sobrepostos para o mesmo hotel.
    verificar_sobreposicao(
        db,
        hotel_id,
        data_inicio,
        data_fim,
        tarifa_id,
    )

    # Atualizar somente os campos enviados.
    for campo, valor in alteracoes.items():
        setattr(tarifa, campo, valor)

    db.commit()
    db.refresh(tarifa)

    return tarifa


@router.delete(
    "/{tarifa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_tarifa(
    tarifa_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    tarifa = buscar_tarifa_ou_404(db, tarifa_id)

    db.delete(tarifa)
    db.commit()
