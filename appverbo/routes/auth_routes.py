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
from membrisia import (
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

router = APIRouter()


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
) -> HTMLResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
    if current_user is not None:
        return RedirectResponse(url="/users/new", status_code=status.HTTP_302_FOUND)
    return render_login(
        request,
        error=error or "",
        success=success or "",
        mode=mode,
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

    context = {
        "request": request,
        "token": token,
        "error": error,
        "success": success,
        "form_data": defaults,
        "account_already_active": account_already_active,
    }
    return templates.TemplateResponse(
        request,
        "user_invite_accept.html",
        context,
        status_code=status_code,
    )


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    entity_id: str = Form(""),
    login_mode: str = Form("login"),
) -> HTMLResponse:
    clean_email = email.strip().lower()
    clean_password = password
    clean_entity_id = entity_id.strip()
    login_data = {
        "entity_id": clean_entity_id,
    }
    requested_mode = "admin" if login_mode.strip().lower() == "admin" else "login"

    if not clean_email or not clean_password:
        return render_login(
            request,
            error="Informe email e palavra-passe.",
            email=clean_email,
            mode=requested_mode,
            login_data=login_data,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    parsed_entity_id: int | None = None
    if clean_entity_id:
        try:
            parsed_entity_id = int(clean_entity_id)
        except ValueError:
            return render_login(
                request,
                error="Entidade selecionada inválida.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    selected_entity_context: dict[str, Any] | None = None
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is not None:
            return RedirectResponse(url="/users/new", status_code=status.HTTP_302_FOUND)

        row = session.execute(
            select(
                User.id,
                User.login_email,
                User.password_hash,
                User.account_status,
                User.member_id,
                Member.full_name,
            )
           .join(Member, Member.id == User.member_id)
           .where(func.lower(User.login_email) == clean_email)
        ).one_or_none()

        if row is None or not verify_password(clean_password, row.password_hash):
            return render_login(
                request,
                error="Credenciais inválidas.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if row.account_status != UserAccountStatus.ACTIVE.value:
            return render_login(
                request,
                error=f"Conta com estado '{row.account_status}'. Contacte o administrador.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        current_user_is_admin = is_admin_user(session, row.id, row.login_email)
        if requested_mode == "admin" and not current_user_is_admin:
            return render_login(
                request,
                error="Acesso administrativo disponivel apenas para utilizadores administradores.",
                email=clean_email,
                mode="admin",
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        linked_entity_ids_rows = session.scalars(
            select(MemberEntity.entity_id)
           .where(
                MemberEntity.member_id == int(row.member_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
           .order_by(MemberEntity.id.asc())
        ).all()
        linked_entity_ids = [
            int(entity_id)
            for entity_id in linked_entity_ids_rows
            if isinstance(entity_id, int)
        ]
        if not linked_entity_ids:
            return render_login(
                request,
                error="Utilizador sem entidade ativa associada.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if parsed_entity_id is None:
            resolved_entity, resolution_error = resolve_active_entity_by_email(session, clean_email)
            if resolved_entity is None:
                return render_login(
                    request,
                    error=resolution_error or "Selecione a entidade para entrar.",
                    email=clean_email,
                    mode=requested_mode,
                    login_data=login_data,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            parsed_entity_id = int(resolved_entity.id)
            login_data["entity_id"] = str(parsed_entity_id)

        if parsed_entity_id not in linked_entity_ids:
            return render_login(
                request,
                error="Não é permitido entrar com uma entidade diferente da associada ao seu utilizador.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        selected_entity_context = get_entity_context_for_user(
            session,
            row.id,
            row.login_email,
            parsed_entity_id,
        )
        if selected_entity_context is None:
            return render_login(
                request,
                error="Não tem permissão para entrar na entidade selecionada.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

    request.session["user_id"] = row.id
    request.session["user_name"] = row.full_name
    request.session["user_email"] = row.login_email
    set_session_entity_context(request, selected_entity_context)
    return RedirectResponse(url="/users/new", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/signup", response_class=HTMLResponse)
def signup(
    request: Request,
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    entity_id: str = Form(""),
) -> HTMLResponse:
    errors: list[str] = []
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_entity_id = entity_id.strip()

    signup_data = {
        "full_name": clean_full_name,
        "primary_phone": clean_primary_phone,
        "email": clean_email,
        "entity_id": clean_entity_id,
    }

    if not clean_full_name:
        errors.append("Nome completo é obrigatório.")
    if not clean_primary_phone:
        errors.append("Telefone principal é obrigatório.")
    if not clean_email:
        errors.append("Email é obrigatório.")
    if len(password) < 8:
        errors.append("A palavra-passe deve ter no minimo 8 caracteres.")
    if password != confirm_password:
        errors.append("A confirmação da palavra-passe não confere.")

    parsed_entity_id: int | None = None
    if clean_entity_id:
        try:
            parsed_entity_id = int(clean_entity_id)
        except ValueError:
            errors.append("Entidade inválida.")

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is not None:
            return RedirectResponse(url="/users/new", status_code=status.HTTP_302_FOUND)

        existing_user = session.execute(
            select(User.id).where(func.lower(User.login_email) == clean_email)
        ).scalar_one_or_none()
        if existing_user:
            errors.append("Já existe conta com este email. Use o login.")

        if parsed_entity_id is not None:
            existing_entity = session.get(Entity, parsed_entity_id)
            if existing_entity is None:
                errors.append("Entidade selecionada não existe.")

        if errors:
            return render_login(
                request,
                error=" ".join(errors),
                mode="signup",
                signup_data=signup_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = upsert_user_by_email(
            session=session,
            email=clean_email,
            full_name=clean_full_name,
            primary_phone=clean_primary_phone,
            entity_id=parsed_entity_id,
        )
        user.password_hash = hash_password(password)
        user.account_status = UserAccountStatus.ACTIVE.value

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return render_login(
                request,
                error="Falha ao criar conta. Tente novamente.",
                mode="signup",
                signup_data=signup_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        request.session["user_id"] = user.id
        request.session["user_name"] = clean_full_name
        request.session["user_email"] = clean_email
        set_session_entity_context(
            request,
            get_entity_context_for_user(session, user.id, user.login_email, parsed_entity_id),
        )

    return RedirectResponse(url="/users/new", status_code=status.HTTP_303_SEE_OTHER)


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
        user = session.get(User, int(invite_payload["uid"]))
        if user is None or (user.login_email or "").strip().lower() != invite_payload["email"]:
            return render_invite_accept(
                request,
                token=clean_token,
                error="Convite inválido. Utilizador não encontrado.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if user.account_status != UserAccountStatus.PENDING.value:
            return render_invite_accept(
                request,
                token=clean_token,
                success="Esta conta já foi ativada. Pode entrar no sistema.",
                account_already_active=True,
            )

        member = session.get(Member, user.member_id)
        if member is None:
            return render_invite_accept(
                request,
                token=clean_token,
                error="Membro associado ao convite não foi encontrado.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        entity_name = "-"
        entity_row = session.execute(
            select(Entity.name)
           .join(MemberEntity, MemberEntity.entity_id == Entity.id)
           .where(
                MemberEntity.member_id == member.id,
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
           .order_by(MemberEntity.id.asc())
           .limit(1)
        ).one_or_none()
        if entity_row is not None:
            entity_name = str(entity_row.name or "-")

        return render_invite_accept(
            request,
            token=clean_token,
            form_data={
                "full_name": member.full_name or "",
                "primary_phone": member.primary_phone or "",
                "address": member.address or "",
                "city": member.city or "",
                "freguesia": member.freguesia or "",
                "postal_code": member.postal_code or "",
                "birth_date": format_optional_date_pt(member.birth_date),
                "entity_name": entity_name,
                "email": user.login_email or "",
            },
        )


@router.post("/users/invite/accept", response_class=HTMLResponse)
def invite_accept_submit(
    request: Request,
    token: str = Form(""),
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    freguesia: str = Form(...),
    postal_code: str = Form(...),
    birth_date: str = Form(""),
    password: str = Form(...),
    confirm_password: str = Form(...),
) -> HTMLResponse:
    clean_token = token.strip()
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_address = address.strip()
    clean_city = city.strip()
    clean_freguesia = freguesia.strip()
    clean_postal_code = postal_code.strip()
    clean_birth_date = birth_date.strip()

    invite_payload = parse_user_invite_token(clean_token)
    if invite_payload is None:
        return render_invite_accept(
            request,
            token=clean_token,
            error="Convite inválido ou expirado. Solicite um novo convite ao administrador.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    form_data: dict[str, str] = {
        "full_name": clean_full_name,
        "primary_phone": clean_primary_phone,
        "address": clean_address,
        "city": clean_city,
        "freguesia": clean_freguesia,
        "postal_code": clean_postal_code,
        "birth_date": clean_birth_date,
        "entity_name": "",
        "email": invite_payload["email"],
    }

    errors: list[str] = []
    if not clean_full_name:
        errors.append("Nome completo é obrigatório.")
    if not clean_primary_phone:
        errors.append("Telefone principal é obrigatório.")
    if not clean_address:
        errors.append("Morada é obrigatória.")
    if not clean_city:
        errors.append("Cidade é obrigatória.")
    if not clean_freguesia:
        errors.append("Freguesia é obrigatória.")
    if not clean_postal_code:
        errors.append("Código postal é obrigatório.")
    if len(password) < 8:
        errors.append("A palavra-passe deve ter no mínimo 8 caracteres.")
    if password != confirm_password:
        errors.append("A confirmação da palavra-passe não confere.")

    parsed_birth_date: date | None = None
    if clean_birth_date:
        try:
            parsed_birth_date = parse_optional_date_pt(clean_birth_date)
        except ValueError:
            errors.append("Data de nascimento inválida. Use o formato dd/mm/aaaa.")

    with SessionLocal() as session:
        user = session.get(User, int(invite_payload["uid"]))
        if user is None or (user.login_email or "").strip().lower() != invite_payload["email"]:
            return render_invite_accept(
                request,
                token=clean_token,
                error="Convite inválido. Utilizador não encontrado.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if user.account_status != UserAccountStatus.PENDING.value:
            return render_invite_accept(
                request,
                token=clean_token,
                success="Esta conta já foi ativada. Pode entrar no sistema.",
                account_already_active=True,
            )

        member = session.get(Member, user.member_id)
        if member is None:
            return render_invite_accept(
                request,
                token=clean_token,
                error="Membro associado ao convite não foi encontrado.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        entity_row = session.execute(
            select(Entity.name)
           .join(MemberEntity, MemberEntity.entity_id == Entity.id)
           .where(
                MemberEntity.member_id == member.id,
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
           .order_by(MemberEntity.id.asc())
           .limit(1)
        ).one_or_none()
        form_data["entity_name"] = str(entity_row.name or "-") if entity_row is not None else "-"
        form_data["email"] = user.login_email or ""

        if errors:
            return render_invite_accept(
                request,
                token=clean_token,
                error=" ".join(errors),
                form_data=form_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        member.full_name = clean_full_name
        member.primary_phone = clean_primary_phone
        member.address = clean_address
        member.city = clean_city
        member.freguesia = clean_freguesia
        member.postal_code = clean_postal_code
        member.birth_date = parsed_birth_date
        user.password_hash = hash_password(password)
        user.account_status = UserAccountStatus.ACTIVE.value

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return render_invite_accept(
                request,
                token=clean_token,
                error="Não foi possível concluir a ativação da conta. Tente novamente.",
                form_data=form_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        request.session["user_id"] = user.id
        request.session["user_name"] = member.full_name
        request.session["user_email"] = user.login_email
        set_session_entity_context(
            request,
            get_entity_context_for_user(session, user.id, user.login_email, None),
        )

    return RedirectResponse(
        url=build_users_new_url(
            profile_success="Conta ativada com sucesso. Complete e mantenha os dados atualizados.",
            profile_tab="pessoal",
            menu="perfil",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


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


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(
        url="/login?success=Sessão encerrada com sucesso.",
        status_code=status.HTTP_303_SEE_OTHER,
    )
