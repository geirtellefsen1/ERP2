"""
Jurisdiction Engine — pluggable country modules for BPO Nexus.

Every client company is assigned a primary jurisdiction (NO / SE / FI). The
engine loads the correct rules package at runtime so accounting, payroll, VAT,
and filing logic always matches the client's country — agents cannot
accidentally apply Norwegian VAT codes to a Swedish client because the
jurisdiction is enforced at the API layer.

Usage:
    from app.jurisdictions import JurisdictionEngine

    rates = JurisdictionEngine.get_vat_rates("NO", date(2026, 1, 1))
    rules = JurisdictionEngine.get_payroll_rules("SE", "permanent", date.today())
    cal = JurisdictionEngine.get_filing_calendar("FI", 2026)

Adding a new country = dropping a new module in this package that subclasses
`JurisdictionBase` and registering it in `REGISTRY`. The core platform does
not change.
"""
from __future__ import annotations

from datetime import date
from typing import Type

from .base import (
    JurisdictionBase,
    VatRate,
    PayrollRules,
    FilingDeadline,
    PublicHoliday,
    BankFormat,
    AccountTemplate,
    StatutoryForm,
)
from .norway import NorwayJurisdiction
from .sweden import SwedenJurisdiction
from .finland import FinlandJurisdiction


# ─── Registry ────────────────────────────────────────────────────────────────

REGISTRY: dict[str, Type[JurisdictionBase]] = {
    "NO": NorwayJurisdiction,
    "SE": SwedenJurisdiction,
    "FI": FinlandJurisdiction,
}

SUPPORTED_COUNTRIES = tuple(REGISTRY.keys())


class UnknownJurisdictionError(ValueError):
    """Raised when an unsupported country code is requested."""


def _get(country_code: str) -> JurisdictionBase:
    """Look up a jurisdiction by ISO country code, raising a clear error."""
    cc = country_code.upper()
    if cc not in REGISTRY:
        raise UnknownJurisdictionError(
            f"Unsupported jurisdiction '{country_code}'. "
            f"Supported: {', '.join(SUPPORTED_COUNTRIES)}"
        )
    return REGISTRY[cc]()


# ─── Public API ──────────────────────────────────────────────────────────────


class JurisdictionEngine:
    """
    Static facade over the registered jurisdiction modules. All methods are
    pure and deterministic — no database access, no network calls. This makes
    them trivially unit-testable and cacheable.
    """

    @staticmethod
    def is_supported(country_code: str) -> bool:
        return country_code.upper() in REGISTRY

    @staticmethod
    def get_vat_rates(country_code: str, on_date: date) -> list[VatRate]:
        return _get(country_code).vat_rates(on_date)

    @staticmethod
    def get_vat_filing_frequency(country_code: str) -> str:
        """Return "monthly", "bimonthly", "quarterly", or "annual"."""
        return _get(country_code).vat_filing_frequency()

    @staticmethod
    def get_payroll_rules(
        country_code: str, employee_type: str, on_date: date
    ) -> PayrollRules:
        return _get(country_code).payroll_rules(employee_type, on_date)

    @staticmethod
    def get_filing_calendar(country_code: str, year: int) -> list[FilingDeadline]:
        return _get(country_code).filing_calendar(year)

    @staticmethod
    def get_public_holidays(country_code: str, year: int) -> list[PublicHoliday]:
        return _get(country_code).public_holidays(year)

    @staticmethod
    def get_coa_template(
        country_code: str, industry_vertical: str | None = None
    ) -> list[AccountTemplate]:
        return _get(country_code).coa_template(industry_vertical)

    @staticmethod
    def get_statutory_forms(country_code: str) -> list[StatutoryForm]:
        return _get(country_code).statutory_forms()

    @staticmethod
    def validate_vat_number(country_code: str, vat_number: str) -> bool:
        return _get(country_code).validate_vat_number(vat_number)

    @staticmethod
    def get_bank_format(country_code: str) -> BankFormat:
        return _get(country_code).bank_format()

    @staticmethod
    def get_currency(country_code: str) -> str:
        """ISO 4217 currency code (NOK, SEK, EUR)."""
        return _get(country_code).currency()

    @staticmethod
    def get_language(country_code: str) -> str:
        """Primary IETF language tag (nb-NO, sv-SE, fi-FI)."""
        return _get(country_code).language()


__all__ = [
    "JurisdictionEngine",
    "JurisdictionBase",
    "UnknownJurisdictionError",
    "REGISTRY",
    "SUPPORTED_COUNTRIES",
    "VatRate",
    "PayrollRules",
    "FilingDeadline",
    "PublicHoliday",
    "BankFormat",
    "AccountTemplate",
    "StatutoryForm",
]
