"""Authentication router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register_user(
    payload: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Register a new user account."""

    user = await auth_service.register_user(payload)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse, summary="Authenticate a user")
async def login_user(
    payload: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Authenticate a user and return a JWT access token."""

    access_token = await auth_service.authenticate_user(payload)
    return TokenResponse(access_token=access_token)

