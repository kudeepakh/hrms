"""Leave record document model."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from beanie import Document
from pymongo import IndexModel, ASCENDING


class LeaveRecord(Document):
    """Leave request stored in MongoDB."""

    emp_code: str
    leave_type: str  # casual, sick, earned
    start_date: date
    end_date: date
    status: str = "pending"  # pending, approved, rejected, credit
    reason: Optional[str] = None
    approved_by: Optional[str] = None
    applied_on: datetime = datetime.utcnow()
    days_credited: Optional[int] = None  # for leave credit records

    class Settings:
        name = "leave_records"
        indexes = [
            IndexModel([("emp_code", ASCENDING)]),
        ]
