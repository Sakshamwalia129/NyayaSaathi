"""
auth_schemas.py — Pydantic models for authentication in NyayaSaathi.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name of the user.")
    email: EmailStr = Field(..., description="User's email address.")
    password: str = Field(..., min_length=6, max_length=128, description="User's password (min 6 characters).")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address.")
    password: str = Field(..., description="User's password.")


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., description="Google OAuth ID Token credential.")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    auth_provider: str
    profile_picture_url: Optional[str] = None
    created_at: datetime



class AuthResponse(BaseModel):
    success: bool
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserResponse] = None
    error: Optional[dict] = None
