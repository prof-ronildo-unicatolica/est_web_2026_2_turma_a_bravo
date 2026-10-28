from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.cidades import router as cidades_router
from app.api.v1.comodidades import hotel_comodidades_router
from app.api.v1.comodidades import router as comodidades_router
from app.api.v1.gestao import router as gestao_router
from app.api.v1.health import router as health_router
from app.api.v1.hotel import router as hotel_router
from app.api.v1.quartos import router as quartos_router
from app.api.v1.tarifas_temporada import router as tarifas_temporada_router
from app.api.v1.servicos_adicionais import router as servicos_adicionais_router
from app.api.v1.sobre import router as sobre_router
from app.core.config import settings
from app.core.database import SessionLocal, get_mongo_db
from app.core.seed_mongo import ensure_catalogo_hoteis, seed_mongo_users
from app.services.catalogo_hoteis import sincronizar_catalogo_hoteis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Evento de inicializacao: Popular/Semear o MongoDB
    mongo_db = get_mongo_db()
    await ensure_catalogo_hoteis(mongo_db)
    with SessionLocal() as postgres_db:
        await sincronizar_catalogo_hoteis(postgres_db, mongo_db)
    await seed_mongo_users(mongo_db)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configuracao de CORS para permitir acesso do Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(sobre_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(gestao_router, prefix=settings.API_V1_STR)
app.include_router(comodidades_router, prefix=settings.API_V1_STR)
app.include_router(hotel_comodidades_router, prefix=settings.API_V1_STR)
app.include_router(cidades_router, prefix=settings.API_V1_STR)
app.include_router(hotel_router, prefix=settings.API_V1_STR)
app.include_router(quartos_router, prefix=settings.API_V1_STR)
app.include_router(tarifas_temporada_router, prefix=settings.API_V1_STR)
app.include_router(servicos_adicionais_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {"message": "Bem-vindo ao Core Service do Sistema de Reservas!"}