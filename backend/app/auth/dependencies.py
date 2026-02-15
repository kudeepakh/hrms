"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from typing import Callable

import jwt
from fastapi import Depends, Header

from app.auth.jwt_handler import decode_token
from app.exceptions import ForbiddenException, UnauthorizedException
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository

_user_repo = UserRepository()


async def get_current_user(authorization: str = Header(default="")) -> User:
    """Extract and validate the Bearer token, return the User document."""
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid Authorization header.")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Token has expired.")
    except jwt.PyJWTError:
        raise UnauthorizedException("Invalid token.")

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type.")

    user = await _user_repo.find_by_email(payload["sub"])
    if not user:
        raise UnauthorizedException("User no longer exists.")
    if not user.is_active:
        raise UnauthorizedException("Account is deactivated.")

    return user


def require_role(*allowed_roles: UserRole) -> Callable:
    """Dependency factory — restrict endpoint to specific roles."""

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise ForbiddenException(
                f"Role '{user.role.value}' is not allowed. Required: {[r.value for r in allowed_roles]}."
            )
        return user

    return _check


def require_permission(permission: str) -> Callable:
    """Dependency factory — restrict endpoint by permission string."""

    async def _check(user: User = Depends(get_current_user)) -> User:
        if not user.has_permission(permission):
            raise ForbiddenException(f"You lack the '{permission}' permission.")
        return user

    return _check
