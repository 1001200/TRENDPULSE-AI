"""
Pydantic Schemas for TrendPulse Authentication & Session Management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ── Strict Signup Request (Email + Password ONLY) ──────────────────
class SignupRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


# ── Login Request ──────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


# ── Google OAuth Request ───────────────────────────────────────────
class GoogleAuthRequest(BaseModel):
    email: str
    name: Optional[str] = None
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None


# ── Password Reset Requests ────────────────────────────────────────
class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


# ── Email Verification Request ─────────────────────────────────────
class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


# ── Authenticated Session Response ─────────────────────────────────
class AuthSessionResponse(BaseModel):
    user_id: int
    email: str
    role: str = "merchant"
    is_verified: bool = True
    onboarding_status: str = "not_started"  # not_started, in_progress, completed
    onboarding_step: int = 1
    has_store: bool = False
    access_token: str
    token_type: str = "bearer"
    csrf_token: Optional[str] = None


class OnboardingProgressUpdate(BaseModel):
    step: int = Field(..., ge=1, le=10, description="Current onboarding step (1 to 10)")
    status: Optional[str] = Field(None, description="'not_started', 'in_progress', or 'completed'")

