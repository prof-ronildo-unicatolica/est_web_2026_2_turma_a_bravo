"""Testes unitarios do TutorialService (app/services/tutorial_service.py).

O publish_event (RabbitMQ) e substituido por um mock: nao precisa de Docker.
A funcao assincrona e executada com asyncio.run, sem depender de pytest-asyncio.
"""

import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest

from app.models.tutorial import (
    Disciplina,
    Linguagem,
    Professor,
    ProfessorDetail,
    Stack,
    Tecnologia,
)
from app.schemas.tutorial import DisciplinaCreateSchema, ProfessorCreateSchema
from app.services.tutorial_service import TutorialService


@pytest.fixture
def service(db_session):
    return TutorialService(db_session)


@pytest.fixture
def publish_mock(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr("app.services.tutorial_service.publish_event", mock)
    return mock


def _professor_payload(**kw):
    dados = dict(
        nome="Ronildo",
        email="ronildo@unicatolica.edu.br",
        sala="Sala 10",
        biografia="Professor de Estagio",
        biografia_mapa=None,
    )
    dados.update(kw)
    return ProfessorCreateSchema(**dados)


# --- get_sobre_data --------------------------------------------------------------
def test_get_sobre_data_sem_dados_retorna_estrutura_vazia(service):
    dados = service.get_sobre_data()

    assert dados == {
        "equipe": "Bravo",
        "ano": 2026,
        "semestre": 2,
        "professor": None,
        "disciplinas": [],
        "stacks": [],
    }


def test_get_sobre_data_professor_sem_detalhe_usa_valores_padrao(service, db_session):
    db_session.add(Professor(nome="Sem Detalhe", email="sd@x.com"))
    db_session.commit()

    professor = service.get_sobre_data()["professor"]

    assert professor["nome"] == "Sem Detalhe"
    assert professor["sala"] == ""
    assert professor["biografia"] == ""
    assert professor["biografia_mapa"] is None


def test_get_sobre_data_com_professor_disciplinas_e_stacks(service, db_session):
    professor = Professor(nome="Ronildo", email="r@x.com")
    db_session.add(professor)
    db_session.flush()
    db_session.add(
        ProfessorDetail(
            professor_id=professor.id,
            sala="Sala 10",
            biografia="Bio",
            biografia_mapa={"lat": -4.97, "lng": -39.01},
        )
    )

    stack = Stack(nome="Backend")
    db_session.add(stack)
    db_session.flush()
    tecnologia = Tecnologia(nome="FastAPI", stack_id=stack.id)
    linguagem = Linguagem(nome="Python")
    tecnologia.linguagens.append(linguagem)
    db_session.add_all([tecnologia, linguagem])

    disciplina = Disciplina(
        nome="Estagio II", ano=2026, semestre=2, professor_id=professor.id
    )
    disciplina.tecnologias.append(tecnologia)
    db_session.add(disciplina)
    db_session.commit()

    dados = service.get_sobre_data()

    assert dados["professor"] == {
        "nome": "Ronildo",
        "email": "r@x.com",
        "sala": "Sala 10",
        "biografia": "Bio",
        "biografia_mapa": {"lat": -4.97, "lng": -39.01},
    }
    assert dados["disciplinas"] == [
        {"nome": "Estagio II", "ano": 2026, "semestre": 2, "tecnologias": ["FastAPI"]}
    ]
    assert dados["stacks"] == [
        {
            "nome": "Backend",
            "tecnologias": [{"nome": "FastAPI", "linguagens": ["Python"]}],
        }
    ]


# --- professores ------------------------------------------------------------------
def test_create_professor_persiste_professor_e_detalhe(service):
    professor = service.create_professor(_professor_payload())

    assert professor.id is not None
    assert professor.nome == "Ronildo"
    assert professor.detalhe.sala == "Sala 10"
    assert professor.detalhe.biografia == "Professor de Estagio"


def test_create_professor_aceita_biografia_mapa(service):
    payload = _professor_payload(biografia_mapa={"lat": 1, "lng": 2})

    professor = service.create_professor(payload)

    assert professor.detalhe.biografia_mapa == {"lat": 1, "lng": 2}


def test_get_professor_by_id_retorna_professor(service):
    criado = service.create_professor(_professor_payload())

    encontrado = service.get_professor_by_id(criado.id)

    assert encontrado.email == "ronildo@unicatolica.edu.br"


def test_get_professor_by_id_inexistente_retorna_none(service):
    assert service.get_professor_by_id(uuid.uuid4()) is None


# --- disciplinas (async + evento) ---------------------------------------------------
def test_create_disciplina_persiste_e_publica_evento(service, publish_mock):
    professor = service.create_professor(_professor_payload())
    payload = DisciplinaCreateSchema(
        nome="Estagio II", ano=2026, semestre=2, professor_id=str(professor.id)
    )

    disciplina = asyncio.run(service.create_disciplina(payload))

    assert disciplina.id is not None
    assert disciplina.nome == "Estagio II"
    assert disciplina.professor_id == professor.id

    publish_mock.assert_awaited_once()
    fila, evento = publish_mock.await_args.args
    assert fila == "audit.logs"
    assert evento == {
        "evento": "disciplina.criada",
        "disciplina_id": str(disciplina.id),
        "nome": "Estagio II",
        "ano": 2026,
        "semestre": 2,
        "professor_id": str(professor.id),
    }


def test_create_disciplina_aceita_professor_id_como_uuid(service, publish_mock):
    professor = service.create_professor(_professor_payload())
    payload = DisciplinaCreateSchema(
        nome="Banco de Dados", ano=2026, semestre=1, professor_id=professor.id
    )

    disciplina = asyncio.run(service.create_disciplina(payload))

    assert disciplina.professor_id == professor.id
    publish_mock.assert_awaited_once()