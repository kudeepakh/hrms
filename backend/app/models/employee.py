"""Employee document model."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from beanie import Document
from pydantic import BaseModel
from pymongo import IndexModel, ASCENDING


class Address(BaseModel):
    """Postal address."""
    line1: str = ""
    line2: Optional[str] = None
    city: str = ""
    state: str = ""
    pincode: str = ""
    country: str = "India"


class EmergencyContact(BaseModel):
    """Emergency contact details."""
    name: str = ""
    relationship: str = ""
    phone: str = ""


class UploadedDocument(BaseModel):
    """Reference to an uploaded file (certificate / ID proof)."""
    doc_type: str          # e.g. "aadhaar", "pan", "degree", "experience_letter"
    file_name: str         # original filename
    file_url: str          # URL path served by backend
    uploaded_at: datetime = datetime.utcnow()


class Employee(Document):
    """Employee profile stored in MongoDB."""

    emp_code: str
    name: str
    email: str
    department: str
    designation: str
    date_of_joining: date
    salary: float
    manager_name: Optional[str] = None
    tax_regime: str = "new"  # employee's choice: "new" or "old"

    # ── Extended profile fields ──────────────────────────
    phone: Optional[str] = None
    personal_email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None           # male, female, other
    blood_group: Optional[str] = None
    marital_status: Optional[str] = None   # single, married, divorced, widowed
    nationality: str = "Indian"

    # Address
    current_address: Optional[Address] = None
    permanent_address: Optional[Address] = None

    # Emergency contact
    emergency_contact: Optional[EmergencyContact] = None

    # ID proofs & certificates (file references)
    documents: list[UploadedDocument] = []

    # Employment extras
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None

    status: str = "active"  # active, resigned, terminated
    resignation_date: Optional[date] = None
    last_working_date: Optional[date] = None
    exit_reason: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "employees"
        indexes = [
            IndexModel([("emp_code", ASCENDING)], unique=True),
            IndexModel([("email", ASCENDING)], unique=True),
        ]
