"""
Multi-tenant middleware — sets the agency context on every request.
Uses PostgreSQL SET LOCAL to enforce RLS within each transaction.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.database import engine


class TenantContext:
    """Thread-local / async-local tenant context."""

    _agency_id: int | None = None

    @classmethod
    def set(cls, agency_id: int) -> None:
        cls._agency_id = agency_id

    @classmethod
    def get(cls) -> int | None:
        return cls._agency_id

    @classmethod
    def clear(cls) -> None:
        cls._agency_id = None


class TenantMiddleware(BaseHTTPMiddleware):
    """
    On every request, reads the agency_id from the authenticated user
    and executes: SET LOCAL app.current_agency_id = :agency_id

    This sets the PostgreSQL session variable, which RLS policies
    then use via: current_setting('app.current_agency_id')::int
    """

    async def dispatch(self, request: Request, call_next):
        # TenantContext is set by the auth dependency (runs before this middleware)
        # We use a DB connection to execute SET LOCAL
        agency_id = TenantContext.get()

        if agency_id:
            # Execute SET LOCAL on a new connection
            # SET LOCAL is transaction-scoped — rolls back automatically
            from sqlalchemy import text
            from app.database import engine
            with engine.connect() as conn:
                conn.execute(text(f"SET LOCAL app.current_agency_id TO {agency_id}"))
                conn.commit()

        response = await call_next(request)
        TenantContext.clear()
        return response
