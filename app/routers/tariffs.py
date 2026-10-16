from fastapi import APIRouter

from app import swagger
from app.dependencies import TariffServiceDep
from app.models import Tariff
from app.schemas import TariffOut

router = APIRouter(tags=["tariffs"])


@router.get(
    "/tariffs",
    response_model=list[TariffOut],
    summary="Список тарифов",
    description=swagger.list_tariffs_description,
    responses=swagger.list_tariffs_responses,
)
def list_tariffs(service: TariffServiceDep) -> list[Tariff]:
    return service.list_tariffs()
