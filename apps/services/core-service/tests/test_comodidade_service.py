"""Testes unitarios do ComodidadeService (app/services/comodidade_service.py)."""

import uuid

import pytest
from fastapi import HTTPException

from app.models.cidade import Cidade
from app.models.hotel import Hotel
from app.schemas.comodidade import ComodidadeCreateSchema, ComodidadeUpdateSchema
from app.services.comodidade_service import ComodidadeService


@pytest.fixture
def service(db_session):
    return ComodidadeService(db_session)


@pytest.fixture
def hotel(db_session):
    cidade = Cidade(nome="Quixadá", uf="CE")
    db_session.add(cidade)
    db_session.flush()

    hotel = Hotel(
        nome="Hotel Teste", endereco="Rua X, 1", estrelas=3, cidade_id=cidade.id
    )
    db_session.add(hotel)
    db_session.commit()
    db_session.refresh(hotel)
    return hotel


def _criar(service, nome, descricao=None):
    return service.criar(ComodidadeCreateSchema(nome=nome, descricao=descricao))


# --- listar / obter ---------------------------------------------------------
def test_listar_retorna_vazio_sem_comodidades(service):
    assert service.listar() == []


def test_listar_ordena_por_nome(service):
    _criar(service, "Piscina")
    _criar(service, "Academia")
    _criar(service, "Wi-Fi")

    assert [c.nome for c in service.listar()] == ["Academia", "Piscina", "Wi-Fi"]


def test_obter_por_id_retorna_comodidade(service):
    criada = _criar(service, "Piscina")

    assert service.obter_por_id(criada.id).nome == "Piscina"


def test_obter_por_id_inexistente_levanta_404(service):
    with pytest.raises(HTTPException) as exc:
        service.obter_por_id(uuid.uuid4())

    assert exc.value.status_code == 404


# --- criar --------------------------------------------------------------------
def test_criar_persiste_nome_e_descricao(service):
    criada = _criar(service, "Piscina", "Piscina aquecida")

    assert criada.id is not None
    assert criada.nome == "Piscina"
    assert criada.descricao == "Piscina aquecida"


def test_criar_com_nome_duplicado_levanta_409(service):
    _criar(service, "Piscina")

    with pytest.raises(HTTPException) as exc:
        _criar(service, "Piscina")

    assert exc.value.status_code == 409


# --- atualizar ------------------------------------------------------------------
def test_atualizar_altera_nome_e_descricao(service):
    criada = _criar(service, "Piscina")

    atualizada = service.atualizar(
        criada.id, ComodidadeUpdateSchema(nome="Piscina coberta", descricao="Nova")
    )

    assert atualizada.nome == "Piscina coberta"
    assert atualizada.descricao == "Nova"


def test_atualizar_somente_descricao_mantem_nome(service):
    criada = _criar(service, "Piscina", "Antiga")

    atualizada = service.atualizar(criada.id, ComodidadeUpdateSchema(descricao="Nova"))

    assert atualizada.nome == "Piscina"
    assert atualizada.descricao == "Nova"


def test_atualizar_mantendo_o_proprio_nome_nao_gera_conflito(service):
    criada = _criar(service, "Piscina")

    atualizada = service.atualizar(
        criada.id, ComodidadeUpdateSchema(nome="Piscina", descricao="Mesmo nome")
    )

    assert atualizada.descricao == "Mesmo nome"


def test_atualizar_para_nome_de_outra_comodidade_levanta_409(service):
    _criar(service, "Piscina")
    outra = _criar(service, "Academia")

    with pytest.raises(HTTPException) as exc:
        service.atualizar(outra.id, ComodidadeUpdateSchema(nome="Piscina"))

    assert exc.value.status_code == 409


def test_atualizar_inexistente_levanta_404(service):
    with pytest.raises(HTTPException) as exc:
        service.atualizar(uuid.uuid4(), ComodidadeUpdateSchema(nome="X"))

    assert exc.value.status_code == 404


# --- excluir ---------------------------------------------------------------------
def test_excluir_remove_comodidade(service):
    criada = _criar(service, "Piscina")

    service.excluir(criada.id)

    with pytest.raises(HTTPException) as exc:
        service.obter_por_id(criada.id)
    assert exc.value.status_code == 404


def test_excluir_inexistente_levanta_404(service):
    with pytest.raises(HTTPException) as exc:
        service.excluir(uuid.uuid4())

    assert exc.value.status_code == 404


# --- comodidades do hotel ------------------------------------------------------
def test_listar_comodidades_do_hotel_retorna_hotel(service, hotel):
    resultado = service.listar_comodidades_do_hotel(hotel.id)

    assert resultado.id == hotel.id
    assert resultado.comodidades == []


def test_listar_comodidades_do_hotel_inexistente_levanta_404(service):
    with pytest.raises(HTTPException) as exc:
        service.listar_comodidades_do_hotel(uuid.uuid4())

    assert exc.value.status_code == 404


def test_definir_comodidades_do_hotel_associa_comodidades(service, hotel):
    piscina = _criar(service, "Piscina")
    wifi = _criar(service, "Wi-Fi")

    resultado = service.definir_comodidades_do_hotel(hotel.id, [piscina.id, wifi.id])

    assert {c.nome for c in resultado.comodidades} == {"Piscina", "Wi-Fi"}


def test_definir_comodidades_do_hotel_substitui_as_anteriores(service, hotel):
    piscina = _criar(service, "Piscina")
    wifi = _criar(service, "Wi-Fi")
    service.definir_comodidades_do_hotel(hotel.id, [piscina.id])

    resultado = service.definir_comodidades_do_hotel(hotel.id, [wifi.id])

    assert [c.nome for c in resultado.comodidades] == ["Wi-Fi"]


def test_definir_comodidades_do_hotel_com_lista_vazia_limpa_tudo(service, hotel):
    piscina = _criar(service, "Piscina")
    service.definir_comodidades_do_hotel(hotel.id, [piscina.id])

    resultado = service.definir_comodidades_do_hotel(hotel.id, [])

    assert resultado.comodidades == []


def test_definir_comodidades_com_hotel_inexistente_levanta_404(service):
    piscina = _criar(service, "Piscina")

    with pytest.raises(HTTPException) as exc:
        service.definir_comodidades_do_hotel(uuid.uuid4(), [piscina.id])

    assert exc.value.status_code == 404


def test_definir_comodidades_com_comodidade_inexistente_levanta_404(service, hotel):
    with pytest.raises(HTTPException) as exc:
        service.definir_comodidades_do_hotel(hotel.id, [uuid.uuid4()])

    assert exc.value.status_code == 404