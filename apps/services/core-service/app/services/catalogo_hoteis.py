from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import UpdateOne
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.hotel import Hotel


def projetar_hotel(hotel: Hotel, projetado_em: datetime | None = None) -> dict:
    quartos = [
        {
            "id": str(quarto.id),
            "tipo": quarto.tipo,
            "preco_diaria_centavos": int(Decimal(str(quarto.preco_diaria)) * 100),
            "max_adultos": quarto.max_adultos,
            "max_criancas": quarto.max_criancas,
        }
        for quarto in sorted(hotel.quartos, key=lambda item: (item.tipo, str(item.id)))
    ]
    precos = [quarto["preco_diaria_centavos"] for quarto in quartos]

    return {
        "hotel_id": str(hotel.id),
        "nome": hotel.nome,
        "endereco": hotel.endereco,
        "estrelas": hotel.estrelas,
        "categoria_estrelas": hotel.categoria_estrelas,
        "diaria": hotel.diaria,
        "cidade": {
            "id": str(hotel.cidade.id),
            "nome": hotel.cidade.nome,
            "uf": hotel.cidade.uf,
        },
        "comodidades": [
            {
                "id": str(comodidade.id),
                "nome": comodidade.nome,
                "descricao": comodidade.descricao,
            }
            for comodidade in sorted(hotel.comodidades, key=lambda item: item.nome)
        ],
        "quartos": quartos,
        "menor_preco_diaria_centavos": min(precos) if precos else None,
        "projetado_em": projetado_em or datetime.now(timezone.utc),
    }


async def sincronizar_catalogo_hoteis(
    db: Session,
    mongo_db: AsyncIOMotorDatabase,
) -> int:
    return await _sincronizar_hoteis(db, mongo_db)


async def sincronizar_hoteis_por_ids(
    db: Session,
    mongo_db: AsyncIOMotorDatabase,
    hotel_ids: set[UUID],
) -> int:
    if not hotel_ids:
        return 0

    return await _sincronizar_hoteis(db, mongo_db, hotel_ids)


async def _sincronizar_hoteis(
    db: Session,
    mongo_db: AsyncIOMotorDatabase,
    hotel_ids: set[UUID] | None = None,
) -> int:
    consulta = db.query(Hotel).options(
        joinedload(Hotel.cidade),
        selectinload(Hotel.comodidades),
        selectinload(Hotel.quartos),
    )
    if hotel_ids is not None:
        consulta = consulta.filter(Hotel.id.in_(hotel_ids))
    hoteis = consulta.all()

    operacoes = [
        UpdateOne(
            {"hotel_id": documento["hotel_id"]},
            {
                "$set": documento,
                "$setOnInsert": {
                    "descricao": "",
                    "fotos": [],
                    "destaque": False,
                },
            },
            upsert=True,
        )
        for hotel in hoteis
        for documento in [projetar_hotel(hotel)]
    ]
    collection = mongo_db["catalogo_hoteis"]

    if operacoes:
        await collection.bulk_write(operacoes, ordered=False)

    ids_projetados = {operacao._filter["hotel_id"] for operacao in operacoes}
    if hotel_ids is None:
        if ids_projetados:
            await collection.delete_many({"hotel_id": {"$nin": list(ids_projetados)}})
        else:
            await collection.delete_many({})
    else:
        ids_removidos = {str(hotel_id) for hotel_id in hotel_ids} - ids_projetados
        if ids_removidos:
            await collection.delete_many({"hotel_id": {"$in": list(ids_removidos)}})

    return len(operacoes)