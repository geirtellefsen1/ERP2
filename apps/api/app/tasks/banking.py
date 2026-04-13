"""
Banking-related background tasks.

The critical path is `sync_agency`: given an agency, use the configured
banking adapter to fetch transactions for each linked BankAccount over
the past N days and upsert them into the bank_transactions table.
`sync_all_agencies` fans out to every agency with banking configured.

Error strategy: we catch provider errors per-agency so one bad config
never blocks the whole sweep. Logged + counted + the task keeps going.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from celery import shared_task
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Agency, BankAccount, BankTransaction, Client, IntegrationConfig
from app.services.banking import BankingError, get_banking_adapter

logger = logging.getLogger(__name__)

# How many days back to ask the provider for on each sync.
DEFAULT_LOOKBACK_DAYS = 7


def _db_session() -> Session:
    """Task-owned DB session. Tasks always close their own sessions."""
    return SessionLocal()


def _agencies_with_banking(db: Session) -> list[Agency]:
    """Every agency that has any banking integration configured."""
    ids = (
        db.query(IntegrationConfig.agency_id)
        .filter(IntegrationConfig.provider.in_(["aiia", "tink"]))
        .distinct()
        .all()
    )
    agency_ids = [row[0] for row in ids]
    if not agency_ids:
        return []
    return db.query(Agency).filter(Agency.id.in_(agency_ids)).all()


def _upsert_transaction(
    db: Session,
    account: BankAccount,
    provider_tx,
) -> bool:
    """
    Upsert one provider transaction into bank_transactions.
    Returns True if a new row was inserted, False if it already existed.
    """
    existing = (
        db.query(BankTransaction)
        .filter(
            BankTransaction.account_id == account.id,
            BankTransaction.external_id == provider_tx.provider_transaction_id,
        )
        .first()
    )
    if existing:
        return False

    amount = provider_tx.amount.amount
    if provider_tx.direction == "outflow" and amount > 0:
        amount = -amount

    row = BankTransaction(
        account_id=account.id,
        external_id=provider_tx.provider_transaction_id,
        date=datetime.combine(provider_tx.date, datetime.min.time(), tzinfo=timezone.utc),
        description=provider_tx.description,
        amount=amount,
        reference=provider_tx.reference,
        category=provider_tx.category or None,
        status="unmatched",
    )
    db.add(row)
    return True


@shared_task(
    name="app.tasks.banking.sync_agency",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(BankingError,),
    retry_backoff=True,
)
def sync_agency(
    self,
    agency_id: int,
    *,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    provider: str = "aiia",
) -> dict:
    """
    Pull transactions for every linked bank account at an agency and
    upsert them. Returns a small summary dict for logging/metrics.
    """
    db = _db_session()
    inserted = 0
    touched_accounts = 0
    try:
        adapter = get_banking_adapter(db, agency_id, provider=provider)

        # Every agency has many clients; every client has many local
        # BankAccount rows. We walk them and match on IBAN.
        accounts = (
            db.query(BankAccount)
            .join(Client, BankAccount.client_id == Client.id)
            .filter(Client.agency_id == agency_id, BankAccount.is_active.is_(True))
            .all()
        )
        if not accounts:
            return {
                "agency_id": agency_id,
                "provider": adapter.provider_name,
                "accounts_touched": 0,
                "transactions_inserted": 0,
                "note": "no active bank accounts",
            }

        provider_accounts = {
            a.iban: a for a in adapter.list_accounts() if a.iban
        }

        today = date.today()
        since = today - timedelta(days=lookback_days)

        for local_acct in accounts:
            matched = provider_accounts.get(local_acct.account_number or "")
            if not matched:
                continue
            touched_accounts += 1
            txs = adapter.fetch_transactions(
                matched.provider_account_id, since=since, until=today
            )
            for tx in txs:
                if _upsert_transaction(db, local_acct, tx):
                    inserted += 1

        db.commit()
        return {
            "agency_id": agency_id,
            "provider": adapter.provider_name,
            "accounts_touched": touched_accounts,
            "transactions_inserted": inserted,
        }
    except BankingError:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("sync_agency failed agency_id=%s", agency_id)
        raise
    finally:
        db.close()


@shared_task(name="app.tasks.banking.sync_all_agencies")
def sync_all_agencies(lookback_days: int = DEFAULT_LOOKBACK_DAYS) -> dict:
    """
    Fan out to every agency that has a banking integration configured.
    One bad agency doesn't block the rest — errors are logged and counted.
    """
    db = _db_session()
    try:
        agencies = _agencies_with_banking(db)
    finally:
        db.close()

    dispatched = 0
    failed = 0
    for agency in agencies:
        try:
            sync_agency.apply_async(
                args=(agency.id,),
                kwargs={"lookback_days": lookback_days},
                queue="banking",
            )
            dispatched += 1
        except Exception:
            failed += 1
            logger.exception("failed to enqueue sync for agency_id=%s", agency.id)

    return {"agencies_found": len(agencies), "dispatched": dispatched, "failed": failed}
