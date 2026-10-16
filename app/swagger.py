"""Тексты и примеры для Swagger. Тела ошибок берутся из тех же исключений, что отдаёт API."""

import json
from typing import Any

from fastapi.openapi.models import Example

from app.schemas.payment import INSTALLMENT_MONTHS_FORBIDDEN, INSTALLMENT_MONTHS_REQUIRED
from app.services.exceptions import (
    AppError,
    InvalidSignature,
    InvalidTransition,
    PaymentNotFound,
    TariffNotFound,
)
from app.services.money import PROMO_CODE, PROMO_PERCENT, UNKNOWN_PROMO_MESSAGE


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _error_response(description: str, error: type[AppError]) -> dict[str, Any]:
    return {"description": description, "content": {"application/json": {"example": error.as_dict()}}}


_validation_schema = {"$ref": "#/components/schemas/HTTPValidationError"}


def _validation_error(
    loc: list[str],
    msg: str,
    input_: Any,
    error_type: str = "value_error",
    expected: str = "",
) -> dict[str, Any]:
    ctx: dict[str, Any] = {"error": {}} if error_type == "value_error" else {"expected": expected}
    return {"detail": [{"type": error_type, "loc": loc, "msg": msg, "input": input_, "ctx": ctx}]}


# Общее описание API

openapi_description = f"""
API, через которое онлайн-школа принимает оплату курса: тарифы, платежи с промокодом и рассрочкой,
уведомления банка о смене статуса.

### Деньги

Все суммы в запросах, ответах и в базе — **целые копейки**: 19 900 ₽ → `1990000`. Дробных сумм нет.

- `amount` — сумма к оплате после скидки, `discount` — размер скидки.
- Промокод `{PROMO_CODE}` даёт −{PROMO_PERCENT}% от цены тарифа, регистр не важен. Любой другой код — `422`.

### Способы оплаты и рассрочка

- `card` и `sbp` — разовая оплата, `installment_months` и `schedule` равны `null`.
- `installment` — рассрочка на 3, 6 или 12 месяцев, `installment_months` обязателен.
  `schedule` — платежи в копейках, их сумма ровно равна `amount`, лишние копейки идут в первые платежи.
  Например, `1990000` на 3 месяца — `[663334, 663333, 663333]`.

### Статусы платежа

Новый платёж создаётся в статусе `pending`. Статус меняет только банк через `POST /webhooks/bank`.

| Из | В | |
|---|---|---|
| `pending` | `succeeded` | оплата прошла |
| `pending` | `failed` | оплата не прошла |
| `succeeded` | `refunded` | возврат |

Любой другой переход, включая повтор текущего статуса, — `409`, статус не меняется.

### Идемпотентность

Заголовок `Idempotency-Key` в `POST /payments` защищает от двойной оплаты при повторе запроса.
Если платёж с таким ключом уже есть, вернётся он же с кодом `200`, даже если тело другое; второй платёж не создаётся.
Тело при этом всё равно проверяется: невалидный запрос получит `422`. Без заголовка каждый запрос создаёт новый платёж.

### Подпись вебхука

Банк подписывает каждый вебхук: заголовок `X-Signature` — HMAC-SHA256 от **сырого тела запроса** в hex,
секрет — переменная окружения `WEBHOOK_SECRET`. Подпись проверяется раньше тела.

```bash
BODY='{{"payment_id":"<id>","status":"succeeded"}}'
printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{{print $NF}}'
```

### Ошибки

| Код | Тело ответа | Когда |
|---|---|---|
| `401` | `{_json(InvalidSignature.as_dict())}` | Вебхук без `X-Signature` или с неверной подписью |
| `404` | `{_json(TariffNotFound.as_dict())}` | `POST /payments` с несуществующим `tariff_id` |
| `404` | `{_json(PaymentNotFound.as_dict())}` | `GET /payments/{{id}}` или вебхук для несуществующего платежа |
| `409` | `{_json(InvalidTransition.as_dict())}` | Вебхук с запрещённым переходом статуса |
| `422` | стандартный ответ FastAPI | Тело или параметры не прошли проверку |

Сообщения `422`, которые задаёт сервис (поле `msg`, с префиксом `Value error, `):

- `{UNKNOWN_PROMO_MESSAGE}` — промокод не `{PROMO_CODE}`.
- `{INSTALLMENT_MONTHS_REQUIRED}` — `method=installment` без срока.
- `{INSTALLMENT_MONTHS_FORBIDDEN}` — срок передан для `card` или `sbp`.

Остальные `422` — стандартные ошибки Pydantic: неверный email, неизвестный `method` или `status`,
срок не из 3/6/12, `limit` вне диапазона.
"""

openapi_tags = [
    {"name": "tariffs", "description": "Тарифы курса. Создаются при старте сервиса."},
    {"name": "payments", "description": "Создание платежей и просмотр их состояния."},
    {"name": "webhooks", "description": "Уведомления банка о смене статуса платежа. Требуют подписи `X-Signature`."},
]


# Примеры данных

_payment_id = "3f2b8c1e-5d4a-4e8b-9c7f-1a2b3c4d5e6f"

tariffs_example = [
    {"id": "basic", "title": "basic", "price": 990_000},
    {"id": "standard", "title": "standard", "price": 1_990_000},
    {"id": "premium", "title": "premium", "price": 2_990_000},
]

payment_card_example = {
    "id": _payment_id,
    "status": "pending",
    "tariff_id": "standard",
    "amount": 1_791_000,
    "discount": 199_000,
    "method": "card",
    "installment_months": None,
    "schedule": None,
    "email": "student@example.com",
    "created_at": "2026-10-16T12:00:00+00:00",
}

payment_installment_example = {
    **payment_card_example,
    "amount": 1_990_000,
    "discount": 0,
    "method": "installment",
    "installment_months": 3,
    "schedule": [663_334, 663_333, 663_333],
}

def _request_examples(examples: dict[str, Example]) -> dict[str, Any]:
    return {"requestBody": {"content": {"application/json": {"examples": examples}}}}


payment_create_examples = {
    "card_promo": Example(
        summary="Карта с промокодом",
        description="standard со скидкой 10%: amount 1791000, discount 199000.",
        value={"tariff_id": "standard", "email": "student@example.com", "method": "card", "promo_code": "kvitto10"},
    ),
    "sbp": Example(
        summary="СБП без промокода",
        value={"tariff_id": "basic", "email": "student@example.com", "method": "sbp"},
    ),
    "installment": Example(
        summary="Рассрочка на 3 месяца",
        description="standard без промокода: schedule [663334, 663333, 663333].",
        value={
            "tariff_id": "standard",
            "email": "student@example.com",
            "method": "installment",
            "installment_months": 3,
        },
    ),
    "installment_promo": Example(
        summary="Рассрочка на 12 месяцев с промокодом",
        value={
            "tariff_id": "premium",
            "email": "student@example.com",
            "method": "installment",
            "installment_months": 12,
            "promo_code": "KVITTO10",
        },
    ),
}

webhook_examples = {
    "succeeded": Example(summary="Оплата прошла", value={"payment_id": _payment_id, "status": "succeeded"}),
    "failed": Example(summary="Оплата не прошла", value={"payment_id": _payment_id, "status": "failed"}),
    "refunded": Example(summary="Возврат", value={"payment_id": _payment_id, "status": "refunded"}),
}

create_payment_openapi_extra = _request_examples(payment_create_examples)

bank_webhook_openapi_extra = _request_examples(webhook_examples)


# Тарифы

list_tariffs_description = """
Возвращает все тарифы по возрастанию цены. Цена — в копейках.
`id` тарифа передаётся в `tariff_id` при создании платежа.
"""

list_tariffs_responses: dict[int | str, dict[str, Any]] = {
    200: {"description": "Список тарифов", "content": {"application/json": {"example": tariffs_example}}},
}


# Платежи

create_payment_description = f"""
Создаёт платёж в статусе `pending` и считает сумму к оплате.

- Скидка по промокоду `{PROMO_CODE}` — {PROMO_PERCENT}% от цены тарифа, считается в целых копейках.
- Для `installment` возвращается график `schedule`, его сумма ровно равна `amount`.
- С заголовком `Idempotency-Key` повтор запроса вернёт уже созданный платёж с кодом `200`.

Готовые тела запроса — в списке **Examples** над редактором.
"""

create_payment_responses: dict[int | str, dict[str, Any]] = {
    201: {
        "description": "Платёж создан",
        "content": {
            "application/json": {
                "examples": {
                    "card": {"summary": "Карта с промокодом", "value": payment_card_example},
                    "installment": {"summary": "Рассрочка на 3 месяца", "value": payment_installment_example},
                },
            },
        },
    },
    200: {
        "description": "Платёж с таким `Idempotency-Key` уже был создан, возвращён он же",
        "content": {"application/json": {"example": payment_card_example}},
    },
    404: _error_response("Тариф не найден", TariffNotFound),
    422: {
        "description": "Тело запроса не прошло проверку",
        "content": {
            "application/json": {
                "schema": _validation_schema,
                "examples": {
                    "unknown_promo": {
                        "summary": "Неизвестный промокод",
                        "value": _validation_error(
                            ["body", "promo_code"], f"Value error, {UNKNOWN_PROMO_MESSAGE}", "SALE"
                        ),
                    },
                    "months_required": {
                        "summary": "Рассрочка без срока",
                        "value": _validation_error(
                            ["body"],
                            f"Value error, {INSTALLMENT_MONTHS_REQUIRED}",
                            {"tariff_id": "standard", "email": "student@example.com", "method": "installment"},
                        ),
                    },
                    "months_forbidden": {
                        "summary": "Срок для оплаты картой",
                        "value": _validation_error(
                            ["body"],
                            f"Value error, {INSTALLMENT_MONTHS_FORBIDDEN}",
                            {
                                "tariff_id": "standard",
                                "email": "student@example.com",
                                "method": "card",
                                "installment_months": 3,
                            },
                        ),
                    },
                    "wrong_months": {
                        "summary": "Срок не из 3, 6, 12",
                        "value": _validation_error(
                            ["body", "installment_months"],
                            "Input should be 3, 6 or 12",
                            5,
                            "literal_error",
                            "3, 6 or 12",
                        ),
                    },
                },
            },
        },
    },
}

list_payments_description = """
Список платежей, сначала новые. Фильтры необязательные и комбинируются:

- `email` — без учёта регистра;
- `status` — `pending`, `succeeded`, `failed` или `refunded`.

Пагинация через `limit` (до 100, по умолчанию 50) и `offset`.
"""

list_payments_responses: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Платежи, подходящие под фильтры. Пустой список, если таких нет",
        "content": {"application/json": {"example": [payment_installment_example]}},
    },
    422: {
        "description": "Неизвестный `status` или `limit`/`offset` вне диапазона",
        "content": {
            "application/json": {
                "schema": _validation_schema,
                "example": _validation_error(
                    ["query", "status"],
                    "Input should be 'pending', 'succeeded', 'failed' or 'refunded'",
                    "paid",
                    "literal_error",
                    "'pending', 'succeeded', 'failed' or 'refunded'",
                ),
            },
        },
    },
}

read_payment_description = """
Возвращает платёж по `id` с текущим статусом, суммой, скидкой и графиком рассрочки.
"""

read_payment_responses: dict[int | str, dict[str, Any]] = {
    200: {"description": "Платёж", "content": {"application/json": {"example": payment_installment_example}}},
    404: _error_response("Платёж не найден", PaymentNotFound),
}


# Вебхук банка

bank_webhook_description = """
Банк сообщает о смене статуса платежа. Допустимые переходы:
`pending → succeeded`, `pending → failed`, `succeeded → refunded`.

**Подпись обязательна.** `X-Signature` — HMAC-SHA256 от тела запроса в hex с секретом `WEBHOOK_SECRET`
(в `docker compose` по умолчанию `dev-webhook-secret`). Подпись проверяется раньше тела,
поэтому неподписанный запрос получает `401`, даже если тело невалидно.

Чтобы вызвать из Swagger, посчитайте подпись ровно от того текста, что стоит в редакторе тела, например:

```bash
BODY='{"payment_id": "<id>", "status": "succeeded"}'
printf '%s' "$BODY" | openssl dgst -sha256 -hmac dev-webhook-secret | awk '{print $NF}'
```

Лишний пробел или перенос строки в теле меняет подпись.
"""

bank_webhook_responses: dict[int | str, dict[str, Any]] = {
    200: {"description": "Статус изменён", "content": {"application/json": {"example": {"result": "ok"}}}},
    401: _error_response("Нет подписи или подпись неверна. Статус не меняется", InvalidSignature),
    404: _error_response("Платёж не найден", PaymentNotFound),
    409: _error_response("Запрещённый переход статуса. Статус не меняется", InvalidTransition),
}
