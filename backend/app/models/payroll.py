"""Payroll document model."""

from __future__ import annotations

from beanie import Document
from pymongo import IndexModel, ASCENDING


class Payroll(Document):
    """Monthly payroll / salary slip."""

    emp_code: str
    month: str  # YYYY-MM format
    basic: float
    hra: float
    allowances: float = 0.0
    deductions: float
    net_pay: float

    class Settings:
        name = "payroll"
        indexes = [
            IndexModel([("emp_code", ASCENDING)]),
        ]
