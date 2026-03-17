"""Frontend-specific dependencies and helpers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from pydantic import ValidationError

from app.api.deps import get_auth_service, get_settings_dependency
from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.models.user import UserModel
from app.schemas.auth import TokenPayload
from app.services.auth_service import AuthService


async def get_optional_cookie_user(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> UserModel | None:
    """Return the authenticated user from the access-token cookie if present."""

    token = request.cookies.get(settings.access_token_cookie_name)
    if not token:
        return None

    try:
        payload = decode_access_token(token, settings)
        token_payload = TokenPayload.model_validate(payload)
        if not token_payload.sub:
            return None
        return await auth_service.get_user_by_id(token_payload.sub)
    except (AuthenticationError, ValidationError):
        return None


def set_access_token_cookie(response, token: str, settings: Settings) -> None:
    """Set the HTTP-only access-token cookie on a response."""

    max_age = settings.access_token_expire_minutes * 60
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=token,
        httponly=True,
        max_age=max_age,
        expires=max_age,
        samesite="lax",
        secure=settings.environment == "production",
        path="/",
    )


def clear_access_token_cookie(response, settings: Settings) -> None:
    """Remove the HTTP-only access-token cookie from a response."""

    response.delete_cookie(
        key=settings.access_token_cookie_name,
        path="/",
        samesite="lax",
        secure=settings.environment == "production",
    )
