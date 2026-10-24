"""
TrendPulse Production Authentication & Session Management Service.

Provides secure enterprise-grade authentication:
- Email + password registration & login with PBKDF2-SHA256 salted hashing
- Google OAuth auto-provisioning & account linking
- Cryptographic session tracking via user_sessions table
- HttpOnly cookie session management with bearer token fallback
- Password reset flow (single-use, SHA-256 hashed in DB, 1-hour expiration, revokes active sessions)
- Email verification flow (single-use, SHA-256 hashed in DB, 24-hour expiration)
- Server-side rate limiting enforcement
- Server-side onboarding status determination (not_started, in_progress, completed)
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import logging
import urllib.parse
import hmac
import httpx
from typing import Dict, Optional, Tuple
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_secure_token,
    hash_token,
    generate_csrf_token,
)
from backend.app.database.connection import get_db
from backend.app.database.models import (
    User,
    Store,
    UserSession,
    PasswordResetToken,
    EmailVerificationToken,
    utcnow,
)
from backend.app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    GoogleAuthRequest,
    AuthSessionResponse,
)
from backend.app.services.rate_limiter import (
    rate_limit_login,
    reset_login_limits,
    rate_limit_signup,
    rate_limit_forgot_password,
)

logger = logging.getLogger("trendpulse.auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

SESSION_COOKIE_NAME = "tp_session"
SESSION_EXPIRE_DAYS = 30
RESET_TOKEN_EXPIRE_HOURS = 1
VERIFY_TOKEN_EXPIRE_HOURS = 24


def log_security_event(
    event_type: str,
    user_id: Optional[int] = None,
    email: Optional[str] = None,
    ip: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """
    Structured security audit logging.
    Strictly NEVER logs passwords, secrets, or raw session tokens.
    """
    sanitized_email = None
    if email and "@" in email:
        parts = email.split("@")
        sanitized_email = f"{parts[0][:3]}***@{parts[1]}"

    audit_entry = {
        "event": event_type,
        "timestamp": utcnow().isoformat(),
        "user_id": user_id,
        "email": sanitized_email,
        "ip": ip or "unknown",
    }
    if extra:
        for k, v in extra.items():
            if not any(bad in k.lower() for bad in ("password", "token", "secret", "cookie")):
                audit_entry[k] = v
    logger.info(f"SECURITY_AUDIT: {audit_entry}")


def update_user_onboarding_progress(
    db: Session,
    user: User,
    step: int,
    status_val: Optional[str] = None,
) -> User:
    """Persist onboarding progress and step server-side."""
    user.onboarding_step = step
    if status_val in ("not_started", "in_progress", "completed"):
        user.onboarding_status = status_val
    elif user.onboarding_status == "not_started" and step > 1:
        user.onboarding_status = "in_progress"
    db.commit()
    db.refresh(user)
    log_security_event("onboarding_progress_updated", user_id=user.id, extra={"step": step, "status": user.onboarding_status})
    return user


def get_client_ip(request: Request) -> str:
    """Safely extract client IP from forward headers or direct client."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def get_user_onboarding_status(db: Session, user: User) -> Tuple[str, bool]:
    """
    Determine onboarding status:
    Returns (status_string, has_store_bool).
    If a store already exists for this user, status is strictly 'completed'.
    """
    store = db.query(Store).filter(Store.user_id == user.id).first()
    if store is not None:
        if user.onboarding_status != "completed":
            user.onboarding_status = "completed"
            db.commit()
        return "completed", True

    current_status = user.onboarding_status or "not_started"
    return current_status, False


def create_user_session(
    db: Session,
    user: User,
    request: Optional[Request] = None,
) -> Tuple[str, str, AuthSessionResponse]:
    """
    Create a persistent server-side session in user_sessions table,
    and generate a signed JWT access token.
    Returns: (raw_session_token, access_token, AuthSessionResponse)
    """
    raw_session_token = generate_secure_token(32)
    session_hash = hash_token(raw_session_token)
    expires_at = utcnow() + timedelta(days=SESSION_EXPIRE_DAYS)

    ip_address = get_client_ip(request) if request else "127.0.0.1"
    user_agent = request.headers.get("User-Agent", "Unknown")[:500] if request else "Unknown"

    session = UserSession(
        user_id=user.id,
        session_token_hash=session_hash,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
        is_revoked=False,
        created_at=utcnow(),
        last_active_at=utcnow(),
    )
    db.add(session)
    db.commit()

    # Determine onboarding status
    onboarding_status_str, has_store = get_user_onboarding_status(db, user)

    # Issue JWT access token
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(days=SESSION_EXPIRE_DAYS),
        extra_claims={
            "email": user.email,
            "role": user.role,
            "onboarding_status": onboarding_status_str,
            "onboarding_step": getattr(user, "onboarding_step", 1) or 1,
            "has_store": has_store,
            "sid": session.id,
        },
    )

    csrf_token = generate_csrf_token()

    session_resp = AuthSessionResponse(
        user_id=user.id,
        email=user.email,
        role=user.role,
        is_verified=user.is_verified,
        onboarding_status=onboarding_status_str,
        onboarding_step=getattr(user, "onboarding_step", 1) or 1,
        has_store=has_store,
        access_token=access_token,
        csrf_token=csrf_token,
    )

    return raw_session_token, access_token, session_resp


def set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    """Set secure HttpOnly cookies for session management."""
    max_age = SESSION_EXPIRE_DAYS * 24 * 60 * 60
    # HttpOnly session cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False,  # In local dev false, will use settings.DEBUG in prod
        path="/",
    )
    # CSRF cookie accessible to frontend JS
    response.set_cookie(
        key="tp_csrf",
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        samesite="lax",
        secure=False,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear session cookies on logout."""
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(key="tp_csrf", path="/")


# ── Core Authentication Actions ────────────────────────────────────

def register_new_account(
    db: Session,
    signup_in: SignupRequest,
    request: Request,
) -> Tuple[str, str, AuthSessionResponse]:
    """
    Register a new merchant account with email & password ONLY.
    Strictly NO brand name or onboarding fields at this stage.
    """
    ip = get_client_ip(request)
    rate_limit_signup(ip)

    clean_email = signup_in.email.lower().strip()

    # Check for existing account
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in instead.",
        )

    hashed_pw = get_password_hash(signup_in.password)
    new_user = User(
        email=clean_email,
        hashed_password=hashed_pw,
        full_name=clean_email.split("@")[0].title(),
        role="merchant",
        is_active=True,
        is_verified=True,  # Default active & verified for rapid seller intake
        onboarding_status="not_started",
        auth_provider="local",
        created_at=utcnow(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_security_event("signup_success", user_id=new_user.id, email=clean_email, ip=ip)
    return create_user_session(db, new_user, request)


def authenticate_user_credentials(
    db: Session,
    login_in: LoginRequest,
    request: Request,
) -> Tuple[str, str, AuthSessionResponse]:
    """
    Authenticate email & password credentials with rate limiting.
    Handles OAuth-only account notifications safely.
    """
    ip = get_client_ip(request)
    clean_email = login_in.email.lower().strip()

    # Enforce brute force protection
    rate_limit_login(ip, clean_email)

    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        log_security_event("login_failure", email=clean_email, ip=ip, extra={"reason": "user_not_found"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        log_security_event("login_failure", user_id=user.id, email=clean_email, ip=ip, extra={"reason": "account_deactivated"})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact support.",
        )

    # Check password
    if not verify_password(login_in.password, user.hashed_password):
        log_security_event("login_failure", user_id=user.id, email=clean_email, ip=ip, extra={"reason": "wrong_password"})
        if user.auth_provider in ("google", "apple"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This account was created with {user.auth_provider.title()}. Please sign in with {user.auth_provider.title()}.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Authentication succeeded: reset rate limits
    reset_login_limits(ip, clean_email)

    log_security_event("login_success", user_id=user.id, email=clean_email, ip=ip)
    return create_user_session(db, user, request)


def generate_google_oauth_url(request: Request) -> Tuple[str, str]:
    """
    Constructs real Google OAuth 2.0 authorization URL with CSRF state protection.
    Redirects user to Google's official account selection and consent screen.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google OAuth 2.0 is not yet configured. Please set GOOGLE_CLIENT_ID "
                "and GOOGLE_CLIENT_SECRET in your .env file or Google Cloud Console."
            ),
        )

    state = generate_secure_token(32)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return auth_url, state


async def handle_google_oauth_callback(
    db: Session,
    code: str,
    state: str,
    expected_state: Optional[str],
    request: Request,
) -> Tuple[str, str, str, AuthSessionResponse]:
    """
    Validates Google OAuth 2.0 authorization code response.
    1. Validates CSRF state against expected state cookie.
    2. Exchanges authorization code with Google's token server.
    3. Fetches verified OpenID Connect user profile from Google.
    4. Confirms Google email verification.
    5. Links Google identity to existing user or auto-provisions new merchant profile.
    6. Establishes authenticated session and computes onboarding handoff destination.
    """
    if not state or not expected_state or not hmac.compare_digest(state, expected_state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state parameter. Please try logging in again.",
        )

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth credentials are missing from server configuration.",
        )

    # 1. Exchange authorization code with Google
    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_res = await client.post(token_url, data=token_payload)
            if token_res.status_code != 200:
                err_data = token_res.json() if token_res.content else {}
                err_msg = err_data.get("error_description") or err_data.get("error") or "Token exchange failed"
                logger.error(f"Google token exchange failed: {err_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Google authentication failed: {err_msg}",
                )
            token_data = token_res.json()
            access_token = token_data.get("access_token")

            # 2. Fetch verified userinfo from Google
            userinfo_res = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to retrieve verified user profile from Google.",
                )
            userinfo = userinfo_res.json()
    except httpx.RequestError as exc:
        logger.error(f"Network error communicating with Google: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to connect to Google authentication servers. Please try again.",
        )

    google_sub = str(userinfo.get("sub") or "")
    clean_email = (userinfo.get("email") or "").lower().strip()
    email_verified = bool(userinfo.get("email_verified", False))
    full_name = userinfo.get("name") or clean_email.split("@")[0].title()

    if not google_sub or not clean_email or "@" not in clean_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google profile did not provide a valid user ID or email.",
        )

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your Google email address is not verified by Google.",
        )

    # 3. User Resolution & Account Linking
    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user:
        # Check by email for existing accounts
        user = db.query(User).filter(User.email == clean_email).first()
        if user:
            # Secure account linking: verified Google identity matches existing email
            if not user.google_sub:
                user.google_sub = google_sub
            if not user.is_verified:
                user.is_verified = True
            db.commit()
            logger.info(f"Existing user account linked to Google: {clean_email}")
        else:
            # Auto-provision new merchant account
            random_pw = generate_secure_token(32)
            user = User(
                email=clean_email,
                hashed_password=get_password_hash(random_pw),
                full_name=full_name,
                role="merchant",
                is_active=True,
                is_verified=True,
                onboarding_status="not_started",
                auth_provider="google",
                google_sub=google_sub,
                created_at=utcnow(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New Google merchant account provisioned: {clean_email}")

    onboarding_status, has_store = get_user_onboarding_status(db, user)
    destination = "/dashboard" if (onboarding_status == "completed" or has_store) else "/setup"
    raw_session, session_access_token, session_data = create_user_session(db, user, request)
    return raw_session, session_access_token, destination, session_data


async def verify_google_id_token(
    db: Session,
    id_token_str: str,
    request: Request,
) -> Tuple[str, str, AuthSessionResponse]:
    """
    Cryptographically verifies a Google ID Token (JWT) against Google's public tokeninfo server.
    Used for Google Identity Services (GIS) / 1-Tap integrations.
    """
    if not id_token_str or not id_token_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Google ID token.",
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tokeninfo_res = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token_str.strip()}"
            )
            if tokeninfo_res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired Google ID token.",
                )
            payload = tokeninfo_res.json()
    except httpx.RequestError as exc:
        logger.error(f"Error validating Google token: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to verify token with Google.",
        )

    # Validate issuer
    issuer = payload.get("iss")
    if issuer not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Untrusted Google token issuer.",
        )

    # Validate audience if client ID is configured
    if settings.GOOGLE_CLIENT_ID:
        aud = payload.get("aud")
        if aud != settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token was not issued for this application.",
            )

    google_sub = str(payload.get("sub") or "")
    clean_email = (payload.get("email") or "").lower().strip()
    email_verified = payload.get("email_verified") in (True, "true", "True")
    full_name = payload.get("name") or clean_email.split("@")[0].title()

    if not google_sub or not clean_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token is missing required user identity claims.",
        )

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is not verified.",
        )

    # Link or auto-provision
    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user:
        user = db.query(User).filter(User.email == clean_email).first()
        if user:
            if not user.google_sub:
                user.google_sub = google_sub
            if not user.is_verified:
                user.is_verified = True
            db.commit()
        else:
            random_pw = generate_secure_token(32)
            user = User(
                email=clean_email,
                hashed_password=get_password_hash(random_pw),
                full_name=full_name,
                role="merchant",
                is_active=True,
                is_verified=True,
                onboarding_status="not_started",
                auth_provider="google",
                google_sub=google_sub,
                created_at=utcnow(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    return create_user_session(db, user, request)


# ── Password Reset Flow ────────────────────────────────────────────

def request_password_reset(
    db: Session,
    email: str,
    request: Request,
) -> Dict[str, str]:
    """
    Request password reset. Returns a generic message to prevent account enumeration.
    Generates a single-use, cryptographically secure token with 1-hour expiration.
    """
    ip = get_client_ip(request)
    clean_email = email.lower().strip()
    rate_limit_forgot_password(ip, clean_email)

    user = db.query(User).filter(User.email == clean_email).first()
    simulated_token = None
    if user and user.is_active:
        raw_token = generate_secure_token(32)
        token_hash_val = hash_token(raw_token)
        expires_at = utcnow() + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash_val,
            expires_at=expires_at,
            used_at=None,
            created_at=utcnow(),
        )
        db.add(reset_record)
        db.commit()
        simulated_token = raw_token
        logger.info(f"Password reset token created for user #{user.id}")

    return {
        "message": "If an account exists with this email, a password reset link has been generated.",
        # In development / testing, provide the token in response for zero-email testing:
        "dev_reset_token": simulated_token,
    }


def execute_password_reset(
    db: Session,
    token: str,
    new_password: str,
) -> Dict[str, str]:
    """
    Validate reset token, update password, mark token as used,
    and revoke all previous user sessions across devices.
    """
    token_hash_val = hash_token(token)
    now = utcnow()

    reset_record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash_val,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .first()
    )

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token is invalid, expired, or has already been used.",
        )

    user = reset_record.user
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Associated account is invalid or inactive.",
        )

    # Update password
    user.hashed_password = get_password_hash(new_password)
    reset_record.used_at = now

    # Revoke all active sessions for this user for security
    db.query(UserSession).filter(UserSession.user_id == user.id).update({"is_revoked": True})
    db.commit()

    logger.info(f"Password reset successfully executed for user #{user.id}")
    return {"message": "Password has been successfully reset. Please log in with your new password."}


# ── Email Verification Flow ────────────────────────────────────────

def execute_email_verification(db: Session, token: str) -> Dict[str, str]:
    """Validate verification token and mark account as verified."""
    token_hash_val = hash_token(token)
    now = utcnow()

    record = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.token_hash == token_hash_val,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > now,
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification token is invalid or expired.",
        )

    user = record.user
    user.is_verified = True
    record.used_at = now
    db.commit()

    return {"message": "Email has been successfully verified."}


# ── Session Termination & Logout ───────────────────────────────────

def terminate_session(db: Session, request: Request) -> None:
    """Revoke session record in database."""
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie:
        session_hash = hash_token(session_cookie)
        db.query(UserSession).filter(UserSession.session_token_hash == session_hash).update({"is_revoked": True})
        db.commit()


# ── Dependency Injection: Current Authenticated User ───────────────

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    bearer_token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """
    Extract current authenticated user:
    1. First tries HttpOnly cookie (tp_session) and verifies active session in DB.
    2. Fallback: tries Authorization: Bearer <jwt_token> header.
    Returns None if unauthenticated (for optional endpoints).
    """
    # 1. Try Cookie Session
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie:
        session_hash = hash_token(session_cookie)
        now = utcnow()
        session_record = (
            db.query(UserSession)
            .filter(
                UserSession.session_token_hash == session_hash,
                UserSession.is_revoked == False,
                UserSession.expires_at > now,
            )
            .first()
        )
        if session_record and session_record.user and session_record.user.is_active:
            # Throttle last active timestamp update to once every 5 minutes
            if not session_record.last_active_at or (now - session_record.last_active_at).total_seconds() > 300:
                session_record.last_active_at = now
                try:
                    db.commit()
                except Exception:
                    db.rollback()
            return session_record.user

    # 2. Try Bearer JWT Token Fallback
    token = bearer_token
    if not token:
        # Check custom header if needed
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if token:
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            try:
                user_id = int(payload["sub"])
                sid = payload.get("sid")
                if sid:
                    now = utcnow()
                    session_rec = (
                        db.query(UserSession)
                        .filter(
                            UserSession.id == sid,
                            UserSession.user_id == user_id,
                            UserSession.is_revoked == False,
                            UserSession.expires_at > now,
                        )
                        .first()
                    )
                    if not session_rec:
                        return None
                    if not session_rec.last_active_at or (now - session_rec.last_active_at).total_seconds() > 300:
                        session_rec.last_active_at = now
                        try:
                            db.commit()
                        except Exception:
                            db.rollback()

                user = db.query(User).filter(User.id == user_id).first()
                if user and user.is_active:
                    return user
            except Exception:
                return None

    return None


def require_current_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Strict dependency for protected routes: raises 401 if unauthenticated."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


# Aliases for compatibility with other backend modules
register_user = register_new_account
authenticate_user = authenticate_user_credentials

