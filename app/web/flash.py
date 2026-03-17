"""Helpers for session-backed flash messages."""

from __future__ import annotations

from typing import TypedDict

from fastapi import Request


class FlashMessage(TypedDict):
    """Simple serializable flash message structure."""

    category: str
    message: str


def add_flash_message(request: Request, category: str, message: str) -> None:
    """Append a flash message to the current session."""

    messages = list(request.session.get("flash_messages", []))
    messages.append({"category": category, "message": message})
    request.session["flash_messages"] = messages


def consume_flash_messages(request: Request) -> list[FlashMessage]:
    """Return and clear flash messages stored in the session."""

    messages = list(request.session.pop("flash_messages", []))
    return [
        {"category": str(item["category"]), "message": str(item["message"])}
        for item in messages
    ]
