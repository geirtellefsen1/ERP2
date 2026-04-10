from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os

security = HTTPBearer()


class MultiTenantContext:
    def __init__(self, user_id: str, email: str, name: str, agency_id: int, role: str, permissions: list):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.agency_id = agency_id
        self.role = role
        self.permissions = permissions


async def get_current_user(credentials: HTTPAuthorizationCredentials) -> MultiTenantContext:
    """Extract and validate JWT token, return multi-tenant context."""
    token = credentials.credentials

    try:
        secret = os.getenv("AUTH0_CLIENT_SECRET", "dev-secret")

        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )

        user_id = payload.get("sub")
        email = payload.get("email")
        name = payload.get("name", "")
        permissions = payload.get("permissions", [])
        agency_id = payload.get("org_id") or payload.get("agency_id")
        role = payload.get("role", "client")

        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return MultiTenantContext(
            user_id=user_id,
            email=email,
            name=name,
            agency_id=int(agency_id) if agency_id else 0,
            role=role,
            permissions=permissions,
        )

    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
