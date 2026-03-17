"""Business logic for protected lookup workflows."""

from __future__ import annotations

from app.models.history import GeolocationResultModel, LookupHistoryRecordModel
from app.models.user import UserModel
from app.repositories.history_repository import HistoryRepository
from app.services.geolocation_service import GeolocationService


class LookupService:
    """Coordinate IP lookups and request history persistence."""

    def __init__(
        self,
        geolocation_service: GeolocationService,
        history_repository: HistoryRepository,
    ) -> None:
        """Initialize the service with its dependencies."""

        self._geolocation_service = geolocation_service
        self._history_repository = history_repository

    async def lookup_ip(self, ip_address: str) -> GeolocationResultModel:
        """Retrieve normalized geolocation data for an IP address."""

        return await self._geolocation_service.lookup_ip(ip_address)

    async def record_lookup(
        self,
        user: UserModel,
        geolocation: GeolocationResultModel,
    ) -> LookupHistoryRecordModel:
        """Persist the lookup response for the authenticated user."""

        return await self._history_repository.create_record(user, geolocation)

    async def list_history(self, user: UserModel, limit: int = 20) -> list[LookupHistoryRecordModel]:
        """Return recent lookup history records for the authenticated user."""

        return await self._history_repository.list_by_user(user.id, limit=limit)

