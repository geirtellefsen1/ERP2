"""
Norway payroll calculator.

Rules implemented (2026 rates):

Employee deductions:
  - Forskuddstrekk (PAYE) — withholding tax, percentage from employee's
    skattekort (tax card). Retrieved from Skatteetaten in production; for
    now we use the employee's stored `tax_percentage` field.

Employer contributions:
  - AGA (arbeidsgiveravgift) — zone-dependent employer NI. Rates:
      Zone 1:   14.1%  (e.g. Oslo, Stavanger, Bergen, Trondheim)
      Zone 1a:  10.6%
      Zone 2:   10.6%
      Zone 3:    6.4%
      Zone 4:    5.1%
      Zone 4a:   7.9%
      Zone 5:    0.0%
  - OTP (obligatorisk tjenestepensjon) — minimum 2% of salary between
    1G and 12G. G = grunnbeløp, approx NOK 124,028 in 2026.

Holiday pay accrual:
  - 10.2% of previous year earnings (12% for employees over 60)
  - Accrued each period, paid at holiday time or annually

Sick pay:
  - Employer pays days 1-16 (arbeidsgiverperioden)
  - NAV reimburses from day 17 for eligible employees
  - For this MVP, sick days just reduce salary proportionally; the full
    NAV integration is out of scope

A-melding XML generation: included as a method but the output is a
simplified element set — production needs the full Altinn XSD which is
hundreds of elements.
"""
from __future__ import annotations

from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from app.services.money import Money

from .base import PayrollCalculator
from .models import EmployeeInput, PayslipLine, PayslipResult


# ── Norwegian constants (2026) ──────────────────────────────────────────

# Grunnbeløp (G) — updated annually 1 May. 2026 approx NOK 124,028.
# Used for OTP lower threshold (1G) and upper threshold (12G).
G_2026 = Decimal("124028")

# AGA rates by zone
AGA_RATES = {
    "1":  Decimal("0.141"),  # Zone 1 — Oslo, Bergen, Trondheim, Stavanger
    "1a": Decimal("0.106"),  # Zone 1a
    "2":  Decimal("0.106"),  # Zone 2
    "3":  Decimal("0.064"),  # Zone 3
    "4":  Decimal("0.051"),  # Zone 4
    "4a": Decimal("0.079"),  # Zone 4a
    "5":  Decimal("0.000"),  # Zone 5 — no AGA (northern municipalities)
}

# Map common city / region names to AGA zones
CITY_TO_ZONE = {
    "oslo": "1",
    "bergen": "1",
    "trondheim": "1",
    "stavanger": "1",
    "kristiansand": "1",
    "tromso": "5",      # Tromsø — most of Troms is zone 5
    "bodo": "4a",
    "alta": "5",
    "kirkenes": "5",
}

# OTP — minimum 2% of salary between 1G and 12G for the standard scheme.
OTP_RATES = {
    "NO_OTP_2_PERCENT": Decimal("0.02"),
    "NO_OTP_5_PERCENT": Decimal("0.05"),
    "NONE": Decimal("0.00"),
}

# Holiday pay rate
HOLIDAY_PAY_RATE = Decimal("0.102")       # 10.2% standard
HOLIDAY_PAY_RATE_OVER_60 = Decimal("0.12")  # 12% for over-60


class NorwayPayrollCalculator(PayrollCalculator):
    country_code = "NO"
    currency = "NOK"

    # ── Employee deductions ─────────────────────────────────────────

    def _calculate_employee_deductions(
        self, employee: EmployeeInput, taxable: Money
    ) -> list[PayslipLine]:
        lines: list[PayslipLine] = []

        # Forskuddstrekk (PAYE)
        paye = taxable * employee.tax_percentage
        lines.append(
            PayslipLine(
                code="FORSKUDDSTREKK",
                label="Forskuddstrekk (PAYE)",
                amount=paye,
                type="employee_deduction",
            )
        )

        return lines

    # ── Employer contributions ──────────────────────────────────────

    def _calculate_employer_contributions(
        self, employee: EmployeeInput, gross: Money
    ) -> list[PayslipLine]:
        lines: list[PayslipLine] = []

        # AGA
        zone = self._resolve_aga_zone(employee.work_region)
        aga_rate = AGA_RATES[zone]
        aga = gross * aga_rate
        lines.append(
            PayslipLine(
                code="AGA",
                label=f"Arbeidsgiveravgift (zone {zone})",
                amount=aga,
                type="employer_contribution",
            )
        )

        # OTP — 2% of salary between 1G and 12G (monthly pro-rata)
        otp_rate = OTP_RATES.get(employee.pension_scheme, Decimal("0"))
        if otp_rate > 0:
            # Convert annual thresholds to monthly (÷12)
            monthly_1g = G_2026 / 12
            monthly_12g = (G_2026 * 12) / 12  # = G
            # Wait — that's wrong. 12G annual = G * 12, monthly = (G * 12) / 12 = G
            # The "between 1G and 12G" range refers to ANNUAL salary, so monthly
            # equivalent is between G/12 and 12G/12 = G.
            # Simpler: check the annualised gross.
            annual_gross = gross.amount * Decimal(12)
            if annual_gross > G_2026:
                # Capped at 12G
                pensionable_annual = min(annual_gross, G_2026 * 12) - G_2026
                pensionable_monthly = pensionable_annual / Decimal(12)
                otp_amount = Money(pensionable_monthly * otp_rate, self.currency)
            else:
                otp_amount = Money.zero(self.currency)
            lines.append(
                PayslipLine(
                    code="OTP",
                    label="Obligatorisk tjenestepensjon",
                    amount=otp_amount,
                    type="employer_contribution",
                )
            )

        # Holiday pay accrual
        rate = (
            HOLIDAY_PAY_RATE_OVER_60 if employee.age >= 60 else HOLIDAY_PAY_RATE
        )
        holiday_pay = gross * rate
        lines.append(
            PayslipLine(
                code="FERIEPENGER",
                label="Feriepenger (accrual)",
                amount=holiday_pay,
                type="employer_contribution",
            )
        )

        return lines

    def _post_calculate(self, employee: EmployeeInput, result: PayslipResult) -> None:
        # Warn if the employee is in a high-AGA zone but no work_region set
        if not employee.work_region:
            result.warnings.append(
                "No work_region set — defaulted to AGA zone 1 (14.1%). "
                "Set employee.work_region to the correct municipality."
            )

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _resolve_aga_zone(work_region: str) -> str:
        if not work_region:
            return "1"
        key = work_region.lower().strip()
        if key in AGA_RATES:
            return key
        if key in CITY_TO_ZONE:
            return CITY_TO_ZONE[key]
        return "1"  # default

    # ── A-melding XML generator ────────────────────────────────────

    @staticmethod
    def generate_a_melding(
        organisation_number: str,
        period_year: int,
        period_month: int,
        payslips: list[PayslipResult],
    ) -> str:
        """
        Generate a simplified A-melding XML payload for Altinn submission.

        The real A-melding schema (Skatteetaten MELDINGSFORMAT_A) has many
        more elements — this skeleton covers the required fields for a
        basic monthly report. Extend when integrating with the live Altinn
        endpoint.
        """
        root = Element("melding")
        root.set("xmlns", "http://skatteetaten.no/a-melding")

        opplysningspliktig = SubElement(root, "opplysningspliktig")
        SubElement(opplysningspliktig, "organisasjonsnummer").text = organisation_number

        periode = SubElement(root, "periode")
        SubElement(periode, "aar").text = str(period_year)
        SubElement(periode, "maaned").text = f"{period_month:02d}"

        for payslip in payslips:
            virksomhet = SubElement(root, "virksomhet")
            inntektsmottaker = SubElement(virksomhet, "inntektsmottaker")
            SubElement(inntektsmottaker, "norskIdentifikator").text = "11111111111"
            SubElement(inntektsmottaker, "navn").text = payslip.employee_name

            inntekt = SubElement(inntektsmottaker, "inntekt")
            SubElement(inntekt, "loennsinntekt").text = str(payslip.gross_salary.amount)

            for line in payslip.lines:
                if line.code == "FORSKUDDSTREKK":
                    forskuddstrekk = SubElement(inntektsmottaker, "forskuddstrekk")
                    SubElement(forskuddstrekk, "beloep").text = str(line.amount.amount)
                elif line.code == "AGA":
                    aga = SubElement(inntektsmottaker, "arbeidsgiveravgift")
                    SubElement(aga, "beregnetAvgift").text = str(line.amount.amount)

        # Pretty-print for readability in tests and logs
        raw = tostring(root, encoding="unicode")
        pretty = minidom.parseString(raw).toprettyxml(indent="  ")
        return pretty
