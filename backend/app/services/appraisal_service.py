"""Appraisal service — performance review and salary revision workflow.

Workflow:
  1. HR/manager → initiate_appraisal (status: initiated)
  2. Optional: add ratings, feedback (status: in_review)
  3. HR/manager → complete_appraisal with rating, hike%, new designation
     → Employee salary + designation updated automatically
     → New payroll generated for current month
  4. History is fully queryable per employee
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from app.models.appraisal import AppraisalRecord, derive_rating_label
from app.models.employee import Employee
from app.repositories.employee_repo import EmployeeRepository
from app.services.hr_policy_service import HRPolicyService


class AppraisalService:
    """Handles the end-to-end appraisal lifecycle."""

    def __init__(self):
        self._emp_repo = EmployeeRepository()
        self._hr_svc = HRPolicyService()

    # ── Initiate ─────────────────────────────────────────

    async def initiate_appraisal(
        self,
        emp_code: str,
        appraisal_cycle: str,
        initiated_by: str,
        manager_feedback: Optional[str] = None,
    ) -> dict:
        """Start an appraisal for an employee in a given cycle."""
        emp = await self._emp_repo.find_by_emp_code(emp_code.upper())
        if not emp:
            return {"error": f"Employee {emp_code} not found."}

        # Check for duplicate in same cycle
        existing = await AppraisalRecord.find_one(
            AppraisalRecord.emp_code == emp_code.upper(),
            AppraisalRecord.appraisal_cycle == appraisal_cycle,
            AppraisalRecord.status != "cancelled",
        )
        if existing:
            return {
                "error": f"An appraisal already exists for {emp_code} in cycle '{appraisal_cycle}' (status: {existing.status})."
            }

        appraisal = AppraisalRecord(
            emp_code=emp_code.upper(),
            employee_name=emp.name,
            appraisal_cycle=appraisal_cycle,
            initiated_by=initiated_by,
            old_salary=emp.salary,
            old_designation=emp.designation,
            old_department=emp.department,
            manager_feedback=manager_feedback,
            status="initiated",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await appraisal.insert()

        return {
            "success": True,
            "message": (
                f"Appraisal initiated for {emp.name} ({emp_code}) — cycle '{appraisal_cycle}'. "
                f"Current salary: ₹{emp.salary:,.0f}, designation: {emp.designation}. "
                f"Use complete_appraisal to finalize with rating and salary revision."
            ),
            "appraisal_id": str(appraisal.id),
            "current_salary": emp.salary,
            "current_designation": emp.designation,
        }

    # ── Complete ─────────────────────────────────────────

    async def complete_appraisal(
        self,
        emp_code: str,
        appraisal_cycle: str,
        rating: float,
        hike_pct: Optional[float] = None,
        new_salary: Optional[float] = None,
        new_designation: Optional[str] = None,
        new_department: Optional[str] = None,
        manager_feedback: Optional[str] = None,
        hr_comments: Optional[str] = None,
        effective_date: Optional[str] = None,
        completed_by: Optional[str] = None,
    ) -> dict:
        """Finalize an appraisal — apply salary revision and update employee."""
        emp = await self._emp_repo.find_by_emp_code(emp_code.upper())
        if not emp:
            return {"error": f"Employee {emp_code} not found."}

        # Find the open appraisal
        appraisal = await AppraisalRecord.find_one(
            AppraisalRecord.emp_code == emp_code.upper(),
            AppraisalRecord.appraisal_cycle == appraisal_cycle,
            AppraisalRecord.status.is_in(["initiated", "in_review"]),
        )
        if not appraisal:
            return {
                "error": (
                    f"No open appraisal found for {emp_code} in cycle '{appraisal_cycle}'. "
                    f"Initiate one first with initiate_appraisal."
                )
            }

        # Validate rating
        if not 1.0 <= rating <= 5.0:
            return {"error": "Rating must be between 1.0 and 5.0."}

        # Calculate new salary
        old_salary = emp.salary
        if new_salary is not None:
            final_salary = new_salary
            final_hike = round(((new_salary - old_salary) / old_salary) * 100, 2)
        elif hike_pct is not None:
            final_hike = hike_pct
            final_salary = round(old_salary * (1 + hike_pct / 100), 2)
        else:
            final_hike = 0.0
            final_salary = old_salary

        final_designation = new_designation or emp.designation
        final_department = new_department or emp.department
        eff_date = date.fromisoformat(effective_date) if effective_date else date.today()

        # ── Update appraisal record ──
        appraisal.rating = rating
        appraisal.rating_label = derive_rating_label(rating)
        appraisal.hike_pct = final_hike
        appraisal.old_salary = old_salary
        appraisal.new_salary = final_salary
        appraisal.old_designation = emp.designation
        appraisal.new_designation = final_designation
        appraisal.old_department = emp.department
        appraisal.new_department = final_department
        appraisal.effective_date = eff_date
        appraisal.status = "completed"
        if manager_feedback:
            appraisal.manager_feedback = manager_feedback
        if hr_comments:
            appraisal.hr_comments = hr_comments
        appraisal.updated_at = datetime.utcnow()
        await appraisal.save()

        # ── Update Employee record ──
        emp.salary = final_salary
        emp.designation = final_designation
        emp.department = final_department
        emp.updated_at = datetime.utcnow()
        await self._emp_repo.update(emp)

        # ── Auto-generate new payroll from revised CTC ──
        payroll_msg = ""
        try:
            current_month = datetime.utcnow().strftime("%Y-%m")
            payroll_result = await self._hr_svc.create_payroll_from_ctc(
                emp_code=emp_code.upper(),
                annual_ctc=final_salary,
                month=current_month,
            )
            net_pay = payroll_result.get("payroll", {}).get("net_take_home", {}).get("monthly", "N/A")
            payroll_msg = f" New payroll for {current_month} created — net pay ₹{net_pay:,}."
        except Exception:
            payroll_msg = " (Auto-payroll generation failed — can be done manually.)"

        return {
            "success": True,
            "message": (
                f"Appraisal completed for {emp.name} ({emp_code}). "
                f"Rating: {rating} ({appraisal.rating_label}). "
                f"Salary: ₹{old_salary:,.0f} → ₹{final_salary:,.0f} ({final_hike:+.1f}%). "
                f"Designation: {appraisal.old_designation} → {final_designation}."
                f"{payroll_msg}"
            ),
            "appraisal": {
                "emp_code": emp_code.upper(),
                "employee_name": emp.name,
                "cycle": appraisal_cycle,
                "rating": rating,
                "rating_label": appraisal.rating_label,
                "old_salary": old_salary,
                "new_salary": final_salary,
                "hike_pct": final_hike,
                "old_designation": appraisal.old_designation,
                "new_designation": final_designation,
                "effective_date": eff_date.isoformat(),
            },
        }

    # ── History ──────────────────────────────────────────

    async def get_appraisal_history(
        self,
        emp_code: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get appraisal history, optionally filtered by employee."""
        query = {}
        if emp_code:
            query["emp_code"] = emp_code.upper()

        records = await AppraisalRecord.find(query).sort("-created_at").limit(limit).to_list()

        return [
            {
                "appraisal_id": str(r.id),
                "emp_code": r.emp_code,
                "employee_name": r.employee_name,
                "cycle": r.appraisal_cycle,
                "status": r.status,
                "rating": r.rating,
                "rating_label": r.rating_label,
                "old_salary": r.old_salary,
                "new_salary": r.new_salary,
                "hike_pct": r.hike_pct,
                "old_designation": r.old_designation,
                "new_designation": r.new_designation,
                "manager_feedback": r.manager_feedback,
                "hr_comments": r.hr_comments,
                "effective_date": r.effective_date.isoformat() if r.effective_date else None,
                "initiated_by": r.initiated_by,
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ]

    # ── Cancel ───────────────────────────────────────────

    async def cancel_appraisal(
        self,
        emp_code: str,
        appraisal_cycle: str,
        cancelled_by: str,
        reason: str,
    ) -> dict:
        """Cancel an in-progress appraisal."""
        appraisal = await AppraisalRecord.find_one(
            AppraisalRecord.emp_code == emp_code.upper(),
            AppraisalRecord.appraisal_cycle == appraisal_cycle,
            AppraisalRecord.status.is_in(["initiated", "in_review"]),
        )
        if not appraisal:
            return {"error": f"No open appraisal for {emp_code} in cycle '{appraisal_cycle}'."}

        appraisal.status = "cancelled"
        appraisal.hr_comments = f"Cancelled by {cancelled_by}: {reason}"
        appraisal.updated_at = datetime.utcnow()
        await appraisal.save()

        return {
            "success": True,
            "message": f"Appraisal for {appraisal.employee_name} ({emp_code}) in cycle '{appraisal_cycle}' has been cancelled.",
        }
