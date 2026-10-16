import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Path, Query, Request
from sqlalchemy.orm import Session

from app.configs.settings import get_settings
from app.db.session import get_db
from app.schemas import PaymentStatus
from app.services.payments import PaymentService
from app.services.signature import is_valid_signature
from app.services.tariffs import TariffService

logger = logging.getLogger("kvitto.dependencies")


def get_idempotency_key(
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", description="Повтор с тем же ключом вернёт уже созданный платёж"),
    ] = None,
) -> str | None:
    """Пустой ключ или ключ из одних пробелов считается отсутствующим."""
    key = idempotency_key.strip() if idempotency_key else None
    return key or None


async def verify_signature(
    request: Request,
    x_signature: Annotated[
        str | None,
        Header(alias="X-Signature", description="HMAC-SHA256 от тела запроса в hex"),
    ] = None,
) -> None:
    """Проверяет подпись до разбора тела: без верной подписи ответ 401, даже если тело невалидно."""
    body = await request.body()
    secret = get_settings().webhook_secret.get_secret_value()
    if x_signature is None or not is_valid_signature(body, x_signature, secret):
        logger.warning("Вебхук с неверной подписью отклонён")
        raise HTTPException(status_code=401, detail="Неверная подпись")


SessionDep = Annotated[Session, Depends(get_db)]


def get_payment_service(db: SessionDep) -> PaymentService:
    return PaymentService(db)


def get_tariff_service(db: SessionDep) -> TariffService:
    return TariffService(db)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]

TariffServiceDep = Annotated[TariffService, Depends(get_tariff_service)]

IdempotencyKeyDep = Annotated[str | None, Depends(get_idempotency_key)]

WebhookSignatureDep = Depends(verify_signature)

PaymentIdPath = Annotated[str, Path(min_length=1, description="Идентификатор платежа")]

EmailQuery = Annotated[str | None, Query(description="Email без учёта регистра")]

PaymentStatusQuery = Annotated[PaymentStatus | None, Query(description="Статус платежа")]

LimitQuery = Annotated[int, Query(ge=1, le=100, description="Сколько записей вернуть, до 100")]

OffsetQuery = Annotated[int, Query(ge=0, description="Сколько записей пропустить")]
