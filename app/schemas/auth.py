"""Authentication request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class UserCreate(BaseModel):
    """Payload used to register a new user."""

    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: SecretStr = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Payload used to authenticate a user."""

    username: str = Field(min_length=3, max_length=50)
    password: SecretStr = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Public representation of a user."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT access token response schema."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT payload schema used after decoding an access token."""

    sub: str
    exp: int
    iat: int

