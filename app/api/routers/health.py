"""Health check router."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/health")


@router.get("", summary="Health check")
async def healthcheck() -> dict[str, str]:
    """Return a simple service health status."""

    return {"status": "ok"}

