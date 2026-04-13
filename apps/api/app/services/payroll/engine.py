"""
Payroll engine entry point — selects the correct country calculator and
runs the pipeline for every employee in the input.
"""
from __future__ import annotations

from typing import Type

from .base import PayrollCalculator, PayrollCalculationError
from .models import PayrollInput, PayrollRunResult
from .norway import NorwayPayrollCalculator
from .sweden import SwedenPayrollCalculator
from .finland import FinlandPayrollCalculator


_REGISTRY: dict[str, Type[PayrollCalculator]] = {
    "NO": NorwayPayrollCalculator,
    "SE": SwedenPayrollCalculator,
    "FI": FinlandPayrollCalculator,
}


def get_calculator(country_code: str) -> PayrollCalculator:
    cc = country_code.upper()
    if cc not in _REGISTRY:
        raise PayrollCalculationError(
            f"No payroll calculator registered for country '{country_code}'. "
            f"Supported: {', '.join(sorted(_REGISTRY.keys()))}"
        )
    return _REGISTRY[cc]()


def run_payroll(input: PayrollInput) -> PayrollRunResult:
    """
    Execute a full payroll run. Returns an aggregated result with one
    PayslipResult per employee.

    This is a pure calculation — it does NOT persist to the database, post
    journal entries, or trigger statutory filing. Those are downstream
    concerns handled by the payroll router after the calculation succeeds.
    """
    calculator = get_calculator(input.country)

    payslips = []
    for employee in input.employees:
        payslip = calculator.calculate(
            employee=employee,
            period_start=input.period_start,
            period_end=input.period_end,
        )
        payslips.append(payslip)

    return PayrollRunResult(
        country=input.country.upper(),
        period_start=input.period_start,
        period_end=input.period_end,
        currency=calculator.currency,
        payslips=payslips,
    )
