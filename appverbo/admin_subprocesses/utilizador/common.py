from __future__ import annotations

from typing import Any

from fastapi import status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from appverbo.core import ADMIN_PROFILE_NAMES
from appverbo.models import (
    Entity,
    MemberEntity,
    MemberEntityStatus,
    Profile,
    User,
    UserAccountStatus,
)
from appverbo.services.auth import is_admin_user
from appverbo.services.page import build_users_new_url


# ###################################################################################
# (1) REDIRECTS PADRAO DO SUBPROCESSO UTILIZADOR
# ###################################################################################

def redirect_admin_users_v1(success: str = "", error: str = "") -> RedirectResponse:
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


def redirect_login_required_v1() -> RedirectResponse:
    return RedirectResponse(
        url="/login?error=Efetue login para continuar.",
        status_code=status.HTTP_302_FOUND,
    )


# ###################################################################################
# (2) VALIDACOES COMUNS DE PERFIL E PERMISSAO
# ###################################################################################

def is_admin_profile_v1(profile: Profile | None) -> bool:
    if profile is None:
        return False

    profile_name = (profile.name or "").strip().lower()

    if not profile_name:
        return False

    return profile_name in ADMIN_PROFILE_NAMES


def member_is_within_permissions_v1(
    session: Any,
    member_id: int,
    permissions: dict[str, Any],
) -> bool:
    if permissions.get("can_manage_all_entities"):
        return True

    allowed_entity_ids = sorted(set(permissions.get("allowed_entity_ids") or set()))

    if not allowed_entity_ids:
        return False

    scoped_link_id = session.scalar(
        select(MemberEntity.id)
        .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            MemberEntity.entity_id.in_(allowed_entity_ids),
        )
        .limit(1)
    )

    return scoped_link_id is not None


# ###################################################################################
# (3) PROTECAO CONTRA REMOVER O ULTIMO ADMIN ATIVO
# ###################################################################################

def get_active_entity_ids_for_member_v1(session: Any, member_id: int) -> list[int]:
    rows = session.scalars(
        select(MemberEntity.entity_id)
        .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
    ).all()

    entity_ids: list[int] = []
    seen: set[int] = set()

    for entity_id in rows:
        if not isinstance(entity_id, int):
            continue

        if entity_id in seen:
            continue

        seen.add(entity_id)
        entity_ids.append(entity_id)

    return entity_ids


def has_other_active_admin_for_entity_v1(
    session: Any,
    entity_id: int,
    excluded_user_id: int,
) -> bool:
    candidate_rows = session.execute(
        select(User.id, User.login_email)
        .join(MemberEntity, MemberEntity.member_id == User.member_id)
        .where(
            MemberEntity.entity_id == entity_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            User.id != excluded_user_id,
            User.account_status == UserAccountStatus.ACTIVE.value,
        )
        .order_by(User.id.asc())
    ).all()

    for row in candidate_rows:
        candidate_user_id = int(row.id)
        candidate_email = str(row.login_email or "")

        if is_admin_user(session, candidate_user_id, candidate_email):
            return True

    return False


def ensure_not_last_active_admin_for_member_v1(
    session: Any,
    member_id: int,
    excluded_user_id: int,
) -> tuple[bool, str]:
    entity_ids = get_active_entity_ids_for_member_v1(session, member_id)

    if not entity_ids:
        return True, ""

    for entity_id in entity_ids:
        if has_other_active_admin_for_entity_v1(session, entity_id, excluded_user_id):
            continue

        entity_name = session.scalar(
            select(Entity.name).where(Entity.id == entity_id).limit(1)
        )

        clean_entity_name = str(entity_name or f"ID {entity_id}")

        return (
            False,
            (
                "Tem de existir pelo menos um Admin ativo por entidade. "
                f"A entidade '{clean_entity_name}' ficaria sem Admin ativo."
            ),
        )

    return True, ""