"""
TrendPulse Security & Authentication Engine.

Implements standard PBKDF2-SHA256 password hashing and HMAC-SHA256 JWT tokens
using Python standard library (hashlib, hmac, base64) for maximum reliability
and zero external dependency conflicts.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from typing import Any, Dict, Optional, Union

from backend.app.core.config import settings


def _b64_encode(data: bytes) -> str:
    """URL-safe Base64 encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64_decode(data_str: str) -> bytes:
    """URL-safe Base64 decode with padding restoration."""
    padding = "=" * (4 - (len(data_str) % 4)) if len(data_str) % 4 != 0 else ""
    return base64.urlsafe_b64decode((data_str + padding).encode("utf-8"))


# ============================================================
# Password Hashing (PBKDF2-SHA256 with Salt)
# ============================================================

def get_password_hash(password: str) -> str:
    """Generate salted PBKDF2-SHA256 hash."""
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored salt and hash."""
    try:
        if "$" not in hashed_password:
            return False
        salt, stored_hash = hashed_password.split("$", 1)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100_000,
        )
        return hmac.compare_digest(key.hex(), stored_hash)
    except Exception:
        return False


# ============================================================
# JWT Token Implementation (HMAC-SHA256)
# ============================================================

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a signed JWT token (HS256)."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    header_b64 = _b64_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify signature and return payload if valid and unexpired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        provided_sig = _b64_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, provided_sig):
            return None

        payload = json.loads(_b64_decode(payload_b64).decode("utf-8"))

        # Check expiration
        exp = payload.get("exp")
        if exp and exp < datetime.now(timezone.utc).timestamp():
            return None

        return payload
    except Exception:
        return None


# ============================================================
# Cryptographic Token Helpers (Reset, Verification, Sessions)
# ============================================================

def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""
    import secrets
    return secrets.token_urlsafe(nbytes)


def hash_token(raw_token: str) -> str:
    """Hash a token with SHA-256 for secure database storage."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    """Generate a CSRF prevention token."""
    import secrets
    return secrets.token_hex(20)

