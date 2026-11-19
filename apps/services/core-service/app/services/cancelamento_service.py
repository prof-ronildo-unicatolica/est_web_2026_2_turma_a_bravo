
"""Servico de cancelamento de reservas - Sprint 8."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.evento_outbox import EventoOutbox
from app.models.reserva import Reserva


def efetivar_cancelamento(
    db: Session,
    reserva: Reserva,
    valor_multa: Decimal,
    valor_reembolso: Decimal,
) -> Reserva:
    """
    Atualiza a reserva e registra a auditoria no Outbox.

    A funcao deve ser chamada somente depois da validacao
    da politica de cancelamento pelo Integrante 2.

    A transacao e confirmada pelo endpoint.
    """

    status_anterior = reserva.status
    data_cancelamento = datetime.now(timezone.utc)

    reserva.status = "Cancelada"

    evento = {
        "tipo_evento": "reserva_cancelada_pelo_cliente",
        "reserva_id": str(reserva.id),
        "cliente_email": reserva.cliente_email,
        "status_anterior": status_anterior,
        "status_novo": "Cancelada",
        "valor_total": str(reserva.valor_total),
        "valor_multa": str(valor_multa),
        "valor_reembolso": str(valor_reembolso),
        "data_cancelamento": data_cancelamento.isoformat(),
    }

    registro_outbox = EventoOutbox(
        id=uuid.uuid4(),
        reserva_id=reserva.id,
        fila="audit.logs",
        payload=evento,
        status="Pendente",
        tentativas=0,
    )

    db.add(reserva)
    db.add(registro_outbox)

    return reserva
