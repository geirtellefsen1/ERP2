"""
Professional Services vertical module.

Law firms, consulting shops, accountants — all run on a matter-based
time tracking model. This module adds:

  - Matters: the unit of client work (one project, one case)
  - Fee earners: people who log time against matters
  - Billing rates: a matrix of rates per grade × matter type × client
  - WIP entries: time logged but not yet billed
  - WIP aging: dashboard rollup showing unbilled time by age bucket
  - Trust accounts: three-way reconciliation (law firms only)

Nordic billing norms are supported out of the box:
  Norway:  hourly rates NOK 1,500–5,000 + 25% VAT
  Sweden:  hourly rates SEK 1,500–5,000 + 25% VAT, contingency fees restricted
  Finland: hourly rates EUR 150–500 + 25.5% VAT, legal aid billing integration
"""
from .models import (
    Matter,
    FeeEarner,
    BillingRate,
    WipEntry,
    MatterStatus,
    WipStatus,
    Grade,
)
from .time_tracking import (
    log_time,
    validate_time_entry,
    TimeEntryError,
    MINIMUM_INCREMENT,
)
from .wip import (
    calculate_wip,
    age_wip_entries,
    WipAgingReport,
    WipAgingBucket,
)
from .billing_rates import (
    resolve_rate,
    BillingRateMatrix,
    RateResolutionError,
)

__all__ = [
    "Matter",
    "FeeEarner",
    "BillingRate",
    "WipEntry",
    "MatterStatus",
    "WipStatus",
    "Grade",
    "log_time",
    "validate_time_entry",
    "TimeEntryError",
    "MINIMUM_INCREMENT",
    "calculate_wip",
    "age_wip_entries",
    "WipAgingReport",
    "WipAgingBucket",
    "resolve_rate",
    "BillingRateMatrix",
    "RateResolutionError",
]
