import logging

from sqlalchemy.orm import Session

from app.models import Tariff
from app.repositories import TariffRepository

logger = logging.getLogger("kvitto.tariffs")

DEFAULT_TARIFFS: tuple[tuple[str, str, int], ...] = (
    ("basic", "basic", 990_000),
    ("standard", "standard", 1_990_000),
    ("premium", "premium", 2_990_000),
)


class TariffService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.tariffs = TariffRepository(session)

    def list_tariffs(self) -> list[Tariff]:
        return self.tariffs.list_by_price()

    def seed_defaults(self) -> None:
        """Создаёт тарифы из DEFAULT_TARIFFS, которых ещё нет в базе."""
        created: list[str] = []
        for tariff_id, title, price in DEFAULT_TARIFFS:
            if self.tariffs.get(tariff_id) is None:
                self.tariffs.add(Tariff(id=tariff_id, title=title, price=price))
                created.append(tariff_id)
        self.session.commit()
        if created:
            logger.info("Созданы тарифы: %s", ", ".join(created))
