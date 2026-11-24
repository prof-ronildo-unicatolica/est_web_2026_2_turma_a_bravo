"""Testes das validacoes de reserva (Sprint 7): periodo, capacidade, disponibilidade."""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.exceptions import ConflitoError, RegraDeNegocioError
from app.models.cidade import Cidade
from app.models.hotel import Hotel
from app.models.quarto import Quarto
from app.models.reserva import Reserva
from app.services.validacao_reserva import (
    LimitesReserva,
    validar_capacidade,
    validar_disponibilidade,
    validar_periodo,
    validar_reserva,
)
from app.workers.reservation_worker import periodos_se_sobrepoem

HOJE = date(2026, 12, 1)


def quarto_fake(max_adultos=2, max_criancas=1):
    return SimpleNamespace(
        id=uuid.uuid4(), max_adultos=max_adultos, max_criancas=max_criancas
    )


# ---------------------------------------------------------------------------
# Capacidade
# ---------------------------------------------------------------------------
class TestCapacidade:
    def test_dentro_do_limite_passa(self):
        validar_capacidade(quarto_fake(2, 1), 2, [5])

    def test_exatamente_no_limite_passa(self):
        validar_capacidade(quarto_fake(3, 2), 3, [1, 9])

    def test_adultos_acima_do_limite(self):
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_capacidade(quarto_fake(2, 1), 3, [])
        assert erro.value.status_code == 422
        assert erro.value.codigo == "capacidade_adultos_excedida"
        assert erro.value.detalhes == {"maximo": 2, "informado": 3}
        assert "no maximo 2 adulto" in erro.value.mensagem

    def test_criancas_acima_do_limite(self):
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_capacidade(quarto_fake(2, 1), 2, [4, 7])
        assert erro.value.codigo == "capacidade_criancas_excedida"
        assert erro.value.detalhes == {"maximo": 1, "informado": 2}
        assert "no maximo 1 crianca" in erro.value.mensagem

    def test_quarto_que_nao_aceita_criancas_tem_mensagem_propria(self):
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_capacidade(quarto_fake(2, 0), 1, [6])
        assert erro.value.codigo == "capacidade_criancas_excedida"
        assert erro.value.mensagem == "Este quarto nao aceita criancas"

    def test_bebe_conta_na_capacidade_de_criancas(self):
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_capacidade(quarto_fake(2, 0), 2, [0])
        assert erro.value.codigo == "capacidade_criancas_excedida"

    def test_adolescente_tambem_conta_como_crianca_na_capacidade(self):
        with pytest.raises(RegraDeNegocioError):
            validar_capacidade(quarto_fake(2, 0), 1, [16])

    def test_adultos_e_checado_antes_de_criancas(self):
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_capacidade(quarto_fake(1, 0), 2, [3])
        assert erro.value.codigo == "capacidade_adultos_excedida"


# ---------------------------------------------------------------------------
# Periodo
# ---------------------------------------------------------------------------
class TestPeriodo:
    def test_periodo_valido_passa(self):
        validar_periodo(HOJE, HOJE + timedelta(days=3), hoje=HOJE)

    def test_entrada_hoje_e_permitida(self):
        validar_periodo(HOJE, HOJE + timedelta(days=1), hoje=HOJE)

    def test_entrada_no_passado(self):
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_periodo(
                HOJE - timedelta(days=1), HOJE + timedelta(days=1), hoje=HOJE
            )
        assert erro.value.codigo == "data_entrada_no_passado"

    @pytest.mark.parametrize("dias", [0, -1, -10])
    def test_saida_igual_ou_antes_da_entrada(self, dias):
        entrada = HOJE + timedelta(days=5)
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_periodo(entrada, entrada + timedelta(days=dias), hoje=HOJE)
        assert erro.value.codigo == "periodo_invalido"

    def test_estadia_de_30_noites_passa_e_31_nao(self):
        entrada = HOJE + timedelta(days=1)
        validar_periodo(entrada, entrada + timedelta(days=30), hoje=HOJE)
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_periodo(entrada, entrada + timedelta(days=31), hoje=HOJE)
        assert erro.value.codigo == "estadia_muito_longa"
        assert erro.value.detalhes == {"maximo_noites": 30, "noites_solicitadas": 31}

    def test_antecedencia_de_365_dias_passa_e_366_nao(self):
        validar_periodo(
            HOJE + timedelta(days=365), HOJE + timedelta(days=367), hoje=HOJE
        )
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_periodo(
                HOJE + timedelta(days=366), HOJE + timedelta(days=368), hoje=HOJE
            )
        assert erro.value.codigo == "reserva_antecipada_demais"
        assert erro.value.detalhes["maximo_dias"] == 365
        assert erro.value.detalhes["antecedencia_dias"] == 366

    def test_limites_sao_configuraveis(self):
        limites = LimitesReserva(max_noites=7, max_antecedencia_dias=30)
        entrada = HOJE + timedelta(days=1)
        validar_periodo(
            entrada, entrada + timedelta(days=7), hoje=HOJE, limites=limites
        )
        with pytest.raises(RegraDeNegocioError):
            validar_periodo(
                entrada, entrada + timedelta(days=8), hoje=HOJE, limites=limites
            )
        with pytest.raises(RegraDeNegocioError):
            validar_periodo(
                HOJE + timedelta(days=31),
                HOJE + timedelta(days=33),
                hoje=HOJE,
                limites=limites,
            )


# ---------------------------------------------------------------------------
# Disponibilidade (usa o banco SQLite do conftest)
# ---------------------------------------------------------------------------
def criar_quarto(db, max_adultos=2, max_criancas=1) -> Quarto:
    cidade = Cidade(id=uuid.uuid4(), nome="Fortaleza", uf="CE")
    db.add(cidade)
    db.flush()
    hotel = Hotel(
        id=uuid.uuid4(),
        nome="Hotel Teste",
        endereco="Rua A, 1",
        estrelas=3,
        diaria="R$ 200",
        cidade_id=cidade.id,
    )
    db.add(hotel)
    db.flush()
    quarto = Quarto(
        id=uuid.uuid4(),
        hotel_id=hotel.id,
        tipo="Standard",
        preco_diaria=Decimal("200.00"),
        max_adultos=max_adultos,
        max_criancas=max_criancas,
    )
    db.add(quarto)
    db.commit()
    return quarto


def criar_reserva(db, quarto, entrada, saida, status="Confirmada") -> Reserva:
    reserva = Reserva(
        id=uuid.uuid4(),
        cliente_email="outro@hotel.com",
        quarto_id=quarto.id,
        data_entrada=entrada,
        data_saida=saida,
        quantidade_adultos=1,
        quantidade_criancas=0,
        valor_total=Decimal("200.00"),
        status=status,
    )
    db.add(reserva)
    db.commit()
    return reserva


D = date(2027, 3, 10)  # reserva existente: noites de 10, 11 e 12 (saida dia 13)


class TestDisponibilidade:
    def test_quarto_livre_passa(self, db_session):
        quarto = criar_quarto(db_session)
        validar_disponibilidade(db_session, quarto.id, D, D + timedelta(days=2))

    @pytest.mark.parametrize(
        "entrada, saida",
        [
            (D, D + timedelta(days=3)),  # periodo identico
            (D - timedelta(days=1), D + timedelta(days=1)),  # invade o inicio
            (D + timedelta(days=2), D + timedelta(days=5)),  # invade o fim
            (D + timedelta(days=1), D + timedelta(days=2)),  # dentro do existente
            (D - timedelta(days=2), D + timedelta(days=6)),  # envolve o existente
        ],
    )
    def test_periodos_que_se_sobrepoem_sao_recusados(self, db_session, entrada, saida):
        quarto = criar_quarto(db_session)
        criar_reserva(db_session, quarto, D, D + timedelta(days=3))
        with pytest.raises(ConflitoError) as erro:
            validar_disponibilidade(db_session, quarto.id, entrada, saida)
        assert erro.value.status_code == 409
        assert erro.value.codigo == "quarto_indisponivel"

    @pytest.mark.parametrize(
        "entrada, saida",
        [
            (D + timedelta(days=3), D + timedelta(days=5)),  # entra no dia que sai
            (D - timedelta(days=2), D),  # sai no dia que o outro entra
            (D + timedelta(days=10), D + timedelta(days=12)),  # bem depois
            (D - timedelta(days=9), D - timedelta(days=5)),  # bem antes
        ],
    )
    def test_periodos_adjacentes_ou_separados_passam(self, db_session, entrada, saida):
        quarto = criar_quarto(db_session)
        criar_reserva(db_session, quarto, D, D + timedelta(days=3))
        validar_disponibilidade(db_session, quarto.id, entrada, saida)

    @pytest.mark.parametrize(
        "status, bloqueia",
        [
            ("Confirmada", True),
            ("Processando", True),
            ("Pendente", False),  # ainda nao aceita: o worker decide
            ("Cancelada", False),  # liberou o quarto
        ],
    )
    def test_so_reservas_ativas_bloqueiam(self, db_session, status, bloqueia):
        quarto = criar_quarto(db_session)
        criar_reserva(db_session, quarto, D, D + timedelta(days=3), status=status)
        if bloqueia:
            with pytest.raises(ConflitoError):
                validar_disponibilidade(db_session, quarto.id, D, D + timedelta(days=3))
        else:
            validar_disponibilidade(db_session, quarto.id, D, D + timedelta(days=3))

    def test_reserva_de_outro_quarto_nao_bloqueia(self, db_session):
        quarto_a = criar_quarto(db_session)
        quarto_b = criar_quarto(db_session)
        criar_reserva(db_session, quarto_a, D, D + timedelta(days=3))
        validar_disponibilidade(db_session, quarto_b.id, D, D + timedelta(days=3))

    def test_nao_expoe_datas_de_outras_reservas(self, db_session):
        quarto = criar_quarto(db_session)
        criar_reserva(db_session, quarto, D, D + timedelta(days=3))
        with pytest.raises(ConflitoError) as erro:
            validar_disponibilidade(
                db_session, quarto.id, D + timedelta(days=1), D + timedelta(days=5)
            )
        # So ecoa o periodo PEDIDO, nunca o da reserva de outro cliente.
        assert erro.value.detalhes == {
            "data_entrada": D + timedelta(days=1),
            "data_saida": D + timedelta(days=5),
        }

    @pytest.mark.parametrize("deslocamento", range(-4, 5))
    @pytest.mark.parametrize("duracao", [1, 2, 3, 5])
    def test_mesma_regra_do_worker_em_todos_os_casos(
        self, db_session, deslocamento, duracao
    ):
        """A API e o worker nao podem discordar sobre o que e sobreposicao."""
        quarto = criar_quarto(db_session)
        existente = (D, D + timedelta(days=3))
        criar_reserva(db_session, quarto, *existente)

        entrada = D + timedelta(days=deslocamento)
        saida = entrada + timedelta(days=duracao)
        esperado = periodos_se_sobrepoem(entrada, saida, *existente)

        if esperado:
            with pytest.raises(ConflitoError):
                validar_disponibilidade(db_session, quarto.id, entrada, saida)
        else:
            validar_disponibilidade(db_session, quarto.id, entrada, saida)


# ---------------------------------------------------------------------------
# Orquestracao
# ---------------------------------------------------------------------------
class TestValidarReserva:
    def test_reserva_valida_passa(self, db_session):
        quarto = criar_quarto(db_session)
        validar_reserva(
            db_session,
            quarto,
            data_entrada=D,
            data_saida=D + timedelta(days=2),
            quantidade_adultos=2,
            idades_criancas=[5],
            hoje=date(2027, 3, 1),
        )

    def test_periodo_invalido_falha_antes_de_consultar_o_banco(self):
        # db=None: se tocasse no banco, quebraria com AttributeError.
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_reserva(
                None,
                quarto_fake(),
                data_entrada=HOJE - timedelta(days=1),
                data_saida=HOJE + timedelta(days=1),
                quantidade_adultos=1,
                idades_criancas=[],
                hoje=HOJE,
            )
        assert erro.value.codigo == "data_entrada_no_passado"

    def test_capacidade_falha_antes_de_consultar_o_banco(self):
        with pytest.raises(RegraDeNegocioError) as erro:
            validar_reserva(
                None,
                quarto_fake(max_adultos=1),
                data_entrada=HOJE + timedelta(days=1),
                data_saida=HOJE + timedelta(days=2),
                quantidade_adultos=2,
                idades_criancas=[],
                hoje=HOJE,
            )
        assert erro.value.codigo == "capacidade_adultos_excedida"
