from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Tariff


def get(session: Session, tariff_id: str) -> Tariff | None:
    return session.get(Tariff, tariff_id)


def list_by_price(session: Session) -> list[Tariff]:
    return list(session.scalars(select(Tariff).order_by(Tariff.price)))


def add(session: Session, tariff: Tariff) -> None:
    session.add(tariff)
