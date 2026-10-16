import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Payment, Tariff
from app.schemas import PaymentCreate
from app.services.exceptions import InvalidTransition, PaymentNotFound, TariffNotFound
from app.services.money import apply_promo, build_schedule

logger = logging.getLogger("kvitto.payments")

ALLOWED_TRANSITIONS = {
    ("pending", "succeeded"),
    ("pending", "failed"),
    ("succeeded", "refunded"),
}


def create_payment(
    session: Session,
    data: PaymentCreate,
    idempotency_key: str | None,
) -> tuple[Payment, bool]:
    if idempotency_key:
        existing = _find_by_key(session, idempotency_key)
        if existing is not None:
            logger.info(
                "Повтор с ключом идемпотентности %s: возвращён платёж %s",
                idempotency_key,
                existing.id,
            )
            return existing, False

    tariff = session.get(Tariff, data.tariff_id)
    if tariff is None:
        logger.info("Тариф %s не найден", data.tariff_id)
        raise TariffNotFound

    amount, discount = apply_promo(tariff.price, data.promo_code)
    months = data.installment_months if data.method == "installment" else None
    schedule = build_schedule(amount, months) if months is not None else None
    payment = Payment(
        id=str(uuid4()),
        status="pending",
        tariff_id=tariff.id,
        amount=amount,
        discount=discount,
        method=data.method,
        installment_months=months,
        schedule=schedule,
        email=str(data.email),
        idempotency_key=idempotency_key,
        created_at=datetime.now(timezone.utc),
    )
    session.add(payment)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        if idempotency_key is None:
            raise
        existing = _find_by_key(session, idempotency_key)
        if existing is None:
            raise
        logger.info(
            "Одновременный повтор ключа %s: возвращён платёж %s",
            idempotency_key,
            existing.id,
        )
        return existing, False

    session.refresh(payment)
    logger.info(
        "Создан платёж %s: сумма %s коп., скидка %s коп., способ %s",
        payment.id,
        payment.amount,
        payment.discount,
        payment.method,
    )
    return payment, True


def apply_bank_status(session: Session, payment_id: str, status: str) -> Payment:
    payment = session.get(Payment, payment_id)
    if payment is None:
        logger.info("Вебхук для неизвестного платежа %s", payment_id)
        raise PaymentNotFound

    transition = (payment.status, status)
    if transition not in ALLOWED_TRANSITIONS:
        logger.warning(
            "Запрещённый переход платежа %s: %s → %s",
            payment.id,
            payment.status,
            status,
        )
        raise InvalidTransition(payment.status, status)

    previous = payment.status
    payment.status = status
    session.commit()
    session.refresh(payment)
    logger.info("Платёж %s: статус %s → %s", payment.id, previous, payment.status)
    return payment


def get_payment(session: Session, payment_id: str) -> Payment:
    payment = session.get(Payment, payment_id)
    if payment is None:
        raise PaymentNotFound
    return payment


def _find_by_key(session: Session, idempotency_key: str) -> Payment | None:
    return session.scalar(select(Payment).where(Payment.idempotency_key == idempotency_key))
