"""Lookup history domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GeolocationResultModel(BaseModel):
    """Normalized geolocation response used internally and for persistence."""

    model_config = ConfigDict(from_attributes=True)

    ip_address: str
    country: str
    region: str
    city: str
    latitude: float
    longitude: float
    timezone: str
    isp: str
    provider_payload: dict[str, Any] = Field(default_factory=dict)


class LookupHistoryRecordModel(BaseModel):
    """Stored history record for a user's IP lookup."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    username: str
    ip_address: str
    requested_at: datetime
    geolocation: GeolocationResultModel

