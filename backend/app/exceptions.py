"""Custom exception classes for consistent error handling."""

from __future__ import annotations


class HRMSException(Exception):
    """Base exception for all HRMS errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(HRMSException):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            status_code=404,
        )


class UnauthorizedException(HRMSException):
    """Authentication required or failed."""

    def __init__(self, message: str = "Authentication required."):
        super().__init__(message=message, status_code=401)


class ForbiddenException(HRMSException):
    """Insufficient permissions."""

    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(message=message, status_code=403)


class BadRequestException(HRMSException):
    """Invalid request data."""

    def __init__(self, message: str = "Invalid request."):
        super().__init__(message=message, status_code=400)


class ConflictException(HRMSException):
    """Duplicate / conflict."""

    def __init__(self, message: str = "Resource already exists."):
        super().__init__(message=message, status_code=409)
