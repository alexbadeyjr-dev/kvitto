import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import (
    models,  # noqa: F401  регистрирует таблицы в Base.metadata
    swagger,
)
from app.configs.settings import get_settings
from app.db import session as database
from app.db.base import Base
from app.routers import payments, tariffs, webhooks
from app.services.exceptions import AppError
from app.services.tariffs import seed_default_tariffs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("kvitto")


def prepare_database() -> None:
    settings = get_settings()
    if database.engine is None:
        database.init_engine(settings.database_url)
    if database.engine is None or database.SessionLocal is None:
        raise RuntimeError("База не инициализирована")
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(database.engine)
    with database.SessionLocal() as session:
        seed_default_tariffs(session)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    prepare_database()
    logger.info("Сервис платежей запущен")
    yield
    logger.info("Сервис платежей остановлен")


app = FastAPI(
    title="Квитто — платежи",
    version="1.0.0",
    description=swagger.openapi_description,
    openapi_tags=swagger.openapi_tags,
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.as_dict())

app.include_router(tariffs.router)
app.include_router(payments.router)
app.include_router(webhooks.router)
