"""Payroll service."""

from __future__ import annotations

import json

from app.repositories.payroll_repo import PayrollRepository


class PayrollService:

    def __init__(self):
        self._repo = PayrollRepository()

    async def get_slip(self, emp_code: str, month: str | None = None) -> str:
        if month:
            record = await self._repo.find_by_emp_and_month(emp_code, month)
            if record:
                return record.model_dump_json(indent=2, exclude={"id", "revision_id"})
            return json.dumps({"error": f"No payroll record found for {emp_code} in {month}."})
        else:
            records = await self._repo.find_all_by_emp(emp_code)
            if records:
                return json.dumps(
                    [json.loads(r.model_dump_json(exclude={"id", "revision_id"})) for r in records],
                    indent=2,
                )
            return json.dumps({"error": f"No payroll records found for {emp_code}."})
