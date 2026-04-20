"""
EHF (Elektronisk Handelsformat) invoice generator and parser.
EHF Billing 3.0 is based on PEPPOL BIS Billing 3.0 / UBL 2.1.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import io
import random
import string

UBL_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
CBC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
CAC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"

NSMAP = {
    "": UBL_NS,
    "cbc": CBC_NS,
    "cac": CAC_NS,
}


@dataclass
class EHFLineItem:
    description: str
    quantity: Decimal
    unit_price: Decimal
    vat_rate: Decimal
    account_code: str = ""

    @property
    def line_amount(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"), ROUND_HALF_UP)

    @property
    def vat_amount(self) -> Decimal:
        return (self.line_amount * self.vat_rate / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)


@dataclass
class EHFInvoice:
    invoice_number: str
    issue_date: date
    due_date: date
    supplier_name: str
    supplier_org_number: str
    supplier_address: str
    supplier_city: str
    supplier_postal_code: str
    supplier_country: str = "NO"
    buyer_name: str = ""
    buyer_org_number: str = ""
    currency: str = "NOK"
    lines: list[EHFLineItem] = field(default_factory=list)
    note: str = ""

    @property
    def subtotal(self) -> Decimal:
        return sum((l.line_amount for l in self.lines), Decimal("0"))

    @property
    def total_vat(self) -> Decimal:
        return sum((l.vat_amount for l in self.lines), Decimal("0"))

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.total_vat


def _el(parent: ET.Element, tag: str, text: str | None = None, **attrs) -> ET.Element:
    e = ET.SubElement(parent, tag, **attrs)
    if text is not None:
        e.text = str(text)
    return e


def generate_ehf_xml(inv: EHFInvoice) -> str:
    for prefix, uri in NSMAP.items():
        ET.register_namespace(prefix, uri)

    root = ET.Element(f"{{{UBL_NS}}}Invoice")
    root.set("xmlns:cbc", CBC_NS)
    root.set("xmlns:cac", CAC_NS)

    _el(root, f"{{{CBC_NS}}}CustomizationID",
        "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0")
    _el(root, f"{{{CBC_NS}}}ProfileID", "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0")
    _el(root, f"{{{CBC_NS}}}ID", inv.invoice_number)
    _el(root, f"{{{CBC_NS}}}IssueDate", inv.issue_date.isoformat())
    _el(root, f"{{{CBC_NS}}}DueDate", inv.due_date.isoformat())
    _el(root, f"{{{CBC_NS}}}InvoiceTypeCode", "380")
    if inv.note:
        _el(root, f"{{{CBC_NS}}}Note", inv.note)
    _el(root, f"{{{CBC_NS}}}DocumentCurrencyCode", inv.currency)

    # Supplier
    supplier = _el(root, f"{{{CAC_NS}}}AccountingSupplierParty")
    sp = _el(supplier, f"{{{CAC_NS}}}Party")
    sp_id = _el(sp, f"{{{CAC_NS}}}PartyIdentification")
    _el(sp_id, f"{{{CBC_NS}}}ID", inv.supplier_org_number, schemeID="0192")
    sp_name = _el(sp, f"{{{CAC_NS}}}PartyName")
    _el(sp_name, f"{{{CBC_NS}}}Name", inv.supplier_name)
    sp_addr = _el(sp, f"{{{CAC_NS}}}PostalAddress")
    _el(sp_addr, f"{{{CBC_NS}}}StreetName", inv.supplier_address)
    _el(sp_addr, f"{{{CBC_NS}}}CityName", inv.supplier_city)
    _el(sp_addr, f"{{{CBC_NS}}}PostalZone", inv.supplier_postal_code)
    sp_country = _el(sp_addr, f"{{{CAC_NS}}}Country")
    _el(sp_country, f"{{{CBC_NS}}}IdentificationCode", inv.supplier_country)
    sp_tax = _el(sp, f"{{{CAC_NS}}}PartyTaxScheme")
    _el(sp_tax, f"{{{CBC_NS}}}CompanyID", f"NO{inv.supplier_org_number}MVA")
    tax_scheme = _el(sp_tax, f"{{{CAC_NS}}}TaxScheme")
    _el(tax_scheme, f"{{{CBC_NS}}}ID", "VAT")
    sp_legal = _el(sp, f"{{{CAC_NS}}}PartyLegalEntity")
    _el(sp_legal, f"{{{CBC_NS}}}RegistrationName", inv.supplier_name)
    _el(sp_legal, f"{{{CBC_NS}}}CompanyID", inv.supplier_org_number, schemeID="0192")

    # Buyer
    buyer = _el(root, f"{{{CAC_NS}}}AccountingCustomerParty")
    bp = _el(buyer, f"{{{CAC_NS}}}Party")
    bp_id = _el(bp, f"{{{CAC_NS}}}PartyIdentification")
    _el(bp_id, f"{{{CBC_NS}}}ID", inv.buyer_org_number, schemeID="0192")
    bp_name = _el(bp, f"{{{CAC_NS}}}PartyName")
    _el(bp_name, f"{{{CBC_NS}}}Name", inv.buyer_name)
    bp_legal = _el(bp, f"{{{CAC_NS}}}PartyLegalEntity")
    _el(bp_legal, f"{{{CBC_NS}}}RegistrationName", inv.buyer_name)

    # Tax totals
    tax_total = _el(root, f"{{{CAC_NS}}}TaxTotal")
    _el(tax_total, f"{{{CBC_NS}}}TaxAmount", str(inv.total_vat), currencyID=inv.currency)

    vat_groups: dict[str, Decimal] = {}
    vat_taxable: dict[str, Decimal] = {}
    for line in inv.lines:
        key = str(line.vat_rate)
        vat_groups[key] = vat_groups.get(key, Decimal("0")) + line.vat_amount
        vat_taxable[key] = vat_taxable.get(key, Decimal("0")) + line.line_amount

    for rate_str in sorted(vat_groups.keys()):
        subtax = _el(tax_total, f"{{{CAC_NS}}}TaxSubtotal")
        _el(subtax, f"{{{CBC_NS}}}TaxableAmount", str(vat_taxable[rate_str]), currencyID=inv.currency)
        _el(subtax, f"{{{CBC_NS}}}TaxAmount", str(vat_groups[rate_str]), currencyID=inv.currency)
        tc = _el(subtax, f"{{{CAC_NS}}}TaxCategory")
        _el(tc, f"{{{CBC_NS}}}ID", "S")
        _el(tc, f"{{{CBC_NS}}}Percent", rate_str)
        ts = _el(tc, f"{{{CAC_NS}}}TaxScheme")
        _el(ts, f"{{{CBC_NS}}}ID", "VAT")

    # Legal monetary total
    lmt = _el(root, f"{{{CAC_NS}}}LegalMonetaryTotal")
    _el(lmt, f"{{{CBC_NS}}}LineExtensionAmount", str(inv.subtotal), currencyID=inv.currency)
    _el(lmt, f"{{{CBC_NS}}}TaxExclusiveAmount", str(inv.subtotal), currencyID=inv.currency)
    _el(lmt, f"{{{CBC_NS}}}TaxInclusiveAmount", str(inv.total), currencyID=inv.currency)
    _el(lmt, f"{{{CBC_NS}}}PayableAmount", str(inv.total), currencyID=inv.currency)

    # Invoice lines
    for idx, line in enumerate(inv.lines, 1):
        il = _el(root, f"{{{CAC_NS}}}InvoiceLine")
        _el(il, f"{{{CBC_NS}}}ID", str(idx))
        _el(il, f"{{{CBC_NS}}}InvoicedQuantity", str(line.quantity), unitCode="EA")
        _el(il, f"{{{CBC_NS}}}LineExtensionAmount", str(line.line_amount), currencyID=inv.currency)
        item = _el(il, f"{{{CAC_NS}}}Item")
        _el(item, f"{{{CBC_NS}}}Name", line.description)
        ct = _el(item, f"{{{CAC_NS}}}ClassifiedTaxCategory")
        _el(ct, f"{{{CBC_NS}}}ID", "S")
        _el(ct, f"{{{CBC_NS}}}Percent", str(line.vat_rate))
        cts = _el(ct, f"{{{CAC_NS}}}TaxScheme")
        _el(cts, f"{{{CBC_NS}}}ID", "VAT")
        price = _el(il, f"{{{CAC_NS}}}Price")
        _el(price, f"{{{CBC_NS}}}PriceAmount", str(line.unit_price), currencyID=inv.currency)

    tree = ET.ElementTree(root)
    buf = io.BytesIO()
    tree.write(buf, xml_declaration=True, encoding="UTF-8")
    return buf.getvalue().decode("utf-8")


def parse_ehf_xml(xml_content: str) -> EHFInvoice:
    root = ET.fromstring(xml_content)

    def find_text(el: ET.Element, path: str, default: str = "") -> str:
        found = el.find(path, {"cbc": CBC_NS, "cac": CAC_NS, "": UBL_NS})
        return found.text if found is not None and found.text else default

    invoice_number = find_text(root, f"{{{CBC_NS}}}ID")
    issue_date_str = find_text(root, f"{{{CBC_NS}}}IssueDate")
    due_date_str = find_text(root, f"{{{CBC_NS}}}DueDate")
    currency = find_text(root, f"{{{CBC_NS}}}DocumentCurrencyCode", "NOK")
    note = find_text(root, f"{{{CBC_NS}}}Note")

    issue_date = date.fromisoformat(issue_date_str) if issue_date_str else date.today()
    due_date = date.fromisoformat(due_date_str) if due_date_str else issue_date + timedelta(days=30)

    ns = {"cbc": CBC_NS, "cac": CAC_NS}

    supplier_party = root.find(f"{{{CAC_NS}}}AccountingSupplierParty/{{{CAC_NS}}}Party", ns)
    supplier_name = ""
    supplier_org = ""
    supplier_address = ""
    supplier_city = ""
    supplier_postal = ""
    if supplier_party is not None:
        sn = supplier_party.find(f"{{{CAC_NS}}}PartyName/{{{CBC_NS}}}Name", ns)
        supplier_name = sn.text if sn is not None and sn.text else ""
        si = supplier_party.find(f"{{{CAC_NS}}}PartyIdentification/{{{CBC_NS}}}ID", ns)
        supplier_org = si.text if si is not None and si.text else ""
        addr = supplier_party.find(f"{{{CAC_NS}}}PostalAddress", ns)
        if addr is not None:
            sa = addr.find(f"{{{CBC_NS}}}StreetName", ns)
            supplier_address = sa.text if sa is not None and sa.text else ""
            sc = addr.find(f"{{{CBC_NS}}}CityName", ns)
            supplier_city = sc.text if sc is not None and sc.text else ""
            sp = addr.find(f"{{{CBC_NS}}}PostalZone", ns)
            supplier_postal = sp.text if sp is not None and sp.text else ""

    buyer_party = root.find(f"{{{CAC_NS}}}AccountingCustomerParty/{{{CAC_NS}}}Party", ns)
    buyer_name = ""
    buyer_org = ""
    if buyer_party is not None:
        bn = buyer_party.find(f"{{{CAC_NS}}}PartyName/{{{CBC_NS}}}Name", ns)
        buyer_name = bn.text if bn is not None and bn.text else ""
        bi = buyer_party.find(f"{{{CAC_NS}}}PartyIdentification/{{{CBC_NS}}}ID", ns)
        buyer_org = bi.text if bi is not None and bi.text else ""

    lines = []
    for il in root.findall(f"{{{CAC_NS}}}InvoiceLine", ns):
        desc_el = il.find(f"{{{CAC_NS}}}Item/{{{CBC_NS}}}Name", ns)
        desc = desc_el.text if desc_el is not None and desc_el.text else ""
        qty_el = il.find(f"{{{CBC_NS}}}InvoicedQuantity", ns)
        qty = Decimal(qty_el.text) if qty_el is not None and qty_el.text else Decimal("1")
        price_el = il.find(f"{{{CAC_NS}}}Price/{{{CBC_NS}}}PriceAmount", ns)
        price = Decimal(price_el.text) if price_el is not None and price_el.text else Decimal("0")
        vat_el = il.find(f"{{{CAC_NS}}}Item/{{{CAC_NS}}}ClassifiedTaxCategory/{{{CBC_NS}}}Percent", ns)
        vat_rate = Decimal(vat_el.text) if vat_el is not None and vat_el.text else Decimal("25")

        lines.append(EHFLineItem(
            description=desc,
            quantity=qty,
            unit_price=price,
            vat_rate=vat_rate,
        ))

    return EHFInvoice(
        invoice_number=invoice_number,
        issue_date=issue_date,
        due_date=due_date,
        supplier_name=supplier_name,
        supplier_org_number=supplier_org,
        supplier_address=supplier_address,
        supplier_city=supplier_city,
        supplier_postal_code=supplier_postal,
        buyer_name=buyer_name,
        buyer_org_number=buyer_org,
        currency=currency,
        lines=lines,
        note=note,
    )


# NS 4102 hotel account mapping: expense description keywords → account code
EXPENSE_ACCOUNT_MAP = [
    (["frokost", "breakfast"], "4010"),
    (["alkohol", "vin", "øl", "spirits"], "4030"),
    (["minibar"], "4100"),
    (["mat", "food", "matvare", "dagligvare", "kjøtt", "fisk", "grønnsak"], "4000"),
    (["drikke", "beverage", "brus", "mineralvann", "kaffe"], "4020"),
    (["gave", "representasjon", "gift"], "4080"),
    (["vare", "innkjøp", "purchase", "supply"], "4300"),
    (["frakt", "transport", "shipping", "freight"], "6100"),
    (["leie", "husleie", "rent", "lokale"], "6300"),
    (["leasing"], "6310"),
    (["strøm", "energi", "electricity", "power", "fjernvarme", "lys", "varme"], "6340"),
    (["renovasjon", "kommunale", "vann", "avløp", "avgift"], "6360"),
    (["vedlikehold bygg", "building maintenance"], "6600"),
    (["vedlikehold", "maintenance", "repair", "reparasjon"], "6600"),
    (["inventar", "furniture"], "6540"),
    (["verktøy", "tools", "utstyr", "equipment"], "6500"),
    (["rengjøring", "renhold", "såpe", "sengetøy", "linnet", "linen", "cleaning"], "6555"),
    (["vaskeri", "laundry"], "6705"),
    (["sikkerhet", "vakt", "security"], "6710"),
    (["regnskap", "revisjon", "accounting", "audit"], "6720"),
    (["juridisk", "legal", "advokat"], "6740"),
    (["kontor", "office", "rekvisita", "papir"], "6800"),
    (["møte", "kurs", "training", "course"], "6860"),
    (["telefon", "mobil", "phone"], "6900"),
    (["internett", "internet", "bredbånd", "wifi", "it-tjeneste"], "6950"),
    (["bil", "drivstoff", "bensin", "diesel"], "7000"),
    (["booking.com", "expedia", "ota", "provisjon"], "7320"),
    (["trykk", "brosjyre", "print"], "7350"),
    (["markedsføring", "marketing", "reklame", "annonse"], "7300"),
    (["forsikring", "insurance"], "7400"),
    (["lisens", "software", "abonnement", "subscription"], "7600"),
    (["bank", "gebyr", "kortprovisjon", "fee"], "7700"),
    (["rente", "interest"], "8140"),
]


def suggest_account_code(description: str) -> str:
    desc_lower = description.lower()
    for keywords, code in EXPENSE_ACCOUNT_MAP:
        if any(kw in desc_lower for kw in keywords):
            return code
    return "4300"


SAMPLE_SUPPLIERS = [
    {
        "name": "Asko Norge AS",
        "org": "962807822",
        "address": "Industriveien 32",
        "city": "Vestby",
        "postal": "1540",
        "lines": [
            EHFLineItem("Matvarer — kjøtt og fisk", Decimal("1"), Decimal("18450.00"), Decimal("15"), "4000"),
            EHFLineItem("Matvarer — grønnsaker og frukt", Decimal("1"), Decimal("8230.00"), Decimal("15"), "4000"),
            EHFLineItem("Drikkevarer — mineralvann og juice", Decimal("1"), Decimal("3200.00"), Decimal("15"), "4020"),
        ],
    },
    {
        "name": "Hafslund Strøm AS",
        "org": "984388250",
        "address": "Drammensveien 144",
        "city": "Oslo",
        "postal": "0277",
        "lines": [
            EHFLineItem("Strøm — lys og varme april 2026", Decimal("1"), Decimal("12800.00"), Decimal("25"), "6340"),
        ],
    },
    {
        "name": "Telenor Norge AS",
        "org": "988312495",
        "address": "Snarøyveien 30",
        "city": "Fornebu",
        "postal": "1360",
        "lines": [
            EHFLineItem("Bedriftsabonnement 4 linjer — april", Decimal("1"), Decimal("3196.00"), Decimal("25"), "6900"),
            EHFLineItem("Bredbånd 500/500 hotellet — april", Decimal("1"), Decimal("899.00"), Decimal("25"), "6950"),
        ],
    },
    {
        "name": "Vectura Vinmonopolet AS",
        "org": "913746548",
        "address": "Oslovegen 16",
        "city": "Gjøvik",
        "postal": "2815",
        "lines": [
            EHFLineItem("Vin — leveranse til hotellbar", Decimal("1"), Decimal("14800.00"), Decimal("25"), "4030"),
            EHFLineItem("Spirit og likør", Decimal("1"), Decimal("6200.00"), Decimal("25"), "4030"),
        ],
    },
    {
        "name": "Gjensidige Forsikring ASA",
        "org": "995568217",
        "address": "Schweigaards gate 21",
        "city": "Oslo",
        "postal": "0191",
        "lines": [
            EHFLineItem("Næringsforsikring hotell — april kvartal", Decimal("1"), Decimal("8750.00"), Decimal("0"), "7400"),
        ],
    },
    {
        "name": "Norsk Vaskeri AS",
        "org": "914778390",
        "address": "Karvesvingen 5",
        "city": "Oslo",
        "postal": "0579",
        "lines": [
            EHFLineItem("Vask av sengetøy, håndklær — april", Decimal("1"), Decimal("8400.00"), Decimal("25"), "6705"),
            EHFLineItem("Uniformvask — april", Decimal("1"), Decimal("2100.00"), Decimal("25"), "6705"),
        ],
    },
    {
        "name": "Lilleborg Profesjonell AS",
        "org": "965067401",
        "address": "Nils Hansens vei 13",
        "city": "Oslo",
        "postal": "0667",
        "lines": [
            EHFLineItem("Rengjøringsmidler og såpe", Decimal("1"), Decimal("4340.00"), Decimal("25"), "6555"),
            EHFLineItem("Linnet — håndklær og sengetøy", Decimal("1"), Decimal("3890.00"), Decimal("25"), "6555"),
        ],
    },
    {
        "name": "Booking.com BV",
        "org": "976104026",
        "address": "Herengracht 597",
        "city": "Amsterdam",
        "postal": "1017",
        "lines": [
            EHFLineItem("Provisjon bookinger april 2026", Decimal("1"), Decimal("18600.00"), Decimal("25"), "7320"),
        ],
    },
    {
        "name": "Securitas AS",
        "org": "983154823",
        "address": "Karenslyst Allé 56",
        "city": "Oslo",
        "postal": "0277",
        "lines": [
            EHFLineItem("Vakthold hotell — april", Decimal("1"), Decimal("5600.00"), Decimal("25"), "6710"),
        ],
    },
    {
        "name": "Nordea Bank Abp, filial i Norge",
        "org": "983258853",
        "address": "Essendrops gate 7",
        "city": "Oslo",
        "postal": "0368",
        "lines": [
            EHFLineItem("Kortterminal og kortprovisjon — april", Decimal("1"), Decimal("3200.00"), Decimal("0"), "7700"),
            EHFLineItem("Nettbanktjenester — april", Decimal("1"), Decimal("450.00"), Decimal("0"), "7700"),
        ],
    },
]


def generate_sample_invoices(buyer_name: str = "Test Hotell AS",
                              buyer_org: str = "974760673") -> list[EHFInvoice]:
    invoices = []
    base_date = date(2026, 4, 1)
    for i, supplier in enumerate(SAMPLE_SUPPLIERS):
        inv = EHFInvoice(
            invoice_number=f"EHF-2026-{1001 + i}",
            issue_date=base_date + timedelta(days=i * 2),
            due_date=base_date + timedelta(days=30 + i * 2),
            supplier_name=supplier["name"],
            supplier_org_number=supplier["org"],
            supplier_address=supplier["address"],
            supplier_city=supplier["city"],
            supplier_postal_code=supplier["postal"],
            buyer_name=buyer_name,
            buyer_org_number=buyer_org,
            lines=supplier["lines"],
        )
        invoices.append(inv)
    return invoices
