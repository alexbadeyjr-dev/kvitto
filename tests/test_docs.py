from typing import Any

from httpx import AsyncClient

from app import swagger


def json_example(responses: dict[int | str, dict[str, Any]], code: int, name: str | None = None) -> Any:
    content = responses[code]["content"]["application/json"]
    return content["examples"][name]["value"] if name else content["example"]


async def test_every_endpoint_is_documented(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()

    assert "### Ошибки" in schema["info"]["description"]
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            assert operation.get("summary"), f"{method} {path} без summary"
            assert operation.get("description"), f"{method} {path} без description"


async def test_request_examples_are_valid(client: AsyncClient) -> None:
    for name, example in swagger.payment_create_examples.items():
        response = await client.post("/payments", json=example["value"])
        assert response.status_code == 201, name

    expected = {"card_promo": 1_791_000, "installment": 1_990_000}
    for name, amount in expected.items():
        response = await client.post("/payments", json=swagger.payment_create_examples[name]["value"])
        assert response.json()["amount"] == amount


async def test_documented_validation_errors_match_api(client: AsyncClient) -> None:
    base = {"tariff_id": "standard", "email": "student@example.com"}
    requests = {
        "unknown_promo": {**base, "method": "card", "promo_code": "SALE"},
        "months_required": {**base, "method": "installment"},
        "months_forbidden": {**base, "method": "card", "installment_months": 3},
        "wrong_months": {**base, "method": "installment", "installment_months": 5},
    }
    for name, body in requests.items():
        response = await client.post("/payments", json=body)
        assert response.status_code == 422, name
        assert response.json() == json_example(swagger.create_payment_responses, 422, name), name

    unknown_status = await client.get("/payments", params={"status": "paid"})
    assert unknown_status.json() == json_example(swagger.list_payments_responses, 422)


async def test_documented_errors_match_api(client: AsyncClient) -> None:
    unknown_tariff = await client.post(
        "/payments",
        json={"tariff_id": "vip", "email": "student@example.com", "method": "card"},
    )
    assert unknown_tariff.json() == json_example(swagger.create_payment_responses, 404)

    missing = await client.get("/payments/missing-id")
    assert missing.json() == json_example(swagger.read_payment_responses, 404)

    unsigned = await client.post("/webhooks/bank", json={"payment_id": "missing-id", "status": "failed"})
    assert unsigned.status_code == 401
    assert unsigned.json() == json_example(swagger.bank_webhook_responses, 401)
