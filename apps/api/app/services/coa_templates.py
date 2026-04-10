import json
import os
from sqlalchemy.orm import Session
from app.models import Account, Client

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "coa_templates")


def load_template(template_name: str) -> dict | None:
    """Load COA template from JSON file."""
    path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def apply_template(client_id: int, agency_id: int, template: dict, db: Session) -> int:
    """Apply a COA template to a client, creating all accounts."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("Client not found")

    count = 0
    account_map: dict[str, int] = {}

    for acc_data in template.get("accounts", []):
        account = Account(
            agency_id=agency_id,
            client_id=client_id,
            account_number=acc_data["account_number"],
            name=acc_data["name"],
            account_type=acc_data["account_type"],
            description=acc_data.get("description"),
            is_active="active",
            balance=0,
        )
        db.add(account)
        db.flush()
        account_map[acc_data["account_number"]] = account.id
        count += 1

    # Set parent relationships
    for acc_data in template.get("accounts", []):
        parent_number = acc_data.get("parent_account_number")
        if parent_number and parent_number in account_map:
            account = db.query(Account).filter(
                Account.account_number == acc_data["account_number"],
                Account.client_id == client_id,
            ).first()
            if account:
                account.parent_account_id = account_map[parent_number]

    db.commit()
    return count
