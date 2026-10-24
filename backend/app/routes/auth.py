"""
Authentication & User Session Endpoints.

Provides production-grade authentication:
- Email + password registration & login with persistent sessions
- Google OAuth auto-provisioning
- HttpOnly cookie session management
- Password reset and email verification flows
- Clean separation of authentication state and onboarding status
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import logging
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from backend.app.core.config import settings

logger = logging.getLogger("trendpulse.auth.routes")
from backend.app.database.connection import get_db
from backend.app.database.models import User, Store
from backend.app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    GoogleAuthRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    AuthSessionResponse,
    OnboardingProgressUpdate,
)
from backend.app.services.auth_service import (
    register_new_account,
    authenticate_user_credentials,
    generate_google_oauth_url,
    handle_google_oauth_callback,
    verify_google_id_token,
    request_password_reset,
    execute_password_reset,
    execute_email_verification,
    terminate_session,
    set_auth_cookies,
    clear_auth_cookies,
    require_current_user,
    get_current_user,
    update_user_onboarding_progress,
    get_user_onboarding_status,
    SESSION_EXPIRE_DAYS,
)
from datetime import timedelta
from backend.app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: SignupRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Register a new merchant account with email & password ONLY.
    Establishes a persistent session with HttpOnly cookies.
    """
    raw_session, access_token, session_data = register_new_account(db, payload, request)
    set_auth_cookies(response, raw_session, session_data.csrf_token or "")
    return session_data


@router.post("/login", response_model=AuthSessionResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate email & password credentials.
    Sets HttpOnly session cookie and returns session data with onboarding status.
    """
    raw_session, access_token, session_data = authenticate_user_credentials(db, payload, request)
    set_auth_cookies(response, raw_session, session_data.csrf_token or "")
    return session_data


# ── Real Google OAuth 2.0 Endpoints ───────────────────────────────

@router.get("/google/authorize")
def google_authorize(request: Request):
    """
    Initiates real Google OAuth 2.0 authorization request.
    Generates a cryptographically secure CSRF state token, sets state cookie,
    and redirects the browser to Google's official accounts.google.com consent screen.
    """
    auth_url, state = generate_google_oauth_url(request)
    redirect_res = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    is_secure = request.url.scheme == "https" and "localhost" not in request.url.netloc and "127.0.0.1" not in request.url.netloc
    redirect_res.set_cookie(
        key="tp_oauth_state",
        value=state,
        max_age=600,  # 10 minutes
        httponly=True,
        samesite="lax",
        secure=is_secure,
        path="/",
    )
    return redirect_res


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Handles real Google OAuth 2.0 redirect callback.
    1. Validates OAuth state (CSRF protection).
    2. Exchanges code with Google's token servers.
    3. Verifies Google user identity and email.
    4. Establishes database session and sets HttpOnly cookies.
    5. Redirects the merchant into the existing setup flow or dashboard.
    """
    if error:
        logger.warning(f"Google OAuth cancelled or failed: {error}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error={error}",
            status_code=status.HTTP_302_FOUND,
        )

    if not code or not state:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=missing_oauth_parameters",
            status_code=status.HTTP_302_FOUND,
        )

    expected_state = request.cookies.get("tp_oauth_state")
    try:
        raw_session, access_token, destination, session_data = await handle_google_oauth_callback(
            db=db,
            code=code,
            state=state,
            expected_state=expected_state,
            request=request,
        )
    except HTTPException as exc:
        # If the user already has a valid active session (e.g., they clicked browser "Back" to this URL),
        # gracefully redirect them to their workspace rather than showing a raw JSON error!
        current_user = get_current_user(request=request, db=db)
        if current_user:
            onboarding_status, has_store = get_user_onboarding_status(db, current_user)
            dest = "/dashboard" if (onboarding_status == "completed" or has_store) else "/setup"
            return RedirectResponse(url=f"{settings.FRONTEND_URL}{dest}", status_code=status.HTTP_302_FOUND)

        logger.warning(f"Google OAuth callback rejected: {exc.detail}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_state_expired",
            status_code=status.HTTP_302_FOUND,
        )

    frontend_redirect = f"{settings.FRONTEND_URL}{destination}"
    redirect_res = RedirectResponse(url=frontend_redirect, status_code=status.HTTP_302_FOUND)
    set_auth_cookies(redirect_res, raw_session, session_data.csrf_token or "")
    redirect_res.delete_cookie(key="tp_oauth_state", path="/")
    return redirect_res


@router.post("/google/verify-token", response_model=AuthSessionResponse)
async def google_verify_id_token(
    payload: Dict[str, Any],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Alternative Google Identity Services (GIS) endpoint.
    Cryptographically verifies signed Google ID token (JWT) against Google's servers.
    """
    token_str = payload.get("credential") or payload.get("id_token") or ""
    raw_session, access_token, session_data = await verify_google_id_token(db, token_str, request)
    set_auth_cookies(response, raw_session, session_data.csrf_token or "")
    return session_data


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Terminate the current user session and clear cookies."""
    terminate_session(db, request)
    clear_auth_cookies(response)
    return {"message": "Successfully logged out of your session."}


@router.get("/me")
def get_current_profile(
    request: Request,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve authenticated user profile with server-verified onboarding status.
    Answers: 'Who is this user?' and 'Has this user completed onboarding?'
    """
    onboarding_status, has_store = get_user_onboarding_status(db, current_user)
    store = db.query(Store).filter(Store.user_id == current_user.id).first()

    access_token = create_access_token(
        subject=current_user.id,
        expires_delta=timedelta(days=SESSION_EXPIRE_DAYS),
        extra_claims={
            "email": current_user.email,
            "role": current_user.role,
            "onboarding_status": onboarding_status,
            "onboarding_step": getattr(current_user, "onboarding_step", 1) or 1,
            "has_store": has_store,
        },
    )

    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "onboarding_status": onboarding_status,
        "onboarding_step": getattr(current_user, "onboarding_step", 1) or 1,
        "has_store": has_store,
        "store_id": store.id if store else None,
        "auth_provider": current_user.auth_provider,
        "access_token": access_token,
    }


@router.patch("/onboarding-progress")
def set_onboarding_progress(
    payload: OnboardingProgressUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """
    Persists onboarding step and status server-side.
    Ensures user returns to where they left off upon login.
    """
    updated_user = update_user_onboarding_progress(
        db=db,
        user=current_user,
        step=payload.step,
        status_val=payload.status,
    )
    return {
        "onboarding_step": updated_user.onboarding_step,
        "onboarding_status": updated_user.onboarding_status,
    }


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Request password reset link.
    Returns generic response to prevent account enumeration.
    """
    return request_password_reset(db, payload.email, request)


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Execute password reset using cryptographic token.
    Updates password, marks token as used, and invalidates all existing sessions.
    """
    return execute_password_reset(db, payload.token, payload.new_password)


@router.post("/verify-email")
def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    """Verify account email with cryptographic single-use token."""
    return execute_email_verification(db, payload.token)
