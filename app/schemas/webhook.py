from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.payment import PaymentStatus


class WebhookIn(BaseModel):
    payment_id: str = Field(min_length=1, description="Идентификатор платежа")
    status: PaymentStatus = Field(description="Новый статус платежа")


class WebhookOut(BaseModel):
    result: Literal["ok"] = Field(description="Статус платежа изменён")
