"""
Auth router — login, register, token refresh.
For the MVP: username/password → internal JWT issued by BPO Nexus API.
When Auth0 is configured: delegates to Auth0 Universal Login.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta, timezone
from jose import jwt
import httpx
from app.database import get_db
from app.models import User
from app.auth import AuthUser, get_current_user
from app.config import get_settings
from app.services.jwt_signing import get_signing_key
from app.services.rate_limit import rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


# ─── Schemas ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    agency_id: int


# ─── Helpers ──────────────────────────────────────────────────────────────────

def create_access_token(user: User, expires_delta: timedelta | None = None) -> str:
    """Issue an internal JWT for the authenticated user."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    claims = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "agency_id": user.agency_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": settings.auth0_audience,
    }
    return jwt.encode(claims, get_signing_key(), algorithm=ALGORITHM)


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
    _rl: None = Depends(
        rate_limit("login", per_minute=settings.rate_limit_login_per_minute)
    ),
):
    """
    Username/password login. Issues an internal JWT (MVP).
    Production: replace with Auth0 Universal Login redirect.
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not pwd_context.verify(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(user)
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "agency_id": user.agency_id,
        },
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (internal — no Auth0 for MVP)."""
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=pwd_context.hash(data.password),
        full_name=data.full_name,
        agency_id=data.agency_id,
        role="agent",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user)
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "agency_id": user.agency_id,
        },
    )


@router.get("/me", response_model=dict)
def get_me(current_user: AuthUser = Depends(get_current_user)):
    """Return the currently authenticated user's info."""
    return {
        "sub": current_user.sub,
        "agency_id": current_user.agency_id,
        "role": current_user.role,
        "email": current_user.email,
    }


@router.post("/auth0/callback")
async def auth0_callback(code: str, db: Session = Depends(get_db)):
    """
    Auth0 callback — exchanges code for tokens, looks up/creates user.
    Called by the frontend after Auth0 Universal Login redirect.
    """
    if not settings.auth0_domain:
        raise HTTPException(status_code=501, detail="Auth0 not configured")

    token_url = f"https://{settings.auth0_domain}/oauth/token"
    user_url = f"https://{settings.auth0_domain}/userinfo"

    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.auth0_audience,
                "client_secret": settings.auth0_domain,  # placeholder — fill real secret
                "code": code,
                "redirect_uri": "http://localhost:3000/auth/callback",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Auth0 token exchange failed")
        tokens = token_resp.json()

        # Get user info from Auth0
        user_resp = await client.get(
            user_url,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Auth0 userinfo failed")
        auth0_user = user_resp.json()

    # Find or create user
    email = auth0_user["email"]
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found — please contact admin")

    internal_token = create_access_token(user)
    return TokenResponse(
        access_token=internal_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "agency_id": user.agency_id,
        },
    )
