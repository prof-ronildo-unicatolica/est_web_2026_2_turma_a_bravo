
"""Rotas de reservas com Transactional Outbox e cancelamento."""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.evento_outbox import EventoOutbox
from app.models.quarto import Quarto
from app.models.reserva import Reserva
from app.models.tarifa_temporada import TarifaTemporada
from app.schemas.reserva import ReservaCreateSchema, ReservaResponseSchema
from app.services.cancelamento_service import efetivar_cancelamento
from app.services.reserva_service import (
    EntradaCotacao,
    ReservaInvalidaError,
    ReservaService,
    TarifaPeriodo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reservas", tags=["Reservas"])


@router.post(
    "",
    response_model=ReservaResponseSchema,
    status_code=status.HTTP_202_ACCEPTED,
)
async def solicitar_reserva(
    payload: ReservaCreateSchema,
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_current_user),
):
    """Registra a reserva e o evento Outbox na mesma transacao."""

    quarto = (
        db.query(Quarto)
        .filter(Quarto.id == payload.quarto_id)
        .first()
    )

    if quarto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quarto nao encontrado",
        )

    tarifas = (
        db.query(TarifaTemporada)
        .filter(
            TarifaTemporada.hotel_id == quarto.hotel_id,
            TarifaTemporada.data_inicio < payload.data_saida,
            TarifaTemporada.data_fim >= payload.data_entrada,
        )
        .all()
    )

    periodos = [
        TarifaPeriodo(
            data_inicio=tarifa.data_inicio,
            data_fim=tarifa.data_fim,
            multiplicador=(1 + tarifa.percentual_ajuste / 100),
        )
        for tarifa in tarifas
    ]

    entrada = EntradaCotacao(
        preco_diaria=quarto.preco_diaria,
        check_in=payload.data_entrada,
        check_out=payload.data_saida,
        adultos=payload.quantidade_adultos,
        idades_criancas=payload.idades_criancas,
        nao_reembolsavel=payload.nao_reembolsavel,
        horario_checkin=payload.horario_checkin,
        horario_checkout=payload.horario_checkout,
        tarifas_temporada=periodos,
        max_adultos=quarto.max_adultos,
        max_criancas=quarto.max_criancas,
    )

    try:
        cotacao = ReservaService().calcular_cotacao(entrada)
    except ReservaInvalidaError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erro),
        ) from erro

    reserva = Reserva(
        id=uuid.uuid4(),
        cliente_email=usuario["email"],
        quarto_id=quarto.id,
        data_entrada=payload.data_entrada,
        data_saida=payload.data_saida,
        quantidade_adultos=payload.quantidade_adultos,
        quantidade_criancas=len(payload.idades_criancas),
        valor_total=cotacao.total,
        status="Pendente",
    )

    evento = {
        "reserva_id": str(reserva.id),
        "quarto_id": str(reserva.quarto_id),
        "cliente_email": reserva.cliente_email,
        "data_entrada": reserva.data_entrada.isoformat(),
        "data_saida": reserva.data_saida.isoformat(),
        "valor_total": str(reserva.valor_total),
    }

    registro_outbox = EventoOutbox(
        id=uuid.uuid4(),
        reserva_id=reserva.id,
        fila="solicitacoes-reserva",
        payload=evento,
        status="Pendente",
        tentativas=0,
    )

    try:
        db.add(reserva)
        db.flush()
        db.add(registro_outbox)
        db.commit()
        db.refresh(reserva)

    except Exception as erro:
        db.rollback()
        logger.exception("Erro ao registrar reserva e evento Outbox")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel registrar a reserva",
        ) from erro

    return reserva


@router.post(
    "/{reserva_id}/cancelar",
    response_model=ReservaResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def cancelar_reserva(
    reserva_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_current_user),
):
    """
    Estrutura de cancelamento da Sprint 8.

    A efetivacao depende da integracao das regras de
    48 horas e multas, desenvolvidas pelo Integrante 2.
    """

    try:
        # Bloqueia o quarto antes de atualizar a reserva,
        # seguindo a ordem de bloqueio do reservation_worker.
        reserva_consulta = (
            db.query(Reserva)
            .filter(
                Reserva.id == reserva_id,
                Reserva.cliente_email == usuario["email"],
            )
            .first()
        )

        if reserva_consulta is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva nao encontrada",
            )

        quarto = (
            db.query(Quarto)
            .filter(Quarto.id == reserva_consulta.quarto_id)
            .with_for_update()
            .first()
        )

        if quarto is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Quarto da reserva nao encontrado",
            )

        reserva = (
            db.query(Reserva)
            .filter(
                Reserva.id == reserva_id,
                Reserva.cliente_email == usuario["email"],
            )
            .with_for_update()
            .first()
        )

        if reserva is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva nao encontrada",
            )

        if reserva.status == "Cancelada":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta reserva ja esta cancelada",
            )

        if reserva.status not in ("Pendente", "Confirmada"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O status atual nao permite cancelamento",
            )

        if reserva.data_entrada <= datetime.now(timezone.utc).date():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nao e possivel cancelar reserva iniciada ou encerrada",
            )

        # Ponto de integracao com o Integrante 2.
        # A politica deve calcular multa e reembolso antes
        # da alteracao do status e do registro de auditoria.
        #
        # Nao efetivar cancelamentos sem essa validacao.
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Cancelamento aguardando integracao das "
                "regras de 48 horas e multas"
            ),
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as erro:
        db.rollback()
        logger.exception(
            "Erro ao processar cancelamento da reserva %s",
            reserva_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel processar o cancelamento",
        ) from erro
