"""User domain model."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserModel(BaseModel):
    """Internal representation of a persisted user."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    hashed_password: str
    created_at: datetime

