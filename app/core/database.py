"""MongoDB connection management."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.core.config import Settings
from app.core.exceptions import RepositoryUnavailableError


class MongoDatabase:
    """Manage the MongoDB client lifecycle."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the connection manager."""

        self._settings = settings
        self._client: AsyncIOMotorClient | None = None
        self._database: AsyncIOMotorDatabase | None = None

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Return the active MongoDB database instance."""

        if self._database is None:
            raise RepositoryUnavailableError("MongoDB connection has not been initialized.")
        return self._database

    async def connect(self) -> None:
        """Open the MongoDB connection and validate connectivity."""

        try:
            self._client = AsyncIOMotorClient(
                self._settings.mongodb_uri,
                tz_aware=True,
                serverSelectionTimeoutMS=5000,
            )
            await self._client.admin.command("ping")
            self._database = self._client[self._settings.mongodb_db_name]
        except PyMongoError as exc:
            raise RepositoryUnavailableError("Unable to connect to MongoDB.") from exc

    async def disconnect(self) -> None:
        """Close the MongoDB client if it is open."""

        if self._client is not None:
            self._client.close()
            self._client = None
            self._database = None

