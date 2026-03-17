"""Exception handlers registered on the FastAPI app."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException


async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    """Convert application exceptions into JSON HTTP responses."""

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=dict(exc.headers or {}),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return HTTP 400 for invalid IP payloads and 422 for other validation failures."""

    invalid_ip_error = any("ip" in ".".join(str(part) for part in error["loc"]) for error in exc.errors())
    status_code = 400 if invalid_ip_error else 422
    return JSONResponse(status_code=status_code, content={"detail": exc.errors()})


def register_exception_handlers(app: FastAPI) -> None:
    """Attach application exception handlers to the FastAPI app."""

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

