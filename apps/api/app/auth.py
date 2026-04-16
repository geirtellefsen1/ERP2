"""Authentication helpers.

Provides a ``get_current_user`` FastAPI dependency that downstream
routers can import.  Decodes JWT Bearer tokens issued by the auth
router, falling back to header-based auth for dev/test proxies.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """Minimal user context extracted from the request."""
    id: int
    agency_id: int
    email: str
    role: str


# Backward-compatible alias used by many existing routers.
AuthUser = CurrentUser


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    x_user_id: Optional[str] = Header(None),
    x_agency_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
) -> CurrentUser:
    """Extract user identity from a JWT Bearer token or request headers.

    Primary path: decode the JWT from ``Authorization: Bearer <token>``.
    Fallback: read ``x-user-id`` / ``x-agency-id`` headers (useful for
    dev proxies and integration tests that don't issue JWTs).
    """
    if credentials and credentials.credentials:
        try:
            from jose import jwt
            from app.services.jwt_signing import get_signing_key

            payload = jwt.decode(
                credentials.credentials,
                get_signing_key(),
                algorithms=["HS256"],
            )
            return CurrentUser(
                id=int(payload["sub"]),
                agency_id=int(payload["agency_id"]),
                email=payload.get("email", ""),
                role=payload.get("role", "admin"),
            )
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    if x_user_id and x_agency_id:
        return CurrentUser(
            id=int(x_user_id),
            agency_id=int(x_agency_id),
            email=x_user_email or "",
            role=x_user_role or "admin",
        )

    raise HTTPException(status_code=401, detail="Not authenticated")
