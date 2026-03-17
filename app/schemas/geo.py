"""Schemas related to IP lookup requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field, IPvAnyAddress, field_validator


class IPLookupRequest(BaseModel):
    """Request payload for a protected IP geolocation lookup."""

    ip: IPvAnyAddress

    @field_validator("ip", mode="before")
    @classmethod
    def normalize_ip(cls, value: object) -> object:
        """Trim whitespace before validating the IP address."""

        if isinstance(value, str):
            return value.strip()
        return value


class CoordinatesResponse(BaseModel):
    """Geographic coordinate response schema."""

    latitude: float = Field(description="Latitude of the IP location.")
    longitude: float = Field(description="Longitude of the IP location.")


class GeolocationResponse(BaseModel):
    """Normalized geolocation response sent to API clients."""

    ip_address: str
    country: str
    region: str
    city: str
    coordinates: CoordinatesResponse
    timezone: str
    isp: str

