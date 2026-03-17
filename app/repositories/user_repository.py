"""MongoDB repository for user persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.core.exceptions import RepositoryUnavailableError, UserAlreadyExistsError
from app.models.user import UserModel


class UserRepository:
    """Persist and retrieve users from MongoDB."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a MongoDB database."""

        self._collection = database["users"]

    async def ensure_indexes(self) -> None:
        """Create the indexes required by the user collection."""

        try:
            await self._collection.create_index([("username", ASCENDING)], unique=True)
        except PyMongoError as exc:
            raise RepositoryUnavailableError() from exc

    async def create_user(self, username: str, hashed_password: str) -> UserModel:
        """Insert a new user document."""

        document = {
            "username": username,
            "hashed_password": hashed_password,
            "created_at": datetime.now(tz=UTC),
        }

        try:
            result = await self._collection.insert_one(document)
        except DuplicateKeyError as exc:
            raise UserAlreadyExistsError() from exc
        except PyMongoError as exc:
            raise RepositoryUnavailableError() from exc

        document["_id"] = result.inserted_id
        return self._document_to_model(document)

    async def find_by_username(self, username: str) -> UserModel | None:
        """Find a user by username."""

        try:
            document = await self._collection.find_one({"username": username})
        except PyMongoError as exc:
            raise RepositoryUnavailableError() from exc

        if document is None:
            return None
        return self._document_to_model(document)

    async def get_by_id(self, user_id: str) -> UserModel | None:
        """Find a user by MongoDB identifier."""

        try:
            object_id = ObjectId(user_id)
        except InvalidId:
            return None

        try:
            document = await self._collection.find_one({"_id": object_id})
        except PyMongoError as exc:
            raise RepositoryUnavailableError() from exc

        if document is None:
            return None
        return self._document_to_model(document)

    @staticmethod
    def _document_to_model(document: dict[str, Any]) -> UserModel:
        """Convert a MongoDB document into a user model."""

        mapped_document = dict(document)
        mapped_document["id"] = str(mapped_document.pop("_id"))
        return UserModel.model_validate(mapped_document)

