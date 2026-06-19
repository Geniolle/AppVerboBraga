from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from fastapi import Request, status
from fastapi.responses import RedirectResponse
from appverbo.admin_subprocesses.utilizador.common import (
    ensure_not_last_active_admin_for_member_v1,
    is_admin_profile_v1,
    member_is_within_permissions_v1,
)
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.core import (
    ALLOWED_ACCOUNT_STATUS,
    SessionLocal,
)
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    Profile,
    User,
    UserAccountStatus,
    UserProfile,
)
from appverbo.services.auth import (
    get_or_create_entity_superuser_profile,
    is_admin_user,
    is_allowed_global_profile,
)
from appverbo.services.user_member import member_status_for_user_account_status
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_current_user, get_session_entity_id


# ###################################################################################
# (1) MODELOS DE ENTRADA DO SUBPROCESSO UTILIZADOR
# ###################################################################################

@dataclass(frozen=True)
class UpdateUserInput:
    raw_user_id: str
    clean_user_id: str
    parsed_user_id: int | None
    clean_full_name: str
    clean_primary_phone: str
    clean_email: str
    clean_entity_id: str
    clean_account_status: str
    clean_profile_id: str


# ###################################################################################
# (2) NORMALIZACAO DA ENTRADA
# ###################################################################################

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
    clean_user_id = str(user_id or "").strip()
    parsed_user_id = int(clean_user_id) if clean_user_id.isdigit() else None

    return UpdateUserInput(
        raw_user_id=str(user_id or ""),
        clean_user_id=clean_user_id,
        parsed_user_id=parsed_user_id,
        clean_full_name=str(full_name or "").strip(),
        clean_primary_phone=str(primary_phone or "").strip(),
        clean_email=str(email or "").strip().lower(),
        clean_entity_id=str(entity_id or "").strip(),
        clean_account_status=str(account_status or "").strip().lower(),
        clean_profile_id=str(profile_id or "").strip(),
    )


# ###################################################################################
# (3) HELPERS LOCAIS SEM DEPENDER DE rotas
# ###################################################################################

def _extract_email_domain_v1(raw_email: str) -> str:
    clean_email = (raw_email or "").strip().lower()

    if "@" not in clean_email:
        return ""

    _, domain = clean_email.split("@", 1)
    return domain.strip()


def _resolve_entity_from_user_email_v1(
    session: Session,
    user_email: str,
    permissions: dict[str, Any],
) -> tuple[Entity | None, str]:
    clean_email = (user_email or "").strip().lower()

    if not clean_email or "@" not in clean_email:
        return None, "Email inv\u00e1lido para determinar entidade."

    query = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())

    if not permissions.get("can_manage_all_entities"):
        allowed_entity_ids = sorted(set(permissions.get("allowed_entity_ids") or set()))

        if not allowed_entity_ids:
            return None, "Sem entidades dispon\u00edveis para este utilizador."

        query = query.where(Entity.id.in_(allowed_entity_ids))

    scoped_entities = list(session.execute(query).scalars().all())

    if not scoped_entities:
        return None, "Sem entidades ativas dispon\u00edveis para atribui\u00e7\u00e3o."

    exact_matches = [
        entity
        for entity in scoped_entities
        if (entity.email or "").strip().lower() == clean_email
    ]

    if len(exact_matches) == 1:
        return exact_matches[0], ""

    if len(exact_matches) > 1:
        return (
            None,
            "Existem m\u00faltiplas entidades com o mesmo email. Corrija os dados das entidades.",
        )

    email_domain = _extract_email_domain_v1(clean_email)

    if email_domain:
        domain_matches = [
            entity
            for entity in scoped_entities
            if _extract_email_domain_v1((entity.email or "").strip().lower()) == email_domain
        ]

        if len(domain_matches) == 1:
            return domain_matches[0], ""

        if len(domain_matches) > 1:
            return (
                None,
                "Existem m\u00faltiplas entidades com este dom\u00ednio de email. Ajuste o email das entidades.",
            )

    if not permissions.get("can_manage_all_entities") and len(scoped_entities) == 1:
        return scoped_entities[0], ""

    return (
        None,
        "N\u00e3o foi poss\u00edvel determinar a entidade pelo email. "
        "Verifique o email da entidade ou ajuste os dados.",
    )

# ###################################################################################
# (4) REDIRECTS PADRAO DO SUBPROCESSO UTILIZADOR
# ###################################################################################

def _build_user_admin_redirect_v1(
    *,
    error: str = "",
    success: str = "",
    user_edit_id: str = "",
    target: str = "#create-user-card",
) -> RedirectResponse:
    extra_params: dict[str, str] = {}

    if user_edit_id:
        extra_params["user_edit_id"] = str(user_edit_id)

    url = build_users_new_url(
        error=error,
        success=success,
        menu="administrativo",
        admin_tab="utilizador",
        **extra_params,
    )

    return RedirectResponse(
        url=f"{url}{target}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _redirect_login_required_v1() -> RedirectResponse:
    return RedirectResponse(
        url="/login?error=Efetue login para continuar.",
        status_code=status.HTTP_302_FOUND,
    )


# ###################################################################################
# (5) VALIDACOES DO SUBPROCESSO UTILIZADOR
# ###################################################################################

def _validate_update_user_required_fields_v1(payload: UpdateUserInput) -> list[str]:
    errors: list[str] = []

    if not payload.clean_full_name:
        errors.append("Nome completo \u00e9 obrigat\u00f3rio.")

    if not payload.clean_primary_phone:
        errors.append("Telefone principal \u00e9 obrigat\u00f3rio.")

    if not payload.clean_email:
        errors.append("Email \u00e9 obrigat\u00f3rio.")

    if payload.clean_account_status not in ALLOWED_ACCOUNT_STATUS:
        errors.append("Estado de conta inv\u00e1lido.")

    return errors


def _resolve_update_user_entity_v1(
    *,
    session: Session,
    member: Member,
    payload: UpdateUserInput,
    entity_permissions: dict[str, Any],
) -> tuple[Entity | None, str]:
    selected_entity, entity_resolution_error = _resolve_entity_from_user_email_v1(
        session,
        payload.clean_email,
        entity_permissions,
    )

    if selected_entity is None and payload.clean_entity_id.isdigit():
        explicit_entity = session.get(Entity, int(payload.clean_entity_id))

        if explicit_entity is not None:
            can_use_explicit_entity = bool(entity_permissions.get("can_manage_all_entities"))

            if not can_use_explicit_entity:
                allowed_entity_ids = sorted(
                    set(entity_permissions.get("allowed_entity_ids") or set())
                )
                can_use_explicit_entity = int(explicit_entity.id) in allowed_entity_ids

            if can_use_explicit_entity:
                selected_entity = explicit_entity
                entity_resolution_error = ""

    if selected_entity is None:
        current_entity_stmt = (
            select(Entity)
            .join(MemberEntity, MemberEntity.entity_id == Entity.id)
            .where(MemberEntity.member_id == member.id)
            .order_by(MemberEntity.id.asc())
        )

        if not entity_permissions.get("can_manage_all_entities"):
            allowed_entity_ids = sorted(
                set(entity_permissions.get("allowed_entity_ids") or set())
            )

            if allowed_entity_ids:
                current_entity_stmt = current_entity_stmt.where(
                    Entity.id.in_(allowed_entity_ids)
                )
            else:
                current_entity_stmt = current_entity_stmt.where(Entity.id == -1)

        selected_entity = session.execute(
            current_entity_stmt.limit(1)
        ).scalar_one_or_none()

        if selected_entity is not None:
            entity_resolution_error = ""

    return selected_entity, entity_resolution_error


def _resolve_update_user_profile_v1(
    *,
    session: Session,
    payload: UpdateUserInput,
    errors: list[str],
) -> Profile | None:
    selected_profile: Profile | None = None

    if payload.clean_profile_id:
        try:
            selected_profile = session.get(Profile, int(payload.clean_profile_id))
        except ValueError:
            errors.append("Perfil selecionado inv\u00e1lido.")

        if selected_profile is None and not errors:
            errors.append("Perfil selecionado n\u00e3o existe.")
        elif not is_allowed_global_profile(selected_profile):
            errors.append("Perfil global inv\u00e1lido. Escolha ADMIN, SUPER USER ou USER.")

    return selected_profile


def _validate_update_user_duplicates_v1(
    *,
    session: Session,
    payload: UpdateUserInput,
    member: Member,
    user: User,
    errors: list[str],
) -> None:
    duplicate_member_id = session.scalar(
        select(Member.id).where(
            func.lower(Member.email) == payload.clean_email,
            Member.id != member.id,
        )
    )

    if duplicate_member_id is not None:
        errors.append("J\u00e1 existe um membro com este email.")

    duplicate_user_id = session.scalar(
        select(User.id).where(
            func.lower(User.login_email) == payload.clean_email,
            User.id != user.id,
        )
    )

    if duplicate_user_id is not None:
        errors.append("J\u00e1 existe um utilizador com este email de login.")


# ###################################################################################
# (6) APLICACAO DA ATUALIZACAO
# ###################################################################################

def _apply_update_user_changes_v1(
    *,
    session: Session,
    payload: UpdateUserInput,
    member: Member,
    user: User,
    selected_entity: Entity | None,
    selected_profile: Profile,
) -> None:
    member.full_name = payload.clean_full_name
    member.primary_phone = payload.clean_primary_phone
    member.email = payload.clean_email
    member.member_status = member_status_for_user_account_status(
        payload.clean_account_status
    )

    user.login_email = payload.clean_email
    user.account_status = payload.clean_account_status

    if selected_entity is not None:
        primary_link = session.execute(
            select(MemberEntity)
            .where(MemberEntity.member_id == member.id)
            .order_by(MemberEntity.id.asc())
            .limit(1)
        ).scalar_one_or_none()

        if primary_link is None:
            session.add(
                MemberEntity(
                    member_id=member.id,
                    entity_id=selected_entity.id,
                    status=MemberEntityStatus.ACTIVE.value,
                    entry_date=date.today(),
                )
            )
        else:
            primary_link.entity_id = selected_entity.id
            primary_link.status = MemberEntityStatus.ACTIVE.value

    session.execute(delete(UserProfile).where(UserProfile.user_id == user.id))
    session.add(
        UserProfile(
            user_id=user.id,
            profile_id=selected_profile.id,
            is_active=True,
        )
    )


# ###################################################################################
# (7) USE CASE PRINCIPAL DO UPDATE DE UTILIZADOR
# ###################################################################################

def execute_update_user_v1(
    *,
    request: Request,
    payload: UpdateUserInput,
) -> RedirectResponse:
    if payload.parsed_user_id is None:
        return _build_user_admin_redirect_v1(
            error="Utilizador inv\u00e1lido para edi\u00e7\u00e3o.",
            target="#create-user-card",
        )

    parsed_user_id = int(payload.parsed_user_id)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return _redirect_login_required_v1()

        selected_entity_id = get_session_entity_id(request)

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return _build_user_admin_redirect_v1(
                error="Apenas administradores podem editar utilizadores.",
                target="#create-user-card",
            )

        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        user = session.get(User, parsed_user_id)

        if user is None:
            return _build_user_admin_redirect_v1(
                error="Utilizador n\u00e3o encontrado.",
                target="#create-user-card",
            )

        if not member_is_within_permissions_v1(
            session,
            int(user.member_id),
            entity_permissions,
        ):
            return _build_user_admin_redirect_v1(
                error="Sem permiss\u00e3o para editar este utilizador.",
                target="#create-user-card",
            )

        member = session.get(Member, user.member_id)

        if member is None:
            return _build_user_admin_redirect_v1(
                error="Membro associado ao utilizador n\u00e3o encontrado.",
                target="#create-user-card",
            )

        errors = _validate_update_user_required_fields_v1(payload)

        selected_entity, entity_resolution_error = _resolve_update_user_entity_v1(
            session=session,
            member=member,
            payload=payload,
            entity_permissions=entity_permissions,
        )

        if selected_entity is None and entity_resolution_error:
            errors.append(entity_resolution_error)

        selected_profile = _resolve_update_user_profile_v1(
            session=session,
            payload=payload,
            errors=errors,
        )

        _validate_update_user_duplicates_v1(
            session=session,
            payload=payload,
            member=member,
            user=user,
            errors=errors,
        )

        if errors:
            return _build_user_admin_redirect_v1(
                error=" ".join(errors),
                user_edit_id=str(parsed_user_id),
                target="#edit-user-card",
            )

        if selected_profile is None:
            selected_profile = get_or_create_entity_superuser_profile(session)

        current_is_active_admin = (
            str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
            and is_admin_user(session, int(user.id), str(user.login_email or ""))
        )

        resulting_is_admin = is_admin_profile_v1(selected_profile)

        resulting_is_active_admin = (
            payload.clean_account_status == UserAccountStatus.ACTIVE.value
            and resulting_is_admin
        )

        if current_is_active_admin and not resulting_is_active_admin:
            can_change_admin_state, admin_state_error = ensure_not_last_active_admin_for_member_v1(
                session,
                int(user.member_id),
                int(user.id),
            )

            if not can_change_admin_state:
                return _build_user_admin_redirect_v1(
                    error=admin_state_error,
                    user_edit_id=str(parsed_user_id),
                    target="#edit-user-card",
                )

        _apply_update_user_changes_v1(
            session=session,
            payload=payload,
            member=member,
            user=user,
            selected_entity=selected_entity,
            selected_profile=selected_profile,
        )

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return _build_user_admin_redirect_v1(
                error="N\u00e3o foi poss\u00edvel atualizar utilizador.",
                user_edit_id=str(parsed_user_id),
                target="#edit-user-card",
            )

    return _build_user_admin_redirect_v1(
        success="Utilizador atualizado com sucesso.",
        target="#create-user-card",
    )
