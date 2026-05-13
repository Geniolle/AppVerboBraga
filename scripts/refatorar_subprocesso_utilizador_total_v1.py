from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(".")


def read_text_v1(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def write_text_v1(path: str, content: str) -> None:
    file_path = ROOT / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_module_v1(path: str, content: str) -> None:
    write_text_v1(path, content)


####################################################################################
# (4.1) REPOSITORIES
####################################################################################

write_module_v1(
    "appverbo/repositories/user_repository.py",
    r'''
from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from appverbo.models import User


def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, int(user_id))


def get_user_by_email_ci(session: Session, login_email: str) -> User | None:
    clean_email = (login_email or "").strip().lower()
    if not clean_email:
        return None

    return session.execute(
        select(User).where(func.lower(User.login_email) == clean_email)
    ).scalar_one_or_none()


def get_duplicate_user_id_by_email_ci(
    session: Session,
    login_email: str,
    excluded_user_id: int | None = None,
) -> int | None:
    clean_email = (login_email or "").strip().lower()
    if not clean_email:
        return None

    stmt = select(User.id).where(func.lower(User.login_email) == clean_email)

    if excluded_user_id is not None:
        stmt = stmt.where(User.id != int(excluded_user_id))

    duplicate_id = session.scalar(stmt.limit(1))
    return int(duplicate_id) if duplicate_id is not None else None


def null_created_by_for_deleted_user(session: Session, user_id: int) -> None:
    session.execute(
        update(User)
        .where(User.created_by_user_id == int(user_id))
        .values(created_by_user_id=None)
    )
''',
)

write_module_v1(
    "appverbo/repositories/member_repository.py",
    r'''
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from appverbo.models import Member


def get_member_by_id(session: Session, member_id: int) -> Member | None:
    return session.get(Member, int(member_id))


def get_member_by_email_ci(session: Session, email: str) -> Member | None:
    clean_email = (email or "").strip().lower()
    if not clean_email:
        return None

    return session.execute(
        select(Member).where(func.lower(Member.email) == clean_email)
    ).scalar_one_or_none()


def get_duplicate_member_id_by_email_ci(
    session: Session,
    email: str,
    excluded_member_id: int | None = None,
) -> int | None:
    clean_email = (email or "").strip().lower()
    if not clean_email:
        return None

    stmt = select(Member.id).where(func.lower(Member.email) == clean_email)

    if excluded_member_id is not None:
        stmt = stmt.where(Member.id != int(excluded_member_id))

    duplicate_id = session.scalar(stmt.limit(1))
    return int(duplicate_id) if duplicate_id is not None else None
''',
)

write_module_v1(
    "appverbo/repositories/member_entity_repository.py",
    r'''
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, MemberEntityStatus


def get_primary_member_entity_link(session: Session, member_id: int) -> MemberEntity | None:
    return session.execute(
        select(MemberEntity)
        .where(MemberEntity.member_id == int(member_id))
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).scalar_one_or_none()


def get_member_entity_link(
    session: Session,
    member_id: int,
    entity_id: int,
) -> MemberEntity | None:
    return session.execute(
        select(MemberEntity)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.entity_id == int(entity_id),
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).scalar_one_or_none()


def upsert_active_member_entity_link(
    session: Session,
    member_id: int,
    entity_id: int,
    *,
    replace_primary: bool = False,
) -> MemberEntity:
    if replace_primary:
        link = get_primary_member_entity_link(session, member_id)
    else:
        link = get_member_entity_link(session, member_id, entity_id)

    if link is None:
        link = MemberEntity(
            member_id=int(member_id),
            entity_id=int(entity_id),
            status=MemberEntityStatus.ACTIVE.value,
            entry_date=date.today(),
        )
        session.add(link)
        return link

    link.entity_id = int(entity_id)
    link.status = MemberEntityStatus.ACTIVE.value

    if link.entry_date is None:
        link.entry_date = date.today()

    return link


def get_primary_entity_for_member(session: Session, member_id: int) -> tuple[int | None, str]:
    row = session.execute(
        select(Entity.id, Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).one_or_none()

    if row is None:
        return None, "-"

    return int(row.id), str(row.name or "-")


def get_active_entity_ids_for_member(session: Session, member_id: int) -> list[int]:
    rows = session.scalars(
        select(MemberEntity.entity_id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
    ).all()

    result: list[int] = []
    seen: set[int] = set()

    for raw_id in rows:
        if raw_id is None:
            continue

        entity_id = int(raw_id)

        if entity_id in seen:
            continue

        seen.add(entity_id)
        result.append(entity_id)

    return result
''',
)

write_module_v1(
    "appverbo/repositories/user_profile_repository.py",
    r'''
from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from appverbo.models import UserProfile


def replace_user_profile(
    session: Session,
    user_id: int,
    profile_id: int,
    *,
    is_active: bool = True,
) -> None:
    session.execute(delete(UserProfile).where(UserProfile.user_id == int(user_id)))
    session.add(
        UserProfile(
            user_id=int(user_id),
            profile_id=int(profile_id),
            is_active=bool(is_active),
        )
    )


def delete_user_profiles(session: Session, user_id: int) -> None:
    session.execute(delete(UserProfile).where(UserProfile.user_id == int(user_id)))
''',
)


####################################################################################
# (4.2) USE CASES COMPARTILHADOS
####################################################################################

write_module_v1(
    "appverbo/use_cases/users/outcome.py",
    r'''
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UserActionOutcome:
    kind: str
    redirect_url: str = ""
    redirect_status_code: int = 303
    template_context: dict[str, Any] | None = None
    template_status_code: int = 400
''',
)

write_module_v1(
    "appverbo/use_cases/users/resolve_user_entity.py",
    r'''
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity
from appverbo.repositories.member_entity_repository import get_primary_entity_for_member


def extract_email_domain_v1(raw_email: str) -> str:
    clean_email = (raw_email or "").strip().lower()

    if "@" not in clean_email:
        return ""

    _, domain = clean_email.split("@", 1)
    return domain.strip()


def _allowed_entity_ids_v1(permissions: dict[str, Any]) -> set[int]:
    return {
        int(raw_id)
        for raw_id in (permissions.get("allowed_entity_ids") or set())
        if str(raw_id).strip().isdigit()
    }


def resolve_selected_entity_fallback_v1(
    session: Session,
    selected_entity_id: int | None,
    permissions: dict[str, Any],
) -> Entity | None:
    parsed_entity_id: int | None = None

    if selected_entity_id is not None:
        try:
            parsed_entity_id = int(selected_entity_id)
        except (TypeError, ValueError):
            parsed_entity_id = None

    if parsed_entity_id is not None and parsed_entity_id > 0:
        if not permissions.get("can_manage_all_entities"):
            allowed_ids = _allowed_entity_ids_v1(permissions)
            if parsed_entity_id not in allowed_ids:
                return None

        selected_entity = session.execute(
            select(Entity).where(
                Entity.id == parsed_entity_id,
                Entity.is_active.is_(True),
            )
        ).scalar_one_or_none()

        if selected_entity is not None:
            return selected_entity

    stmt = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())

    if not permissions.get("can_manage_all_entities"):
        allowed_ids = sorted(_allowed_entity_ids_v1(permissions))
        if not allowed_ids:
            return None
        stmt = stmt.where(Entity.id.in_(allowed_ids))

    return session.execute(stmt.limit(1)).scalar_one_or_none()


def resolve_entity_from_user_email_v1(
    session: Session,
    user_email: str,
    permissions: dict[str, Any],
    selected_entity_id: int | None = None,
) -> tuple[Entity | None, str]:
    clean_email = (user_email or "").strip().lower()

    if clean_email and "@" in clean_email:
        stmt = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())

        if not permissions.get("can_manage_all_entities"):
            allowed_ids = sorted(_allowed_entity_ids_v1(permissions))
            if allowed_ids:
                stmt = stmt.where(Entity.id.in_(allowed_ids))
            else:
                return None, "Sem entidades disponíveis para este utilizador."

        entities = list(session.execute(stmt).scalars().all())

        exact_matches = [
            entity
            for entity in entities
            if (entity.email or "").strip().lower() == clean_email
        ]

        if len(exact_matches) == 1:
            return exact_matches[0], ""

        if len(exact_matches) > 1:
            return None, "Existem múltiplas entidades com o mesmo email. Corrija os dados das entidades."

        email_domain = extract_email_domain_v1(clean_email)

        if email_domain:
            domain_matches = [
                entity
                for entity in entities
                if extract_email_domain_v1(entity.email or "") == email_domain
            ]

            if len(domain_matches) == 1:
                return domain_matches[0], ""

            if len(domain_matches) > 1:
                return None, "Existem múltiplas entidades com este domínio de email. Ajuste o email das entidades."

    fallback_entity = resolve_selected_entity_fallback_v1(
        session=session,
        selected_entity_id=selected_entity_id,
        permissions=permissions,
    )

    if fallback_entity is not None:
        return fallback_entity, ""

    return None, "Não foi possível determinar uma entidade ativa para este convite."


def resolve_edit_entity_v1(
    session: Session,
    *,
    email: str,
    clean_entity_id: str,
    member_id: int,
    permissions: dict[str, Any],
) -> tuple[Entity | None, str]:
    selected_entity, error = resolve_entity_from_user_email_v1(
        session=session,
        user_email=email,
        permissions=permissions,
        selected_entity_id=None,
    )

    if selected_entity is not None:
        return selected_entity, ""

    if clean_entity_id.strip().isdigit():
        explicit_entity = session.get(Entity, int(clean_entity_id))

        if explicit_entity is not None:
            can_use = bool(permissions.get("can_manage_all_entities"))

            if not can_use:
                can_use = int(explicit_entity.id) in _allowed_entity_ids_v1(permissions)

            if can_use:
                return explicit_entity, ""

    current_entity_stmt = (
        select(Entity)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(MemberEntity.member_id == int(member_id))
        .order_by(MemberEntity.id.asc())
    )

    if not permissions.get("can_manage_all_entities"):
        allowed_ids = sorted(_allowed_entity_ids_v1(permissions))

        if allowed_ids:
            current_entity_stmt = current_entity_stmt.where(Entity.id.in_(allowed_ids))
        else:
            current_entity_stmt = current_entity_stmt.where(Entity.id == -1)

    current_entity = session.execute(current_entity_stmt.limit(1)).scalar_one_or_none()

    if current_entity is not None:
        return current_entity, ""

    current_entity_id, current_entity_name = get_primary_entity_for_member(session, member_id)
    if current_entity_id is not None:
        entity = session.get(Entity, current_entity_id)
        if entity is not None:
            return entity, ""

    return None, error
''',
)

write_module_v1(
    "appverbo/use_cases/users/user_permissions.py",
    r'''
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, MemberEntityStatus, Profile, User, UserAccountStatus
from appverbo.repositories.member_entity_repository import get_active_entity_ids_for_member
from appverbo.services.auth import is_admin_user


def allowed_entity_ids_v1(permissions: dict[str, Any]) -> set[int]:
    return {
        int(raw_id)
        for raw_id in (permissions.get("allowed_entity_ids") or set())
        if str(raw_id).strip().isdigit()
    }


def member_is_within_permissions_v1(
    session: Session,
    member_id: int,
    permissions: dict[str, Any],
) -> bool:
    if permissions.get("can_manage_all_entities"):
        return True

    allowed_ids = sorted(allowed_entity_ids_v1(permissions))

    if not allowed_ids:
        return False

    scoped_link_id = session.scalar(
        select(MemberEntity.id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            MemberEntity.entity_id.in_(allowed_ids),
        )
        .limit(1)
    )

    return scoped_link_id is not None


def is_admin_profile_v1(profile: Profile | None) -> bool:
    if profile is None:
        return False

    clean_name = (profile.name or "").strip().lower()

    return clean_name in {"admin", "administrador"}


def _has_other_active_admin_for_entity_v1(
    session: Session,
    entity_id: int,
    excluded_user_id: int,
) -> bool:
    rows = session.execute(
        select(User.id, User.login_email)
        .join(MemberEntity, MemberEntity.member_id == User.member_id)
        .where(
            MemberEntity.entity_id == int(entity_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            User.id != int(excluded_user_id),
            User.account_status == UserAccountStatus.ACTIVE.value,
        )
        .order_by(User.id.asc())
    ).all()

    for row in rows:
        if is_admin_user(session, int(row.id), str(row.login_email or "")):
            return True

    return False


def ensure_not_last_active_admin_for_member_v1(
    session: Session,
    member_id: int,
    excluded_user_id: int,
) -> tuple[bool, str]:
    entity_ids = get_active_entity_ids_for_member(session, int(member_id))

    if not entity_ids:
        return True, ""

    for entity_id in entity_ids:
        if _has_other_active_admin_for_entity_v1(session, entity_id, excluded_user_id):
            continue

        entity_name = session.scalar(
            select(Entity.name).where(Entity.id == int(entity_id)).limit(1)
        )
        display_name = str(entity_name or f"ID {entity_id}")

        return (
            False,
            (
                "Tem de existir pelo menos um Admin ativo por entidade. "
                f"A entidade '{display_name}' ficaria sem Admin ativo."
            ),
        )

    return True, ""
''',
)

write_module_v1(
    "appverbo/use_cases/users/user_invites.py",
    r'''
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
''',
)


####################################################################################
# (4.3) CREATE USER USE CASE
####################################################################################

write_module_v1(
    "appverbo/use_cases/users/create_user.py",
    r'''
from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.models import Member, MemberStatus, Profile, User, UserAccountStatus
from appverbo.repositories.member_entity_repository import get_primary_entity_for_member, upsert_active_member_entity_link
from appverbo.repositories.member_repository import get_member_by_email_ci
from appverbo.repositories.user_profile_repository import replace_user_profile
from appverbo.repositories.user_repository import get_user_by_email_ci
from appverbo.services.auth import (
    build_user_invite_link,
    build_user_invite_token,
    get_or_create_entity_superuser_profile,
    hash_password,
    is_admin_user,
    is_allowed_global_profile,
    send_user_invite_email,
)
from appverbo.services.page import (
    build_users_new_url,
    get_entity_edit_defaults,
    get_entity_form_defaults,
    get_next_entity_internal_number,
    get_page_data,
    get_user_edit_defaults,
)
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.profile import get_user_personal_data
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.resolve_user_entity import resolve_entity_from_user_email_v1
from appverbo.use_cases.users.user_permissions import member_is_within_permissions_v1


@dataclass(frozen=True)
class CreateUserInput:
    clean_full_name: str
    clean_primary_phone: str
    clean_email: str
    clean_profile_id: str
    clean_invite_delivery: str
    form_data: dict[str, str]
    errors: list[str]


CreateUserOutcome = UserActionOutcome


def normalize_create_user_input_v1(
    *,
    full_name: str,
    primary_phone: str,
    email: str,
    profile_id: str,
    invite_delivery: str,
) -> CreateUserInput:
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_profile_id = profile_id.strip()
    clean_invite_delivery = invite_delivery.strip().lower()

    if clean_invite_delivery not in {"email", "link"}:
        clean_invite_delivery = "email"

    form_data = {
        "full_name": clean_full_name,
        "primary_phone": clean_primary_phone,
        "email": clean_email,
        "entity_id": "",
        "entity_name": "",
        "profile_id": clean_profile_id,
    }

    errors: list[str] = []

    if not clean_full_name:
        errors.append("Nome completo é obrigatório.")

    if not clean_primary_phone:
        errors.append("Telefone principal é obrigatório.")

    if not clean_email:
        errors.append("Email é obrigatório.")

    return CreateUserInput(
        clean_full_name=clean_full_name,
        clean_primary_phone=clean_primary_phone,
        clean_email=clean_email,
        clean_profile_id=clean_profile_id,
        clean_invite_delivery=clean_invite_delivery,
        form_data=form_data,
        errors=errors,
    )


normalize_create_user_input = normalize_create_user_input_v1


def _build_error_context_v1(
    *,
    request: Request,
    errors: list[str],
    form_data: dict[str, str],
    current_user: dict[str, Any],
    current_user_is_admin: bool,
    can_manage_all_entities: bool,
    user_personal_data: dict[str, Any],
    next_entity_internal_number: int,
    page_data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "request": request,
        "errors": errors,
        "success": "",
        "generated_invite_link": "",
        "form_data": form_data,
        "entity_form_data": get_entity_form_defaults(),
        "entity_edit_data": get_entity_edit_defaults(),
        "user_edit_data": get_user_edit_defaults(),
        "entity_readonly_mode": False,
        "user_readonly_mode": False,
        "current_user": current_user,
        "current_user_is_admin": current_user_is_admin,
        "current_user_can_manage_all_entities": bool(can_manage_all_entities),
        "user_personal_data": user_personal_data,
        "entity_success": "",
        "entity_error": "",
        "next_entity_internal_number": str(next_entity_internal_number),
        "profile_success": "",
        "profile_error": "",
        "settings_success": "",
        "settings_error": "",
        "settings_edit_data": None,
        "settings_edit_key": "",
        "settings_action": "edit",
        "settings_tab": "",
        "profile_tab": "pessoal",
        "initial_menu": "administrativo",
        "initial_menu_target": "#create-user-card",
        "initial_dynamic_process_section": "",
        "initial_profile_section": "",
        "requested_profile_section": "",
        "requested_dynamic_process_section": "",
        "appverbo_after_save": False,
        "admin_tab": "utilizador",
        **page_data,
    }


def execute_create_user(
    *,
    session: Session,
    request: Request,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: CreateUserInput,
) -> CreateUserOutcome:
    actor_user_id = int(actor_user["id"])
    actor_login_email = str(actor_user["login_email"])

    current_user_is_admin = bool(
        is_admin_user(session, actor_user_id, actor_login_email)
    )

    entity_permissions = get_user_entity_permissions(
        session,
        actor_user_id,
        actor_login_email,
        selected_entity_id,
    )

    page_data = get_page_data(
        session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
    )

    user_personal_data = get_user_personal_data(
        session,
        actor_user_id,
        selected_entity_id,
    )

    next_entity_internal_number = get_next_entity_internal_number(session)

    if not current_user_is_admin:
        return UserActionOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                error="Apenas administradores podem criar utilizadores.",
                menu="perfil",
            ),
        )

    errors = list(payload.errors)
    form_data = dict(payload.form_data)

    selected_entity, entity_resolution_error = resolve_entity_from_user_email_v1(
        session=session,
        user_email=payload.clean_email,
        permissions=entity_permissions,
        selected_entity_id=selected_entity_id,
    )

    if selected_entity is not None:
        form_data["entity_id"] = str(selected_entity.id)
        form_data["entity_name"] = selected_entity.name or ""
    elif entity_resolution_error:
        errors.append(entity_resolution_error)

    existing_member = get_member_by_email_ci(session, payload.clean_email)
    existing_user = get_user_by_email_ci(session, payload.clean_email)

    if existing_user is not None:
        existing_entity_id, existing_entity_name = get_primary_entity_for_member(
            session,
            int(existing_user.member_id),
        )
        can_manage_existing = member_is_within_permissions_v1(
            session=session,
            member_id=int(existing_user.member_id),
            permissions=entity_permissions,
        )

        if not can_manage_existing:
            errors.append("Sem permissão para gerir utilizador com este email.")
            existing_user = None
        else:
            linked_entity_name = (
                selected_entity.name
                if selected_entity is not None
                else existing_entity_name
            )
            linked_entity_id = (
                int(selected_entity.id)
                if selected_entity is not None
                else existing_entity_id
            )

            existing_status = str(existing_user.account_status or "").strip().lower()

            if existing_status == UserAccountStatus.PENDING.value:
                invite_token = build_user_invite_token(
                    int(existing_user.id),
                    str(existing_user.login_email),
                    linked_entity_id,
                )
                invite_link = build_user_invite_link(request, invite_token)

                if payload.clean_invite_delivery == "link":
                    return UserActionOutcome(
                        kind="redirect",
                        redirect_url=build_users_new_url(
                            success="Utilizador já estava pendente. Link de ativação gerado.",
                            invite_link=invite_link,
                            menu="administrativo",
                            admin_tab="utilizador",
                        )
                        + "#create-user-card",
                    )

                email_sent, email_error = send_user_invite_email(
                    recipient_email=payload.clean_email,
                    recipient_name=payload.clean_full_name,
                    entity_name=linked_entity_name,
                    invite_link=invite_link,
                    invited_by_name=str(actor_user["full_name"]),
                )

                if email_sent:
                    return UserActionOutcome(
                        kind="redirect",
                        redirect_url=build_users_new_url(
                            success="Utilizador já estava pendente. Convite reenviado por email.",
                            menu="administrativo",
                            admin_tab="utilizador",
                        )
                        + "#create-user-card",
                    )

                return UserActionOutcome(
                    kind="redirect",
                    redirect_url=build_users_new_url(
                        success="Utilizador já estava pendente.",
                        error=f"{email_error} Link de ativação: {invite_link}",
                        menu="administrativo",
                        admin_tab="utilizador",
                    )
                    + "#create-user-card",
                )

            errors.append("Já existe um utilizador com este email de login.")

    if existing_member is not None and existing_user is None:
        can_manage_member = member_is_within_permissions_v1(
            session=session,
            member_id=int(existing_member.id),
            permissions=entity_permissions,
        )
        existing_entity_id, _ = get_primary_entity_for_member(session, int(existing_member.id))

        if existing_entity_id is not None and not can_manage_member:
            errors.append("Sem permissão para utilizar este email noutra entidade.")
            existing_member = None

    selected_profile: Profile | None = None

    if payload.clean_profile_id:
        try:
            selected_profile = session.get(Profile, int(payload.clean_profile_id))
        except ValueError:
            errors.append("Perfil selecionado inválido.")

        if selected_profile is None and not errors:
            errors.append("Perfil selecionado não existe.")
        elif selected_profile is not None and not is_allowed_global_profile(selected_profile):
            errors.append("Perfil global inválido. Escolha ADMIN, SUPER USER ou USER.")

    if errors:
        return UserActionOutcome(
            kind="template",
            template_context=_build_error_context_v1(
                request=request,
                errors=errors,
                form_data=form_data,
                current_user=actor_user,
                current_user_is_admin=current_user_is_admin,
                can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
                user_personal_data=user_personal_data,
                next_entity_internal_number=next_entity_internal_number,
                page_data=page_data,
            ),
        )

    if selected_entity is None:
        return UserActionOutcome(
            kind="template",
            template_context=_build_error_context_v1(
                request=request,
                errors=["Não foi possível determinar a entidade do utilizador."],
                form_data=form_data,
                current_user=actor_user,
                current_user_is_admin=current_user_is_admin,
                can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
                user_personal_data=user_personal_data,
                next_entity_internal_number=next_entity_internal_number,
                page_data=page_data,
            ),
        )

    if selected_profile is None:
        selected_profile = get_or_create_entity_superuser_profile(session)

    if existing_member is None:
        member = Member(
            full_name=payload.clean_full_name,
            primary_phone=payload.clean_primary_phone,
            email=payload.clean_email,
            member_status=MemberStatus.ACTIVE.value,
            is_collaborator=True,
        )
        session.add(member)
        session.flush()
    else:
        member = existing_member
        member.full_name = payload.clean_full_name
        member.primary_phone = payload.clean_primary_phone
        member.email = payload.clean_email
        member.member_status = MemberStatus.ACTIVE.value
        member.is_collaborator = True

    upsert_active_member_entity_link(
        session=session,
        member_id=int(member.id),
        entity_id=int(selected_entity.id),
        replace_primary=False,
    )

    user = User(
        member_id=int(member.id),
        login_email=payload.clean_email,
        password_hash=hash_password(secrets.token_urlsafe(24)),
        account_status=UserAccountStatus.PENDING.value,
        created_by_user_id=actor_user_id,
    )
    session.add(user)
    session.flush()

    replace_user_profile(
        session=session,
        user_id=int(user.id),
        profile_id=int(selected_profile.id),
        is_active=True,
    )

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return UserActionOutcome(
            kind="template",
            template_context=_build_error_context_v1(
                request=request,
                errors=[
                    "Falha ao gravar no banco. Verifique dados duplicados e tente novamente."
                ],
                form_data=form_data,
                current_user=actor_user,
                current_user_is_admin=current_user_is_admin,
                can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
                user_personal_data=user_personal_data,
                next_entity_internal_number=next_entity_internal_number,
                page_data=page_data,
            ),
        )

    invite_token = build_user_invite_token(
        int(user.id),
        str(user.login_email),
        int(selected_entity.id),
    )
    invite_link = build_user_invite_link(request, invite_token)

    if payload.clean_invite_delivery == "link":
        return UserActionOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                success="Utilizador criado em estado pendente. Link de ativação gerado.",
                invite_link=invite_link,
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
        )

    email_sent, email_error = send_user_invite_email(
        recipient_email=payload.clean_email,
        recipient_name=payload.clean_full_name,
        entity_name=selected_entity.name or "",
        invite_link=invite_link,
        invited_by_name=str(actor_user["full_name"]),
    )

    if email_sent:
        return UserActionOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                success="Utilizador criado em estado pendente. Convite enviado por email.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
        )

    return UserActionOutcome(
        kind="redirect",
        redirect_url=build_users_new_url(
            success="Utilizador criado em estado pendente.",
            error=f"{email_error} Link de ativação: {invite_link}",
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
    )
''',
)


####################################################################################
# (4.4) UPDATE USER USE CASE
####################################################################################

write_module_v1(
    "appverbo/use_cases/users/update_user.py",
    r'''
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.models import Profile, UserAccountStatus
from appverbo.repositories.member_entity_repository import upsert_active_member_entity_link
from appverbo.repositories.member_repository import get_duplicate_member_id_by_email_ci, get_member_by_id
from appverbo.repositories.user_profile_repository import replace_user_profile
from appverbo.repositories.user_repository import get_duplicate_user_id_by_email_ci, get_user_by_id
from appverbo.services.auth import get_or_create_entity_superuser_profile, is_admin_user, is_allowed_global_profile
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.resolve_user_entity import resolve_edit_entity_v1
from appverbo.use_cases.users.user_permissions import (
    ensure_not_last_active_admin_for_member_v1,
    is_admin_profile_v1,
    member_is_within_permissions_v1,
)


ALLOWED_ACCOUNT_STATUS = {
    UserAccountStatus.ACTIVE.value,
    UserAccountStatus.PENDING.value,
    UserAccountStatus.INACTIVE.value,
}


@dataclass(frozen=True)
class UpdateUserInput:
    clean_user_id: str
    clean_full_name: str
    clean_primary_phone: str
    clean_email: str
    clean_entity_id: str
    clean_account_status: str
    clean_profile_id: str
    errors: list[str]


def normalize_update_user_input_v1(
    *,
    user_id: str,
    full_name: str,
    primary_phone: str,
    email: str,
    entity_id: str,
    account_status: str,
    profile_id: str,
) -> UpdateUserInput:
    clean_user_id = user_id.strip()
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_entity_id = entity_id.strip()
    clean_account_status = account_status.strip().lower()
    clean_profile_id = profile_id.strip()

    errors: list[str] = []

    if not clean_user_id.isdigit():
        errors.append("Utilizador inválido para edição.")

    if not clean_full_name:
        errors.append("Nome completo é obrigatório.")

    if not clean_primary_phone:
        errors.append("Telefone principal é obrigatório.")

    if not clean_email:
        errors.append("Email é obrigatório.")

    if clean_account_status not in ALLOWED_ACCOUNT_STATUS:
        errors.append("Estado de conta inválido.")

    return UpdateUserInput(
        clean_user_id=clean_user_id,
        clean_full_name=clean_full_name,
        clean_primary_phone=clean_primary_phone,
        clean_email=clean_email,
        clean_entity_id=clean_entity_id,
        clean_account_status=clean_account_status,
        clean_profile_id=clean_profile_id,
        errors=errors,
    )


def _redirect_v1(
    *,
    success: str = "",
    error: str = "",
    user_edit_id: str = "",
    anchor: str = "#create-user-card",
) -> UserActionOutcome:
    kwargs: dict[str, str] = {
        "success": success,
        "error": error,
        "menu": "administrativo",
        "admin_tab": "utilizador",
    }

    if user_edit_id:
        kwargs["user_edit_id"] = user_edit_id

    return UserActionOutcome(
        kind="redirect",
        redirect_url=build_users_new_url(**kwargs) + anchor,
    )


def execute_update_user(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: UpdateUserInput,
) -> UserActionOutcome:
    if payload.errors and not payload.clean_user_id.isdigit():
        return _redirect_v1(error=" ".join(payload.errors))

    parsed_user_id = int(payload.clean_user_id)

    if not is_admin_user(session, int(actor_user["id"]), str(actor_user["login_email"])):
        return _redirect_v1(error="Apenas administradores podem editar utilizadores.")

    entity_permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    user = get_user_by_id(session, parsed_user_id)

    if user is None:
        return _redirect_v1(error="Utilizador não encontrado.")

    if not member_is_within_permissions_v1(
        session=session,
        member_id=int(user.member_id),
        permissions=entity_permissions,
    ):
        return _redirect_v1(error="Sem permissão para editar este utilizador.")

    member = get_member_by_id(session, int(user.member_id))

    if member is None:
        return _redirect_v1(error="Membro associado ao utilizador não encontrado.")

    errors = list(payload.errors)

    selected_entity, entity_resolution_error = resolve_edit_entity_v1(
        session=session,
        email=payload.clean_email,
        clean_entity_id=payload.clean_entity_id,
        member_id=int(member.id),
        permissions=entity_permissions,
    )

    if selected_entity is None and entity_resolution_error:
        errors.append(entity_resolution_error)

    selected_profile: Profile | None = None

    if payload.clean_profile_id:
        try:
            selected_profile = session.get(Profile, int(payload.clean_profile_id))
        except ValueError:
            errors.append("Perfil selecionado inválido.")

        if selected_profile is None and not errors:
            errors.append("Perfil selecionado não existe.")
        elif selected_profile is not None and not is_allowed_global_profile(selected_profile):
            errors.append("Perfil global inválido. Escolha ADMIN, SUPER USER ou USER.")

    duplicate_member_id = get_duplicate_member_id_by_email_ci(
        session=session,
        email=payload.clean_email,
        excluded_member_id=int(member.id),
    )

    if duplicate_member_id is not None:
        errors.append("Já existe um membro com este email.")

    duplicate_user_id = get_duplicate_user_id_by_email_ci(
        session=session,
        login_email=payload.clean_email,
        excluded_user_id=int(user.id),
    )

    if duplicate_user_id is not None:
        errors.append("Já existe um utilizador com este email de login.")

    if errors:
        return _redirect_v1(
            error=" ".join(errors),
            user_edit_id=str(parsed_user_id),
            anchor="#edit-user-card",
        )

    if selected_profile is None:
        selected_profile = get_or_create_entity_superuser_profile(session)

    current_is_active_admin = (
        str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
        and is_admin_user(session, int(user.id), str(user.login_email or ""))
    )
    resulting_is_active_admin = (
        payload.clean_account_status == UserAccountStatus.ACTIVE.value
        and is_admin_profile_v1(selected_profile)
    )

    if current_is_active_admin and not resulting_is_active_admin:
        can_change, admin_error = ensure_not_last_active_admin_for_member_v1(
            session=session,
            member_id=int(user.member_id),
            excluded_user_id=int(user.id),
        )

        if not can_change:
            return _redirect_v1(
                error=admin_error,
                user_edit_id=str(parsed_user_id),
                anchor="#edit-user-card",
            )

    member.full_name = payload.clean_full_name
    member.primary_phone = payload.clean_primary_phone
    member.email = payload.clean_email

    user.login_email = payload.clean_email
    user.account_status = payload.clean_account_status

    if selected_entity is not None:
        upsert_active_member_entity_link(
            session=session,
            member_id=int(member.id),
            entity_id=int(selected_entity.id),
            replace_primary=True,
        )

    replace_user_profile(
        session=session,
        user_id=int(user.id),
        profile_id=int(selected_profile.id),
        is_active=True,
    )

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return _redirect_v1(
            error="Não foi possível atualizar utilizador.",
            user_edit_id=str(parsed_user_id),
            anchor="#edit-user-card",
        )

    return _redirect_v1(success="Utilizador atualizado com sucesso.")
''',
)


####################################################################################
# (4.5) DELETE USER USE CASE
####################################################################################

write_module_v1(
    "appverbo/use_cases/users/delete_user.py",
    r'''
from __future__ import annotations

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.repositories.user_profile_repository import delete_user_profiles
from appverbo.repositories.user_repository import get_user_by_id, null_created_by_for_deleted_user
from appverbo.services.auth import is_admin_user
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.user_status import is_user_account_status_inactive_v1
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.user_permissions import member_is_within_permissions_v1


def _redirect_v1(success: str = "", error: str = "") -> UserActionOutcome:
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


def execute_delete_user(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    user_id: int,
) -> UserActionOutcome:
    parsed_user_id = int(user_id)

    if not is_admin_user(session, int(actor_user["id"]), str(actor_user["login_email"])):
        return _redirect_v1(error="Apenas administradores podem eliminar utilizadores.")

    if parsed_user_id == int(actor_user["id"]):
        return _redirect_v1(error="Não é permitido eliminar o próprio utilizador ligado.")

    entity_permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    user = get_user_by_id(session, parsed_user_id)

    if user is None:
        return _redirect_v1(error="Utilizador não encontrado.")

    if not member_is_within_permissions_v1(
        session=session,
        member_id=int(user.member_id),
        permissions=entity_permissions,
    ):
        return _redirect_v1(error="Sem permissão para eliminar este utilizador.")

    if not is_user_account_status_inactive_v1(user.account_status):
        return _redirect_v1(error="Só é permitido eliminar utilizadores inativos.")

    null_created_by_for_deleted_user(session, parsed_user_id)
    delete_user_profiles(session, parsed_user_id)
    session.delete(user)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return _redirect_v1(error="Não foi possível eliminar utilizador.")

    return _redirect_v1(success="Utilizador eliminado com sucesso.")
''',
)


####################################################################################
# (4.6) OUTROS USE CASES DO DOMÍNIO UTILIZADOR
####################################################################################

write_module_v1(
    "appverbo/use_cases/users/list_admin_users.py",
    r'''
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.services.page import get_page_data


def list_admin_users_v1(
    session: Session,
    *,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
) -> dict[str, Any]:
    page_data = get_page_data(
        session,
        actor_user_id=int(actor_user_id),
        actor_login_email=str(actor_login_email),
        selected_entity_id=selected_entity_id,
    )

    return {
        "created_users": page_data.get("created_users", []),
        "active_created_users": page_data.get("active_created_users", []),
        "inactive_users": page_data.get("inactive_users", []),
        "pending_users": page_data.get("pending_users", []),
    }
''',
)

write_module_v1(
    "appverbo/use_cases/users/get_user_edit_data.py",
    r'''
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.services.page import get_page_data, get_user_edit_defaults


def get_user_edit_data_v1(
    session: Session,
    *,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
    user_edit_id: int | None,
) -> dict[str, Any]:
    if user_edit_id is None:
        return get_user_edit_defaults()

    page_data = get_page_data(
        session,
        actor_user_id=int(actor_user_id),
        actor_login_email=str(actor_login_email),
        selected_entity_id=selected_entity_id,
    )

    return page_data.get("user_edit_data") or get_user_edit_defaults()
''',
)


####################################################################################
# (4.7) INIT DO PACOTE USE_CASES.USERS
####################################################################################

write_module_v1(
    "appverbo/use_cases/users/__init__.py",
    r'''
from __future__ import annotations

from appverbo.use_cases.users.create_user import (
    CreateUserInput,
    CreateUserOutcome,
    execute_create_user,
    normalize_create_user_input,
    normalize_create_user_input_v1,
)
from appverbo.use_cases.users.delete_user import execute_delete_user
from appverbo.use_cases.users.get_user_edit_data import get_user_edit_data_v1
from appverbo.use_cases.users.list_admin_users import list_admin_users_v1
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.resolve_user_entity import (
    extract_email_domain_v1,
    resolve_edit_entity_v1,
    resolve_entity_from_user_email_v1,
)
from appverbo.use_cases.users.update_user import (
    UpdateUserInput,
    execute_update_user,
    normalize_update_user_input_v1,
)
from appverbo.use_cases.users.user_invites import (
    prepare_user_invite_payload_v1,
    redirect_admin_users_v1,
    send_user_invite_v1,
)
from appverbo.use_cases.users.user_permissions import (
    ensure_not_last_active_admin_for_member_v1,
    is_admin_profile_v1,
    member_is_within_permissions_v1,
)

__all__ = [
    "CreateUserInput",
    "CreateUserOutcome",
    "UpdateUserInput",
    "UserActionOutcome",
    "execute_create_user",
    "execute_delete_user",
    "execute_update_user",
    "extract_email_domain_v1",
    "get_user_edit_data_v1",
    "list_admin_users_v1",
    "normalize_create_user_input",
    "normalize_create_user_input_v1",
    "normalize_update_user_input_v1",
    "prepare_user_invite_payload_v1",
    "redirect_admin_users_v1",
    "resolve_edit_entity_v1",
    "resolve_entity_from_user_email_v1",
    "send_user_invite_v1",
    "ensure_not_last_active_admin_for_member_v1",
    "is_admin_profile_v1",
    "member_is_within_permissions_v1",
]
''',
)


####################################################################################
# (4.8) HELPERS COMO COMPATIBILIDADE
####################################################################################

write_module_v1(
    "appverbo/routes/users/helpers.py",
    r'''
from __future__ import annotations

from appverbo.repositories.member_entity_repository import get_primary_entity_for_member
from appverbo.use_cases.users.resolve_user_entity import (
    extract_email_domain_v1,
    resolve_entity_from_user_email_v1,
)
from appverbo.use_cases.users.user_permissions import (
    ensure_not_last_active_admin_for_member_v1,
    is_admin_profile_v1,
    member_is_within_permissions_v1,
)


_extract_email_domain = extract_email_domain_v1
_resolve_entity_from_user_email = resolve_entity_from_user_email_v1
_get_primary_entity_for_member = get_primary_entity_for_member
_member_is_within_permissions = member_is_within_permissions_v1
_is_admin_profile = is_admin_profile_v1
_ensure_not_last_active_admin_for_member = ensure_not_last_active_admin_for_member_v1


def _get_primary_entity_name_for_member(session, member_id: int) -> str:
    _, entity_name = get_primary_entity_for_member(session, int(member_id))
    return entity_name
''',
)


####################################################################################
# (4.9) HANDLERS FINOS
####################################################################################

write_module_v1(
    "appverbo/routes/users/update_handler.py",
    r'''
from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.models import UserAccountStatus
from appverbo.routes.users.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.users import execute_update_user, normalize_update_user_input_v1


logger = logging.getLogger(__name__)


@router.post("/users/update", response_class=HTMLResponse)
def update_user_v1(
    request: Request,
    user_id: str = Form(...),
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    entity_id: str = Form(""),
    account_status: str = Form(UserAccountStatus.ACTIVE.value),
    profile_id: str = Form(""),
) -> RedirectResponse:
    try:
        payload = normalize_update_user_input_v1(
            user_id=user_id,
            full_name=full_name,
            primary_phone=primary_phone,
            email=email,
            entity_id=entity_id,
            account_status=account_status,
            profile_id=profile_id,
        )

        with SessionLocal() as session:
            current_user = get_current_user(request, session)

            if current_user is None:
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            outcome = execute_update_user(
                session=session,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                payload=payload,
            )

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "Erro inesperado ao atualizar utilizador: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=build_users_new_url(
                error="Erro ao atualizar utilizador. Consulte os logs recentes do serviço web.",
                menu="administrativo",
                admin_tab="utilizador",
                user_edit_id=user_id,
            )
            + "#edit-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )


update_user = update_user_v1
''',
)

write_module_v1(
    "appverbo/routes/users/delete_handler.py",
    r'''
from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.users.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.users import execute_delete_user


logger = logging.getLogger(__name__)


@router.post("/users/delete", response_class=HTMLResponse)
def delete_user_v1(
    request: Request,
    user_id: str = Form(...),
) -> RedirectResponse:
    clean_user_id = user_id.strip()

    if not clean_user_id.isdigit():
        return RedirectResponse(
            url=build_users_new_url(
                error="Utilizador inválido para eliminação.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        with SessionLocal() as session:
            current_user = get_current_user(request, session)

            if current_user is None:
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            outcome = execute_delete_user(
                session=session,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                user_id=int(clean_user_id),
            )

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "Erro inesperado ao eliminar utilizador: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=build_users_new_url(
                error="Erro ao eliminar utilizador. Consulte os logs recentes do serviço web.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )


delete_user = delete_user_v1
''',
)

write_module_v1(
    "appverbo/routes/users/resend_handler.py",
    r'''
from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.users.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.users import (
    prepare_user_invite_payload_v1,
    redirect_admin_users_v1,
    send_user_invite_v1,
)


logger = logging.getLogger(__name__)


def _generate_user_invite_v1(
    *,
    request: Request,
    user_id: str,
    raw_entity_id: str = "",
) -> RedirectResponse:
    clean_user_id = user_id.strip()

    if not clean_user_id.isdigit():
        outcome = redirect_admin_users_v1(error="Utilizador inválido para gerar convite.")
        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    try:
        with SessionLocal() as session:
            current_user = get_current_user(request, session)

            if current_user is None:
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            payload, early_outcome = prepare_user_invite_payload_v1(
                session=session,
                request=request,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                user_id=int(clean_user_id),
                raw_entity_id=raw_entity_id,
            )

        if early_outcome is not None:
            return RedirectResponse(
                url=early_outcome.redirect_url,
                status_code=early_outcome.redirect_status_code,
            )

        if payload is None:
            outcome = redirect_admin_users_v1(error="Não foi possível gerar convite.")
        else:
            outcome = send_user_invite_v1(payload)

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "Erro inesperado ao gerar convite: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=build_users_new_url(
                error="Erro ao gerar convite. Consulte os logs recentes do serviço web.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/users/generate-invite", response_class=HTMLResponse)
def generate_user_invite_v1(
    request: Request,
    user_id: str = Form(...),
    entity_id: str = Form(""),
) -> RedirectResponse:
    return _generate_user_invite_v1(
        request=request,
        user_id=user_id,
        raw_entity_id=entity_id,
    )


@router.post("/users/resend-invite", response_class=HTMLResponse)
def resend_user_invite_v1(
    request: Request,
    user_id: str = Form(...),
) -> RedirectResponse:
    return _generate_user_invite_v1(
        request=request,
        user_id=user_id,
        raw_entity_id="",
    )


generate_user_invite = generate_user_invite_v1
resend_user_invite = resend_user_invite_v1
''',
)


####################################################################################
# (4.10) EXTRAIR PARTIALS DO TEMPLATE
####################################################################################

def find_section_range_v1(content: str, section_id: str) -> tuple[int, int] | None:
    opening = re.search(
        r'<section\b[^>]*\bid=(["\'])' + re.escape(section_id) + r'\1[^>]*>',
        content,
        flags=re.I,
    )

    if opening is None:
        return None

    index = opening.end()
    depth = 1

    token_re = re.compile(r'<section\b[^>]*>|</section>', flags=re.I)

    for token in token_re.finditer(content, index):
        token_text = token.group(0).lower()

        if token_text.startswith("<section"):
            depth += 1
        else:
            depth -= 1

        if depth == 0:
            return opening.start(), token.end()

    return None


def extract_or_create_partial_v1(
    *,
    template_path: str,
    section_id: str,
    partial_path: str,
    include_line: str,
    required: bool,
) -> None:
    content = read_text_v1(template_path)

    if include_line in content:
        return

    section_range = find_section_range_v1(content, section_id)

    if section_range is None:
        if required:
            raise RuntimeError(f"ERRO: secção #{section_id} não encontrada em {template_path}.")
        return

    start, end = section_range
    block = content[start:end]

    write_text_v1(partial_path, block)

    new_content = content[:start] + include_line + content[end:]
    write_text_v1(template_path, new_content)


extract_or_create_partial_v1(
    template_path="templates/new_user.html",
    section_id="create-user-card",
    partial_path="templates/admin/users/create_user_card.html",
    include_line='{% include "admin/users/create_user_card.html" %}',
    required=True,
)

extract_or_create_partial_v1(
    template_path="templates/new_user.html",
    section_id="edit-user-card",
    partial_path="templates/admin/users/edit_user_card.html",
    include_line='{% include "admin/users/edit_user_card.html" %}',
    required=True,
)

extract_or_create_partial_v1(
    template_path="templates/new_user.html",
    section_id="admin-users-created-card",
    partial_path="templates/admin/users/active_users_card.html",
    include_line='{% include "admin/users/active_users_card.html" %}',
    required=False,
)

extract_or_create_partial_v1(
    template_path="templates/new_user.html",
    section_id="inactive-users-card",
    partial_path="templates/admin/users/inactive_users_card.html",
    include_line='{% include "admin/users/inactive_users_card.html" %}',
    required=False,
)


####################################################################################
# (4.11) VALIDAR CONTEÚDO GERADO
####################################################################################

expected_files = [
    "appverbo/repositories/user_repository.py",
    "appverbo/repositories/member_repository.py",
    "appverbo/repositories/member_entity_repository.py",
    "appverbo/repositories/user_profile_repository.py",
    "appverbo/use_cases/users/outcome.py",
    "appverbo/use_cases/users/create_user.py",
    "appverbo/use_cases/users/update_user.py",
    "appverbo/use_cases/users/delete_user.py",
    "appverbo/use_cases/users/user_invites.py",
    "appverbo/use_cases/users/user_permissions.py",
    "appverbo/use_cases/users/resolve_user_entity.py",
    "appverbo/use_cases/users/list_admin_users.py",
    "appverbo/use_cases/users/get_user_edit_data.py",
    "appverbo/use_cases/users/__init__.py",
    "appverbo/routes/users/helpers.py",
    "appverbo/routes/users/update_handler.py",
    "appverbo/routes/users/delete_handler.py",
    "appverbo/routes/users/resend_handler.py",
    "templates/admin/users/create_user_card.html",
    "templates/admin/users/edit_user_card.html",
]

for file_name in expected_files:
    require_v1((ROOT / file_name).exists(), f"ERRO: ficheiro não criado: {file_name}")

content_update_handler = read_text_v1("appverbo/routes/users/update_handler.py")
content_delete_handler = read_text_v1("appverbo/routes/users/delete_handler.py")
content_resend_handler = read_text_v1("appverbo/routes/users/resend_handler.py")
content_template = read_text_v1("templates/new_user.html")

require_v1("execute_update_user" in content_update_handler, "ERRO: update_handler não chama execute_update_user.")
require_v1("execute_delete_user" in content_delete_handler, "ERRO: delete_handler não chama execute_delete_user.")
require_v1("prepare_user_invite_payload_v1" in content_resend_handler, "ERRO: resend_handler não usa user_invites.")
require_v1('{% include "admin/users/create_user_card.html" %}' in content_template, "ERRO: include create_user_card não aplicado.")
require_v1('{% include "admin/users/edit_user_card.html" %}' in content_template, "ERRO: include edit_user_card não aplicado.")

print("OK: refatoração total do subprocesso Utilizador aplicada.")
