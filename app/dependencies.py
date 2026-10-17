import logging
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Header, Path, Query, Request
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.configs.settings import get_settings
from app.db.session import get_db
from app.models.payment import IDEMPOTENCY_KEY_MAX_LENGTH
from app.schemas import PaymentStatus
from app.services.exceptions import InvalidSignature
from app.services.signature import is_valid_signature

logger = logging.getLogger("kvitto.dependencies")


def get_idempotency_key(
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", max_length=IDEMPOTENCY_KEY_MAX_LENGTH),
    ] = None,
) -> str | None:
    """Пустой ключ или ключ из одних пробелов считается отсутствующим."""
    key = idempotency_key.strip() if idempotency_key else None
    return key or None


async def verify_signature(
    request: Request,
    x_signature: Annotated[str | None, Header(alias="X-Signature")] = None,
) -> None:
    """Проверяет подпись до разбора тела: без верной подписи ответ 401, даже если тело невалидно."""
    body = await request.body()
    secret = get_settings().webhook_secret.get_secret_value()
    if x_signature is None or not is_valid_signature(body, x_signature, secret):
        logger.warning("Вебхук с неверной подписью отклонён")
        raise InvalidSignature


SessionDep = Annotated[Session, Depends(get_db)]

IdempotencyKeyDep = Annotated[str | None, Depends(get_idempotency_key)]

WebhookSignatureDep = Depends(verify_signature)


class SignedWebhookRoute(APIRoute):
    """Проверяет подпись до разбора JSON: FastAPI читает тело раньше зависимостей ручки."""

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            await verify_signature(request, request.headers.get("x-signature"))
            return await original(request)

        return handler


PaymentIdPath = Annotated[str, Path(min_length=1)]

EmailQuery = Annotated[str | None, Query()]

PaymentStatusQuery = Annotated[PaymentStatus | None, Query()]

LimitQuery = Annotated[int, Query(ge=1, le=100)]

OffsetQuery = Annotated[int, Query(ge=0)]
