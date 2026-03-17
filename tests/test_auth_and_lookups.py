"""Integration tests for authentication and protected lookup flows."""

from __future__ import annotations

from typing import Any

import pytest


async def _register_and_login(client, username: str = "tester") -> str:
    """Register and authenticate a user, returning the access token."""

    register_response = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "strongpass123"},
    )
    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "strongpass123"},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_register_and_login_flow(client) -> None:
    """Users can register and log in successfully."""

    register_response = await client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "password": "supersecret123"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["username"] == "alice"

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "supersecret123"},
    )
    payload = login_response.json()
    assert login_response.status_code == 200
    assert payload["token_type"] == "bearer"
    assert isinstance(payload["access_token"], str)
    assert payload["access_token"]


@pytest.mark.asyncio
async def test_lookup_requires_authentication(client) -> None:
    """The lookup endpoint rejects unauthenticated requests."""

    response = await client.post("/api/v1/lookups", json={"ip": "8.8.8.8"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_lookup_returns_data_and_persists_history(client) -> None:
    """Authenticated lookups return data and persist a history record."""

    token = await _register_and_login(client, username="history-user")
    headers = {"Authorization": f"Bearer {token}"}

    lookup_response = await client.post("/api/v1/lookups", json={"ip": "8.8.8.8"}, headers=headers)
    lookup_payload = lookup_response.json()

    assert lookup_response.status_code == 200
    assert lookup_payload["country"] == "United States"
    assert lookup_payload["coordinates"]["latitude"] == 37.386
    assert lookup_payload["timezone"] == "America/Los_Angeles"

    history_response = await client.get("/api/v1/lookups/history", headers=headers)
    history_payload = history_response.json()

    assert history_response.status_code == 200
    assert len(history_payload) == 1
    assert history_payload[0]["ip_address"] == "8.8.8.8"
    assert history_payload[0]["geolocation"]["isp"] == "Google LLC"


@pytest.mark.asyncio
async def test_invalid_ip_returns_http_400(client) -> None:
    """Invalid IP payloads return HTTP 400 as required."""

    token = await _register_and_login(client, username="ip-validation-user")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/v1/lookups", json={"ip": "not-an-ip"}, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upstream_failure_returns_http_503(client, app_bundle: dict[str, Any]) -> None:
    """Upstream geolocation failures are translated to HTTP 503."""

    app_bundle["geolocation_service"].raise_unavailable = True
    token = await _register_and_login(client, username="upstream-user")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/v1/lookups", json={"ip": "1.1.1.1"}, headers=headers)
    assert response.status_code == 503

