"""Password hashing and JWT helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import Settings
from app.core.exceptions import AuthenticationError


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""

    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(
    subject: str,
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for the given subject."""

    now = datetime.now(tz=UTC)
    expiry = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"sub": subject, "iat": now, "exp": expiry}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decode and validate a JWT access token."""

    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise AuthenticationError() from exc

