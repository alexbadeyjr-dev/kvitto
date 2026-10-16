# Квитто — платёжный API

FastAPI-сервис тестового задания: тарифы, платежи с промокодом и рассрочкой, подписанный вебхук банка.

## Команды

```bash
pip install -r requirements.txt
ruff check .          # правила в ruff.toml, CI требует чистый результат
pytest                # SQLite в памяти, Docker не нужен
docker compose up --build   # Postgres + миграции + API на :8000
```

Локально без Docker: `DATABASE_URL=sqlite:///./kvitto.db WEBHOOK_SECRET=dev-webhook-secret uvicorn app.main:app --reload`.

## Структура

- `app/routers/` — только HTTP: параметры, коды ответов, перевод исключений сервиса в `HTTPException`.
- `app/services/` — бизнес-логика. `money.py` — промокод и график, `payments.py` — платежи и статусы, `signature.py` — HMAC.
- `app/schemas/` — Pydantic v2, `app/models/` — SQLAlchemy 2.0, `app/db/` — сессия, `Base`, сид тарифов.
- `alembic/versions/` — миграции. Изменил модель — добавь миграцию, старую не правь.

## Правила, которые нельзя нарушать

- Деньги — только целые копейки (`int`). Никаких `float`, `Decimal` и `round`, деление только `//` и `divmod`.
- Сумма графика рассрочки ровно равна `amount`, лишние копейки идут в первые платежи.
- Переходы статусов только из `ALLOWED_TRANSITIONS` в `services/payments.py`. Запрещённый переход — `409 {"error": "invalid_transition"}`, статус не меняется.
- `Idempotency-Key`: повтор возвращает первый платёж с `200`, даже если тело другое. Второй платёж не создаётся.
- Подпись вебхука проверяется до разбора тела, ответ на неё — `401`. `WEBHOOK_SECRET` обязателен, не добавляй ему значение по умолчанию и не отключай проверку.
- Ошибки валидации — стандартный `422` FastAPI, свой формат не вводить.

## Как писать код

- Ручки — обычные `def`: сессия SQLAlchemy синхронная. `async def` только там, где нужен `await` (как `verify_signature`).
- `engine` и `SessionLocal` читать через модуль (`from app.db import session as database`), а не импортировать по имени: они создаются в `init_engine` после импорта.
- Сервисы бросают исключения из `services/exceptions.py`, роутеры переводят их в коды ответа.
- Логи — через `logging.getLogger("kvitto.<модуль>")`, сообщения по-русски, без секретов и подписей.
- Тесты проверяют тело ответа и состояние базы, а не только код. Вебхуки в тестах отправлять через `post_webhook`, он подписывает тело.
- Перед коммитом: `ruff check .` и `pytest` должны проходить.
