from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.core import *  # noqa: F403,F401
from appverbo.services import *  # noqa: F403,F401
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    Profile,
    User,
    UserAccountStatus,
    UserProfile,
)

from appverbo.routes.auth.router import router

@router.get("/", response_class=HTMLResponse)
def root_page(request: Request) -> RedirectResponse:
    if get_session_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/users/new", status_code=status.HTTP_302_FOUND)

@router.get("/home", response_class=HTMLResponse)
def home_page(request: Request) -> RedirectResponse:
    if get_session_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/users/new?menu=home", status_code=status.HTTP_302_FOUND)

@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    error: str | None = None,
    success: str | None = None,
    mode: str = "login",
    entity_id: str = "",
) -> HTMLResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
    if current_user is not None:
        return RedirectResponse(url="/users/new", status_code=status.HTTP_302_FOUND)
    signup_data = None
    clean_entity_id = entity_id.strip()
    if mode.strip().lower() == "signup" and clean_entity_id.isdigit():
        signup_data = get_signup_defaults()
        with SessionLocal() as session:
            linked_entity = session.get(Entity, int(clean_entity_id))
        if linked_entity is not None and linked_entity.is_active:
            signup_data["entity_id"] = clean_entity_id
            signup_data["entity_name"] = linked_entity.name or ""
            signup_data["entity_locked"] = "1"
    return render_login(
        request,
        error=error or "",
        success=success or "",
        mode=mode,
        signup_data=signup_data,
    )

@router.get("/login/admin", response_class=HTMLResponse)
def admin_login_page(
    request: Request,
    error: str | None = None,
    success: str | None = None,
) -> HTMLResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
    if current_user is not None:
        return RedirectResponse(url="/users/new", status_code=status.HTTP_302_FOUND)
    return render_login(
        request,
        error=error or "",
        success=success or "",
        mode="admin",
    )
