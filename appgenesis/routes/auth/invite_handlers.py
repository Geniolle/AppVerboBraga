from __future__ import annotations

from fastapi import Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appgenesis.db.session import SessionLocal
from appgenesis.domains.auth.schemas import InviteAcceptSubmitFormInput
from appgenesis.domains.auth.use_cases import (
    InviteAcceptAlreadyActive,
    InviteAcceptInvalid,
    InviteAcceptSuccess,
    InvitePageAlreadyActive,
    InvitePageInvalid,
    InvitePageReady,
    execute_invite_accept,
    resolve_invite_accept_page,
)
from appgenesis.services.auth import parse_user_invite_token
from appgenesis.services.page import build_users_new_url
from appgenesis.services.phone_country import (
    get_supported_phone_countries,
    get_supported_phone_country_option,
    normalize_country_code,
)
from appgenesis.services.session import get_entity_context_for_user, set_session_entity_context
from appgenesis.web.templates import templates

from appgenesis.routes.auth.router import router

def render_invite_accept(
    request: Request,
    token: str,
    error: str = "",
    success: str = "",
    form_data: dict[str, str] | None = None,
    account_already_active: bool = False,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    defaults = {
        "full_name": "",
        "country": "",
        "primary_phone": "",
        "address": "",
        "city": "",
        "freguesia": "",
        "postal_code": "",
        "birth_date": "",
        "entity_name": "",
        "email": "",
    }
    if form_data:
        defaults.update(form_data)
    defaults["country"] = normalize_country_code(defaults.get("country", ""))

    selected_phone_country = get_supported_phone_country_option(defaults["country"])
    phone_placeholder = (
        selected_phone_country["placeholder"]
        if selected_phone_country is not None
        else "+351 910 000 000"
    )

    context = {
        "request": request,
        "token": token,
        "error": error,
        "success": success,
        "form_data": defaults,
        "supported_phone_countries": get_supported_phone_countries(),
        "selected_phone_country": selected_phone_country,
        "phone_placeholder": phone_placeholder,
        "account_already_active": account_already_active,
    }
    return templates.TemplateResponse(
        request,
        "user_invite_accept.html",
        context,
        status_code=status_code,
    )

@router.get("/users/invite/accept", response_class=HTMLResponse)
def invite_accept_page(
    request: Request,
    token: str = Query(""),
) -> HTMLResponse:
    clean_token = token.strip()
    if not clean_token:
        return render_invite_accept(
            request,
            token="",
            error="Convite inválido: token ausente.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    invite_payload = parse_user_invite_token(clean_token)
    if invite_payload is None:
        return render_invite_accept(
            request,
            token=clean_token,
            error="Convite inválido ou expirado. Solicite um novo convite ao administrador.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    with SessionLocal() as session:
        result = resolve_invite_accept_page(session, invite_payload)

    if isinstance(result, InvitePageInvalid):
        return render_invite_accept(
            request,
            token=clean_token,
            error=result.error,
            status_code=result.status_code,
        )

    if isinstance(result, InvitePageAlreadyActive):
        return render_invite_accept(
            request,
            token=clean_token,
            success="Esta conta já foi ativada. Pode entrar no sistema.",
            account_already_active=True,
        )

    assert isinstance(result, InvitePageReady)
    return render_invite_accept(
        request,
        token=clean_token,
        form_data=result.form_data,
    )

@router.post("/users/invite/accept", response_class=HTMLResponse)
def invite_accept_submit(
    request: Request,
    token: str = Form(""),
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    country: str = Form(""),
    address: str = Form(...),
    city: str = Form(...),
    freguesia: str = Form(...),
    postal_code: str = Form(...),
    birth_date: str = Form(""),
    password: str = Form(...),
    confirm_password: str = Form(...),
) -> HTMLResponse:
    form = InviteAcceptSubmitFormInput(
        token=token,
        full_name=full_name,
        primary_phone=primary_phone,
        country=country,
        address=address,
        city=city,
        freguesia=freguesia,
        postal_code=postal_code,
        birth_date=birth_date,
        password=password,
        confirm_password=confirm_password,
    )

    clean_token = form.token.strip()
    invite_payload = parse_user_invite_token(clean_token)
    if invite_payload is None:
        return render_invite_accept(
            request,
            token=clean_token,
            error="Convite inválido ou expirado. Solicite um novo convite ao administrador.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    with SessionLocal() as session:
        result = execute_invite_accept(session, form, invite_payload)

        if isinstance(result, InviteAcceptInvalid):
            return render_invite_accept(
                request,
                token=clean_token,
                error=result.error,
                form_data=result.form_data,
                status_code=result.status_code,
            )

        if isinstance(result, InviteAcceptAlreadyActive):
            return render_invite_accept(
                request,
                token=clean_token,
                success="Esta conta já foi ativada. Pode entrar no sistema.",
                account_already_active=True,
            )

        assert isinstance(result, InviteAcceptSuccess)
        request.session["user_id"] = result.user.id
        request.session["user_name"] = result.member.full_name
        request.session["user_email"] = result.user.login_email
        set_session_entity_context(
            request,
            get_entity_context_for_user(
                session, result.user.id, result.user.login_email, result.invite_entity_id
            ),
        )

    return RedirectResponse(
        url=build_users_new_url(
            profile_success="Conta ativada com sucesso. Complete e mantenha os dados atualizados.",
            profile_tab="pessoal",
            menu="perfil",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
