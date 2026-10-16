from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Payment


class PaymentRepository:
    """Запросы к таблице payments. Транзакцией не управляет: commit делает сервис."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, payment_id: str) -> Payment | None:
        return self.session.get(Payment, payment_id)

    def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        return self.session.scalar(select(Payment).where(Payment.idempotency_key == idempotency_key))

    def find(
        self,
        email: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[Payment]:
        query = select(Payment)
        if email:
            query = query.where(func.lower(Payment.email) == email.strip().lower())
        if status:
            query = query.where(Payment.status == status)
        query = query.order_by(Payment.created_at.desc(), Payment.id).limit(limit).offset(offset)
        return list(self.session.scalars(query))

    def add(self, payment: Payment) -> None:
        self.session.add(payment)
