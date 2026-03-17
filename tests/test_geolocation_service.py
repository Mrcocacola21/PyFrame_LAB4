"""Unit tests for geolocation service normalization."""

from __future__ import annotations

import httpx
import pytest

from app.core.exceptions import ExternalAPIError
from app.services.geolocation_service import GeolocationService


@pytest.mark.asyncio
async def test_geolocation_service_normalizes_provider_payload() -> None:
    """The geolocation service maps provider fields into the internal model."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Return a successful fake provider response."""

        assert request.url.path == "/8.8.4.4"
        return httpx.Response(
            200,
            json={
                "success": True,
                "ip": "8.8.4.4",
                "country": "United States",
                "region": "California",
                "city": "Mountain View",
                "latitude": 37.4056,
                "longitude": -122.0775,
                "timezone": {"id": "America/Los_Angeles"},
                "connection": {"isp": "Google LLC"},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(base_url="https://ipwho.is", transport=transport) as client:
        service = GeolocationService(client)
        result = await service.lookup_ip("8.8.4.4")

    assert result.ip_address == "8.8.4.4"
    assert result.country == "United States"
    assert result.timezone == "America/Los_Angeles"
    assert result.isp == "Google LLC"


@pytest.mark.asyncio
async def test_geolocation_service_raises_for_invalid_provider_payload() -> None:
    """The geolocation service raises if the provider omits required fields."""

    def handler(_: httpx.Request) -> httpx.Response:
        """Return an incomplete fake provider response."""

        return httpx.Response(
            200,
            json={"success": True, "country": "United States", "connection": {"isp": "Google LLC"}},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(base_url="https://ipwho.is", transport=transport) as client:
        service = GeolocationService(client)
        with pytest.raises(ExternalAPIError):
            await service.lookup_ip("8.8.4.4")

