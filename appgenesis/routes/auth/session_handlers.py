from __future__ import annotations

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appgenesis.db.session import SessionLocal
from appgenesis.domains.auth.schemas import LoginFormInput, SignupFormInput
from appgenesis.domains.auth.use_cases import (
    LoginFailure,
    LoginSuccess,
    SignupFailure,
    SignupSuccess,
    execute_login,
    execute_signup,
)
from appgenesis.services.auth import render_login
from appgenesis.services.i18n import persist_user_language_after_auth, persist_user_language_selection
from appgenesis.services.session import get_entity_context_for_user, set_session_entity_context
from appgenesis.shared.results import RedirectOutcome

from appgenesis.routes.auth.router import router

@router.post("/login", response_class=HTMLResponse)
def login_v1(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    entity_id: str = Form(""),
    login_mode: str = Form("login"),
) -> HTMLResponse:
    form = LoginFormInput(email=email, password=password, entity_id=entity_id, login_mode=login_mode)

    with SessionLocal() as session:
        result = execute_login(session, request, form)

        if isinstance(result, RedirectOutcome):
            return RedirectResponse(url=result.url, status_code=result.status_code)

        if isinstance(result, LoginFailure):
            return render_login(
                request,
                error=result.error,
                email=result.email,
                mode=result.mode,
                login_data=result.login_data,
                status_code=result.status_code,
            )

        assert isinstance(result, LoginSuccess)
        response = RedirectResponse(url="/users/new", status_code=status.HTTP_303_SEE_OTHER)
        resolved_language, should_commit_language = persist_user_language_after_auth(
            request,
            response,
            result.user,
        )
        if should_commit_language:
            session.commit()

    request.session["user_id"] = result.user.id
    request.session["user_name"] = result.user_full_name
    request.session["user_email"] = result.user.login_email
    set_session_entity_context(request, result.selected_entity_context)

    return response

@router.post("/signup", response_class=HTMLResponse)
def signup(
    request: Request,
    full_name: str = Form(...),
    country: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    entity_id: str = Form(""),
) -> HTMLResponse:
    form = SignupFormInput(
        full_name=full_name,
        country=country,
        primary_phone=primary_phone,
        email=email,
        password=password,
        confirm_password=confirm_password,
        entity_id=entity_id,
    )

    with SessionLocal() as session:
        result = execute_signup(session, request, form)

        if isinstance(result, RedirectOutcome):
            return RedirectResponse(url=result.url, status_code=result.status_code)

        if isinstance(result, SignupFailure):
            return render_login(
                request,
                error=" ".join(result.errors),
                mode="signup",
                signup_data=result.signup_data,
                status_code=result.status_code,
            )

        assert isinstance(result, SignupSuccess)
        response = RedirectResponse(url="/users/new", status_code=status.HTTP_303_SEE_OTHER)
        persist_user_language_selection(request, response, result.resolved_language)

        request.session["user_id"] = result.user.id
        request.session["user_name"] = result.clean_full_name
        request.session["user_email"] = result.clean_email
        set_session_entity_context(
            request,
            get_entity_context_for_user(
                session, result.user.id, result.user.login_email, result.parsed_entity_id
            ),
        )

    return response

@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(
        url="/login?success=Sessão encerrada com sucesso.",
        status_code=status.HTTP_303_SEE_OTHER,
    )
