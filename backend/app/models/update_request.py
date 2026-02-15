"""Employee profile-update request model.

Employees can request changes to their own profile data. HR/manager
reviews and approves or rejects. On approval the changes are applied
to the Employee document automatically.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from beanie import Document
from pymongo import IndexModel, ASCENDING, DESCENDING
from pydantic import BaseModel


class FieldChange(BaseModel):
    """One field the employee wants to change."""
    field: str                     # e.g. "name", "email", "department"
    current_value: Optional[str] = None
    requested_value: str


class UpdateRequest(Document):
    """Employee-initiated profile update request."""

    emp_code: str
    employee_name: str             # denormalized for convenience
    requested_fields: list[FieldChange]
    reason: str                    # why the employee wants this change
    status: str = "pending"        # pending | approved | rejected
    reviewed_by: Optional[str] = None   # email of HR/manager who reviewed
    review_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "update_requests"
        indexes = [
            IndexModel([("emp_code", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
        ]
