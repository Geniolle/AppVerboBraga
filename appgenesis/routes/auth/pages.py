from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appgenesis.db.session import SessionLocal
from appgenesis.domains.auth.use_cases import resolve_signup_entity_lock
from appgenesis.services.auth import render_login
from appgenesis.services.session import get_current_user, get_session_user_id

from appgenesis.routes.auth.router import router

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

    resolved_mode = "login" if mode.strip().lower() == "admin" else mode
    signup_data = None
    clean_entity_id = entity_id.strip()
    if resolved_mode.strip().lower() == "signup" and clean_entity_id.isdigit():
        with SessionLocal() as session:
            signup_data = resolve_signup_entity_lock(session, clean_entity_id)

    return render_login(
        request,
        error=error or "",
        success=success or "",
        mode=resolved_mode,
        signup_data=signup_data,
    )
