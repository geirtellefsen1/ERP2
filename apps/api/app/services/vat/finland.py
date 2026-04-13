"""
Finland ALV (VAT return) generator.

Filing frequency: monthly (large/medium), quarterly (small), annual (very small).
Submission endpoint: OmaVero (Vero Suomi portal and API).
Authentication: Katso ID / Suomi.fi / Finnish Trust Network.

Note: Finland's standard rate changed from 24% to 25.5% on 1 Sep 2024.
The VAT engine picks up the right rate automatically from the jurisdiction
engine based on the period end date.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from .models import VatReturnResult


class FinlandVatReturn:
    """Helpers for Finnish VAT returns (arvonlisäveroilmoitus)."""

    @staticmethod
    def to_xml(result: VatReturnResult, business_id: str) -> str:
        """Generate an OmaVero-compatible ALV XML payload."""
        root = Element("Arvonlisaveroilmoitus")
        root.set("xmlns", "http://vero.fi/alvilmoitus")

        tunnistetiedot = SubElement(root, "Tunnistetiedot")
        SubElement(tunnistetiedot, "YTunnus").text = business_id
        SubElement(tunnistetiedot, "Verokausi").text = (
            f"{result.period_start.isoformat()}/{result.period_end.isoformat()}"
        )

        erittely = SubElement(root, "Erittely")
        for line in result.lines:
            rivi = SubElement(erittely, "Rivi")
            SubElement(rivi, "VeroKoodi").text = line.code
            SubElement(rivi, "Suunta").text = line.direction
            SubElement(rivi, "Peruste").text = str(line.net_total.amount)
            SubElement(rivi, "VeroKanta").text = str(line.rate)
            SubElement(rivi, "Vero").text = str(line.vat_total.amount)

        yhteenveto = SubElement(root, "Yhteenveto")
        SubElement(yhteenveto, "MyynninVero").text = str(result.total_output_vat.amount)
        SubElement(yhteenveto, "OstonVero").text = str(result.total_input_vat.amount)
        SubElement(yhteenveto, "NettoVero").text = str(result.net_vat_payable.amount)

        raw = tostring(root, encoding="unicode")
        return minidom.parseString(raw).toprettyxml(indent="  ")
