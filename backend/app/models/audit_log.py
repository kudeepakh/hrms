"""Audit log document — tracks every write operation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from beanie import Document
from pymongo import IndexModel, ASCENDING


class AuditLog(Document):
    """Immutable audit trail for all mutations."""

    action: str  # e.g. "add_employee", "approve_leave", "assign_role"
    performed_by: str  # user email
    target: Optional[str] = None  # e.g. emp_code affected
    details: Optional[dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()

    class Settings:
        name = "audit_logs"
        indexes = [
            IndexModel([("performed_by", ASCENDING)]),
        ]
