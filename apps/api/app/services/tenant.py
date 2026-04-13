"""
Tenant context helper — sets the Postgres session variable that RLS
policies read to decide which rows are visible.

Usage in routers:
    from app.services.tenant import set_tenant_context

    def my_route(
        db: Session = Depends(get_db),
        current_user: AuthUser = Depends(get_current_user),
    ):
        set_tenant_context(db, current_user.agency_id)
        # ... all queries are now scoped to current_user.agency_id ...

Or as a context manager for scripts and background jobs:
    with tenant_scope(db, agency_id=42):
        ...

For admin bypass (migrations, seed script, cross-tenant reports):
    set_tenant_context(db, 0)  # 0 = admin, sees all rows
"""
from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session


ADMIN_BYPASS = 0


def set_tenant_context(db: Session, agency_id: int) -> None:
    """
    Set the current tenant for the duration of this Postgres session.

    RLS policies read `app.current_agency_id` and return only rows whose
    `agency_id` (or the agency_id of their parent client) matches. Pass 0
    to bypass RLS entirely (admin/system scope).

    SET LOCAL is used so the variable is rolled back at the end of the
    transaction — no leakage into the next request served by the same
    connection from the pool.
    """
    if agency_id is None:
        raise ValueError("agency_id must not be None — use 0 for admin bypass")
    if not isinstance(agency_id, int):
        raise TypeError(f"agency_id must be int, got {type(agency_id).__name__}")
    # Use a parameterised-style call via f-string since SET LOCAL doesn't
    # accept bind parameters. Safe because we typecheck agency_id above.
    db.execute(text(f"SET LOCAL app.current_agency_id = {agency_id}"))


@contextmanager
def tenant_scope(db: Session, agency_id: int):
    """Context manager that enters and exits a tenant scope within a transaction."""
    # Start a nested transaction (SAVEPOINT) so we can roll back just the
    # SET LOCAL on exit.
    set_tenant_context(db, agency_id)
    try:
        yield
    finally:
        # SET LOCAL auto-resets at transaction end, but we also explicitly
        # reset to keep pool-reuse safe.
        db.execute(text("RESET app.current_agency_id"))


@contextmanager
def admin_scope(db: Session):
    """Context manager for admin-scope queries (bypass RLS)."""
    with tenant_scope(db, ADMIN_BYPASS):
        yield
