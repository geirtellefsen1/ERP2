"""
Core payroll engine — pluggable per-country calculators.

The spec's payroll pipeline:
  1. Collect inputs (hours, expenses, leave, one-time items)
  2. Apply jurisdiction rules (tax tables, deduction rates, allowances)
  3. Calculate gross, deductions, net
  4. Generate payslip data
  5. Post to accounting (journal entries to payroll expense + liability)
  6. Trigger statutory filing (Tulorekisteri realtime, A-melding/AGD monthly)
  7. Generate bank payment file
  8. Deliver payslips (portal, email, WhatsApp)

This module owns steps 1-4. Steps 5-8 live in downstream services because
they depend on the journal engine, the filing connectors, and delivery
channels — all separate concerns.

Usage:
    from app.services.payroll import run_payroll, PayrollInput, EmployeeInput
    from datetime import date

    result = run_payroll(
        country="NO",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        employees=[
            EmployeeInput(
                id=1,
                first_name="Sarah",
                last_name="Mokoena",
                gross_salary=Money("45000", "NOK"),
                tax_percentage=Decimal("0.35"),
                age=38,
                work_region="oslo",
                pension_scheme="OTP_2_PERCENT",
            ),
        ],
    )
    # result is a PayrollRunResult with one PayslipResult per employee
    # plus aggregate totals for the run.
"""
from .models import (
    EmployeeInput,
    PayrollInput,
    PayslipResult,
    PayslipLine,
    PayrollRunResult,
    PensionScheme,
)
from .engine import run_payroll, get_calculator
from .base import PayrollCalculator, PayrollCalculationError

__all__ = [
    "EmployeeInput",
    "PayrollInput",
    "PayslipResult",
    "PayslipLine",
    "PayrollRunResult",
    "PensionScheme",
    "run_payroll",
    "get_calculator",
    "PayrollCalculator",
    "PayrollCalculationError",
]
