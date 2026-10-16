from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.payment import PaymentStatus


class WebhookIn(BaseModel):
    payment_id: str = Field(min_length=1)
    status: PaymentStatus


class WebhookOut(BaseModel):
    result: Literal["ok"]
