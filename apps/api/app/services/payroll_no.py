"""Norwegian payroll calculation engine.

Implements:
- Trinnskatt (bracket income tax)
- Trygdeavgift (social security contribution)
- OTP pension (mandatory occupational pension)
- Holiday pay accrual (feriepenger)
- Employer NI (arbeidsgiveravgift)
- A-melding XML generation (mock/template)
"""

from decimal import Decimal, ROUND_HALF_UP

# ---------- 2026 Tax Constants ----------

TRINNSKATT_BRACKETS = [
    # (lower_bound, upper_bound_or_None, rate)
    (Decimal("208050"), Decimal("292850"), Decimal("0.017")),   # Step 1
    (Decimal("292850"), Decimal("670000"), Decimal("0.040")),   # Step 2
    (Decimal("670000"), Decimal("937900"), Decimal("0.136")),   # Step 3
    (Decimal("937900"), Decimal("1350000"), Decimal("0.166")),  # Step 4
    (Decimal("1350000"), None, Decimal("0.176")),               # Step 5
]

TRYGDEAVGIFT_RATE = Decimal("0.079")       # 7.9% social security
HOLIDAY_PAY_RATE = Decimal("0.102")        # 10.2% holiday pay accrual
EMPLOYER_NI_RATE = Decimal("0.141")        # 14.1% employer national insurance
DEFAULT_OTP_RATE = Decimal("0.02")         # 2% default OTP pension


def _quantize(value: Decimal) -> Decimal:
    """Round to 2 decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_trinnskatt(annual_gross: Decimal) -> Decimal:
    """Calculate trinnskatt (bracket tax) on annual gross income."""
    total = Decimal("0")
    for lower, upper, rate in TRINNSKATT_BRACKETS:
        if annual_gross <= lower:
            break
        if upper is None:
            taxable = annual_gross - lower
        else:
            taxable = min(annual_gross, upper) - lower
        total += taxable * rate
    return _quantize(total)


def calculate_trygdeavgift(annual_gross: Decimal) -> Decimal:
    """Calculate trygdeavgift (social security) — flat 7.9% of gross."""
    return _quantize(annual_gross * TRYGDEAVGIFT_RATE)


def calculate_otp(annual_gross: Decimal, pension_pct: Decimal = DEFAULT_OTP_RATE) -> Decimal:
    """Calculate OTP pension contribution."""
    return _quantize(annual_gross * pension_pct)


def calculate_holiday_pay(annual_gross: Decimal) -> Decimal:
    """Calculate holiday pay accrual — 10.2% of gross."""
    return _quantize(annual_gross * HOLIDAY_PAY_RATE)


def calculate_employer_ni(annual_gross: Decimal) -> Decimal:
    """Calculate employer national insurance — 14.1% of gross."""
    return _quantize(annual_gross * EMPLOYER_NI_RATE)


def calculate_payslip(
    gross_salary: Decimal,
    pension_pct: Decimal = Decimal("2.0"),
) -> dict:
    """
    Calculate a complete Norwegian payslip.

    Args:
        gross_salary: Annual gross salary in NOK.
        pension_pct: OTP pension percentage (e.g. 2.0 means 2%).

    Returns:
        Dictionary with full payslip breakdown.
    """
    annual = Decimal(str(gross_salary))
    otp_rate = Decimal(str(pension_pct)) / Decimal("100")

    trinnskatt = calculate_trinnskatt(annual)
    trygdeavgift = calculate_trygdeavgift(annual)
    income_tax = trinnskatt + trygdeavgift
    otp_pension = calculate_otp(annual, otp_rate)
    holiday_pay = calculate_holiday_pay(annual)
    employer_ni = calculate_employer_ni(annual)

    # Net = gross minus employee-side deductions (tax + pension)
    net_salary = _quantize(annual - income_tax - otp_pension)

    return {
        "gross_salary": annual,
        "otp_pension": otp_pension,
        "trinnskatt": trinnskatt,
        "trygdeavgift": trygdeavgift,
        "income_tax": income_tax,
        "holiday_pay_accrual": holiday_pay,
        "employer_ni": employer_ni,
        "net_salary": net_salary,
    }


def generate_a_melding_xml(
    org_number: str,
    period: str,
    employee_count: int = 1,
    total_gross: Decimal = Decimal("0"),
) -> str:
    """
    Generate a mock A-melding XML document.

    In production this would conform to Altinn's A-melding schema.
    This is a template/mock for development purposes.
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<melding xmlns="urn:no:skatteetaten:datasamarbeid:amelding:v1">
  <leveranse>
    <kalendermaaned>{period}</kalendermaaned>
    <oppgavegiver>
      <organisasjonsnummer>{org_number}</organisasjonsnummer>
    </oppgavegiver>
    <opplysningspliktig>
      <organisasjonsnummer>{org_number}</organisasjonsnummer>
    </opplysningspliktig>
    <virksomhet>
      <organisasjonsnummer>{org_number}</organisasjonsnummer>
      <antallInntektsmottakere>{employee_count}</antallInntektsmottakere>
      <sumLoenn>{total_gross}</sumLoenn>
    </virksomhet>
  </leveranse>
</melding>"""
    return xml.strip()
