"""South African payroll tax engine (2024 tax year)."""

from decimal import Decimal, ROUND_HALF_UP

# 2024 PAYE tax brackets (annual income thresholds)
PAYE_BRACKETS = [
    (Decimal("237100"), Decimal("0.18"), Decimal("0")),
    (Decimal("370500"), Decimal("0.26"), Decimal("42678")),
    (Decimal("512800"), Decimal("0.31"), Decimal("77362")),
    (Decimal("673000"), Decimal("0.36"), Decimal("121475")),
    (Decimal("857900"), Decimal("0.39"), Decimal("179147")),
    (Decimal("1817000"), Decimal("0.41"), Decimal("251258")),
    (Decimal("999999999"), Decimal("0.45"), Decimal("644489")),
]

# Primary rebate (annual)
PRIMARY_REBATE = Decimal("17235")

# UIF rates
UIF_EMPLOYEE_RATE = Decimal("0.01")  # 1%
UIF_EMPLOYER_RATE = Decimal("0.01")  # 1%
UIF_MONTHLY_CAP = Decimal("177.12")  # max monthly UIF contribution

# SDL rate
SDL_RATE = Decimal("0.01")  # 1% on total payroll

# ETI monthly amounts (simplified: first 12 months for qualifying employees)
ETI_MAX_MONTHLY = Decimal("1000")


def _round2(value: Decimal) -> Decimal:
    """Round to 2 decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_annual_paye(annual_income: Decimal) -> Decimal:
    """Calculate annual PAYE tax before rebate using 2024 brackets."""
    if annual_income <= 0:
        return Decimal("0")

    prev_threshold = Decimal("0")
    for threshold, rate, base_tax in PAYE_BRACKETS:
        if annual_income <= threshold:
            taxable_in_bracket = annual_income - prev_threshold
            return base_tax + taxable_in_bracket * rate
        prev_threshold = threshold

    # Should not reach here given the last bracket is very high
    return Decimal("0")


def calculate_monthly_paye(monthly_gross: Decimal) -> Decimal:
    """Calculate monthly PAYE from monthly gross salary."""
    annual_income = monthly_gross * 12
    annual_tax = calculate_annual_paye(annual_income)
    annual_tax_after_rebate = max(annual_tax - PRIMARY_REBATE, Decimal("0"))
    monthly_tax = _round2(annual_tax_after_rebate / 12)
    return monthly_tax


def calculate_uif_employee(monthly_gross: Decimal) -> Decimal:
    """Calculate employee UIF contribution (1%, capped)."""
    uif = _round2(monthly_gross * UIF_EMPLOYEE_RATE)
    return min(uif, UIF_MONTHLY_CAP)


def calculate_uif_employer(monthly_gross: Decimal) -> Decimal:
    """Calculate employer UIF contribution (1%, capped)."""
    uif = _round2(monthly_gross * UIF_EMPLOYER_RATE)
    return min(uif, UIF_MONTHLY_CAP)


def calculate_sdl(monthly_gross: Decimal) -> Decimal:
    """Calculate Skills Development Levy (1% of gross payroll, employer cost)."""
    return _round2(monthly_gross * SDL_RATE)


def calculate_eti(monthly_gross: Decimal, months_employed: int = 1) -> Decimal:
    """Calculate Employment Tax Incentive (simplified).

    ETI applies to qualifying employees (18-29, earning R2,000–R6,500/month).
    Simplified: returns ETI_MAX_MONTHLY for qualifying employees in first 12 months.
    """
    if months_employed > 24:
        return Decimal("0")
    if monthly_gross < Decimal("2000") or monthly_gross > Decimal("6500"):
        return Decimal("0")
    if months_employed <= 12:
        return ETI_MAX_MONTHLY
    else:
        return _round2(ETI_MAX_MONTHLY / 2)


def calculate_payslip(gross_salary: Decimal, months_employed: int = 1) -> dict:
    """Calculate a full payslip breakdown for a monthly gross salary.

    Returns dict with all deductions and net salary.
    """
    gross = _round2(gross_salary)
    paye = calculate_monthly_paye(gross)
    uif_employee = calculate_uif_employee(gross)
    sdl = calculate_sdl(gross)
    eti = calculate_eti(gross, months_employed)

    net = _round2(gross - paye - uif_employee)

    return {
        "gross_salary": gross,
        "paye_tax": paye,
        "uif_employee": uif_employee,
        "uif_employer": calculate_uif_employer(gross),
        "sdl": sdl,
        "eti": eti,
        "net_salary": net,
    }


def generate_emp201(payslips: list[dict]) -> dict:
    """Generate EMP201 summary from a list of payslip dicts.

    EMP201 is the monthly employer declaration to SARS, summarising
    PAYE, UIF (employee + employer), and SDL.
    """
    total_paye = Decimal("0")
    total_uif = Decimal("0")
    total_sdl = Decimal("0")
    total_eti = Decimal("0")
    total_gross = Decimal("0")
    total_employees = len(payslips)

    for slip in payslips:
        total_paye += slip.get("paye_tax", Decimal("0"))
        total_uif += slip.get("uif_employee", Decimal("0")) + slip.get("uif_employer", Decimal("0"))
        total_sdl += slip.get("sdl", Decimal("0"))
        total_eti += slip.get("eti", Decimal("0"))
        total_gross += slip.get("gross_salary", Decimal("0"))

    total_liability = _round2(total_paye + total_uif + total_sdl - total_eti)

    return {
        "total_employees": total_employees,
        "total_gross": _round2(total_gross),
        "total_paye": _round2(total_paye),
        "total_uif": _round2(total_uif),
        "total_sdl": _round2(total_sdl),
        "total_eti": _round2(total_eti),
        "total_liability": total_liability,
    }
