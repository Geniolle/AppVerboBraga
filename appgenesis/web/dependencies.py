from __future__ import annotations

"""Thin, explicitly-imported helpers for request/session/current-user access.

These wrap the existing services (`appgenesis.services.session`,
`appgenesis.services.permissions`) without changing their behavior. The goal
is to give new code (use cases, domains/) a way to reach this data without
pulling in the `appgenesis.core` / `appgenesis.services` wildcard hubs.
"""

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from appgenesis.db.session import SessionLocal
from appgenesis.services.permissions import get_user_entity_permissions
from appgenesis.services.session import (
    get_current_user,
    get_session_entity_id,
    get_session_user_id,
)


def get_db_session():
    """FastAPI dependency yielding a database session, closed after the request."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_user_dict(request: Request, session: Session) -> dict[str, Any] | None:
    """Return the logged-in user dict (id, full_name, login_email), or None."""

    return get_current_user(request, session)


def get_selected_entity_id(request: Request) -> int | None:
    """Return the entity id currently selected in the request session, if any."""

    return get_session_entity_id(request)


def get_current_user_permissions(
    session: Session,
    request: Request,
    *,
    login_email: str = "",
) -> dict[str, Any] | None:
    """Resolve the acting user's entity permissions for the current request.

    Returns None when there is no logged-in user in the session.
    """

    user_id = get_session_user_id(request)
    if user_id is None:
        return None
    return get_user_entity_permissions(
        session,
        user_id,
        login_email,
        get_session_entity_id(request),
    )


__all__ = [
    "get_db_session",
    "get_current_user_dict",
    "get_selected_entity_id",
    "get_current_user_permissions",
]
