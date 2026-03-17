"""Dependency providers used by API routers."""

from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.models.user import UserModel
from app.repositories.history_repository import HistoryRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPayload
from app.services.auth_service import AuthService
from app.services.geolocation_service import GeolocationService
from app.services.lookup_service import LookupService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_settings_dependency(request: Request) -> Settings:
    """Return application settings stored on the FastAPI app state."""

    return request.app.state.settings


def get_database(request: Request) -> AsyncIOMotorDatabase:
    """Return the configured MongoDB database from the application state."""

    return request.app.state.mongo.database


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Return the shared HTTP client from the application state."""

    return request.app.state.http_client


def get_user_repository(
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> UserRepository:
    """Build a user repository dependency."""

    return UserRepository(database)


def get_history_repository(
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> HistoryRepository:
    """Build a history repository dependency."""

    return HistoryRepository(database)


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> AuthService:
    """Build an authentication service dependency."""

    return AuthService(user_repository, settings)


def get_lookup_service(
    history_repository: Annotated[HistoryRepository, Depends(get_history_repository)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> LookupService:
    """Build a lookup service dependency."""

    geolocation_service = GeolocationService(http_client)
    return LookupService(geolocation_service, history_repository)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> UserModel:
    """Resolve the authenticated user from the access token."""

    payload = decode_access_token(token, settings)
    token_payload = TokenPayload.model_validate(payload)
    if not token_payload.sub:
        raise AuthenticationError()
    return await auth_service.get_user_by_id(token_payload.sub)

