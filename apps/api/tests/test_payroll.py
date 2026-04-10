"""Tests for Sprint 14 – South African Payroll Engine.

Covers:
  - 401 auth enforcement on every payroll endpoint
  - Direct SA PAYE calculation accuracy (R20k and R50k monthly)
  - UIF and SDL calculations
"""

from decimal import Decimal
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.payroll import router as payroll_router
from app.services.payroll_sa import (
    calculate_payslip,
    calculate_monthly_paye,
    calculate_uif_employee,
    calculate_uif_employer,
    calculate_sdl,
    calculate_eti,
    generate_emp201,
)

# Build a lightweight app that includes the payroll router so we can test
# auth enforcement without modifying app/main.py.
_test_app = FastAPI()
_test_app.include_router(payroll_router)
client = TestClient(_test_app)


# ── Auth enforcement (401 without token) ──────────────────────────────


def test_create_payroll_run_requires_auth():
    response = client.post("/payroll/runs", json={
        "client_id": 1,
        "period_start": "2024-01-01T00:00:00Z",
        "period_end": "2024-01-31T23:59:59Z",
    })
    assert response.status_code in (401, 403)


def test_list_payroll_runs_requires_auth():
    response = client.get("/payroll/runs")
    assert response.status_code in (401, 403)


def test_get_payroll_run_requires_auth():
    response = client.get("/payroll/runs/1")
    assert response.status_code in (401, 403)


def test_calculate_payroll_run_requires_auth():
    response = client.post("/payroll/runs/1/calculate")
    assert response.status_code in (401, 403)


def test_approve_payroll_run_requires_auth():
    response = client.post("/payroll/runs/1/approve")
    assert response.status_code in (401, 403)


def test_list_employees_requires_auth():
    response = client.get("/payroll/employees")
    assert response.status_code in (401, 403)


def test_create_employee_requires_auth():
    response = client.post("/payroll/employees", json={
        "client_id": 1,
        "full_name": "Test Employee",
        "monthly_salary": 20000,
    })
    assert response.status_code in (401, 403)


def test_emp201_requires_auth():
    response = client.get("/payroll/runs/1/emp201")
    assert response.status_code in (401, 403)


# ── SA PAYE calculation tests ────────────────────────────────────────


def test_paye_20k_monthly():
    """R20,000/month gross → expected monthly PAYE R2,183.08.

    Annual = R240,000
    Bracket 2: base 42,678 + (240,000 - 237,100) * 26% = 42,678 + 754 = 43,432
    After primary rebate: 43,432 - 17,235 = 26,197
    Monthly: 26,197 / 12 = 2,183.08
    """
    paye = calculate_monthly_paye(Decimal("20000"))
    assert paye == Decimal("2183.08")


def test_paye_50k_monthly():
    """R50,000/month gross → expected monthly PAYE R11,302.67.

    Annual = R600,000
    Bracket 4: base 121,475 + (600,000 - 512,800) * 36% = 121,475 + 31,392 = 152,867
    After primary rebate: 152,867 - 17,235 = 135,632
    Monthly: 135,632 / 12 = 11,302.67
    """
    paye = calculate_monthly_paye(Decimal("50000"))
    assert paye == Decimal("11302.67")


def test_paye_zero_income():
    """Zero income should produce zero PAYE."""
    paye = calculate_monthly_paye(Decimal("0"))
    assert paye == Decimal("0")


def test_paye_low_income_below_rebate():
    """Very low income where tax is less than rebate should return 0."""
    # R5,000/month = R60,000/year → bracket 1: 60,000 * 18% = 10,800
    # After rebate: 10,800 - 17,235 = -6,435 → clamped to 0
    paye = calculate_monthly_paye(Decimal("5000"))
    assert paye == Decimal("0")


# ── UIF tests ─────────────────────────────────────────────────────────


def test_uif_employee_standard():
    """UIF employee contribution is 1% of gross, capped at R177.12."""
    uif = calculate_uif_employee(Decimal("20000"))
    # 1% of 20,000 = 200, but capped at 177.12
    assert uif == Decimal("177.12")


def test_uif_employee_below_cap():
    """UIF for salary below cap threshold."""
    uif = calculate_uif_employee(Decimal("10000"))
    # 1% of 10,000 = 100, below cap
    assert uif == Decimal("100.00")


def test_uif_employer_matches_employee():
    """Employer UIF should mirror employee UIF."""
    emp = calculate_uif_employee(Decimal("20000"))
    employer = calculate_uif_employer(Decimal("20000"))
    assert emp == employer


# ── SDL tests ─────────────────────────────────────────────────────────


def test_sdl_calculation():
    """SDL is 1% of gross salary."""
    sdl = calculate_sdl(Decimal("20000"))
    assert sdl == Decimal("200.00")


def test_sdl_50k():
    """SDL for R50,000."""
    sdl = calculate_sdl(Decimal("50000"))
    assert sdl == Decimal("500.00")


# ── ETI tests ─────────────────────────────────────────────────────────


def test_eti_qualifying():
    """ETI for qualifying employee (R2,000-R6,500, first 12 months)."""
    eti = calculate_eti(Decimal("5000"), months_employed=1)
    assert eti == Decimal("1000")


def test_eti_not_qualifying_high_salary():
    """ETI should be 0 for salary above R6,500."""
    eti = calculate_eti(Decimal("20000"), months_employed=1)
    assert eti == Decimal("0")


# ── Full payslip test ─────────────────────────────────────────────────


def test_calculate_payslip_20k():
    """Full payslip breakdown for R20,000/month."""
    result = calculate_payslip(Decimal("20000"))
    assert result["gross_salary"] == Decimal("20000.00")
    assert result["paye_tax"] == Decimal("2183.08")
    assert result["uif_employee"] == Decimal("177.12")
    assert result["sdl"] == Decimal("200.00")
    assert result["net_salary"] == Decimal("17639.80")


def test_calculate_payslip_50k():
    """Full payslip breakdown for R50,000/month."""
    result = calculate_payslip(Decimal("50000"))
    assert result["gross_salary"] == Decimal("50000.00")
    assert result["paye_tax"] == Decimal("11302.67")
    assert result["uif_employee"] == Decimal("177.12")
    assert result["sdl"] == Decimal("500.00")
    assert result["net_salary"] == Decimal("38520.21")


# ── EMP201 summary test ──────────────────────────────────────────────


def test_emp201_summary():
    """EMP201 should aggregate payslip data correctly."""
    slip1 = calculate_payslip(Decimal("20000"))
    slip2 = calculate_payslip(Decimal("30000"))
    summary = generate_emp201([slip1, slip2])

    assert summary["total_employees"] == 2
    assert summary["total_gross"] == slip1["gross_salary"] + slip2["gross_salary"]
    assert summary["total_paye"] == slip1["paye_tax"] + slip2["paye_tax"]
    # total_uif = employee + employer for both slips
    expected_uif = (
        slip1["uif_employee"] + slip1["uif_employer"]
        + slip2["uif_employee"] + slip2["uif_employer"]
    )
    assert summary["total_uif"] == expected_uif
    assert summary["total_sdl"] == slip1["sdl"] + slip2["sdl"]
