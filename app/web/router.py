"""Server-rendered frontend routes."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.api.deps import get_auth_service, get_lookup_service, get_settings_dependency
from app.core.config import Settings
from app.core.exceptions import AppException
from app.models.user import UserModel
from app.schemas.auth import UserCreate, UserLogin
from app.schemas.geo import IPLookupRequest
from app.services.auth_service import AuthService
from app.services.lookup_service import LookupService
from app.web.deps import clear_access_token_cookie, get_optional_cookie_user, set_access_token_cookie
from app.web.flash import FlashMessage, add_flash_message, consume_flash_messages

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse, response_model=None)
async def show_home_page(
    request: Request,
    current_user: Annotated[UserModel | None, Depends(get_optional_cookie_user)],
    lookup_service: Annotated[LookupService, Depends(get_lookup_service)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> Response:
    """Render the authenticated home page or redirect to login."""

    if current_user is None:
        add_flash_message(request, "info", "Log in to access the IP lookup dashboard.")
        return _redirect("/login")

    history = await lookup_service.list_history(current_user, limit=settings.frontend_history_limit)
    return _render(
        request,
        "index.html",
        current_user=current_user,
        history=history,
        form_data={"ip_address": ""},
    )


@router.get("/register", response_class=HTMLResponse, response_model=None)
async def show_register_page(
    request: Request,
    current_user: Annotated[UserModel | None, Depends(get_optional_cookie_user)],
) -> Response:
    """Render the registration page for anonymous users."""

    if current_user is not None:
        return _redirect("/")

    return _render(
        request,
        "register.html",
        current_user=current_user,
        form_data={"username": ""},
    )


@router.post("/register", response_class=HTMLResponse, response_model=None)
async def submit_register_form(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[UserModel | None, Depends(get_optional_cookie_user)],
) -> Response:
    """Handle registration form submissions."""

    if current_user is not None:
        return _redirect("/")

    form_data = {"username": username}

    try:
        payload = UserCreate(username=username, password=password)
        await auth_service.register_user(payload)
    except ValidationError as exc:
        return _render_form_error(
            request,
            "register.html",
            form_data=form_data,
            message=_format_validation_error(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except AppException as exc:
        return _render_form_error(
            request,
            "register.html",
            form_data=form_data,
            message=exc.detail,
            status_code=exc.status_code,
        )

    add_flash_message(request, "success", "Registration complete. You can now log in.")
    return _redirect("/login")


@router.get("/login", response_class=HTMLResponse, response_model=None)
async def show_login_page(
    request: Request,
    current_user: Annotated[UserModel | None, Depends(get_optional_cookie_user)],
) -> Response:
    """Render the login page for anonymous users."""

    if current_user is not None:
        return _redirect("/")

    return _render(
        request,
        "login.html",
        current_user=current_user,
        form_data={"username": ""},
    )


@router.post("/login", response_class=HTMLResponse, response_model=None)
async def submit_login_form(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
    current_user: Annotated[UserModel | None, Depends(get_optional_cookie_user)],
) -> Response:
    """Handle login form submissions and issue an auth cookie."""

    if current_user is not None:
        return _redirect("/")

    form_data = {"username": username}

    try:
        payload = UserLogin(username=username, password=password)
        access_token = await auth_service.authenticate_user(payload)
    except ValidationError as exc:
        return _render_form_error(
            request,
            "login.html",
            form_data=form_data,
            message=_format_validation_error(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except AppException as exc:
        return _render_form_error(
            request,
            "login.html",
            form_data=form_data,
            message=exc.detail,
            status_code=exc.status_code,
        )

    add_flash_message(request, "success", "Logged in successfully.")
    response = _redirect("/")
    set_access_token_cookie(response, access_token, settings)
    return response


@router.post("/logout", response_model=None)
async def logout_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> Response:
    """Log the current user out by clearing the auth cookie and transient session state."""

    request.session.pop("last_lookup_result", None)
    add_flash_message(request, "success", "You have been logged out.")
    response = _redirect("/login")
    clear_access_token_cookie(response, settings)
    return response


@router.post("/lookup", response_class=HTMLResponse, response_model=None)
async def submit_lookup_form(
    request: Request,
    ip_address: Annotated[str, Form(alias="ip_address")],
    current_user: Annotated[UserModel | None, Depends(get_optional_cookie_user)],
    lookup_service: Annotated[LookupService, Depends(get_lookup_service)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> Response:
    """Handle authenticated IP lookup submissions from the web UI."""

    if current_user is None:
        add_flash_message(request, "info", "Log in to perform an IP lookup.")
        return _redirect("/login")

    history = await lookup_service.list_history(current_user, limit=settings.frontend_history_limit)

    try:
        payload = IPLookupRequest(ip=ip_address)
        geolocation = await lookup_service.lookup_ip(str(payload.ip))
        await lookup_service.record_lookup(current_user, geolocation)
    except ValidationError as exc:
        return _render_form_error(
            request,
            "index.html",
            current_user=current_user,
            history=history,
            form_data={"ip_address": ip_address},
            message=_format_validation_error(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except AppException as exc:
        return _render_form_error(
            request,
            "index.html",
            current_user=current_user,
            history=history,
            form_data={"ip_address": ip_address},
            message=exc.detail,
            status_code=exc.status_code,
        )

    request.session["last_lookup_result"] = geolocation.model_dump(mode="json")
    add_flash_message(request, "success", f"Geolocation data loaded for {geolocation.ip_address}.")
    return _redirect("/result")


@router.get("/result", response_class=HTMLResponse, response_model=None)
async def show_result_page(
    request: Request,
    current_user: Annotated[UserModel | None, Depends(get_optional_cookie_user)],
) -> Response:
    """Render the latest geolocation lookup result."""

    if current_user is None:
        add_flash_message(request, "info", "Log in to view lookup results.")
        return _redirect("/login")

    result = request.session.get("last_lookup_result")
    if result is None:
        add_flash_message(request, "info", "Run an IP lookup to view a result card.")
        return _redirect("/")

    return _render(
        request,
        "result.html",
        current_user=current_user,
        result=result,
    )


def _render(
    request: Request,
    template_name: str,
    status_code: int = status.HTTP_200_OK,
    flash_messages: list[FlashMessage] | None = None,
    **context: Any,
) -> HTMLResponse:
    """Render a template with common context values."""

    messages = consume_flash_messages(request)
    if flash_messages:
        messages.extend(flash_messages)

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "request": request,
            "flash_messages": messages,
            **context,
        },
        status_code=status_code,
    )


def _render_form_error(
    request: Request,
    template_name: str,
    message: str,
    status_code: int,
    **context: Any,
) -> HTMLResponse:
    """Render a template with a single flash-style error message."""

    return _render(
        request,
        template_name,
        status_code=status_code,
        flash_messages=[{"category": "error", "message": message}],
        **context,
    )


def _redirect(path: str) -> RedirectResponse:
    """Build a consistent POST-redirect-GET response."""

    return RedirectResponse(url=path, status_code=status.HTTP_303_SEE_OTHER)


def _format_validation_error(exc: ValidationError) -> str:
    """Convert a Pydantic validation error into a concise human-readable string."""

    first_error = exc.errors()[0]
    field_name = str(first_error["loc"][-1]).replace("_", " ").capitalize()
    message = first_error["msg"]
    return f"{field_name}: {message}"
