from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator, model_validator

from app.services.money import normalize_promo

PaymentStatus = Literal["pending", "succeeded", "failed", "refunded"]

INSTALLMENT_MONTHS_REQUIRED = "Для рассрочки нужно указать installment_months: 3, 6 или 12"
INSTALLMENT_MONTHS_FORBIDDEN = "installment_months передаётся только вместе с method=installment"


class PaymentCreate(BaseModel):
    tariff_id: str = Field(min_length=1, description="Идентификатор тарифа из `GET /tariffs`")
    email: EmailStr = Field(description="Email ученика")
    method: Literal["card", "sbp", "installment"] = Field(description="Способ оплаты")
    installment_months: Literal[3, 6, 12] | None = Field(
        default=None,
        description="Срок рассрочки в месяцах. Обязателен для `installment`, запрещён для `card` и `sbp`",
    )
    promo_code: str | None = Field(
        default=None,
        description="Промокод, регистр не важен. Сейчас действует только `KVITTO10`",
    )

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

    id: str = Field(description="Идентификатор платежа, UUID")
    status: PaymentStatus = Field(description="Текущий статус платежа")
    tariff_id: str = Field(description="Идентификатор тарифа")
    amount: int = Field(description="Сумма к оплате после скидки, в копейках")
    discount: int = Field(description="Размер скидки в копейках, `0` без промокода")
    method: str = Field(description="Способ оплаты: `card`, `sbp` или `installment`")
    installment_months: int | None = Field(description="Срок рассрочки, `null` для `card` и `sbp`")
    schedule: list[int] | None = Field(
        description="График рассрочки в копейках, сумма равна `amount`. `null` для `card` и `sbp`",
    )
    email: EmailStr = Field(description="Email ученика")
    created_at: datetime = Field(description="Время создания, ISO 8601 в UTC")

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat()
