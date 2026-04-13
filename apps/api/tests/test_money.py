"""
Unit tests for the Money value object and CurrencyService.

Pure unit tests — no DB, no network. CurrencyService tests prime the cache
with known rates so they are deterministic.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.money import Money, CurrencyMismatchError
from app.services.currency import CurrencyService, CurrencyError


# ── Money basics ───────────────────────────────────────────────────────────


def test_money_constructs_from_string():
    m = Money("1000.50", "NOK")
    assert m.amount == Decimal("1000.50")
    assert m.currency == "NOK"


def test_money_constructs_from_int():
    assert Money(1000, "EUR").amount == Decimal("1000.00")


def test_money_quantizes_to_currency_exponent():
    # Two decimal places for EUR/NOK/SEK
    assert Money("1.005", "EUR").amount == Decimal("1.01")  # half-up
    assert Money("1.004", "NOK").amount == Decimal("1.00")


def test_money_zero_factory():
    assert Money.zero("SEK").amount == Decimal("0.00")
    assert Money.zero("SEK").currency == "SEK"


def test_money_currency_uppercased():
    assert Money("100", "nok").currency == "NOK"


def test_money_invalid_amount_raises():
    with pytest.raises(ValueError):
        Money("not-a-number", "EUR")


# ── Minor units round-trip ─────────────────────────────────────────────────


def test_money_to_minor_units_nok():
    assert Money("1000.00", "NOK").to_minor_units() == 100000
    assert Money("0.05", "NOK").to_minor_units() == 5
    assert Money("1234.56", "NOK").to_minor_units() == 123456


def test_money_from_minor_units():
    assert Money.from_minor_units(123456, "EUR") == Money("1234.56", "EUR")
    assert Money.from_minor_units(5, "NOK") == Money("0.05", "NOK")
    assert Money.from_minor_units(0, "SEK") == Money.zero("SEK")


def test_money_minor_units_round_trip():
    original = Money("9876.54", "EUR")
    restored = Money.from_minor_units(original.to_minor_units(), "EUR")
    assert restored == original


# ── Arithmetic ────────────────────────────────────────────────────────────


def test_money_addition_same_currency():
    a = Money("100.00", "NOK")
    b = Money("50.00", "NOK")
    assert (a + b) == Money("150.00", "NOK")


def test_money_subtraction_same_currency():
    assert (Money("100", "EUR") - Money("30", "EUR")) == Money("70", "EUR")


def test_money_addition_rejects_currency_mismatch():
    with pytest.raises(CurrencyMismatchError):
        Money("100", "NOK") + Money("100", "EUR")


def test_money_multiplication_by_scalar():
    assert (Money("100.00", "EUR") * 3) == Money("300.00", "EUR")
    assert (Money("100.00", "NOK") * Decimal("0.25")) == Money("25.00", "NOK")


def test_money_negation():
    assert -Money("100", "EUR") == Money("-100", "EUR")


# ── Comparison ────────────────────────────────────────────────────────────


def test_money_comparison_same_currency():
    a = Money("100", "EUR")
    b = Money("200", "EUR")
    assert a < b
    assert b > a
    assert a <= Money("100", "EUR")
    assert a == Money("100", "EUR")


def test_money_comparison_rejects_currency_mismatch():
    with pytest.raises(CurrencyMismatchError):
        Money("100", "NOK") < Money("100", "EUR")


def test_money_equality_across_currencies_is_false():
    """100 NOK != 100 EUR — different currencies means not equal, without raising."""
    assert Money("100", "NOK") != Money("100", "EUR")


def test_money_is_hashable():
    s = {Money("100", "NOK"), Money("100", "EUR"), Money("100", "NOK")}
    assert len(s) == 2  # same Money deduplicated, different currencies kept


# ── CurrencyService (primed cache, deterministic) ────────────────────────


@pytest.fixture(autouse=True)
def _primed_rates():
    """Prime the cache with fixed rates before each test in this module."""
    CurrencyService.prime_cache(
        {
            "EUR": Decimal("1.0"),
            "NOK": Decimal("11.80"),
            "SEK": Decimal("11.30"),
            "USD": Decimal("1.08"),
        },
        source="test",
    )
    yield
    CurrencyService.clear_cache()


def test_rate_same_currency_is_one():
    assert CurrencyService.get_rate("EUR", "EUR") == Decimal("1.0")


def test_rate_eur_to_nok():
    # 1 EUR = 11.80 NOK exactly
    assert CurrencyService.get_rate("EUR", "NOK") == Decimal("11.80")


def test_rate_nok_to_eur_inverse():
    rate = CurrencyService.get_rate("NOK", "EUR")
    # Should be 1 / 11.80
    expected = Decimal("1.0") / Decimal("11.80")
    assert rate == expected


def test_rate_cross_via_eur():
    # NOK -> SEK should cross through EUR: SEK/NOK = 11.30/11.80
    rate = CurrencyService.get_rate("NOK", "SEK")
    expected = Decimal("11.30") / Decimal("11.80")
    assert rate == expected


def test_rate_unknown_currency_raises():
    with pytest.raises(CurrencyError):
        CurrencyService.get_rate("XYZ", "EUR")
    with pytest.raises(CurrencyError):
        CurrencyService.get_rate("EUR", "XYZ")


def test_convert_same_currency_is_noop():
    m = Money("1000", "EUR")
    assert CurrencyService.convert(m, "EUR") is m


def test_convert_eur_to_nok():
    eur = Money("100.00", "EUR")
    nok = CurrencyService.convert(eur, "NOK")
    assert nok.currency == "NOK"
    assert nok.amount == Decimal("1180.00")


def test_convert_nok_to_sek_via_eur():
    nok = Money("1180.00", "NOK")
    sek = CurrencyService.convert(nok, "SEK")
    assert sek.currency == "SEK"
    # 1180 NOK = 100 EUR = 1130 SEK
    assert sek.amount == Decimal("1130.00")


def test_source_reports_primed_value():
    assert CurrencyService.source() == "test"
