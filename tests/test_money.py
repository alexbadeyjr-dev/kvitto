import pytest

from app.money import apply_promo, build_schedule, normalize_promo


def test_schedule_puts_remainder_on_first_payments() -> None:
    assert build_schedule(1_990_000, 3) == [663_334, 663_333, 663_333]


@pytest.mark.parametrize("months", [3, 6, 12])
def test_schedule_sum_equals_amount(months: int) -> None:
    amount = 1_990_000
    schedule = build_schedule(amount, months)

    assert len(schedule) == months
    assert sum(schedule) == amount
    assert max(schedule) - min(schedule) <= 1


def test_promo_is_ten_percent_and_case_insensitive() -> None:
    assert apply_promo(1_990_000, None) == (1_990_000, 0)
    assert apply_promo(1_990_000, "kvitto10") == (1_791_000, 199_000)
    assert apply_promo(1_990_000, "KVITTO10") == (1_791_000, 199_000)


def test_unknown_promo_is_rejected() -> None:
    with pytest.raises(ValueError, match="Неизвестный промокод"):
        normalize_promo("sale")
