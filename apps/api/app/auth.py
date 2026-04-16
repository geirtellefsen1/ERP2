"""Authentication helpers.

Lightweight stub — will be expanded when Auth0/JWT integration lands.
Provides a ``get_current_user`` FastAPI dependency that downstream
routers can import today.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException


@dataclass
class CurrentUser:
    """Minimal user context extracted from the request."""
    id: int
    agency_id: int
    email: str
    role: str


async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    x_agency_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
) -> CurrentUser:
    """Extract user identity from request headers.

    In production this will validate a JWT; for now it reads simple
    headers so the onboarding (and other) routers can be tested without
    a full auth stack.
    """
    if not x_user_id or not x_agency_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return CurrentUser(
        id=int(x_user_id),
        agency_id=int(x_agency_id),
        email=x_user_email or "",
        role=x_user_role or "admin",
    )
