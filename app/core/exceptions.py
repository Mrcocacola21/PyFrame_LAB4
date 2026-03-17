"""Custom application exceptions."""

from __future__ import annotations

from typing import Mapping


class AppException(Exception):
    """Base application exception with an associated HTTP status code."""

    status_code = 500
    detail = "Internal server error."
    headers: Mapping[str, str] | None = None

    def __init__(
        self,
        detail: str | None = None,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize an application exception."""

        self.detail = detail or self.detail
        self.headers = headers or self.headers
        super().__init__(self.detail)


class UserAlreadyExistsError(AppException):
    """Raised when a username is already registered."""

    status_code = 409
    detail = "A user with that username already exists."


class InvalidCredentialsError(AppException):
    """Raised when authentication credentials are invalid."""

    status_code = 401
    detail = "Invalid username or password."
    headers = {"WWW-Authenticate": "Bearer"}


class AuthenticationError(AppException):
    """Raised when a JWT cannot be validated."""

    status_code = 401
    detail = "Could not validate credentials."
    headers = {"WWW-Authenticate": "Bearer"}


class ExternalAPIError(AppException):
    """Raised when the geolocation provider returns a bad response."""

    status_code = 502
    detail = "The geolocation provider returned an invalid response."


class UpstreamServiceUnavailableError(AppException):
    """Raised when the geolocation provider cannot be reached."""

    status_code = 503
    detail = "The geolocation provider is currently unavailable."


class RepositoryUnavailableError(AppException):
    """Raised when the persistence layer is unavailable."""

    status_code = 503
    detail = "The persistence layer is unavailable."

