from fastapi import APIRouter

from app import swagger
from app.dependencies import SessionDep
from app.models import Tariff
from app.schemas import TariffOut
from app.services import tariffs as tariff_service

router = APIRouter(tags=["tariffs"])


@router.get(
    "/tariffs",
    response_model=list[TariffOut],
    summary="Список тарифов",
    description=swagger.list_tariffs_description,
    responses=swagger.list_tariffs_responses,
)
def list_tariffs(db: SessionDep) -> list[Tariff]:
    return tariff_service.list_tariffs(db)
