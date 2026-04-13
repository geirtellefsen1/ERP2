"""
Unit tests for the Jurisdiction Engine.

These are pure Python tests — no database, no HTTP, fast. They verify that:
- The engine routes to the correct country module for each country code
- Each country module returns reasonable values for all interface methods
- VAT number validation works for known-good and known-bad inputs
- Unknown country codes raise a clear error
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.jurisdictions import (
    JurisdictionEngine,
    UnknownJurisdictionError,
    SUPPORTED_COUNTRIES,
)


# ── Registry & routing ──────────────────────────────────────────────────────


def test_supported_countries_are_exactly_no_se_fi():
    assert set(SUPPORTED_COUNTRIES) == {"NO", "SE", "FI"}


def test_is_supported():
    assert JurisdictionEngine.is_supported("NO") is True
    assert JurisdictionEngine.is_supported("se") is True
    assert JurisdictionEngine.is_supported("FI") is True
    assert JurisdictionEngine.is_supported("US") is False
    assert JurisdictionEngine.is_supported("ZA") is False


def test_unknown_country_raises():
    with pytest.raises(UnknownJurisdictionError) as exc:
        JurisdictionEngine.get_currency("US")
    assert "US" in str(exc.value)
    assert "NO" in str(exc.value)  # error message lists supported codes


# ── Currency and language ──────────────────────────────────────────────────


def test_currencies():
    assert JurisdictionEngine.get_currency("NO") == "NOK"
    assert JurisdictionEngine.get_currency("SE") == "SEK"
    assert JurisdictionEngine.get_currency("FI") == "EUR"


def test_languages():
    assert JurisdictionEngine.get_language("NO") == "nb-NO"
    assert JurisdictionEngine.get_language("SE") == "sv-SE"
    assert JurisdictionEngine.get_language("FI") == "fi-FI"


# ── VAT rates ──────────────────────────────────────────────────────────────


def test_norway_vat_rates():
    rates = JurisdictionEngine.get_vat_rates("NO", date(2026, 1, 1))
    # Standard 25%, reduced 15% (food), low 12% (transport), zero
    assert len(rates) >= 4
    standard = next(r for r in rates if r.category == "standard")
    assert standard.rate == Decimal("0.25")


def test_sweden_vat_rates():
    rates = JurisdictionEngine.get_vat_rates("SE", date(2026, 1, 1))
    standard = next(r for r in rates if r.category == "standard")
    assert standard.rate == Decimal("0.25")
    # Sweden has both 12% and 6% reduced rates
    reduced = [r for r in rates if r.category == "reduced"]
    assert Decimal("0.12") in [r.rate for r in reduced]
    assert Decimal("0.06") in [r.rate for r in reduced]


def test_finland_vat_rates_post_september_2024():
    """After 1 Sep 2024, Finland's standard VAT rate is 25.5%."""
    rates = JurisdictionEngine.get_vat_rates("FI", date(2026, 1, 1))
    standard = next(r for r in rates if r.category == "standard")
    assert standard.rate == Decimal("0.255")


def test_finland_vat_rates_pre_september_2024():
    """Before the increase, Finland's standard rate was 24%."""
    rates = JurisdictionEngine.get_vat_rates("FI", date(2024, 1, 1))
    standard = next(r for r in rates if r.category == "standard")
    assert standard.rate == Decimal("0.24")


# ── VAT filing frequency ───────────────────────────────────────────────────


def test_vat_filing_frequency():
    assert JurisdictionEngine.get_vat_filing_frequency("NO") == "bimonthly"
    assert JurisdictionEngine.get_vat_filing_frequency("SE") == "monthly"
    assert JurisdictionEngine.get_vat_filing_frequency("FI") == "monthly"


# ── Payroll rules ──────────────────────────────────────────────────────────


def test_norway_payroll_has_aga_and_otp():
    rules = JurisdictionEngine.get_payroll_rules("NO", "permanent", date(2026, 1, 1))
    codes = {d.code for d in rules.employer_contributions}
    assert "AGA" in codes
    assert "OTP" in codes
    assert rules.holiday_pay_rate == Decimal("0.102")
    assert rules.sick_pay_employer_days == 16
    assert rules.reporting_endpoint == "Altinn A-melding"


def test_sweden_payroll_has_arbetsgivaravgifter():
    rules = JurisdictionEngine.get_payroll_rules("SE", "permanent", date(2026, 1, 1))
    codes = {d.code for d in rules.employer_contributions}
    assert "ARBGAV" in codes
    arb = next(d for d in rules.employer_contributions if d.code == "ARBGAV")
    assert arb.rate == Decimal("0.3142")
    assert rules.holiday_pay_rate == Decimal("0.12")
    assert "AGD" in rules.reporting_endpoint or "Skatteverket" in rules.reporting_endpoint


def test_finland_payroll_has_tyel_and_realtime_reporting():
    rules = JurisdictionEngine.get_payroll_rules("FI", "permanent", date(2026, 1, 1))
    codes = {d.code for d in rules.employer_contributions}
    assert "TYEL" in codes
    assert rules.reporting_frequency == "realtime_5d"
    assert rules.reporting_endpoint == "Tulorekisteri"


# ── Filing calendar ────────────────────────────────────────────────────────


def test_norway_filing_calendar_has_bimonthly_vat_and_monthly_a_melding():
    deadlines = JurisdictionEngine.get_filing_calendar("NO", 2026)
    mva = [d for d in deadlines if d.form_code == "MVA-melding"]
    amelding = [d for d in deadlines if d.form_code == "A-melding"]
    # 6 bimonthly VAT filings per year
    assert len(mva) == 6
    # 12 monthly A-melding filings per year
    assert len(amelding) == 12


def test_sweden_filing_calendar_has_monthly_agd():
    deadlines = JurisdictionEngine.get_filing_calendar("SE", 2026)
    agd = [d for d in deadlines if d.form_code == "AGD"]
    assert len(agd) == 12


def test_finland_filing_calendar_has_monthly_vat_and_tulorekisteri_markers():
    deadlines = JurisdictionEngine.get_filing_calendar("FI", 2026)
    alv = [d for d in deadlines if d.form_code == "ALV"]
    tulo = [d for d in deadlines if d.form_code == "Tulorekisteri"]
    assert len(alv) == 12
    assert len(tulo) == 12


# ── Public holidays ────────────────────────────────────────────────────────


def test_public_holidays_include_country_specific_day():
    no_holidays = JurisdictionEngine.get_public_holidays("NO", 2026)
    # Norway's constitution day 17 May
    assert any(h.date == date(2026, 5, 17) for h in no_holidays)

    fi_holidays = JurisdictionEngine.get_public_holidays("FI", 2026)
    # Finland's independence day 6 December
    assert any(h.date == date(2026, 12, 6) for h in fi_holidays)

    se_holidays = JurisdictionEngine.get_public_holidays("SE", 2026)
    # Sweden's national day 6 June
    assert any(h.date == date(2026, 6, 6) for h in se_holidays)


# ── Chart of accounts ──────────────────────────────────────────────────────


def test_coa_templates_have_reasonable_size():
    """Each country ships at least the core accounts needed to run a journal."""
    for country in ("NO", "SE", "FI"):
        coa = JurisdictionEngine.get_coa_template(country, None)
        assert len(coa) >= 15
        types = {a.account_type for a in coa}
        assert {"asset", "liability", "equity", "revenue", "expense"}.issubset(types)


def test_norway_coa_has_vat_accounts():
    coa = JurisdictionEngine.get_coa_template("NO", None)
    codes = {a.code for a in coa}
    # Norwegian NS 4102 VAT accounts
    assert "2700" in codes  # VAT output
    assert "2710" in codes  # VAT input


def test_sweden_coa_uses_bas_numbering():
    coa = JurisdictionEngine.get_coa_template("SE", None)
    codes = {a.code for a in coa}
    # BAS 2024 standard account codes
    assert "3001" in codes  # Sales Sweden 25% VAT
    assert "7010" in codes  # Wages


# ── VAT number validation ─────────────────────────────────────────────────


def test_norway_org_number_validation():
    # Saga Advisory AS real org number for demo — use a known-valid one
    # 123456785 has a valid mod-11 checksum
    assert JurisdictionEngine.validate_vat_number("NO", "123456785") is True
    # Clearly invalid
    assert JurisdictionEngine.validate_vat_number("NO", "123456789") is False
    assert JurisdictionEngine.validate_vat_number("NO", "ABC") is False
    assert JurisdictionEngine.validate_vat_number("NO", "12345678") is False  # too short


def test_finland_vat_number_validation():
    # Y-tunnus 0737546-2 is a known-valid Finnish business ID
    assert JurisdictionEngine.validate_vat_number("FI", "FI07375462") is True
    assert JurisdictionEngine.validate_vat_number("FI", "07375462") is True
    # Invalid check digit
    assert JurisdictionEngine.validate_vat_number("FI", "07375460") is False
    assert JurisdictionEngine.validate_vat_number("FI", "ABC") is False


# ── Bank formats ──────────────────────────────────────────────────────────


def test_bank_formats_are_correct():
    no = JurisdictionEngine.get_bank_format("NO")
    assert no.iban_prefix == "NO"
    assert "Aiia" in no.open_banking_provider

    se = JurisdictionEngine.get_bank_format("SE")
    assert se.iban_prefix == "SE"
    assert "Tink" in se.open_banking_provider or "Aiia" in se.open_banking_provider

    fi = JurisdictionEngine.get_bank_format("FI")
    assert fi.iban_prefix == "FI"
    assert "SEPA" in fi.payment_file_format


# ── Statutory forms ────────────────────────────────────────────────────────


def test_statutory_forms_include_critical_country_forms():
    no_forms = {f.code for f in JurisdictionEngine.get_statutory_forms("NO")}
    assert "MVA-melding" in no_forms
    assert "A-melding" in no_forms

    se_forms = {f.code for f in JurisdictionEngine.get_statutory_forms("SE")}
    assert "AGD" in se_forms
    assert "KU" in se_forms

    fi_forms = {f.code for f in JurisdictionEngine.get_statutory_forms("FI")}
    assert "Tulorekisteri" in fi_forms
    assert "ALV" in fi_forms
