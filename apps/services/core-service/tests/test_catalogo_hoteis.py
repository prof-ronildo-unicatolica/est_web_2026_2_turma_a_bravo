import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.core.seed_mongo import ensure_catalogo_hoteis
from app.services.catalogo_hoteis import (
    projetar_hotel,
    sincronizar_catalogo_hoteis,
    sincronizar_hoteis_por_ids,
)


def hotel_de_teste():
    hotel_id = uuid4()
    cidade_id = uuid4()
    comodidade_id = uuid4()
    quarto_id = uuid4()
    return SimpleNamespace(
        id=hotel_id,
        nome="Hotel do Sol",
        endereco="Av. das Dunas, 200",
        estrelas=4,
        categoria_estrelas="Luxo",
        diaria="R$ 0",
        cidade=SimpleNamespace(id=cidade_id, nome="Natal", uf="RN"),
        comodidades=[
            SimpleNamespace(
                id=comodidade_id,
                nome="Piscina",
                descricao="Piscina externa",
            )
        ],
        quartos=[
            SimpleNamespace(
                id=quarto_id,
                tipo="Duplo",
                preco_diaria=Decimal("175.50"),
                max_adultos=2,
                max_criancas=1,
            )
        ],
    )


def test_cria_colecao_catalogo_hoteis_com_validacao_e_indices():
    db = MagicMock()
    db.list_collection_names = AsyncMock(return_value=[])
    db.create_collection = AsyncMock()
    collection = MagicMock()
    collection.create_index = AsyncMock()
    db.__getitem__.return_value = collection

    asyncio.run(ensure_catalogo_hoteis(db))

    db.create_collection.assert_awaited_once()
    args = db.create_collection.await_args
    assert args.args == ("catalogo_hoteis",)
    schema = args.kwargs["validator"]["$jsonSchema"]
    assert "hotel_id" in schema["required"]
    assert {"cidade", "comodidades", "quartos"}.issubset(schema["properties"])
    assert "menor_preco_diaria_centavos" in schema["properties"]
    quarto_fields = schema["properties"]["quartos"]["items"]["properties"]
    assert quarto_fields["preco_diaria_centavos"]["bsonType"] == ["int", "long"]
    assert args.kwargs["validationLevel"] == "moderate"
    index_calls = collection.create_index.await_args_list
    assert [call.args[0] for call in index_calls] == [
        "hotel_id",
        [
            ("cidade.id", 1),
            ("estrelas", 1),
            ("menor_preco_diaria_centavos", 1),
        ],
        [
            ("nome", "text"),
            ("cidade.nome", "text"),
            ("descricao", "text"),
            ("comodidades.nome", "text"),
        ],
    ]
    assert index_calls[0].kwargs["unique"] is True


def test_atualiza_colecao_catalogo_hoteis_existente():
    db = MagicMock()
    db.list_collection_names = AsyncMock(return_value=["catalogo_hoteis"])
    db.command = AsyncMock()
    collection = MagicMock()
    collection.create_index = AsyncMock()
    db.__getitem__.return_value = collection

    asyncio.run(ensure_catalogo_hoteis(db))

    db.create_collection.assert_not_called()
    db.command.assert_awaited_once()
    assert db.command.await_args.args[:2] == ("collMod", "catalogo_hoteis")
    assert db.command.await_args.kwargs["validationAction"] == "error"
    assert collection.create_index.await_count == 3


def test_projeta_hotel_com_cidade_comodidades_e_quartos_embutidos():
    hotel = hotel_de_teste()
    projetado_em = datetime(2026, 10, 13, tzinfo=timezone.utc)

    documento = projetar_hotel(hotel, projetado_em)

    assert documento["hotel_id"] == str(hotel.id)
    assert documento["cidade"] == {
        "id": str(hotel.cidade.id),
        "nome": "Natal",
        "uf": "RN",
    }
    assert documento["comodidades"][0]["nome"] == "Piscina"
    assert documento["quartos"][0]["preco_diaria_centavos"] == 17550
    assert documento["menor_preco_diaria_centavos"] == 17550
    assert documento["projetado_em"] == projetado_em


def test_sincroniza_hotel_com_upsert_preservando_campos_editoriais():
    hotel = hotel_de_teste()
    db = MagicMock()
    db.query.return_value.options.return_value.all.return_value = [hotel]
    mongo_db = MagicMock()
    collection = MagicMock()
    collection.bulk_write = AsyncMock()
    collection.delete_many = AsyncMock()
    mongo_db.__getitem__.return_value = collection

    total = asyncio.run(sincronizar_catalogo_hoteis(db, mongo_db))

    assert total == 1
    operacoes = collection.bulk_write.await_args.args[0]
    assert len(operacoes) == 1
    assert operacoes[0]._filter == {"hotel_id": str(hotel.id)}
    assert operacoes[0]._upsert is True
    assert operacoes[0]._doc["$set"]["cidade"]["nome"] == "Natal"
    assert operacoes[0]._doc["$setOnInsert"]["fotos"] == []
    collection.delete_many.assert_awaited_once()
    assert collection.delete_many.await_args.args[0] == {
        "hotel_id": {"$nin": [str(hotel.id)]}
    }


def test_sincroniza_apenas_hoteis_afetados():
    hotel = hotel_de_teste()
    db = MagicMock()
    query = db.query.return_value
    query.options.return_value = query
    query.filter.return_value = query
    query.all.return_value = [hotel]
    mongo_db = MagicMock()
    collection = MagicMock()
    collection.bulk_write = AsyncMock()
    collection.delete_many = AsyncMock()
    mongo_db.__getitem__.return_value = collection

    total = asyncio.run(
        sincronizar_hoteis_por_ids(db, mongo_db, {hotel.id})
    )

    assert total == 1
    query.filter.assert_called_once()
    collection.bulk_write.assert_awaited_once()
    collection.delete_many.assert_not_awaited()


def test_remove_do_catalogo_hotel_que_nao_existe_mais_no_postgres():
    hotel_id = uuid4()
    db = MagicMock()
    query = db.query.return_value
    query.options.return_value = query
    query.filter.return_value = query
    query.all.return_value = []
    mongo_db = MagicMock()
    collection = MagicMock()
    collection.bulk_write = AsyncMock()
    collection.delete_many = AsyncMock()
    mongo_db.__getitem__.return_value = collection

    total = asyncio.run(
        sincronizar_hoteis_por_ids(db, mongo_db, {hotel_id})
    )

    assert total == 0
    collection.bulk_write.assert_not_awaited()
    collection.delete_many.assert_awaited_once_with(
        {"hotel_id": {"$in": [str(hotel_id)]}}
    )
