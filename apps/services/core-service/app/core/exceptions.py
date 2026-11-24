"""Excecoes de dominio e tratamento padronizado de erros da API (Sprint 7).

Toda resposta de erro tem o mesmo formato:

    {
      "detail":  "Mensagem legivel para exibir ao usuario",
      "codigo":  "identificador_estavel_para_o_frontend",
      "detalhes": {...},   # opcional: dados da regra violada (limites etc.)
      "erros":   [...]     # opcional: so em erro de validacao (um item por campo)
    }

`detail` continua sendo SEMPRE o texto principal, como o FastAPI faz por padrao
(com uma diferenca: em erro de validacao ele vira um texto unico, e nao uma
lista). O frontend pode exibir `detail` direto e usar `codigo` para decidir o
que fazer (ex.: destacar um campo, oferecer outras datas).

Como usar nas rotas/services:

    raise RegraDeNegocioError("Mensagem", codigo="meu_codigo", maximo=2)   # 422
    raise ConflitoError("Mensagem", codigo="quarto_indisponivel")          # 409
    raise RecursoNaoEncontradoError("Quarto nao encontrado")               # 404

e, uma unica vez em main.py:  registrar_handlers(app)
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.reserva_service import ReservaInvalidaError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Excecoes de dominio
# ---------------------------------------------------------------------------
class ErroDeNegocio(Exception):
    """Base: um erro esperado, causado por uma regra de negocio."""

    status_code = 400
    codigo = "erro_de_negocio"

    def __init__(self, mensagem: str, *, codigo: str | None = None, **detalhes):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if codigo is not None:
            self.codigo = codigo
        self.detalhes = detalhes


class RegraDeNegocioError(ErroDeNegocio):
    """Dados validos no formato, mas que violam uma regra (ex.: capacidade)."""

    status_code = 422
    codigo = "regra_de_negocio"


class RecursoNaoEncontradoError(ErroDeNegocio):
    status_code = 404
    codigo = "nao_encontrado"


class ConflitoError(ErroDeNegocio):
    """O pedido conflita com o estado atual (ex.: quarto ja reservado)."""

    status_code = 409
    codigo = "conflito"


# ---------------------------------------------------------------------------
# Formatacao
# ---------------------------------------------------------------------------
_CODIGOS_HTTP = {
    400: "requisicao_invalida",
    401: "nao_autenticado",
    403: "acesso_negado",
    404: "nao_encontrado",
    405: "metodo_nao_permitido",
    409: "conflito",
    422: "validacao",
    429: "muitas_requisicoes",
    500: "erro_interno",
    503: "servico_indisponivel",
}

_MENSAGENS_VALIDACAO = {
    "missing": "Campo obrigatorio",
    "string_too_short": "Deve ter no minimo {min_length} caractere(s)",
    "string_too_long": "Deve ter no maximo {max_length} caractere(s)",
    "too_short": "Deve ter no minimo {min_length} item(ns)",
    "too_long": "Deve ter no maximo {max_length} item(ns)",
    "greater_than": "Deve ser maior que {gt}",
    "greater_than_equal": "Deve ser maior ou igual a {ge}",
    "less_than": "Deve ser menor que {lt}",
    "less_than_equal": "Deve ser menor ou igual a {le}",
    "int_parsing": "Deve ser um numero inteiro",
    "int_from_float": "Deve ser um numero inteiro",
    "int_type": "Deve ser um numero inteiro",
    "decimal_parsing": "Deve ser um numero decimal valido",
    "decimal_type": "Deve ser um numero decimal valido",
    "bool_parsing": "Deve ser verdadeiro ou falso",
    "string_type": "Deve ser um texto",
    "list_type": "Deve ser uma lista",
    "uuid_parsing": "Identificador (UUID) invalido",
    "uuid_type": "Identificador (UUID) invalido",
    "date_parsing": "Data invalida (use AAAA-MM-DD)",
    "date_from_datetime_parsing": "Data invalida (use AAAA-MM-DD)",
    "date_type": "Data invalida (use AAAA-MM-DD)",
    "time_parsing": "Horario invalido (use HH:MM ou HH:MM:SS)",
    "time_type": "Horario invalido (use HH:MM ou HH:MM:SS)",
    "json_invalid": "JSON invalido no corpo da requisicao",
}

_ORIGENS = {"body", "query", "path", "header", "cookie"}


def _corpo(detail, codigo: str, **extras) -> dict:
    corpo = {"detail": detail, "codigo": codigo}
    for chave, valor in extras.items():
        if valor:  # omite {} e [] para manter a resposta enxuta
            corpo[chave] = valor
    return corpo


def _resposta(status_code: int, corpo: dict, headers: dict | None = None):
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(corpo),
        headers=headers,
    )


def _formatar_erro_validacao(erro: dict) -> dict:
    """Converte um erro do Pydantic em {campo, mensagem, tipo}.

    Nunca copia o valor enviado (`input`): o FastAPI padrao o devolve e, num
    cadastro, isso reflete a senha digitada de volta na resposta.
    """
    loc = [str(parte) for parte in erro.get("loc", ())]
    if loc and loc[0] in _ORIGENS:
        loc = loc[1:]
    campo = ".".join(loc) or None

    tipo = erro.get("type", "")
    modelo = _MENSAGENS_VALIDACAO.get(tipo)
    if modelo is not None:
        try:
            mensagem = modelo.format(**(erro.get("ctx") or {}))
        except (KeyError, IndexError):
            mensagem = modelo.split("{")[0].strip()
    else:
        mensagem = str(erro.get("msg", "Valor invalido"))
        # Erros levantados por ValueError nos validators vem com este prefixo.
        mensagem = mensagem.removeprefix("Value error, ")

    return {"campo": campo, "mensagem": mensagem, "tipo": tipo}


def _corpo_permitido(status_code: int) -> bool:
    return not (status_code < 200 or status_code in (204, 205, 304))


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
async def _tratar_erro_de_negocio(request: Request, exc: ErroDeNegocio):
    return _resposta(
        exc.status_code,
        _corpo(exc.mensagem, exc.codigo, detalhes=exc.detalhes),
    )


async def _tratar_reserva_invalida(request: Request, exc: ReservaInvalidaError):
    return _resposta(422, _corpo(str(exc), "reserva_invalida"))


async def _tratar_validacao(request: Request, exc: RequestValidationError):
    erros = [_formatar_erro_validacao(e) for e in exc.errors()]
    resumo = "; ".join(
        f"{e['campo']}: {e['mensagem']}" if e["campo"] else e["mensagem"] for e in erros
    )
    return _resposta(
        422,
        _corpo(resumo or "Dados invalidos", "validacao", erros=erros),
    )


async def _tratar_http(request: Request, exc: StarletteHTTPException):
    headers = getattr(exc, "headers", None)
    if not _corpo_permitido(exc.status_code):
        return Response(status_code=exc.status_code, headers=headers)
    codigo = _CODIGOS_HTTP.get(exc.status_code, f"http_{exc.status_code}")
    return _resposta(exc.status_code, _corpo(exc.detail, codigo), headers)


async def _tratar_integridade(request: Request, exc: IntegrityError):
    # O detalhe do banco (nome de tabela/constraint) fica so no log.
    logger.warning("Violacao de integridade em %s: %s", request.url.path, exc.orig)
    return _resposta(
        409,
        _corpo(
            "A operacao viola uma regra de integridade dos dados "
            "(registro duplicado ou referencia inexistente)",
            "violacao_integridade",
        ),
    )


async def _tratar_banco_indisponivel(request: Request, exc: OperationalError):
    logger.error("Banco de dados indisponivel em %s: %s", request.url.path, exc.orig)
    return _resposta(
        503,
        _corpo(
            "Servico temporariamente indisponivel. Tente novamente em instantes",
            "servico_indisponivel",
        ),
    )


async def _tratar_erro_inesperado(request: Request, exc: Exception):
    logger.exception(
        "Erro nao tratado em %s %s", request.method, request.url.path, exc_info=exc
    )
    # Mensagem generica: stack trace e detalhes internos nunca vao ao cliente.
    return _resposta(500, _corpo("Erro interno do servidor", "erro_interno"))


def registrar_handlers(app: FastAPI) -> None:
    """Instala o formato padrao de erro. Chamar uma vez, logo apos criar o app."""
    app.add_exception_handler(ErroDeNegocio, _tratar_erro_de_negocio)
    app.add_exception_handler(ReservaInvalidaError, _tratar_reserva_invalida)
    app.add_exception_handler(RequestValidationError, _tratar_validacao)
    app.add_exception_handler(StarletteHTTPException, _tratar_http)
    app.add_exception_handler(IntegrityError, _tratar_integridade)
    app.add_exception_handler(OperationalError, _tratar_banco_indisponivel)
    app.add_exception_handler(Exception, _tratar_erro_inesperado)
