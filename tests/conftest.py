import os
from collections.abc import AsyncIterator

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["WEBHOOK_SECRET"] = "test-webhook-secret"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.configs.settings import get_settings
from app.db import session as database
from app.main import app, prepare_database
from app.models import Payment


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    get_settings.cache_clear()
    prepare_database()
    with database.SessionLocal() as session:
        session.execute(delete(Payment))
        session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
