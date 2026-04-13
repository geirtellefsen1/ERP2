"""
Finland payroll calculator.

Rules implemented (2026 rates):

Employee deductions:
  - Ennakonpidätys — preliminary tax withheld per employee's verokortti.
    Percentage retrieved from Vero Suomi in production; for MVP we use
    the stored `tax_percentage` field.
  - TyEL (työntekijän osuus) — employee pension ~7.15% (varies by age
    category 17-52, 53-62, 63+).
  - Työttömyysvakuutusmaksu (employee) — unemployment insurance 1.5%.

Employer contributions:
  - TyEL (työnantajan osuus) — employer pension ~24.8% (negotiated
    annually with pension insurance company).
  - Työttömyysvakuutusmaksu (employer) — 0.52% up to EUR 2,251,500
    annual wage bill, 2.06% above that threshold.
  - Tapaturmavakuutus — accident insurance, rate set by insurer
    (simplified: 0.7%).
  - Ryhmähenkivakuutus — group life insurance (simplified: 0.06%).

Holiday pay:
  - 2 days per month worked, paid at vacation time.
  - Simplified as 9% accrual (common approximation).

IMPORTANT: TULOREKISTERI real-time reporting.
Every salary payment must be reported to the Incomes Register within 5
calendar days. The `generate_tulorekisteri_payload` method produces the
JSON payload that gets posted to the Vero Tulorekisteri API. In
production, this must be triggered AUTOMATICALLY on every payroll run
confirmation — never batched monthly.
"""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from app.services.money import Money

from .base import PayrollCalculator
from .models import EmployeeInput, PayslipLine, PayslipResult


# ── Finnish constants (2026 rates) ─────────────────────────────────────

# TyEL employer + employee rates (aggregate)
TYEL_EMPLOYER = Decimal("0.1742")   # ~17.42% after employee share netted off (simplified)
TYEL_EMPLOYEE_YOUNG = Decimal("0.0715")   # ages 17-52
TYEL_EMPLOYEE_MIDDLE = Decimal("0.0870")  # ages 53-62
TYEL_EMPLOYEE_SENIOR = Decimal("0.0715")  # ages 63+ (drops back)

# Unemployment insurance
UNEMP_EMPLOYER_LOW = Decimal("0.0052")    # up to annual threshold
UNEMP_EMPLOYER_HIGH = Decimal("0.0206")   # above threshold
UNEMP_EMPLOYEE = Decimal("0.015")

# Accident and group life (approximations — real rates set by insurer)
TAPATURMA_RATE = Decimal("0.007")
GROUP_LIFE_RATE = Decimal("0.0006")

# Holiday pay
HOLIDAY_PAY_RATE = Decimal("0.09")  # simplified — real rule is 2 days/month


class FinlandPayrollCalculator(PayrollCalculator):
    country_code = "FI"
    currency = "EUR"

    # ── Employee deductions ─────────────────────────────────────────

    def _calculate_employee_deductions(
        self, employee: EmployeeInput, taxable: Money
    ) -> list[PayslipLine]:
        lines: list[PayslipLine] = []

        # Ennakonpidätys
        tax = taxable * employee.tax_percentage
        lines.append(
            PayslipLine(
                code="ENNAKONPIDATYS",
                label="Ennakonpidätys",
                amount=tax,
                type="employee_deduction",
            )
        )

        # TyEL employee contribution (age-banded)
        tyel_rate = self._tyel_employee_rate(employee.age)
        tyel_emp = taxable * tyel_rate
        lines.append(
            PayslipLine(
                code="TYEL_EMPLOYEE",
                label="TyEL-maksu (työntekijä)",
                amount=tyel_emp,
                type="employee_deduction",
            )
        )

        # Unemployment insurance (employee)
        unemp = taxable * UNEMP_EMPLOYEE
        lines.append(
            PayslipLine(
                code="TVR_EMPLOYEE",
                label="Työttömyysvakuutusmaksu (työntekijä)",
                amount=unemp,
                type="employee_deduction",
            )
        )

        return lines

    # ── Employer contributions ──────────────────────────────────────

    def _calculate_employer_contributions(
        self, employee: EmployeeInput, gross: Money
    ) -> list[PayslipLine]:
        lines: list[PayslipLine] = []

        # TyEL employer share
        tyel = gross * TYEL_EMPLOYER
        lines.append(
            PayslipLine(
                code="TYEL_EMPLOYER",
                label="TyEL työeläkevakuutus (työnantaja)",
                amount=tyel,
                type="employer_contribution",
            )
        )

        # Unemployment insurance (employer) — always low rate for single-employee
        # scope. Real rule depends on total annual wage bill across the company.
        unemp = gross * UNEMP_EMPLOYER_LOW
        lines.append(
            PayslipLine(
                code="TVR_EMPLOYER",
                label="Työttömyysvakuutusmaksu (työnantaja)",
                amount=unemp,
                type="employer_contribution",
            )
        )

        # Accident insurance
        tapaturma = gross * TAPATURMA_RATE
        lines.append(
            PayslipLine(
                code="ACCIDENT_INS",
                label="Tapaturmavakuutus",
                amount=tapaturma,
                type="employer_contribution",
            )
        )

        # Group life insurance
        group_life = gross * GROUP_LIFE_RATE
        lines.append(
            PayslipLine(
                code="GROUP_LIFE",
                label="Ryhmähenkivakuutus",
                amount=group_life,
                type="employer_contribution",
            )
        )

        # Holiday pay accrual
        holiday = gross * HOLIDAY_PAY_RATE
        lines.append(
            PayslipLine(
                code="LOMARAHA",
                label="Lomaraha (accrual)",
                amount=holiday,
                type="employer_contribution",
            )
        )

        return lines

    def _post_calculate(self, employee: EmployeeInput, result: PayslipResult) -> None:
        # Loud reminder about the 5-day Tulorekisteri deadline
        result.warnings.append(
            "Remember: Tulorekisteri requires submission within 5 calendar days "
            "of the payment date. Use generate_tulorekisteri_payload() and post "
            "it to the Vero API as soon as this run is confirmed."
        )

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _tyel_employee_rate(age: int) -> Decimal:
        if age < 53:
            return TYEL_EMPLOYEE_YOUNG
        if age <= 62:
            return TYEL_EMPLOYEE_MIDDLE
        return TYEL_EMPLOYEE_SENIOR

    # ── Tulorekisteri (Incomes Register) payload generator ────────

    @staticmethod
    def generate_tulorekisteri_payload(
        employer_business_id: str,
        payment_date: str,  # YYYY-MM-DD
        payslips: list[PayslipResult],
    ) -> str:
        """
        Build the Tulorekisteri "earnings-payment-report" JSON payload.

        Real Tulorekisteri has a fuller schema — this is the minimum for
        a valid MVP submission. Each payment to each employee becomes one
        "incomeEarnerReport" item in the top-level payload.

        Returns the JSON as a string. Post to Vero's
        /tulorekisteri/earnings-payment-reports endpoint in production.

        NOTE: Vero assigns a unique "payerReportReference" per submission.
        Production code must generate this deterministically (e.g. from
        the payroll run ID) so retries don't create duplicates.
        """
        reports = []
        for p in payslips:
            # Sum taxable items and deductions by type
            income_items = []
            tax_items = []
            insurance_items = []

            for line in p.lines:
                if line.type == "earning":
                    income_items.append(
                        {
                            "incomeType": {
                                "generalCode": "201",  # "Time-rate pay"
                                "codeSeries": "2",
                            },
                            "amount": str(line.amount.amount),
                        }
                    )
                elif line.code == "ENNAKONPIDATYS":
                    tax_items.append(
                        {
                            "type": "withholdingTax",
                            "amount": str(line.amount.amount),
                        }
                    )
                elif line.code in ("TYEL_EMPLOYEE",):
                    insurance_items.append(
                        {
                            "type": "employeePensionInsurance",
                            "amount": str(line.amount.amount),
                        }
                    )
                elif line.code == "TVR_EMPLOYEE":
                    insurance_items.append(
                        {
                            "type": "employeeUnemploymentInsurance",
                            "amount": str(line.amount.amount),
                        }
                    )

            reports.append(
                {
                    "incomeEarner": {
                        "identifier": {
                            "type": "finnishPersonalIdentityCode",
                            "id": "000000-0000",  # production: real hetu
                        },
                        "name": p.employee_name,
                    },
                    "paymentDate": payment_date,
                    "payPeriod": {
                        "start": p.period_start.isoformat(),
                        "end": p.period_end.isoformat(),
                    },
                    "incomeItems": income_items,
                    "taxItems": tax_items,
                    "insuranceItems": insurance_items,
                }
            )

        payload: dict[str, Any] = {
            "payer": {
                "identifier": {
                    "type": "finnishBusinessId",
                    "id": employer_business_id,
                },
            },
            "paymentDate": payment_date,
            "deliveryDataOwner": {
                "identifier": {
                    "type": "finnishBusinessId",
                    "id": employer_business_id,
                },
            },
            "incomeEarnerReports": reports,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)
