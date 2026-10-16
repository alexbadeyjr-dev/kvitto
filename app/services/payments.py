import logging
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Payment
from app.repositories import PaymentRepository, TariffRepository
from app.schemas import PaymentCreate
from app.services.exceptions import InvalidTransition, PaymentNotFound, TariffNotFound
from app.services.money import apply_promo, build_schedule

logger = logging.getLogger("kvitto.payments")

ALLOWED_TRANSITIONS = {
    ("pending", "succeeded"),
    ("pending", "failed"),
    ("succeeded", "refunded"),
}


class PaymentService:
    """Бизнес-логика платежей. Запросы к БД — через репозитории, транзакция — здесь."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.payments = PaymentRepository(session)
        self.tariffs = TariffRepository(session)

    def create_payment(self, data: PaymentCreate, idempotency_key: str | None) -> tuple[Payment, bool]:
        """Возвращает платёж и признак, что он создан сейчас, а не найден по ключу идемпотентности."""
        if idempotency_key:
            existing = self.payments.get_by_idempotency_key(idempotency_key)
            if existing is not None:
                logger.info(
                    "Повтор с ключом идемпотентности %s: возвращён платёж %s",
                    idempotency_key,
                    existing.id,
                )
                return existing, False

        tariff = self.tariffs.get(data.tariff_id)
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
            created_at=datetime.now(UTC),
        )
        self.payments.add(payment)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            if idempotency_key is None:
                raise
            existing = self.payments.get_by_idempotency_key(idempotency_key)
            if existing is None:
                raise
            logger.info(
                "Одновременный повтор ключа %s: возвращён платёж %s",
                idempotency_key,
                existing.id,
            )
            return existing, False

        self.session.refresh(payment)
        logger.info(
            "Создан платёж %s: сумма %s коп., скидка %s коп., способ %s",
            payment.id,
            payment.amount,
            payment.discount,
            payment.method,
        )
        return payment, True

    def apply_bank_status(self, payment_id: str, status: str) -> Payment:
        payment = self.payments.get(payment_id)
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
        self.session.commit()
        self.session.refresh(payment)
        logger.info("Платёж %s: статус %s → %s", payment.id, previous, payment.status)
        return payment

    def get_payment(self, payment_id: str) -> Payment:
        payment = self.payments.get(payment_id)
        if payment is None:
            raise PaymentNotFound
        return payment

    def list_payments(
        self,
        email: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[Payment]:
        return self.payments.find(email, status, limit, offset)
