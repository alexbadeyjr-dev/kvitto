from fastapi import APIRouter
from sqlalchemy import select

from app.dependencies import SessionDep
from app.models import Tariff
from app.schemas import TariffOut

router = APIRouter(tags=["tariffs"])


@router.get("/tariffs", response_model=list[TariffOut])
def list_tariffs(db: SessionDep) -> list[Tariff]:
    return list(db.scalars(select(Tariff).order_by(Tariff.price)))
