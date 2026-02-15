"""User document — authentication, roles, and SSO profiles."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document
from pymongo import IndexModel, ASCENDING
from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    HR_ADMIN = "hr_admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class RolePermissions:
    """Centralized permission map — single source of truth."""

    _MAP: dict[UserRole, set[str]] = {
        UserRole.SUPER_ADMIN: {
            "view_employee",
            "view_leave",
            "apply_leave",
            "approve_leave",
            "view_payroll",
            "view_attendance",
            "manage_employee",
            "manage_roles",
            "view_own_data",
            "view_all_data",
        },
        UserRole.HR_ADMIN: {
            "view_employee",
            "view_leave",
            "apply_leave",
            "approve_leave",
            "view_payroll",
            "view_attendance",
            "manage_employee",
            "view_own_data",
            "view_all_data",
        },
        UserRole.MANAGER: {
            "view_employee",
            "view_leave",
            "apply_leave",
            "approve_leave",
            "view_payroll",
            "view_attendance",
            "view_own_data",
        },
        UserRole.EMPLOYEE: {
            "view_employee",
            "view_leave",
            "apply_leave",
            "view_attendance",
            "view_payroll",
            "view_own_data",
        },
    }

    @classmethod
    def has_permission(cls, role: UserRole, permission: str) -> bool:
        return permission in cls._MAP.get(role, set())

    @classmethod
    def get_permissions(cls, role: UserRole) -> set[str]:
        return cls._MAP.get(role, set())


class SSOProfile(BaseModel):
    """Linked SSO identity."""
    provider: str  # google, microsoft, github
    provider_user_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class User(Document):
    """User account — supports password + SSO login."""

    email: str
    name: str
    hashed_password: Optional[str] = None  # None for SSO-only users
    role: UserRole = UserRole.EMPLOYEE
    emp_code: Optional[str] = None  # Link to Employee document
    is_active: bool = True
    sso_profiles: list[SSOProfile] = []
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
        ]

    def has_permission(self, permission: str) -> bool:
        return RolePermissions.has_permission(self.role, permission)
