"""Business logic for upstream IP geolocation lookups."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.exceptions import ExternalAPIError, UpstreamServiceUnavailableError
from app.models.history import GeolocationResultModel


class GeolocationService:
    """Fetch and normalize geolocation data from an upstream provider."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        """Initialize the service with a shared HTTP client."""

        self._http_client = http_client

    async def lookup_ip(self, ip_address: str) -> GeolocationResultModel:
        """Fetch geolocation information for the provided IP address."""

        try:
            response = await self._http_client.get(f"/{ip_address}")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500:
                raise UpstreamServiceUnavailableError() from exc
            raise ExternalAPIError("The geolocation provider rejected the lookup request.") from exc
        except httpx.RequestError as exc:
            raise UpstreamServiceUnavailableError() from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalAPIError() from exc

        if payload.get("success") is False:
            message = payload.get("message") or "The geolocation provider could not process the IP."
            raise ExternalAPIError(str(message))

        timezone_data = payload.get("timezone")
        connection_data = payload.get("connection")
        timezone = self._extract_timezone(timezone_data)
        isp = self._extract_isp(connection_data, payload)

        try:
            return GeolocationResultModel(
                ip_address=str(payload.get("ip") or ip_address),
                country=str(payload["country"]),
                region=str(payload.get("region") or ""),
                city=str(payload.get("city") or ""),
                latitude=float(payload["latitude"]),
                longitude=float(payload["longitude"]),
                timezone=timezone,
                isp=isp,
                provider_payload=payload,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ExternalAPIError() from exc

    @staticmethod
    def _extract_timezone(timezone_data: Any) -> str:
        """Normalize a timezone value from the provider payload."""

        if isinstance(timezone_data, dict):
            timezone = timezone_data.get("id") or timezone_data.get("name")
            if timezone:
                return str(timezone)
        if isinstance(timezone_data, str) and timezone_data:
            return timezone_data
        raise ExternalAPIError("The geolocation provider did not return a valid timezone.")

    @staticmethod
    def _extract_isp(connection_data: Any, payload: dict[str, Any]) -> str:
        """Normalize an ISP value from the provider payload."""

        if isinstance(connection_data, dict):
            isp = connection_data.get("isp") or connection_data.get("org")
            if isp:
                return str(isp)

        fallback_isp = payload.get("org")
        if fallback_isp:
            return str(fallback_isp)

        raise ExternalAPIError("The geolocation provider did not return ISP information.")

