"""Testes do tratamento padronizado de erros (Sprint 7) e das regras na rota."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError, OperationalError

from app.api.deps import get_current_user
from app.core.exceptions import (
    ConflitoError,
    RecursoNaoEncontradoError,
    RegraDeNegocioError,
    registrar_handlers,
)
from app.main import app
from app.models.cidade import Cidade
from app.models.evento_outbox import EventoOutbox
from app.models.hotel import Hotel
from app.models.quarto import Quarto
from app.models.reserva import Reserva
from app.services.reserva_service import ReservaInvalidaError


# ---------------------------------------------------------------------------
# App minimo so com os handlers: testa o formato sem depender do resto
# ---------------------------------------------------------------------------
class Corpo(BaseModel):
    nome: str = Field(min_length=3)
    idade: int = Field(ge=0)
    senha: str

    @field_validator("senha")
    @classmethod
    def senha_forte(cls, v):
        if len(v) < 8:
            raise ValueError("senha muito curta")
        return v


def _mini_app() -> TestClient:
    mini = FastAPI()
    registrar_handlers(mini)

    @mini.post("/corpo")
    def corpo(c: Corpo):
        return {"ok": True}

    @mini.get("/item/{item_id}")
    def item(item_id: int):
        return {"id": item_id}

    @mini.get("/regra")
    def regra():
        raise RegraDeNegocioError("Regra violada", codigo="minha_regra", maximo=2)

    @mini.get("/conflito")
    def conflito():
        raise ConflitoError("Ja existe")

    @mini.get("/naoachou")
    def naoachou():
        raise RecursoNaoEncontradoError("Sumiu")

    @mini.get("/reserva-invalida")
    def reserva_invalida():
        raise ReservaInvalidaError("dados ruins")

    @mini.get("/http")
    def http():
        raise HTTPException(status_code=403, detail="Sem permissao")

    @mini.get("/http-headers")
    def http_headers():
        raise HTTPException(
            status_code=401,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @mini.get("/sem-corpo")
    def sem_corpo():
        raise HTTPException(status_code=304)

    @mini.get("/integridade")
    def integridade():
        raise IntegrityError("INSERT x", {}, Exception('UNIQUE "tabela_secreta"'))

    @mini.get("/banco-fora")
    def banco_fora():
        raise OperationalError("SELECT 1", {}, Exception("connection refused host=db"))

    @mini.get("/bug")
    def bug():
        raise RuntimeError("senha do banco: 123")

    return TestClient(mini, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def mini():
    return _mini_app()


class TestFormatoDosErros:
    def test_regra_de_negocio_422_com_detalhes(self, mini):
        r = mini.get("/regra")
        assert r.status_code == 422
        assert r.json() == {
            "detail": "Regra violada",
            "codigo": "minha_regra",
            "detalhes": {"maximo": 2},
        }

    def test_conflito_409_sem_detalhes_omite_a_chave(self, mini):
        r = mini.get("/conflito")
        assert r.status_code == 409
        assert r.json() == {"detail": "Ja existe", "codigo": "conflito"}

    def test_nao_encontrado_404(self, mini):
        r = mini.get("/naoachou")
        assert r.status_code == 404
        assert r.json() == {"detail": "Sumiu", "codigo": "nao_encontrado"}

    def test_reserva_invalida_do_motor_de_preco_vira_422(self, mini):
        r = mini.get("/reserva-invalida")
        assert r.status_code == 422
        assert r.json() == {"detail": "dados ruins", "codigo": "reserva_invalida"}

    def test_http_exception_ganha_codigo_e_mantem_detail(self, mini):
        r = mini.get("/http")
        assert r.status_code == 403
        assert r.json() == {"detail": "Sem permissao", "codigo": "acesso_negado"}

    def test_http_exception_preserva_headers(self, mini):
        r = mini.get("/http-headers")
        assert r.status_code == 401
        assert r.headers["www-authenticate"] == "Bearer"
        assert r.json()["codigo"] == "nao_autenticado"

    def test_rota_inexistente_e_404_com_codigo(self, mini):
        r = mini.get("/nao-existe")
        assert r.status_code == 404
        assert r.json()["codigo"] == "nao_encontrado"

    def test_metodo_nao_permitido_405(self, mini):
        r = mini.delete("/regra")
        assert r.status_code == 405
        assert r.json()["codigo"] == "metodo_nao_permitido"

    def test_304_nao_tem_corpo(self, mini):
        r = mini.get("/sem-corpo")
        assert r.status_code == 304
        assert r.content == b""


class TestErrosDeValidacao:
    def test_um_item_por_campo_com_mensagem_em_portugues(self, mini):
        r = mini.post("/corpo", json={"nome": "ab", "idade": -1})
        corpo = r.json()
        assert r.status_code == 422
        assert corpo["codigo"] == "validacao"
        assert isinstance(corpo["detail"], str)
        por_campo = {e["campo"]: e for e in corpo["erros"]}
        assert por_campo["nome"]["mensagem"] == "Deve ter no minimo 3 caractere(s)"
        assert por_campo["idade"]["mensagem"] == "Deve ser maior ou igual a 0"
        assert por_campo["senha"]["mensagem"] == "Campo obrigatorio"
        assert "nome: Deve ter no minimo 3" in corpo["detail"]

    def test_loc_nao_inclui_a_origem_body(self, mini):
        r = mini.post("/corpo", json={})
        assert all(not e["campo"].startswith("body") for e in r.json()["erros"])

    def test_erro_de_path_param(self, mini):
        r = mini.get("/item/abc")
        assert r.status_code == 422
        erro = r.json()["erros"][0]
        assert erro["campo"] == "item_id"
        assert erro["mensagem"] == "Deve ser um numero inteiro"

    def test_value_error_do_validator_perde_o_prefixo_do_pydantic(self, mini):
        r = mini.post("/corpo", json={"nome": "Maria", "idade": 3, "senha": "123"})
        erro = r.json()["erros"][0]
        assert erro["campo"] == "senha"
        assert erro["mensagem"] == "senha muito curta"

    def test_nao_devolve_o_valor_enviado(self, mini):
        """O FastAPI padrao ecoa `input`: a senha digitada voltava na resposta."""
        r = mini.post("/corpo", json={"nome": "Maria", "idade": 3, "senha": "abc"})
        assert "abc" not in r.text
        assert "input" not in r.text

    def test_json_malformado(self, mini):
        r = mini.post(
            "/corpo",
            content="{nao e json",
            headers={"content-type": "application/json"},
        )
        assert r.status_code == 422
        assert r.json()["codigo"] == "validacao"


class TestErrosDeInfraestrutura:
    def test_integridade_vira_409_sem_vazar_o_banco(self, mini):
        r = mini.get("/integridade")
        assert r.status_code == 409
        assert r.json()["codigo"] == "violacao_integridade"
        assert "tabela_secreta" not in r.text
        assert "INSERT" not in r.text

    def test_banco_fora_do_ar_vira_503(self, mini):
        r = mini.get("/banco-fora")
        assert r.status_code == 503
        assert r.json()["codigo"] == "servico_indisponivel"
        assert "connection refused" not in r.text

    def test_erro_inesperado_vira_500_generico(self, mini):
        r = mini.get("/bug")
        assert r.status_code == 500
        assert r.json() == {
            "detail": "Erro interno do servidor",
            "codigo": "erro_interno",
        }
        assert "123" not in r.text

    def test_erro_inesperado_e_registrado_no_log(self, mini, caplog):
        with caplog.at_level("ERROR"):
            mini.get("/bug")
        assert any("senha do banco" in (r.exc_text or "") for r in caplog.records)


# ---------------------------------------------------------------------------
# Integracao: POST /api/v1/reservas com as validacoes da Sprint 7
# ---------------------------------------------------------------------------
def _autenticar():
    app.dependency_overrides[get_current_user] = lambda: {
        "email": "cliente@hotel.com",
        "nome": "Cliente",
        "is_admin": False,
    }


def _quarto(db, max_adultos=2, max_criancas=1) -> Quarto:
    cidade = Cidade(id=uuid.uuid4(), nome="Banabuiu", uf="CE")
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


def _payload(quarto_id, *, dias_ate_entrada=10, noites=2, adultos=2, criancas=()):
    entrada = date.today() + timedelta(days=dias_ate_entrada)
    return {
        "quarto_id": str(quarto_id),
        "data_entrada": entrada.isoformat(),
        "data_saida": (entrada + timedelta(days=noites)).isoformat(),
        "quantidade_adultos": adultos,
        "idades_criancas": list(criancas),
        "nao_reembolsavel": False,
    }


class TestReservaNaRota:
    URL = "/api/v1/reservas"

    def test_reserva_valida_continua_202(self, client, db_session):
        _autenticar()
        quarto = _quarto(db_session)
        r = client.post(self.URL, json=_payload(quarto.id))
        assert r.status_code == 202, r.text
        assert db_session.query(Reserva).count() == 1

    def test_quarto_inexistente_404_com_codigo(self, client):
        _autenticar()
        r = client.post(self.URL, json=_payload(uuid.uuid4()))
        assert r.status_code == 404
        assert r.json()["detail"] == "Quarto nao encontrado"
        assert r.json()["codigo"] == "nao_encontrado"

    def test_adultos_acima_da_capacidade_422_e_nada_e_gravado(self, client, db_session):
        _autenticar()
        quarto = _quarto(db_session, max_adultos=2)
        r = client.post(self.URL, json=_payload(quarto.id, adultos=3))
        assert r.status_code == 422
        assert r.json()["codigo"] == "capacidade_adultos_excedida"
        assert r.json()["detalhes"] == {"maximo": 2, "informado": 3}
        assert db_session.query(Reserva).count() == 0
        assert db_session.query(EventoOutbox).count() == 0

    def test_criancas_acima_da_capacidade_422(self, client, db_session):
        _autenticar()
        quarto = _quarto(db_session, max_criancas=1)
        r = client.post(self.URL, json=_payload(quarto.id, criancas=[4, 6]))
        assert r.status_code == 422
        assert r.json()["codigo"] == "capacidade_criancas_excedida"
        assert db_session.query(Reserva).count() == 0

    def test_quarto_sem_criancas_tem_mensagem_clara(self, client, db_session):
        _autenticar()
        quarto = _quarto(db_session, max_criancas=0)
        r = client.post(self.URL, json=_payload(quarto.id, criancas=[7]))
        assert r.status_code == 422
        assert r.json()["detail"] == "Este quarto nao aceita criancas"

    def test_estadia_longa_demais_422(self, client, db_session):
        _autenticar()
        quarto = _quarto(db_session)
        r = client.post(self.URL, json=_payload(quarto.id, noites=31))
        assert r.status_code == 422
        assert r.json()["codigo"] == "estadia_muito_longa"

    def test_antecedencia_excessiva_422(self, client, db_session):
        _autenticar()
        quarto = _quarto(db_session)
        r = client.post(self.URL, json=_payload(quarto.id, dias_ate_entrada=400))
        assert r.status_code == 422
        assert r.json()["codigo"] == "reserva_antecipada_demais"

    def test_data_no_passado_e_recusada(self, client, db_session):
        _autenticar()
        quarto = _quarto(db_session)
        r = client.post(self.URL, json=_payload(quarto.id, dias_ate_entrada=-3))
        assert r.status_code == 422
        assert r.json()["codigo"] in ("data_entrada_no_passado", "validacao")
        assert db_session.query(Reserva).count() == 0

    def test_saida_antes_da_entrada_422_com_formato_padrao(self, client, db_session):
        _autenticar()
        quarto = _quarto(db_session)
        r = client.post(self.URL, json=_payload(quarto.id, noites=-1))
        assert r.status_code == 422
        assert isinstance(r.json()["detail"], str)
        assert "codigo" in r.json()

    def test_segunda_reserva_no_mesmo_periodo_409(self, client, db_session):
        _autenticar()
        quarto = _quarto(db_session)
        payload = _payload(quarto.id)
        db_session.add(
            Reserva(
                id=uuid.uuid4(),
                cliente_email="outro@hotel.com",
                quarto_id=quarto.id,
                data_entrada=date.fromisoformat(payload["data_entrada"]),
                data_saida=date.fromisoformat(payload["data_saida"]),
                quantidade_adultos=1,
                quantidade_criancas=0,
                valor_total=Decimal("400.00"),
                status="Confirmada",
            )
        )
        db_session.commit()

        r = client.post(self.URL, json=payload)
        assert r.status_code == 409
        assert r.json()["codigo"] == "quarto_indisponivel"
        assert db_session.query(Reserva).count() == 1  # so a original
        assert db_session.query(EventoOutbox).count() == 0

    def test_checkin_no_dia_do_checkout_de_outro_hospede_e_aceito(
        self, client, db_session
    ):
        _autenticar()
        quarto = _quarto(db_session)
        payload = _payload(quarto.id)
        entrada = date.fromisoformat(payload["data_entrada"])
        db_session.add(
            Reserva(
                id=uuid.uuid4(),
                cliente_email="outro@hotel.com",
                quarto_id=quarto.id,
                data_entrada=entrada - timedelta(days=3),
                data_saida=entrada,  # sai no dia em que o novo hospede entra
                quantidade_adultos=1,
                quantidade_criancas=0,
                valor_total=Decimal("600.00"),
                status="Confirmada",
            )
        )
        db_session.commit()

        r = client.post(self.URL, json=payload)
        assert r.status_code == 202, r.text

    def test_reserva_cancelada_nao_bloqueia_o_quarto(self, client, db_session):
        _autenticar()
        quarto = _quarto(db_session)
        payload = _payload(quarto.id)
        db_session.add(
            Reserva(
                id=uuid.uuid4(),
                cliente_email="outro@hotel.com",
                quarto_id=quarto.id,
                data_entrada=date.fromisoformat(payload["data_entrada"]),
                data_saida=date.fromisoformat(payload["data_saida"]),
                quantidade_adultos=1,
                quantidade_criancas=0,
                valor_total=Decimal("400.00"),
                status="Cancelada",
            )
        )
        db_session.commit()
        assert client.post(self.URL, json=payload).status_code == 202

    def test_corpo_invalido_nao_vaza_o_valor_enviado(self, client):
        _autenticar()
        r = client.post(self.URL, json={"quarto_id": "nao-e-uuid", "segredo": "xyz"})
        assert r.status_code == 422
        assert r.json()["codigo"] == "validacao"
        assert "nao-e-uuid" not in r.text
        assert any(e["campo"] == "quarto_id" for e in r.json()["erros"])
