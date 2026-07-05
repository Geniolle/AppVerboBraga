from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import RedirectResponse

from appgenesis.core import OAuthError
from appgenesis.db.session import SessionLocal
from appgenesis.domains.auth.use_cases import (
    OAuthCallbackFailure,
    OAuthCallbackSuccess,
    execute_oauth_callback,
)
from appgenesis.services.auth import fetch_oauth_userinfo, get_oauth_client
from appgenesis.services.i18n import persist_user_language_selection
from appgenesis.services.session import (
    get_current_user,
    get_entity_context_for_user,
    set_session_entity_context,
)

from appgenesis.routes.auth.router import router

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

    with SessionLocal() as session:
        result = execute_oauth_callback(session, request, userinfo)

        if isinstance(result, OAuthCallbackFailure):
            return RedirectResponse(
                url=f"/login?error={result.error}&mode=login",
                status_code=status.HTTP_302_FOUND,
            )

        assert isinstance(result, OAuthCallbackSuccess)
        response = RedirectResponse(url="/users/new", status_code=status.HTTP_303_SEE_OTHER)
        persist_user_language_selection(request, response, result.resolved_language)

        request.session["user_id"] = result.user.id
        request.session["user_name"] = result.full_name
        request.session["user_email"] = result.clean_email
        set_session_entity_context(
            request,
            get_entity_context_for_user(session, result.user.id, result.user.login_email, None),
        )

    return response
