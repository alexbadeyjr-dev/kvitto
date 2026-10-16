from pydantic import BaseModel, Field

from app.schemas.payment import PaymentStatus


class WebhookIn(BaseModel):
    payment_id: str = Field(min_length=1)
    status: PaymentStatus
