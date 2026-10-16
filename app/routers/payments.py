from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Payment
from app.schemas import PaymentCreate, PaymentOut, PaymentStatus
from app.services.exceptions import PaymentNotFound, TariffNotFound
from app.services.payments import create_payment, get_payment, list_payments

router = APIRouter(tags=["payments"])


@router.post("/payments", response_model=PaymentOut, status_code=201)
def create(
    payload: PaymentCreate,
    response: Response,
    db: Session = Depends(get_db),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> Payment:
    key = idempotency_key.strip() if idempotency_key else None
    if key == "":
        key = None
    try:
        payment, created = create_payment(db, payload, key)
    except TariffNotFound:
        raise HTTPException(status_code=404, detail="Тариф не найден") from None
    if not created:
        response.status_code = 200
    return payment


@router.get("/payments", response_model=list[PaymentOut])
def read_payments(
    db: Session = Depends(get_db),
    email: Annotated[str | None, Query(description="Email без учёта регистра")] = None,
    status: PaymentStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Payment]:
    return list_payments(db, email, status, limit, offset)


@router.get("/payments/{payment_id}", response_model=PaymentOut)
def read_payment(payment_id: str, db: Session = Depends(get_db)) -> Payment:
    try:
        return get_payment(db, payment_id)
    except PaymentNotFound:
        raise HTTPException(status_code=404, detail="Платёж не найден") from None
