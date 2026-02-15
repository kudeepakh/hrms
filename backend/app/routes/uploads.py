"""File upload endpoint for employee documents (certificates, ID proofs)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, Form

from app.auth.dependencies import get_current_user
from app.models.employee import Employee, UploadedDocument
from app.models.user import User
from app.repositories.employee_repo import EmployeeRepository

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

_emp_repo = EmployeeRepository()


@router.post("/{emp_code}/document")
async def upload_document(
    emp_code: str,
    doc_type: str = Form(..., description="Document type: aadhaar, pan, degree, experience_letter, offer_letter, passport, voter_id, other"),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Upload a document (certificate / ID proof) for an employee."""
    emp = await _emp_repo.find_by_emp_code(emp_code.upper())
    if not emp:
        return {"error": f"Employee {emp_code} not found."}

    # Generate unique filename
    ext = os.path.splitext(file.filename or "file")[1] or ".pdf"
    unique_name = f"{emp_code.upper()}_{doc_type}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Create document reference
    doc_ref = UploadedDocument(
        doc_type=doc_type,
        file_name=file.filename or unique_name,
        file_url=f"/api/uploads/files/{unique_name}",
        uploaded_at=datetime.utcnow(),
    )
    emp.documents.append(doc_ref)
    emp.updated_at = datetime.utcnow()
    await _emp_repo.update(emp)

    return {
        "success": True,
        "message": f"Document '{doc_type}' uploaded for {emp_code}.",
        "document": doc_ref.model_dump(mode="json"),
    }


@router.get("/files/{filename}")
async def serve_file(filename: str):
    """Serve an uploaded file."""
    from fastapi.responses import FileResponse
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return {"error": "File not found."}
    return FileResponse(file_path)


@router.get("/{emp_code}/documents")
async def list_documents(
    emp_code: str,
    user: User = Depends(get_current_user),
):
    """List all uploaded documents for an employee."""
    emp = await _emp_repo.find_by_emp_code(emp_code.upper())
    if not emp:
        return {"error": f"Employee {emp_code} not found."}
    return {
        "emp_code": emp.emp_code,
        "documents": [d.model_dump(mode="json") for d in emp.documents],
    }


@router.delete("/{emp_code}/document/{doc_type}")
async def delete_document(
    emp_code: str,
    doc_type: str,
    user: User = Depends(get_current_user),
):
    """Delete a document of a specific type for an employee."""
    emp = await _emp_repo.find_by_emp_code(emp_code.upper())
    if not emp:
        return {"error": f"Employee {emp_code} not found."}

    original_count = len(emp.documents)
    emp.documents = [d for d in emp.documents if d.doc_type != doc_type]

    if len(emp.documents) == original_count:
        return {"error": f"No document of type '{doc_type}' found for {emp_code}."}

    emp.updated_at = datetime.utcnow()
    await _emp_repo.update(emp)
    return {"success": True, "message": f"Document '{doc_type}' removed for {emp_code}."}
