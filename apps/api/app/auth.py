"""
JWT validation for authenticated requests.

Two token formats are supported:
  1. Internal HS256 tokens issued by app/routers/auth.py — signed with
     JWT_SIGNING_KEY and verified locally. This is the MVP flow.
  2. Auth0 RS256 tokens — verified via Auth0's JWKS endpoint. Only
     attempted when settings.auth0_domain is non-empty. When Auth0 is
     configured, tokens with an RS256 `alg` header are routed through
     the JWKS path.

The order matters: local tokens are cheap to verify (no network), so we
try them first. Auth0 fallback only happens if the internal verify fails
AND the token's header is RS256 AND Auth0 is configured.
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from pydantic import BaseModel

from app.config import get_settings
from app.services.jwt_signing import get_signing_key

logger = logging.getLogger(__name__)

settings = get_settings()
security = HTTPBearer(auto_error=False)

ALGORITHM_INTERNAL = "HS256"


class AuthUser(BaseModel):
    sub: str          # user id (as string)
    agency_id: int
    role: str
    email: Optional[str] = None


# ── JWKS cache (Auth0 path) ────────────────────────────────────────────

_jwks_cache: Optional[dict] = None


async def get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    jwks_url = f"https://{settings.auth0_domain}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_url, timeout=10.0)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache


def _decode_auth0_token(token: str, jwks: dict) -> dict:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
        raise JWTError("Missing kid in token header")

    key = None
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            key = k
            break
    if not key:
        raise JWTError(f"No matching key for kid={kid}")

    return jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=settings.auth0_audience,
        issuer=f"https://{settings.auth0_domain}/",
    )


def _decode_internal_token(token: str) -> dict:
    """Verify an internally-issued HS256 token."""
    key = get_signing_key()
    return jwt.decode(
        token,
        key,
        algorithms=[ALGORITHM_INTERNAL],
        # Audience + issuer are ignored for internal tokens — if we
        # wanted to enforce them we'd include them in create_access_token.
        options={"verify_aud": False, "verify_iss": False},
    )


# ── Dependency ─────────────────────────────────────────────────────────


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthUser:
    """
    FastAPI dependency — validates a JWT and returns the authenticated
    user. Raises 401 on any failure.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = credentials.credentials
    claims: Optional[dict] = None
    last_error: Optional[str] = None

    # Try internal HS256 first (fast, no network)
    try:
        claims = _decode_internal_token(token)
    except JWTError as e:
        last_error = f"Internal token invalid: {e}"

    # Fall back to Auth0 RS256 if configured
    if claims is None and settings.auth0_domain:
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") == "RS256":
                jwks = await get_jwks()
                claims = _decode_auth0_token(token, jwks)
        except JWTError as e:
            last_error = f"Auth0 token invalid: {e}"
        except httpx.HTTPError as e:
            logger.warning("Auth0 JWKS fetch failed: %s", e)
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable",
            )

    if claims is None:
        raise HTTPException(
            status_code=401,
            detail=last_error or "Invalid token",
        )

    # Extract claims — internal and Auth0 token shapes differ slightly.
    # Internal token: {sub, email, role, agency_id, ...}
    # Auth0 token:    {sub, email, https://bponexus.com/role, https://bponexus.com/agency_id}
    agency_id = claims.get("agency_id") or claims.get(
        "https://bponexus.com/agency_id"
    )
    if agency_id is None:
        raise HTTPException(status_code=403, detail="Missing agency_id in token")

    role = (
        claims.get("role")
        or claims.get("https://bponexus.com/role")
        or "agent"
    )

    return AuthUser(
        sub=str(claims.get("sub", "")),
        agency_id=int(agency_id),
        role=role,
        email=claims.get("email"),
    )


async def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthUser | None:
    """Return the user if a valid token is present, None otherwise."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
