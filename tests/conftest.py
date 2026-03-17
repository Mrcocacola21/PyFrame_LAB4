"""Shared test fixtures and in-memory doubles."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_auth_service, get_history_repository, get_lookup_service, get_user_repository
from app.core.config import Settings
from app.core.exceptions import UpstreamServiceUnavailableError
from app.factory import create_app
from app.models.history import GeolocationResultModel, LookupHistoryRecordModel
from app.models.user import UserModel
from app.services.auth_service import AuthService
from app.services.lookup_service import LookupService


class FakeUserRepository:
    """In-memory user repository used in tests."""

    def __init__(self) -> None:
        """Initialize the in-memory storage."""

        self.users_by_id: dict[str, UserModel] = {}
        self.users_by_username: dict[str, UserModel] = {}

    async def find_by_username(self, username: str) -> UserModel | None:
        """Return a user by username."""

        return self.users_by_username.get(username)

    async def create_user(self, username: str, hashed_password: str) -> UserModel:
        """Store a new in-memory user."""

        user = UserModel(
            id=str(uuid4()),
            username=username,
            hashed_password=hashed_password,
            created_at=datetime.now(tz=UTC),
        )
        self.users_by_id[user.id] = user
        self.users_by_username[user.username] = user
        return user

    async def get_by_id(self, user_id: str) -> UserModel | None:
        """Return a user by identifier."""

        return self.users_by_id.get(user_id)


class FakeHistoryRepository:
    """In-memory lookup history repository used in tests."""

    def __init__(self) -> None:
        """Initialize the in-memory storage."""

        self.records: list[LookupHistoryRecordModel] = []

    async def create_record(
        self,
        user: UserModel,
        geolocation: GeolocationResultModel,
    ) -> LookupHistoryRecordModel:
        """Store a lookup history entry."""

        record = LookupHistoryRecordModel(
            id=str(uuid4()),
            user_id=user.id,
            username=user.username,
            ip_address=geolocation.ip_address,
            requested_at=datetime.now(tz=UTC),
            geolocation=geolocation,
        )
        self.records.append(record)
        return record

    async def list_by_user(self, user_id: str, limit: int = 20) -> list[LookupHistoryRecordModel]:
        """Return stored history entries for a given user."""

        records = [record for record in self.records if record.user_id == user_id]
        return list(reversed(records))[:limit]


class FakeGeolocationService:
    """Deterministic geolocation service used in tests."""

    def __init__(self) -> None:
        """Initialize the fake service state."""

        self.raise_unavailable = False

    async def lookup_ip(self, ip_address: str) -> GeolocationResultModel:
        """Return fixed geolocation data or simulate an upstream failure."""

        if self.raise_unavailable:
            raise UpstreamServiceUnavailableError()

        return GeolocationResultModel(
            ip_address=ip_address,
            country="United States",
            region="California",
            city="Mountain View",
            latitude=37.386,
            longitude=-122.0838,
            timezone="America/Los_Angeles",
            isp="Google LLC",
            provider_payload={"source": "fake"},
        )


@pytest.fixture
def app_bundle() -> dict[str, Any]:
    """Create a test app with dependency overrides and in-memory doubles."""

    settings = Settings(
        JWT_SECRET_KEY="test-secret-key-with-32-characters",
        MONGODB_URI="mongodb://localhost:27017",
        testing=True,
    )
    user_repository = FakeUserRepository()
    history_repository = FakeHistoryRepository()
    geolocation_service = FakeGeolocationService()

    app = create_app(settings)

    def override_user_repository() -> FakeUserRepository:
        """Return the fake user repository."""

        return user_repository

    def override_history_repository() -> FakeHistoryRepository:
        """Return the fake history repository."""

        return history_repository

    def override_auth_service() -> AuthService:
        """Return the auth service wired to the fake repository."""

        return AuthService(user_repository, settings)

    def override_lookup_service() -> LookupService:
        """Return the lookup service wired to fake dependencies."""

        return LookupService(geolocation_service, history_repository)

    app.dependency_overrides[get_user_repository] = override_user_repository
    app.dependency_overrides[get_history_repository] = override_history_repository
    app.dependency_overrides[get_auth_service] = override_auth_service
    app.dependency_overrides[get_lookup_service] = override_lookup_service

    return {
        "app": app,
        "settings": settings,
        "user_repository": user_repository,
        "history_repository": history_repository,
        "geolocation_service": geolocation_service,
    }


@pytest.fixture
async def client(app_bundle: dict[str, Any]) -> AsyncIterator[AsyncClient]:
    """Yield an async HTTP client for the FastAPI test app."""

    app = app_bundle["app"]
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            yield async_client
