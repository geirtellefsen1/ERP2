"""
Currency conversion service.

Rates are fetched from the European Central Bank's daily reference rates
(free, no API key, updated around 16:00 CET on banking days). Rates are
cached in-process for 24 hours to avoid hammering the endpoint.

For determinism in tests and graceful degradation when the network is
unavailable, a fallback rate table is built in. Production code should
still prefer the live ECB feed — the fallbacks are last-resort only and
noted as stale.

Usage:
    from app.services.currency import CurrencyService
    from app.services.money import Money

    converted = CurrencyService.convert(Money("1000.00", "NOK"), "EUR")
    rate = CurrencyService.get_rate("SEK", "EUR", date.today())
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from xml.etree import ElementTree

import httpx

from .money import Money

logger = logging.getLogger(__name__)


ECB_DAILY_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
CACHE_TTL = timedelta(hours=24)


# ── Fallback rates (against EUR = 1.0) ──────────────────────────────────────
# Used only when the live feed fails. Deliberately conservative, updated
# manually when the team notices a significant drift. Tests rely on these
# being stable.

_FALLBACK_RATES_EUR: dict[str, Decimal] = {
    "EUR": Decimal("1.0"),
    "NOK": Decimal("11.80"),  # approx EUR→NOK Jan 2026
    "SEK": Decimal("11.30"),  # approx EUR→SEK Jan 2026
    "USD": Decimal("1.08"),
    "GBP": Decimal("0.84"),
    "ZAR": Decimal("20.50"),
}


@dataclass
class _RateCache:
    """In-process cache for ECB rates relative to EUR."""
    rates_eur: dict[str, Decimal]
    fetched_at: datetime
    source: str  # "ecb" | "fallback"

    def is_fresh(self) -> bool:
        return datetime.now(timezone.utc) - self.fetched_at < CACHE_TTL


class CurrencyError(Exception):
    """Raised when a conversion cannot be performed."""


class CurrencyService:
    """Stateful facade — holds a module-level cache of rates."""

    _cache: Optional[_RateCache] = None
    _lock = threading.Lock()

    # ── Public API ──────────────────────────────────────────────────

    @classmethod
    def get_rate(
        cls,
        from_currency: str,
        to_currency: str,
        on_date: date | None = None,
    ) -> Decimal:
        """
        Return the exchange rate such that `amount_from * rate = amount_to`.

        The `on_date` parameter is accepted for API symmetry with the spec
        but this implementation only holds the latest rates — historical
        conversion requires a database-backed rate table (Sprint 20+).
        """
        from_c = from_currency.upper()
        to_c = to_currency.upper()

        if from_c == to_c:
            return Decimal("1.0")

        rates = cls._get_rates_eur()

        if from_c not in rates:
            raise CurrencyError(
                f"No rate available for {from_c}. Known: {sorted(rates.keys())}"
            )
        if to_c not in rates:
            raise CurrencyError(
                f"No rate available for {to_c}. Known: {sorted(rates.keys())}"
            )

        # Cross rate via EUR:  from→EUR = 1/rates[from],  EUR→to = rates[to]
        from_rate = rates[from_c]
        to_rate = rates[to_c]
        cross = to_rate / from_rate
        return cross

    @classmethod
    def convert(
        cls,
        money: Money,
        to_currency: str,
        on_date: date | None = None,
    ) -> Money:
        """Convert a Money amount to another currency."""
        if money.currency == to_currency.upper():
            return money
        rate = cls.get_rate(money.currency, to_currency, on_date)
        converted_amount = money.amount * rate
        return Money(converted_amount, to_currency)

    @classmethod
    def refresh(cls) -> None:
        """Force refresh from ECB (ignores cache TTL)."""
        cls._cache = None
        cls._get_rates_eur()

    @classmethod
    def source(cls) -> str:
        """Return the data source currently in the cache: 'ecb' or 'fallback'."""
        if cls._cache is None:
            cls._get_rates_eur()
        return cls._cache.source if cls._cache else "unknown"

    @classmethod
    def prime_cache(cls, rates_eur: dict[str, Decimal], source: str = "test") -> None:
        """
        Test helper — load a known rate table into the cache so tests are
        deterministic without depending on network or fallback values.
        """
        with cls._lock:
            cls._cache = _RateCache(
                rates_eur=dict(rates_eur),
                fetched_at=datetime.now(timezone.utc),
                source=source,
            )

    @classmethod
    def clear_cache(cls) -> None:
        """Test helper — drop the cache entirely."""
        with cls._lock:
            cls._cache = None

    # ── Internal ────────────────────────────────────────────────────

    @classmethod
    def _get_rates_eur(cls) -> dict[str, Decimal]:
        with cls._lock:
            if cls._cache and cls._cache.is_fresh():
                return cls._cache.rates_eur

            rates = cls._fetch_ecb_rates()
            if rates:
                cls._cache = _RateCache(
                    rates_eur=rates,
                    fetched_at=datetime.now(timezone.utc),
                    source="ecb",
                )
            else:
                # Fall back to static table; log loudly
                logger.warning(
                    "ECB rate feed unavailable — using fallback rates. "
                    "This is acceptable for dev and tests but production "
                    "should alert on this condition."
                )
                cls._cache = _RateCache(
                    rates_eur=dict(_FALLBACK_RATES_EUR),
                    fetched_at=datetime.now(timezone.utc),
                    source="fallback",
                )
            return cls._cache.rates_eur

    @staticmethod
    def _fetch_ecb_rates() -> dict[str, Decimal] | None:
        """Fetch latest rates from ECB. Returns None on any failure."""
        try:
            resp = httpx.get(ECB_DAILY_URL, timeout=5.0)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("ECB fetch failed: %s", e)
            return None

        try:
            root = ElementTree.fromstring(resp.text)
            ns = {"g": "http://www.gesmes.org/xml/2002-08-01",
                  "e": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}
            rates: dict[str, Decimal] = {"EUR": Decimal("1.0")}
            for cube in root.findall(".//e:Cube/e:Cube/e:Cube", ns):
                currency = cube.get("currency")
                rate_str = cube.get("rate")
                if currency and rate_str:
                    rates[currency] = Decimal(rate_str)
            return rates
        except Exception as e:
            logger.warning("ECB parse failed: %s", e)
            return None
