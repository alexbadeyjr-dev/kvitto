from typing import Any, ClassVar


class AppError(Exception):
    """Ошибка с готовым HTTP-ответом. Обработчик в main.py отдаёт as_dict() с кодом status_code."""

    status_code: ClassVar[int] = 400
    body: ClassVar[dict[str, Any]] = {}

    @classmethod
    def as_dict(cls) -> dict[str, Any]:
        return dict(cls.body)


class TariffNotFound(AppError):
    status_code = 404
    body = {"detail": "Тариф не найден"}


class PaymentNotFound(AppError):
    status_code = 404
    body = {"detail": "Платёж не найден"}


class InvalidTransition(AppError):
    status_code = 409
    body = {"error": "invalid_transition"}

    def __init__(self, current: str, requested: str) -> None:
        self.current = current
        self.requested = requested
        super().__init__(f"{current} -> {requested}")


class InvalidSignature(AppError):
    status_code = 401
    body = {"detail": "Неверная подпись"}
