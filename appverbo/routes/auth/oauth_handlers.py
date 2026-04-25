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

@router.get("/oauth/login/{provider}")
async def oauth_login(request: Request, provider: str) -> RedirectResponse:
    provider = provider.strip().lower()

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
    if current_user is not None:
        return RedirectResponse(url="/users/new", status_code=status.HTTP_302_FOUND)

    client = get_oauth_client(provider)
    if client is None:
        return RedirectResponse(
            url="/login?error=Provedor não configurado.&mode=login",
            status_code=status.HTTP_302_FOUND,
        )

    redirect_uri = request.url_for("oauth_callback", provider=provider)
    return await client.authorize_redirect(request, redirect_uri)

@router.get("/oauth/callback/{provider}")
async def oauth_callback(request: Request, provider: str) -> RedirectResponse:
    provider = provider.strip().lower()

    client = get_oauth_client(provider)
    if client is None:
        return RedirectResponse(
            url="/login?error=Provedor não configurado.&mode=login",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        token = await client.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(
            url="/login?error=Falha na autenticacao externa.&mode=login",
            status_code=status.HTTP_302_FOUND,
        )

    userinfo = await fetch_oauth_userinfo(request, provider, client, token)

    email = (
        userinfo.get("email")
        or userinfo.get("preferred_username")
        or userinfo.get("upn")
        or ""
    ).strip().lower()
    if not email:
        return RedirectResponse(
            url="/login?error=O provedor não devolveu email.&mode=login",
            status_code=status.HTTP_302_FOUND,
        )

    full_name = (
        userinfo.get("name")
        or userinfo.get("given_name")
        or email.split("@")[0]
    )

    with SessionLocal() as session:
        existing_user = session.execute(
            select(User.id, User.account_status).where(func.lower(User.login_email) == email)
        ).one_or_none()
        if existing_user is not None and existing_user.account_status != UserAccountStatus.ACTIVE.value:
            return RedirectResponse(
                url=f"/login?error=Conta com estado '{existing_user.account_status}'. Contacte o administrador.&mode=login",
                status_code=status.HTTP_302_FOUND,
            )

        try:
            user = upsert_user_by_email(
                session=session,
                email=email,
                full_name=full_name,
                primary_phone="N/D",
                entity_id=None,
            )
            user.account_status = UserAccountStatus.ACTIVE.value
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url="/login?error=Falha ao concluir login externo.&mode=login",
                status_code=status.HTTP_302_FOUND,
            )

        request.session["user_id"] = user.id
        request.session["user_name"] = full_name
        request.session["user_email"] = email
        set_session_entity_context(
            request,
            get_entity_context_for_user(session, user.id, user.login_email, None),
        )

    return RedirectResponse(url="/users/new", status_code=status.HTTP_303_SEE_OTHER)
