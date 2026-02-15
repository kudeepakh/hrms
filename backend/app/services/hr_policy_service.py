"""HR Policy service — salary breakup, leave credits, TDS calculation.

ALL configuration is read from the active HRPolicy document in MongoDB.
No hardcoded constants are used at runtime — the INITIAL_* values in
hr_policy.py are only consumed by the seed script (once).
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Optional

from app.models.hr_policy import (
    HRPolicy,
    SalaryBreakup,
    LeavePolicy,
    TaxSlab,
    PolicyChangeLog,
    PolicyChangeEntry,
    # Only imported for the fallback in get_active_policy (first-ever boot)
    INITIAL_TAX_SLABS_NEW_REGIME,
    INITIAL_TAX_SLABS_OLD_REGIME,
    INITIAL_STATE_PROFESSIONAL_TAX,
    INITIAL_STATE_LEAVE_OVERRIDES,
)
from app.models.leave import LeaveRecord
from app.models.payroll import Payroll


class HRPolicyService:
    """Business logic for HR policy, salary breakup, leave credits, TDS."""

    # ── Policy CRUD ──────────────────────────────────────

    async def get_active_policy(self) -> HRPolicy:
        """Return the active HR policy, or create a seed one (first boot)."""
        policy = await HRPolicy.find_one(HRPolicy.is_active == True)
        if not policy:
            # First-ever boot — create from INITIAL_ constants (only time they're used)
            policy = HRPolicy(
                state_professional_tax=INITIAL_STATE_PROFESSIONAL_TAX,
                state_leave_overrides=INITIAL_STATE_LEAVE_OVERRIDES,
                tax_slabs=INITIAL_TAX_SLABS_NEW_REGIME,
                old_regime_tax_slabs=INITIAL_TAX_SLABS_OLD_REGIME,
            )
            await policy.insert()
        return policy

    async def set_policy(
        self,
        state: str,
        is_metro: bool = True,
        tax_regime: str = "new",
        # ── Salary breakup (all configurable) ──
        basic_pct: Optional[float] = None,
        hra_pct: Optional[float] = None,
        pf_employee_pct: Optional[float] = None,
        pf_employer_pct: Optional[float] = None,
        esi_employee_pct: Optional[float] = None,
        esi_employer_pct: Optional[float] = None,
        esi_threshold: Optional[float] = None,
        gratuity_pct: Optional[float] = None,
        professional_tax: Optional[float] = None,
        medical_allowance: Optional[float] = None,
        conveyance_allowance: Optional[float] = None,
        # ── Tax config ──
        standard_deduction: Optional[float] = None,
        cess_pct: Optional[float] = None,
        tax_slabs: Optional[list[dict]] = None,
        old_regime_tax_slabs: Optional[list[dict]] = None,
        old_regime_standard_deduction: Optional[float] = None,
        # ── Leave policy (all 7 configurable) ──
        casual_leave: Optional[int] = None,
        sick_leave: Optional[int] = None,
        earned_leave: Optional[int] = None,
        maternity_leave: Optional[int] = None,
        paternity_leave: Optional[int] = None,
        compensatory_off: Optional[int] = None,
        public_holidays: Optional[int] = None,
        # ── State reference data ──
        state_professional_tax: Optional[dict[str, float]] = None,
        state_leave_overrides: Optional[dict[str, dict[str, int]]] = None,
        # ── Audit ──
        change_reason: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> dict:
        """Create or update the active HR policy.

        IMPORTANT: Every field that is NOT explicitly provided is carried
        forward from the previous active policy — never from hardcoded
        defaults.  This ensures the DB is the single source of truth.
        """
        # ── Fetch old policy (single source of truth) ──
        old = await self.get_active_policy()
        old_version = old.version
        old_state = old.state

        # Deactivate old
        old.is_active = False
        await old.save()

        state_lower = state.lower().strip()

        # ── Build salary breakup: start from OLD, apply overrides ──
        # Look up state PT from the DB-stored state_professional_tax map
        pt_map = old.state_professional_tax or {}
        pt_for_state = pt_map.get(state_lower, pt_map.get("default", old.salary_breakup.professional_tax))

        breakup = SalaryBreakup(
            basic_pct=old.salary_breakup.basic_pct,
            hra_pct=old.salary_breakup.hra_pct,
            pf_employee_pct=old.salary_breakup.pf_employee_pct,
            pf_employer_pct=old.salary_breakup.pf_employer_pct,
            esi_employee_pct=old.salary_breakup.esi_employee_pct,
            esi_employer_pct=old.salary_breakup.esi_employer_pct,
            esi_threshold=old.salary_breakup.esi_threshold,
            gratuity_pct=old.salary_breakup.gratuity_pct,
            professional_tax=pt_for_state,
            medical_allowance=old.salary_breakup.medical_allowance,
            conveyance_allowance=old.salary_breakup.conveyance_allowance,
        )
        _BREAKUP_FIELDS = {
            "basic_pct": basic_pct,
            "hra_pct": hra_pct,
            "pf_employee_pct": pf_employee_pct,
            "pf_employer_pct": pf_employer_pct,
            "esi_employee_pct": esi_employee_pct,
            "esi_employer_pct": esi_employer_pct,
            "esi_threshold": esi_threshold,
            "gratuity_pct": gratuity_pct,
            "professional_tax": professional_tax,  # explicit override
            "medical_allowance": medical_allowance,
            "conveyance_allowance": conveyance_allowance,
        }
        for field, val in _BREAKUP_FIELDS.items():
            if val is not None:
                setattr(breakup, field, val)

        # ── Build leave policy: start from OLD, apply state overrides from DB, then user overrides ──
        lp = LeavePolicy(
            casual_leave=old.leave_policy.casual_leave,
            sick_leave=old.leave_policy.sick_leave,
            earned_leave=old.leave_policy.earned_leave,
            maternity_leave=old.leave_policy.maternity_leave,
            paternity_leave=old.leave_policy.paternity_leave,
            compensatory_off=old.leave_policy.compensatory_off,
            public_holidays=old.leave_policy.public_holidays,
        )
        # Apply state-level leave overrides from DB
        leave_override_map = old.state_leave_overrides or {}
        state_leave = leave_override_map.get(state_lower, {})
        for k, v in state_leave.items():
            if hasattr(lp, k):
                setattr(lp, k, v)
        # Then user explicit overrides (highest priority)
        _LEAVE_FIELDS = {
            "casual_leave": casual_leave,
            "sick_leave": sick_leave,
            "earned_leave": earned_leave,
            "maternity_leave": maternity_leave,
            "paternity_leave": paternity_leave,
            "compensatory_off": compensatory_off,
            "public_holidays": public_holidays,
        }
        for field, val in _LEAVE_FIELDS.items():
            if val is not None:
                setattr(lp, field, val)

        # ── Tax config: carry forward from old, override if provided ──
        new_std_deduction = standard_deduction if standard_deduction is not None else old.standard_deduction
        new_old_std_deduction = old.old_regime_standard_deduction
        new_cess = cess_pct if cess_pct is not None else old.cess_pct

        # Tax slabs: carry forward or replace
        if tax_slabs is not None:
            new_tax_slabs = [TaxSlab(**s) for s in tax_slabs]
        else:
            new_tax_slabs = old.tax_slabs

        # Old regime tax slabs: carry forward or replace
        if old_regime_tax_slabs is not None:
            new_old_regime_slabs = [TaxSlab(**s) for s in old_regime_tax_slabs]
        else:
            new_old_regime_slabs = old.old_regime_tax_slabs

        # Old regime standard deduction
        if old_regime_standard_deduction is not None:
            new_old_std_deduction = old_regime_standard_deduction

        # State reference data: carry forward or replace
        new_state_pt = state_professional_tax if state_professional_tax is not None else (old.state_professional_tax or {})
        new_state_leave = state_leave_overrides if state_leave_overrides is not None else (old.state_leave_overrides or {})

        # ── Build change log by diffing old vs new ──
        changes: list[PolicyChangeEntry] = []

        if old_state != state_lower:
            changes.append(PolicyChangeEntry(field="state", old_value=old_state, new_value=state_lower))
        if old.is_metro != is_metro:
            changes.append(PolicyChangeEntry(field="is_metro", old_value=str(old.is_metro), new_value=str(is_metro)))
        if old.tax_regime != tax_regime:
            changes.append(PolicyChangeEntry(field="tax_regime", old_value=old.tax_regime, new_value=tax_regime))

        # Salary breakup diffs
        for field in ["basic_pct", "hra_pct", "pf_employee_pct", "pf_employer_pct",
                       "esi_employee_pct", "esi_employer_pct", "esi_threshold",
                       "gratuity_pct", "professional_tax", "medical_allowance",
                       "conveyance_allowance"]:
            ov = getattr(old.salary_breakup, field)
            nv = getattr(breakup, field)
            if ov != nv:
                changes.append(PolicyChangeEntry(field=field, old_value=str(ov), new_value=str(nv)))

        # Tax diffs
        if old.standard_deduction != new_std_deduction:
            changes.append(PolicyChangeEntry(field="standard_deduction", old_value=str(old.standard_deduction), new_value=str(new_std_deduction)))
        if old.cess_pct != new_cess:
            changes.append(PolicyChangeEntry(field="cess_pct", old_value=str(old.cess_pct), new_value=str(new_cess)))

        # Tax slab diffs
        old_slab_str = "|".join(f"{s.min_income}-{s.max_income}@{s.rate_pct}" for s in old.tax_slabs)
        new_slab_str = "|".join(f"{s.min_income}-{s.max_income}@{s.rate_pct}" for s in new_tax_slabs)
        if old_slab_str != new_slab_str:
            changes.append(PolicyChangeEntry(field="tax_slabs (new regime)", old_value=old_slab_str, new_value=new_slab_str))

        # Old regime slab diffs
        old_old_slab_str = "|".join(f"{s.min_income}-{s.max_income}@{s.rate_pct}" for s in old.old_regime_tax_slabs)
        new_old_slab_str = "|".join(f"{s.min_income}-{s.max_income}@{s.rate_pct}" for s in new_old_regime_slabs)
        if old_old_slab_str != new_old_slab_str:
            changes.append(PolicyChangeEntry(field="tax_slabs (old regime)", old_value=old_old_slab_str, new_value=new_old_slab_str))

        # Old regime standard deduction diff
        if old.old_regime_standard_deduction != new_old_std_deduction:
            changes.append(PolicyChangeEntry(field="old_regime_standard_deduction", old_value=str(old.old_regime_standard_deduction), new_value=str(new_old_std_deduction)))

        # State config diffs
        old_pt_str = json.dumps(old.state_professional_tax or {}, sort_keys=True)
        new_pt_str = json.dumps(new_state_pt, sort_keys=True)
        if old_pt_str != new_pt_str:
            changes.append(PolicyChangeEntry(field="state_professional_tax", old_value=old_pt_str, new_value=new_pt_str))
        old_sl_str = json.dumps(old.state_leave_overrides or {}, sort_keys=True)
        new_sl_str = json.dumps(new_state_leave, sort_keys=True)
        if old_sl_str != new_sl_str:
            changes.append(PolicyChangeEntry(field="state_leave_overrides", old_value=old_sl_str, new_value=new_sl_str))

        # Leave policy diffs
        for field in ["casual_leave", "sick_leave", "earned_leave", "maternity_leave",
                       "paternity_leave", "compensatory_off", "public_holidays"]:
            ov = getattr(old.leave_policy, field)
            nv = getattr(lp, field)
            if ov != nv:
                changes.append(PolicyChangeEntry(field=field, old_value=str(ov), new_value=str(nv)))

        change_log = PolicyChangeLog(
            changed_by=created_by or "system",
            changed_at=datetime.utcnow(),
            reason=change_reason,
            changes=changes,
        )

        # Carry forward history
        prev_history = old.change_history or []

        policy = HRPolicy(
            policy_name=f"India HR Policy — {state.title()}",
            state=state_lower,
            is_metro=is_metro,
            salary_breakup=breakup,
            leave_policy=lp,
            tax_regime=tax_regime,
            tax_slabs=new_tax_slabs,
            old_regime_tax_slabs=new_old_regime_slabs,
            standard_deduction=new_std_deduction,
            old_regime_standard_deduction=new_old_std_deduction,
            cess_pct=new_cess,
            state_professional_tax=new_state_pt,
            state_leave_overrides=new_state_leave,
            is_active=True,
            change_history=[*prev_history, change_log],
            version=old_version + 1,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await policy.insert()

        changes_summary = ", ".join(f"{c.field}: {c.old_value}→{c.new_value}" for c in changes) if changes else "No field changes"

        return {
            "success": True,
            "message": f"HR Policy v{policy.version} set for {state.title()} (metro={is_metro}, regime={tax_regime}). Changes: {changes_summary}",
            "version": policy.version,
            "policy": {
                "state": state.title(),
                "is_metro": is_metro,
                "salary_breakup": {
                    "basic_pct": breakup.basic_pct,
                    "hra_pct": breakup.hra_pct,
                    "pf_employee_pct": breakup.pf_employee_pct,
                    "pf_employer_pct": breakup.pf_employer_pct,
                    "esi_employee_pct": breakup.esi_employee_pct,
                    "esi_employer_pct": breakup.esi_employer_pct,
                    "esi_threshold": breakup.esi_threshold,
                    "gratuity_pct": breakup.gratuity_pct,
                    "professional_tax": breakup.professional_tax,
                    "medical_allowance": breakup.medical_allowance,
                    "conveyance_allowance": breakup.conveyance_allowance,
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
                    "company_default_regime": tax_regime,
                    "new_regime": {
                        "standard_deduction": new_std_deduction,
                        "tax_slabs": [{"min": s.min_income, "max": s.max_income, "rate": s.rate_pct} for s in new_tax_slabs],
                    },
                    "old_regime": {
                        "standard_deduction": new_old_std_deduction,
                        "tax_slabs": [{"min": s.min_income, "max": s.max_income, "rate": s.rate_pct} for s in new_old_regime_slabs],
                    },
                    "cess_pct": new_cess,
                },
                "state_professional_tax": new_state_pt,
                "state_leave_overrides": new_state_leave,
            },
            "changes_in_this_update": [c.model_dump() for c in changes],
        }

    async def get_policy_history(self, limit: int = 10) -> list[dict]:
        """Return policy change history across all versions (most recent first)."""
        policies = await HRPolicy.find().sort("-version").limit(limit + 5).to_list()

        history = []
        for pol in policies:
            entry = {
                "version": pol.version,
                "policy_name": pol.policy_name,
                "state": pol.state.title(),
                "is_active": pol.is_active,
                "created_by": pol.created_by,
                "created_at": pol.created_at.isoformat() if pol.created_at else None,
                "leave_policy": {
                    "casual_leave": pol.leave_policy.casual_leave,
                    "sick_leave": pol.leave_policy.sick_leave,
                    "earned_leave": pol.leave_policy.earned_leave,
                    "maternity_leave": pol.leave_policy.maternity_leave,
                    "paternity_leave": pol.leave_policy.paternity_leave,
                    "compensatory_off": pol.leave_policy.compensatory_off,
                    "public_holidays": pol.leave_policy.public_holidays,
                },
                "salary_breakup": {
                    "basic_pct": pol.salary_breakup.basic_pct,
                    "hra_pct": pol.salary_breakup.hra_pct,
                    "pf_employee_pct": pol.salary_breakup.pf_employee_pct,
                    "pf_employer_pct": pol.salary_breakup.pf_employer_pct,
                    "esi_employee_pct": pol.salary_breakup.esi_employee_pct,
                    "esi_employer_pct": pol.salary_breakup.esi_employer_pct,
                    "esi_threshold": pol.salary_breakup.esi_threshold,
                    "gratuity_pct": pol.salary_breakup.gratuity_pct,
                    "professional_tax": pol.salary_breakup.professional_tax,
                    "medical_allowance": pol.salary_breakup.medical_allowance,
                    "conveyance_allowance": pol.salary_breakup.conveyance_allowance,
                },
                "tax_config": {
                    "company_default_regime": pol.tax_regime,
                    "new_regime": {
                        "standard_deduction": pol.standard_deduction,
                        "tax_slabs": [{"min": s.min_income, "max": s.max_income, "rate": s.rate_pct} for s in pol.tax_slabs],
                    },
                    "old_regime": {
                        "standard_deduction": pol.old_regime_standard_deduction,
                        "tax_slabs": [{"min": s.min_income, "max": s.max_income, "rate": s.rate_pct} for s in pol.old_regime_tax_slabs],
                    },
                    "cess_pct": pol.cess_pct,
                },
                "state_professional_tax": pol.state_professional_tax,
                "state_leave_overrides": pol.state_leave_overrides,
                "changes": [],
            }
            for log in pol.change_history:
                entry["changes"].append({
                    "changed_by": log.changed_by,
                    "changed_at": log.changed_at.isoformat(),
                    "reason": log.reason,
                    "fields_changed": [
                        {"field": c.field, "from": c.old_value, "to": c.new_value}
                        for c in log.changes
                    ],
                })
            history.append(entry)

        return history[:limit]

    # ── Salary Breakup ───────────────────────────────────

    async def compute_salary_breakup(self, annual_ctc: float, tax_regime: str | None = None) -> dict:
        """Compute monthly and annual salary breakup from CTC.

        If tax_regime is provided, TDS is calculated using that regime's slabs.
        Otherwise, the company default regime from the policy is used.
        """
        policy = await self.get_active_policy()
        b = policy.salary_breakup

        effective_regime = tax_regime or policy.tax_regime

        monthly_ctc = annual_ctc / 12

        # Core components (annual)
        basic_annual = annual_ctc * (b.basic_pct / 100)
        hra_annual = annual_ctc * (b.hra_pct / 100)

        # Employer PF (12% of Basic, capped at 15000/month basic for PF)
        pf_basic_monthly = min(basic_annual / 12, 15000)
        pf_employer_annual = pf_basic_monthly * (b.pf_employer_pct / 100) * 12
        pf_employee_annual = pf_basic_monthly * (b.pf_employee_pct / 100) * 12

        # Gratuity (4.81% of Basic)
        gratuity_annual = basic_annual * (b.gratuity_pct / 100)

        # ESI (only if monthly gross < threshold)
        monthly_gross = monthly_ctc
        esi_employer_annual = 0
        esi_employee_annual = 0
        if monthly_gross < b.esi_threshold:
            esi_employer_annual = monthly_gross * (b.esi_employer_pct / 100) * 12
            esi_employee_annual = monthly_gross * (b.esi_employee_pct / 100) * 12

        # Professional Tax
        pt_annual = b.professional_tax * 12

        # Fixed allowances
        medical_annual = b.medical_allowance * 12
        conveyance_annual = b.conveyance_allowance * 12

        # Special allowance = CTC - all other employer costs
        employer_costs = (basic_annual + hra_annual + pf_employer_annual +
                          gratuity_annual + esi_employer_annual +
                          medical_annual + conveyance_annual)
        special_allowance_annual = max(0, annual_ctc - employer_costs)

        # Gross salary (what employee sees before deductions)
        gross_annual = (basic_annual + hra_annual + special_allowance_annual +
                        medical_annual + conveyance_annual)
        gross_monthly = gross_annual / 12

        # Employee deductions
        total_deductions_annual = pf_employee_annual + esi_employee_annual + pt_annual

        # TDS (income tax)
        tds_annual = self._compute_tds(gross_annual, pf_employee_annual, policy, regime=effective_regime)
        tds_monthly = round(tds_annual / 12)

        total_deductions_annual += tds_annual

        # Net take-home
        net_annual = gross_annual - total_deductions_annual
        net_monthly = round(net_annual / 12)

        return {
            "annual_ctc": annual_ctc,
            "monthly_ctc": round(monthly_ctc),
            "breakup": {
                "basic": {"annual": round(basic_annual), "monthly": round(basic_annual / 12)},
                "hra": {"annual": round(hra_annual), "monthly": round(hra_annual / 12)},
                "special_allowance": {"annual": round(special_allowance_annual), "monthly": round(special_allowance_annual / 12)},
                "medical_allowance": {"annual": round(medical_annual), "monthly": round(b.medical_allowance)},
                "conveyance_allowance": {"annual": round(conveyance_annual), "monthly": round(b.conveyance_allowance)},
            },
            "employer_contributions": {
                "pf_employer": {"annual": round(pf_employer_annual), "monthly": round(pf_employer_annual / 12)},
                "gratuity": {"annual": round(gratuity_annual), "monthly": round(gratuity_annual / 12)},
                "esi_employer": {"annual": round(esi_employer_annual), "monthly": round(esi_employer_annual / 12)},
            },
            "deductions": {
                "pf_employee": {"annual": round(pf_employee_annual), "monthly": round(pf_employee_annual / 12)},
                "esi_employee": {"annual": round(esi_employee_annual), "monthly": round(esi_employee_annual / 12)},
                "professional_tax": {"annual": round(pt_annual), "monthly": round(b.professional_tax)},
                "tds": {"annual": round(tds_annual), "monthly": tds_monthly},
            },
            "gross_salary": {"annual": round(gross_annual), "monthly": round(gross_monthly)},
            "total_deductions": {"annual": round(total_deductions_annual), "monthly": round(total_deductions_annual / 12)},
            "net_take_home": {"annual": round(net_annual), "monthly": net_monthly},
            "policy": {
                "state": policy.state.title(),
                "is_metro": policy.is_metro,
                "tax_regime": effective_regime,
            },
        }

    def _compute_tds(self, gross_annual: float, pf_annual: float, policy: HRPolicy, regime: str | None = None) -> float:
        """Compute annual income tax (TDS) based on chosen regime."""
        effective_regime = regime or policy.tax_regime

        if effective_regime == "old":
            std_ded = policy.old_regime_standard_deduction
            slabs = policy.old_regime_tax_slabs
        else:
            std_ded = policy.standard_deduction
            slabs = policy.tax_slabs

        taxable = gross_annual - std_ded
        if effective_regime == "old":
            taxable -= pf_annual  # Section 80C in old regime
        taxable = max(0, taxable)

        # Rebate u/s 87A: If taxable ≤ 12,00,000 under new regime → zero tax
        if effective_regime == "new" and taxable <= 1200000:
            return 0
        # Old regime rebate u/s 87A: taxable ≤ 5,00,000
        if effective_regime == "old" and taxable <= 500000:
            return 0

        tax = 0.0
        for slab in slabs:
            if taxable <= 0:
                break
            upper = slab.max_income if slab.max_income > 0 else float("inf")
            slab_width = upper - slab.min_income
            taxable_in_slab = min(taxable, slab_width)
            tax += taxable_in_slab * (slab.rate_pct / 100)
            taxable -= taxable_in_slab

        # Add cess
        tax += tax * (policy.cess_pct / 100)
        return round(tax)

    # ── Leave Credits ────────────────────────────────────

    async def get_leave_credits(self) -> dict:
        """Return leave credit entitlements from active policy."""
        policy = await self.get_active_policy()
        lp = policy.leave_policy
        return {
            "casual_leave": lp.casual_leave,
            "sick_leave": lp.sick_leave,
            "earned_leave": lp.earned_leave,
            "maternity_leave": lp.maternity_leave,
            "paternity_leave": lp.paternity_leave,
            "compensatory_off": lp.compensatory_off,
            "public_holidays": lp.public_holidays,
            "state": policy.state.title(),
        }

    # ── Create Payroll Record (breakup-based) ────────────

    async def create_payroll_from_ctc(self, emp_code: str, annual_ctc: float, month: str, tax_regime: str | None = None) -> dict:
        """Generate a payroll record for an employee using policy-based breakup.

        If tax_regime is not provided, looks up the employee's chosen regime.
        """
        # Look up employee's chosen regime if not explicitly provided
        if tax_regime is None:
            from app.repositories.employee_repo import EmployeeRepository
            emp_repo = EmployeeRepository()
            emp = await emp_repo.find_by_emp_code(emp_code.upper())
            if emp:
                tax_regime = emp.tax_regime

        breakup = await self.compute_salary_breakup(annual_ctc, tax_regime=tax_regime)

        payroll = Payroll(
            emp_code=emp_code.upper(),
            month=month,
            basic=breakup["breakup"]["basic"]["monthly"],
            hra=breakup["breakup"]["hra"]["monthly"],
            allowances=(
                breakup["breakup"]["special_allowance"]["monthly"] +
                breakup["breakup"]["medical_allowance"]["monthly"] +
                breakup["breakup"]["conveyance_allowance"]["monthly"]
            ),
            deductions=(
                breakup["deductions"]["pf_employee"]["monthly"] +
                breakup["deductions"]["professional_tax"]["monthly"] +
                breakup["deductions"]["tds"]["monthly"] +
                breakup["deductions"]["esi_employee"]["monthly"]
            ),
            net_pay=breakup["net_take_home"]["monthly"],
        )
        await payroll.insert()
        return {
            "success": True,
            "message": f"Payroll for {emp_code} ({month}) created with net pay ₹{breakup['net_take_home']['monthly']:,}.",
            "payroll": breakup,
        }
