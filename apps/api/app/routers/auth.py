from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.schemas import UserCreate, UserResponse
from app.auth.auth0_client import Auth0Client
from app.auth.middleware import get_current_user, MultiTenantContext, security
from app.models import User, Agency
from passlib.hash import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])
auth0 = Auth0Client()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register new user."""
    # Check if agency exists
    agency = db.query(Agency).filter(Agency.id == user.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    # Check for duplicate email
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create user in database
    db_user = User(
        email=user.email,
        hashed_password=bcrypt.hash(user.password),
        full_name=user.name,
        role="client_user",
        agency_id=user.agency_id,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user information from JWT."""
    ctx = await get_current_user(credentials)
    user = db.query(User).filter(User.auth0_id == ctx.user_id).first()
    if not user:
        # Fall back to email lookup
        user = db.query(User).filter(User.email == ctx.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/logout")
async def logout(credentials=Depends(security)):
    """Logout current user (token invalidation handled client-side / Auth0)."""
    return {"message": "Logged out successfully"}


@router.get("/health")
async def auth_health():
    """Check auth configuration status."""
    has_domain = bool(auth0.domain)
    return {
        "status": "ok" if has_domain else "unconfigured",
        "service": "auth",
        "auth0_configured": has_domain,
    }
