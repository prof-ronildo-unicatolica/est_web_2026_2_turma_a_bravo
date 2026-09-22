from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.comodidades import hotel_comodidades_router, router as comodidades_router
from app.api.v1.cidades import router as cidades_router
from app.api.v1.health import router as health_router
from app.api.v1.hotel import router as hotel_router
from app.api.v1.sobre import router as sobre_router
from app.core.config import settings
from app.core.database import get_mongo_db
from app.core.seed_mongo import seed_mongo_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_db = get_mongo_db()
    await seed_mongo_users(mongo_db)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

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
app.include_router(comodidades_router, prefix=settings.API_V1_STR)
app.include_router(hotel_comodidades_router, prefix=settings.API_V1_STR)
app.include_router(cidades_router, prefix=settings.API_V1_STR)
app.include_router(hotel_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {"message": "Bem-vindo ao Core Service do Sistema de Reservas!"}