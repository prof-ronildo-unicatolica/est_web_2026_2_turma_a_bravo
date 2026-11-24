"""Worker de processamento assincrono de reservas."""

import asyncio
import json
import logging
import random
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

import aio_pika
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.hotel import Hotel
from app.models.quarto import Quarto
from app.models.reserva import Reserva

FILA_RESERVAS = "solicitacoes-reserva"
STATUS_PENDENTE = "Pendente"
STATUS_CONFIRMADA = "Confirmada"
STATUS_CANCELADA = "Cancelada"
STATUS_ATIVOS = (STATUS_CONFIRMADA, "Processando")

logger = logging.getLogger("reservation-worker")


def periodos_se_sobrepoem(entrada_a: date, saida_a: date,
                          entrada_b: date, saida_b: date) -> bool:
    """Checkout e check-in no mesmo dia nao representam noites sobrepostas."""
    return entrada_a < saida_b and entrada_b < saida_a


def simular_pagamento(valor_total: Decimal) -> bool:
    """Simula pagamento com 90% de chance de aprovacao."""
    try:
        valor = Decimal(str(valor_total))
    except (InvalidOperation, TypeError, ValueError):
        return False
    if not valor.is_finite() or valor <= 0:
        return False
    return random.random() < 0.90


def processar_reserva(reserva_id: uuid.UUID) -> str:
    """Processa uma reserva sob lock do quarto para evitar overbooking."""
    with SessionLocal() as db:
        try:
            reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
            if reserva is None:
                logger.warning("Reserva %s nao encontrada", reserva_id)
                return "Nao encontrada"

            if reserva.status != STATUS_PENDENTE:
                logger.info("Mensagem duplicada para reserva %s; ignorada", reserva_id)
                return reserva.status

            # PostgreSQL serializa workers que tentam reservar o mesmo quarto.
            quarto = (
                db.query(Quarto)
                .filter(Quarto.id == reserva.quarto_id)
                .with_for_update()
                .first()
            )
            if quarto is None:
                reserva.status = STATUS_CANCELADA
                db.commit()
                return STATUS_CANCELADA

            # Atualiza a entidade apos obter o lock para cobrir entregas duplicadas.
            db.refresh(reserva)
            if reserva.status != STATUS_PENDENTE:
                return reserva.status

            reservas_ativas = (
                db.query(Reserva)
                .filter(
                    Reserva.quarto_id == reserva.quarto_id,
                    Reserva.status.in_(STATUS_ATIVOS),
                    Reserva.id != reserva.id,
                )
                .all()
            )
            conflito = any(
                periodos_se_sobrepoem(
                    reserva.data_entrada, reserva.data_saida,
                    existente.data_entrada, existente.data_saida,
                )
                for existente in reservas_ativas
            )

            if conflito:
                reserva.status = STATUS_CANCELADA
                db.commit()
                logger.info("Reserva %s cancelada: periodo indisponivel", reserva_id)
                return STATUS_CANCELADA

            if not simular_pagamento(reserva.valor_total):
                reserva.status = STATUS_CANCELADA
                db.commit()
                logger.info("Pagamento recusado para reserva %s", reserva_id)
                return STATUS_CANCELADA

            reserva.status = STATUS_CONFIRMADA
            db.commit()
            logger.info("Reserva %s confirmada", reserva_id)
            return STATUS_CONFIRMADA

        except Exception:
            db.rollback()
            logger.exception("Falha ao processar reserva %s", reserva_id)
            raise


async def process_message(message: aio_pika.IncomingMessage) -> None:
    """Valida o evento e processa a reserva sem bloquear o loop asyncio."""
    try:
        payload = json.loads(message.body.decode("utf-8"))
        reserva_id = uuid.UUID(str(payload["reserva_id"]))
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        logger.exception("Mensagem invalida na fila %s", FILA_RESERVAS)
        await message.reject(requeue=False)
        return

    async with message.process(requeue=True):
        await asyncio.to_thread(processar_reserva, reserva_id)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.info("Conectando ao RabbitMQ")
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(FILA_RESERVAS, durable=True)
        await queue.consume(process_message)
        logger.info("Aguardando mensagens em %s", FILA_RESERVAS)
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker encerrado pelo usuario")
