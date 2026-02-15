"""Pydantic request/response schemas — separate from DB documents (SRP)."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, EmailStr


# ── Chat ──

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    data: Optional[Any] = None


# ── Auth ──

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    name: str
    email: str


# ── Employee ──

class EmployeeResponse(BaseModel):
    emp_code: str
    name: str
    email: str
    department: str
    designation: str
    date_of_joining: date
    salary: float
    manager_name: Optional[str] = None
    status: str


# ── Leave ──

class LeaveResponse(BaseModel):
    emp_code: str
    leave_type: str
    start_date: date
    end_date: date
    status: str
    reason: Optional[str] = None


# ── Attendance ──

class AttendanceResponse(BaseModel):
    emp_code: str
    date: date
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str


# ── Payroll ──

class PayrollResponse(BaseModel):
    emp_code: str
    month: str
    basic: float
    hra: float
    deductions: float
    net_pay: float
