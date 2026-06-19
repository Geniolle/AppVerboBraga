
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, Member, MemberEntity, MemberEntityStatus, User, UserAccountStatus
from appverbo.services.auth import build_user_invite_link, build_user_invite_token, is_admin_user, send_user_invite_email
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.user_permissions import member_is_within_permissions_v1


@dataclass(frozen=True)
class UserInvitePayload:
    recipient_email: str
    recipient_name: str
    entity_name: str
    invite_link: str
    invited_by_name: str


def redirect_admin_users_v1(success: str = "", error: str = "") -> UserActionOutcome:
    return UserActionOutcome(
        kind="redirect",
        redirect_url=build_users_new_url(
            success=success,
            error=error,
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
    )


def prepare_user_invite_payload_v1(
    *,
    session: Session,
    request: Request,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    user_id: int,
    raw_entity_id: str = "",
) -> tuple[UserInvitePayload | None, UserActionOutcome | None]:
    if not is_admin_user(session, int(actor_user["id"]), str(actor_user["login_email"])):
        return None, redirect_admin_users_v1(error="Apenas administradores podem gerar convites.")

    entity_permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    user_row = session.execute(
        select(User.id, User.login_email, User.account_status, User.member_id)
        .where(User.id == int(user_id))
        .limit(1)
    ).one_or_none()

    if user_row is None:
        return None, redirect_admin_users_v1(error="Utilizador não encontrado.")

    if str(user_row.account_status or "").strip().lower() != UserAccountStatus.PENDING.value:
        return None, redirect_admin_users_v1(
            error="Só é possível gerar convite para utilizadores pendentes."
        )

    if not member_is_within_permissions_v1(
        session=session,
        member_id=int(user_row.member_id),
        permissions=entity_permissions,
    ):
        return None, redirect_admin_users_v1(
            error="Sem permissão para gerar convite deste utilizador."
        )

    member = session.get(Member, int(user_row.member_id))

    if member is None:
        return None, redirect_admin_users_v1(
            error="Membro associado ao utilizador não encontrado."
        )

    parsed_entity_id: int | None = None
    clean_entity_id = (raw_entity_id or "").strip()

    if clean_entity_id:
        if not clean_entity_id.isdigit():
            return None, redirect_admin_users_v1(error="Entidade inválida para gerar convite.")
        parsed_entity_id = int(clean_entity_id)

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
        allowed_ids = sorted(
            {
                int(raw_id)
                for raw_id in (entity_permissions.get("allowed_entity_ids") or set())
                if str(raw_id).strip().isdigit()
            }
        )

        if not allowed_ids:
            return None, redirect_admin_users_v1(
                error="Sem permissão para gerar convite deste utilizador."
            )

        entity_links_stmt = entity_links_stmt.where(MemberEntity.entity_id.in_(allowed_ids))

    entity_link_rows = session.execute(entity_links_stmt).all()

    if not entity_link_rows:
        return None, redirect_admin_users_v1(
            error="Utilizador sem entidade ativa para gerar convite."
        )

    entity_name_by_id = {
        int(row.entity_id): str(row.name or "-")
        for row in entity_link_rows
        if row.entity_id is not None
    }

    invite_entity_id: int | None = None

    if parsed_entity_id is not None and parsed_entity_id in entity_name_by_id:
        invite_entity_id = parsed_entity_id
    elif selected_entity_id is not None and int(selected_entity_id) in entity_name_by_id:
        invite_entity_id = int(selected_entity_id)
    else:
        invite_entity_id = next(iter(entity_name_by_id.keys()), None)

    if invite_entity_id is None:
        return None, redirect_admin_users_v1(
            error="Não foi possível determinar a entidade do convite."
        )

    invite_token = build_user_invite_token(
        int(user_row.id),
        str(user_row.login_email),
        invite_entity_id,
    )
    invite_link = build_user_invite_link(request, invite_token)

    return (
        UserInvitePayload(
            recipient_email=str(user_row.login_email),
            recipient_name=str(member.full_name or user_row.login_email),
            entity_name=entity_name_by_id.get(invite_entity_id, "-"),
            invite_link=invite_link,
            invited_by_name=str(actor_user["full_name"]),
        ),
        None,
    )


def send_user_invite_v1(payload: UserInvitePayload) -> UserActionOutcome:
    email_sent, email_error = send_user_invite_email(
        recipient_email=payload.recipient_email,
        recipient_name=payload.recipient_name,
        entity_name=payload.entity_name,
        invite_link=payload.invite_link,
        invited_by_name=payload.invited_by_name,
    )

    if email_sent:
        return redirect_admin_users_v1(success="Convite gerado e enviado com sucesso.")

    return redirect_admin_users_v1(
        success="Não foi possível enviar email automático.",
        error=f"{email_error} Link de ativação: {payload.invite_link}",
    )
