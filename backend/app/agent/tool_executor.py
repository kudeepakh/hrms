"""
RBAC-aware tool executor.

Maps tool names to service-layer calls and checks user permissions
before executing any tool.  Services return JSON strings; we parse
them back to dicts before returning to the orchestrator.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.models.audit_log import AuditLog
from app.models.user import RolePermissions, User, UserRole
from app.services.employee_service import EmployeeService
from app.services.leave_service import LeaveService
from app.services.attendance_service import AttendanceService
from app.services.payroll_service import PayrollService
from app.services.hr_policy_service import HRPolicyService
from app.services.update_request_service import UpdateRequestService
from app.services.appraisal_service import AppraisalService
from app.repositories.user_repo import UserRepository

logger = logging.getLogger("hrms.tool_executor")

# ---------------------------------------------------------------------------
# Permission matrix – map each tool to the permission it requires
# ---------------------------------------------------------------------------
TOOL_PERMISSION_MAP: dict[str, str | None] = {
    "lookup_employee": "view_employee",
    "list_employees_by_department": "view_employee",
    "list_all_employees": "view_all_data",
    "get_leave_records": "view_leave",
    "apply_leave": "apply_leave",
    "approve_or_reject_leave": "approve_leave",
    "get_attendance": "view_attendance",
    "get_payroll": "view_payroll",
    "get_company_stats": "view_employee",
    "add_employee": "manage_employee",
    "update_employee": "manage_employee",
    "initiate_resignation": "manage_employee",
    "assign_role": "manage_roles",
    "set_hr_policy": "manage_employee",
    "get_hr_policy": "view_employee",
    "get_hr_policy_history": "view_employee",
    "compute_salary_breakup": "view_payroll",
    # Employee tax regime
    "set_employee_tax_regime": "apply_leave",  # any authenticated user can set their own
    # Update requests
    "submit_update_request": "apply_leave",  # any authenticated user can submit
    "list_update_requests": "view_employee",
    "review_update_request": "manage_employee",
    # Appraisals
    "initiate_appraisal": "manage_employee",
    "complete_appraisal": "manage_employee",
    "get_appraisal_history": "view_employee",
}

# Tools that mutate data (triggers cache invalidation)
WRITE_TOOLS = {
    "apply_leave",
    "approve_or_reject_leave",
    "add_employee",
    "update_employee",
    "initiate_resignation",
    "assign_role",
    "set_hr_policy",
    "set_employee_tax_regime",
    "submit_update_request",
    "review_update_request",
    "initiate_appraisal",
    "complete_appraisal",
}


async def _audit(action: str, user: User, target: str, details: dict | None = None):
    """Write an audit-log entry for a mutation."""
    await AuditLog(
        action=action,
        performed_by=user.email,
        target=target,
        details=details or {},
    ).insert()


def _parse(json_str: str) -> dict | list:
    """Safely parse a JSON string from a service."""
    return json.loads(json_str)


async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    user: User,
) -> dict[str, Any]:
    """
    Execute a tool call after verifying RBAC permissions.

    Returns a dict that will be serialised to JSON and sent back
    to the LLM as the tool result.
    """

    # ---- Permission check --------------------------------------------------
    required_permission = TOOL_PERMISSION_MAP.get(tool_name)
    if required_permission:
        user_perms = RolePermissions.get_permissions(user.role)
        if required_permission not in user_perms:
            return {
                "error": (
                    f"Access denied. Your role '{user.role.value}' does not have "
                    f"'{required_permission}' permission."
                )
            }

    # ---- Service instances --------------------------------------------------
    emp_svc = EmployeeService()
    leave_svc = LeaveService()
    att_svc = AttendanceService()
    pay_svc = PayrollService()
    hr_svc = HRPolicyService()
    user_repo = UserRepository()
    update_req_svc = UpdateRequestService()
    appraisal_svc = AppraisalService()

    try:
        # ---- Dispatch -------------------------------------------------------
        if tool_name == "lookup_employee":
            result = _parse(await emp_svc.lookup(arguments["query"]))
            return result if isinstance(result, dict) else {"data": result}

        elif tool_name == "list_employees_by_department":
            result = _parse(await emp_svc.list_by_department(arguments["department"]))
            if isinstance(result, list) and not result:
                return {"message": f"No employees in '{arguments['department']}'."}
            return {"employees": result} if isinstance(result, list) else result

        elif tool_name == "get_leave_records":
            result = _parse(await leave_svc.get_records(
                arguments["emp_code"],
                status=arguments.get("status"),
            ))
            if isinstance(result, list) and not result:
                return {"message": f"No leave records for {arguments['emp_code']}."}
            return {"leave_records": result} if isinstance(result, list) else result

        elif tool_name == "apply_leave":
            result = _parse(await leave_svc.apply_leave(
                emp_code=arguments["emp_code"],
                leave_type=arguments["leave_type"],
                start_date=arguments["start_date"],
                end_date=arguments["end_date"],
                reason=arguments["reason"],
            ))
            await _audit("apply_leave", user, arguments["emp_code"], arguments)
            return result

        elif tool_name == "approve_or_reject_leave":
            result = _parse(await leave_svc.approve_or_reject(
                emp_code=arguments["emp_code"],
                start_date=arguments["start_date"],
                action=arguments["action"],
                approved_by=user.email,
            ))
            await _audit("approve_reject_leave", user, arguments["emp_code"], arguments)
            return result

        elif tool_name == "get_attendance":
            result = _parse(await att_svc.get_records(
                arguments["emp_code"],
                target_date=arguments.get("date"),
            ))
            if isinstance(result, list) and not result:
                return {"message": f"No attendance records for {arguments['emp_code']}."}
            return {"attendance": result} if isinstance(result, list) else result

        elif tool_name == "get_payroll":
            result = _parse(await pay_svc.get_slip(
                arguments["emp_code"], arguments.get("month"),
            ))
            if isinstance(result, list) and not result:
                return {"message": f"No payroll records for {arguments['emp_code']}."}
            return {"payroll": result} if isinstance(result, list) else result

        elif tool_name == "list_all_employees":
            page = arguments.get("page", 1)
            page_size = min(arguments.get("page_size", 10), 25)
            search = arguments.get("search")
            result = _parse(await emp_svc.list_all_paginated(page, page_size, search))
            return result

        elif tool_name == "get_company_stats":
            result = _parse(await emp_svc.get_company_stats())
            return result

        elif tool_name == "add_employee":
            result = _parse(await emp_svc.add_employee(
                emp_code=arguments["emp_code"],
                name=arguments["name"],
                email=arguments["email"],
                department=arguments["department"],
                designation=arguments["designation"],
                date_of_joining=arguments["date_of_joining"],
                salary=arguments["salary"],
                manager_name=arguments.get("manager_name"),
                # Extended fields
                phone=arguments.get("phone"),
                personal_email=arguments.get("personal_email"),
                date_of_birth=arguments.get("date_of_birth"),
                gender=arguments.get("gender"),
                blood_group=arguments.get("blood_group"),
                marital_status=arguments.get("marital_status"),
                nationality=arguments.get("nationality", "Indian"),
                current_address=arguments.get("current_address"),
                permanent_address=arguments.get("permanent_address"),
                emergency_contact=arguments.get("emergency_contact"),
                pan_number=arguments.get("pan_number"),
                aadhaar_number=arguments.get("aadhaar_number"),
                bank_account=arguments.get("bank_account"),
                bank_name=arguments.get("bank_name"),
                ifsc_code=arguments.get("ifsc_code"),
            ))
            # Auto-generate payroll from CTC using active HR policy
            from datetime import datetime
            current_month = datetime.utcnow().strftime("%Y-%m")
            try:
                payroll_result = await hr_svc.create_payroll_from_ctc(
                    emp_code=arguments["emp_code"],
                    annual_ctc=arguments["salary"],
                    month=current_month,
                )
                result["payroll"] = payroll_result.get("payroll", {})
                result["message"] += (
                    f" Payroll created for {current_month} with net pay "
                    f"₹{payroll_result.get('payroll', {}).get('net_take_home', {}).get('monthly', 'N/A'):,}."
                )
            except Exception as e:
                logger.warning("Auto-payroll failed for %s: %s", arguments["emp_code"], e)
                result["payroll_warning"] = f"Auto-payroll generation failed: {str(e)}"

            # Auto-credit annual leaves from policy
            try:
                leave_credits = await hr_svc.get_leave_credits()
                from app.models.leave import LeaveRecord
                for leave_type, days in [
                    ("casual", leave_credits["casual_leave"]),
                    ("sick", leave_credits["sick_leave"]),
                    ("earned", leave_credits["earned_leave"]),
                ]:
                    await LeaveRecord(
                        emp_code=arguments["emp_code"].upper(),
                        leave_type=leave_type,
                        start_date=datetime.utcnow().date(),
                        end_date=datetime.utcnow().date(),
                        status="credit",
                        reason=f"Annual {leave_type} leave credit ({days} days) as per HR policy",
                        days_credited=days,
                    ).insert()
                result["message"] += (
                    f" Leave credits: CL={leave_credits['casual_leave']}, "
                    f"SL={leave_credits['sick_leave']}, EL={leave_credits['earned_leave']}."
                )
                result["leave_credits"] = leave_credits
            except Exception as e:
                logger.warning("Auto-leave-credit failed for %s: %s", arguments["emp_code"], e)
                result["leave_warning"] = f"Auto-leave-credit failed: {str(e)}"

            await _audit("add_employee", user, arguments["emp_code"], arguments)
            return result

        elif tool_name == "update_employee":
            updates = {k: v for k, v in arguments.items() if k != "emp_code" and v is not None}
            result = _parse(await emp_svc.update_employee(arguments["emp_code"], **updates))
            await _audit("update_employee", user, arguments["emp_code"], arguments)
            return result

        elif tool_name == "initiate_resignation":
            result = _parse(await emp_svc.initiate_resignation(
                emp_code=arguments["emp_code"],
                resignation_date=arguments["resignation_date"],
                reason=arguments["reason"],
            ))
            await _audit("initiate_resignation", user, arguments["emp_code"], arguments)
            return result

        elif tool_name == "assign_role":
            target_user = await user_repo.find_by_email(arguments["email"])
            if target_user is None:
                return {"error": f"User with email '{arguments['email']}' not found."}
            await user_repo.update_role(arguments["email"], UserRole(arguments["role"]))
            await _audit("assign_role", user, arguments["email"], arguments)
            return {"message": f"Role updated to '{arguments['role']}' for {arguments['email']}."}

        # ── HR Policy tools ─────────────────────────────
        elif tool_name == "set_hr_policy":
            result = await hr_svc.set_policy(
                state=arguments["state"],
                is_metro=arguments.get("is_metro", True),
                tax_regime=arguments.get("tax_regime", "new"),
                # Salary breakup
                basic_pct=arguments.get("basic_pct"),
                hra_pct=arguments.get("hra_pct"),
                pf_employee_pct=arguments.get("pf_employee_pct"),
                pf_employer_pct=arguments.get("pf_employer_pct"),
                esi_employee_pct=arguments.get("esi_employee_pct"),
                esi_employer_pct=arguments.get("esi_employer_pct"),
                esi_threshold=arguments.get("esi_threshold"),
                gratuity_pct=arguments.get("gratuity_pct"),
                professional_tax=arguments.get("professional_tax"),
                medical_allowance=arguments.get("medical_allowance"),
                conveyance_allowance=arguments.get("conveyance_allowance"),
                # Tax config
                standard_deduction=arguments.get("standard_deduction"),
                cess_pct=arguments.get("cess_pct"),
                tax_slabs=arguments.get("tax_slabs"),
                old_regime_tax_slabs=arguments.get("old_regime_tax_slabs"),
                old_regime_standard_deduction=arguments.get("old_regime_standard_deduction"),
                # Leave policy
                casual_leave=arguments.get("casual_leave"),
                sick_leave=arguments.get("sick_leave"),
                earned_leave=arguments.get("earned_leave"),
                maternity_leave=arguments.get("maternity_leave"),
                paternity_leave=arguments.get("paternity_leave"),
                compensatory_off=arguments.get("compensatory_off"),
                public_holidays=arguments.get("public_holidays"),
                # State reference data
                state_professional_tax=arguments.get("state_professional_tax"),
                state_leave_overrides=arguments.get("state_leave_overrides"),
                # Audit
                change_reason=arguments.get("change_reason"),
                created_by=user.email,
            )
            await _audit("set_hr_policy", user, "hr_policy", arguments)
            return result

        elif tool_name == "get_hr_policy":
            policy = await hr_svc.get_active_policy()
            b = policy.salary_breakup
            lp = policy.leave_policy
            return {
                "version": policy.version,
                "state": policy.state.title(),
                "is_metro": policy.is_metro,
                "salary_breakup": {
                    "basic_pct": b.basic_pct,
                    "hra_pct": b.hra_pct,
                    "pf_employee_pct": b.pf_employee_pct,
                    "pf_employer_pct": b.pf_employer_pct,
                    "esi_employee_pct": b.esi_employee_pct,
                    "esi_employer_pct": b.esi_employer_pct,
                    "esi_threshold": b.esi_threshold,
                    "gratuity_pct": b.gratuity_pct,
                    "professional_tax": b.professional_tax,
                    "medical_allowance": b.medical_allowance,
                    "conveyance_allowance": b.conveyance_allowance,
                },
                "leave_policy": {
                    "casual_leave": lp.casual_leave,
                    "sick_leave": lp.sick_leave,
                    "earned_leave": lp.earned_leave,
                    "maternity_leave": lp.maternity_leave,
                    "paternity_leave": lp.paternity_leave,
                    "compensatory_off": lp.compensatory_off,
                    "public_holidays": lp.public_holidays,
                },
                "tax_config": {
                    "company_default_regime": policy.tax_regime,
                    "new_regime": {
                        "standard_deduction": policy.standard_deduction,
                        "tax_slabs": [{"min": s.min_income, "max": s.max_income, "rate": s.rate_pct} for s in policy.tax_slabs],
                    },
                    "old_regime": {
                        "standard_deduction": policy.old_regime_standard_deduction,
                        "tax_slabs": [{"min": s.min_income, "max": s.max_income, "rate": s.rate_pct} for s in policy.old_regime_tax_slabs],
                    },
                    "cess_pct": policy.cess_pct,
                },
                "state_professional_tax": policy.state_professional_tax,
                "state_leave_overrides": policy.state_leave_overrides,
            }

        elif tool_name == "get_hr_policy_history":
            limit = arguments.get("limit", 10)
            history = await hr_svc.get_policy_history(limit=limit)
            if not history:
                return {"message": "No policy history found. Set an HR policy first."}
            return {"policy_history": history, "total_versions": len(history)}

        elif tool_name == "compute_salary_breakup":
            result = await hr_svc.compute_salary_breakup(
                arguments["annual_ctc"],
                tax_regime=arguments.get("tax_regime"),
            )
            return result

        # ── Employee Tax Regime ───────────────────────
        elif tool_name == "set_employee_tax_regime":
            from app.repositories.employee_repo import EmployeeRepository
            from datetime import datetime as _dt
            emp_repo = EmployeeRepository()
            emp = await emp_repo.find_by_emp_code(arguments["emp_code"].upper())
            if not emp:
                return {"error": f"Employee {arguments['emp_code']} not found."}
            regime = arguments["tax_regime"].lower()
            if regime not in ("new", "old"):
                return {"error": "tax_regime must be 'new' or 'old'."}
            emp.tax_regime = regime
            emp.updated_at = _dt.utcnow()
            await emp_repo.update(emp)
            await _audit("set_employee_tax_regime", user, arguments["emp_code"], arguments)
            return {
                "success": True,
                "message": f"Tax regime for {emp.name} ({emp.emp_code}) set to '{regime}'. TDS will be calculated using {regime} regime slabs.",
            }

        # ── Update Request tools ─────────────────────────
        elif tool_name == "submit_update_request":
            result = await update_req_svc.submit_request(
                emp_code=arguments["emp_code"],
                fields=arguments["fields"],
                reason=arguments["reason"],
            )
            if result.get("success"):
                await _audit("submit_update_request", user, arguments["emp_code"], arguments)
            return result

        elif tool_name == "list_update_requests":
            results = await update_req_svc.list_requests(
                status=arguments.get("status"),
                emp_code=arguments.get("emp_code"),
            )
            if not results:
                return {"message": "No update requests found."}
            return {"update_requests": results, "total": len(results)}

        elif tool_name == "review_update_request":
            result = await update_req_svc.review_request(
                request_id=arguments["request_id"],
                action=arguments["action"],
                reviewer_email=user.email,
                comment=arguments.get("comment"),
            )
            if result.get("success"):
                await _audit("review_update_request", user, arguments.get("request_id", ""), arguments)
            return result

        # ── Appraisal tools ──────────────────────────────
        elif tool_name == "initiate_appraisal":
            result = await appraisal_svc.initiate_appraisal(
                emp_code=arguments["emp_code"],
                appraisal_cycle=arguments["appraisal_cycle"],
                initiated_by=user.email,
                manager_feedback=arguments.get("manager_feedback"),
            )
            if result.get("success"):
                await _audit("initiate_appraisal", user, arguments["emp_code"], arguments)
            return result

        elif tool_name == "complete_appraisal":
            result = await appraisal_svc.complete_appraisal(
                emp_code=arguments["emp_code"],
                appraisal_cycle=arguments["appraisal_cycle"],
                rating=arguments["rating"],
                hike_pct=arguments.get("hike_pct"),
                new_salary=arguments.get("new_salary"),
                new_designation=arguments.get("new_designation"),
                new_department=arguments.get("new_department"),
                manager_feedback=arguments.get("manager_feedback"),
                hr_comments=arguments.get("hr_comments"),
                effective_date=arguments.get("effective_date"),
                completed_by=user.email,
            )
            if result.get("success"):
                await _audit("complete_appraisal", user, arguments["emp_code"], arguments)
            return result

        elif tool_name == "get_appraisal_history":
            results = await appraisal_svc.get_appraisal_history(
                emp_code=arguments.get("emp_code"),
                limit=arguments.get("limit", 20),
            )
            if not results:
                return {"message": "No appraisal records found."}
            return {"appraisals": results, "total": len(results)}

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as exc:
        logger.exception("Tool execution error for %s", tool_name)
        return {"error": str(exc)}


def is_write_tool(tool_name: str) -> bool:
    """Return True if the tool mutates data (used for cache invalidation)."""
    return tool_name in WRITE_TOOLS
