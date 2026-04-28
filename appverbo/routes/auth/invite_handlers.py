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

def _resolve_invite_entity_for_member(
    session: Session,
    member_id: int,
    requested_entity_id: int | None,
) -> tuple[int | None, str]:
    entity_rows = session.execute(
        select(Entity.id, Entity.name)
       .join(MemberEntity, MemberEntity.entity_id == Entity.id)
       .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            Entity.is_active.is_(True),
        )
       .order_by(MemberEntity.id.asc())
    ).all()
    if not entity_rows:
        return None, "-"

    if isinstance(requested_entity_id, int) and requested_entity_id > 0:
        for row in entity_rows:
            if int(row.id) == requested_entity_id:
                return int(row.id), str(row.name or "-")

    first_row = entity_rows[0]
    return int(first_row.id), str(first_row.name or "-")


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

        _, entity_name = _resolve_invite_entity_for_member(
            session,
            int(member.id),
            invite_payload.get("entity_id"),
        )

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
    country: str = Form(""),
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
    clean_country = country.strip()
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

        invite_entity_id, invite_entity_name = _resolve_invite_entity_for_member(
            session,
            int(member.id),
            invite_payload.get("entity_id"),
        )
        form_data["entity_name"] = invite_entity_name
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
            get_entity_context_for_user(session, user.id, user.login_email, invite_entity_id),
        )

    return RedirectResponse(
        url=build_users_new_url(
            profile_success="Conta ativada com sucesso. Complete e mantenha os dados atualizados.",
            profile_tab="pessoal",
            menu="perfil",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
