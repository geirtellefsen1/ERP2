"""
Auth0 JWT validation — validates access tokens on every request.
Extracts: agency_id, user_id, role from the JWT claims.
"""

import httpx
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from app.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


class AuthUser(BaseModel):
    sub: str  # Auth0 subject (user ID)
    agency_id: int
    role: str
    email: str | None = None


# Cache JWKS to avoid fetching on every request
_jwks_cache: dict | None = None


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


def decode_token(token: str, jwks: dict) -> dict:
    """Decode and validate a JWT using Auth0's JWKS."""
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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthUser:
    """
    Dependency — validates JWT and returns the authenticated user.
    Raises 401 if missing or invalid.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = credentials.credentials

    try:
        jwks = await get_jwks()
        claims = decode_token(token, jwks)
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {e}")

    # Map Auth0 claims → internal AuthUser
    agency_id = claims.get("https://bponexus.com/agency_id")
    if not agency_id:
        raise HTTPException(status_code=403, detail="Missing agency_id in token")

    return AuthUser(
        sub=claims["sub"],
        agency_id=agency_id,
        role=claims.get("https://bponexus.com/role", "agent"),
        email=claims.get("email"),
    )


async def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthUser | None:
    """Returns user if token is valid, None otherwise."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
