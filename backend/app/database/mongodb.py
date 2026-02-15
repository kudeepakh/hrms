"""MongoDB connection setup using Motor (async) + Beanie ODM."""

from __future__ import annotations

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    """Initialize Motor client and Beanie ODM."""
    global _client

    from app.models.user import User
    from app.models.employee import Employee
    from app.models.leave import LeaveRecord
    from app.models.attendance import Attendance
    from app.models.payroll import Payroll
    from app.models.audit_log import AuditLog
    from app.models.hr_policy import HRPolicy
    from app.cache.query_cache import CachedQuery
    from app.models.update_request import UpdateRequest
    from app.models.appraisal import AppraisalRecord

    _client = AsyncIOMotorClient(settings.MONGODB_URI)

    await init_beanie(
        database=_client[settings.MONGODB_DB_NAME],
        document_models=[
            User,
            Employee,
            LeaveRecord,
            Attendance,
            Payroll,
            AuditLog,
            HRPolicy,
            CachedQuery,
            UpdateRequest,
            AppraisalRecord,
        ],
    )


async def close_db() -> None:
    """Close the Motor client."""
    global _client
    if _client:
        _client.close()
        _client = None


def get_database():
    """Return the raw Motor database object."""
    if _client is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _client[settings.MONGODB_DB_NAME]
