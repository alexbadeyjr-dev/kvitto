PROMO_CODE = "KVITTO10"
PROMO_PERCENT = 10
UNKNOWN_PROMO_MESSAGE = "Неизвестный промокод"


def normalize_promo(promo_code: str | None) -> str | None:
    if promo_code is None or not promo_code.strip():
        return None
    normalized = promo_code.strip()
    if normalized.upper() != PROMO_CODE:
        raise ValueError(UNKNOWN_PROMO_MESSAGE)
    return normalized


def apply_promo(price: int, promo_code: str | None) -> tuple[int, int]:
    """Возвращает сумму к оплате и скидку. Обе величины — целые копейки."""
    if normalize_promo(promo_code) is None:
        return price, 0
    discount = price * PROMO_PERCENT // 100
    return price - discount, discount


def build_schedule(amount: int, months: int) -> list[int]:
    """Делит сумму на срок. Лишние копейки добавляются к первым платежам."""
    base, remainder = divmod(amount, months)
    return [base + 1 if index < remainder else base for index in range(months)]
