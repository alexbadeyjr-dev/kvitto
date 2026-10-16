import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.configs.settings import get_settings
from app.db.session import get_db
from app.schemas import WebhookIn
from app.services.exceptions import InvalidTransition, PaymentNotFound
from app.services.payments import apply_bank_status
from app.services.signature import is_valid_signature

logger = logging.getLogger("kvitto.webhooks")

router = APIRouter(tags=["webhooks"])


async def verify_signature(
    request: Request,
    x_signature: Annotated[str | None, Header(alias="X-Signature")] = None,
) -> None:
    """Проверяет подпись до разбора тела: без верной подписи ответ 401, даже если тело невалидно."""
    body = await request.body()
    secret = get_settings().webhook_secret.get_secret_value()
    if x_signature is None or not is_valid_signature(body, x_signature, secret):
        logger.warning("Вебхук с неверной подписью отклонён")
        raise HTTPException(status_code=401, detail="Неверная подпись")


@router.post("/webhooks/bank", response_model=None, dependencies=[Depends(verify_signature)])
def bank_webhook(payload: WebhookIn, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        apply_bank_status(db, payload.payment_id, payload.status)
    except PaymentNotFound:
        raise HTTPException(status_code=404, detail="Платёж не найден") from None
    except InvalidTransition:
        return JSONResponse(status_code=409, content={"error": "invalid_transition"})
    return JSONResponse(status_code=200, content={"result": "ok"})
