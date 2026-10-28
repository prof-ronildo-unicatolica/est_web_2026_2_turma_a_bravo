"""Testes do motor de precificacao (app/services/reserva_service.py).

Nao precisam de banco nem de Docker: rodar com `pytest tests/test_reserva_service.py`.
"""

from datetime import date, time
from decimal import Decimal

import pytest

from app.services.reserva_service import (
    EntradaCotacao,
    RegrasPrecificacao,
    ReservaInvalidaError,
    ReservaService,
    TarifaPeriodo,
)

D = Decimal
service = ReservaService()


def entrada(**kw) -> EntradaCotacao:
    base = dict(
        preco_diaria=D("100.00"),
        check_in=date(2026, 12, 10),
        check_out=date(2026, 12, 13),  # 3 noites
        adultos=1,
    )
    base.update(kw)
    return EntradaCotacao(**base)


# --- Diarias ----------------------------------------------------------------
def test_diarias_simples():
    c = service.calcular_cotacao(entrada())
    assert c.noites == 3
    assert c.subtotal_diarias == D("300.00")
    assert c.total == D("300.00")
    assert [n.data for n in c.detalhe_noites] == [
        date(2026, 12, 10),
        date(2026, 12, 11),
        date(2026, 12, 12),
    ]


def test_data_de_saida_nao_conta_como_noite():
    c = service.calcular_cotacao(
        entrada(check_in=date(2026, 12, 10), check_out=date(2026, 12, 11))
    )
    assert c.noites == 1


def test_preco_float_e_coagido_sem_ruido_binario():
    c = service.calcular_cotacao(
        entrada(preco_diaria=99.9, check_out=date(2026, 12, 11))
    )
    assert c.total == D("99.90")


# --- Bebes e criancas -------------------------------------------------------
def test_bebe_nao_paga():
    sem = service.calcular_cotacao(entrada(adultos=2))
    com = service.calcular_cotacao(entrada(adultos=2, idades_criancas=[0]))
    assert com.total == sem.total == D("600.00")
    assert com.bebes == 1
    assert com.criancas_pagantes == 0


def test_crianca_paga_metade():
    # 2 adultos + 1 crianca(8) = 2.5 ocupantes * 100 * 3 noites
    c = service.calcular_cotacao(entrada(adultos=2, idades_criancas=[8]))
    assert c.ocupantes_equivalentes == D("2.5")
    assert c.total == D("750.00")


@pytest.mark.parametrize(
    "idade, bebes, pagantes, total",
    [
        (2, 1, 0, "100.00"),  # ultimo ano de bebe
        (3, 0, 1, "150.00"),  # primeiro ano de crianca
        (12, 0, 1, "150.00"),  # ultimo ano de crianca
        (13, 0, 1, "200.00"),  # adolescente paga como adulto
        (17, 0, 1, "200.00"),
    ],
)
def test_limites_de_idade(idade, bebes, pagantes, total):
    c = service.calcular_cotacao(
        entrada(check_out=date(2026, 12, 11), idades_criancas=[idade])
    )
    assert (c.bebes, c.criancas_pagantes) == (bebes, pagantes)
    assert c.total == D(total)


# --- Temporada --------------------------------------------------------------
def test_temporada_aplica_por_noite_e_periodo_e_inclusivo():
    alta = TarifaPeriodo(date(2026, 12, 11), date(2026, 12, 11), D("1.5"))
    c = service.calcular_cotacao(entrada(tarifas_temporada=[alta]))
    assert [n.valor for n in c.detalhe_noites] == [
        D("100.00"),
        D("150.00"),
        D("100.00"),
    ]
    assert c.total == D("350.00")


def test_temporada_sobreposta_vale_a_de_maior_multiplicador():
    t1 = TarifaPeriodo(date(2026, 12, 1), date(2026, 12, 31), D("1.2"))
    t2 = TarifaPeriodo(date(2026, 12, 10), date(2026, 12, 10), D("2"))
    c = service.calcular_cotacao(entrada(tarifas_temporada=[t1, t2]))
    assert [n.valor for n in c.detalhe_noites] == [
        D("200.00"),
        D("120.00"),
        D("120.00"),
    ]


# --- Early check-in ---------------------------------------------------------
@pytest.mark.parametrize(
    "chegada, taxa",
    [
        (None, "0.00"),
        (time(14, 0), "0.00"),  # horario padrao
        (time(18, 30), "0.00"),  # depois do padrao: sem taxa
        (time(13, 59), "50.00"),  # antes do padrao: meia diaria
        (time(6, 0), "50.00"),  # limite inferior da faixa parcial
        (time(5, 59), "100.00"),  # madrugada: diaria cheia
    ],
)
def test_early_checkin(chegada, taxa):
    c = service.calcular_cotacao(entrada(horario_checkin=chegada))
    assert c.taxa_early_checkin == D(taxa)
    assert c.total == D("300.00") + D(taxa)


# --- Late check-out ---------------------------------------------------------
@pytest.mark.parametrize(
    "saida, taxa",
    [
        (None, "0.00"),
        (time(10, 0), "0.00"),
        (time(12, 0), "0.00"),  # horario padrao
        (time(12, 1), "50.00"),
        (time(18, 0), "50.00"),  # limite superior da faixa parcial
        (time(18, 1), "100.00"),  # depois das 18h: diaria cheia
    ],
)
def test_late_checkout(saida, taxa):
    c = service.calcular_cotacao(entrada(horario_checkout=saida))
    assert c.taxa_late_checkout == D(taxa)


def test_taxas_usam_a_noite_afetada_com_temporada():
    # early -> 1a noite (x2), late -> ultima noite (x3)
    tarifas = [
        TarifaPeriodo(date(2026, 12, 10), date(2026, 12, 10), D("2")),
        TarifaPeriodo(date(2026, 12, 12), date(2026, 12, 12), D("3")),
    ]
    c = service.calcular_cotacao(
        entrada(
            tarifas_temporada=tarifas,
            horario_checkin=time(5, 0),  # diaria cheia da 1a noite = 200
            horario_checkout=time(15, 0),  # meia diaria da ultima = 150
        )
    )
    assert c.taxa_early_checkin == D("200.00")
    assert c.taxa_late_checkout == D("150.00")


# --- Nao reembolsavel -------------------------------------------------------
def test_nao_reembolsavel_desconta_10_por_cento_das_diarias():
    c = service.calcular_cotacao(entrada(nao_reembolsavel=True))
    assert c.desconto_nao_reembolsavel == D("30.00")
    assert c.total == D("270.00")


def test_reembolsavel_nao_tem_desconto():
    c = service.calcular_cotacao(entrada(nao_reembolsavel=False))
    assert c.desconto_nao_reembolsavel == D("0.00")


def test_desconto_nao_incide_sobre_taxas_por_padrao():
    c = service.calcular_cotacao(
        entrada(nao_reembolsavel=True, horario_checkin=time(5, 0))
    )
    assert c.taxa_early_checkin == D("100.00")
    assert c.desconto_nao_reembolsavel == D("30.00")
    assert c.total == D("370.00")  # 300 + 100 - 30


def test_desconto_pode_incidir_sobre_taxas_se_a_regra_mandar():
    svc = ReservaService(RegrasPrecificacao(desconto_incide_sobre_taxas=True))
    c = svc.calcular_cotacao(entrada(nao_reembolsavel=True, horario_checkin=time(5, 0)))
    assert c.desconto_nao_reembolsavel == D("40.00")
    assert c.total == D("360.00")  # 300 + 100 - 40


# --- Arredondamento ---------------------------------------------------------
def test_arredonda_cada_noite_em_centavos_half_up():
    # 1 adulto + 1 crianca = 1.5 * 10.01 = 15.015 -> 15.02 por noite
    c = service.calcular_cotacao(
        entrada(
            preco_diaria=D("10.01"),
            check_out=date(2026, 12, 12),  # 2 noites
            idades_criancas=[5],
        )
    )
    assert [n.valor for n in c.detalhe_noites] == [D("15.02"), D("15.02")]
    assert c.total == D("30.04")  # arredondar so no fim daria 30.03


# --- Regras customizadas ----------------------------------------------------
def test_regras_podem_ser_trocadas():
    svc = ReservaService(RegrasPrecificacao(fator_crianca=D("0.7"), idade_max_bebe=4))
    c = svc.calcular_cotacao(
        entrada(check_out=date(2026, 12, 11), idades_criancas=[4, 6])
    )
    assert c.bebes == 1  # 4 anos agora e bebe
    assert c.total == D("170.00")  # 1 adulto + 1 crianca(0.7)


# --- Capacidade e validacao -------------------------------------------------
def test_adolescente_conta_na_capacidade_de_criancas():
    with pytest.raises(ReservaInvalidaError, match="crianca"):
        service.calcular_cotacao(entrada(idades_criancas=[15], max_criancas=0))


def test_bebe_conta_na_capacidade_de_criancas():
    with pytest.raises(ReservaInvalidaError, match="crianca"):
        service.calcular_cotacao(entrada(idades_criancas=[1], max_criancas=0))


def test_capacidade_de_adultos():
    with pytest.raises(ReservaInvalidaError, match="adulto"):
        service.calcular_cotacao(entrada(adultos=3, max_adultos=2))


def test_dentro_da_capacidade_passa():
    c = service.calcular_cotacao(
        entrada(adultos=2, idades_criancas=[1], max_adultos=2, max_criancas=1)
    )
    assert c.total == D("600.00")


@pytest.mark.parametrize(
    "kw, msg",
    [
        (dict(check_out=date(2026, 12, 10)), "posterior"),  # mesma data
        (dict(check_out=date(2026, 12, 9)), "posterior"),  # saida antes
        (dict(adultos=0), "adulto"),
        (dict(preco_diaria=D("0")), "preco_diaria"),
        (dict(idades_criancas=[-1]), "negativa"),
        (dict(idades_criancas=[18]), "menor que 18"),
        (
            dict(
                tarifas_temporada=[
                    TarifaPeriodo(date(2026, 12, 5), date(2026, 12, 1), D("1"))
                ]
            ),
            "data_fim",
        ),
        (
            dict(
                tarifas_temporada=[
                    TarifaPeriodo(date(2026, 12, 1), date(2026, 12, 5), D("0"))
                ]
            ),
            "multiplicador",
        ),
    ],
)
def test_entradas_invalidas(kw, msg):
    with pytest.raises(ReservaInvalidaError, match=msg):
        service.calcular_cotacao(entrada(**kw))