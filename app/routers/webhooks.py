from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import WebhookIn
from app.services.exceptions import InvalidTransition, PaymentNotFound
from app.services.payments import apply_bank_status

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/bank", response_model=None)
def bank_webhook(payload: WebhookIn, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        apply_bank_status(db, payload.payment_id, payload.status)
    except PaymentNotFound:
        raise HTTPException(status_code=404, detail="Платёж не найден") from None
    except InvalidTransition:
        return JSONResponse(status_code=409, content={"error": "invalid_transition"})
    return JSONResponse(status_code=200, content={"result": "ok"})
