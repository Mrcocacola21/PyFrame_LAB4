"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.middleware.sessions import SessionMiddleware

from app.api.routers import auth, health, lookups
from app.core.config import Settings
from app.core.database import MongoDatabase
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.repositories.history_repository import HistoryRepository
from app.repositories.user_repository import UserRepository
from app.web.router import router as web_router


def create_app(settings: Settings) -> FastAPI:
    """Create and configure a FastAPI application instance."""

    base_dir = Path(__file__).resolve().parent

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Initialize and tear down shared resources."""

        configure_logging(settings.log_level)
        app.state.settings = settings
        app.state.http_client = httpx.AsyncClient(
            base_url=str(settings.geolocation_base_url),
            headers={"Accept": "application/json"},
            timeout=settings.request_timeout_seconds,
        )
        app.state.mongo = MongoDatabase(settings)

        if not settings.testing:
            await app.state.mongo.connect()
            database = app.state.mongo.database
            await UserRepository(database).ensure_indexes()
            await HistoryRepository(database).ensure_indexes()
            logging.getLogger(__name__).info("MongoDB connection established.")

        try:
            yield
        finally:
            if not settings.testing:
                await app.state.mongo.disconnect()
            await app.state.http_client.aclose()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Authenticated service for IP geolocation lookups with MongoDB-backed request history."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.jwt_secret_key,
        session_cookie=settings.session_cookie_name,
        same_site="lax",
        https_only=settings.environment == "production",
    )
    app.mount(
        "/static",
        StaticFiles(directory=base_dir / "static"),
        name="static",
    )

    register_exception_handlers(app)

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next) -> Response:
        """Log request method, path, status code, and latency."""

        logger = logging.getLogger("app.request")
        response = await call_next(request)
        logger.info(
            "%s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
        )
        response.headers["X-Service-Name"] = settings.app_name
        return response

    app.include_router(web_router)
    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(auth.router, prefix=settings.api_prefix, tags=["auth"])
    app.include_router(lookups.router, prefix=settings.api_prefix, tags=["lookups"])
    return app
