"""Employee REST routes (optional direct access alongside chat)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.models.user import User, RolePermissions
from app.services.employee_service import EmployeeService
from app.services.hr_policy_service import HRPolicyService

router = APIRouter(prefix="/employees", tags=["employees"])
_svc = EmployeeService()
_hr_svc = HRPolicyService()


class SalaryPreviewRequest(BaseModel):
    annual_ctc: float


@router.get("/")
async def list_employees(user: User = Depends(get_current_user)):
    return await _svc.list_all()


@router.post("/salary-preview")
async def salary_preview(
    body: SalaryPreviewRequest,
    user: User = Depends(get_current_user),
):
    """Compute salary breakup from annual CTC using active HR policy."""
    perms = RolePermissions.get_permissions(user.role)
    if "view_payroll" not in perms and "manage_employee" not in perms:
        return {"error": "Access denied. You need view_payroll or manage_employee permission."}
    return await _hr_svc.compute_salary_breakup(body.annual_ctc)
