"""
Sweden payroll calculator.

Rules implemented (2026 rates):

Employee deductions:
  - Preliminärskatt (A-skatt) — withholding tax from employee's skattsedel.
    Percentage retrieved from Skatteverket in production; for MVP we use
    the stored `tax_percentage` field.

Employer contributions:
  - Arbetsgivaravgifter — age-banded:
      Standard (23-65):           31.42%
      Under-23 (born 2003-):      10.21%
      Over-65 (born -1960):       10.21%
      First-year employment:      reductions may apply, not modelled here
  - ITP1 occupational pension — 4.5% up to 7.5 income base amounts,
    30% above. Income base amount (inkomstbasbelopp) 2026 ≈ SEK 75,400
    monthly threshold. Simplified: treat as 4.5% flat for MVP.
  - Other ITP variants + SAF-LO: collective-agreement dependent,
    out of scope for MVP — use "SE_NONE" for pension_scheme to skip.

Holiday pay (semesterlön):
  - 12% of gross accrued. Paid at vacation time or reconciled annually.

Karensdag (sick leave day 1):
  - First day of sick leave is unpaid (karensavdrag deduction).
  - Days 2-14 paid by employer at 80%.

AGD (arbetsgivardeklaration) generation: simplified XML.
"""
from __future__ import annotations

from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from app.services.money import Money

from .base import PayrollCalculator
from .models import EmployeeInput, PayslipLine, PayslipResult


# ── Swedish constants (2026) ────────────────────────────────────────────

# Arbetsgivaravgifter rates
ARBGAV_STANDARD = Decimal("0.3142")     # ages 23-65
ARBGAV_REDUCED = Decimal("0.1021")      # under-23 or over-65

# ITP1 pension contribution
ITP1_BELOW_THRESHOLD = Decimal("0.045")  # 4.5% below 7.5 income base amounts
ITP1_ABOVE_THRESHOLD = Decimal("0.30")   # 30% above

# Income base amount (inkomstbasbelopp) 2026 ≈ SEK 79,300
# 7.5 IBB = SEK 594,750 annual = SEK 49,562.50 monthly
ITP1_MONTHLY_THRESHOLD = Decimal("49562.50")

# Holiday pay rate
SEMESTERLON_RATE = Decimal("0.12")

# Sick pay
SICK_PAY_RATE = Decimal("0.80")   # days 2-14 at 80%


class SwedenPayrollCalculator(PayrollCalculator):
    country_code = "SE"
    currency = "SEK"

    # ── Employee deductions ─────────────────────────────────────────

    def _calculate_employee_deductions(
        self, employee: EmployeeInput, taxable: Money
    ) -> list[PayslipLine]:
        lines: list[PayslipLine] = []

        # Preliminärskatt (A-skatt)
        prelim_tax = taxable * employee.tax_percentage
        lines.append(
            PayslipLine(
                code="PRELIMINAR_SKATT",
                label="Preliminärskatt (A-skatt)",
                amount=prelim_tax,
                type="employee_deduction",
            )
        )

        return lines

    # ── Employer contributions ──────────────────────────────────────

    def _calculate_employer_contributions(
        self, employee: EmployeeInput, gross: Money
    ) -> list[PayslipLine]:
        lines: list[PayslipLine] = []

        # Arbetsgivaravgifter — rate depends on age band
        rate = self._arbgav_rate_for_age(employee.age)
        arbgav = gross * rate
        age_label = (
            "standard" if rate == ARBGAV_STANDARD
            else f"reduced (age {employee.age})"
        )
        lines.append(
            PayslipLine(
                code="ARBGAV",
                label=f"Arbetsgivaravgifter ({age_label})",
                amount=arbgav,
                type="employer_contribution",
            )
        )

        # ITP1 pension (for SE_ITP1 scheme only — others out of scope for MVP)
        if employee.pension_scheme == "SE_ITP1":
            gross_amount = gross.amount
            if gross_amount <= ITP1_MONTHLY_THRESHOLD:
                itp = gross * ITP1_BELOW_THRESHOLD
            else:
                below = Money(ITP1_MONTHLY_THRESHOLD * ITP1_BELOW_THRESHOLD, self.currency)
                above_base = gross_amount - ITP1_MONTHLY_THRESHOLD
                above = Money(above_base * ITP1_ABOVE_THRESHOLD, self.currency)
                itp = below + above
            lines.append(
                PayslipLine(
                    code="ITP1",
                    label="Tjänstepension ITP1",
                    amount=itp,
                    type="employer_contribution",
                )
            )

        # Semesterlön accrual
        semesterlon = gross * SEMESTERLON_RATE
        lines.append(
            PayslipLine(
                code="SEMESTERLON",
                label="Semesterlön (accrual)",
                amount=semesterlon,
                type="employer_contribution",
            )
        )

        return lines

    def _post_calculate(self, employee: EmployeeInput, result: PayslipResult) -> None:
        if employee.pension_scheme not in ("SE_ITP1", "SE_NONE", "NONE"):
            result.warnings.append(
                f"Pension scheme {employee.pension_scheme} not modelled in MVP. "
                f"ITP1, SE_NONE, and NONE are supported. Others fall back to no pension."
            )

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _arbgav_rate_for_age(age: int) -> Decimal:
        """Under-23 and over-65 get the reduced rate."""
        if age < 23 or age > 65:
            return ARBGAV_REDUCED
        return ARBGAV_STANDARD

    # ── AGD XML generator ──────────────────────────────────────────

    @staticmethod
    def generate_agd(
        organisation_number: str,
        period_year: int,
        period_month: int,
        payslips: list[PayslipResult],
    ) -> str:
        """
        Generate a simplified Arbetsgivardeklaration XML payload.

        Real Skatteverket AGD schema has many more elements — this is a
        skeleton for the MVP. Extend before production rollout.
        """
        root = Element("arbetsgivardeklaration")
        root.set("xmlns", "http://xmls.skatteverket.se/se/skatteverket/agd")

        huvuduppgift = SubElement(root, "HuvudUppgift")
        SubElement(huvuduppgift, "ArbetsgivareID").text = organisation_number
        SubElement(huvuduppgift, "Period").text = f"{period_year}{period_month:02d}"

        total_gross = sum(
            (p.gross_salary.amount for p in payslips),
            start=Decimal(0),
        )
        total_tax = sum(
            (
                line.amount.amount
                for p in payslips
                for line in p.lines
                if line.code == "PRELIMINAR_SKATT"
            ),
            start=Decimal(0),
        )
        total_arbgav = sum(
            (
                line.amount.amount
                for p in payslips
                for line in p.lines
                if line.code == "ARBGAV"
            ),
            start=Decimal(0),
        )

        huvud_belopp = SubElement(huvuduppgift, "Belopp")
        SubElement(huvud_belopp, "SamladLoneSumma").text = str(total_gross)
        SubElement(huvud_belopp, "AvdragenSkatt").text = str(total_tax)
        SubElement(huvud_belopp, "Arbetsgivaravgifter").text = str(total_arbgav)

        for payslip in payslips:
            ind = SubElement(root, "IndividUppgift")
            SubElement(ind, "BetalningsmottagareID").text = "000000000000"
            SubElement(ind, "Namn").text = payslip.employee_name
            SubElement(ind, "KontantErsattning").text = str(payslip.gross_salary.amount)

            for line in payslip.lines:
                if line.code == "PRELIMINAR_SKATT":
                    SubElement(ind, "AvdragenPreliminarSkatt").text = str(line.amount.amount)

        raw = tostring(root, encoding="unicode")
        pretty = minidom.parseString(raw).toprettyxml(indent="  ")
        return pretty
