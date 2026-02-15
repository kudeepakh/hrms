"""User repository — authentication and role queries."""

from __future__ import annotations

from typing import Optional

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self):
        super().__init__(User)

    async def find_by_email(self, email: str) -> Optional[User]:
        return await User.find_one(User.email == email)

    async def find_by_sso(self, provider: str, provider_user_id: str) -> Optional[User]:
        return await User.find_one(
            {"sso_profiles": {"$elemMatch": {"provider": provider, "provider_user_id": provider_user_id}}}
        )

    async def update_role(self, email: str, new_role: UserRole) -> Optional[User]:
        user = await self.find_by_email(email)
        if user:
            user.role = new_role
            await user.save()
        return user

    async def list_users(self, role: Optional[UserRole] = None, limit: int = 100) -> list[User]:
        filters = {}
        if role:
            filters["role"] = role
        return await User.find(filters).limit(limit).to_list()
