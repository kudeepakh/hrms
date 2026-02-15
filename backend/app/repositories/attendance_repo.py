"""Attendance repository."""

from __future__ import annotations

from datetime import date
from typing import Optional

from app.models.attendance import Attendance
from app.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):

    def __init__(self):
        super().__init__(Attendance)

    async def find_by_emp_code(
        self, emp_code: str, target_date: Optional[str] = None, limit: int = 10
    ) -> list[Attendance]:
        filters: dict = {"emp_code": emp_code.upper()}
        if target_date:
            filters["date"] = date.fromisoformat(target_date)
        return await (
            Attendance.find(filters)
            .sort("-date")
            .limit(limit)
            .to_list()
        )
