from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.middleware import get_current_user, MultiTenantContext
from app.models import User, Agency


async def get_current_user_from_db(
    current_user: MultiTenantContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the JWT identity to a database User row."""
    user = db.query(User).filter(User.auth0_id == current_user.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in database",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_agency(
    current_user: MultiTenantContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Agency:
    """Get the agency for the current user."""
    agency = db.query(Agency).filter(Agency.id == current_user.agency_id).first()

    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found",
        )

    return agency
