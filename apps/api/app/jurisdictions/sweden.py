"""
Sweden jurisdiction module.

Sources:
- VAT rates: Skatteverket (moms)
- Payroll: Skatteverket (arbetsgivaravgifter, A-skatt), AGD monthly declaration
- Public holidays: svenska helgdagar
- Bank format: clearing number + account, IBAN SExx

All rates verified as of January 2026.
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


class SwedenJurisdiction(JurisdictionBase):
    country_code = "SE"
    country_name = "Sweden"

    def currency(self) -> str:
        return "SEK"

    def language(self) -> str:
        return "sv-SE"

    # ── VAT ──────────────────────────────────────────────────────────────

    def vat_rates(self, on_date: date) -> list[VatRate]:
        return [
            VatRate(
                code="SE-25",
                label="Standardskattesats",
                rate=Decimal("0.25"),
                category="standard",
                applies_to="Most goods and services",
                effective_from=date(1990, 1, 1),
            ),
            VatRate(
                code="SE-12",
                label="Reducerad skattesats (12%)",
                rate=Decimal("0.12"),
                category="reduced",
                applies_to="Food, non-alcoholic restaurant & hotel services",
                effective_from=date(2012, 1, 1),
            ),
            VatRate(
                code="SE-6",
                label="Reducerad skattesats (6%)",
                rate=Decimal("0.06"),
                category="reduced",
                applies_to="Books, newspapers, public transport, cultural events",
                effective_from=date(2002, 1, 1),
            ),
            VatRate(
                code="SE-0",
                label="Noll moms",
                rate=Decimal("0.00"),
                category="zero",
                applies_to="Exports, intra-EU supplies with valid VAT numbers",
                effective_from=date(1995, 1, 1),
            ),
        ]

    def vat_filing_frequency(self) -> str:
        # Large companies: monthly. Medium: quarterly. Small: annual.
        # This returns the default for a mid-sized bureau client.
        return "monthly"

    # ── Payroll ─────────────────────────────────────────────────────────

    def payroll_rules(self, employee_type: str, on_date: date) -> PayrollRules:
        """
        Swedish payroll rules — 2026 rates.
        arbetsgivaravgifter standard rate 31.42%; reduced 10.21% for under-23
        and over-65. Pick the right rate from employee's date of birth in the
        actual payroll engine.
        """
        return PayrollRules(
            country_code="SE",
            effective_on=on_date,
            currency="SEK",
            employer_contributions=[
                PayrollDeduction(
                    code="ARBGAV",
                    label="Arbetsgivaravgifter (standard)",
                    rate=Decimal("0.3142"),
                    base="gross",
                    paid_by="employer",
                    notes="Full rate 31.42% for employees aged 23-65. Reduced "
                          "rate 10.21% for under-23 and over-65. Rate applied "
                          "per employee in the engine.",
                ),
                PayrollDeduction(
                    code="ITP1",
                    label="Tjänstepension (ITP1)",
                    rate=Decimal("0.045"),
                    base="capped",
                    paid_by="employer",
                    notes="Default occupational pension — ITP1 4.5% below 7.5 "
                          "income base amounts, 30% above. Rate varies by "
                          "collective agreement (ITP1, ITP2, SAF-LO, PA 16, "
                          "AKAP). Store agreement type per employee.",
                ),
            ],
            employee_deductions=[
                PayrollDeduction(
                    code="PRELIMINAR_SKATT",
                    label="Preliminärskatt (A-skatt)",
                    rate=None,
                    base="taxable",
                    paid_by="employee",
                    notes="Personalised withholding per employee's skattsedel. "
                          "Use Skatteverket tax tables or jämkningsbeslut.",
                ),
            ],
            holiday_pay_rate=Decimal("0.12"),   # semesterlön 12% of gross
            sick_pay_employer_days=14,          # employer pays days 2-14 (day 1 = karensdag)
            reporting_frequency="monthly",
            reporting_endpoint="Skatteverket AGD (arbetsgivardeklaration)",
            notes="KU (kontrolluppgift) filed annually in January. "
                  "BankID e-signing commonly used for approval flows.",
        )

    # ── Calendars ───────────────────────────────────────────────────────

    def filing_calendar(self, year: int) -> list[FilingDeadline]:
        deadlines: list[FilingDeadline] = []

        # Monthly VAT (momsdeklaration) — due 26th of month + 2
        for month in range(1, 13):
            due_month = month + 2
            due_year = year + (1 if due_month > 12 else 0)
            due_month = ((due_month - 1) % 12) + 1
            deadlines.append(
                FilingDeadline(
                    form_code="Moms",
                    label=f"Momsdeklaration — {year}-{month:02d}",
                    due_date=date(due_year, due_month, 26),
                    covers_period=f"{year}-{month:02d}",
                    endpoint="Skatteverket",
                )
            )

        # Monthly AGD (arbetsgivardeklaration) — due 12th of following month
        for month in range(1, 13):
            due_month = month + 1
            due_year = year + (1 if due_month > 12 else 0)
            due_month = ((due_month - 1) % 12) + 1
            deadlines.append(
                FilingDeadline(
                    form_code="AGD",
                    label=f"Arbetsgivardeklaration — {year}-{month:02d}",
                    due_date=date(due_year, due_month, 12),
                    covers_period=f"{year}-{month:02d}",
                    endpoint="Skatteverket",
                )
            )

        # Annual KU — 31 January of following year
        deadlines.append(
            FilingDeadline(
                form_code="KU",
                label=f"Kontrolluppgift — {year}",
                due_date=date(year + 1, 1, 31),
                covers_period=str(year),
                endpoint="Skatteverket",
            )
        )

        return sorted(deadlines, key=lambda d: d.due_date)

    def public_holidays(self, year: int) -> list[PublicHoliday]:
        return [
            PublicHoliday(date(year, 1, 1), "Nyårsdagen", "SE"),
            PublicHoliday(date(year, 1, 6), "Trettondedag jul", "SE"),
            PublicHoliday(date(year, 5, 1), "Första maj", "SE"),
            PublicHoliday(date(year, 6, 6), "Sveriges nationaldag", "SE"),
            PublicHoliday(date(year, 12, 25), "Juldagen", "SE"),
            PublicHoliday(date(year, 12, 26), "Annandag jul", "SE"),
            # Easter-based (Långfredagen, Påskdagen, Annandag påsk, Pingstdagen,
            # Kristi himmelsfärdsdag) computed with dateutil.easter in production.
            # Midsommardagen (Saturday between 20-26 June) also skipped here.
        ]

    # ── Chart of accounts ───────────────────────────────────────────────

    def coa_template(self, industry_vertical: str | None) -> list[AccountTemplate]:
        """
        Minimal BAS 2024-aligned account set. Full BAS has 2000+ accounts.
        Extend per vertical.
        """
        base: list[AccountTemplate] = [
            # 1xxx — assets
            AccountTemplate("1220", "Inventarier", "Fixtures and fittings", "asset", "non_current_asset"),
            AccountTemplate("1510", "Kundfordringar", "Accounts receivable", "asset", "current_asset"),
            AccountTemplate("1930", "Företagskonto / checkräkning", "Bank account", "asset", "current_asset"),
            # 2xxx — equity & liabilities
            AccountTemplate("2081", "Aktiekapital", "Share capital", "equity", "equity"),
            AccountTemplate("2091", "Balanserad vinst eller förlust", "Retained earnings", "equity", "equity"),
            AccountTemplate("2440", "Leverantörsskulder", "Accounts payable", "liability", "current_liability"),
            AccountTemplate("2611", "Utgående moms 25%", "VAT output 25%", "liability", "current_liability"),
            AccountTemplate("2641", "Ingående moms", "VAT input", "asset", "current_asset"),
            AccountTemplate("2710", "Personalskatt", "Employee tax withheld", "liability", "current_liability"),
            AccountTemplate("2731", "Avräkning lagstadgade sociala avgifter", "Employer social security", "liability", "current_liability"),
            # 3xxx — revenue
            AccountTemplate("3001", "Försäljning inom Sverige, 25%", "Sales Sweden 25% VAT", "revenue", "operating_revenue"),
            AccountTemplate("3002", "Försäljning inom Sverige, 12%", "Sales Sweden 12% VAT", "revenue", "operating_revenue"),
            AccountTemplate("3105", "Försäljning varor till land utanför EU", "Sales outside EU", "revenue", "operating_revenue"),
            # 4xxx — materials and services
            AccountTemplate("4010", "Inköp material och varor", "Purchases", "expense", "cost_of_sales"),
            # 5xxx/6xxx — other expenses
            AccountTemplate("5010", "Lokalhyra", "Rent of premises", "expense", "operating_expense"),
            AccountTemplate("6110", "Kontorsmateriel", "Office supplies", "expense", "operating_expense"),
            # 7xxx — personnel
            AccountTemplate("7010", "Löner till kollektivanställda", "Wages", "expense", "operating_expense"),
            AccountTemplate("7210", "Löner till tjänstemän", "Salaries", "expense", "operating_expense"),
            AccountTemplate("7510", "Arbetsgivaravgifter", "Employer contributions", "expense", "operating_expense"),
            AccountTemplate("7570", "Premier för tjänstepensioner", "Occupational pension", "expense", "operating_expense"),
            # 8xxx — financial
            AccountTemplate("8310", "Ränteintäkter", "Interest income", "revenue", "financial_income"),
            AccountTemplate("8410", "Räntekostnader", "Interest expense", "expense", "financial_expense"),
        ]
        return base

    # ── Forms ───────────────────────────────────────────────────────────

    def statutory_forms(self) -> list[StatutoryForm]:
        return [
            StatutoryForm(
                code="Moms",
                label="VAT return (momsdeklaration)",
                description="Monthly/quarterly/annual VAT return to Skatteverket",
                frequency="monthly",
                endpoint="Skatteverket",
            ),
            StatutoryForm(
                code="AGD",
                label="Employer declaration",
                description="Monthly arbetsgivardeklaration to Skatteverket "
                            "(replaced KU + arbetsgivarinbetalning in 2019)",
                frequency="monthly",
                endpoint="Skatteverket",
            ),
            StatutoryForm(
                code="KU",
                label="Annual income statement",
                description="Annual kontrolluppgift per employee, filed January",
                frequency="annual",
                endpoint="Skatteverket",
            ),
            StatutoryForm(
                code="INK2",
                label="Corporate tax return",
                description="Annual income declaration 2 (inkomstdeklaration)",
                frequency="annual",
                endpoint="Skatteverket",
            ),
        ]

    # ── Validation & banking ────────────────────────────────────────────

    def validate_vat_number(self, vat_number: str) -> bool:
        """
        Swedish VAT number: SE + 10 digits + 01 suffix = 12 digits total.
        The 10-digit part is the organisationsnummer. Modulus-10 / Luhn check.
        """
        cleaned = vat_number.strip().upper()
        if cleaned.startswith("SE"):
            cleaned = cleaned[2:]
        if not cleaned.isdigit() or len(cleaned) != 12:
            return False
        if not cleaned.endswith("01"):
            return False
        org_no = cleaned[:10]
        # Luhn check on 10-digit organisationsnummer
        total = 0
        for i, d in enumerate(org_no):
            n = int(d) * (2 if i % 2 == 0 else 1)
            if n > 9:
                n -= 9
            total += n
        return total % 10 == 0

    def bank_format(self) -> BankFormat:
        return BankFormat(
            country_code="SE",
            iban_prefix="SE",
            iban_length=24,
            domestic_format="Clearing number (4 digits) + account number",
            payment_file_format="Bankgirot / ISO 20022",
            open_banking_provider="Tink / Aiia",
        )
