"""
VAT return engine.

Reads journal lines for a given client and period, aggregates them by
VAT code, and produces a country-specific VAT return ready for submission
to the relevant tax authority (Altinn, Skatteverket, OmaVero).

Usage:
    from app.services.vat import build_vat_return, VatReturnInput
    from datetime import date

    vat_return = build_vat_return(
        country="NO",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 4, 30),
        transactions=[
            VatTransaction(
                amount_net=Money("1000", "NOK"),
                vat_code="NO-25",
                direction="sale",
            ),
            # ...
        ],
    )
    print(vat_return.total_output_vat, vat_return.total_input_vat)
    xml = vat_return.to_xml()
"""
from .models import (
    VatTransaction,
    VatReturnInput,
    VatReturnLine,
    VatReturnResult,
    VatDirection,
)
from .engine import build_vat_return
from .norway import NorwayVatReturn
from .sweden import SwedenVatReturn
from .finland import FinlandVatReturn

__all__ = [
    "VatTransaction",
    "VatReturnInput",
    "VatReturnLine",
    "VatReturnResult",
    "VatDirection",
    "build_vat_return",
    "NorwayVatReturn",
    "SwedenVatReturn",
    "FinlandVatReturn",
]
