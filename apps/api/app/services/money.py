"""
Money value object — an amount paired with its ISO 4217 currency.

Why this exists:
- Financial amounts without a currency are a bug waiting to happen. Mixing
  NOK and SEK in a simple `Decimal` addition silently produces wrong answers.
- This class refuses to add, subtract, or compare two amounts in different
  currencies unless you explicitly convert one of them via CurrencyService.
- Amounts are stored as `Decimal` — never floats. Float arithmetic on money
  is unacceptable.

Usage:
    from app.services.money import Money

    a = Money("1000.00", "NOK")
    b = Money("500.00", "NOK")
    c = a + b                     # Money('1500.00', 'NOK')

    d = Money("100.00", "EUR")
    a + d                         # raises CurrencyMismatchError

Integer-based storage:
    The spec (Section 9.1) mandates "all monetary values stored as integers
    (øre/ören/cents)". Use `Money.to_minor_units()` when serialising to DB
    and `Money.from_minor_units(...)` when loading back.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union

Amount = Union[Decimal, int, str, float]


# ── ISO 4217 minor-unit exponents (digits after the decimal point) ──────────

_MINOR_UNITS: dict[str, int] = {
    "NOK": 2,  # 1 krone = 100 øre
    "SEK": 2,  # 1 krona = 100 öre
    "EUR": 2,  # 1 euro = 100 cents
    "USD": 2,
    "GBP": 2,
    "ZAR": 2,
    "JPY": 0,  # Japanese yen has no subunit
    "KWD": 3,  # Kuwaiti dinar has three
}

SUPPORTED_CURRENCIES = ("NOK", "SEK", "EUR")


class CurrencyMismatchError(ValueError):
    """Raised when trying to combine amounts in different currencies."""


def _normalise_currency(code: str) -> str:
    return code.strip().upper()


def _exponent(currency: str) -> int:
    return _MINOR_UNITS.get(currency, 2)


def _quantize_to_currency(amount: Decimal, currency: str) -> Decimal:
    """Round an amount to the correct number of decimal places for the currency."""
    exponent = _exponent(currency)
    quantum = Decimal(1).scaleb(-exponent)
    return amount.quantize(quantum, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Money:
    """
    Immutable amount + currency.

    Use the `Money(amount, currency)` constructor for the common case. For
    database-safe integer storage, use `Money.to_minor_units()` and
    `Money.from_minor_units(units, currency)`.
    """
    amount: Decimal
    currency: str

    def __init__(self, amount: Amount, currency: str):
        try:
            parsed = Decimal(str(amount))
        except InvalidOperation as e:
            raise ValueError(f"Invalid monetary amount: {amount!r}") from e

        cleaned_currency = _normalise_currency(currency)
        quantized = _quantize_to_currency(parsed, cleaned_currency)

        object.__setattr__(self, "amount", quantized)
        object.__setattr__(self, "currency", cleaned_currency)

    # ── Construction helpers ─────────────────────────────────────────

    @classmethod
    def zero(cls, currency: str) -> "Money":
        return cls(Decimal(0), currency)

    @classmethod
    def from_minor_units(cls, units: int, currency: str) -> "Money":
        """Build from an integer in the currency's minor units (øre/ören/cents)."""
        cc = _normalise_currency(currency)
        exp = _exponent(cc)
        divisor = Decimal(10) ** exp
        return cls(Decimal(units) / divisor, cc)

    def to_minor_units(self) -> int:
        """
        Convert to integer minor units for database storage.
        This is the canonical persistent form — always round-trip-safe.
        """
        exp = _exponent(self.currency)
        multiplier = Decimal(10) ** exp
        return int((self.amount * multiplier).to_integral_value(rounding=ROUND_HALF_UP))

    # ── Arithmetic ───────────────────────────────────────────────────

    def _assert_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"Cannot combine {self.currency} and {other.currency} without conversion. "
                f"Use CurrencyService.convert() first."
            )

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        self._assert_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        self._assert_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Amount) -> "Money":
        """Multiply by a scalar (e.g. VAT rate or quantity)."""
        try:
            multiplier = Decimal(str(factor))
        except InvalidOperation as e:
            raise ValueError(f"Invalid multiplier: {factor!r}") from e
        return Money(self.amount * multiplier, self.currency)

    __rmul__ = __mul__

    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)

    # ── Comparison ───────────────────────────────────────────────────

    def __lt__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.amount >= other.amount

    # Equality intentionally allows cross-currency comparison to return False
    # (so dict keys and sets containing Money work without surprises)
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __hash__(self) -> int:
        return hash((self.amount, self.currency))

    # ── Formatting ───────────────────────────────────────────────────

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __repr__(self) -> str:
        return f"Money('{self.amount}', '{self.currency}')"

    # ── Utilities ────────────────────────────────────────────────────

    def is_zero(self) -> bool:
        return self.amount == Decimal(0)

    def is_positive(self) -> bool:
        return self.amount > Decimal(0)

    def is_negative(self) -> bool:
        return self.amount < Decimal(0)
