"""Inbox AI extraction stub.

In production this calls Claude (or a vision model) to extract vendor,
date, amount, VAT, and suggested account from a receipt/invoice image
or PDF. For the demo we use rule-based pattern matching against the
filename and known suppliers.

The shape of `extract_from_filename()` is the same as the future
real extractor — drop-in replaceable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class ExtractionResult:
    vendor: Optional[str]
    date: Optional[date]
    amount_minor: Optional[int]
    vat_minor: Optional[int]
    currency: str
    invoice_number: Optional[str]
    suggested_account_code: Optional[str]
    suggested_outlet_type: Optional[str]
    confidence: Decimal           # 0.000 – 1.000
    reasoning: str


# Norwegian supplier patterns. Real extractor learns these per-agency
# from approved history; here we hardcode the demo suppliers.
SUPPLIER_PATTERNS = [
    # (regex, vendor, account_code, outlet_type, default_currency)
    (r"tine", "Tine SA", "4000", "food", "NOK"),
    (r"bama", "Bama Gruppen", "4000", "food", "NOK"),
    (r"vinmono", "Vinmonopolet", "4010", "beverage_alcohol", "NOK"),
    (r"hansa", "Hansa Borg Bryggerier", "4010", "beverage_alcohol", "NOK"),
    (r"ringnes", "Ringnes", "4020", "beverage_soft", "NOK"),
    (r"berg.?lin|berglin", "Berg Linservice AS", "4100", None, "NOK"),
    (r"hafslund", "Hafslund Eco", "5100", None, "NOK"),
    (r"bergen.?vann", "Bergen Vann KF", "5110", None, "NOK"),
    (r"lilleborg", "Lilleborg", "5200", None, "NOK"),
    (r"booking", "Booking.com", "5300", None, "NOK"),
    (r"expedia", "Expedia Group", "5300", None, "NOK"),
    (r"meta|facebook", "Meta (Facebook ads)", "5400", None, "NOK"),
]


def _match_supplier(text: str):
    """Return the supplier tuple that matches, or None."""
    t = text.lower()
    for pattern, vendor, account, outlet, currency in SUPPLIER_PATTERNS:
        if re.search(pattern, t):
            return vendor, account, outlet, currency
    return None


def _extract_amount(text: str) -> Optional[int]:
    """Pull a NOK amount from a filename like 'tine_2026-04-12_3850nok.pdf'.

    Returns minor units (øre)."""
    # Match patterns like "3850nok", "3.850", "3,850.50"
    m = re.search(r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*nok", text.lower())
    if m:
        raw = m.group(1).replace(".", "").replace(",", ".")
        try:
            major = float(raw)
            return int(round(major * 100))
        except ValueError:
            pass
    return None


def _extract_date(text: str) -> Optional[date]:
    """Pull an ISO date from a filename. Returns None if absent."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            return None
    return None


def extract_from_filename(filename: str) -> ExtractionResult:
    """Demo extractor — rule-based, deterministic.

    A filename like `tine_2026-04-12_3850nok_inv-2389.pdf` produces a
    high-confidence extraction. A random filename produces a low-confidence
    result with the supplier slot empty (signalling the accountant needs
    to enter it manually).
    """
    base = filename.lower()

    supplier = _match_supplier(base)
    amount = _extract_amount(base)
    extracted_date = _extract_date(base)
    inv_number = None
    inv_match = re.search(r"inv[-_]?(\w+)", base)
    if inv_match:
        inv_number = inv_match.group(1).upper()

    if supplier is None:
        return ExtractionResult(
            vendor=None,
            date=extracted_date,
            amount_minor=amount,
            vat_minor=None,
            currency="NOK",
            invoice_number=inv_number,
            suggested_account_code=None,
            suggested_outlet_type=None,
            confidence=Decimal("0.40"),
            reasoning=(
                "No matching supplier pattern. Filename did not contain a "
                "known vendor name. Manual coding required."
            ),
        )

    vendor, account_code, outlet_type, currency = supplier

    # VAT estimation: alcohol/food = 25%, accommodation = 12%
    # Default to 25% (most line items at a hotel)
    vat_minor = None
    if amount is not None:
        # gross / 1.25 = net  →  vat = gross - net
        net = int(amount / Decimal("1.25"))
        vat_minor = amount - net

    confidence = Decimal("0.95") if amount and extracted_date else Decimal("0.75")

    return ExtractionResult(
        vendor=vendor,
        date=extracted_date,
        amount_minor=amount,
        vat_minor=vat_minor,
        currency=currency,
        invoice_number=inv_number,
        suggested_account_code=account_code,
        suggested_outlet_type=outlet_type,
        confidence=confidence,
        reasoning=(
            f"Matched known supplier '{vendor}' from filename. "
            f"Suggested account {account_code} based on prior coding history. "
            f"VAT estimated at standard 25%."
        ),
    )
