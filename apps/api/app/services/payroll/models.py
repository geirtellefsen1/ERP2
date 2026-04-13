"""
Data classes for the payroll engine — inputs and outputs.

All amounts are Money objects so cross-currency bugs are impossible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from app.services.money import Money


PensionScheme = Literal[
    # Norway
    "NO_OTP_2_PERCENT",      # 2% minimum
    "NO_OTP_5_PERCENT",      # common higher tier
    # Sweden
    "SE_ITP1",               # standard white-collar
    "SE_ITP2",               # legacy
    "SE_SAF_LO",             # blue-collar
    "SE_NONE",               # no agreement
    # Finland
    "FI_TYEL_STANDARD",      # default — company negotiates rate annually
    # Everyone
    "NONE",
]


@dataclass
class EmployeeInput:
    """Everything the payroll engine needs to know about an employee."""
    id: int
    first_name: str
    last_name: str
    gross_salary: Money
    # Personalised withholding percentage from the country's tax card system.
    # Stored against the employee record and refreshed periodically from the
    # respective tax authority API (Skatteetaten / Skatteverket / Vero).
    tax_percentage: Decimal
    age: int
    work_region: str = ""       # Norway: AGA zone lookup; Sweden: county; Finland: n/a
    pension_scheme: PensionScheme = "NONE"
    is_first_employment_year: bool = False  # Sweden: affects youth reductions
    id_number: Optional[str] = None
    # Extra one-off items for this period (bonus, overtime, taxable perk, etc.)
    additional_gross: Money | None = None
    # Pre-tax deductions (union dues, additional pension contributions)
    pre_tax_deductions: Money | None = None
    # Post-tax deductions (garnishments, loans)
    post_tax_deductions: Money | None = None
    # Sick days in this period (0-based; engine applies country rules)
    sick_days: int = 0
    # Holiday days taken in this period
    holiday_days: int = 0


@dataclass
class PayrollInput:
    """Input for a full payroll run covering one or more employees."""
    country: str               # NO / SE / FI
    period_start: date
    period_end: date
    employees: list[EmployeeInput]
    client_id: Optional[int] = None  # links the run to a client company


@dataclass
class PayslipLine:
    """A single line on a payslip (earning or deduction)."""
    code: str                  # e.g. "BASE", "PAYE", "AGA", "OTP"
    label: str
    amount: Money
    type: Literal["earning", "employee_deduction", "employer_contribution"]


@dataclass
class PayslipResult:
    """Calculated payslip for one employee for one period."""
    employee_id: int
    employee_name: str
    country: str
    period_start: date
    period_end: date

    gross_salary: Money
    total_earnings: Money      # gross + additional
    total_employee_deductions: Money
    total_employer_contributions: Money
    net_pay: Money             # what lands in the employee's bank

    lines: list[PayslipLine] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_line(
        self,
        code: str,
        label: str,
        amount: Money,
        type: Literal["earning", "employee_deduction", "employer_contribution"],
    ) -> None:
        self.lines.append(PayslipLine(code=code, label=label, amount=amount, type=type))


@dataclass
class PayrollRunResult:
    """Aggregate result for a payroll run across all employees."""
    country: str
    period_start: date
    period_end: date
    currency: str
    payslips: list[PayslipResult]

    @property
    def total_gross(self) -> Money:
        if not self.payslips:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for p in self.payslips:
            total = total + p.gross_salary
        return total

    @property
    def total_employee_deductions(self) -> Money:
        if not self.payslips:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for p in self.payslips:
            total = total + p.total_employee_deductions
        return total

    @property
    def total_employer_contributions(self) -> Money:
        if not self.payslips:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for p in self.payslips:
            total = total + p.total_employer_contributions
        return total

    @property
    def total_net(self) -> Money:
        if not self.payslips:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for p in self.payslips:
            total = total + p.net_pay
        return total
