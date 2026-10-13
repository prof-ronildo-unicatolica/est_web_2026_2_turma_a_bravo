import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)


async def ensure_catalogo_hoteis(db: AsyncIOMotorDatabase):
    collection_name = "catalogo_hoteis"
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "hotel_id",
                "nome",
                "endereco",
                "estrelas",
                "categoria_estrelas",
                "diaria",
                "cidade",
                "comodidades",
                "quartos",
                "menor_preco_diaria_centavos",
                "projetado_em",
            ],
            "properties": {
                "hotel_id": {"bsonType": "string"},
                "nome": {"bsonType": "string", "minLength": 2},
                "endereco": {"bsonType": "string"},
                "estrelas": {"bsonType": "int", "minimum": 1, "maximum": 5},
                "categoria_estrelas": {
                    "enum": ["Economico", "Padrao", "Luxo"]
                },
                "diaria": {"bsonType": "string"},
                "cidade": {
                    "bsonType": "object",
                    "required": ["id", "nome", "uf"],
                    "properties": {
                        "id": {"bsonType": "string"},
                        "nome": {"bsonType": "string"},
                        "uf": {"bsonType": "string"},
                    },
                },
                "comodidades": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["id", "nome"],
                        "properties": {
                            "id": {"bsonType": "string"},
                            "nome": {"bsonType": "string"},
                            "descricao": {"bsonType": ["string", "null"]},
                        },
                    },
                },
                "quartos": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": [
                            "id",
                            "tipo",
                            "preco_diaria_centavos",
                            "max_adultos",
                            "max_criancas",
                        ],
                        "properties": {
                            "id": {"bsonType": "string"},
                            "tipo": {"bsonType": "string"},
                            "preco_diaria_centavos": {
                                "bsonType": ["int", "long"],
                                "minimum": 0,
                            },
                            "max_adultos": {"bsonType": "int", "minimum": 1},
                            "max_criancas": {"bsonType": "int", "minimum": 0},
                        },
                    },
                },
                "menor_preco_diaria_centavos": {
                    "bsonType": ["int", "long", "null"],
                    "minimum": 0,
                },
                "projetado_em": {"bsonType": "date"},
                "descricao": {"bsonType": "string"},
                "fotos": {"bsonType": "array", "items": {"bsonType": "string"}},
                "destaque": {"bsonType": "bool"},
            },
        }
    }

    collections = await db.list_collection_names()
    if collection_name not in collections:
        await db.create_collection(
            collection_name,
            validator=validator,
            validationLevel="moderate",
            validationAction="error",
        )
    else:
        await db.command(
            "collMod",
            collection_name,
            validator=validator,
            validationLevel="moderate",
            validationAction="error",
        )

    collection = db[collection_name]
    await collection.create_index("hotel_id", unique=True, name="uq_catalogo_hoteis_hotel_id")
    await collection.create_index(
        [
            ("cidade.id", 1),
            ("estrelas", 1),
            ("menor_preco_diaria_centavos", 1),
        ],
        name="ix_catalogo_hoteis_filtros",
    )
    await collection.create_index(
        [
            ("nome", "text"),
            ("cidade.nome", "text"),
            ("descricao", "text"),
            ("comodidades.nome", "text"),
        ],
        name="tx_catalogo_hoteis_busca",
    )


async def seed_mongo_users(db: AsyncIOMotorDatabase):
    try:
        users_collection = db["users"]
        existing_user = await users_collection.find_one({"email": "admin@hotel.com"})
        if not existing_user:
            hashed_password = pwd_context.hash("admin123")
            admin_user = {
                "username": "admin",
                "email": "admin@hotel.com",
                "password_hash": hashed_password,
                "role": "admin_master",
                "active": True,
            }
            await users_collection.insert_one(admin_user)
            logger.info("MongoDB seed user created successfully.")
        else:
            logger.info("MongoDB seed user already exists.")
    except Exception as e:
        logger.error(f"Error seeding MongoDB: {str(e)}")
