"""
Hotel demo baseline — seeds a realistic Q1 (Jan-Mar) for a Norwegian legacy
hotel so the P&L and Balance Sheet have non-trivial opening balances before
the EHF import demo.

Numbers reflect a ~25-room legacy hotel: owns the property, has a mortgage,
mixed revenue across rom (12% MVA), mat (15%), alkohol/minibar/konferanse
(25%), and typical Q1 cost structure with heavy winter energy + payroll.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Account, JournalEntry, JournalLine, Client


Dec = Decimal


@dataclass
class Posting:
    code: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    description: str = ""


def _post(
    db: Session,
    client_id: int,
    user_id: int,
    accounts_by_code: dict[str, Account],
    entry_date: datetime,
    description: str,
    reference: str,
    postings: list[Posting],
) -> JournalEntry:
    entry = JournalEntry(
        client_id=client_id,
        entry_date=entry_date,
        description=description,
        reference=reference,
        posted_by=user_id,
    )
    db.add(entry)
    db.flush()
    for p in postings:
        acct = accounts_by_code.get(p.code)
        if not acct:
            raise ValueError(f"Demo baseline requires account {p.code} to be seeded")
        db.add(
            JournalLine(
                entry_id=entry.id,
                account_id=acct.id,
                debit=p.debit,
                credit=p.credit,
                description=p.description or description,
            )
        )
    return entry


# Monthly revenue template (stable across Jan/Feb/Mar for demo clarity).
# Rom 12% MVA, Mat/frokost 15%, resten 25%.
def _revenue_postings(month_idx: int) -> list[Posting]:
    # month_idx: 0=Jan, 1=Feb, 2=Mar. Slight uptick toward spring.
    scale = {0: Dec("0.90"), 1: Dec("1.00"), 2: Dec("1.15")}[month_idx]

    rom_net = (Dec("310000") * scale).quantize(Dec("1"))
    frokost_net = (Dec("42000") * scale).quantize(Dec("1"))
    mat_net = (Dec("105000") * scale).quantize(Dec("1"))
    drikke_net = (Dec("48000") * scale).quantize(Dec("1"))
    alkohol_net = (Dec("35000") * scale).quantize(Dec("1"))
    minibar_net = (Dec("14000") * scale).quantize(Dec("1"))
    konferanse_net = (Dec("55000") * scale).quantize(Dec("1"))
    spa_net = (Dec("22000") * scale).quantize(Dec("1"))
    parkering_net = (Dec("8000") * scale).quantize(Dec("1"))

    vat_12 = rom_net * Dec("0.12")
    vat_15 = (frokost_net + mat_net) * Dec("0.15")
    vat_25 = (drikke_net + alkohol_net + minibar_net + konferanse_net + spa_net + parkering_net) * Dec("0.25")

    net_total = rom_net + frokost_net + mat_net + drikke_net + alkohol_net + minibar_net + konferanse_net + spa_net + parkering_net
    gross_total = net_total + vat_12 + vat_15 + vat_25

    return [
        Posting("1910", debit=gross_total, description="Salg innbetalt via kort/kontant"),
        Posting("3010", credit=rom_net, description="Romsinntekt"),
        Posting("3150", credit=frokost_net, description="Frokostinntekt"),
        Posting("3100", credit=mat_net, description="Matinntekt (restaurant)"),
        Posting("3200", credit=drikke_net, description="Drikke/bar"),
        Posting("3250", credit=alkohol_net, description="Alkoholsalg"),
        Posting("3300", credit=minibar_net, description="Minibar"),
        Posting("3400", credit=konferanse_net, description="Konferansesal"),
        Posting("3500", credit=spa_net, description="SPA og velvære"),
        Posting("3600", credit=parkering_net, description="Parkering"),
        Posting("2728", credit=vat_12.quantize(Dec("0.01")), description="Utgående MVA 12%"),
        Posting("2725", credit=vat_15.quantize(Dec("0.01")), description="Utgående MVA 15%"),
        Posting("2720", credit=vat_25.quantize(Dec("0.01")), description="Utgående MVA 25%"),
    ]


def _payroll_postings() -> list[Posting]:
    # 8-10 ansatte, blanding av fastlønn og timelønn
    fast_lonn = Dec("320000")
    time_lonn = Dec("85000")
    feriepenger = (fast_lonn + time_lonn) * Dec("0.12")  # 12% avsetning
    aga_sats = Dec("0.141")  # sone 1
    aga = (fast_lonn + time_lonn) * aga_sats
    aga_feriepenger = feriepenger * aga_sats
    total = fast_lonn + time_lonn + feriepenger + aga + aga_feriepenger
    return [
        Posting("5010", debit=fast_lonn, description="Fast lønn"),
        Posting("5020", debit=time_lonn, description="Timelønn deltid"),
        Posting("5090", debit=feriepenger.quantize(Dec("0.01")), description="Avsatt feriepenger 12%"),
        Posting("5400", debit=aga.quantize(Dec("0.01")), description="AGA 14,1% sone 1"),
        Posting("5420", debit=aga_feriepenger.quantize(Dec("0.01")), description="AGA feriepenger"),
        Posting("1910", credit=(fast_lonn + time_lonn), description="Nettolønn utbetalt"),
        Posting("2780", credit=feriepenger.quantize(Dec("0.01")), description="Skyldig feriepenger"),
        Posting("2770", credit=(aga + aga_feriepenger).quantize(Dec("0.01")), description="Skyldig AGA"),
    ]


def _cogs_postings() -> list[Posting]:
    # Varekjøp månedlig — på kreditt (AP), betales senere
    mat = Dec("148000")
    frokost = Dec("24000")
    drikke = Dec("32000")
    alkohol = Dec("28000")
    minibar = Dec("8500")
    mat_vat = (mat + frokost + drikke) * Dec("0.15")
    ah_vat = (alkohol + minibar) * Dec("0.25")
    total_gross = mat + frokost + drikke + alkohol + minibar + mat_vat + ah_vat
    return [
        Posting("4000", debit=mat, description="Varekjøp mat (Asko o.l.)"),
        Posting("4010", debit=frokost, description="Varekjøp frokost"),
        Posting("4020", debit=drikke, description="Varekjøp drikke (ikke-alkohol)"),
        Posting("4030", debit=alkohol, description="Varekjøp alkohol"),
        Posting("4100", debit=minibar, description="Varekjøp minibar"),
        Posting("2710", debit=(mat_vat + ah_vat).quantize(Dec("0.01")), description="Inngående MVA varekjøp"),
        Posting("2400", credit=total_gross.quantize(Dec("0.01")), description="Leverandørgjeld"),
    ]


def _opex_postings() -> list[Posting]:
    # Månedlige driftskostnader — mix av bank og AP
    energi_net = Dec("18000")
    energi_vat = energi_net * Dec("0.25")
    kom = Dec("5500")
    rengjoring_net = Dec("6000")
    rengjoring_vat = rengjoring_net * Dec("0.25")
    linnet_net = Dec("4200")
    linnet_vat = linnet_net * Dec("0.25")
    vaskeri_net = Dec("10500")
    vaskeri_vat = vaskeri_net * Dec("0.25")
    telefon_net = Dec("2800")
    telefon_vat = telefon_net * Dec("0.25")
    internett_net = Dec("1500")
    internett_vat = internett_net * Dec("0.25")
    regnskap_net = Dec("8500")
    regnskap_vat = regnskap_net * Dec("0.25")
    booking_net = Dec("16500")
    booking_vat = booking_net * Dec("0.25")
    marketing_net = Dec("6000")
    marketing_vat = marketing_net * Dec("0.25")
    forsikring = Dec("6500")
    bankgebyr = Dec("2200")
    rente = Dec("28000")
    bygg_depr = Dec("50000")
    inv_depr = Dec("12500")

    # VAT to 2710 (standard input VAT)
    total_vat = (
        energi_vat + rengjoring_vat + linnet_vat + vaskeri_vat +
        telefon_vat + internett_vat + regnskap_vat + booking_vat + marketing_vat
    )

    # Split: bank-paid vs AP-accrued
    bank_paid = (
        energi_net + energi_vat + kom + telefon_net + telefon_vat +
        internett_net + internett_vat + marketing_net + marketing_vat +
        forsikring + bankgebyr + rente
    )
    ap_accrued = (
        rengjoring_net + rengjoring_vat + linnet_net + linnet_vat +
        vaskeri_net + vaskeri_vat + regnskap_net + regnskap_vat +
        booking_net + booking_vat
    )

    return [
        Posting("6000", debit=bygg_depr, description="Avskrivning bygg"),
        Posting("1117", credit=bygg_depr, description="Akkumulert avskrivning bygg"),
        Posting("6050", debit=inv_depr, description="Avskrivning inventar"),
        Posting("1250", credit=inv_depr, description="Akkumulert avskrivning inventar"),
        Posting("6340", debit=energi_net, description="Lys og varme"),
        Posting("6360", debit=kom, description="Kommunale avgifter"),
        Posting("6555", debit=rengjoring_net, description="Rengjøringsmidler"),
        Posting("6555", debit=linnet_net, description="Linnet og håndklær"),
        Posting("6705", debit=vaskeri_net, description="Vaskeritjenester"),
        Posting("6720", debit=regnskap_net, description="Regnskap og revisjon"),
        Posting("6900", debit=telefon_net, description="Telefon"),
        Posting("6950", debit=internett_net, description="Internett/IT"),
        Posting("7300", debit=marketing_net, description="Markedsføring"),
        Posting("7320", debit=booking_net, description="Booking.com-provisjon"),
        Posting("7400", debit=forsikring, description="Forsikring"),
        Posting("7700", debit=bankgebyr, description="Bankgebyrer + kortprovisjon"),
        Posting("8140", debit=rente, description="Renter pantelån"),
        Posting("2710", debit=total_vat.quantize(Dec("0.01")), description="Inngående MVA driftskostnader"),
        Posting("1910", credit=bank_paid.quantize(Dec("0.01")), description="Betalt fra driftskonto"),
        Posting("2400", credit=ap_accrued.quantize(Dec("0.01")), description="Leverandørgjeld"),
    ]


def _opening_postings() -> list[Posting]:
    # Åpningsbalanse 1. januar 2026 — legacy hotell, eier bygget
    return [
        # Assets
        Posting("1115", debit=Dec("2500000"), description="Tomt"),
        Posting("1117", debit=Dec("14000000"), description="Hotellbygning"),
        Posting("1250", debit=Dec("1800000"), description="Inventar (senger, møbler, kjøkken)"),
        Posting("1280", debit=Dec("350000"), description="Hotellvan"),
        Posting("1460", debit=Dec("185000"), description="Varelager mat/drikke"),
        Posting("1500", debit=Dec("125000"), description="Utestående fra kunder"),
        Posting("1900", debit=Dec("15000"), description="Kasse resepsjon"),
        Posting("1910", debit=Dec("620000"), description="Driftskonto DNB"),
        Posting("1950", debit=Dec("300000"), description="Høyrentekonto"),
        # Liabilities
        Posting("2220", credit=Dec("9500000"), description="Pantelån hotellbygg"),
        Posting("2240", credit=Dec("180000"), description="Billån"),
        Posting("2400", credit=Dec("215000"), description="Utestående leverandørgjeld"),
        # Equity
        Posting("2010", credit=Dec("500000"), description="Aksjekapital"),
        Posting("2050", credit=Dec("9500000"), description="Opptjent egenkapital"),
    ]


def seed_hotel_baseline(
    db: Session,
    client: Client,
    user_id: int,
    accounts_by_code: dict[str, Account],
) -> dict:
    """
    Creates 7 journal entries for Q1 2026:
      - Opening balance (1 Jan)
      - Jan/Feb/Mar revenue (last day of month)
      - Jan/Feb/Mar expenses (25th of month) — combined payroll + COGS + opex
    Refuses to seed if the client already has journal entries.
    """
    existing = db.query(JournalEntry).filter(JournalEntry.client_id == client.id).count()
    if existing > 0:
        return {"seeded": 0, "entries": 0, "reason": "client already has journal entries"}

    entries_created = 0

    # 1. Opening balance
    _post(
        db, client.id, user_id, accounts_by_code,
        entry_date=datetime(2026, 1, 1),
        description=f"Åpningsbalanse 2026 — {client.name}",
        reference="IB-2026",
        postings=_opening_postings(),
    )
    entries_created += 1

    # 2. Q1 monthly entries
    month_specs = [
        (0, datetime(2026, 1, 31), "Januar"),
        (1, datetime(2026, 2, 28), "Februar"),
        (2, datetime(2026, 3, 31), "Mars"),
    ]

    for idx, month_end, month_name in month_specs:
        _post(
            db, client.id, user_id, accounts_by_code,
            entry_date=month_end,
            description=f"Salgsinntekter {month_name} 2026",
            reference=f"REV-2026-{month_end.month:02d}",
            postings=_revenue_postings(idx),
        )
        entries_created += 1

        # Expenses: combine payroll + COGS + opex into one entry per month
        combined = _payroll_postings() + _cogs_postings() + _opex_postings()
        _post(
            db, client.id, user_id, accounts_by_code,
            entry_date=month_end,
            description=f"Driftskostnader {month_name} 2026",
            reference=f"OPEX-2026-{month_end.month:02d}",
            postings=combined,
        )
        entries_created += 1

    return {
        "seeded": entries_created,
        "entries": entries_created,
        "period": "Q1 2026",
        "hotel_name": client.name,
    }
