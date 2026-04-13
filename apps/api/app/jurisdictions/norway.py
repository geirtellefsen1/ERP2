"""
Norway jurisdiction module.

Sources:
- VAT rates: Skatteetaten (mva, merverdiavgift)
- Payroll: Skatteetaten (forskuddstrekk, AGA, OTP), NAV (sick pay)
- Public holidays: norske helligdager
- Bank format: Norwegian 11-digit account number, IBAN NOxx

All rates verified as of January 2026. Update this file when the statutes
change — tax changes typically take effect 1 Jan, 1 Jul, or from a specific
date announced in the state budget.
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


class NorwayJurisdiction(JurisdictionBase):
    country_code = "NO"
    country_name = "Norway"

    def currency(self) -> str:
        return "NOK"

    def language(self) -> str:
        return "nb-NO"

    # ── VAT ──────────────────────────────────────────────────────────────

    def vat_rates(self, on_date: date) -> list[VatRate]:
        # Rates stable since 2016. Zero rate for exports, certain books/newspapers.
        return [
            VatRate(
                code="NO-25",
                label="Standard sats",
                rate=Decimal("0.25"),
                category="standard",
                applies_to="Most goods and services",
                effective_from=date(2005, 1, 1),
            ),
            VatRate(
                code="NO-15",
                label="Redusert sats (matvarer)",
                rate=Decimal("0.15"),
                category="reduced",
                applies_to="Food and beverages (non-alcoholic)",
                effective_from=date(2012, 1, 1),
            ),
            VatRate(
                code="NO-12",
                label="Lav sats (persontransport, hotell)",
                rate=Decimal("0.12"),
                category="reduced",
                applies_to="Passenger transport, hotel accommodation, cinema, museums",
                effective_from=date(2016, 1, 1),
            ),
            VatRate(
                code="NO-0",
                label="Null sats",
                rate=Decimal("0.00"),
                category="zero",
                applies_to="Exports, books, newspapers",
                effective_from=date(2005, 1, 1),
            ),
        ]

    def vat_filing_frequency(self) -> str:
        # Norway: bimonthly MVA-melding via Altinn is the default
        return "bimonthly"

    # ── Payroll ─────────────────────────────────────────────────────────

    def payroll_rules(self, employee_type: str, on_date: date) -> PayrollRules:
        """
        Norwegian payroll rules — 2026 rates.
        AGA zone 1 (standard 14.1%) assumed; pick zone from employee's work
        municipality in the actual payroll engine.
        """
        return PayrollRules(
            country_code="NO",
            effective_on=on_date,
            currency="NOK",
            employer_contributions=[
                PayrollDeduction(
                    code="AGA",
                    label="Arbeidsgiveravgift (sone 1)",
                    rate=Decimal("0.141"),
                    base="gross",
                    paid_by="employer",
                    notes="Zone-dependent (0% in zone 5 up to 14.1% in zone 1a). "
                          "Must be set per employee's work location.",
                ),
                PayrollDeduction(
                    code="OTP",
                    label="Obligatorisk tjenestepensjon",
                    rate=Decimal("0.02"),
                    base="capped",
                    paid_by="employer",
                    notes="Minimum 2% of salary between 1G and 12G. "
                          "G = grunnbeløp, updated 1 May annually.",
                ),
            ],
            employee_deductions=[
                PayrollDeduction(
                    code="FORSKUDDSTREKK",
                    label="Forskuddstrekk (PAYE)",
                    rate=None,
                    base="taxable",
                    paid_by="employee",
                    notes="Personalised deduction retrieved from Skatteetaten via "
                          "skattekort-API. Table or percentage-based depending on "
                          "the employee's tax card type.",
                ),
            ],
            holiday_pay_rate=Decimal("0.102"),  # 12% for employees over 60
            sick_pay_employer_days=16,          # arbeidsgiverperioden
            reporting_frequency="monthly",
            reporting_endpoint="Altinn A-melding",
            notes="Annual reconciliation in January. NAV reimburses sick pay "
                  "from day 17 if employee has NAV sick-pay rights.",
        )

    # ── Calendars ───────────────────────────────────────────────────────

    def filing_calendar(self, year: int) -> list[FilingDeadline]:
        """Key statutory deadlines for a Norwegian client for the given year."""
        deadlines: list[FilingDeadline] = []

        # Bimonthly VAT — due 10th of the second month after the period
        # (e.g. Jan-Feb period due 10 April)
        mva_periods = [
            (f"Jan-Feb {year}", date(year, 4, 10)),
            (f"Mar-Apr {year}", date(year, 6, 10)),
            (f"May-Jun {year}", date(year, 8, 31)),
            (f"Jul-Aug {year}", date(year, 10, 10)),
            (f"Sep-Oct {year}", date(year, 12, 10)),
            (f"Nov-Dec {year}", date(year + 1, 2, 10)),
        ]
        for period, due in mva_periods:
            deadlines.append(
                FilingDeadline(
                    form_code="MVA-melding",
                    label=f"MVA-melding — {period}",
                    due_date=due,
                    covers_period=period,
                    endpoint="Altinn",
                )
            )

        # Monthly A-melding — due 5th of following month
        for month in range(1, 13):
            due_year = year if month < 12 else year + 1
            due_month = month + 1 if month < 12 else 1
            deadlines.append(
                FilingDeadline(
                    form_code="A-melding",
                    label=f"A-melding — {year}-{month:02d}",
                    due_date=date(due_year, due_month, 5),
                    covers_period=f"{year}-{month:02d}",
                    endpoint="Altinn",
                )
            )

        return sorted(deadlines, key=lambda d: d.due_date)

    def public_holidays(self, year: int) -> list[PublicHoliday]:
        """
        Norwegian public holidays (fixed-date subset — Easter-based ones
        need dateutil.easter in a production build).
        """
        return [
            PublicHoliday(date(year, 1, 1), "Første nyttårsdag", "NO"),
            PublicHoliday(date(year, 5, 1), "Arbeidernes dag", "NO"),
            PublicHoliday(date(year, 5, 17), "Grunnlovsdag", "NO"),
            PublicHoliday(date(year, 12, 25), "Første juledag", "NO"),
            PublicHoliday(date(year, 12, 26), "Andre juledag", "NO"),
            # Easter-based (Skjærtorsdag, Langfredag, Påskedag, 2. påskedag,
            # Kristi himmelfartsdag, Pinsedag, 2. pinsedag) computed in
            # the full implementation using dateutil.easter.
        ]

    # ── Chart of accounts ───────────────────────────────────────────────

    def coa_template(self, industry_vertical: str | None) -> list[AccountTemplate]:
        """
        Minimal NS 4102-aligned account set. Full NS 4102 has hundreds of
        accounts — this skeleton covers the essentials so a journal engine
        can run. Extend per vertical (hospitality, construction, etc.).
        """
        base: list[AccountTemplate] = [
            # 1xxx — assets
            AccountTemplate("1200", "Maskiner og anlegg", "Machinery and plant", "asset", "non_current_asset"),
            AccountTemplate("1500", "Kundefordringer", "Accounts receivable", "asset", "current_asset"),
            AccountTemplate("1920", "Bankinnskudd", "Bank deposits", "asset", "current_asset"),
            # 2xxx — equity & liabilities
            AccountTemplate("2000", "Aksjekapital", "Share capital", "equity", "equity"),
            AccountTemplate("2050", "Annen egenkapital", "Retained earnings", "equity", "equity"),
            AccountTemplate("2400", "Leverandørgjeld", "Accounts payable", "liability", "current_liability"),
            AccountTemplate("2700", "Utgående merverdiavgift", "VAT output", "liability", "current_liability"),
            AccountTemplate("2710", "Inngående merverdiavgift", "VAT input", "asset", "current_asset"),
            AccountTemplate("2770", "Skyldig skattetrekk", "PAYE payable", "liability", "current_liability"),
            AccountTemplate("2780", "Skyldig arbeidsgiveravgift", "Employer NI payable", "liability", "current_liability"),
            # 3xxx — revenue
            AccountTemplate("3000", "Salgsinntekt, avgiftspliktig", "Sales revenue, taxable", "revenue", "operating_revenue"),
            AccountTemplate("3100", "Salgsinntekt, avgiftsfri", "Sales revenue, exempt", "revenue", "operating_revenue"),
            # 4xxx — cost of sales
            AccountTemplate("4000", "Varekjøp", "Purchases", "expense", "cost_of_sales"),
            # 5xxx — payroll
            AccountTemplate("5000", "Lønn til ansatte", "Salaries and wages", "expense", "operating_expense"),
            AccountTemplate("5400", "Arbeidsgiveravgift", "Employer NI", "expense", "operating_expense"),
            AccountTemplate("5900", "Feriepenger", "Holiday pay", "expense", "operating_expense"),
            # 6xxx — other operating costs
            AccountTemplate("6300", "Leie lokaler", "Rent of premises", "expense", "operating_expense"),
            AccountTemplate("6810", "Kontorutstyr", "Office supplies", "expense", "operating_expense"),
            # 8xxx — financial
            AccountTemplate("8051", "Renteinntekter bank", "Interest income", "revenue", "financial_income"),
            AccountTemplate("8150", "Rentekostnader", "Interest expense", "expense", "financial_expense"),
        ]
        # Vertical overlays will be added here in Sprint 18+
        return base

    # ── Forms ───────────────────────────────────────────────────────────

    def statutory_forms(self) -> list[StatutoryForm]:
        return [
            StatutoryForm(
                code="MVA-melding",
                label="VAT return",
                description="Merverdiavgiftsmelding — bimonthly VAT return via Altinn",
                frequency="bimonthly",
                endpoint="Altinn",
            ),
            StatutoryForm(
                code="A-melding",
                label="Payroll & employment report",
                description="Monthly report of salaries, deductions, and employment "
                            "to Skatteetaten and NAV via Altinn",
                frequency="monthly",
                endpoint="Altinn",
            ),
            StatutoryForm(
                code="Næringsoppgave",
                label="Business specification",
                description="Annual business accounts, filed with income tax return",
                frequency="annual",
                endpoint="Altinn",
            ),
            StatutoryForm(
                code="RF-1167",
                label="Annual payroll and benefits",
                description="Annual employee income statement reconciliation",
                frequency="annual",
                endpoint="Altinn",
            ),
        ]

    # ── Validation & banking ────────────────────────────────────────────

    def validate_vat_number(self, vat_number: str) -> bool:
        """
        Norwegian organisasjonsnummer: 9 digits + mod-11 checksum.
        Optionally followed by " MVA" to indicate VAT registration.
        """
        cleaned = vat_number.strip().upper().replace(" ", "").replace("MVA", "")
        if not (cleaned.isdigit() and len(cleaned) == 9):
            return False
        weights = (3, 2, 7, 6, 5, 4, 3, 2)
        s = sum(int(cleaned[i]) * weights[i] for i in range(8))
        remainder = s % 11
        if remainder == 0:
            check = 0
        elif remainder == 1:
            return False  # no valid check digit
        else:
            check = 11 - remainder
        return check == int(cleaned[8])

    def bank_format(self) -> BankFormat:
        return BankFormat(
            country_code="NO",
            iban_prefix="NO",
            iban_length=15,  # NO + 2 check + 11 BBAN
            domestic_format="11 digits, typically formatted NNNN NN NNNNN",
            payment_file_format="Nordic PAIN / ISO 20022 / SEPA for EUR",
            open_banking_provider="Aiia",
        )
