
"""Rotas de reservas - Sprint 6 com Transactional Outbox."""

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
from app.schemas.reserva import (
    CancelamentoResponseSchema,
    MultaCancelamentoSchema,
    ReservaCreateSchema,
    ReservaResponseSchema,
)
from app.services.cancelamento_service import (
    CancelamentoInvalidoError,
    calcular_multa,
)
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
            multiplicador=(
                1 + tarifa.percentual_ajuste / 100
            ),
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
        nao_reembolsavel=payload.nao_reembolsavel,
        valor_diaria=cotacao.detalhe_noites[0].valor,
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
        # Insere primeiro a reserva no PostgreSQL.
        db.add(reserva)
        db.flush()

        # Insere o evento Outbox na mesma transacao.
        db.add(registro_outbox)

        # Confirma os dois registros juntos.
        db.commit()

        db.refresh(reserva)

    except Exception as erro:
        db.rollback()
        logger.exception(
            "Erro ao registrar reserva e evento Outbox"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel registrar a reserva",
        ) from erro

    # O outbox-worker publicara a mensagem no RabbitMQ.
    return reserva
STATUS_CANCELAVEIS = ("Pendente", "Confirmada")


def _buscar_reserva_do_usuario(
    db: Session, reserva_id: uuid.UUID, usuario: dict
) -> Reserva:
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()

    pertence = reserva is not None and (
        reserva.cliente_email == usuario["email"] or usuario["is_admin"]
    )
    if not pertence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva nao encontrada",
        )
    return reserva


def _simular_multa(reserva: Reserva):
    if reserva.status not in STATUS_CANCELAVEIS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Reserva com status {reserva.status} nao pode ser cancelada",
        )
    try:
        return calcular_multa(
            data_entrada=reserva.data_entrada,
            valor_total=reserva.valor_total,
            valor_diaria=reserva.valor_diaria,
            nao_reembolsavel=reserva.nao_reembolsavel,
        )
    except CancelamentoInvalidoError as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erro),
        ) from erro


@router.get(
    "/{reserva_id}/multa",
    response_model=MultaCancelamentoSchema,
)
async def consultar_multa(
    reserva_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_current_user),
):
    reserva = _buscar_reserva_do_usuario(db, reserva_id, usuario)
    resultado = _simular_multa(reserva)

    return MultaCancelamentoSchema(
        reserva_id=reserva.id,
        nao_reembolsavel=reserva.nao_reembolsavel,
        dentro_do_prazo=resultado.dentro_do_prazo,
        prazo_limite=resultado.prazo_limite,
        valor_total=reserva.valor_total,
        valor_multa=resultado.multa,
        percentual_multa=resultado.percentual_multa,
        valor_reembolso=resultado.valor_reembolso,
        motivo=resultado.motivo,
    )


@router.post(
    "/{reserva_id}/cancelar",
    response_model=CancelamentoResponseSchema,
)
async def cancelar_reserva(
    reserva_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_current_user),
):
    reserva = _buscar_reserva_do_usuario(db, reserva_id, usuario)
    resultado = _simular_multa(reserva)

    agora = datetime.now(timezone.utc)
    reserva.status = "Cancelada"
    reserva.valor_multa = resultado.multa
    reserva.data_cancelamento = agora

    try:
        db.commit()
        db.refresh(reserva)
    except Exception as erro:
        db.rollback()
        logger.exception("Erro ao cancelar a reserva %s", reserva_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel cancelar a reserva",
        ) from erro

    return CancelamentoResponseSchema(
        reserva_id=reserva.id,
        nao_reembolsavel=reserva.nao_reembolsavel,
        dentro_do_prazo=resultado.dentro_do_prazo,
        prazo_limite=resultado.prazo_limite,
        valor_total=reserva.valor_total,
        valor_multa=resultado.multa,
        percentual_multa=resultado.percentual_multa,
        valor_reembolso=resultado.valor_reembolso,
        motivo=resultado.motivo,
        status=reserva.status,
        data_cancelamento=agora,
    )