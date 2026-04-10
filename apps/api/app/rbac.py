"""
RBAC — Role-Based Access Control.
Decorators + dependency for enforcing role restrictions on routes.
"""

from functools import wraps
from fastapi import HTTPException
from app.auth import AuthUser


# All valid roles, ordered by privilege level
ROLE_HIERARCHY = {
    "owner": 4,
    "admin": 3,
    "agent": 2,
    "client_admin": 1,
    "client_user": 0,
}


def require_roles(*allowed_roles: str):
    """
    Decorator — restricts endpoint to users with one of the allowed roles.
    Usage: @require_roles("admin", "owner")
    """
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            # User is injected via dependency in kwargs as 'current_user'
            user: AuthUser | None = kwargs.get("current_user")
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Role '{user.role}' is not permitted on this endpoint",
                )
            return await fn(*args, **kwargs)
        return wrapper
    return decorator


def require_min_role(min_role: str):
    """
    Dependency — returns user only if their role >= min_role.
    Usage: async def route(..., user: AuthUser = Depends(require_min_role("admin"))):
    """
    def check_role(user: AuthUser):
        user_level = ROLE_HIERARCHY.get(user.role, -1)
        required_level = ROLE_HIERARCHY.get(min_role, 999)
        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user.role}' does not meet minimum required role: {min_role}",
            )
        return user
    return check_role


# Role constants
class Roles:
    OWNER = "owner"
    ADMIN = "admin"
    AGENT = "agent"
    CLIENT_ADMIN = "client_admin"
    CLIENT_USER = "client_user"
