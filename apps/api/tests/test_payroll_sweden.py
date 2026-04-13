"""Sweden payroll calculator tests."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.services.money import Money
from app.services.payroll import EmployeeInput, PayrollInput, run_payroll
from app.services.payroll.sweden import SwedenPayrollCalculator


@pytest.fixture
def stockholm_employee():
    return EmployeeInput(
        id=1,
        first_name="Erik",
        last_name="Johansson",
        gross_salary=Money("40000.00", "SEK"),
        tax_percentage=Decimal("0.30"),
        age=35,
        work_region="stockholm",
        pension_scheme="SE_ITP1",
    )


@pytest.fixture
def young_employee():
    """Under-23 — gets the reduced arbetsgivaravgifter rate."""
    return EmployeeInput(
        id=2,
        first_name="Linnea",
        last_name="Svensson",
        gross_salary=Money("25000.00", "SEK"),
        tax_percentage=Decimal("0.25"),
        age=21,
        work_region="gothenburg",
        pension_scheme="SE_NONE",
    )


@pytest.fixture
def senior_employee():
    """Over-65 — also gets the reduced rate."""
    return EmployeeInput(
        id=3,
        first_name="Ingrid",
        last_name="Bergman",
        gross_salary=Money("35000.00", "SEK"),
        tax_percentage=Decimal("0.35"),
        age=68,
        work_region="malmo",
        pension_scheme="SE_NONE",
    )


# ── Deductions ────────────────────────────────────────────────────────────


def test_preliminar_skatt_withheld(stockholm_employee):
    calc = SwedenPayrollCalculator()
    result = calc.calculate(stockholm_employee, date(2026, 4, 1), date(2026, 4, 30))
    tax = next(l for l in result.lines if l.code == "PRELIMINAR_SKATT")
    # 40000 * 0.30 = 12000
    assert tax.amount == Money("12000.00", "SEK")


def test_net_pay_excludes_employer_contributions(stockholm_employee):
    """Employer contributions must NOT come out of employee net pay."""
    calc = SwedenPayrollCalculator()
    result = calc.calculate(stockholm_employee, date(2026, 4, 1), date(2026, 4, 30))
    # Net = 40000 - 12000 = 28000
    assert result.net_pay == Money("28000.00", "SEK")


# ── Employer contributions ────────────────────────────────────────────────


def test_arbetsgivaravgifter_standard_rate(stockholm_employee):
    """Ages 23-65 get 31.42%."""
    calc = SwedenPayrollCalculator()
    result = calc.calculate(stockholm_employee, date(2026, 4, 1), date(2026, 4, 30))
    arbgav = next(l for l in result.lines if l.code == "ARBGAV")
    # 40000 * 0.3142 = 12568
    assert arbgav.amount == Money("12568.00", "SEK")


def test_arbetsgivaravgifter_reduced_for_under_23(young_employee):
    calc = SwedenPayrollCalculator()
    result = calc.calculate(young_employee, date(2026, 4, 1), date(2026, 4, 30))
    arbgav = next(l for l in result.lines if l.code == "ARBGAV")
    # 25000 * 0.1021 = 2552.50
    assert arbgav.amount == Money("2552.50", "SEK")


def test_arbetsgivaravgifter_reduced_for_over_65(senior_employee):
    calc = SwedenPayrollCalculator()
    result = calc.calculate(senior_employee, date(2026, 4, 1), date(2026, 4, 30))
    arbgav = next(l for l in result.lines if l.code == "ARBGAV")
    # 35000 * 0.1021 = 3573.50
    assert arbgav.amount == Money("3573.50", "SEK")


def test_itp1_pension_below_threshold(stockholm_employee):
    """ITP1 is 4.5% for salaries below 7.5 IBB monthly (49,562.50 SEK)."""
    calc = SwedenPayrollCalculator()
    result = calc.calculate(stockholm_employee, date(2026, 4, 1), date(2026, 4, 30))
    itp = next(l for l in result.lines if l.code == "ITP1")
    # 40000 * 0.045 = 1800
    assert itp.amount == Money("1800.00", "SEK")


def test_itp1_pension_crosses_threshold():
    """ITP1 jumps to 30% on the portion above 49,562.50 SEK monthly."""
    high = EmployeeInput(
        id=1,
        first_name="High",
        last_name="Earner",
        gross_salary=Money("60000", "SEK"),
        tax_percentage=Decimal("0.45"),
        age=40,
        pension_scheme="SE_ITP1",
    )
    calc = SwedenPayrollCalculator()
    result = calc.calculate(high, date(2026, 4, 1), date(2026, 4, 30))
    itp = next(l for l in result.lines if l.code == "ITP1")
    # Below threshold: 49562.50 * 0.045 = 2230.3125
    # Above threshold: (60000 - 49562.50) * 0.30 = 10437.50 * 0.30 = 3131.25
    # Total: 2230.3125 + 3131.25 = 5361.5625 → 5361.56
    assert itp.amount == Money("5361.56", "SEK")


def test_no_itp_when_scheme_is_none():
    employee = EmployeeInput(
        id=1,
        first_name="No",
        last_name="Pension",
        gross_salary=Money("30000", "SEK"),
        tax_percentage=Decimal("0.28"),
        age=30,
        pension_scheme="SE_NONE",
    )
    calc = SwedenPayrollCalculator()
    result = calc.calculate(employee, date(2026, 4, 1), date(2026, 4, 30))
    itp_lines = [l for l in result.lines if l.code == "ITP1"]
    assert itp_lines == []


def test_semesterlon_12_percent(stockholm_employee):
    calc = SwedenPayrollCalculator()
    result = calc.calculate(stockholm_employee, date(2026, 4, 1), date(2026, 4, 30))
    sem = next(l for l in result.lines if l.code == "SEMESTERLON")
    # 40000 * 0.12 = 4800
    assert sem.amount == Money("4800.00", "SEK")


# ── Full run ──────────────────────────────────────────────────────────────


def test_run_payroll_sweden(stockholm_employee, young_employee):
    input = PayrollInput(
        country="SE",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        employees=[stockholm_employee, young_employee],
    )
    result = run_payroll(input)
    assert len(result.payslips) == 2
    assert result.currency == "SEK"
    assert result.total_gross == Money("65000.00", "SEK")


# ── AGD XML generation ───────────────────────────────────────────────────


def test_generate_agd_returns_valid_xml(stockholm_employee):
    calc = SwedenPayrollCalculator()
    result = calc.calculate(stockholm_employee, date(2026, 4, 1), date(2026, 4, 30))
    xml = SwedenPayrollCalculator.generate_agd(
        organisation_number="556123456701",
        period_year=2026,
        period_month=4,
        payslips=[result],
    )
    assert "556123456701" in xml
    assert "202604" in xml  # period
    assert "Erik Johansson" in xml
    assert "SamladLoneSumma" in xml
    assert "Arbetsgivaravgifter" in xml
