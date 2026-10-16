import json
from collections.abc import Mapping

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import func, select

from app.configs.settings import get_settings
from app.db import session as database
from app.models import Payment
from app.services.signature import sign


def payment_count() -> int:
    with database.SessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(Payment))
    return int(count or 0)


async def post_payment(
    client: AsyncClient,
    headers: Mapping[str, str] | None = None,
    **overrides: object,
) -> Response:
    payload: dict[str, object] = {
        "tariff_id": "standard",
        "email": "student@example.com",
        "method": "card",
    }
    payload.update(overrides)
    return await client.post("/payments", json=payload, headers=headers)


async def post_webhook(
    client: AsyncClient,
    payload: Mapping[str, object],
    signature: str | None = None,
) -> Response:
    """Отправляет вебхук. Без явной подписи подписывает тело секретом из настроек."""
    body = json.dumps(payload).encode()
    if signature is None:
        signature = sign(body, get_settings().webhook_secret.get_secret_value())
    headers = {"Content-Type": "application/json", "X-Signature": signature}
    return await client.post("/webhooks/bank", content=body, headers=headers)


async def test_amount_with_and_without_promo(client: AsyncClient) -> None:
    tariffs = await client.get("/tariffs")
    assert tariffs.status_code == 200
    prices = {item["id"]: item["price"] for item in tariffs.json()}
    assert prices == {
        "basic": 990_000,
        "standard": 1_990_000,
        "premium": 2_990_000,
    }
    assert [item["title"] for item in tariffs.json()] == ["basic", "standard", "premium"]

    plain = await post_payment(client)
    assert plain.status_code == 201
    plain_body = plain.json()
    assert plain_body["amount"] == 1_990_000
    assert plain_body["discount"] == 0
    assert plain_body["status"] == "pending"
    assert plain_body["schedule"] is None
    assert plain_body["installment_months"] is None
    assert "idempotency_key" not in plain_body

    discounted = await post_payment(client, promo_code="kvitto10")
    assert discounted.status_code == 201
    assert discounted.json()["amount"] == 1_791_000
    assert discounted.json()["discount"] == 199_000

    upper = await post_payment(client, promo_code="KVITTO10")
    assert upper.status_code == 201
    assert upper.json()["amount"] == 1_791_000
    assert upper.json()["discount"] == 199_000

    installment = await post_payment(
        client,
        method="installment",
        installment_months=3,
        promo_code="kvitto10",
    )
    assert installment.status_code == 201
    assert installment.json()["amount"] == 1_791_000
    assert installment.json()["discount"] == 199_000
    assert installment.json()["schedule"] == [597_000, 597_000, 597_000]

    unknown = await post_payment(client, promo_code="sale")
    assert unknown.status_code == 422
    assert any("promo_code" in error["loc"] for error in unknown.json()["detail"])


@pytest.mark.parametrize("months", [3, 6, 12])
async def test_installment_schedule_sums_to_amount(client: AsyncClient, months: int) -> None:
    response = await post_payment(client, method="installment", installment_months=months)

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == 1_990_000
    assert body["installment_months"] == months
    assert sum(body["schedule"]) == body["amount"]
    assert len(body["schedule"]) == months
    assert max(body["schedule"]) - min(body["schedule"]) <= 1
    assert all(isinstance(part, int) for part in body["schedule"])
    if months == 3:
        assert body["schedule"] == [663_334, 663_333, 663_333]


async def test_same_idempotency_key_returns_existing_payment(client: AsyncClient) -> None:
    headers = {"Idempotency-Key": "order-42"}
    first = await post_payment(client, headers=headers)
    assert first.status_code == 201

    second = await post_payment(
        client,
        headers=headers,
        tariff_id="premium",
        email="other@example.com",
        promo_code="kvitto10",
    )
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["tariff_id"] == "standard"
    assert second.json()["email"] == "student@example.com"
    assert second.json()["amount"] == 1_990_000
    assert payment_count() == 1

    third = await post_payment(client)
    fourth = await post_payment(client)
    assert third.status_code == 201
    assert fourth.status_code == 201
    assert third.json()["id"] != fourth.json()["id"]
    assert payment_count() == 3


async def test_forbidden_transition_returns_409_and_keeps_status(client: AsyncClient) -> None:
    created = await post_payment(client)
    payment_id = created.json()["id"]

    async def send(status: str) -> Response:
        return await post_webhook(client, {"payment_id": payment_id, "status": status})

    async def current_status() -> str:
        response = await client.get(f"/payments/{payment_id}")
        assert response.status_code == 200
        return response.json()["status"]

    same = await send("pending")
    assert same.status_code == 409
    assert same.json() == {"error": "invalid_transition"}
    assert await current_status() == "pending"

    denied = await send("refunded")
    assert denied.status_code == 409
    assert denied.json() == {"error": "invalid_transition"}
    assert await current_status() == "pending"

    succeeded = await send("succeeded")
    assert succeeded.status_code == 200
    assert succeeded.json() == {"result": "ok"}
    assert await current_status() == "succeeded"

    failed = await send("failed")
    assert failed.status_code == 409
    assert await current_status() == "succeeded"

    refunded = await send("refunded")
    assert refunded.status_code == 200
    assert await current_status() == "refunded"

    failed_payment = await post_payment(client)
    failed_id = failed_payment.json()["id"]
    failed_hook = await post_webhook(client, {"payment_id": failed_id, "status": "failed"})
    assert failed_hook.status_code == 200
    blocked = await post_webhook(client, {"payment_id": failed_id, "status": "succeeded"})
    assert blocked.status_code == 409
    assert blocked.json() == {"error": "invalid_transition"}
    stayed = await client.get(f"/payments/{failed_id}")
    assert stayed.json()["status"] == "failed"


async def test_missing_payment_returns_404(client: AsyncClient) -> None:
    missing = await client.get("/payments/missing-id")
    assert missing.status_code == 404

    webhook = await post_webhook(client, {"payment_id": "missing-id", "status": "succeeded"})
    assert webhook.status_code == 404

    unknown_tariff = await post_payment(client, tariff_id="vip")
    assert unknown_tariff.status_code == 404


async def test_installment_months_match_method(client: AsyncClient) -> None:
    missing_months = await post_payment(client, method="installment")
    assert missing_months.status_code == 422

    months_for_card = await post_payment(client, method="card", installment_months=3)
    assert months_for_card.status_code == 422

    months_for_sbp = await post_payment(client, method="sbp", installment_months=6)
    assert months_for_sbp.status_code == 422


async def test_webhook_requires_valid_signature(client: AsyncClient) -> None:
    created = await post_payment(client)
    payment_id = created.json()["id"]
    payload = {"payment_id": payment_id, "status": "succeeded"}
    body = json.dumps(payload).encode()

    async def current_status() -> str:
        return (await client.get(f"/payments/{payment_id}")).json()["status"]

    unsigned = await client.post("/webhooks/bank", content=body, headers={"Content-Type": "application/json"})
    assert unsigned.status_code == 401
    assert await current_status() == "pending"

    wrong_secret = await post_webhook(client, payload, signature=sign(body, "other-secret"))
    assert wrong_secret.status_code == 401
    assert await current_status() == "pending"

    other_body = json.dumps({"payment_id": payment_id, "status": "failed"}).encode()
    tampered = await post_webhook(client, payload, signature=sign(other_body, "test-webhook-secret"))
    assert tampered.status_code == 401
    assert await current_status() == "pending"

    not_ascii = await client.post(
        "/webhooks/bank",
        content=body,
        headers={"Content-Type": "application/json", "X-Signature": "подпись".encode()},
    )
    assert not_ascii.status_code == 401

    invalid_body = await post_webhook(client, {"payment_id": payment_id, "status": "unknown"}, signature="bad")
    assert invalid_body.status_code == 401

    signed = await post_webhook(client, payload)
    assert signed.status_code == 200
    assert signed.json() == {"result": "ok"}
    assert await current_status() == "succeeded"
