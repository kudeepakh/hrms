"""Appraisal model — tracks performance reviews and salary revisions.

Supports a full appraisal workflow:
  1. HR/manager initiates an appraisal for an employee
  2. Rating, feedback, salary revision, designation change are recorded
  3. On completion the Employee record + payroll are updated automatically
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from beanie import Document
from pymongo import IndexModel, ASCENDING, DESCENDING
from pydantic import BaseModel


class AppraisalRecord(Document):
    """One appraisal cycle entry for an employee."""

    emp_code: str
    employee_name: str                       # denormalized
    appraisal_cycle: str                     # e.g. "FY2025-26", "Q4-2026"
    initiated_by: str                        # email of HR/manager who started

    # ── Ratings ──
    rating: Optional[float] = None           # 1.0 – 5.0
    rating_label: Optional[str] = None       # auto-derived: Outstanding, Exceeds, Meets, etc.

    # ── Feedback ──
    manager_feedback: Optional[str] = None
    employee_self_review: Optional[str] = None
    hr_comments: Optional[str] = None

    # ── Compensation changes ──
    old_salary: Optional[float] = None
    new_salary: Optional[float] = None
    hike_pct: Optional[float] = None         # % increase
    old_designation: Optional[str] = None
    new_designation: Optional[str] = None
    old_department: Optional[str] = None
    new_department: Optional[str] = None

    # ── Status workflow ──
    status: str = "initiated"                # initiated | in_review | completed | cancelled
    effective_date: Optional[date] = None    # date from which new salary applies

    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "appraisals"
        indexes = [
            IndexModel([("emp_code", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("appraisal_cycle", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
        ]


def derive_rating_label(rating: float) -> str:
    """Map numeric rating to descriptive label."""
    if rating >= 4.5:
        return "Outstanding"
    elif rating >= 3.5:
        return "Exceeds Expectations"
    elif rating >= 2.5:
        return "Meets Expectations"
    elif rating >= 1.5:
        return "Needs Improvement"
    else:
        return "Unsatisfactory"
