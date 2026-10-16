from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Tariff


class TariffRepository:
    """Запросы к таблице tariffs. Транзакцией не управляет: commit делает сервис."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, tariff_id: str) -> Tariff | None:
        return self.session.get(Tariff, tariff_id)

    def list_by_price(self) -> list[Tariff]:
        return list(self.session.scalars(select(Tariff).order_by(Tariff.price)))

    def add(self, tariff: Tariff) -> None:
        self.session.add(tariff)
