"""Motor de precificacao de reservas (Sprint 5 - Parte 1).

Este modulo e PURO: nao acessa banco, nao depende de Quarto/Tarifa/Servico.
Quem chama (rota, outro service) busca os dados e passa valores simples.
Assim ele roda e e testado sem Docker, e as Partes 2, 3 e 4 da sprint
dependem apenas do contrato abaixo (EntradaCotacao -> CotacaoReserva).

Regras (todas ajustaveis em RegrasPrecificacao):
  1. Diarias   = noites entre check-in e check-out (a data de saida nao conta).
  2. Hospedes  = cobranca por pessoa: adulto 100%, crianca 50%, bebe gratis.
  3. Temporada = multiplicador por noite (alta/baixa temporada), opcional.
  4. Early check-in / late check-out = taxa em fracao da diaria da noite
     afetada (primeira noite no early, ultima noite no late).
  5. Tarifa nao reembolsavel = 10% de desconto sobre as diarias.

Arredondamento (importante para o front bater com o back): cada noite e cada
taxa sao arredondadas para centavos (ROUND_HALF_UP); o desconto tambem.
O total e a soma de valores JA arredondados.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

CENTAVOS = Decimal("0.01")


class ReservaInvalidaError(ValueError):
    """Dados de entrada invalidos para a cotacao (a rota deve responder 422)."""


# ---------------------------------------------------------------------------
# Regras de negocio (um unico lugar para ajustar)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RegrasPrecificacao:
    # Idades (em anos completos na data do check-in)
    idade_max_bebe: int = 2  # 0..2  -> nao paga
    idade_max_crianca: int = 12  # 3..12 -> paga fator_crianca
    # 13..17 -> paga como adulto (continua contando em max_criancas)
    fator_crianca: Decimal = Decimal("0.50")

    # Horarios padrao do hotel
    checkin_padrao: time = time(14, 0)
    checkout_padrao: time = time(12, 0)

    # Early check-in: chegando antes de checkin_padrao
    #   [early_limite_diaria_cheia, checkin_padrao) -> fator_taxa_parcial
    #   antes de early_limite_diaria_cheia           -> diaria cheia
    early_limite_diaria_cheia: time = time(6, 0)

    # Late check-out: saindo depois de checkout_padrao
    #   (checkout_padrao, late_limite_diaria_cheia] -> fator_taxa_parcial
    #   depois de late_limite_diaria_cheia           -> diaria cheia
    late_limite_diaria_cheia: time = time(18, 0)

    fator_taxa_parcial: Decimal = Decimal("0.50")

    # Tarifa nao reembolsavel
    desconto_nao_reembolsavel: Decimal = Decimal("0.10")
    # False: desconto so sobre as diarias. True: tambem sobre early/late.
    desconto_incide_sobre_taxas: bool = False


REGRAS_PADRAO = RegrasPrecificacao()


# ---------------------------------------------------------------------------
# Contrato de entrada / saida
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TarifaPeriodo:
    """Multiplicador de temporada. Periodo INCLUSIVO nas duas pontas.

    Ex.: alta temporada = multiplicador 1.30; baixa = 0.90.
    Se duas tarifas cobrirem a mesma noite, vale a de maior multiplicador.
    """

    data_inicio: date
    data_fim: date
    multiplicador: Decimal


@dataclass(frozen=True)
class EntradaCotacao:
    preco_diaria: Decimal  # Quarto.preco_diaria (valor por pessoa/noite)
    check_in: date
    check_out: date
    adultos: int
    idades_criancas: Sequence[int] = ()  # uma idade por crianca (bebes incluidos)
    nao_reembolsavel: bool = False
    horario_checkin: time | None = None  # chegada prevista (None = padrao)
    horario_checkout: time | None = None  # saida prevista (None = padrao)
    tarifas_temporada: Sequence[TarifaPeriodo] = ()
    # Capacidade do Quarto; se informada, a cotacao valida os limites.
    # Bebes contam como crianca na capacidade.
    max_adultos: int | None = None
    max_criancas: int | None = None


@dataclass(frozen=True)
class NoiteCotada:
    data: date
    multiplicador: Decimal
    valor: Decimal


@dataclass(frozen=True)
class CotacaoReserva:
    noites: int
    adultos: int
    criancas_pagantes: int
    bebes: int
    ocupantes_equivalentes: Decimal  # adultos + criancas * fator
    detalhe_noites: list[NoiteCotada] = field(default_factory=list)
    subtotal_diarias: Decimal = Decimal("0.00")
    taxa_early_checkin: Decimal = Decimal("0.00")
    taxa_late_checkout: Decimal = Decimal("0.00")
    desconto_nao_reembolsavel: Decimal = Decimal("0.00")  # valor POSITIVO
    total: Decimal = Decimal("0.00")


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
def _dinheiro(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def _dec(valor: object) -> Decimal:
    # str() evita o ruido binario do float (Decimal(0.1) != Decimal("0.1")).
    return valor if isinstance(valor, Decimal) else Decimal(str(valor))


class ReservaService:
    def __init__(self, regras: RegrasPrecificacao = REGRAS_PADRAO):
        self.regras = regras

    # -- API publica --------------------------------------------------------
    def calcular_cotacao(self, entrada: EntradaCotacao) -> CotacaoReserva:
        preco = _dec(entrada.preco_diaria)
        self._validar(entrada, preco)

        bebes, criancas_pagantes, adolescentes = self._classificar_criancas(
            entrada.idades_criancas
        )
        # Adolescentes (13-17) pagam como adulto.
        pagantes_integrais = entrada.adultos + adolescentes
        ocupantes = Decimal(pagantes_integrais) + (
            Decimal(criancas_pagantes) * self.regras.fator_crianca
        )

        noites = self._calcular_noites(entrada, preco, ocupantes)
        subtotal = sum((n.valor for n in noites), Decimal("0.00"))

        taxa_early = self._taxa_early_checkin(entrada.horario_checkin, noites[0].valor)
        taxa_late = self._taxa_late_checkout(entrada.horario_checkout, noites[-1].valor)

        desconto = Decimal("0.00")
        if entrada.nao_reembolsavel:
            base = subtotal
            if self.regras.desconto_incide_sobre_taxas:
                base += taxa_early + taxa_late
            desconto = _dinheiro(base * self.regras.desconto_nao_reembolsavel)

        total = subtotal + taxa_early + taxa_late - desconto

        return CotacaoReserva(
            noites=len(noites),
            adultos=entrada.adultos,
            criancas_pagantes=criancas_pagantes + adolescentes,
            bebes=bebes,
            ocupantes_equivalentes=ocupantes,
            detalhe_noites=noites,
            subtotal_diarias=subtotal,
            taxa_early_checkin=taxa_early,
            taxa_late_checkout=taxa_late,
            desconto_nao_reembolsavel=desconto,
            total=total,
        )

    # -- Diarias ------------------------------------------------------------
    def _calcular_noites(
        self, entrada: EntradaCotacao, preco: Decimal, ocupantes: Decimal
    ) -> list[NoiteCotada]:
        total_noites = (entrada.check_out - entrada.check_in).days
        noites: list[NoiteCotada] = []
        for i in range(total_noites):
            dia = entrada.check_in + timedelta(days=i)
            mult = self._multiplicador_do_dia(dia, entrada.tarifas_temporada)
            valor = _dinheiro(preco * mult * ocupantes)
            noites.append(NoiteCotada(data=dia, multiplicador=mult, valor=valor))
        return noites

    @staticmethod
    def _multiplicador_do_dia(dia: date, tarifas: Sequence[TarifaPeriodo]) -> Decimal:
        aplicaveis = [
            _dec(t.multiplicador) for t in tarifas if t.data_inicio <= dia <= t.data_fim
        ]
        return max(aplicaveis) if aplicaveis else Decimal("1")

    # -- Bebes e criancas ---------------------------------------------------
    def _classificar_criancas(self, idades: Sequence[int]) -> tuple[int, int, int]:
        """Retorna (bebes, criancas_pagantes_parcial, adolescentes_integrais)."""
        bebes = criancas = adolescentes = 0
        for idade in idades:
            if idade <= self.regras.idade_max_bebe:
                bebes += 1
            elif idade <= self.regras.idade_max_crianca:
                criancas += 1
            else:
                adolescentes += 1
        return bebes, criancas, adolescentes

    # -- Early check-in / late check-out ------------------------------------
    def _taxa_early_checkin(
        self, chegada: time | None, valor_noite: Decimal
    ) -> Decimal:
        r = self.regras
        if chegada is None or chegada >= r.checkin_padrao:
            return Decimal("0.00")
        if chegada < r.early_limite_diaria_cheia:
            return _dinheiro(valor_noite)
        return _dinheiro(valor_noite * r.fator_taxa_parcial)

    def _taxa_late_checkout(self, saida: time | None, valor_noite: Decimal) -> Decimal:
        r = self.regras
        if saida is None or saida <= r.checkout_padrao:
            return Decimal("0.00")
        if saida > r.late_limite_diaria_cheia:
            return _dinheiro(valor_noite)
        return _dinheiro(valor_noite * r.fator_taxa_parcial)

    # -- Validacao ----------------------------------------------------------
    def _validar(self, e: EntradaCotacao, preco: Decimal) -> None:
        if preco <= 0:
            raise ReservaInvalidaError("preco_diaria deve ser maior que zero")
        if e.check_out <= e.check_in:
            raise ReservaInvalidaError("check_out deve ser posterior ao check_in")
        if e.adultos < 1:
            raise ReservaInvalidaError("informe ao menos 1 adulto")
        for idade in e.idades_criancas:
            if idade < 0:
                raise ReservaInvalidaError("idade de crianca nao pode ser negativa")
            if idade >= 18:
                raise ReservaInvalidaError(
                    "idade de crianca deve ser menor que 18; informe como adulto"
                )
        for t in e.tarifas_temporada:
            if _dec(t.multiplicador) <= 0:
                raise ReservaInvalidaError("multiplicador de temporada deve ser > 0")
            if t.data_fim < t.data_inicio:
                raise ReservaInvalidaError("tarifa com data_fim anterior a data_inicio")
        if e.max_adultos is not None and e.adultos > e.max_adultos:
            raise ReservaInvalidaError(
                f"quarto comporta no maximo {e.max_adultos} adulto(s)"
            )
        if e.max_criancas is not None and len(e.idades_criancas) > e.max_criancas:
            raise ReservaInvalidaError(
                f"quarto comporta no maximo {e.max_criancas} crianca(s)"
            )