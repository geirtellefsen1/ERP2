"""
Norway payroll calculator tests.

All expected values were hand-calculated first, then encoded here. If any
test fails on rate changes, verify against Skatteetaten's published rules
and bump the rate constants in norway.py in the same commit.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.services.money import Money
from app.services.payroll import (
    EmployeeInput,
    PayrollInput,
    run_payroll,
    get_calculator,
    PayrollCalculationError,
)
from app.services.payroll.norway import NorwayPayrollCalculator


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def oslo_employee():
    """Mid-career Oslo-based employee with standard OTP."""
    return EmployeeInput(
        id=1,
        first_name="Sarah",
        last_name="Mokoena",
        gross_salary=Money("45000.00", "NOK"),
        tax_percentage=Decimal("0.35"),
        age=38,
        work_region="oslo",
        pension_scheme="NO_OTP_2_PERCENT",
    )


@pytest.fixture
def over60_employee():
    """Employee over 60 — gets 12% holiday pay instead of 10.2%."""
    return EmployeeInput(
        id=2,
        first_name="Jan",
        last_name="Olsen",
        gross_salary=Money("60000.00", "NOK"),
        tax_percentage=Decimal("0.40"),
        age=63,
        work_region="oslo",
        pension_scheme="NO_OTP_2_PERCENT",
    )


@pytest.fixture
def northern_employee():
    """Employee in Tromsø (zone 5) — 0% AGA."""
    return EmployeeInput(
        id=3,
        first_name="Kari",
        last_name="Hansen",
        gross_salary=Money("40000.00", "NOK"),
        tax_percentage=Decimal("0.30"),
        age=42,
        work_region="tromso",
        pension_scheme="NO_OTP_2_PERCENT",
    )


# ── Calculator selection ──────────────────────────────────────────────────


def test_get_calculator_for_norway():
    calc = get_calculator("NO")
    assert isinstance(calc, NorwayPayrollCalculator)
    assert calc.currency == "NOK"


# ── Earnings ───────────────────────────────────────────────────────────────


def test_gross_salary_appears_on_payslip(oslo_employee):
    calc = NorwayPayrollCalculator()
    result = calc.calculate(oslo_employee, date(2026, 4, 1), date(2026, 4, 30))
    assert result.gross_salary == Money("45000.00", "NOK")
    assert result.total_earnings == Money("45000.00", "NOK")


def test_additional_earnings_added_to_total(oslo_employee):
    oslo_employee.additional_gross = Money("5000.00", "NOK")
    calc = NorwayPayrollCalculator()
    result = calc.calculate(oslo_employee, date(2026, 4, 1), date(2026, 4, 30))
    assert result.total_earnings == Money("50000.00", "NOK")


# ── Employee deductions ───────────────────────────────────────────────────


def test_paye_withheld_at_stored_percentage(oslo_employee):
    """Forskuddstrekk = gross * tax_percentage."""
    calc = NorwayPayrollCalculator()
    result = calc.calculate(oslo_employee, date(2026, 4, 1), date(2026, 4, 30))
    paye_line = next(l for l in result.lines if l.code == "FORSKUDDSTREKK")
    # 45000 * 0.35 = 15750
    assert paye_line.amount == Money("15750.00", "NOK")


def test_net_pay_is_gross_minus_deductions(oslo_employee):
    calc = NorwayPayrollCalculator()
    result = calc.calculate(oslo_employee, date(2026, 4, 1), date(2026, 4, 30))
    # 45000 - 15750 PAYE = 29250
    assert result.net_pay == Money("29250.00", "NOK")


# ── Employer contributions ────────────────────────────────────────────────


def test_aga_zone_1_is_14_1_percent(oslo_employee):
    """Oslo is AGA zone 1 — 14.1%."""
    calc = NorwayPayrollCalculator()
    result = calc.calculate(oslo_employee, date(2026, 4, 1), date(2026, 4, 30))
    aga_line = next(l for l in result.lines if l.code == "AGA")
    # 45000 * 0.141 = 6345
    assert aga_line.amount == Money("6345.00", "NOK")


def test_aga_zone_5_is_zero_percent(northern_employee):
    """Tromsø is zone 5 — 0% AGA. Major tax advantage for northern employers."""
    calc = NorwayPayrollCalculator()
    result = calc.calculate(northern_employee, date(2026, 4, 1), date(2026, 4, 30))
    aga_line = next(l for l in result.lines if l.code == "AGA")
    assert aga_line.amount == Money.zero("NOK")


def test_holiday_pay_10_2_percent_standard(oslo_employee):
    calc = NorwayPayrollCalculator()
    result = calc.calculate(oslo_employee, date(2026, 4, 1), date(2026, 4, 30))
    holiday_line = next(l for l in result.lines if l.code == "FERIEPENGER")
    # 45000 * 0.102 = 4590
    assert holiday_line.amount == Money("4590.00", "NOK")


def test_holiday_pay_12_percent_for_over_60(over60_employee):
    """Employees aged 60+ get 12% holiday pay instead of 10.2%."""
    calc = NorwayPayrollCalculator()
    result = calc.calculate(over60_employee, date(2026, 4, 1), date(2026, 4, 30))
    holiday_line = next(l for l in result.lines if l.code == "FERIEPENGER")
    # 60000 * 0.12 = 7200
    assert holiday_line.amount == Money("7200.00", "NOK")


def test_otp_only_applies_above_1g():
    """OTP is 2% of salary between 1G and 12G annualised."""
    employee = EmployeeInput(
        id=1,
        first_name="High",
        last_name="Earner",
        gross_salary=Money("50000.00", "NOK"),  # 600k/year > 124k (1G)
        tax_percentage=Decimal("0.40"),
        age=38,
        work_region="oslo",
        pension_scheme="NO_OTP_2_PERCENT",
    )
    calc = NorwayPayrollCalculator()
    result = calc.calculate(employee, date(2026, 4, 1), date(2026, 4, 30))
    otp_line = next(l for l in result.lines if l.code == "OTP")
    # Annual gross 600,000, 1G=124,028, pensionable = 600,000 - 124,028 = 475,972
    # Monthly OTP = 475,972 / 12 * 0.02 ≈ 793.29
    assert otp_line.amount.amount > Decimal("700")
    assert otp_line.amount.amount < Decimal("900")


def test_otp_zero_when_no_pension_scheme():
    employee = EmployeeInput(
        id=1,
        first_name="NoPension",
        last_name="Person",
        gross_salary=Money("40000", "NOK"),
        tax_percentage=Decimal("0.30"),
        age=30,
        work_region="oslo",
        pension_scheme="NONE",
    )
    calc = NorwayPayrollCalculator()
    result = calc.calculate(employee, date(2026, 4, 1), date(2026, 4, 30))
    otp_lines = [l for l in result.lines if l.code == "OTP"]
    assert otp_lines == []


# ── Validation ────────────────────────────────────────────────────────────


def test_currency_mismatch_rejected():
    employee = EmployeeInput(
        id=1,
        first_name="Wrong",
        last_name="Currency",
        gross_salary=Money("1000", "EUR"),  # WRONG currency for Norway
        tax_percentage=Decimal("0.30"),
        age=30,
    )
    calc = NorwayPayrollCalculator()
    with pytest.raises(PayrollCalculationError) as exc:
        calc.calculate(employee, date(2026, 4, 1), date(2026, 4, 30))
    assert "EUR" in str(exc.value)
    assert "NOK" in str(exc.value)


def test_invalid_tax_percentage_rejected():
    employee = EmployeeInput(
        id=1,
        first_name="Too",
        last_name="High",
        gross_salary=Money("45000", "NOK"),
        tax_percentage=Decimal("1.5"),  # >100%
        age=30,
        work_region="oslo",
    )
    calc = NorwayPayrollCalculator()
    with pytest.raises(PayrollCalculationError):
        calc.calculate(employee, date(2026, 4, 1), date(2026, 4, 30))


# ── Full run ──────────────────────────────────────────────────────────────


def test_run_payroll_aggregates_multiple_employees(oslo_employee, northern_employee):
    input = PayrollInput(
        country="NO",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        employees=[oslo_employee, northern_employee],
    )
    result = run_payroll(input)

    assert len(result.payslips) == 2
    assert result.currency == "NOK"
    assert result.total_gross == Money("85000.00", "NOK")  # 45000 + 40000
    # Net = 29250 + (40000 - 12000) = 29250 + 28000 = 57250
    assert result.total_net == Money("57250.00", "NOK")


# ── A-melding XML generation ──────────────────────────────────────────────


def test_generate_a_melding_returns_valid_xml(oslo_employee):
    calc = NorwayPayrollCalculator()
    result = calc.calculate(oslo_employee, date(2026, 4, 1), date(2026, 4, 30))
    xml = NorwayPayrollCalculator.generate_a_melding(
        organisation_number="987654321",
        period_year=2026,
        period_month=4,
        payslips=[result],
    )
    assert "987654321" in xml
    assert "Sarah Mokoena" in xml
    assert "<aar>2026</aar>" in xml
    assert "<maaned>04</maaned>" in xml
    assert "forskuddstrekk" in xml.lower()
    assert "arbeidsgiveravgift" in xml.lower()
