"""JWT token creation and verification."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import jwt

from app.config import settings


def create_access_token(data: dict[str, Any]) -> str:
    """Create a short-lived access token."""
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["type"] = "access"
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a long-lived refresh token."""
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
