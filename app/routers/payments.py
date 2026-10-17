from fastapi import APIRouter, Response

from app import swagger
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
from app.services import payments as payment_service

router = APIRouter(tags=["payments"])


@router.post(
    "/payments",
    response_model=PaymentOut,
    status_code=201,
    summary="Создать платёж",
    description=swagger.create_payment_description,
    responses=swagger.create_payment_responses,
    openapi_extra=swagger.create_payment_openapi_extra,
)
def create(
    payload: PaymentCreate,
    response: Response,
    db: SessionDep,
    idempotency_key: IdempotencyKeyDep,
) -> Payment:
    payment, created = payment_service.create_payment(db, payload, idempotency_key)
    if not created:
        response.status_code = 200
    return payment


@router.get(
    "/payments",
    response_model=list[PaymentOut],
    summary="Список платежей с фильтрами",
    description=swagger.list_payments_description,
    responses=swagger.list_payments_responses,
)
def read_payments(
    db: SessionDep,
    email: EmailQuery = None,
    status: PaymentStatusQuery = None,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[Payment]:
    return payment_service.list_payments(db, email, status, limit, offset)


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentOut,
    summary="Получить платёж",
    description=swagger.read_payment_description,
    responses=swagger.read_payment_responses,
)
def read_payment(payment_id: PaymentIdPath, db: SessionDep) -> Payment:
    return payment_service.get_payment(db, payment_id)
