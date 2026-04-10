"""Tests for Norway payroll engine — Sprint 15.

Tests cover:
- Auth protection (401 without token)
- Tax calculation accuracy (trinnskatt + trygdeavgift)
- OTP pension calculation
- Holiday pay accrual (10.2%)
- A-melding XML generation
"""

from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.routers.payroll_no import router as payroll_no_router
from app.services.payroll_no import (
    calculate_payslip,
    calculate_trinnskatt,
    calculate_trygdeavgift,
    calculate_otp,
    calculate_holiday_pay,
    calculate_employer_ni,
    generate_a_melding_xml,
)

# Register the Norway payroll router on the app for testing
# (main.py is not modified per project conventions)
if payroll_no_router not in [r for r in app.routes]:
    app.include_router(payroll_no_router)

client = TestClient(app)


# ──────────────────────────────────────────────
# Auth protection tests
# ──────────────────────────────────────────────

def test_calculate_requires_auth():
    response = client.post("/payroll-no/calculate", json={
        "gross_salary": "500000",
    })
    assert response.status_code in (401, 403)


def test_tax_tables_requires_auth():
    response = client.get("/payroll-no/tax-tables")
    assert response.status_code in (401, 403)


def test_a_melding_requires_auth():
    response = client.post("/payroll-no/a-melding/generate", json={
        "org_number": "123456789",
        "period": "2026-03",
    })
    assert response.status_code in (401, 403)


def test_settings_requires_auth():
    response = client.get("/payroll-no/settings/1")
    assert response.status_code in (401, 403)


# ──────────────────────────────────────────────
# Trinnskatt (bracket tax) calculation tests
# ──────────────────────────────────────────────

def test_trinnskatt_below_threshold():
    """Income below NOK 208,050 should have zero trinnskatt."""
    assert calculate_trinnskatt(Decimal("200000")) == Decimal("0.00")


def test_trinnskatt_500k():
    """NOK 500,000 annual — hits steps 1 and 2."""
    # Step 1: (292850 - 208050) * 1.7% = 84800 * 0.017 = 1441.60
    # Step 2: (500000 - 292850) * 4.0% = 207150 * 0.04 = 8286.00
    # Total = 9727.60
    result = calculate_trinnskatt(Decimal("500000"))
    assert result == Decimal("9727.60")


def test_trinnskatt_800k():
    """NOK 800,000 annual — hits steps 1, 2, and 3."""
    # Step 1: (292850 - 208050) * 0.017 = 84800 * 0.017 = 1441.60
    # Step 2: (670000 - 292850) * 0.040 = 377150 * 0.04 = 15086.00
    # Step 3: (800000 - 670000) * 0.136 = 130000 * 0.136 = 17680.00
    # Total = 34207.60
    result = calculate_trinnskatt(Decimal("800000"))
    assert result == Decimal("34207.60")


def test_trinnskatt_1_5m():
    """NOK 1,500,000 annual — hits all 5 steps."""
    # Step 1: 84800 * 0.017 = 1441.60
    # Step 2: 377150 * 0.040 = 15086.00
    # Step 3: 267900 * 0.136 = 36434.40
    # Step 4: 412100 * 0.166 = 68408.60
    # Step 5: 150000 * 0.176 = 26400.00
    # Total = 147770.60
    result = calculate_trinnskatt(Decimal("1500000"))
    assert result == Decimal("147770.60")


# ──────────────────────────────────────────────
# Trygdeavgift (social security) tests
# ──────────────────────────────────────────────

def test_trygdeavgift_500k():
    """7.9% of 500,000 = 39,500."""
    result = calculate_trygdeavgift(Decimal("500000"))
    assert result == Decimal("39500.00")


def test_trygdeavgift_800k():
    """7.9% of 800,000 = 63,200."""
    result = calculate_trygdeavgift(Decimal("800000"))
    assert result == Decimal("63200.00")


# ──────────────────────────────────────────────
# Full payslip calculation tests
# ──────────────────────────────────────────────

def test_payslip_500k():
    """Full payslip for NOK 500,000 annual gross."""
    result = calculate_payslip(Decimal("500000"))

    assert result["gross_salary"] == Decimal("500000")
    # Trinnskatt: 9727.60
    assert result["trinnskatt"] == Decimal("9727.60")
    # Trygdeavgift: 39500.00
    assert result["trygdeavgift"] == Decimal("39500.00")
    # Income tax total: 49227.60
    assert result["income_tax"] == Decimal("49227.60")
    # OTP pension: 2% of 500000 = 10000
    assert result["otp_pension"] == Decimal("10000.00")
    # Holiday pay: 10.2% of 500000 = 51000
    assert result["holiday_pay_accrual"] == Decimal("51000.00")
    # Employer NI: 14.1% of 500000 = 70500
    assert result["employer_ni"] == Decimal("70500.00")
    # Net: 500000 - 49227.60 - 10000 = 440772.40
    assert result["net_salary"] == Decimal("440772.40")


def test_payslip_800k():
    """Full payslip for NOK 800,000 annual gross."""
    result = calculate_payslip(Decimal("800000"))

    assert result["gross_salary"] == Decimal("800000")
    assert result["trinnskatt"] == Decimal("34207.60")
    assert result["trygdeavgift"] == Decimal("63200.00")
    assert result["income_tax"] == Decimal("97407.60")
    assert result["otp_pension"] == Decimal("16000.00")
    assert result["holiday_pay_accrual"] == Decimal("81600.00")
    assert result["employer_ni"] == Decimal("112800.00")
    # Net: 800000 - 97407.60 - 16000.00 = 686592.40
    assert result["net_salary"] == Decimal("686592.40")


# ──────────────────────────────────────────────
# OTP pension calculation tests
# ──────────────────────────────────────────────

def test_otp_default_2_percent():
    """Default OTP is 2% of gross."""
    result = calculate_otp(Decimal("600000"))
    assert result == Decimal("12000.00")


def test_otp_custom_5_percent():
    """Custom OTP at 5%."""
    result = calculate_otp(Decimal("600000"), Decimal("0.05"))
    assert result == Decimal("30000.00")


def test_payslip_custom_pension():
    """Payslip with custom 5% pension percentage."""
    result = calculate_payslip(Decimal("500000"), pension_pct=Decimal("5.0"))
    # OTP: 5% of 500000 = 25000
    assert result["otp_pension"] == Decimal("25000.00")


# ──────────────────────────────────────────────
# Holiday pay tests
# ──────────────────────────────────────────────

def test_holiday_pay_accrual():
    """Holiday pay is 10.2% of gross."""
    result = calculate_holiday_pay(Decimal("500000"))
    assert result == Decimal("51000.00")


def test_holiday_pay_high_salary():
    """Holiday pay for NOK 1,000,000."""
    result = calculate_holiday_pay(Decimal("1000000"))
    assert result == Decimal("102000.00")


# ──────────────────────────────────────────────
# Employer NI tests
# ──────────────────────────────────────────────

def test_employer_ni():
    """Employer NI is 14.1% of gross."""
    result = calculate_employer_ni(Decimal("500000"))
    assert result == Decimal("70500.00")


# ──────────────────────────────────────────────
# A-melding XML tests
# ──────────────────────────────────────────────

def test_a_melding_xml_generation():
    """Generated A-melding XML contains correct org and period."""
    xml = generate_a_melding_xml(
        org_number="987654321",
        period="2026-03",
        employee_count=5,
        total_gross=Decimal("2500000"),
    )
    assert "987654321" in xml
    assert "2026-03" in xml
    assert "<antallInntektsmottakere>5</antallInntektsmottakere>" in xml
    assert "2500000" in xml
    assert '<?xml version="1.0"' in xml
