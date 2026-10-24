"""
TrendPulse Production Rate Limiting & Abuse Prevention Engine.

Provides in-memory sliding window rate limiting for authentication endpoints:
- Login attempts (IP and email based throttling)
- Signup attempts (IP based throttling)
- Password reset requests (email and IP based throttling)
- Email verification requests

Uses threading.Lock for concurrency safety and automatic memory cleanup.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import threading
from typing import Dict, List, Tuple
from fastapi import HTTPException, status


class SlidingWindowRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        # key -> list of UTC datetime timestamps
        self._records: Dict[str, List[datetime]] = {}

    def _cleanup_old_records(self, key: str, window_seconds: int, now: datetime) -> List[datetime]:
        cutoff = now - timedelta(seconds=window_seconds)
        timestamps = self._records.get(key, [])
        valid_timestamps = [ts for ts in timestamps if ts > cutoff]
        if valid_timestamps:
            self._records[key] = valid_timestamps
        else:
            self._records.pop(key, None)
        return valid_timestamps

    def check_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        action_name: str = "request",
    ) -> None:
        """
        Check if request exceeds rate limit. If it does, raise 429 Too Many Requests.
        Otherwise, records the attempt.
        """
        now = datetime.now(timezone.utc)
        with self._lock:
            valid_timestamps = self._cleanup_old_records(key, window_seconds, now)
            if len(valid_timestamps) >= max_requests:
                oldest = valid_timestamps[0]
                retry_after_seconds = max(1, int((oldest + timedelta(seconds=window_seconds) - now).total_seconds()))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many {action_name} attempts. Please try again in {retry_after_seconds} seconds.",
                    headers={"Retry-After": str(retry_after_seconds)},
                )
            # Record current attempt
            if key not in self._records:
                self._records[key] = []
            self._records[key].append(now)

    def reset(self, key: str) -> None:
        """Reset limits for a given key upon successful authentication."""
        with self._lock:
            self._records.pop(key, None)


# Global singleton instance
rate_limiter = SlidingWindowRateLimiter()


def rate_limit_login(ip: str, email: str) -> None:
    """Enforce login rate limits: max 5 failed attempts per 5 minutes per IP or email."""
    normalized_email = email.lower().strip()
    rate_limiter.check_limit(f"login:ip:{ip}", max_requests=10, window_seconds=300, action_name="login")
    rate_limiter.check_limit(f"login:email:{normalized_email}", max_requests=5, window_seconds=300, action_name="login")


def reset_login_limits(ip: str, email: str) -> None:
    """Clear login rate limits after a successful login."""
    normalized_email = email.lower().strip()
    rate_limiter.reset(f"login:ip:{ip}")
    rate_limiter.reset(f"login:email:{normalized_email}")


def rate_limit_signup(ip: str) -> None:
    """Enforce signup rate limits: max 5 signups per hour per IP."""
    rate_limiter.check_limit(f"signup:ip:{ip}", max_requests=5, window_seconds=3600, action_name="signup")


def rate_limit_forgot_password(ip: str, email: str) -> None:
    """Enforce password reset limits: max 3 requests per 15 minutes."""
    normalized_email = email.lower().strip()
    rate_limiter.check_limit(f"forgot:ip:{ip}", max_requests=5, window_seconds=900, action_name="password reset")
    rate_limiter.check_limit(f"forgot:email:{normalized_email}", max_requests=3, window_seconds=900, action_name="password reset")
