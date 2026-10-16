from typing import Literal

from pydantic import BaseModel, Field


class WebhookIn(BaseModel):
    payment_id: str = Field(min_length=1)
    status: Literal["pending", "succeeded", "failed", "refunded"]
