"""VAT return engine tests."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.services.money import Money
from app.services.vat import (
    VatTransaction,
    VatReturnInput,
    build_vat_return,
    NorwayVatReturn,
    SwedenVatReturn,
    FinlandVatReturn,
)


# ── Engine — aggregation ──────────────────────────────────────────────────


def test_aggregates_sales_and_purchases_separately():
    """Sales and purchases get their own lines even for the same VAT code."""
    tx = [
        VatTransaction(Money("1000.00", "NOK"), "NO-25", "sale"),
        VatTransaction(Money("500.00", "NOK"), "NO-25", "purchase"),
    ]
    result = build_vat_return(
        VatReturnInput(
            country="NO",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 4, 30),
            transactions=tx,
        )
    )
    assert len(result.lines) == 2
    sales = [l for l in result.lines if l.direction == "sale"]
    purchases = [l for l in result.lines if l.direction == "purchase"]
    assert len(sales) == 1
    assert len(purchases) == 1
    assert sales[0].net_total == Money("1000.00", "NOK")
    assert purchases[0].net_total == Money("500.00", "NOK")


def test_aggregates_multiple_transactions_for_same_code():
    tx = [
        VatTransaction(Money("1000", "NOK"), "NO-25", "sale"),
        VatTransaction(Money("500", "NOK"), "NO-25", "sale"),
        VatTransaction(Money("200", "NOK"), "NO-25", "sale"),
    ]
    result = build_vat_return(
        VatReturnInput(
            country="NO",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 4, 30),
            transactions=tx,
        )
    )
    assert len(result.lines) == 1
    assert result.lines[0].net_total == Money("1700", "NOK")
    assert result.lines[0].vat_total == Money("425", "NOK")  # 1700 * 0.25


def test_total_output_and_input_vat():
    tx = [
        VatTransaction(Money("10000", "NOK"), "NO-25", "sale"),
        VatTransaction(Money("4000", "NOK"), "NO-25", "purchase"),
        VatTransaction(Money("2000", "NOK"), "NO-15", "purchase"),
    ]
    result = build_vat_return(
        VatReturnInput(
            country="NO",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 4, 30),
            transactions=tx,
        )
    )
    # Output: 10000 * 0.25 = 2500
    # Input:  4000 * 0.25 + 2000 * 0.15 = 1000 + 300 = 1300
    # Net:    2500 - 1300 = 1200
    assert result.total_output_vat == Money("2500", "NOK")
    assert result.total_input_vat == Money("1300", "NOK")
    assert result.net_vat_payable == Money("1200", "NOK")


def test_empty_transactions_returns_empty_result():
    result = build_vat_return(
        VatReturnInput(
            country="NO",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 4, 30),
            transactions=[],
        )
    )
    assert result.lines == []
    assert result.total_output_vat == Money.zero("NOK")
    assert result.total_input_vat == Money.zero("NOK")
    assert result.currency == "NOK"


def test_currency_mismatch_rejected():
    with pytest.raises(ValueError):
        build_vat_return(
            VatReturnInput(
                country="NO",
                period_start=date(2026, 3, 1),
                period_end=date(2026, 4, 30),
                transactions=[
                    VatTransaction(Money("1000", "NOK"), "NO-25", "sale"),
                    VatTransaction(Money("1000", "EUR"), "NO-25", "sale"),
                ],
            )
        )


def test_wrong_country_currency_rejected():
    """NOK transactions can't go on a Swedish VAT return."""
    with pytest.raises(ValueError):
        build_vat_return(
            VatReturnInput(
                country="SE",
                period_start=date(2026, 3, 1),
                period_end=date(2026, 4, 30),
                transactions=[
                    VatTransaction(Money("1000", "NOK"), "SE-25", "sale"),
                ],
            )
        )


def test_unknown_vat_code_rejected():
    with pytest.raises(ValueError) as exc:
        build_vat_return(
            VatReturnInput(
                country="NO",
                period_start=date(2026, 3, 1),
                period_end=date(2026, 4, 30),
                transactions=[
                    VatTransaction(Money("1000", "NOK"), "NO-999", "sale"),
                ],
            )
        )
    assert "NO-999" in str(exc.value)


# ── Finland: standard rate switch ────────────────────────────────────────


def test_finland_uses_25_5_percent_after_sep_2024():
    """Period end date drives which rate applies."""
    result = build_vat_return(
        VatReturnInput(
            country="FI",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            transactions=[
                VatTransaction(Money("1000.00", "EUR"), "FI-255", "sale"),
            ],
        )
    )
    assert result.lines[0].rate == Decimal("0.255")
    assert result.lines[0].vat_total == Money("255.00", "EUR")


def test_finland_uses_24_percent_before_sep_2024():
    """Historic periods use the old 24% rate."""
    result = build_vat_return(
        VatReturnInput(
            country="FI",
            period_start=date(2024, 7, 1),
            period_end=date(2024, 7, 31),
            transactions=[
                VatTransaction(Money("1000.00", "EUR"), "FI-24", "sale"),
            ],
        )
    )
    assert result.lines[0].rate == Decimal("0.24")
    assert result.lines[0].vat_total == Money("240.00", "EUR")


# ── XML payload generators ──────────────────────────────────────────────


def test_norway_mva_melding_xml():
    result = build_vat_return(
        VatReturnInput(
            country="NO",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 4, 30),
            transactions=[
                VatTransaction(Money("10000", "NOK"), "NO-25", "sale"),
                VatTransaction(Money("3000", "NOK"), "NO-25", "purchase"),
            ],
        )
    )
    xml = NorwayVatReturn.to_xml(result, organisation_number="987654321")
    assert "987654321" in xml
    assert "2026-03-01" in xml
    assert "2026-04-30" in xml
    assert "NO-25" in xml
    assert "1750" in xml  # net VAT payable (2500 - 750)


def test_sweden_momsdeklaration_xml():
    result = build_vat_return(
        VatReturnInput(
            country="SE",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 30),
            transactions=[
                VatTransaction(Money("20000", "SEK"), "SE-25", "sale"),
                VatTransaction(Money("5000", "SEK"), "SE-12", "purchase"),
            ],
        )
    )
    xml = SwedenVatReturn.to_xml(result, organisation_number="556123456701")
    assert "556123456701" in xml
    assert "SE-25" in xml
    assert "SE-12" in xml
    assert "UtgaendeMoms" in xml
    assert "IngaendeMoms" in xml


def test_finland_alv_xml_uses_2024_onwards_rate():
    result = build_vat_return(
        VatReturnInput(
            country="FI",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 30),
            transactions=[
                VatTransaction(Money("10000", "EUR"), "FI-255", "sale"),
            ],
        )
    )
    xml = FinlandVatReturn.to_xml(result, business_id="07375462")
    assert "07375462" in xml
    assert "FI-255" in xml
    assert "0.255" in xml
    assert "2550" in xml  # 10000 * 0.255
