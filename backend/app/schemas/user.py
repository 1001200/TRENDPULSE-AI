"""
Pydantic Schemas for User Authentication & Profile Management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    organization_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: Optional[str] = None
    role: str


from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    organization_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
