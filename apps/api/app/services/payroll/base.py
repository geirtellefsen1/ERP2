"""
Abstract payroll calculator. Each country module subclasses this.

The base class implements the pipeline — collect, calculate earnings,
calculate deductions, calculate employer contributions, assemble payslip —
and delegates the country-specific math to abstract hook methods.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from app.services.money import Money

from .models import (
    EmployeeInput,
    PayslipResult,
)


class PayrollCalculationError(Exception):
    """Raised when a payroll calculation cannot proceed."""


class PayrollCalculator(ABC):
    """Interface every country's payroll module must implement."""

    country_code: str
    currency: str

    # ── Calculation entry point ─────────────────────────────────────

    def calculate(self, employee: EmployeeInput, period_start, period_end) -> PayslipResult:
        """Run the full per-employee pipeline."""
        self._validate_input(employee)

        gross = employee.gross_salary
        additional = employee.additional_gross or Money.zero(self.currency)
        total_earnings = gross + additional

        result = PayslipResult(
            employee_id=employee.id,
            employee_name=f"{employee.first_name} {employee.last_name}",
            country=self.country_code,
            period_start=period_start,
            period_end=period_end,
            gross_salary=gross,
            total_earnings=total_earnings,
            total_employee_deductions=Money.zero(self.currency),
            total_employer_contributions=Money.zero(self.currency),
            net_pay=Money.zero(self.currency),
        )

        # Earnings
        result.add_line("BASE", "Base salary", gross, "earning")
        if not additional.is_zero():
            result.add_line("ADDITIONAL", "Additional earnings", additional, "earning")

        # Pre-tax deductions reduce taxable income
        pre_tax = employee.pre_tax_deductions or Money.zero(self.currency)
        taxable = total_earnings - pre_tax
        if not pre_tax.is_zero():
            result.add_line("PRETAX", "Pre-tax deductions", pre_tax, "employee_deduction")

        # Employee deductions (country-specific)
        employee_deductions_total = Money.zero(self.currency)
        for line in self._calculate_employee_deductions(employee, taxable):
            result.lines.append(line)
            if line.type == "employee_deduction":
                employee_deductions_total = employee_deductions_total + line.amount

        # Post-tax deductions
        post_tax = employee.post_tax_deductions or Money.zero(self.currency)
        if not post_tax.is_zero():
            result.add_line("POSTTAX", "Post-tax deductions", post_tax, "employee_deduction")
            employee_deductions_total = employee_deductions_total + post_tax

        result.total_employee_deductions = employee_deductions_total + pre_tax

        # Employer contributions (country-specific)
        employer_total = Money.zero(self.currency)
        for line in self._calculate_employer_contributions(employee, total_earnings):
            result.lines.append(line)
            employer_total = employer_total + line.amount
        result.total_employer_contributions = employer_total

        # Net
        result.net_pay = total_earnings - result.total_employee_deductions

        # Allow the subclass to append warnings or adjust the result
        self._post_calculate(employee, result)

        return result

    # ── Hooks for country modules ──────────────────────────────────

    @abstractmethod
    def _calculate_employee_deductions(
        self, employee: EmployeeInput, taxable: Money
    ) -> list:
        """Return a list of PayslipLine objects for employee deductions."""

    @abstractmethod
    def _calculate_employer_contributions(
        self, employee: EmployeeInput, gross: Money
    ) -> list:
        """Return a list of PayslipLine objects for employer contributions."""

    def _post_calculate(self, employee: EmployeeInput, result: PayslipResult) -> None:
        """Optional hook — no-op by default."""
        pass

    def _validate_input(self, employee: EmployeeInput) -> None:
        """Basic sanity checks on the employee input."""
        if employee.gross_salary.currency != self.currency:
            raise PayrollCalculationError(
                f"Currency mismatch: employee salary is {employee.gross_salary.currency} "
                f"but {self.country_code} payroll expects {self.currency}"
            )
        if employee.tax_percentage < Decimal(0) or employee.tax_percentage > Decimal(1):
            raise PayrollCalculationError(
                f"Invalid tax_percentage {employee.tax_percentage} — "
                f"expected a decimal fraction between 0 and 1"
            )
        if employee.age < 0 or employee.age > 150:
            raise PayrollCalculationError(f"Invalid age {employee.age}")
