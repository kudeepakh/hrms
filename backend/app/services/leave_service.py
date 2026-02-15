"""Leave service — business logic for leave operations."""

from __future__ import annotations

import json
from typing import Optional

from app.repositories.leave_repo import LeaveRepository


class LeaveService:

    def __init__(self):
        self._repo = LeaveRepository()

    async def get_records(self, emp_code: str, status: Optional[str] = None) -> str:
        records = await self._repo.find_by_emp_code(emp_code, status)
        results = [r.model_dump(mode="json", exclude={"id", "revision_id"}) for r in records]
        return json.dumps(results, indent=2, default=str)

    async def apply_leave(
        self, emp_code: str, leave_type: str, start_date: str, end_date: str, reason: str
    ) -> str:
        record = await self._repo.apply_leave(emp_code, leave_type, start_date, end_date, reason)
        return json.dumps({
            "success": True,
            "message": f"Leave applied for {emp_code} from {start_date} to {end_date}.",
        })

    async def approve_or_reject(
        self, emp_code: str, start_date: str, action: str, approved_by: str
    ) -> str:
        new_status = "approved" if action.lower() == "approve" else "rejected"
        record = await self._repo.update_status(emp_code, start_date, new_status, approved_by)
        if not record:
            return json.dumps({"error": f"No pending leave found for {emp_code} starting {start_date}."})
        return json.dumps({
            "success": True,
            "message": f"Leave for {emp_code} starting {start_date} has been {new_status}.",
        })
