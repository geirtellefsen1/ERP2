import csv
import io
from sqlalchemy.orm import Session
from app.models import Account


def import_csv(client_id: int, agency_id: int, content: bytes, db: Session) -> dict:
    """Import accounts from a CSV file.

    Expected columns: account_number, name, account_type, description
    """
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0
    errors: list[str] = []

    for row_num, row in enumerate(reader, start=2):
        account_number = row.get("account_number", "").strip()
        name = row.get("name", "").strip()
        account_type = row.get("account_type", "").strip().lower()

        if not account_number or not name:
            errors.append(f"Row {row_num}: missing account_number or name")
            skipped += 1
            continue

        if account_type not in ("asset", "liability", "equity", "revenue", "expense"):
            errors.append(f"Row {row_num}: invalid account_type '{account_type}'")
            skipped += 1
            continue

        # Check for duplicate
        existing = db.query(Account).filter(
            Account.client_id == client_id,
            Account.account_number == account_number,
        ).first()

        if existing:
            skipped += 1
            continue

        account = Account(
            agency_id=agency_id,
            client_id=client_id,
            account_number=account_number,
            name=name,
            account_type=account_type,
            description=row.get("description", "").strip() or None,
            is_active="active",
            balance=0,
        )
        db.add(account)
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}
