from pydantic import BaseModel, EmailStr
from typing import List, Optional


class TokenPayload(BaseModel):
    sub: str
    email: str
    name: str
    aud: str
    iat: int
    exp: int
    permissions: List[str] = []
    org_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    agency_id: int


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    agency_id: int
    is_active: bool

    model_config = {"from_attributes": True}
