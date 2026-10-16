# Платежи Квитто

Небольшой API, через который онлайн-школа принимает оплату курса: тарифы, платёж, вебхук банка.

Суммы везде в копейках, целым числом. `amount` — сумма к оплате после скидки, `discount` — размер скидки. Промокод `KVITTO10` даёт 10%, регистр не важен. Для `card` и `sbp` поля `installment_months` и `schedule` пустые. У рассрочки график в копейках, лишние копейки попадают в первые платежи, сумма графика равна `amount`.

Новый платёж в статусе `pending`. Допустимы переходы `pending → succeeded`, `pending → failed`, `succeeded → refunded`. Остальные, включая повтор того же статуса, отвечают `409` и статус не меняют.

Заголовок `Idempotency-Key` после успешной валидации тела возвращает уже созданный платёж с кодом `200`, даже если второе тело другое. Без заголовка каждый запрос создаёт новый платёж. Неизвестный тариф и неизвестный платёж — `404`. Неизвестный промокод и неверные поля — стандартный `422` FastAPI.

Вебхук банка подписывается: заголовок `X-Signature` — HMAC-SHA256 от сырого тела запроса в hex, секрет берётся из переменной `WEBHOOK_SECRET`. Без заголовка или с неверной подписью ответ `401`, статус не меняется. Подпись проверяется раньше тела, поэтому неподписанный запрос с кривым JSON тоже получает `401`. Без `WEBHOOK_SECRET` сервис не стартует: молча принимать неподписанные вебхуки опаснее, чем упасть при запуске.

## Тесты

Тесты поднимают SQLite в памяти, Docker для них не нужен.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
ruff check .
pytest
```

На macOS и Linux активация другая: `source .venv/bin/activate`.

Те же `ruff check .` и `pytest` запускает GitHub Actions на каждый push и pull request, на Python 3.11 и 3.12: `.github/workflows/ci.yml`.

## Запуск

Нужны Docker и свободный порт 5432.

```bash
docker compose up --build
```

Сервис поднимется на http://localhost:8000. Документация: http://localhost:8000/docs.

Остановка: `docker compose down`.

## Примеры

Список тарифов:

```bash
curl http://localhost:8000/tariffs
```

Оплата standard картой:

```bash
curl -X POST http://localhost:8000/payments -H "Content-Type: application/json" -H "Idempotency-Key: order-1" -d "{\"tariff_id\":\"standard\",\"email\":\"student@example.com\",\"method\":\"card\"}"
```

Рассрочка standard на 3 месяца. В ответе `schedule` будет `[663334, 663333, 663333]`.

```bash
curl -X POST http://localhost:8000/payments -H "Content-Type: application/json" -d "{\"tariff_id\":\"standard\",\"email\":\"student@example.com\",\"method\":\"installment\",\"installment_months\":3}"
```

Платёж и вебхук банка. Подставьте `id` из ответа создания. В `docker compose` секрет по умолчанию — `dev-webhook-secret`.

```bash
curl http://localhost:8000/payments/{id}

BODY='{"payment_id":"{id}","status":"succeeded"}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "dev-webhook-secret" | awk '{print $NF}')
curl -X POST http://localhost:8000/webhooks/bank -H "Content-Type: application/json" -H "X-Signature: $SIG" -d "$BODY"
```

Подпись считается от тела байт в байт: если после подписи поменять в `BODY` хоть пробел, ответ будет `401`.

Список платежей с фильтрами. Оба фильтра необязательные, `email` сравнивается без учёта регистра, неизвестный `status` — `422`. Сначала новые, по умолчанию 50 записей, `limit` до 100, есть `offset`.

```bash
curl "http://localhost:8000/payments?email=student@example.com&status=pending"
curl "http://localhost:8000/payments?limit=10&offset=10"
```

В PowerShell для этих команд нужна программа `curl.exe`: встроенный `curl` там вызывает другой командлет.

Повтор того же `Idempotency-Key` вернёт первый платёж и код `200`. Повторный `curl` без ключа создаст второй платёж.
