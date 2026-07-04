from __future__ import annotations

import secrets
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appgenesis.core import *  # noqa: F403,F401
from appgenesis.services import *  # noqa: F403,F401
from appgenesis.services.user_member import member_status_for_user_account_status
from appgenesis.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    User,
    UserAccountStatus,
)

from appgenesis.routes.users.router import router
from appgenesis.routes.users.helpers import (
    _ensure_not_last_active_admin_for_member,
    _member_is_within_permissions,
    _resolve_entity_from_user_email,
)
from appgenesis.services.permissions import is_entity_within_permissions


# ###################################################################################
# (1) VALIDACAO EXPLICITA DA ENTIDADE SELECIONADA
# ###################################################################################
def _clean_optional_form_value_v1(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _resolve_explicit_user_entity_v1(
    session: Session,
    raw_entity_id: str,
    permissions: dict[str, Any],
) -> tuple[Entity | None, str]:
    clean_entity_id = (raw_entity_id or "").strip()
    if not clean_entity_id:
        return None, ""
    if not clean_entity_id.isdigit():
        return None, "Selecione uma entidade válida."

    parsed_entity_id = int(clean_entity_id)
    if not is_entity_within_permissions(parsed_entity_id, permissions):
        return None, "Não tem permissão para associar utilizador a esta entidade."

    entity = session.execute(
        select(Entity).where(
            Entity.id == parsed_entity_id,
            Entity.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if entity is None:
        return None, "Entidade selecionada não existe ou está inativa."
    return entity, ""

@router.post("/users/update", response_class=HTMLResponse)
def update_user(
    request: Request,
    user_id: str = Form(...),
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    entity_id: str = Form(""),
    account_status: str = Form(UserAccountStatus.ACTIVE.value),
    system_profile: str = Form(""),
    return_menu: str = Form(""),
    return_admin_tab: str = Form(""),
    return_target: str = Form(""),
) -> RedirectResponse:
    clean_user_id = user_id.strip()
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_account_status = account_status.strip().lower()
    clean_entity_id = entity_id.strip()
    raw_system_profile = _clean_optional_form_value_v1(system_profile)

    if not clean_user_id.isdigit():
        return RedirectResponse(
            url=build_return_url_v1(
                return_menu=return_menu,
                return_admin_tab=return_admin_tab,
                error="Utilizador inválido para edição.",
                default_menu="administrativo",
                default_admin_tab="utilizador",
                default_hash="#create-user-card",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    parsed_user_id = int(clean_user_id)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        selected_entity_id = get_session_entity_id(request)

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error="Apenas administradores podem editar utilizadores.",
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#create-user-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        user = session.get(User, parsed_user_id)
        if user is None:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error="Utilizador não encontrado.",
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#create-user-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        clean_system_type = (
            normalize_user_system_type_v1(raw_system_profile)
            if raw_system_profile
            else normalize_user_system_type_v1(user.system_type)
        )

        if not _member_is_within_permissions(
            session,
            int(user.member_id),
            entity_permissions,
        ):
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error="Sem permissão para editar este utilizador.",
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#create-user-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        member = session.get(Member, user.member_id)
        if member is None:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error="Membro associado ao utilizador não encontrado.",
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#create-user-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        errors: list[str] = []
        if not clean_full_name:
            errors.append("Nome completo é obrigatório.")
        if not clean_primary_phone:
            errors.append("Telefone principal é obrigatório.")
        if not clean_email:
            errors.append("Email é obrigatório.")
        if clean_account_status not in ALLOWED_ACCOUNT_STATUS:
            errors.append("Estado de conta inválido.")

        selected_entity = None
        entity_resolution_error = ""
        explicit_entity, explicit_entity_error = _resolve_explicit_user_entity_v1(
            session,
            clean_entity_id,
            entity_permissions,
        )
        if explicit_entity_error:
            errors.append(explicit_entity_error)
        elif explicit_entity is not None:
            selected_entity = explicit_entity
        else:
            selected_entity, entity_resolution_error = _resolve_entity_from_user_email(
                session,
                clean_email,
                entity_permissions,
            )
        # APPGENESIS_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_START
        # Ao editar um utilizador existente, não devemos bloquear a atualização só porque
        # o domínio do email do utilizador não corresponde ao domínio/email da entidade.
        #
        # Regra:
        # 1. Se vier entity_id explícito e permitido, usa essa entidade.
        # 2. Se não for possível resolver pelo email, mantém a entidade já ligada ao membro.
        # 3. A entidade atual pode estar inativa; ainda assim deve ser mantida para permitir
        #    alteração de estado do utilizador sem forçar nova resolução por domínio.
        if selected_entity is None and not clean_entity_id:
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
        # APPGENESIS_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_END


        if selected_entity is None and entity_resolution_error:
            errors.append(entity_resolution_error)

        duplicate_member_id = session.scalar(
            select(Member.id).where(
                func.lower(Member.email) == clean_email,
                Member.id != member.id,
            )
        )
        if duplicate_member_id is not None:
            errors.append("Já existe um membro com este email.")

        duplicate_user_id = session.scalar(
            select(User.id).where(
                func.lower(User.login_email) == clean_email,
                User.id != user.id,
            )
        )
        if duplicate_user_id is not None:
            errors.append("Já existe um utilizador com este email de login.")

        if errors:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error=" ".join(errors),
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#edit-user-card",
                    user_edit_id=str(parsed_user_id),
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        current_is_active_admin = (
            str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
            and is_admin_user(session, int(user.id), str(user.login_email or ""))
        )
        resulting_is_admin = (
            (bool(ADMIN_LOGIN_EMAIL) and clean_email == ADMIN_LOGIN_EMAIL)
            or is_owner_system_v1(clean_system_type)
        )
        resulting_is_active_admin = (
            clean_account_status == UserAccountStatus.ACTIVE.value and resulting_is_admin
        )
        if current_is_active_admin and not resulting_is_active_admin:
            can_change_admin_state, admin_state_error = _ensure_not_last_active_admin_for_member(
                session,
                int(user.member_id),
                int(user.id),
            )
            if not can_change_admin_state:
                return RedirectResponse(
                    url=build_return_url_v1(
                        return_menu=return_menu,
                        return_admin_tab=return_admin_tab,
                        error=admin_state_error,
                        default_menu="administrativo",
                        default_admin_tab="utilizador",
                        default_hash="#edit-user-card",
                        user_edit_id=str(parsed_user_id),
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        member.full_name = clean_full_name
        member.primary_phone = clean_primary_phone
        member.email = clean_email
        user.login_email = clean_email
        user.account_status = clean_account_status
        user.system_type = clean_system_type
        member.member_status = member_status_for_user_account_status(clean_account_status)

        if selected_entity is not None:
            member_links = session.execute(
                select(MemberEntity)
               .where(MemberEntity.member_id == member.id)
                .order_by(MemberEntity.id.asc())
            ).scalars().all()
            primary_link = member_links[0] if member_links else None
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
                if primary_link.entry_date is None:
                    primary_link.entry_date = date.today()
                primary_link.exit_date = None

                for duplicate_link in member_links[1:]:
                    if int(duplicate_link.entity_id) != int(selected_entity.id):
                        continue
                    if duplicate_link.status != MemberEntityStatus.INACTIVE.value:
                        duplicate_link.status = MemberEntityStatus.INACTIVE.value
                    if duplicate_link.exit_date is None:
                        duplicate_link.exit_date = date.today()

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error="Não foi possível atualizar utilizador.",
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#edit-user-card",
                    user_edit_id=str(parsed_user_id),
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_return_url_v1(
            return_menu=return_menu,
            return_admin_tab=return_admin_tab,
            success="Utilizador atualizado com sucesso.",
            default_menu="administrativo",
            default_admin_tab="utilizador",
            default_hash="#create-user-card",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
