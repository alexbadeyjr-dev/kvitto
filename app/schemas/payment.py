from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator, model_validator

from app.services.money import normalize_promo

PaymentStatus = Literal["pending", "succeeded", "failed", "refunded"]

INSTALLMENT_MONTHS_REQUIRED = "Для рассрочки нужно указать installment_months: 3, 6 или 12"
INSTALLMENT_MONTHS_FORBIDDEN = "installment_months передаётся только вместе с method=installment"


class PaymentCreate(BaseModel):
    tariff_id: str = Field(min_length=1)
    email: EmailStr
    method: Literal["card", "sbp", "installment"]
    installment_months: Literal[3, 6, 12] | None = None
    promo_code: str | None = None

    @field_validator("promo_code")
    @classmethod
    def validate_promo(cls, value: str | None) -> str | None:
        return normalize_promo(value)

    @model_validator(mode="after")
    def check_installment(self) -> "PaymentCreate":
        if self.method == "installment" and self.installment_months is None:
            raise ValueError(INSTALLMENT_MONTHS_REQUIRED)
        if self.method != "installment" and self.installment_months is not None:
            raise ValueError(INSTALLMENT_MONTHS_FORBIDDEN)
        return self


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: PaymentStatus
    tariff_id: str
    amount: int
    discount: int
    method: str
    installment_months: int | None
    schedule: list[int] | None
    email: EmailStr
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat()
