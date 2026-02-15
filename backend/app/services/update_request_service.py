"""Update-request service — employee self-service profile change workflow.

Employees submit a request to change their profile fields. HR or managers
review and approve/reject. On approval, changes are applied to the Employee
document automatically.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from app.models.update_request import UpdateRequest, FieldChange
from app.models.employee import Employee
from app.repositories.employee_repo import EmployeeRepository


class UpdateRequestService:
    """Handles employee profile-update requests."""

    def __init__(self):
        self._emp_repo = EmployeeRepository()

    # ── Submit ───────────────────────────────────────────

    async def submit_request(
        self,
        emp_code: str,
        fields: dict[str, str],
        reason: str,
    ) -> dict:
        """Employee submits a profile change request.

        Args:
            emp_code: Employee code of the requester
            fields: Dict of {field_name: desired_new_value}
            reason: Why the change is needed
        """
        emp = await self._emp_repo.find_by_emp_code(emp_code.upper())
        if not emp:
            return {"error": f"Employee {emp_code} not found."}

        # Only allow safe fields to be changed by employees
        ALLOWED_FIELDS = {
            "name", "email", "department", "designation",
            "manager_name",
        }
        invalid = set(fields.keys()) - ALLOWED_FIELDS
        if invalid:
            return {"error": f"You cannot request changes to: {', '.join(invalid)}. Allowed: {', '.join(sorted(ALLOWED_FIELDS))}"}

        # Build field-change entries with current values
        changes = []
        for field, new_value in fields.items():
            current = str(getattr(emp, field, "")) if hasattr(emp, field) else ""
            changes.append(FieldChange(
                field=field,
                current_value=current,
                requested_value=str(new_value),
            ))

        req = UpdateRequest(
            emp_code=emp_code.upper(),
            employee_name=emp.name,
            requested_fields=changes,
            reason=reason,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await req.insert()

        return {
            "success": True,
            "message": f"Update request submitted for {emp.name} ({emp_code}). Request is pending HR/manager approval.",
            "request_id": str(req.id),
            "fields_requested": [
                {"field": c.field, "current": c.current_value, "requested": c.requested_value}
                for c in changes
            ],
        }

    # ── List Requests ────────────────────────────────────

    async def list_requests(
        self,
        status: Optional[str] = None,
        emp_code: Optional[str] = None,
    ) -> list[dict]:
        """List update requests, optionally filtered."""
        query = {}
        if status:
            query["status"] = status
        if emp_code:
            query["emp_code"] = emp_code.upper()

        requests = await UpdateRequest.find(query).sort("-created_at").limit(50).to_list()

        return [
            {
                "request_id": str(r.id),
                "emp_code": r.emp_code,
                "employee_name": r.employee_name,
                "status": r.status,
                "reason": r.reason,
                "fields": [
                    {"field": c.field, "current": c.current_value, "requested": c.requested_value}
                    for c in r.requested_fields
                ],
                "reviewed_by": r.reviewed_by,
                "review_comment": r.review_comment,
                "created_at": r.created_at.isoformat(),
            }
            for r in requests
        ]

    # ── Approve / Reject ─────────────────────────────────

    async def review_request(
        self,
        request_id: str,
        action: str,           # "approve" or "reject"
        reviewer_email: str,
        comment: Optional[str] = None,
    ) -> dict:
        """HR/manager approves or rejects an update request."""
        from bson import ObjectId

        req = await UpdateRequest.get(ObjectId(request_id))
        if not req:
            return {"error": f"Update request '{request_id}' not found."}

        if req.status != "pending":
            return {"error": f"Request is already '{req.status}'. Cannot {action}."}

        action_lower = action.lower().strip()
        if action_lower not in ("approve", "reject"):
            return {"error": "Action must be 'approve' or 'reject'."}

        if action_lower == "approve":
            # Apply changes to Employee document
            emp = await self._emp_repo.find_by_emp_code(req.emp_code)
            if not emp:
                return {"error": f"Employee {req.emp_code} not found. Cannot apply changes."}

            applied = []
            for change in req.requested_fields:
                if hasattr(emp, change.field):
                    setattr(emp, change.field, change.requested_value)
                    applied.append(f"{change.field}: {change.current_value} → {change.requested_value}")
            emp.updated_at = datetime.utcnow()
            await self._emp_repo.update(emp)

            req.status = "approved"
            req.reviewed_by = reviewer_email
            req.review_comment = comment
            req.reviewed_at = datetime.utcnow()
            req.updated_at = datetime.utcnow()
            await req.save()

            return {
                "success": True,
                "message": f"Request approved. Changes applied to {req.emp_code} ({req.employee_name}): {'; '.join(applied)}.",
            }

        else:  # reject
            req.status = "rejected"
            req.reviewed_by = reviewer_email
            req.review_comment = comment
            req.reviewed_at = datetime.utcnow()
            req.updated_at = datetime.utcnow()
            await req.save()

            return {
                "success": True,
                "message": f"Request rejected for {req.emp_code} ({req.employee_name}). Comment: {comment or 'No comment'}.",
            }
