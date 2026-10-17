import logging

from sqlalchemy.orm import Session

from app.models import Tariff
from app.repositories import tariffs as tariff_repository

logger = logging.getLogger("kvitto.tariffs")

DEFAULT_TARIFFS: tuple[tuple[str, str, int], ...] = (
    ("basic", "basic", 990_000),
    ("standard", "standard", 1_990_000),
    ("premium", "premium", 2_990_000),
)


def list_tariffs(session: Session) -> list[Tariff]:
    return tariff_repository.list_by_price(session)


def seed_default_tariffs(session: Session) -> None:
    """Создаёт тарифы из DEFAULT_TARIFFS, которых ещё нет в базе."""
    created: list[str] = []
    for tariff_id, title, price in DEFAULT_TARIFFS:
        if tariff_repository.get(session, tariff_id) is None:
            tariff_repository.add(session, Tariff(id=tariff_id, title=title, price=price))
            created.append(tariff_id)
    session.commit()
    if created:
        logger.info("Созданы тарифы: %s", ", ".join(created))
