"""Leave repository — leave record queries and mutations."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from app.models.leave import LeaveRecord
from app.repositories.base import BaseRepository


class LeaveRepository(BaseRepository[LeaveRecord]):

    def __init__(self):
        super().__init__(LeaveRecord)

    async def find_by_emp_code(
        self, emp_code: str, status: Optional[str] = None
    ) -> list[LeaveRecord]:
        filters: dict = {"emp_code": emp_code.upper()}
        if status:
            filters["status"] = status.lower()
        return await LeaveRecord.find(filters).to_list()

    async def apply_leave(
        self,
        emp_code: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        reason: str,
    ) -> LeaveRecord:
        record = LeaveRecord(
            emp_code=emp_code.upper(),
            leave_type=leave_type.lower(),
            start_date=date.fromisoformat(start_date),
            end_date=date.fromisoformat(end_date),
            status="pending",
            reason=reason,
            applied_on=datetime.utcnow(),
        )
        await record.insert()
        return record

    async def update_status(
        self, emp_code: str, start_date: str, new_status: str, approved_by: str
    ) -> Optional[LeaveRecord]:
        """Approve or reject a pending leave."""
        record = await LeaveRecord.find_one(
            LeaveRecord.emp_code == emp_code.upper(),
            LeaveRecord.start_date == date.fromisoformat(start_date),
            LeaveRecord.status == "pending",
        )
        if record:
            record.status = new_status.lower()
            record.approved_by = approved_by
            await record.save()
        return record
