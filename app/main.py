import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  регистрирует таблицы в Base.metadata
from app.configs.settings import get_settings
from app.db import session as database
from app.db.base import Base
from app.db.seed import seed_tariffs
from app.routers import payments, tariffs, webhooks

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
        seed_tariffs(session)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    prepare_database()
    logger.info("Сервис платежей запущен")
    yield
    logger.info("Сервис платежей остановлен")


app = FastAPI(title="Квитто — платежи", lifespan=lifespan)
app.include_router(tariffs.router)
app.include_router(payments.router)
app.include_router(webhooks.router)
