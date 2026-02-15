"""Attendance service."""

from __future__ import annotations

import json
from typing import Optional

from app.repositories.attendance_repo import AttendanceRepository


class AttendanceService:

    def __init__(self):
        self._repo = AttendanceRepository()

    async def get_records(self, emp_code: str, target_date: Optional[str] = None) -> str:
        records = await self._repo.find_by_emp_code(emp_code, target_date)
        results = [r.model_dump(mode="json", exclude={"id", "revision_id"}) for r in records]
        return json.dumps(results, indent=2, default=str)
