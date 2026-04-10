import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from app.models import Account


# Xero account type mapping
XERO_TYPE_MAP = {
    "BANK": "asset",
    "CURRENT": "asset",
    "CURRLIAB": "liability",
    "EQUITY": "equity",
    "REVENUE": "revenue",
    "DIRECTCOSTS": "expense",
    "EXPENSE": "expense",
    "OVERHEADS": "expense",
    "DEPRECIATN": "expense",
    "OTHERINCOME": "revenue",
    "TERMLIAB": "liability",
    "FIXED": "asset",
    "INVENTORY": "asset",
    "PREPAYMENT": "asset",
    "SALES": "revenue",
    "LIABILITY": "liability",
    "NONCURRENT": "asset",
}


def parse_xero_xml(client_id: int, agency_id: int, content: bytes, db: Session) -> dict:
    """Parse a Xero-format Chart of Accounts XML and create accounts."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        return {"error": f"Invalid XML: {str(e)}", "created": 0}

    created = 0
    skipped = 0
    errors: list[str] = []

    # Try different possible root structures
    accounts_elem = root.findall(".//Account") or root.findall(".//account")

    for acc_elem in accounts_elem:
        code = (acc_elem.findtext("Code") or acc_elem.findtext("code") or "").strip()
        name = (acc_elem.findtext("Name") or acc_elem.findtext("name") or "").strip()
        xero_type = (acc_elem.findtext("Type") or acc_elem.findtext("type") or "").strip().upper()

        if not code or not name:
            skipped += 1
            continue

        account_type = XERO_TYPE_MAP.get(xero_type, "expense")

        existing = db.query(Account).filter(
            Account.client_id == client_id,
            Account.account_number == code,
        ).first()

        if existing:
            skipped += 1
            continue

        desc = (acc_elem.findtext("Description") or acc_elem.findtext("description") or "").strip()

        account = Account(
            agency_id=agency_id,
            client_id=client_id,
            account_number=code,
            name=name,
            account_type=account_type,
            description=desc or None,
            is_active="active",
            balance=0,
        )
        db.add(account)
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}
