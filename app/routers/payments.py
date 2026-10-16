from fastapi import APIRouter, Response

from app import swagger
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
    service: PaymentServiceDep,
    idempotency_key: IdempotencyKeyDep,
) -> Payment:
    payment, created = service.create_payment(payload, idempotency_key)
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
    service: PaymentServiceDep,
    email: EmailQuery = None,
    status: PaymentStatusQuery = None,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[Payment]:
    return service.list_payments(email, status, limit, offset)


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentOut,
    summary="Получить платёж",
    description=swagger.read_payment_description,
    responses=swagger.read_payment_responses,
)
def read_payment(payment_id: PaymentIdPath, service: PaymentServiceDep) -> Payment:
    return service.get_payment(payment_id)
