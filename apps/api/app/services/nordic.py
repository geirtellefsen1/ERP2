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

# NS 4102 (Norway) — Hotel kontoplan
# Follows standard Norwegian accounting practice with hospitality-specific
# department splits (Tripletex/Regnskapsprofeten hotel template).
# VAT rates:
#   12% (lav) — overnatting (rom), persontransport
#   15% (middels) — mat og drikke servert i restaurant
#   25% (høy) — alkohol, minibar, spa, konferanse, suvenirer
NS4102_ACCOUNTS: list[AccountTemplate] = [
    # 1xxx — Eiendeler
    AccountTemplate("1000", "Eiendeler",                 "Assets",                    "Tillgångar",                "asset",     "",        ""),
    AccountTemplate("1115", "Tomter",                    "Land",                      "Tomter",                    "asset",     "",        "1000"),
    AccountTemplate("1117", "Bygg — hotell",             "Buildings — hotel",         "Byggnad — hotell",          "asset",     "",        "1000"),
    AccountTemplate("1200", "Maskiner og anlegg",        "Machinery & installations", "Maskiner och anläggningar", "asset",     "",        "1000"),
    AccountTemplate("1250", "Inventar",                  "Furniture & fittings",      "Inventarier",               "asset",     "",        "1000"),
    AccountTemplate("1280", "Kjøretøy",                  "Vehicles",                  "Fordon",                    "asset",     "",        "1000"),
    AccountTemplate("1460", "Varelager",                 "Inventory",                 "Varulager",                 "asset",     "",        "1000"),
    AccountTemplate("1500", "Kundefordringer",           "Accounts receivable",       "Kundfordringar",            "asset",     "",        "1000"),
    AccountTemplate("1570", "Andre fordringer",          "Other receivables",         "Övriga fordringar",         "asset",     "",        "1000"),
    AccountTemplate("1614", "Inngående MVA lav sats",    "Input VAT low rate (12%)",  "Ingående moms låg sats",    "asset",     "",        "1000"),
    AccountTemplate("1900", "Kasse",                     "Cash on hand",              "Kassa",                     "asset",     "",        "1000"),
    AccountTemplate("1910", "Driftskonto",               "Operating account",         "Företagskonto",             "asset",     "",        "1000"),
    AccountTemplate("1920", "Skattetrekkskonto",         "Tax withholding account",   "Skattekonto",               "asset",     "",        "1000"),
    AccountTemplate("1950", "Høyrentekonto",             "Savings account",           "Sparkonto",                 "asset",     "",        "1000"),

    # 2xxx — Egenkapital
    AccountTemplate("2000", "Egenkapital",               "Equity",                    "Eget kapital",              "equity",    "",        ""),
    AccountTemplate("2010", "Aksjekapital",              "Share capital",             "Aktiekapital",              "equity",    "",        "2000"),
    AccountTemplate("2050", "Annen egenkapital",         "Retained earnings",         "Annat eget kapital",        "equity",    "",        "2000"),
    AccountTemplate("2080", "Udekket tap",               "Uncovered loss",            "Outdelade förluster",       "equity",    "",        "2000"),

    # 2xxx — Gjeld (Liabilities)
    AccountTemplate("2200", "Langsiktig gjeld",          "Long-term liabilities",     "Långfristiga skulder",      "liability", "",        ""),
    AccountTemplate("2220", "Pantelån — hotell",         "Mortgage — hotel",          "Pantlån",                   "liability", "",        "2200"),
    AccountTemplate("2240", "Billån",                    "Vehicle loan",              "Billån",                    "liability", "",        "2200"),
    AccountTemplate("2380", "Kassakreditt",              "Overdraft",                 "Checkkredit",               "liability", "",        "2200"),
    AccountTemplate("2400", "Leverandørgjeld",           "Accounts payable",          "Leverantörsskulder",        "liability", "",        ""),
    AccountTemplate("2600", "Skattetrekk",               "Tax withholdings",          "Skatteavdrag",              "liability", "",        ""),
    AccountTemplate("2700", "Skyldig MVA",               "VAT payable",               "Moms att betala",           "liability", "",        ""),
    AccountTemplate("2710", "Inngående MVA",             "Input VAT (standard)",      "Ingående moms",             "liability", "",        "2700"),
    AccountTemplate("2720", "Utgående MVA 25 %",         "Output VAT 25%",            "Utgående moms 25 %",        "liability", "NO_HIGH", "2700"),
    AccountTemplate("2725", "Utgående MVA 15 %",         "Output VAT 15%",            "Utgående moms 15 %",        "liability", "NO_FOOD", "2700"),
    AccountTemplate("2728", "Utgående MVA 12 %",         "Output VAT 12%",            "Utgående moms 12 %",        "liability", "NO_LOW",  "2700"),
    AccountTemplate("2740", "Oppgjørskonto MVA",         "VAT settlement",            "Momsredovisning",           "liability", "",        "2700"),
    AccountTemplate("2770", "Skyldig arbeidsgiveravgift","Employer NI payable",       "Arbetsgivaravgifter att betala","liability","",      ""),
    AccountTemplate("2780", "Skyldig feriepenger",       "Vacation pay liability",    "Semesterlöneskuld",         "liability", "",        ""),

    # 3xxx — Salgsinntekter, delt per avdeling
    AccountTemplate("3000", "Salgsinntekter",            "Sales revenue",             "Försäljningsintäkter",      "revenue",   "",        ""),
    AccountTemplate("3010", "Salgsinntekt rom",          "Room revenue (12%)",        "Rumsintäkter",              "revenue",   "NO_LOW",  "3000"),
    AccountTemplate("3050", "Salgsinntekt pakker",       "Package revenue (12%)",     "Paketintäkter",             "revenue",   "NO_LOW",  "3000"),
    AccountTemplate("3100", "Salgsinntekt mat",          "Food revenue (15%)",        "Matintäkter",               "revenue",   "NO_FOOD", "3000"),
    AccountTemplate("3150", "Salgsinntekt frokost",      "Breakfast revenue (15%)",   "Frukostintäkter",           "revenue",   "NO_FOOD", "3000"),
    AccountTemplate("3200", "Salgsinntekt drikke/bar",   "Beverage & bar revenue (25%)","Dryck- och barintäkter",  "revenue",   "NO_HIGH", "3000"),
    AccountTemplate("3250", "Salgsinntekt alkohol",      "Alcohol revenue (25%)",     "Alkoholintäkter",           "revenue",   "NO_HIGH", "3000"),
    AccountTemplate("3300", "Salgsinntekt minibar",      "Minibar revenue (25%)",     "Minibarintäkter",           "revenue",   "NO_HIGH", "3000"),
    AccountTemplate("3350", "Salgsinntekt vaskeri",      "Laundry revenue (25%)",     "Tvättintäkter",             "revenue",   "NO_HIGH", "3000"),
    AccountTemplate("3400", "Salgsinntekt konferanse",   "Conference revenue (25%)",  "Konferensintäkter",         "revenue",   "NO_HIGH", "3000"),
    AccountTemplate("3500", "Salgsinntekt SPA/velvære",  "SPA & wellness (25%)",      "SPA och välmående",         "revenue",   "NO_HIGH", "3000"),
    AccountTemplate("3600", "Salgsinntekt parkering",    "Parking revenue (25%)",     "Parkering",                 "revenue",   "NO_HIGH", "3000"),
    AccountTemplate("3900", "Annen driftsinntekt",       "Other operating revenue",   "Övriga rörelseintäkter",    "revenue",   "NO_HIGH", "3000"),

    # 4xxx — Varekostnad
    AccountTemplate("4000", "Varekjøp mat",              "Food purchases (15%)",      "Varuinköp mat",             "expense",   "NO_FOOD", ""),
    AccountTemplate("4010", "Varekjøp frokost",          "Breakfast purchases",       "Varuinköp frukost",         "expense",   "NO_FOOD", "4000"),
    AccountTemplate("4020", "Varekjøp drikke",           "Non-alcoholic beverages",   "Varuinköp dryck",           "expense",   "NO_FOOD", "4000"),
    AccountTemplate("4030", "Varekjøp alkohol",          "Alcohol purchases (25%)",   "Varuinköp alkohol",         "expense",   "NO_HIGH", "4000"),
    AccountTemplate("4080", "Gave og representasjon",    "Gifts & entertainment",     "Gåvor och representation",  "expense",   "NO_HIGH", "4000"),
    AccountTemplate("4100", "Varekjøp minibar",          "Minibar purchases (25%)",   "Varuinköp minibar",         "expense",   "NO_HIGH", "4000"),
    AccountTemplate("4300", "Annet varekjøp",            "Other purchases",           "Annat varuinköp",           "expense",   "NO_HIGH", "4000"),

    # 5xxx — Lønn
    AccountTemplate("5000", "Lønnskostnader",            "Payroll costs",             "Lönekostnader",             "expense",   "",        ""),
    AccountTemplate("5010", "Fast lønn",                 "Fixed salaries",            "Fasta löner",               "expense",   "",        "5000"),
    AccountTemplate("5020", "Timelønn",                  "Hourly wages",              "Timlöner",                  "expense",   "",        "5000"),
    AccountTemplate("5090", "Feriepenger",               "Vacation pay",              "Semesterlön",               "expense",   "",        "5000"),
    AccountTemplate("5400", "Arbeidsgiveravgift",        "Employer NI contributions", "Arbetsgivaravgifter",       "expense",   "",        "5000"),
    AccountTemplate("5420", "AGA av feriepenger",        "Employer NI on vacation pay","AGA på semesterlön",       "expense",   "",        "5000"),
    AccountTemplate("5900", "Yrkesskadeforsikring",      "Occupational injury insurance","Arbetsskadeförsäkring",  "expense",   "NO_ZERO", "5000"),

    # 6xxx — Avskrivning og drift
    AccountTemplate("6000", "Avskrivning bygg",          "Depreciation buildings",    "Avskrivning byggnader",     "expense",   "",        ""),
    AccountTemplate("6050", "Avskrivning inventar",      "Depreciation furniture",    "Avskrivning inventarier",   "expense",   "",        ""),
    AccountTemplate("6100", "Frakt og transport",        "Freight & transport",       "Frakt och transport",       "expense",   "NO_HIGH", ""),
    AccountTemplate("6300", "Leie lokaler",              "Rent — premises",           "Hyra lokaler",              "expense",   "NO_ZERO", ""),
    AccountTemplate("6310", "Leasing",                   "Leasing",                   "Leasing",                   "expense",   "NO_HIGH", "6300"),
    AccountTemplate("6340", "Lys, varme",                "Electricity & heating",     "El och värme",              "expense",   "NO_HIGH", ""),
    AccountTemplate("6360", "Kommunale avgifter",        "Municipal fees",            "Kommunala avgifter",        "expense",   "NO_ZERO", ""),
    AccountTemplate("6400", "Reise og transport (drift)","Travel & transport (ops)",  "Rese- och transport drift", "expense",   "NO_HIGH", ""),
    AccountTemplate("6500", "Verktøy og små anskaffelser","Tools & small equipment",  "Verktyg och småanskaff.",   "expense",   "NO_HIGH", ""),
    AccountTemplate("6540", "Inventarkjøp",              "Furniture purchases",       "Inventarieinköp",           "expense",   "NO_HIGH", ""),
    AccountTemplate("6550", "Driftsmateriale",           "Operating supplies",        "Driftmaterial",             "expense",   "NO_HIGH", ""),
    AccountTemplate("6555", "Rengjøringsmidler og linnet","Cleaning & linen",         "Rengöring och linne",       "expense",   "NO_HIGH", "6550"),
    AccountTemplate("6600", "Vedlikehold bygg",          "Building maintenance",      "Underhåll byggnader",       "expense",   "NO_HIGH", ""),
    AccountTemplate("6700", "Fremmede tjenester",        "Outsourced services",       "Främmande tjänster",        "expense",   "NO_HIGH", ""),
    AccountTemplate("6705", "Vaskeritjenester",          "Laundry services",          "Tvätteritjänster",          "expense",   "NO_HIGH", "6700"),
    AccountTemplate("6710", "Sikkerhet og vakt",         "Security",                  "Säkerhetstjänster",         "expense",   "NO_HIGH", "6700"),
    AccountTemplate("6720", "Regnskap og revisjon",      "Accounting & audit",        "Redovisning och revision",  "expense",   "NO_HIGH", "6700"),
    AccountTemplate("6740", "Juridisk bistand",          "Legal services",            "Juridisk hjälp",            "expense",   "NO_HIGH", "6700"),
    AccountTemplate("6800", "Kontorkostnader",           "Office supplies",           "Kontorskostnader",          "expense",   "NO_HIGH", ""),
    AccountTemplate("6860", "Møter og kurs",             "Meetings & training",       "Möten och kurs",            "expense",   "NO_HIGH", ""),
    AccountTemplate("6900", "Telefon",                   "Phone",                     "Telefon",                   "expense",   "NO_HIGH", ""),
    AccountTemplate("6950", "Internett og IT",           "Internet & IT",             "Internet och IT",           "expense",   "NO_HIGH", ""),

    # 7xxx — Andre driftskostnader
    AccountTemplate("7000", "Drivstoff og bilhold",      "Fuel & vehicle running",    "Bränsle och bil",           "expense",   "NO_HIGH", ""),
    AccountTemplate("7140", "Reisekostnader",            "Travel expenses",           "Resekostnader",             "expense",   "NO_LOW",  ""),
    AccountTemplate("7160", "Diettkostnader",            "Per diem",                  "Traktamente",               "expense",   "NO_ZERO", ""),
    AccountTemplate("7300", "Salgs- og reklamekostnader","Sales & advertising",       "Sälj- och reklamkostnad",   "expense",   "NO_HIGH", ""),
    AccountTemplate("7320", "Booking.com provisjon",     "OTA commission",            "OTA-provision",             "expense",   "NO_HIGH", "7300"),
    AccountTemplate("7350", "Trykksaker og brosjyrer",   "Print & brochures",         "Tryck och broschyrer",      "expense",   "NO_HIGH", "7300"),
    AccountTemplate("7400", "Forsikring",                "Insurance",                 "Försäkring",                "expense",   "NO_ZERO", ""),
    AccountTemplate("7600", "Lisens og rettigheter",     "Licenses & rights",         "Licenser och rättigheter",  "expense",   "NO_HIGH", ""),
    AccountTemplate("7700", "Bankgebyrer og kortprovisjon","Bank fees & card provisjons","Bankavgifter",          "expense",   "NO_ZERO", ""),
    AccountTemplate("7710", "Tap på fordringer",         "Bad debt",                  "Kundförluster",             "expense",   "NO_ZERO", ""),
    AccountTemplate("7790", "Annen kostnad",             "Other expense",             "Övrig kostnad",             "expense",   "NO_HIGH", ""),

    # 8xxx — Finansposter
    AccountTemplate("8000", "Finansposter",              "Financial items",           "Finansiella poster",        "expense",   "",        ""),
    AccountTemplate("8040", "Renteinntekt",              "Interest income",           "Ränteintäkter",             "revenue",   "",        "8000"),
    AccountTemplate("8140", "Rentekostnad pantelån",     "Interest expense mortgage", "Räntekostnad pantlån",      "expense",   "",        "8000"),
    AccountTemplate("8150", "Annen rentekostnad",        "Other interest expense",    "Annan räntekostnad",        "expense",   "",        "8000"),
    AccountTemplate("8170", "Valutagevinst/-tap",        "Currency gain/loss",        "Valutavinst/-förlust",      "expense",   "",        "8000"),
    AccountTemplate("8300", "Skattekostnad",             "Income tax expense",        "Skattekostnad",             "expense",   "",        "8000"),
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
