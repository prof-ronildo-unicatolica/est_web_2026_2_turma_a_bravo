"""Paridade de precos entre backend e frontend (app/services/reserva_service.py).

Os casos e os valores esperados ficam em apps/shared/precificacao_casos.json, o MESMO
arquivo lido pelo teste do frontend (apps/frontend/tests/precificacao.test.mjs).
Se alguem mudar uma regra de preco so de um lado, um dos dois testes passa a falhar.

Nao precisa de banco nem de Docker: `pytest tests/test_precificacao_paridade.py`.
"""

import json
from datetime import date, time
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.reserva_service import (
    EntradaCotacao,
    ReservaInvalidaError,
    ReservaService,
    TarifaPeriodo,
)

# tests/ -> core-service/ -> services/ -> apps/
ARQUIVO_CASOS = Path(__file__).resolve().parents[3] / "shared" / "precificacao_casos.json"
_ARQUIVO = json.loads(ARQUIVO_CASOS.read_text(encoding="utf-8"))
PADRAO_ENTRADA = _ARQUIVO["padrao_entrada"]
PADRAO_ESPERADO = _ARQUIVO["padrao_esperado"]
CASOS = _ARQUIVO["casos"]

service = ReservaService()


def centavos(valor: Decimal) -> int:
    return int((valor * 100).to_integral_value())


def hora(texto: str | None) -> time | None:
    return None if texto is None else time.fromisoformat(texto)


def para_entrada(entrada_do_caso: dict) -> EntradaCotacao:
    """Converte o formato do arquivo compartilhado para o contrato do service.

    Cada caso so informa o que difere de padrao_entrada.
    percentual_ajuste +30.00 vira multiplicador 1.30 (a conversao que a rota de cotacao
    tera que fazer ao ler a TarifaTemporada do banco).
    """
    e = {**PADRAO_ENTRADA, **entrada_do_caso}
    return EntradaCotacao(
        preco_diaria=Decimal(e["preco_diaria"]),
        check_in=date.fromisoformat(e["check_in"]),
        check_out=date.fromisoformat(e["check_out"]),
        adultos=e["adultos"],
        idades_criancas=e["idades_criancas"],
        nao_reembolsavel=e["nao_reembolsavel"],
        horario_checkin=hora(e["horario_checkin"]),
        horario_checkout=hora(e["horario_checkout"]),
        tarifas_temporada=[
            TarifaPeriodo(
                data_inicio=date.fromisoformat(t["data_inicio"]),
                data_fim=date.fromisoformat(t["data_fim"]),
                multiplicador=Decimal(1) + Decimal(t["percentual_ajuste"]) / 100,
            )
            for t in e["tarifas"]
        ],
        max_adultos=e["max_adultos"],
        max_criancas=e["max_criancas"],
    )


def test_arquivo_compartilhado_tem_casos_suficientes():
    assert len(CASOS) >= 40
    assert any(c.get("erro") for c in CASOS), "faltam casos de entrada invalida"


@pytest.mark.parametrize("caso", CASOS, ids=[c["nome"] for c in CASOS])
def test_paridade_com_frontend(caso):
    entrada = para_entrada(caso["entrada"])

    if caso.get("erro"):
        with pytest.raises(ReservaInvalidaError):
            service.calcular_cotacao(entrada)
        return

    cotacao = service.calcular_cotacao(entrada)
    esperado = {**PADRAO_ESPERADO, **caso["esperado"]}

    assert cotacao.noites == esperado["noites"]
    assert [centavos(n.valor) for n in cotacao.detalhe_noites] == esperado["detalhe_noites_centavos"]
    assert centavos(cotacao.subtotal_diarias) == esperado["subtotal_centavos"]
    assert centavos(cotacao.taxa_early_checkin) == esperado["early_centavos"]
    assert centavos(cotacao.taxa_late_checkout) == esperado["late_centavos"]
    assert centavos(cotacao.desconto_nao_reembolsavel) == esperado["desconto_centavos"]
    assert centavos(cotacao.total) == esperado["total_centavos"]
    assert cotacao.bebes == esperado["bebes"]
    assert cotacao.criancas_pagantes == esperado["criancas_pagantes"]