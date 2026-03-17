"""MongoDB repository for lookup history persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING
from pymongo.errors import PyMongoError

from app.core.exceptions import RepositoryUnavailableError
from app.models.history import GeolocationResultModel, LookupHistoryRecordModel
from app.models.user import UserModel


class HistoryRepository:
    """Persist and retrieve lookup history records from MongoDB."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a MongoDB database."""

        self._collection = database["lookup_history"]

    async def ensure_indexes(self) -> None:
        """Create indexes required for the lookup history collection."""

        try:
            await self._collection.create_index(
                [("user_id", DESCENDING), ("requested_at", DESCENDING)]
            )
        except PyMongoError as exc:
            raise RepositoryUnavailableError() from exc

    async def create_record(
        self,
        user: UserModel,
        geolocation: GeolocationResultModel,
    ) -> LookupHistoryRecordModel:
        """Insert a lookup history record for a user."""

        document = {
            "user_id": user.id,
            "username": user.username,
            "ip_address": geolocation.ip_address,
            "requested_at": datetime.now(tz=UTC),
            "geolocation": geolocation.model_dump(mode="json"),
        }

        try:
            result = await self._collection.insert_one(document)
        except PyMongoError as exc:
            raise RepositoryUnavailableError() from exc

        document["_id"] = result.inserted_id
        return self._document_to_model(document)

    async def list_by_user(self, user_id: str, limit: int = 20) -> list[LookupHistoryRecordModel]:
        """Return recent lookup history records for a user."""

        try:
            cursor = (
                self._collection.find({"user_id": user_id})
                .sort("requested_at", DESCENDING)
                .limit(limit)
            )
            documents = await cursor.to_list(length=limit)
        except PyMongoError as exc:
            raise RepositoryUnavailableError() from exc

        return [self._document_to_model(document) for document in documents]

    @staticmethod
    def _document_to_model(document: dict[str, Any]) -> LookupHistoryRecordModel:
        """Convert a MongoDB document into a lookup history model."""

        mapped_document = dict(document)
        mapped_document["id"] = str(mapped_document.pop("_id"))
        return LookupHistoryRecordModel.model_validate(mapped_document)

