from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.dependencies import PaymentServiceDep, WebhookSignatureDep
from app.schemas import WebhookIn
from app.services.exceptions import InvalidTransition, PaymentNotFound

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/bank", response_model=None, dependencies=[WebhookSignatureDep])
def bank_webhook(payload: WebhookIn, service: PaymentServiceDep) -> JSONResponse:
    try:
        service.apply_bank_status(payload.payment_id, payload.status)
    except PaymentNotFound:
        raise HTTPException(status_code=404, detail="Платёж не найден") from None
    except InvalidTransition:
        return JSONResponse(status_code=409, content={"error": "invalid_transition"})
    return JSONResponse(status_code=200, content={"result": "ok"})
