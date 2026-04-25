from __future__ import annotations

from typing import Any

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from appverbo.core import *  # noqa: F403,F401
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    User,
    UserAccountStatus,
)
from appverbo.routes.users.helpers import _member_is_within_permissions
from appverbo.routes.users.router import router
from appverbo.services import *  # noqa: F403,F401


def _redirect_admin_users(success: str = "", error: str = "") -> RedirectResponse:
    return RedirectResponse(
        url=build_users_new_url(
            success=success,
            error=error,
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _prepare_user_invite_payload(
    request: Request,
    user_id: str,
    raw_entity_id: str = "",
) -> tuple[dict[str, Any] | None, RedirectResponse | None]:
    clean_user_id = user_id.strip()
    if not clean_user_id.isdigit():
        return None, _redirect_admin_users(error="Utilizador inválido para gerar convite.")

    parsed_user_id = int(clean_user_id)
    clean_entity_id = raw_entity_id.strip()
    parsed_entity_id: int | None = None
    if clean_entity_id:
        if not clean_entity_id.isdigit():
            return None, _redirect_admin_users(error="Entidade inválida para gerar convite.")
        parsed_entity_id = int(clean_entity_id)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return None, RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        selected_entity_id = get_session_entity_id(request)

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return None, _redirect_admin_users(
                error="Apenas administradores podem gerar convites."
            )

        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        user_row = session.execute(
            select(User.id, User.login_email, User.account_status, User.member_id).where(
                User.id == parsed_user_id
            )
        ).one_or_none()
        if user_row is None:
            return None, _redirect_admin_users(error="Utilizador não encontrado.")

        if str(user_row.account_status or "").strip().lower() != UserAccountStatus.PENDING.value:
            return None, _redirect_admin_users(
                error="Só é possível gerar convite para utilizadores pendentes."
            )

        if not _member_is_within_permissions(
            session,
            int(user_row.member_id),
            entity_permissions,
        ):
            return None, _redirect_admin_users(
                error="Sem permissão para gerar convite deste utilizador."
            )

        member = session.get(Member, int(user_row.member_id))
        if member is None:
            return None, _redirect_admin_users(
                error="Membro associado ao utilizador não encontrado."
            )

        allowed_entity_ids = sorted(set(entity_permissions.get("allowed_entity_ids") or set()))
        entity_links_stmt = (
            select(MemberEntity.entity_id, Entity.name)
            .join(Entity, Entity.id == MemberEntity.entity_id)
            .where(
                MemberEntity.member_id == int(user_row.member_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                Entity.is_active.is_(True),
            )
            .order_by(MemberEntity.id.asc())
        )
        if not entity_permissions.get("can_manage_all_entities"):
            if not allowed_entity_ids:
                return None, _redirect_admin_users(
                    error="Sem permissão para gerar convite deste utilizador."
                )
            entity_links_stmt = entity_links_stmt.where(
                MemberEntity.entity_id.in_(allowed_entity_ids)
            )

        entity_link_rows = session.execute(entity_links_stmt).all()
        if not entity_link_rows:
            return None, _redirect_admin_users(
                error="Utilizador sem entidade ativa para gerar convite."
            )

        entity_name_by_id: dict[int, str] = {
            int(row.entity_id): str(row.name or "-")
            for row in entity_link_rows
            if isinstance(row.entity_id, int)
        }

        invite_entity_id: int | None = None
        if parsed_entity_id is not None and parsed_entity_id in entity_name_by_id:
            invite_entity_id = parsed_entity_id
        elif selected_entity_id is not None and selected_entity_id in entity_name_by_id:
            invite_entity_id = int(selected_entity_id)
        else:
            invite_entity_id = next(iter(entity_name_by_id.keys()), None)

        if invite_entity_id is None:
            return None, _redirect_admin_users(
                error="Não foi possível determinar a entidade do convite."
            )

        entity_name = entity_name_by_id.get(invite_entity_id, "-")
        invite_token = build_user_invite_token(
            int(user_row.id),
            str(user_row.login_email),
            invite_entity_id,
        )
        invite_link = build_user_invite_link(request, invite_token)

        return {
            "recipient_email": str(user_row.login_email),
            "recipient_name": str(member.full_name or user_row.login_email),
            "entity_name": entity_name,
            "invite_link": invite_link,
            "invited_by_name": current_user["full_name"],
        }, None


def _generate_user_invite(
    request: Request,
    user_id: str,
    raw_entity_id: str = "",
) -> RedirectResponse:
    invite_payload, redirect_response = _prepare_user_invite_payload(
        request=request,
        user_id=user_id,
        raw_entity_id=raw_entity_id,
    )
    if redirect_response is not None:
        return redirect_response
    if invite_payload is None:
        return _redirect_admin_users(error="Não foi possível gerar convite.")

    email_sent, email_error = send_user_invite_email(
        recipient_email=str(invite_payload["recipient_email"]),
        recipient_name=str(invite_payload["recipient_name"]),
        entity_name=str(invite_payload["entity_name"]),
        invite_link=str(invite_payload["invite_link"]),
        invited_by_name=str(invite_payload["invited_by_name"]),
    )
    if email_sent:
        return _redirect_admin_users(success="Convite gerado e enviado com sucesso.")

    return _redirect_admin_users(
        success="Não foi possível enviar email automático.",
        error=f"{email_error} Link de ativação: {invite_payload['invite_link']}",
    )


@router.post("/users/generate-invite", response_class=HTMLResponse)
def generate_user_invite(
    request: Request,
    user_id: str = Form(...),
    entity_id: str = Form(""),
) -> RedirectResponse:
    return _generate_user_invite(request=request, user_id=user_id, raw_entity_id=entity_id)


@router.post("/users/resend-invite", response_class=HTMLResponse)
def resend_user_invite(
    request: Request,
    user_id: str = Form(...),
) -> RedirectResponse:
    return _generate_user_invite(request=request, user_id=user_id, raw_entity_id="")
