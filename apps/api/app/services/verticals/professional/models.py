"""Professional services data classes (value objects, not ORM models)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from app.services.money import Money


MatterStatus = Literal["open", "on_hold", "closed", "archived"]
WipStatus = Literal["unbilled", "draft_bill", "billed", "written_off"]
Grade = Literal["partner", "senior", "associate", "paralegal", "trainee"]
MatterType = Literal[
    "corporate",
    "litigation",
    "tax",
    "ip",
    "employment",
    "property",
    "advisory",
    "audit",
    "bookkeeping",
    "other",
]


@dataclass
class FeeEarner:
    id: int
    client_id: int                 # the BPO agency's OWN client (the law firm, consulting shop, etc.)
    name: str
    email: str
    grade: Grade
    default_hourly_rate: Money
    is_active: bool = True


@dataclass
class Matter:
    id: int
    client_id: int                 # the agency's client
    code: str                      # e.g. "ACME-2026-001"
    title: str
    matter_type: MatterType
    status: MatterStatus
    opened_on: date
    closed_on: Optional[date] = None
    partner_in_charge: Optional[int] = None  # FeeEarner id
    billing_contact: str = ""
    fixed_fee: Optional[Money] = None   # null for hourly matters
    retainer_balance: Optional[Money] = None


@dataclass
class BillingRate:
    id: int
    # Rate matrix key — any subset can be set
    grade: Optional[Grade] = None
    matter_type: Optional[MatterType] = None
    client_id: Optional[int] = None       # client-specific override
    matter_id: Optional[int] = None       # matter-specific override
    hourly_rate: Money = field(default_factory=lambda: Money.zero("NOK"))
    effective_from: date = field(default_factory=date.today)
    effective_to: Optional[date] = None


@dataclass
class WipEntry:
    id: int
    matter_id: int
    fee_earner_id: int
    worked_on: date
    hours: Decimal                 # must be multiples of 0.1
    hourly_rate: Money             # rate at time of entry (snapshot)
    description: str
    status: WipStatus = "unbilled"
    logged_at: datetime = field(default_factory=datetime.now)
    billed_at: Optional[datetime] = None
    written_off_at: Optional[datetime] = None

    @property
    def value(self) -> Money:
        return Money(
            self.hourly_rate.amount * self.hours,
            self.hourly_rate.currency,
        )
