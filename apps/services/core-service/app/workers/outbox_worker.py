
"""Worker de publicacao e recuperacao de eventos Outbox - Sprint 6."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.rabbitmq import publish_event

# Carrega os modelos relacionados para o SQLAlchemy reconhecer
# as tabelas e os relacionamentos utilizados pelo Outbox.
from app.models.hotel import Hotel
from app.models.quarto import Quarto
from app.models.reserva import Reserva
from app.models.evento_outbox import EventoOutbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbox_worker")

INTERVALO_SEGUNDOS = 5
LOTE_MAXIMO = 20


def agora_utc():
    return datetime.now(timezone.utc)


def buscar_eventos_pendentes(db: Session):
    """Busca eventos pendentes, bloqueando as linhas selecionadas."""

    consulta = (
        select(EventoOutbox)
        .where(EventoOutbox.status == "Pendente")
        .order_by(EventoOutbox.criado_em, EventoOutbox.id)
        .limit(LOTE_MAXIMO)
        .with_for_update(skip_locked=True)
    )

    return db.execute(consulta).scalars().all()


async def processar_lote():
    """Publica eventos pendentes e registra o resultado."""

    db = SessionLocal()

    try:
        eventos = buscar_eventos_pendentes(db)

        for evento in eventos:
            try:
                await publish_event(
                    evento.fila,
                    evento.payload,
                )

                evento.status = "Publicado"
                evento.publicado_em = agora_utc()
                evento.ultimo_erro = None
                evento.tentativas += 1

                logger.info(
                    "Evento %s publicado na fila %s",
                    evento.id,
                    evento.fila,
                )

            except Exception as erro:
                evento.tentativas += 1
                evento.ultimo_erro = str(erro)

                logger.warning(
                    "Falha na publicacao do evento %s: %s",
                    evento.id,
                    erro,
                )

        db.commit()

    except Exception:
        db.rollback()
        logger.exception(
            "Erro ao processar eventos Outbox"
        )

    finally:
        db.close()


async def main():
    """Executa continuamente a verificacao de eventos pendentes."""

    logger.info("Worker Outbox iniciado.")

    while True:
        await processar_lote()
        await asyncio.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker Outbox encerrado.")
