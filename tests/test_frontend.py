"""Integration tests for the server-rendered frontend."""

from __future__ import annotations

import pytest


async def _frontend_register_and_login(client, username: str = "web-user") -> None:
    """Register and log in through the HTML form flow."""

    register_response = await client.post(
        "/register",
        data={"username": username, "password": "frontendpass123"},
    )
    assert register_response.status_code == 303
    assert register_response.headers["location"] == "/login"

    login_response = await client.post(
        "/login",
        data={"username": username, "password": "frontendpass123"},
    )
    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/"
    assert client.cookies.get("access_token")


@pytest.mark.asyncio
async def test_home_redirects_to_login_for_anonymous_users(client) -> None:
    """Anonymous users are redirected away from the dashboard."""

    response = await client.get("/")
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    login_page = await client.get("/login")
    assert login_page.status_code == 200
    assert "Log in to access the IP lookup dashboard." in login_page.text


@pytest.mark.asyncio
async def test_frontend_register_login_and_dashboard_render(client) -> None:
    """Users can register, log in, and see the dashboard page."""

    await _frontend_register_and_login(client, username="dashboard-user")

    dashboard_response = await client.get("/")
    assert dashboard_response.status_code == 200
    assert "Inspect IP locations with a fast, clean workflow." in dashboard_response.text
    assert "dashboard-user" in dashboard_response.text


@pytest.mark.asyncio
async def test_frontend_lookup_flow_renders_result_and_history(client) -> None:
    """Lookup form submissions redirect to the result page and persist history."""

    await _frontend_register_and_login(client, username="result-user")

    lookup_response = await client.post("/lookup", data={"ip_address": "8.8.8.8"})
    assert lookup_response.status_code == 303
    assert lookup_response.headers["location"] == "/result"

    result_response = await client.get("/result")
    assert result_response.status_code == 200
    assert "United States" in result_response.text
    assert "Google LLC" in result_response.text
    assert "8.8.8.8" in result_response.text

    dashboard_response = await client.get("/")
    assert dashboard_response.status_code == 200
    assert "Your latest persisted lookups from MongoDB." in dashboard_response.text
    assert "8.8.8.8" in dashboard_response.text


@pytest.mark.asyncio
async def test_frontend_lookup_validation_error_is_rendered(client) -> None:
    """Invalid IP values are rendered back into the dashboard with an error."""

    await _frontend_register_and_login(client, username="validation-user")

    response = await client.post("/lookup", data={"ip_address": "not-an-ip"})
    assert response.status_code == 400
    assert "Ip: value is not a valid IPv4 or IPv6 address" in response.text
