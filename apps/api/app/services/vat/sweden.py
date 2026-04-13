"""
Sweden momsdeklaration (VAT return) generator.

Filing frequency: monthly (large), quarterly (medium), annual (small).
Submission endpoint: Skatteverket e-service.
Authentication: BankID or organisational certificate.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from .models import VatReturnResult


class SwedenVatReturn:
    """Helpers for Swedish VAT returns (momsdeklaration)."""

    @staticmethod
    def to_xml(result: VatReturnResult, organisation_number: str) -> str:
        """Generate a Skatteverket momsdeklaration XML payload."""
        root = Element("Momsdeklaration")
        root.set("xmlns", "http://xmls.skatteverket.se/se/skatteverket/moms")

        huvud = SubElement(root, "Huvud")
        SubElement(huvud, "Organisationsnummer").text = organisation_number
        SubElement(huvud, "PeriodStart").text = result.period_start.isoformat()
        SubElement(huvud, "PeriodSlut").text = result.period_end.isoformat()

        poster = SubElement(root, "Poster")
        for line in result.lines:
            post = SubElement(poster, "Post")
            SubElement(post, "VatKod").text = line.code
            SubElement(post, "Riktning").text = line.direction
            SubElement(post, "Beskattningsunderlag").text = str(line.net_total.amount)
            SubElement(post, "Skattesats").text = str(line.rate)
            SubElement(post, "Moms").text = str(line.vat_total.amount)

        summary = SubElement(root, "Summering")
        SubElement(summary, "UtgaendeMoms").text = str(result.total_output_vat.amount)
        SubElement(summary, "IngaendeMoms").text = str(result.total_input_vat.amount)
        SubElement(summary, "NettoMoms").text = str(result.net_vat_payable.amount)

        raw = tostring(root, encoding="unicode")
        return minidom.parseString(raw).toprettyxml(indent="  ")
