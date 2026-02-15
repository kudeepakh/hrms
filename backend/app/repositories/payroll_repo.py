"""Payroll repository."""

from __future__ import annotations

from typing import Optional

from app.models.payroll import Payroll
from app.repositories.base import BaseRepository


class PayrollRepository(BaseRepository[Payroll]):

    def __init__(self):
        super().__init__(Payroll)

    async def find_by_emp_and_month(self, emp_code: str, month: str) -> Optional[Payroll]:
        return await Payroll.find_one(
            Payroll.emp_code == emp_code.upper(),
            Payroll.month == month,
        )

    async def find_all_by_emp(self, emp_code: str) -> list[Payroll]:
        return await Payroll.find(
            Payroll.emp_code == emp_code.upper(),
        ).sort("-month").to_list()
