"""
Finland payroll calculator tests.

Includes coverage of the Tulorekisteri real-time JSON payload generator —
the critical 5-day reporting requirement that's unique to Finland in
the Nordics.
"""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest

from app.services.money import Money
from app.services.payroll import EmployeeInput, PayrollInput, run_payroll
from app.services.payroll.finland import FinlandPayrollCalculator


@pytest.fixture
def helsinki_employee():
    """Standard working-age employee in Helsinki."""
    return EmployeeInput(
        id=1,
        first_name="Matti",
        last_name="Virtanen",
        gross_salary=Money("4500.00", "EUR"),
        tax_percentage=Decimal("0.28"),
        age=40,
        pension_scheme="FI_TYEL_STANDARD",
    )


@pytest.fixture
def senior_employee():
    """Employee in the 53-62 age band — gets a higher TyEL employee rate."""
    return EmployeeInput(
        id=2,
        first_name="Liisa",
        last_name="Korhonen",
        gross_salary=Money("5000.00", "EUR"),
        tax_percentage=Decimal("0.32"),
        age=58,
        pension_scheme="FI_TYEL_STANDARD",
    )


# ── Deductions ────────────────────────────────────────────────────────────


def test_ennakonpidatys_withheld(helsinki_employee):
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    tax = next(l for l in result.lines if l.code == "ENNAKONPIDATYS")
    # 4500 * 0.28 = 1260
    assert tax.amount == Money("1260.00", "EUR")


def test_tyel_employee_rate_young(helsinki_employee):
    """Employees under 53 pay 7.15%."""
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    tyel = next(l for l in result.lines if l.code == "TYEL_EMPLOYEE")
    # 4500 * 0.0715 = 321.75
    assert tyel.amount == Money("321.75", "EUR")


def test_tyel_employee_rate_53_to_62(senior_employee):
    """Employees aged 53-62 pay 8.70%."""
    calc = FinlandPayrollCalculator()
    result = calc.calculate(senior_employee, date(2026, 4, 1), date(2026, 4, 30))
    tyel = next(l for l in result.lines if l.code == "TYEL_EMPLOYEE")
    # 5000 * 0.0870 = 435.00
    assert tyel.amount == Money("435.00", "EUR")


def test_unemployment_insurance_employee(helsinki_employee):
    """Employee share is 1.5%."""
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    unemp = next(l for l in result.lines if l.code == "TVR_EMPLOYEE")
    # 4500 * 0.015 = 67.50
    assert unemp.amount == Money("67.50", "EUR")


# ── Employer contributions ────────────────────────────────────────────────


def test_tyel_employer_contribution(helsinki_employee):
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    tyel = next(l for l in result.lines if l.code == "TYEL_EMPLOYER")
    # 4500 * 0.1742 = 783.90
    assert tyel.amount == Money("783.90", "EUR")


def test_unemployment_insurance_employer(helsinki_employee):
    """Low rate 0.52% for small employers."""
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    unemp = next(l for l in result.lines if l.code == "TVR_EMPLOYER")
    # 4500 * 0.0052 = 23.40
    assert unemp.amount == Money("23.40", "EUR")


def test_accident_and_group_life_insurance(helsinki_employee):
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    acc = next(l for l in result.lines if l.code == "ACCIDENT_INS")
    life = next(l for l in result.lines if l.code == "GROUP_LIFE")
    # 4500 * 0.007 = 31.50, 4500 * 0.0006 = 2.70
    assert acc.amount == Money("31.50", "EUR")
    assert life.amount == Money("2.70", "EUR")


# ── Net pay ───────────────────────────────────────────────────────────────


def test_net_pay_subtracts_all_employee_deductions(helsinki_employee):
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    # Gross 4500
    # Deductions: ennakonpidätys 1260 + TyEL 321.75 + unemp 67.50 = 1649.25
    # Net = 4500 - 1649.25 = 2850.75
    assert result.net_pay == Money("2850.75", "EUR")


# ── Tulorekisteri warning ─────────────────────────────────────────────────


def test_tulorekisteri_5_day_warning_is_present(helsinki_employee):
    """Every Finnish payslip must surface the 5-day deadline as a warning."""
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    warnings_text = " ".join(result.warnings)
    assert "Tulorekisteri" in warnings_text
    assert "5 calendar days" in warnings_text


# ── Tulorekisteri JSON payload ────────────────────────────────────────────


def test_generate_tulorekisteri_payload_is_valid_json(helsinki_employee):
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    payload_str = FinlandPayrollCalculator.generate_tulorekisteri_payload(
        employer_business_id="07375462",
        payment_date="2026-04-30",
        payslips=[result],
    )
    payload = json.loads(payload_str)

    assert payload["payer"]["identifier"]["id"] == "07375462"
    assert payload["paymentDate"] == "2026-04-30"
    assert len(payload["incomeEarnerReports"]) == 1

    report = payload["incomeEarnerReports"][0]
    assert report["incomeEarner"]["name"] == "Matti Virtanen"
    assert report["payPeriod"]["start"] == "2026-04-01"
    assert report["payPeriod"]["end"] == "2026-04-30"


def test_tulorekisteri_reports_tax_withheld(helsinki_employee):
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    payload_str = FinlandPayrollCalculator.generate_tulorekisteri_payload(
        employer_business_id="07375462",
        payment_date="2026-04-30",
        payslips=[result],
    )
    payload = json.loads(payload_str)
    tax_items = payload["incomeEarnerReports"][0]["taxItems"]
    assert any(
        item["type"] == "withholdingTax" and Decimal(item["amount"]) == Decimal("1260.00")
        for item in tax_items
    )


def test_tulorekisteri_reports_insurance_contributions(helsinki_employee):
    calc = FinlandPayrollCalculator()
    result = calc.calculate(helsinki_employee, date(2026, 4, 1), date(2026, 4, 30))
    payload_str = FinlandPayrollCalculator.generate_tulorekisteri_payload(
        employer_business_id="07375462",
        payment_date="2026-04-30",
        payslips=[result],
    )
    payload = json.loads(payload_str)
    insurance = payload["incomeEarnerReports"][0]["insuranceItems"]
    types = {i["type"] for i in insurance}
    assert "employeePensionInsurance" in types
    assert "employeeUnemploymentInsurance" in types


# ── Full run ──────────────────────────────────────────────────────────────


def test_run_payroll_finland(helsinki_employee, senior_employee):
    input = PayrollInput(
        country="FI",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        employees=[helsinki_employee, senior_employee],
    )
    result = run_payroll(input)
    assert len(result.payslips) == 2
    assert result.currency == "EUR"
    assert result.total_gross == Money("9500.00", "EUR")
