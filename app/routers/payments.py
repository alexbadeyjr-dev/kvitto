from fastapi import APIRouter, HTTPException, Response

from app.dependencies import (
    EmailQuery,
    IdempotencyKeyDep,
    LimitQuery,
    OffsetQuery,
    PaymentIdPath,
    PaymentStatusQuery,
    SessionDep,
)
from app.models import Payment
from app.schemas import PaymentCreate, PaymentOut
from app.services.exceptions import PaymentNotFound, TariffNotFound
from app.services.payments import create_payment, get_payment, list_payments

router = APIRouter(tags=["payments"])


@router.post("/payments", response_model=PaymentOut, status_code=201)
def create(
    payload: PaymentCreate,
    response: Response,
    db: SessionDep,
    idempotency_key: IdempotencyKeyDep,
) -> Payment:
    try:
        payment, created = create_payment(db, payload, idempotency_key)
    except TariffNotFound:
        raise HTTPException(status_code=404, detail="Тариф не найден") from None
    if not created:
        response.status_code = 200
    return payment


@router.get("/payments", response_model=list[PaymentOut])
def read_payments(
    db: SessionDep,
    email: EmailQuery = None,
    status: PaymentStatusQuery = None,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[Payment]:
    return list_payments(db, email, status, limit, offset)


@router.get("/payments/{payment_id}", response_model=PaymentOut)
def read_payment(payment_id: PaymentIdPath, db: SessionDep) -> Payment:
    try:
        return get_payment(db, payment_id)
    except PaymentNotFound:
        raise HTTPException(status_code=404, detail="Платёж не найден") from None
