import logging

from sqlalchemy.orm import Session

from app.models import Tariff

logger = logging.getLogger("kvitto.seed")

TARIFFS: tuple[tuple[str, str, int], ...] = (
    ("basic", "basic", 990_000),
    ("standard", "standard", 1_990_000),
    ("premium", "premium", 2_990_000),
)


def seed_tariffs(session: Session) -> None:
    created: list[str] = []
    for tariff_id, title, price in TARIFFS:
        if session.get(Tariff, tariff_id) is None:
            session.add(Tariff(id=tariff_id, title=title, price=price))
            created.append(tariff_id)
    session.commit()
    if created:
        logger.info("Созданы тарифы: %s", ", ".join(created))
