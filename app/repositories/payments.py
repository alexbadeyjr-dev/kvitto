from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Payment


def get(session: Session, payment_id: str) -> Payment | None:
    return session.get(Payment, payment_id)


def get_by_idempotency_key(session: Session, idempotency_key: str) -> Payment | None:
    return session.scalar(select(Payment).where(Payment.idempotency_key == idempotency_key))


def find(
    session: Session,
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
    return list(session.scalars(query))


def add(session: Session, payment: Payment) -> None:
    session.add(payment)
