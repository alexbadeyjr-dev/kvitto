from pydantic import BaseModel, ConfigDict, Field


class TariffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Идентификатор тарифа, передаётся в `tariff_id` при оплате")
    title: str = Field(description="Название тарифа")
    price: int = Field(description="Цена в копейках")
