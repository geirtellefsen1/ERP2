"""
OAuth router — Google and Microsoft social sign-in.

Flow (per provider):
  1. Frontend redirects user to GET /api/v1/auth/<provider>/login
  2. We generate a signed state token, then 302 redirect the user to the
     provider's authorization URL.
  3. Provider authenticates the user and redirects to
     /api/v1/auth/<provider>/callback?code=...&state=...
  4. We verify state, exchange the code for access tokens, fetch the user's
     profile, find or create the user (auto-creating an agency if new), then
     issue an internal JWT.
  5. We 302 redirect the user to <FRONTEND_URL>/auth/callback?token=...&user=...
  6. The frontend reads the token from the query string, stores it in
     localStorage, and routes to /dashboard.

This flow does NOT require Auth0 or any third-party identity service —
it talks directly to Google's and Microsoft's OAuth 2.0 endpoints.
"""

import secrets
import json
import base64
from datetime import datetime, timedelta, timezone
from typing import Literal
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agency, User
from app.config import get_settings
from app.routers.auth import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["oauth"])
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ProviderName = Literal["google", "microsoft"]

# ─── Provider configuration ────────────────────────────────────────────────────

PROVIDERS = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
    },
    "microsoft": {
        # Tenant is filled in at request time from settings.microsoft_tenant
        "auth_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid email profile User.Read",
    },
}


def _provider_config(provider: ProviderName) -> dict:
    cfg = dict(PROVIDERS[provider])
    if provider == "microsoft":
        cfg["auth_url"] = cfg["auth_url"].format(tenant=settings.microsoft_tenant)
        cfg["token_url"] = cfg["token_url"].format(tenant=settings.microsoft_tenant)
    return cfg


def _client_credentials(provider: ProviderName) -> tuple[str, str]:
    if provider == "google":
        return settings.google_client_id, settings.google_client_secret
    return settings.microsoft_client_id, settings.microsoft_client_secret


def _redirect_uri(provider: ProviderName) -> str:
    return f"{settings.oauth_redirect_base_url.rstrip('/')}/api/v1/auth/{provider}/callback"


# ─── Stateless state-token helpers ─────────────────────────────────────────────


def _create_state(provider: ProviderName, redirect_to: str = "/dashboard") -> str:
    """Issue a short-lived signed state token to prevent CSRF on the callback."""
    payload = {
        "provider": provider,
        "nonce": secrets.token_urlsafe(16),
        "redirect_to": redirect_to,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.oauth_state_secret, algorithm="HS256")


def _verify_state(state: str, expected_provider: ProviderName) -> dict:
    try:
        decoded = jwt.decode(state, settings.oauth_state_secret, algorithms=["HS256"])
    except JWTError as e:
        raise HTTPException(status_code=400, detail=f"Invalid OAuth state: {e}")
    if decoded.get("provider") != expected_provider:
        raise HTTPException(status_code=400, detail="OAuth state provider mismatch")
    return decoded


# ─── User-creation helpers ─────────────────────────────────────────────────────


def _slugify_email_local(email: str) -> str:
    local = email.split("@")[0].lower()
    return "".join(ch if (ch.isalnum() or ch == "-") else "-" for ch in local)


def _find_or_create_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    provider: ProviderName,
) -> User:
    """
    Find an existing user by email, or auto-create a new user (and a personal
    agency for them) if no match exists. OAuth users get a random hashed
    password since they will never use email/password login.
    """
    user = db.query(User).filter(User.email == email.lower()).first()
    if user:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")
        return user

    # New user — create a personal workspace agency
    base_slug = _slugify_email_local(email)
    suffix = secrets.token_hex(3)
    slug = f"{base_slug}-{suffix}"

    agency_name = f"{full_name}'s Workspace" if full_name else f"{email}'s Workspace"
    agency = Agency(
        name=agency_name[:255],
        slug=slug[:100],
        subscription_tier="starter",
        countries_enabled="ZA,NO,UK",
    )
    db.add(agency)
    db.flush()

    # OAuth users have a random password they'll never use
    placeholder_password = pwd_context.hash(secrets.token_urlsafe(32))
    user = User(
        agency_id=agency.id,
        email=email.lower(),
        hashed_password=placeholder_password,
        full_name=full_name or email,
        role="admin",  # First user of an auto-created workspace is the admin
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── Profile fetching per provider ─────────────────────────────────────────────


async def _fetch_userinfo(
    provider: ProviderName, access_token: str
) -> tuple[str, str]:
    """Return (email, full_name) from the provider's userinfo endpoint."""
    cfg = _provider_config(provider)
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            cfg["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch user profile from {provider}: {resp.text[:200]}",
        )
    data = resp.json()

    if provider == "google":
        email = data.get("email")
        name = data.get("name") or ""
    else:  # microsoft
        # Graph API returns 'mail' (work) or 'userPrincipalName' (consumer)
        email = data.get("mail") or data.get("userPrincipalName")
        name = data.get("displayName") or ""

    if not email:
        raise HTTPException(
            status_code=400, detail=f"{provider} did not return an email address"
        )
    return email, name


# ─── Routes ────────────────────────────────────────────────────────────────────


@router.get("/{provider}/login")
async def oauth_login(provider: ProviderName, redirect_to: str = "/dashboard"):
    """
    Initiate the OAuth flow. Redirects the user to the provider's
    authorization endpoint.
    """
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    client_id, _ = _client_credentials(provider)
    if not client_id:
        raise HTTPException(
            status_code=503,
            detail=f"{provider.title()} login is not configured on this server. "
            f"Set {provider.upper()}_CLIENT_ID and {provider.upper()}_CLIENT_SECRET in the .env file.",
        )

    cfg = _provider_config(provider)
    state = _create_state(provider, redirect_to=redirect_to)

    params = {
        "client_id": client_id,
        "redirect_uri": _redirect_uri(provider),
        "response_type": "code",
        "scope": cfg["scope"],
        "state": state,
        "access_type": "offline",  # Google: get a refresh token
        "prompt": "select_account",
    }
    auth_url = f"{cfg['auth_url']}?{urlencode(params)}"
    return RedirectResponse(auth_url, status_code=302)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: ProviderName,
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: Session = Depends(get_db),
):
    """
    OAuth callback. Exchanges the auth code for an access token, fetches the
    user's profile, finds or creates the user, issues an internal JWT, and
    redirects the browser back to the frontend with the token.
    """
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    # Handle provider-side errors
    if error:
        return _error_redirect(error_description or error)

    if not code or not state:
        return _error_redirect("Missing code or state parameter")

    state_payload = _verify_state(state, provider)
    redirect_to = state_payload.get("redirect_to", "/dashboard")

    client_id, client_secret = _client_credentials(provider)
    cfg = _provider_config(provider)

    # 1. Exchange the authorization code for tokens
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            cfg["token_url"],
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": _redirect_uri(provider),
            },
            headers={"Accept": "application/json"},
        )
    if token_resp.status_code != 200:
        return _error_redirect(
            f"Token exchange failed: {token_resp.text[:200]}"
        )

    tokens = token_resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        return _error_redirect("Provider did not return an access token")

    # 2. Fetch the user's profile
    try:
        email, full_name = await _fetch_userinfo(provider, access_token)
    except HTTPException as e:
        return _error_redirect(e.detail)

    # 3. Find or create the user (and agency)
    user = _find_or_create_user(
        db, email=email, full_name=full_name, provider=provider
    )

    # 4. Issue an internal JWT (same one as email/password login uses)
    internal_token = create_access_token(user)

    # 5. Build the success redirect with the token + user payload
    user_payload = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "agency_id": user.agency_id,
    }
    user_b64 = base64.urlsafe_b64encode(
        json.dumps(user_payload).encode()
    ).decode().rstrip("=")

    success_url = (
        f"{settings.frontend_url.rstrip('/')}/auth/callback"
        f"?token={internal_token}&user={user_b64}&next={redirect_to}"
    )
    return RedirectResponse(success_url, status_code=302)


def _error_redirect(message: str) -> RedirectResponse:
    """Redirect to the frontend callback page with an error message."""
    err_b64 = base64.urlsafe_b64encode(
        message.encode()
    ).decode().rstrip("=")
    return RedirectResponse(
        f"{settings.frontend_url.rstrip('/')}/auth/callback?error={err_b64}",
        status_code=302,
    )


@router.get("/providers")
def list_providers():
    """
    List which OAuth providers are configured on this server. The frontend
    uses this to decide which buttons to show on the login page.
    """
    return {
        "google": bool(settings.google_client_id and settings.google_client_secret),
        "microsoft": bool(
            settings.microsoft_client_id and settings.microsoft_client_secret
        ),
    }
