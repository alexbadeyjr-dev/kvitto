from fastapi import APIRouter

from app import swagger
from app.dependencies import SessionDep, WebhookSignatureDep
from app.schemas import WebhookIn, WebhookOut
from app.services import payments as payment_service

router = APIRouter(tags=["webhooks"])


@router.post(
    "/webhooks/bank",
    response_model=WebhookOut,
    summary="Вебхук банка: смена статуса платежа",
    description=swagger.bank_webhook_description,
    responses=swagger.bank_webhook_responses,
    openapi_extra=swagger.bank_webhook_openapi_extra,
    dependencies=[WebhookSignatureDep],
)
def bank_webhook(payload: WebhookIn, db: SessionDep) -> WebhookOut:
    payment_service.apply_bank_status(db, payload.payment_id, payload.status)
    return WebhookOut(result="ok")
