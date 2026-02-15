"""Auth service — login, register, SSO, and password hashing."""

from __future__ import annotations

from datetime import datetime

import bcrypt

from app.auth.jwt_handler import create_access_token, create_refresh_token
from app.exceptions import BadRequestException, ConflictException, UnauthorizedException
from app.models.user import SSOProfile, User, UserRole
from app.repositories.user_repo import UserRepository


class AuthService:

    def __init__(self):
        self._repo = UserRepository()

    # ── Password helpers ──

    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def _verify_password(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    # ── Token helpers ──

    def _build_tokens(self, user: User) -> dict:
        payload = {"sub": user.email, "role": user.role.value, "name": user.name}
        return {
            "access_token": create_access_token(payload),
            "refresh_token": create_refresh_token(payload),
            "token_type": "bearer",
            "role": user.role.value,
            "name": user.name,
            "email": user.email,
        }

    # ── Register ──

    async def register(self, email: str, name: str, password: str) -> dict:
        if await self._repo.find_by_email(email):
            raise ConflictException(f"Email {email} already registered.")
        if len(password) < 6:
            raise BadRequestException("Password must be at least 6 characters.")

        user = User(
            email=email,
            name=name,
            hashed_password=self._hash_password(password),
            role=UserRole.EMPLOYEE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await self._repo.create(user)
        return self._build_tokens(user)

    # ── Login ──

    async def login(self, email: str, password: str) -> dict:
        user = await self._repo.find_by_email(email)
        if not user or not user.hashed_password:
            raise UnauthorizedException("Invalid email or password.")
        if not self._verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedException("Account is deactivated.")
        return self._build_tokens(user)

    # ── SSO ──

    async def sso_login(self, provider: str, provider_user_id: str, email: str, name: str, avatar_url: str | None = None) -> dict:
        """Upsert user from SSO provider and return tokens."""
        user = await self._repo.find_by_sso(provider, provider_user_id)

        if not user:
            # Check if email already registered (link SSO profile)
            user = await self._repo.find_by_email(email)
            if user:
                user.sso_profiles.append(
                    SSOProfile(provider=provider, provider_user_id=provider_user_id, email=email, name=name, avatar_url=avatar_url)
                )
                user.updated_at = datetime.utcnow()
                await self._repo.update(user)
            else:
                # Create new user
                user = User(
                    email=email,
                    name=name,
                    role=UserRole.EMPLOYEE,
                    sso_profiles=[
                        SSOProfile(provider=provider, provider_user_id=provider_user_id, email=email, name=name, avatar_url=avatar_url)
                    ],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                await self._repo.create(user)

        return self._build_tokens(user)
