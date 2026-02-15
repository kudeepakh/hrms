"""Employee repository — employee CRUD and queries."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from app.models.employee import Employee
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):

    def __init__(self):
        super().__init__(Employee)

    async def find_by_emp_code(self, emp_code: str) -> Optional[Employee]:
        return await Employee.find_one(Employee.emp_code == emp_code.upper())

    async def find_by_name(self, name: str) -> Optional[Employee]:
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        return await Employee.find_one({"name": {"$regex": pattern}})

    async def find_by_query(self, query: str) -> Optional[Employee]:
        """Look up by emp_code first, then by name."""
        emp = await self.find_by_emp_code(query)
        if not emp:
            emp = await self.find_by_name(query)
        return emp

    async def list_by_department(self, department: str) -> list[Employee]:
        pattern = re.compile(re.escape(department), re.IGNORECASE)
        return await Employee.find({"department": {"$regex": pattern}}).to_list()

    async def list_active(self) -> list[Employee]:
        return await Employee.find(Employee.status == "active").to_list()

    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
    ) -> tuple[list[Employee], int]:
        """Return a page of active employees + total count.

        *search* filters across name, emp_code, department, designation
        (case-insensitive partial match).
        """
        query: dict = {"status": "active"}
        if search:
            pattern = re.compile(re.escape(search), re.IGNORECASE)
            query["$or"] = [
                {"name": {"$regex": pattern}},
                {"emp_code": {"$regex": pattern}},
                {"department": {"$regex": pattern}},
                {"designation": {"$regex": pattern}},
            ]
        total = await Employee.find(query).count()
        skip = (page - 1) * page_size
        employees = (
            await Employee.find(query)
            .sort("+emp_code")
            .skip(skip)
            .limit(page_size)
            .to_list()
        )
        return employees, total

    async def get_all_departments(self) -> dict[str, int]:
        """Department breakdown with counts."""
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$department", "count": {"$sum": 1}}},
        ]
        results = await Employee.aggregate(pipeline).to_list()
        return {r["_id"]: r["count"] for r in results}

    async def get_average_salary(self) -> float:
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": None, "avg": {"$avg": "$salary"}}},
        ]
        results = await Employee.aggregate(pipeline).to_list()
        return round(results[0]["avg"], 2) if results else 0.0

    async def initiate_resignation(
        self, emp_code: str, resignation_date: str, exit_reason: str
    ) -> Optional[Employee]:
        emp = await self.find_by_emp_code(emp_code)
        if not emp:
            return None
        emp.status = "resigned"
        emp.resignation_date = datetime.strptime(resignation_date, "%Y-%m-%d").date()
        emp.exit_reason = exit_reason
        emp.updated_at = datetime.utcnow()
        await emp.save()
        return emp
