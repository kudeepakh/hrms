"""Employee service — business logic for employee operations."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional

from app.exceptions import ConflictException, NotFoundException
from app.models.employee import Employee, Address, EmergencyContact
from app.repositories.employee_repo import EmployeeRepository


class EmployeeService:
    """Handles employee business logic, delegates persistence to repo."""

    def __init__(self):
        self._repo = EmployeeRepository()

    async def lookup(self, query: str) -> str:
        emp = await self._repo.find_by_query(query)
        if not emp:
            return json.dumps({"error": f"No employee found for '{query}'."})
        return emp.model_dump_json(indent=2, exclude={"id", "revision_id"})

    async def list_by_department(self, department: str) -> str:
        emps = await self._repo.list_by_department(department)
        results = [e.model_dump(mode="json", exclude={"id", "revision_id"}) for e in emps]
        return json.dumps(results, indent=2, default=str)

    async def add_employee(
        self,
        emp_code: str,
        name: str,
        email: str,
        department: str,
        designation: str,
        date_of_joining: str,
        salary: float,
        manager_name: Optional[str] = None,
        # Extended fields
        phone: Optional[str] = None,
        personal_email: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        gender: Optional[str] = None,
        blood_group: Optional[str] = None,
        marital_status: Optional[str] = None,
        nationality: str = "Indian",
        current_address: Optional[dict] = None,
        permanent_address: Optional[dict] = None,
        emergency_contact: Optional[dict] = None,
        pan_number: Optional[str] = None,
        aadhaar_number: Optional[str] = None,
        bank_account: Optional[str] = None,
        bank_name: Optional[str] = None,
        ifsc_code: Optional[str] = None,
    ) -> str:
        existing = await self._repo.find_by_emp_code(emp_code)
        if existing:
            raise ConflictException(f"Employee {emp_code} already exists.")
        emp = Employee(
            emp_code=emp_code.upper(),
            name=name,
            email=email,
            department=department,
            designation=designation,
            date_of_joining=date.fromisoformat(date_of_joining),
            salary=salary,
            manager_name=manager_name,
            phone=phone,
            personal_email=personal_email,
            date_of_birth=date.fromisoformat(date_of_birth) if date_of_birth else None,
            gender=gender,
            blood_group=blood_group,
            marital_status=marital_status,
            nationality=nationality,
            current_address=Address(**current_address) if current_address else None,
            permanent_address=Address(**permanent_address) if permanent_address else None,
            emergency_contact=EmergencyContact(**emergency_contact) if emergency_contact else None,
            pan_number=pan_number,
            aadhaar_number=aadhaar_number,
            bank_account=bank_account,
            bank_name=bank_name,
            ifsc_code=ifsc_code,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await self._repo.create(emp)
        return json.dumps({"success": True, "message": f"Employee {emp_code} ({name}) added successfully."})

    async def update_employee(self, emp_code: str, **updates) -> str:
        emp = await self._repo.find_by_emp_code(emp_code)
        if not emp:
            raise NotFoundException("Employee", emp_code)
        for key, value in updates.items():
            if hasattr(emp, key) and value is not None:
                setattr(emp, key, value)
        emp.updated_at = datetime.utcnow()
        await self._repo.update(emp)
        return json.dumps({"success": True, "message": f"Employee {emp_code} updated successfully."})

    async def initiate_resignation(self, emp_code: str, resignation_date: str, reason: str) -> str:
        emp = await self._repo.initiate_resignation(emp_code, resignation_date, reason)
        if not emp:
            raise NotFoundException("Employee", emp_code)
        return json.dumps({
            "success": True,
            "message": f"Resignation initiated for {emp_code}. Status: resigned. Reason: {reason}.",
        })

    async def get_company_stats(self) -> str:
        total = await self._repo.count({"status": "active"})
        departments = await self._repo.get_all_departments()
        avg_salary = await self._repo.get_average_salary()
        return json.dumps({
            "total_employees": total,
            "department_breakdown": departments,
            "average_salary": avg_salary,
        }, indent=2)

    async def list_all(self) -> list[dict]:
        emps = await self._repo.list_active()
        return [e.model_dump(mode="json", exclude={"id", "revision_id"}) for e in emps]

    async def list_all_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
    ) -> str:
        """Return paginated employee list with metadata as JSON."""
        import math
        emps, total = await self._repo.list_paginated(page, page_size, search)
        total_pages = math.ceil(total / page_size) if total else 1
        rows = [e.model_dump(mode="json", exclude={"id", "revision_id"}) for e in emps]
        return json.dumps({
            "employees": rows,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_employees": total,
                "total_pages": total_pages,
            },
        }, indent=2, default=str)
