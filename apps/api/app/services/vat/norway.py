"""
Norway MVA-melding (VAT return) generator.

The real Altinn MVA-melding schema is large — this is a simplified payload
that covers the essential line boxes. When integrating with production
Altinn, extend to cover the full XSD.

Filing frequency: bimonthly (every 2 months).
Submission endpoint: Altinn v3 API.
Authentication: virksomhetssertifikat (enterprise certificate).
"""
from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from .models import VatReturnResult


class NorwayVatReturn:
    """Helpers for Norwegian VAT returns (MVA-melding)."""

    @staticmethod
    def to_xml(result: VatReturnResult, organisation_number: str) -> str:
        """
        Generate an Altinn-compatible MVA-melding XML envelope.

        Output boxes (simplified):
          post2 — Total output VAT (sales VAT owed)
          post3 — Total input VAT (purchases VAT claimed)
          post4 — Net VAT to pay / receive
        """
        root = Element("mva-melding")
        root.set("xmlns", "http://skatteetaten.no/mva-melding")

        identifikasjon = SubElement(root, "identifikasjon")
        SubElement(identifikasjon, "organisasjonsnummer").text = organisation_number
        SubElement(identifikasjon, "periodeFra").text = result.period_start.isoformat()
        SubElement(identifikasjon, "periodeTil").text = result.period_end.isoformat()

        poster = SubElement(root, "poster")

        # One <post> element per VAT bracket
        for line in result.lines:
            post = SubElement(poster, "post")
            SubElement(post, "kode").text = line.code
            SubElement(post, "retning").text = line.direction
            SubElement(post, "grunnlag").text = str(line.net_total.amount)
            SubElement(post, "sats").text = str(line.rate)
            SubElement(post, "avgift").text = str(line.vat_total.amount)

        # Summary
        summary = SubElement(root, "sammendrag")
        SubElement(summary, "totalUtgaaende").text = str(result.total_output_vat.amount)
        SubElement(summary, "totalInngaaende").text = str(result.total_input_vat.amount)
        SubElement(summary, "nettoAvgift").text = str(result.net_vat_payable.amount)

        raw = tostring(root, encoding="unicode")
        return minidom.parseString(raw).toprettyxml(indent="  ")
