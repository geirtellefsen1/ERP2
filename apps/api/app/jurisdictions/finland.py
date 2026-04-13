"""
Finland jurisdiction module.

Sources:
- VAT rates: Vero Suomi (Vero = Finnish tax authority). Standard rate changed
  to 25.5% in September 2024.
- Payroll: TyEL pension, työttömyysvakuutus, Tulorekisteri real-time reporting
- Public holidays: suomalaiset juhlapyhät
- Bank format: IBAN FIxx (EUR, SEPA)

IMPORTANT: Finland's Tulorekisteri (Incomes Register) requires real-time
payroll reporting within 5 calendar days of every payment. This is the
strictest reporting requirement in the Nordics — the payroll engine MUST
submit to Tulorekisteri on every payroll run, not in a monthly batch.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from .base import (
    JurisdictionBase,
    VatRate,
    PayrollRules,
    PayrollDeduction,
    FilingDeadline,
    PublicHoliday,
    BankFormat,
    AccountTemplate,
    StatutoryForm,
)


class FinlandJurisdiction(JurisdictionBase):
    country_code = "FI"
    country_name = "Finland"

    def currency(self) -> str:
        return "EUR"

    def language(self) -> str:
        return "fi-FI"

    # ── VAT ──────────────────────────────────────────────────────────────

    def vat_rates(self, on_date: date) -> list[VatRate]:
        """Finnish VAT standard rate increased from 24% to 25.5% on 1 Sep 2024."""
        rates = [
            VatRate(
                code="FI-14",
                label="Alennettu kanta (14%)",
                rate=Decimal("0.14"),
                category="reduced",
                applies_to="Food, restaurant and catering services",
                effective_from=date(2013, 1, 1),
            ),
            VatRate(
                code="FI-10",
                label="Alennettu kanta (10%)",
                rate=Decimal("0.10"),
                category="reduced",
                applies_to="Books, medicine, sport, cultural events, passenger transport, hotel",
                effective_from=date(2013, 1, 1),
            ),
            VatRate(
                code="FI-0",
                label="Nollakanta",
                rate=Decimal("0.00"),
                category="zero",
                applies_to="Exports, intra-EU supplies",
                effective_from=date(1995, 1, 1),
            ),
        ]
        # Standard rate: 24% until 31 Aug 2024, 25.5% from 1 Sep 2024
        if on_date < date(2024, 9, 1):
            rates.insert(
                0,
                VatRate(
                    code="FI-24",
                    label="Yleinen verokanta (24%)",
                    rate=Decimal("0.24"),
                    category="standard",
                    applies_to="Most goods and services",
                    effective_from=date(2013, 1, 1),
                    effective_to=date(2024, 8, 31),
                ),
            )
        else:
            rates.insert(
                0,
                VatRate(
                    code="FI-255",
                    label="Yleinen verokanta (25.5%)",
                    rate=Decimal("0.255"),
                    category="standard",
                    applies_to="Most goods and services",
                    effective_from=date(2024, 9, 1),
                ),
            )
        return rates

    def vat_filing_frequency(self) -> str:
        return "monthly"

    # ── Payroll ─────────────────────────────────────────────────────────

    def payroll_rules(self, employee_type: str, on_date: date) -> PayrollRules:
        """
        Finnish payroll rules — 2026 rates.
        NOTE: Tulorekisteri requires submission within 5 days of payment.
        """
        return PayrollRules(
            country_code="FI",
            effective_on=on_date,
            currency="EUR",
            employer_contributions=[
                PayrollDeduction(
                    code="TYEL",
                    label="TyEL työeläkevakuutus",
                    rate=Decimal("0.248"),
                    base="gross",
                    paid_by="employer",
                    notes="~24.8% employer pension contribution. Exact rate "
                          "negotiated annually with pension insurance company. "
                          "Employee also contributes ~7.15%.",
                ),
                PayrollDeduction(
                    code="TVR_EMPLOYER",
                    label="Työttömyysvakuutusmaksu (työnantaja)",
                    rate=Decimal("0.0052"),
                    base="gross",
                    paid_by="employer",
                    notes="0.52% up to EUR 2,251,500 wage bill, 2.06% above.",
                ),
                PayrollDeduction(
                    code="ACCIDENT_INS",
                    label="Tapaturmavakuutus",
                    rate=None,
                    base="gross",
                    paid_by="employer",
                    notes="Rate set by the employer's accident insurance company.",
                ),
                PayrollDeduction(
                    code="GROUP_LIFE",
                    label="Ryhmähenkivakuutus",
                    rate=None,
                    base="gross",
                    paid_by="employer",
                    notes="Typically negotiated in collective agreement.",
                ),
            ],
            employee_deductions=[
                PayrollDeduction(
                    code="ENNAKONPIDATYS",
                    label="Ennakonpidätys",
                    rate=None,
                    base="taxable",
                    paid_by="employee",
                    notes="Preliminary tax withheld per employee's verokortti "
                          "(tax card) from Vero Suomi.",
                ),
                PayrollDeduction(
                    code="TYEL_EMPLOYEE",
                    label="TyEL-maksu (työntekijä)",
                    rate=Decimal("0.0715"),
                    base="gross",
                    paid_by="employee",
                    notes="~7.15% employee pension contribution; exact rate "
                          "varies by age category.",
                ),
                PayrollDeduction(
                    code="TVR_EMPLOYEE",
                    label="Työttömyysvakuutusmaksu (työntekijä)",
                    rate=Decimal("0.015"),
                    base="gross",
                    paid_by="employee",
                    notes="1.5% unemployment insurance.",
                ),
            ],
            holiday_pay_rate=Decimal("0.09"),   # approx; 2 days per month worked, 9% of gross
            sick_pay_employer_days=9,           # waiting day + 9 payable days, employer-paid
            reporting_frequency="realtime_5d",
            reporting_endpoint="Tulorekisteri",
            notes="CRITICAL: Tulorekisteri requires individual submission "
                  "within 5 calendar days of each payment. Cannot batch. "
                  "Must be automated from payroll run confirmation.",
        )

    # ── Calendars ───────────────────────────────────────────────────────

    def filing_calendar(self, year: int) -> list[FilingDeadline]:
        deadlines: list[FilingDeadline] = []

        # Monthly VAT — due 12th of month + 2 (self-assessment tax return period)
        for month in range(1, 13):
            due_month = month + 2
            due_year = year + (1 if due_month > 12 else 0)
            due_month = ((due_month - 1) % 12) + 1
            deadlines.append(
                FilingDeadline(
                    form_code="ALV",
                    label=f"Arvonlisäveroilmoitus — {year}-{month:02d}",
                    due_date=date(due_year, due_month, 12),
                    covers_period=f"{year}-{month:02d}",
                    endpoint="OmaVero",
                )
            )

        # Tulorekisteri is real-time (every payment within 5 days) so no
        # periodic deadline — represent it as a monthly marker instead.
        for month in range(1, 13):
            deadlines.append(
                FilingDeadline(
                    form_code="Tulorekisteri",
                    label=f"Tulorekisteri submissions — {year}-{month:02d}",
                    due_date=date(year, month, 1),  # marker only
                    covers_period=f"{year}-{month:02d}",
                    endpoint="Tulorekisteri",
                    reminder_days=(0,),  # real-time — no reminder window
                )
            )

        return sorted(deadlines, key=lambda d: d.due_date)

    def public_holidays(self, year: int) -> list[PublicHoliday]:
        return [
            PublicHoliday(date(year, 1, 1), "Uudenvuodenpäivä", "FI"),
            PublicHoliday(date(year, 1, 6), "Loppiainen", "FI"),
            PublicHoliday(date(year, 5, 1), "Vappu", "FI"),
            PublicHoliday(date(year, 12, 6), "Itsenäisyyspäivä", "FI"),
            PublicHoliday(date(year, 12, 25), "Joulupäivä", "FI"),
            PublicHoliday(date(year, 12, 26), "Tapaninpäivä", "FI"),
            # Easter-based (Pitkäperjantai, Pääsiäispäivä, 2. pääsiäispäivä,
            # Helatorstai, Helluntai) + Juhannuspäivä + Pyhäinpäivä handled
            # via dateutil.easter in production.
        ]

    # ── Chart of accounts ───────────────────────────────────────────────

    def coa_template(self, industry_vertical: str | None) -> list[AccountTemplate]:
        """
        Minimal Finnish standard account skeleton (Finnish Accounting Act).
        Extend per vertical.
        """
        base: list[AccountTemplate] = [
            # Assets
            AccountTemplate("1000", "Koneet ja kalusto", "Machinery and equipment", "asset", "non_current_asset"),
            AccountTemplate("1700", "Myyntisaamiset", "Trade receivables", "asset", "current_asset"),
            AccountTemplate("1910", "Pankkitili", "Bank account", "asset", "current_asset"),
            # Equity & liabilities
            AccountTemplate("2000", "Osakepääoma", "Share capital", "equity", "equity"),
            AccountTemplate("2100", "Edellisten tilikausien voitto/tappio", "Retained earnings", "equity", "equity"),
            AccountTemplate("2400", "Ostovelat", "Trade payables", "liability", "current_liability"),
            AccountTemplate("2930", "Arvonlisäverovelka", "VAT payable", "liability", "current_liability"),
            AccountTemplate("2941", "Ennakonpidätysvelka", "PAYE payable", "liability", "current_liability"),
            # Revenue
            AccountTemplate("3000", "Myynti 25,5%", "Sales 25.5% VAT", "revenue", "operating_revenue"),
            AccountTemplate("3100", "Myynti 14%", "Sales 14% VAT", "revenue", "operating_revenue"),
            AccountTemplate("3200", "Myynti 10%", "Sales 10% VAT", "revenue", "operating_revenue"),
            # Cost of sales
            AccountTemplate("4000", "Ostot", "Purchases", "expense", "cost_of_sales"),
            # Personnel
            AccountTemplate("5000", "Palkat", "Wages and salaries", "expense", "operating_expense"),
            AccountTemplate("5100", "TyEL-maksut", "TyEL contributions", "expense", "operating_expense"),
            AccountTemplate("5200", "Muut henkilösivukulut", "Other personnel costs", "expense", "operating_expense"),
            # Other operating costs
            AccountTemplate("6300", "Vuokrat", "Rent", "expense", "operating_expense"),
            AccountTemplate("6800", "Toimistokulut", "Office expenses", "expense", "operating_expense"),
            # Financial
            AccountTemplate("9000", "Korkotuotot", "Interest income", "revenue", "financial_income"),
            AccountTemplate("9400", "Korkokulut", "Interest expense", "expense", "financial_expense"),
        ]
        return base

    # ── Forms ───────────────────────────────────────────────────────────

    def statutory_forms(self) -> list[StatutoryForm]:
        return [
            StatutoryForm(
                code="ALV",
                label="VAT return (arvonlisäveroilmoitus)",
                description="Monthly/quarterly VAT return via OmaVero",
                frequency="monthly",
                endpoint="OmaVero",
            ),
            StatutoryForm(
                code="Tulorekisteri",
                label="Incomes Register real-time report",
                description="Individual payment report within 5 calendar days "
                            "of each salary payment — REAL-TIME, NOT BATCH",
                frequency="adhoc",
                endpoint="Tulorekisteri",
            ),
            StatutoryForm(
                code="TVL",
                label="Corporate income tax return",
                description="Annual corporate tax return via OmaVero",
                frequency="annual",
                endpoint="OmaVero",
            ),
        ]

    # ── Validation & banking ────────────────────────────────────────────

    def validate_vat_number(self, vat_number: str) -> bool:
        """
        Finnish VAT number: FI + 8 digits. The 8-digit part is the Y-tunnus
        (business ID): 7 digits + check digit using modulo-11.
        """
        cleaned = vat_number.strip().upper()
        if cleaned.startswith("FI"):
            cleaned = cleaned[2:]
        if not cleaned.isdigit() or len(cleaned) != 8:
            return False
        weights = (7, 9, 10, 5, 8, 4, 2)
        s = sum(int(cleaned[i]) * weights[i] for i in range(7))
        remainder = s % 11
        if remainder == 0:
            check = 0
        elif remainder == 1:
            return False
        else:
            check = 11 - remainder
        return check == int(cleaned[7])

    def bank_format(self) -> BankFormat:
        return BankFormat(
            country_code="FI",
            iban_prefix="FI",
            iban_length=18,
            domestic_format="IBAN FI + 16 digits (SEPA native)",
            payment_file_format="SEPA / ISO 20022 PAIN.001",
            open_banking_provider="Aiia / OP Financial Group API",
        )
