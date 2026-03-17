"""Schemas for lookup history responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.geo import GeolocationResponse


class LookupHistoryRecordResponse(BaseModel):
    """Response schema for a stored lookup history record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    username: str
    ip_address: str
    requested_at: datetime
    geolocation: GeolocationResponse

