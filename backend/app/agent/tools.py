"""Tool definitions for the OpenAI Chat Completions function-calling API."""

from __future__ import annotations

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_employee",
            "description": "Look up an employee by emp_code or name. Returns employee profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Employee code (e.g. EMP001) or partial name to search.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_employees_by_department",
            "description": "List all employees in a given department.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "Department name, e.g. Engineering, HR, Finance.",
                    }
                },
                "required": ["department"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_leave_records",
            "description": "Get leave records for an employee by emp_code. Optionally filter by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string", "description": "Employee code."},
                    "status": {
                        "type": "string",
                        "description": "Filter by leave status: pending, approved, rejected. Optional.",
                    },
                },
                "required": ["emp_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_leave",
            "description": "Apply for leave on behalf of an employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string"},
                    "leave_type": {"type": "string", "description": "casual, sick, or earned."},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD."},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD."},
                    "reason": {"type": "string", "description": "Reason for leave."},
                },
                "required": ["emp_code", "leave_type", "start_date", "end_date", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "approve_or_reject_leave",
            "description": "Approve or reject a pending leave request. Only managers and HR can use this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string", "description": "Employee code whose leave to action."},
                    "start_date": {"type": "string", "description": "Start date of the leave YYYY-MM-DD."},
                    "action": {"type": "string", "description": "'approve' or 'reject'."},
                },
                "required": ["emp_code", "start_date", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_attendance",
            "description": "Get attendance records for an employee, optionally for a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string"},
                    "date": {"type": "string", "description": "Date YYYY-MM-DD. Optional."},
                },
                "required": ["emp_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_payroll",
            "description": "Get payroll / salary slip details for an employee. If month is omitted, returns ALL payroll records for that employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string", "description": "Employee code, e.g. EMP001."},
                    "month": {"type": "string", "description": "Month YYYY-MM, e.g. 2026-01. Optional — omit to get all months."},
                },
                "required": ["emp_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_all_employees",
            "description": "List all active employees with pagination and optional search. HR admin, manager, and super admin only. Returns a page of employees and pagination metadata (total, page count). Use search to filter by name, emp_code, department, or designation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "Page number (1-based). Default 1.",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of employees per page. Default 10, max 25.",
                    },
                    "search": {
                        "type": "string",
                        "description": "Optional search term to filter by name, emp_code, department, or designation.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_stats",
            "description": "Get overall company HR statistics: total employees, department breakdown, average salary.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_employee",
            "description": "Add a new employee to the system. Only HR admin and super admin can use this. Automatically generates salary breakup (basic, HRA, PF, ESI, TDS, etc.) from CTC using active HR policy, creates a payroll record for the current month, and credits annual leaves. Supports extended fields: contact details, address, emergency contact, ID proofs, and bank details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string", "description": "Unique employee code, e.g. EMP006."},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "department": {"type": "string"},
                    "designation": {"type": "string"},
                    "date_of_joining": {"type": "string", "description": "YYYY-MM-DD."},
                    "salary": {"type": "number", "description": "Annual CTC in INR."},
                    "manager_name": {"type": "string", "description": "Optional manager name."},
                    "phone": {"type": "string", "description": "Mobile / phone number. Optional."},
                    "personal_email": {"type": "string", "description": "Personal email address. Optional."},
                    "date_of_birth": {"type": "string", "description": "Date of birth YYYY-MM-DD. Optional."},
                    "gender": {"type": "string", "description": "male, female, or other. Optional."},
                    "blood_group": {"type": "string", "description": "Blood group, e.g. A+, B-, O+. Optional."},
                    "marital_status": {"type": "string", "description": "single, married, divorced, widowed. Optional."},
                    "nationality": {"type": "string", "description": "Default Indian. Optional."},
                    "current_address": {
                        "type": "object",
                        "description": "Current address: line1, line2, city, state, pincode, country.",
                        "properties": {
                            "line1": {"type": "string"},
                            "line2": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                            "pincode": {"type": "string"},
                            "country": {"type": "string"}
                        }
                    },
                    "permanent_address": {
                        "type": "object",
                        "description": "Permanent address: line1, line2, city, state, pincode, country.",
                        "properties": {
                            "line1": {"type": "string"},
                            "line2": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                            "pincode": {"type": "string"},
                            "country": {"type": "string"}
                        }
                    },
                    "emergency_contact": {
                        "type": "object",
                        "description": "Emergency contact: name, relationship, phone.",
                        "properties": {
                            "name": {"type": "string"},
                            "relationship": {"type": "string"},
                            "phone": {"type": "string"}
                        }
                    },
                    "pan_number": {"type": "string", "description": "PAN card number. Optional."},
                    "aadhaar_number": {"type": "string", "description": "Aadhaar number. Optional."},
                    "bank_account": {"type": "string", "description": "Bank account number. Optional."},
                    "bank_name": {"type": "string", "description": "Bank name. Optional."},
                    "ifsc_code": {"type": "string", "description": "IFSC code. Optional."}
                },
                "required": ["emp_code", "name", "email", "department", "designation", "date_of_joining", "salary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_employee",
            "description": "Update an existing employee's details. Only HR admin and super admin.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string"},
                    "department": {"type": "string", "description": "New department. Optional."},
                    "designation": {"type": "string", "description": "New designation. Optional."},
                    "salary": {"type": "number", "description": "New salary. Optional."},
                    "manager_name": {"type": "string", "description": "New manager. Optional."},
                },
                "required": ["emp_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "initiate_resignation",
            "description": "Initiate resignation process for an employee. Only HR admin and super admin.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string"},
                    "resignation_date": {"type": "string", "description": "YYYY-MM-DD."},
                    "reason": {"type": "string"},
                },
                "required": ["emp_code", "resignation_date", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "assign_role",
            "description": "Assign or change a user's role. Only super admin can use this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "User email to update."},
                    "role": {
                        "type": "string",
                        "description": "New role: super_admin, hr_admin, manager, or employee.",
                    },
                },
                "required": ["email", "role"],
            },
        },
    },
    # ── HR Policy tools ──────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "set_hr_policy",
            "description": (
                "Configure the active HR policy. ALL fields are optional except state. "
                "Covers: salary breakup (basic%, HRA%, PF%, ESI%, gratuity%, allowances), "
                "leave credits (CL, SL, EL, maternity, paternity, comp-off, holidays), "
                "tax config (regime, standard deduction, cess%, tax slabs), "
                "state reference data (professional tax per state, leave overrides per state). "
                "All values are stored in DB — nothing is hardcoded. "
                "Only HR admin and super admin can use this. Every change is versioned and audited."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "description": "Indian state for labour law compliance, e.g. maharashtra, karnataka, delhi, tamil_nadu.",
                    },
                    "is_metro": {"type": "boolean", "description": "Whether the office is in a metro city (affects HRA). Default true."},
                    "tax_regime": {"type": "string", "description": "'new' or 'old'. Default 'new'."},
                    "basic_pct": {"type": "number", "description": "Basic salary % of CTC. Default 40."},
                    "hra_pct": {"type": "number", "description": "HRA % of CTC. Default 20."},
                    "pf_employee_pct": {"type": "number", "description": "Employee PF contribution % of Basic. Default 12."},
                    "pf_employer_pct": {"type": "number", "description": "Employer PF contribution % of Basic. Default 12."},
                    "esi_employee_pct": {"type": "number", "description": "Employee ESI %. Default 0.75."},
                    "esi_employer_pct": {"type": "number", "description": "Employer ESI %. Default 3.25."},
                    "esi_threshold": {"type": "number", "description": "Monthly gross threshold for ESI applicability. Default 21000."},
                    "gratuity_pct": {"type": "number", "description": "Gratuity % of Basic. Default 4.81."},
                    "professional_tax": {"type": "number", "description": "Monthly professional tax (₹). Auto-set by state but can be overridden."},
                    "medical_allowance": {"type": "number", "description": "Monthly medical allowance (₹). Default 1250."},
                    "conveyance_allowance": {"type": "number", "description": "Monthly conveyance allowance (₹). Default 1600."},
                    "standard_deduction": {"type": "number", "description": "Annual standard deduction for tax (₹). Default 75000."},
                    "cess_pct": {"type": "number", "description": "Health & Education Cess % on tax. Default 4."},
                    "tax_slabs": {
                        "type": "array",
                        "description": "NEW REGIME income tax slabs. Array of objects with min_income, max_income (-1 for unlimited), rate_pct. Only provide when changing new regime slabs.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "min_income": {"type": "number"},
                                "max_income": {"type": "number", "description": "Use -1 for unlimited (last slab)."},
                                "rate_pct": {"type": "number"},
                            },
                            "required": ["min_income", "max_income", "rate_pct"],
                        },
                    },
                    "old_regime_tax_slabs": {
                        "type": "array",
                        "description": "OLD REGIME income tax slabs. Array of objects with min_income, max_income (-1 for unlimited), rate_pct. Only provide when changing old regime slabs.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "min_income": {"type": "number"},
                                "max_income": {"type": "number", "description": "Use -1 for unlimited (last slab)."},
                                "rate_pct": {"type": "number"},
                            },
                            "required": ["min_income", "max_income", "rate_pct"],
                        },
                    },
                    "old_regime_standard_deduction": {"type": "number", "description": "Annual standard deduction for OLD regime (₹). Default 50000."},
                    "state_professional_tax": {
                        "type": "object",
                        "description": "Map of state name to monthly professional tax (\u20b9). e.g. {\"maharashtra\": 200, \"delhi\": 0}. Only provide when updating state PT values.",
                    },
                    "state_leave_overrides": {
                        "type": "object",
                        "description": "Map of state name to leave overrides. e.g. {\"kerala\": {\"earned_leave\": 18}}. Only provide when updating state leave rules.",
                    },
                    "casual_leave": {"type": "integer", "description": "Annual casual leaves."},
                    "sick_leave": {"type": "integer", "description": "Annual sick leaves."},
                    "earned_leave": {"type": "integer", "description": "Annual earned/privilege leaves."},
                    "maternity_leave": {"type": "integer", "description": "Maternity leave days."},
                    "paternity_leave": {"type": "integer", "description": "Paternity leave days."},
                    "compensatory_off": {"type": "integer", "description": "Compensatory off days."},
                    "public_holidays": {"type": "integer", "description": "Annual public holidays."},
                    "change_reason": {"type": "string", "description": "Reason for this policy change (for audit trail). Always provide this."},
                },
                "required": ["state"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hr_policy",
            "description": (
                "View the current active HR policy — shows EVERYTHING stored in DB: "
                "salary breakup, leave credits, tax slabs, state professional tax map, "
                "state leave overrides, standard deduction, cess%, version. Nothing is hardcoded."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hr_policy_history",
            "description": (
                "View the change history of the HR policy — who changed what and when. "
                "Shows all past policy versions with diffs. Useful for auditing policy changes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max number of history entries to return. Default 10."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_salary_breakup",
            "description": (
                "Compute detailed salary breakup from annual CTC using the active HR policy. "
                "Shows monthly & yearly: basic, HRA, PF, ESI, professional tax, TDS, gratuity, "
                "special allowance, gross, deductions, and net take-home pay. "
                "Optionally specify tax_regime ('new' or 'old') to see TDS under a specific regime."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "annual_ctc": {"type": "number", "description": "Annual CTC in INR, e.g. 1200000."},
                    "tax_regime": {"type": "string", "description": "'new' or 'old'. Optional — defaults to employee's chosen regime or company default."},
                },
                "required": ["annual_ctc"],
            },
        },
    },
    # ── Employee Tax Regime Choice ──────────────────
    {
        "type": "function",
        "function": {
            "name": "set_employee_tax_regime",
            "description": (
                "Set an employee's chosen income tax regime ('new' or 'old'). "
                "This determines which tax slabs are used for TDS calculation in their salary/payroll. "
                "Employees can choose based on which regime gives them lower tax liability."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string", "description": "Employee code."},
                    "tax_regime": {"type": "string", "description": "'new' or 'old'."},
                },
                "required": ["emp_code", "tax_regime"],
            },
        },
    },
    # ── Employee Update Request tools ────────────────────
    {
        "type": "function",
        "function": {
            "name": "submit_update_request",
            "description": (
                "Employee submits a request to update their own profile fields. "
                "Allowed fields: name, email, department, designation, manager_name. "
                "The request goes to HR for approval. Employee must provide the fields they want to change and a reason."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string", "description": "Employee code of the requester."},
                    "fields": {
                        "type": "object",
                        "description": "Fields to update. Keys are field names, values are new desired values. e.g. {\"designation\": \"Senior Engineer\", \"department\": \"Product\"}",
                    },
                    "reason": {"type": "string", "description": "Reason for the change request."},
                },
                "required": ["emp_code", "fields", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_update_requests",
            "description": (
                "List employee profile update requests. HR/managers see all; employees see only their own. "
                "Can filter by status (pending, approved, rejected) and emp_code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status: pending, approved, rejected. Optional."},
                    "emp_code": {"type": "string", "description": "Filter by employee code. Optional."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "review_update_request",
            "description": (
                "Approve or reject an employee's profile update request. Only HR admin and super admin can do this. "
                "On approval, changes are automatically applied to the employee record."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string", "description": "The update request ID to review."},
                    "action": {"type": "string", "description": "'approve' or 'reject'."},
                    "comment": {"type": "string", "description": "Optional review comment."},
                },
                "required": ["request_id", "action"],
            },
        },
    },
    # ── Appraisal tools ──────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "initiate_appraisal",
            "description": (
                "Start an appraisal for an employee in a given cycle (e.g. 'FY2025-26', 'H1-2025'). "
                "Only HR admin, manager, and super admin can initiate. "
                "Captures current salary and designation as baseline."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string", "description": "Employee code to appraise."},
                    "appraisal_cycle": {"type": "string", "description": "Appraisal cycle label, e.g. 'FY2025-26', 'H1-2025'."},
                    "manager_feedback": {"type": "string", "description": "Optional initial manager feedback."},
                },
                "required": ["emp_code", "appraisal_cycle"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_appraisal",
            "description": (
                "Finalize an appraisal with rating and optional salary revision. "
                "Rating is 1-5 scale. Provide either hike_pct or new_salary for salary revision. "
                "On completion: employee salary, designation, department are auto-updated and new payroll is generated."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string", "description": "Employee code."},
                    "appraisal_cycle": {"type": "string", "description": "Cycle to finalize."},
                    "rating": {"type": "number", "description": "Performance rating 1.0 to 5.0."},
                    "hike_pct": {"type": "number", "description": "Percentage salary hike, e.g. 15 for 15%. Optional if new_salary given."},
                    "new_salary": {"type": "number", "description": "New annual CTC in INR. Optional if hike_pct given."},
                    "new_designation": {"type": "string", "description": "New designation after appraisal. Optional."},
                    "new_department": {"type": "string", "description": "New department after appraisal. Optional."},
                    "manager_feedback": {"type": "string", "description": "Manager feedback. Optional."},
                    "hr_comments": {"type": "string", "description": "HR comments. Optional."},
                    "effective_date": {"type": "string", "description": "Effective date YYYY-MM-DD. Defaults to today."},
                },
                "required": ["emp_code", "appraisal_cycle", "rating"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_appraisal_history",
            "description": (
                "View appraisal history. Shows past appraisals with ratings, salary changes, feedback. "
                "Can filter by emp_code. Returns most recent first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "emp_code": {"type": "string", "description": "Filter by employee code. Optional — omit to view all."},
                    "limit": {"type": "integer", "description": "Max results. Default 20."},
                },
            },
        },
    },
]
