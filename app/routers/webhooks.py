from fastapi import APIRouter

from app import swagger
from app.dependencies import PaymentServiceDep, WebhookBody, WebhookSignatureDep
from app.schemas import WebhookOut

router = APIRouter(tags=["webhooks"])


@router.post(
    "/webhooks/bank",
    response_model=WebhookOut,
    summary="Вебхук банка: смена статуса платежа",
    description=swagger.bank_webhook_description,
    responses=swagger.bank_webhook_responses,
    dependencies=[WebhookSignatureDep],
)
def bank_webhook(payload: WebhookBody, service: PaymentServiceDep) -> WebhookOut:
    service.apply_bank_status(payload.payment_id, payload.status)
    return WebhookOut(result="ok")
