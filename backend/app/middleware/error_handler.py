"""Global error-handling middleware.

Catches HRMSException subclasses and unhandled errors,
returning a consistent JSON envelope.
"""

from __future__ import annotations

import logging
import traceback

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.exceptions import HRMSException

logger = logging.getLogger("hrms.error")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Translate exceptions into uniform JSON responses."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HRMSException as exc:
            logger.warning("HRMS error: %s (status=%d)", exc.message, exc.status_code)
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.message, "status_code": exc.status_code},
            )
        except Exception as exc:
            logger.error("Unhandled error: %s\n%s", str(exc), traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error.", "status_code": 500},
            )
