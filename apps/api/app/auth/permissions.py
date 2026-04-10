from fastapi import Depends, HTTPException, status
from app.auth.middleware import get_current_user, MultiTenantContext, security


def require_role(*allowed_roles: str):
    """Return a dependency that checks the user has one of the allowed roles."""
    async def role_checker(
        current_user: MultiTenantContext = Depends(get_current_user),
    ) -> MultiTenantContext:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {allowed_roles}",
            )
        return current_user
    return role_checker


def require_permission(*required_permissions: str):
    """Return a dependency that checks the user has all required permissions."""
    async def permission_checker(
        current_user: MultiTenantContext = Depends(get_current_user),
    ) -> MultiTenantContext:
        missing = set(required_permissions) - set(current_user.permissions)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {missing}",
            )
        return current_user
    return permission_checker


async def get_current_admin(
    current_user: MultiTenantContext = Depends(get_current_user),
) -> MultiTenantContext:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_agent(
    current_user: MultiTenantContext = Depends(get_current_user),
) -> MultiTenantContext:
    """Require agent or admin role."""
    if current_user.role not in ("admin", "agent"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent access required",
        )
    return current_user
