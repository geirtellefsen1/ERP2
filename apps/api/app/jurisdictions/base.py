"""
Jurisdiction base interface and shared data classes.

Every country module must subclass JurisdictionBase and implement the
abstract methods. Helper dataclasses (VatRate, PayrollRules, etc.) are
defined here so country modules share a single shape.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal


# ─── Shared value objects ────────────────────────────────────────────────────

VatCategory = Literal["standard", "reduced", "super_reduced", "zero", "exempt"]


@dataclass(frozen=True)
class VatRate:
    """A VAT rate applicable to a jurisdiction for a given period."""
    code: str              # e.g. "NO-25", "SE-12", "FI-14"
    label: str             # human-readable
    rate: Decimal          # 0.25 for 25%
    category: VatCategory
    applies_to: str        # free-form description ("food", "hotel", "all")
    effective_from: date
    effective_to: date | None = None  # None = still in force


@dataclass(frozen=True)
class PayrollDeduction:
    """A single statutory deduction component of a payroll calculation."""
    code: str              # "PAYE", "AGA", "OTP", "TyEL", "ARBGAV"
    label: str
    rate: Decimal | None   # None if it's a fixed amount
    fixed_amount: Decimal | None = None
    base: Literal["gross", "taxable", "capped", "custom"] = "gross"
    paid_by: Literal["employee", "employer", "both"] = "employee"
    notes: str = ""


@dataclass(frozen=True)
class PayrollRules:
    """Full set of rules needed to run payroll for an employee in a jurisdiction."""
    country_code: str
    effective_on: date
    currency: str
    employer_contributions: list[PayrollDeduction]
    employee_deductions: list[PayrollDeduction]
    holiday_pay_rate: Decimal       # e.g. 0.102 for Norway's 10.2%
    sick_pay_employer_days: int     # employer's sick pay obligation in days
    reporting_frequency: Literal["realtime_5d", "monthly", "bimonthly"]
    reporting_endpoint: str         # "Altinn A-melding", "Skatteverket AGD", etc.
    notes: str = ""


@dataclass(frozen=True)
class FilingDeadline:
    """A statutory filing deadline in a jurisdiction's calendar."""
    form_code: str         # e.g. "MVA-melding", "AGD", "Tulorekisteri"
    label: str
    due_date: date
    covers_period: str     # "Q1 2026", "January 2026", "realtime"
    endpoint: str          # "Altinn", "Skatteverket", "OmaVero"
    reminder_days: tuple[int, ...] = (5, 2, 1)


@dataclass(frozen=True)
class PublicHoliday:
    """A public (non-working) day for SLA and payroll calendars."""
    date: date
    name: str
    country_code: str


@dataclass(frozen=True)
class BankFormat:
    """Local bank account format rules."""
    country_code: str
    iban_prefix: str               # "NO", "SE", "FI"
    iban_length: int               # total chars incl. prefix
    domestic_format: str           # free-form description
    payment_file_format: str       # "Bankgirot", "SEPA", "Nordic PAIN"
    open_banking_provider: str     # "Aiia", "Tink", "OP"


@dataclass(frozen=True)
class AccountTemplate:
    """A single row from a country-standard chart of accounts template."""
    code: str
    name_local: str        # in country language
    name_en: str
    account_type: Literal["asset", "liability", "equity", "revenue", "expense"]
    sub_type: str = ""
    parent_code: str | None = None
    is_control_account: bool = False


@dataclass(frozen=True)
class StatutoryForm:
    """A statutory form the jurisdiction requires."""
    code: str              # e.g. "RF-1167"
    label: str
    description: str
    frequency: Literal["monthly", "bimonthly", "quarterly", "annual", "adhoc"]
    endpoint: str          # submission target


# ─── Base class ──────────────────────────────────────────────────────────────


class JurisdictionBase(ABC):
    """Abstract base every country module must implement."""

    country_code: str
    country_name: str

    @abstractmethod
    def currency(self) -> str: ...

    @abstractmethod
    def language(self) -> str: ...

    @abstractmethod
    def vat_rates(self, on_date: date) -> list[VatRate]: ...

    @abstractmethod
    def vat_filing_frequency(self) -> str: ...

    @abstractmethod
    def payroll_rules(
        self, employee_type: str, on_date: date
    ) -> PayrollRules: ...

    @abstractmethod
    def filing_calendar(self, year: int) -> list[FilingDeadline]: ...

    @abstractmethod
    def public_holidays(self, year: int) -> list[PublicHoliday]: ...

    @abstractmethod
    def coa_template(
        self, industry_vertical: str | None
    ) -> list[AccountTemplate]: ...

    @abstractmethod
    def statutory_forms(self) -> list[StatutoryForm]: ...

    @abstractmethod
    def validate_vat_number(self, vat_number: str) -> bool: ...

    @abstractmethod
    def bank_format(self) -> BankFormat: ...
