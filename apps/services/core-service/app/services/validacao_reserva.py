"""Validacoes de reserva que dependem do quarto e do banco (Sprint 7).

Ordem em `validar_reserva` (da mais barata para a mais cara, para falhar rapido):

  1. Periodo        -> datas coerentes e dentro dos limites do hotel
  2. Capacidade     -> adultos e criancas cabem no quarto
  3. Disponibilidade-> nenhuma reserva ativa ocupa o quarto no periodo

Os erros sao `ErroDeNegocio` (app/core/exceptions.py): viram 422 ou 409 com um
`codigo` estavel e os limites violados em `detalhes`, sem try/except na rota.

Sobre a disponibilidade: o reservation_worker continua sendo a decisao FINAL
(ele trava o quarto com SELECT ... FOR UPDATE e cancela quem perdeu a corrida).
A checagem daqui e so para responder 409 na hora, em vez de aceitar a reserva
(202) e cancelar depois. Por isso reaproveita as MESMAS regras do worker
(`STATUS_ATIVOS` e `periodos_se_sobrepoem`): as duas nunca divergem.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ConflitoError, RegraDeNegocioError
from app.models.reserva import Reserva
from app.workers.reservation_worker import STATUS_ATIVOS, periodos_se_sobrepoem


@dataclass(frozen=True)
class LimitesReserva:
    """Limites do periodo. Ajuste aqui se o hotel pedir outros valores."""

    max_noites: int = 30
    max_antecedencia_dias: int = 365


LIMITES_PADRAO = LimitesReserva()


def validar_periodo(
    data_entrada: date,
    data_saida: date,
    *,
    hoje: date | None = None,
    limites: LimitesReserva = LIMITES_PADRAO,
) -> None:
    hoje = hoje or date.today()

    if data_entrada < hoje:
        raise RegraDeNegocioError(
            "A data de entrada nao pode estar no passado",
            codigo="data_entrada_no_passado",
            data_entrada=data_entrada,
        )

    if data_saida <= data_entrada:
        raise RegraDeNegocioError(
            "A data de saida deve ser posterior a data de entrada",
            codigo="periodo_invalido",
            data_entrada=data_entrada,
            data_saida=data_saida,
        )

    noites = (data_saida - data_entrada).days
    if noites > limites.max_noites:
        raise RegraDeNegocioError(
            f"A estadia maxima e de {limites.max_noites} noites",
            codigo="estadia_muito_longa",
            maximo_noites=limites.max_noites,
            noites_solicitadas=noites,
        )

    antecedencia = (data_entrada - hoje).days
    if antecedencia > limites.max_antecedencia_dias:
        raise RegraDeNegocioError(
            "A reserva so pode ser feita com ate "
            f"{limites.max_antecedencia_dias} dias de antecedencia",
            codigo="reserva_antecipada_demais",
            maximo_dias=limites.max_antecedencia_dias,
            antecedencia_dias=antecedencia,
        )


def validar_capacidade(
    quarto: Any,
    quantidade_adultos: int,
    idades_criancas: Sequence[int],
) -> None:
    """Confere os limites do quarto (`max_adultos` e `max_criancas`).

    Bebes contam como crianca na capacidade (a mesma regra do motor de preco).
    """
    if quantidade_adultos > quarto.max_adultos:
        raise RegraDeNegocioError(
            f"O quarto comporta no maximo {quarto.max_adultos} adulto(s)",
            codigo="capacidade_adultos_excedida",
            maximo=quarto.max_adultos,
            informado=quantidade_adultos,
        )

    criancas = len(idades_criancas)
    if criancas > quarto.max_criancas:
        if quarto.max_criancas == 0:
            mensagem = "Este quarto nao aceita criancas"
        else:
            mensagem = f"O quarto comporta no maximo {quarto.max_criancas} crianca(s)"
        raise RegraDeNegocioError(
            mensagem,
            codigo="capacidade_criancas_excedida",
            maximo=quarto.max_criancas,
            informado=criancas,
        )


def validar_disponibilidade(
    db: Session,
    quarto_id: Any,
    data_entrada: date,
    data_saida: date,
) -> None:
    """Rejeita (409) se alguma reserva ATIVA do quarto cobre noites do periodo.

    Checkout e check-in no mesmo dia nao conflitam (mesma regra do worker).
    Reservas Pendente/Cancelada nao bloqueiam: pendente ainda nao foi aceita
    (o worker decide) e cancelada liberou o quarto.
    """
    ocupadas = (
        db.query(Reserva.data_entrada, Reserva.data_saida)
        .filter(
            Reserva.quarto_id == quarto_id,
            Reserva.status.in_(STATUS_ATIVOS),
        )
        .all()
    )
    if any(
        periodos_se_sobrepoem(data_entrada, data_saida, entrada, saida)
        for entrada, saida in ocupadas
    ):
        raise ConflitoError(
            "O quarto ja esta reservado em parte do periodo solicitado",
            codigo="quarto_indisponivel",
            data_entrada=data_entrada,
            data_saida=data_saida,
        )


def validar_reserva(
    db: Session,
    quarto: Any,
    *,
    data_entrada: date,
    data_saida: date,
    quantidade_adultos: int,
    idades_criancas: Sequence[int],
    hoje: date | None = None,
    limites: LimitesReserva = LIMITES_PADRAO,
) -> None:
    validar_periodo(data_entrada, data_saida, hoje=hoje, limites=limites)
    validar_capacidade(quarto, quantidade_adultos, idades_criancas)
    validar_disponibilidade(db, quarto.id, data_entrada, data_saida)
