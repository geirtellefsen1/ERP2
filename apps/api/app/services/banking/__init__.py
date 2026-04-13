"""
Open banking adapter layer.

Abstract BankingAdapter interface + live adapters for each provider.
Tier 5 ships Aiia (Nordic coverage: Norway, Sweden, Finland) as the
primary adapter, with Tink as a backup for Sweden.

In dev/test we use MockBankingAdapter which returns deterministic
transaction data — the rest of the pipeline (reconciliation, journal
posting, AI matching) runs identically against it.
"""
from .base import (
    BankingAdapter,
    BankingError,
    BankAccount,
    BankTransaction,
    TransactionDirection,
)
from .mock import MockBankingAdapter
from .aiia import AiiaBankingAdapter
from .factory import get_banking_adapter

__all__ = [
    "BankingAdapter",
    "BankingError",
    "BankAccount",
    "BankTransaction",
    "TransactionDirection",
    "MockBankingAdapter",
    "AiiaBankingAdapter",
    "get_banking_adapter",
]
