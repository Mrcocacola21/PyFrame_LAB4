"""Application configuration."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    app_name: str = "IP Geolocation Service"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    debug: bool = False
    testing: bool = False
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    access_token_cookie_name: str = "access_token"
    session_cookie_name: str = "ip_lookup_session"
    frontend_history_limit: int = 8
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db_name: str = Field("ip_lookup_service", alias="MONGODB_DB_NAME")
    geolocation_base_url: HttpUrl = Field("https://ipwho.is", alias="GEOLOCATION_BASE_URL")
    request_timeout_seconds: float = Field(10.0, alias="REQUEST_TIMEOUT_SECONDS")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_flag(cls, value: object) -> object:
        """Accept common deployment-style string values for the debug flag."""

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        """Require a sufficiently long JWT secret for HMAC signing."""

        if len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters.")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
