"""
Nordic accounting configuration — VAT rates, org number validation,
and chart of accounts templates for Norway and Sweden.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


# ── VAT Rate Tables ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class VATRate:
    code: str
    rate: Decimal
    label_no: str
    label_en: str
    label_sv: str

NO_VAT_RATES: list[VATRate] = [
    VATRate("NO_HIGH",    Decimal("25"), "Høy sats (25 %)",          "Standard rate (25%)",       "Hög sats (25 %)"),
    VATRate("NO_FOOD",    Decimal("15"), "Mat og drikke (15 %)",     "Food & beverage (15%)",     "Mat och dryck (15 %)"),
    VATRate("NO_LOW",     Decimal("12"), "Lav sats (12 %)",          "Low rate (12%)",            "Låg sats (12 %)"),
    VATRate("NO_SUPER",   Decimal("6"),  "Superredusert (6 %)",      "Super-reduced (6%)",        "Superreducerad (6 %)"),
    VATRate("NO_ZERO",    Decimal("0"),  "Fritatt (0 %)",            "Exempt (0%)",               "Momsfritt (0 %)"),
]

SE_VAT_RATES: list[VATRate] = [
    VATRate("SE_HIGH",    Decimal("25"), "Høy sats (25 %)",          "Standard rate (25%)",       "Hög moms (25 %)"),
    VATRate("SE_FOOD",    Decimal("12"), "Mat og drikke (12 %)",     "Food & beverage (12%)",     "Mat och dryck (12 %)"),
    VATRate("SE_LOW",     Decimal("6"),  "Lav sats (6 %)",           "Low rate (6%)",             "Låg moms (6 %)"),
    VATRate("SE_ZERO",    Decimal("0"),  "Fritatt (0 %)",            "Exempt (0%)",               "Momsfritt (0 %)"),
]

VAT_RATES_BY_COUNTRY: dict[str, list[VATRate]] = {
    "NO": NO_VAT_RATES,
    "SE": SE_VAT_RATES,
}

def get_vat_rates(country: str) -> list[VATRate]:
    return VAT_RATES_BY_COUNTRY.get(country.upper(), NO_VAT_RATES)

def get_default_vat_rate(country: str) -> Decimal:
    rates = get_vat_rates(country)
    return rates[0].rate if rates else Decimal("25")

def vat_rate_options(country: str, locale: str = "en") -> list[dict]:
    """Return VAT rates as JSON-friendly dicts for frontend selectors."""
    label_key = {
        "no": "label_no",
        "nb": "label_no",
        "sv": "label_sv",
    }.get(locale, "label_en")

    return [
        {"code": r.code, "rate": str(r.rate), "label": getattr(r, label_key)}
        for r in get_vat_rates(country)
    ]


# ── Org Number Validation ───────────────────────────────────────────────────

@dataclass
class OrgNumberResult:
    valid: bool
    formatted: str
    error: Optional[str] = None

def validate_no_org_number(raw: str) -> OrgNumberResult:
    """
    Validate a Norwegian organization number (9 digits, mod-11 check).
    Accepts formats: 123456789, 123 456 789, NO123456789MVA
    """
    cleaned = re.sub(r"[^0-9]", "", raw.replace("MVA", "").replace("mva", ""))

    if len(cleaned) != 9:
        return OrgNumberResult(False, raw, "Organisasjonsnummer må ha 9 siffer")

    weights = [3, 2, 7, 6, 5, 4, 3, 2]
    digits = [int(d) for d in cleaned]

    checksum = sum(d * w for d, w in zip(digits[:8], weights))
    remainder = 11 - (checksum % 11)
    if remainder == 11:
        remainder = 0

    if remainder == 10 or remainder != digits[8]:
        return OrgNumberResult(False, raw, "Ugyldig kontrollsiffer")

    formatted = f"{cleaned[:3]} {cleaned[3:6]} {cleaned[6:9]}"
    return OrgNumberResult(True, formatted)

def validate_se_org_number(raw: str) -> OrgNumberResult:
    """
    Validate a Swedish organization number (10 digits, Luhn check on digits 1-10).
    Accepts formats: 5566778899, 556677-8899, SE556677889901
    """
    cleaned = raw.upper().replace("SE", "").replace(" ", "").replace("-", "")
    if cleaned.endswith("01"):
        cleaned = cleaned[:-2]

    if len(cleaned) != 10 or not cleaned.isdigit():
        return OrgNumberResult(False, raw, "Organisationsnummer måste ha 10 siffror")

    digits = [int(d) for d in cleaned]
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 0:
            doubled = d * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += d

    if total % 10 != 0:
        return OrgNumberResult(False, raw, "Ogiltigt kontrollnummer")

    formatted = f"{cleaned[:6]}-{cleaned[6:]}"
    return OrgNumberResult(True, formatted)

def validate_org_number(raw: str, country: str) -> OrgNumberResult:
    """Dispatch to country-specific validator."""
    validators = {
        "NO": validate_no_org_number,
        "SE": validate_se_org_number,
    }
    validator = validators.get(country.upper())
    if not validator:
        return OrgNumberResult(True, raw)
    return validator(raw)


# ── Chart of Accounts Templates ─────────────────────────────────────────────

@dataclass(frozen=True)
class AccountTemplate:
    code: str
    name_no: str
    name_en: str
    name_sv: str
    type: str          # asset, liability, equity, revenue, expense
    vat_code: str      # default VAT code for this account, or ""
    parent_code: str   # parent account code for grouping, or ""

# NS 4102 (Norway) — standard chart of accounts for SMB
# Focused on hospitality-relevant accounts
NS4102_ACCOUNTS: list[AccountTemplate] = [
    # 1xxx — Assets (Eiendeler)
    AccountTemplate("1000", "Eiendeler",              "Assets",                  "Tillgångar",              "asset",     "",        ""),
    AccountTemplate("1200", "Maskiner og inventar",   "Machinery & equipment",   "Maskiner och inventarier","asset",     "",        "1000"),
    AccountTemplate("1500", "Kundefordringer",        "Accounts receivable",     "Kundfordringar",         "asset",     "",        "1000"),
    AccountTemplate("1900", "Bankinnskudd",           "Bank deposits",           "Banktillgodohavanden",   "asset",     "",        "1000"),
    AccountTemplate("1910", "Driftskonto",            "Operating account",       "Driftskonto",            "asset",     "",        "1900"),
    AccountTemplate("1920", "Skattetrekkskonto",      "Tax withholding account", "Skattekonto",            "asset",     "",        "1900"),

    # 2xxx — Liabilities (Gjeld) & Equity (Egenkapital)
    AccountTemplate("2000", "Egenkapital og gjeld",   "Equity & liabilities",    "Eget kapital och skulder","liability", "",        ""),
    AccountTemplate("2400", "Leverandørgjeld",        "Accounts payable",        "Leverantörsskulder",     "liability", "",        "2000"),
    AccountTemplate("2600", "Skattetrekk",            "Tax withholdings",        "Skatteavdrag",           "liability", "",        "2000"),
    AccountTemplate("2700", "Skyldig MVA",            "VAT payable",             "Moms att betala",        "liability", "",        "2000"),
    AccountTemplate("2710", "Inngående MVA",          "Input VAT",               "Ingående moms",         "liability", "",        "2700"),
    AccountTemplate("2720", "Utgående MVA",           "Output VAT",              "Utgående moms",         "liability", "",        "2700"),
    AccountTemplate("2740", "Oppgjørskonto MVA",      "VAT settlement",          "Momsredovisning",       "liability", "",        "2700"),

    # 3xxx — Revenue (Inntekter)
    AccountTemplate("3000", "Salgsinntekter",         "Sales revenue",           "Försäljningsintäkter",   "revenue",   "NO_HIGH", ""),
    AccountTemplate("3010", "Romsinntekter",          "Room revenue",            "Rumsintäkter",           "revenue",   "NO_HIGH", "3000"),
    AccountTemplate("3020", "Mat- og drikkeinntekter","F&B revenue",             "Mat- och dryckesintäkter","revenue",  "NO_FOOD", "3000"),
    AccountTemplate("3030", "Konferanseinntekter",    "Conference revenue",      "Konferensintäkter",      "revenue",   "NO_HIGH", "3000"),
    AccountTemplate("3040", "Andre inntekter",        "Other revenue",           "Övriga intäkter",        "revenue",   "NO_HIGH", "3000"),
    AccountTemplate("3400", "Offentlig tilskudd",     "Public grants",           "Offentliga bidrag",      "revenue",   "NO_ZERO", "3000"),

    # 4xxx — Cost of goods (Varekostnad)
    AccountTemplate("4000", "Varekostnad",            "Cost of goods",           "Varukostnad",            "expense",   "NO_HIGH", ""),
    AccountTemplate("4010", "Varekostnad mat",        "Food cost",               "Varukostnad mat",        "expense",   "NO_FOOD", "4000"),
    AccountTemplate("4020", "Varekostnad drikke",     "Beverage cost",           "Varukostnad dryck",      "expense",   "NO_FOOD", "4000"),
    AccountTemplate("4300", "Innkjøp av varer",       "Purchases",               "Inköp av varor",         "expense",   "NO_HIGH", "4000"),

    # 5xxx — Payroll (Lønnskostnad)
    AccountTemplate("5000", "Lønnskostnader",         "Payroll costs",           "Lönekostnader",          "expense",   "",        ""),
    AccountTemplate("5010", "Lønn",                   "Salaries",                "Löner",                  "expense",   "",        "5000"),
    AccountTemplate("5090", "Feriepenger",            "Vacation pay",            "Semesterlön",            "expense",   "",        "5000"),
    AccountTemplate("5400", "Arbeidsgiveravgift",     "Employer NI contributions","Arbetsgivaravgifter",   "expense",   "",        "5000"),

    # 6xxx — Operating expenses (Driftskostnader)
    AccountTemplate("6000", "Driftskostnader",        "Operating expenses",      "Driftskostnader",        "expense",   "NO_HIGH", ""),
    AccountTemplate("6100", "Frakt og transport",     "Freight & transport",     "Frakt och transport",    "expense",   "NO_HIGH", "6000"),
    AccountTemplate("6200", "Leie lokaler",           "Rent",                    "Hyra lokaler",           "expense",   "NO_ZERO", "6000"),
    AccountTemplate("6300", "Energikostnader",        "Energy costs",            "Energikostnader",        "expense",   "NO_HIGH", "6000"),
    AccountTemplate("6400", "Vedlikehold",            "Maintenance",             "Underhåll",              "expense",   "NO_HIGH", "6000"),
    AccountTemplate("6500", "Verktøy og inventar",    "Tools & equipment",       "Verktyg och inventarier","expense",   "NO_HIGH", "6000"),
    AccountTemplate("6700", "Regnskap og revisjon",   "Accounting & audit",      "Redovisning och revision","expense",  "NO_HIGH", "6000"),
    AccountTemplate("6800", "Kontorkostnader",        "Office costs",            "Kontorskostnader",       "expense",   "NO_HIGH", "6000"),
    AccountTemplate("6900", "Telefon og internett",   "Phone & internet",        "Telefon och internet",   "expense",   "NO_HIGH", "6000"),

    # 7xxx — Other operating (Andre driftskostnader)
    AccountTemplate("7000", "Andre driftskostnader",  "Other operating costs",   "Övriga driftskostnader", "expense",   "NO_HIGH", ""),
    AccountTemplate("7100", "Bilkostnader",           "Vehicle costs",           "Bilkostnader",           "expense",   "NO_HIGH", "7000"),
    AccountTemplate("7300", "Markedsføring",          "Marketing",               "Marknadsföring",         "expense",   "NO_HIGH", "7000"),
    AccountTemplate("7400", "Forsikring",             "Insurance",               "Försäkring",             "expense",   "NO_ZERO", "7000"),
    AccountTemplate("7700", "Bankgebyrer",            "Bank fees",               "Bankavgifter",           "expense",   "NO_ZERO", "7000"),

    # 8xxx — Financial items
    AccountTemplate("8000", "Finansposter",           "Financial items",         "Finansiella poster",     "expense",   "",        ""),
    AccountTemplate("8040", "Renteinntekt",           "Interest income",         "Ränteintäkter",          "revenue",   "",        "8000"),
    AccountTemplate("8140", "Rentekostnad",           "Interest expense",        "Räntekostnader",         "expense",   "",        "8000"),
    AccountTemplate("8170", "Valutagevinst/-tap",     "Currency gain/loss",      "Valutavinst/-förlust",   "expense",   "",        "8000"),
]

# BAS 2024 (Sweden) — standard chart of accounts
# Focused on hospitality-relevant accounts
BAS2024_ACCOUNTS: list[AccountTemplate] = [
    # 1xxx — Tillgångar
    AccountTemplate("1000", "Tillgångar",                "Assets",                  "Tillgångar",              "asset",     "",        ""),
    AccountTemplate("1200", "Maskiner och inventarier",  "Machinery & equipment",   "Maskiner och inventarier","asset",     "",        "1000"),
    AccountTemplate("1500", "Kundfordringar",            "Accounts receivable",     "Kundfordringar",         "asset",     "",        "1000"),
    AccountTemplate("1900", "Kassa och bank",            "Cash & bank",             "Kassa och bank",         "asset",     "",        "1000"),
    AccountTemplate("1910", "Företagskonto",             "Operating account",       "Företagskonto",          "asset",     "",        "1900"),
    AccountTemplate("1920", "Skattekonto",               "Tax account",             "Skattekonto",            "asset",     "",        "1900"),

    # 2xxx — Eget kapital och skulder
    AccountTemplate("2000", "Eget kapital och skulder",  "Equity & liabilities",    "Eget kapital och skulder","liability", "",       ""),
    AccountTemplate("2400", "Leverantörsskulder",        "Accounts payable",        "Leverantörsskulder",     "liability", "",        "2000"),
    AccountTemplate("2600", "Skatteskulder",             "Tax liabilities",         "Skatteskulder",          "liability", "",        "2000"),
    AccountTemplate("2610", "Utgående moms 25 %",        "Output VAT 25%",          "Utgående moms 25 %",    "liability", "SE_HIGH", "2600"),
    AccountTemplate("2620", "Utgående moms 12 %",        "Output VAT 12%",          "Utgående moms 12 %",    "liability", "SE_FOOD", "2600"),
    AccountTemplate("2630", "Utgående moms 6 %",         "Output VAT 6%",           "Utgående moms 6 %",     "liability", "SE_LOW",  "2600"),
    AccountTemplate("2640", "Ingående moms",             "Input VAT",               "Ingående moms",         "liability", "",        "2600"),
    AccountTemplate("2650", "Momsredovisning",           "VAT settlement",          "Momsredovisning",       "liability", "",        "2600"),

    # 3xxx — Intäkter
    AccountTemplate("3000", "Försäljningsintäkter",      "Sales revenue",           "Försäljningsintäkter",   "revenue",   "SE_HIGH", ""),
    AccountTemplate("3010", "Rumsintäkter",              "Room revenue",            "Rumsintäkter",           "revenue",   "SE_HIGH", "3000"),
    AccountTemplate("3020", "Mat- och dryckesintäkter",  "F&B revenue",             "Mat- och dryckesintäkter","revenue",  "SE_FOOD", "3000"),
    AccountTemplate("3030", "Konferensintäkter",         "Conference revenue",      "Konferensintäkter",      "revenue",   "SE_HIGH", "3000"),
    AccountTemplate("3040", "Övriga intäkter",           "Other revenue",           "Övriga intäkter",        "revenue",   "SE_HIGH", "3000"),

    # 4xxx — Varukostnad
    AccountTemplate("4000", "Varukostnad",               "Cost of goods",           "Varukostnad",            "expense",   "SE_HIGH", ""),
    AccountTemplate("4010", "Varukostnad mat",           "Food cost",               "Varukostnad mat",        "expense",   "SE_FOOD", "4000"),
    AccountTemplate("4020", "Varukostnad dryck",         "Beverage cost",           "Varukostnad dryck",      "expense",   "SE_FOOD", "4000"),

    # 5xxx — Lönekostnader
    AccountTemplate("5000", "Lönekostnader",             "Payroll costs",           "Lönekostnader",          "expense",   "",        ""),
    AccountTemplate("5010", "Löner",                     "Salaries",                "Löner",                  "expense",   "",        "5000"),
    AccountTemplate("5090", "Semesterlöneskuld",         "Vacation pay liability",  "Semesterlöneskuld",      "expense",   "",        "5000"),
    AccountTemplate("5400", "Arbetsgivaravgifter",       "Employer contributions",  "Arbetsgivaravgifter",    "expense",   "",        "5000"),

    # 6xxx — Övriga externa kostnader
    AccountTemplate("6000", "Övriga externa kostnader",  "Other external costs",    "Övriga externa kostnader","expense",  "SE_HIGH", ""),
    AccountTemplate("6100", "Frakt och transport",       "Freight & transport",     "Frakt och transport",    "expense",   "SE_HIGH", "6000"),
    AccountTemplate("6200", "Hyra lokaler",              "Rent",                    "Hyra lokaler",           "expense",   "SE_ZERO", "6000"),
    AccountTemplate("6300", "Energikostnader",           "Energy costs",            "Energikostnader",        "expense",   "SE_HIGH", "6000"),
    AccountTemplate("6400", "Reparation och underhåll",  "Maintenance",             "Reparation och underhåll","expense",  "SE_HIGH", "6000"),
    AccountTemplate("6500", "Förbrukningsinventarier",   "Consumables",             "Förbrukningsinventarier","expense",   "SE_HIGH", "6000"),
    AccountTemplate("6700", "Redovisning och revision",  "Accounting & audit",      "Redovisning och revision","expense",  "SE_HIGH", "6000"),
    AccountTemplate("6800", "Kontorsmaterial",           "Office supplies",         "Kontorsmaterial",        "expense",   "SE_HIGH", "6000"),
    AccountTemplate("6900", "Telefon och internet",      "Phone & internet",        "Telefon och internet",   "expense",   "SE_HIGH", "6000"),

    # 7xxx — Övriga driftskostnader
    AccountTemplate("7000", "Övriga driftskostnader",    "Other operating costs",   "Övriga driftskostnader", "expense",   "SE_HIGH", ""),
    AccountTemplate("7100", "Bilkostnader",              "Vehicle costs",           "Bilkostnader",           "expense",   "SE_HIGH", "7000"),
    AccountTemplate("7300", "Marknadsföring",            "Marketing",               "Marknadsföring",         "expense",   "SE_HIGH", "7000"),
    AccountTemplate("7400", "Försäkringar",              "Insurance",               "Försäkringar",           "expense",   "SE_ZERO", "7000"),
    AccountTemplate("7700", "Bankavgifter",              "Bank fees",               "Bankavgifter",           "expense",   "SE_ZERO", "7000"),

    # 8xxx — Finansiella poster
    AccountTemplate("8000", "Finansiella poster",        "Financial items",         "Finansiella poster",     "expense",   "",        ""),
    AccountTemplate("8300", "Ränteintäkter",             "Interest income",         "Ränteintäkter",          "revenue",   "",        "8000"),
    AccountTemplate("8400", "Räntekostnader",            "Interest expense",        "Räntekostnader",         "expense",   "",        "8000"),
    AccountTemplate("8490", "Valutakursvinst/-förlust",  "Currency gain/loss",      "Valutakursvinst/-förlust","expense",  "",        "8000"),
]

COA_TEMPLATES: dict[str, list[AccountTemplate]] = {
    "NO": NS4102_ACCOUNTS,
    "SE": BAS2024_ACCOUNTS,
}

def get_coa_template(country: str) -> list[AccountTemplate]:
    return COA_TEMPLATES.get(country.upper(), NS4102_ACCOUNTS)

def coa_as_dicts(country: str, locale: str = "en") -> list[dict]:
    """Return COA template as JSON-friendly dicts."""
    name_key = {
        "no": "name_no",
        "nb": "name_no",
        "sv": "name_sv",
    }.get(locale, "name_en")

    return [
        {
            "code": a.code,
            "name": getattr(a, name_key),
            "type": a.type,
            "vat_code": a.vat_code,
            "parent_code": a.parent_code,
        }
        for a in get_coa_template(country)
    ]
