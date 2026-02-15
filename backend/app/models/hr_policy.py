"""HR Policy document — ALL configuration lives in the DB, nothing hardcoded.

The INITIAL_* constants below are used ONLY once — to seed the very first policy
into MongoDB. After that, every calculation reads from the active HRPolicy
document, and every update creates a new versioned document with full diff
tracking.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from beanie import Document
from pymongo import IndexModel, ASCENDING
from pydantic import BaseModel


# ── Salary Breakup Configuration ─────────────────────────

class SalaryBreakup(BaseModel):
    """Salary component percentages (of CTC).
    Defaults here are ONLY used when constructing the initial seed policy.
    At runtime the service always reads from the DB document.
    """
    basic_pct: float = 40.0
    hra_pct: float = 20.0
    special_allowance_pct: float = 0.0
    pf_employer_pct: float = 12.0
    pf_employee_pct: float = 12.0
    esi_employer_pct: float = 3.25
    esi_employee_pct: float = 0.75
    esi_threshold: float = 21000.0
    professional_tax: float = 200.0
    gratuity_pct: float = 4.81
    medical_allowance: float = 1250.0
    conveyance_allowance: float = 1600.0


# ── Leave Policy Configuration ───────────────────────────

class LeavePolicy(BaseModel):
    """Annual leave credits per employee.
    Defaults here are ONLY used when constructing the initial seed policy.
    """
    casual_leave: int = 12
    sick_leave: int = 12
    earned_leave: int = 15
    maternity_leave: int = 182
    paternity_leave: int = 15
    compensatory_off: int = 0
    public_holidays: int = 10


# ── Tax Slab ─────────────────────────────────────────────

class TaxSlab(BaseModel):
    """Income tax slab."""
    min_income: float
    max_income: float  # use -1 for unlimited
    rate_pct: float


# ── INITIAL SEED VALUES (used only in seed.py, never at runtime) ──

INITIAL_TAX_SLABS_NEW_REGIME = [
    TaxSlab(min_income=0, max_income=400000, rate_pct=0),
    TaxSlab(min_income=400000, max_income=800000, rate_pct=5),
    TaxSlab(min_income=800000, max_income=1200000, rate_pct=10),
    TaxSlab(min_income=1200000, max_income=1600000, rate_pct=15),
    TaxSlab(min_income=1600000, max_income=2000000, rate_pct=20),
    TaxSlab(min_income=2000000, max_income=2400000, rate_pct=25),
    TaxSlab(min_income=2400000, max_income=-1, rate_pct=30),
]

INITIAL_TAX_SLABS_OLD_REGIME = [
    TaxSlab(min_income=0, max_income=250000, rate_pct=0),
    TaxSlab(min_income=250000, max_income=500000, rate_pct=5),
    TaxSlab(min_income=500000, max_income=1000000, rate_pct=20),
    TaxSlab(min_income=1000000, max_income=-1, rate_pct=30),
]

INITIAL_STATE_PROFESSIONAL_TAX: dict[str, float] = {
    "maharashtra": 200,
    "karnataka": 200,
    "west bengal": 200,
    "tamil_nadu": 0,
    "andhra_pradesh": 200,
    "telangana": 200,
    "kerala": 208,
    "gujarat": 200,
    "madhya_pradesh": 208,
    "rajasthan": 200,
    "delhi": 0,
    "uttar_pradesh": 0,
    "punjab": 0,
    "haryana": 0,
    "default": 200,
}

INITIAL_STATE_LEAVE_OVERRIDES: dict[str, dict[str, int]] = {
    "kerala": {"earned_leave": 18},
    "karnataka": {"earned_leave": 18},
    "tamil_nadu": {"earned_leave": 12, "casual_leave": 12, "sick_leave": 12},
}


# ── Policy Change Log ─────────────────────────────────

class PolicyChangeEntry(BaseModel):
    """Single field change within a policy update."""
    field: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class PolicyChangeLog(BaseModel):
    """One policy revision record — who changed what and when."""
    changed_by: str
    changed_at: datetime = datetime.utcnow()
    reason: Optional[str] = None
    changes: list[PolicyChangeEntry] = []


class HRPolicy(Document):
    """Company HR policy — one active document per company.

    ALL configuration is stored here (salary, leave, tax, state rules).
    Nothing is hardcoded in the service layer; everything is read from this
    document at runtime.
    """

    policy_name: str = "Default India HR Policy"
    state: str = "maharashtra"
    is_metro: bool = True
    salary_breakup: SalaryBreakup = SalaryBreakup()
    leave_policy: LeavePolicy = LeavePolicy()
    tax_regime: str = "new"  # company default
    tax_slabs: list[TaxSlab] = INITIAL_TAX_SLABS_NEW_REGIME
    old_regime_tax_slabs: list[TaxSlab] = INITIAL_TAX_SLABS_OLD_REGIME
    standard_deduction: float = 75000.0
    old_regime_standard_deduction: float = 50000.0
    cess_pct: float = 4.0

    # ── State-level reference data (stored in DB, fully editable) ──
    state_professional_tax: dict[str, float] = INITIAL_STATE_PROFESSIONAL_TAX
    state_leave_overrides: dict[str, dict[str, int]] = INITIAL_STATE_LEAVE_OVERRIDES

    is_active: bool = True
    change_history: list[PolicyChangeLog] = []
    version: int = 1
    created_by: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "hr_policies"
        indexes = [
            IndexModel([("is_active", ASCENDING)]),
            IndexModel([("version", ASCENDING)]),
        ]
