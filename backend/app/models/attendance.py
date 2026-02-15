"""Attendance document model."""

from __future__ import annotations

from datetime import date
from typing import Optional

from beanie import Document
from pymongo import IndexModel, ASCENDING


class Attendance(Document):
    """Daily attendance record."""

    emp_code: str
    date: date
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str = "present"  # present, absent, half-day, work-from-home

    class Settings:
        name = "attendance"
        indexes = [
            IndexModel([("emp_code", ASCENDING)]),
        ]
