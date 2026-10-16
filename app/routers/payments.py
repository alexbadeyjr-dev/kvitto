from fastapi import APIRouter, HTTPException, Response

from app.dependencies import (
    EmailQuery,
    IdempotencyKeyDep,
    LimitQuery,
    OffsetQuery,
    PaymentIdPath,
    PaymentServiceDep,
    PaymentStatusQuery,
)
from app.models import Payment
from app.schemas import PaymentCreate, PaymentOut
from app.services.exceptions import PaymentNotFound, TariffNotFound

router = APIRouter(tags=["payments"])


@router.post("/payments", response_model=PaymentOut, status_code=201)
def create(
    payload: PaymentCreate,
    response: Response,
    service: PaymentServiceDep,
    idempotency_key: IdempotencyKeyDep,
) -> Payment:
    try:
        payment, created = service.create_payment(payload, idempotency_key)
    except TariffNotFound:
        raise HTTPException(status_code=404, detail="Тариф не найден") from None
    if not created:
        response.status_code = 200
    return payment


@router.get("/payments", response_model=list[PaymentOut])
def read_payments(
    service: PaymentServiceDep,
    email: EmailQuery = None,
    status: PaymentStatusQuery = None,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[Payment]:
    return service.list_payments(email, status, limit, offset)


@router.get("/payments/{payment_id}", response_model=PaymentOut)
def read_payment(payment_id: PaymentIdPath, service: PaymentServiceDep) -> Payment:
    try:
        return service.get_payment(payment_id)
    except PaymentNotFound:
        raise HTTPException(status_code=404, detail="Платёж не найден") from None
