from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Any

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appgenesis.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    User,
    UserAccountStatus,
)
from appgenesis.services.auth import (
    build_user_invite_link,
    build_user_invite_token,
    is_admin_user,
    send_user_invite_email,
)
from appgenesis.services.user_entity_scope import (
    get_actor_primary_entity_v1,
)
from appgenesis.services.user_member import ensure_user_for_member
from appgenesis.services.page import (
    build_users_new_url,
    get_entity_edit_defaults,
    get_entity_form_defaults,
    get_next_entity_number,
    get_page_data,
    get_user_edit_defaults,
)
from appgenesis.services.permissions import get_user_entity_permissions
from appgenesis.services.profile import get_user_personal_data
from appgenesis.services.user_system import normalize_user_system_type_v1


# ###################################################################################
# (1) COMPATIBILIDADE LEGADA DO SYSTEM TYPE
# ###################################################################################
LEGACY_USER_SYSTEM_TYPE_DEFAULT = "default"


def _extract_email_domain(raw_email: str) -> str:
    clean_email = (raw_email or "").strip().lower()
    if "@" not in clean_email:
        return ""
    _, domain = clean_email.split("@", 1)
    return domain.strip()


def _resolve_selected_entity_fallback_v2(
    session: Session,
    selected_entity_id: int | None,
    permissions: dict[str, Any],
) -> Entity | None:
    clean_selected_entity_id: int | None = None

    if selected_entity_id is not None:
        try:
            clean_selected_entity_id = int(selected_entity_id)
        except (TypeError, ValueError):
            clean_selected_entity_id = None

    if clean_selected_entity_id is not None and clean_selected_entity_id > 0:
        if not permissions.get("can_manage_all_entities"):
            allowed_entity_ids = {
                int(raw_id)
                for raw_id in (permissions.get("allowed_entity_ids") or set())
                if str(raw_id).strip().isdigit()
            }
            if clean_selected_entity_id not in allowed_entity_ids:
                return None

        selected_entity = session.execute(
            select(Entity).where(
                Entity.id == clean_selected_entity_id,
                Entity.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if selected_entity is not None:
            return selected_entity

    query = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())

    if not permissions.get("can_manage_all_entities"):
        allowed_entity_ids = sorted(
            {
                int(raw_id)
                for raw_id in (permissions.get("allowed_entity_ids") or set())
                if str(raw_id).strip().isdigit()
            }
        )
        if not allowed_entity_ids:
            return None
        query = query.where(Entity.id.in_(allowed_entity_ids))

    return session.execute(query.limit(1)).scalars().first()


def _resolve_entity_from_user_email_v2(
    session: Session,
    user_email: str,
    permissions: dict[str, Any],
    selected_entity_id: int | None = None,
) -> tuple[Entity | None, str]:
    clean_email = (user_email or "").strip().lower()

    if clean_email and "@" in clean_email:
        query = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())

        if not permissions.get("can_manage_all_entities"):
            allowed_entity_ids = sorted(set(permissions.get("allowed_entity_ids") or set()))
            if allowed_entity_ids:
                query = query.where(Entity.id.in_(allowed_entity_ids))

        scoped_entities = list(session.execute(query).scalars().all())

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
                "Existem multiplas entidades com o mesmo email. Corrija os dados das entidades.",
            )

        email_domain = _extract_email_domain(clean_email)
        if email_domain:
            domain_matches = [
                entity
                for entity in scoped_entities
                if _extract_email_domain((entity.email or "").strip().lower()) == email_domain
            ]
            if len(domain_matches) == 1:
                return domain_matches[0], ""
            if len(domain_matches) > 1:
                return (
                    None,
                    "Existem multiplas entidades com este dominio de email. Ajuste o email das entidades.",
                )

    selected_fallback_entity = _resolve_selected_entity_fallback_v2(
        session,
        selected_entity_id,
        permissions,
    )
    if selected_fallback_entity is not None:
        return selected_fallback_entity, ""

    return (
        None,
        "Nao foi possivel determinar uma entidade ativa para este convite.",
    )


_resolve_entity_from_user_email = _resolve_entity_from_user_email_v2

def _get_primary_entity_for_member(session: Session, member_id: int) -> tuple[int | None, str]:
    entity_row = session.execute(
        select(Entity.id, Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).one_or_none()
    if entity_row is None:
        return None, "-"
    return int(entity_row.id), str(entity_row.name or "-")


def _member_is_within_permissions(
    session: Session,
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


@dataclass(frozen=True)
class CreateUserInput:
    clean_full_name: str
    clean_primary_phone: str
    clean_email: str
    clean_system_type: str
    clean_invite_delivery: str
    form_data: dict[str, str]
    errors: list[str]


@dataclass(frozen=True)
class CreateUserOutcome:
    kind: str
    redirect_url: str = ""
    redirect_status_code: int = 303
    template_context: dict[str, Any] | None = None
    template_status_code: int = 400


def normalize_create_user_input_v1(
    *,
    full_name: str,
    primary_phone: str,
    email: str,
    entity_id: str = "",
    invite_delivery: str,
    system_profile: str = "",
) -> CreateUserInput:
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_entity_id = (entity_id or "").strip()
    clean_system_type = normalize_user_system_type_v1(system_profile) if system_profile.strip() else LEGACY_USER_SYSTEM_TYPE_DEFAULT
    clean_invite_delivery = invite_delivery.strip().lower()
    if clean_invite_delivery not in {"email", "link"}:
        clean_invite_delivery = "email"

    form_data = {
        "full_name": clean_full_name,
        "primary_phone": clean_primary_phone,
        "email": clean_email,
        "entity_id": clean_entity_id,
        "entity_name": "",
        "entity_number": "",
        "system_profile": clean_system_type,
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
        clean_system_type=clean_system_type,
        clean_invite_delivery=clean_invite_delivery,
        form_data=form_data,
        errors=errors,
    )


normalize_create_user_input = normalize_create_user_input_v1

def _build_error_context(
    *,
    request: Request,
    errors: list[str],
    form_data: dict[str, str],
    current_user: dict[str, Any],
    current_user_is_admin: bool,
    can_manage_all_entities: bool,
    user_personal_data: dict[str, Any],
    next_entity_number: int,
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
        "current_user_can_manage_tenant_structure": bool(can_manage_all_entities),
        "current_user_can_manage_all_entities": bool(can_manage_all_entities),
        "user_personal_data": user_personal_data,
        "entity_success": "",
        "entity_error": "",
        "next_entity_number": str(next_entity_number),
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
        "appgenesis_after_save": False,
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
    current_user_is_admin = bool(
        is_admin_user(
            session,
            int(actor_user["id"]),
            str(actor_user["login_email"]),
        )
    )
    entity_permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )
    page_data = get_page_data(
        session,
        actor_user_id=int(actor_user["id"]),
        actor_login_email=str(actor_user["login_email"]),
        selected_entity_id=selected_entity_id,
    )
    user_personal_data = get_user_personal_data(
        session, int(actor_user["id"]), selected_entity_id
    )
    next_entity_number = get_next_entity_number(session)

    if not current_user_is_admin:
        return CreateUserOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                error="Apenas administradores podem criar utilizadores.",
                menu="perfil",
            ),
        )

    errors = list(payload.errors)
    form_data = dict(payload.form_data)
    selected_entity = None

    # APPGENESIS_ENTITY_SCOPE_RESOLUTION_V1_START
    # A entidade do novo utilizador depende das permissões ativas do utilizador logado:
    # - can_manage_all_entities → escolhe qualquer entidade ativa no dropdown
    # - restantes → ficam restritos à entidade ativa do próprio ator
    if entity_permissions.get("can_manage_all_entities"):
        submitted_entity_id = form_data.get("entity_id", "")
        if submitted_entity_id:
            try:
                _owner_eid = int(submitted_entity_id)
            except (TypeError, ValueError):
                _owner_eid = 0
            if _owner_eid > 0:
                _candidate = session.execute(
                    select(Entity).where(
                        Entity.id == _owner_eid,
                        Entity.is_active.is_(True),
                    )
                ).scalar_one_or_none()
                if _candidate is not None:
                    selected_entity = _candidate
                else:
                    errors.append("Entidade selecionada não existe ou está inativa.")
            else:
                errors.append("Selecione uma entidade válida.")
        if selected_entity is None and not errors:
            # Fallback: resolução por domínio de email
            selected_entity, entity_resolution_error = _resolve_entity_from_user_email_v2(
                session,
                payload.clean_email,
                entity_permissions,
                selected_entity_id,
            )
            if selected_entity is None and entity_resolution_error:
                errors.append(entity_resolution_error)
    else:
        # Legado / Default: entidade do ator logado
        _actor_entity = get_actor_primary_entity_v1(session, int(actor_user["id"]))
        if _actor_entity is None:
            errors.append(
                "O utilizador logado não tem entidade associada. Contacte o administrador."
            )
        else:
            selected_entity = session.execute(
                select(Entity).where(
                    Entity.id == _actor_entity["id"],
                    Entity.is_active.is_(True),
                )
            ).scalar_one_or_none()
            if selected_entity is None:
                errors.append("Entidade do utilizador logado está inativa ou não foi encontrada.")

    if selected_entity is not None:
        form_data["entity_id"] = str(selected_entity.id)
        form_data["entity_name"] = selected_entity.name or ""
        form_data["entity_number"] = (
            str(selected_entity.entity_number)
            if selected_entity.entity_number is not None
            else ""
        )
    # APPGENESIS_ENTITY_SCOPE_RESOLUTION_V1_END

    existing_member: Member | None = None
    existing_user_row: Any | None = None
    if payload.clean_email:
        existing_member = session.execute(
            select(Member).where(func.lower(Member.email) == payload.clean_email)
        ).scalar_one_or_none()
        existing_user_row = session.execute(
            select(User.id, User.account_status, User.login_email, User.member_id).where(
                func.lower(User.login_email) == payload.clean_email
            )
        ).one_or_none()

        if existing_user_row is not None:
            existing_user_entity_id, existing_user_entity_name = _get_primary_entity_for_member(
                session,
                int(existing_user_row.member_id),
            )
            can_manage_existing_user = _member_is_within_permissions(
                session,
                int(existing_user_row.member_id),
                entity_permissions,
            )
            if not can_manage_existing_user:
                errors.append("Sem permissão para gerir utilizador com este email.")
                existing_user_row = None
            else:
                linked_entity_name = (
                    selected_entity.name
                    if selected_entity is not None
                    else existing_user_entity_name
                )
                linked_entity_id = (
                    int(selected_entity.id)
                    if selected_entity is not None
                    else existing_user_entity_id
                )

        if existing_user_row is not None:
            existing_status = str(existing_user_row.account_status or "").strip().lower()
            if existing_status == UserAccountStatus.PENDING.value:
                invite_token = build_user_invite_token(
                    int(existing_user_row.id),
                    str(existing_user_row.login_email),
                    linked_entity_id,
                )
                invite_link = build_user_invite_link(request, invite_token)
                if payload.clean_invite_delivery == "link":
                    return CreateUserOutcome(
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
                    return CreateUserOutcome(
                        kind="redirect",
                        redirect_url=build_users_new_url(
                            success="Utilizador já estava pendente. Convite reenviado por email.",
                            menu="administrativo",
                            admin_tab="utilizador",
                        )
                        + "#create-user-card",
                    )
                return CreateUserOutcome(
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

        if existing_member is not None and existing_user_row is None:
            existing_member_entity_id, _ = _get_primary_entity_for_member(
                session,
                int(existing_member.id),
            )
            if (
                existing_member_entity_id is not None
                and not _member_is_within_permissions(
                    session,
                    int(existing_member.id),
                    entity_permissions,
                )
            ):
                errors.append("Sem permissão para utilizar este email noutra entidade.")
                existing_member = None

    if errors:
        return CreateUserOutcome(
            kind="template",
            template_context=_build_error_context(
                request=request,
                errors=errors,
                form_data=form_data,
                current_user=actor_user,
                current_user_is_admin=current_user_is_admin,
                can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
                user_personal_data=user_personal_data,
                next_entity_number=next_entity_number,
                page_data=page_data,
            ),
        )

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

    existing_member_link = session.execute(
        select(MemberEntity)
        .where(
            MemberEntity.member_id == member.id,
            MemberEntity.entity_id == selected_entity.id,
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    if existing_member_link is None:
        session.add(
            MemberEntity(
                member_id=member.id,
                entity_id=selected_entity.id,
                status=MemberEntityStatus.ACTIVE.value,
                entry_date=date.today(),
            )
        )
    else:
        existing_member_link.status = MemberEntityStatus.ACTIVE.value
        if existing_member_link.entry_date is None:
            existing_member_link.entry_date = date.today()

    user = ensure_user_for_member(
        session,
        member,
        status=UserAccountStatus.PENDING.value,
        created_by_user_id=int(actor_user["id"]),
    )
    user.system_type = payload.clean_system_type

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return CreateUserOutcome(
            kind="template",
            template_context=_build_error_context(
                request=request,
                errors=[
                    "Falha ao gravar no banco. Verifique dados duplicados e tente novamente."
                ],
                form_data=form_data,
                current_user=actor_user,
                current_user_is_admin=current_user_is_admin,
                can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
                user_personal_data=user_personal_data,
                next_entity_number=next_entity_number,
                page_data=page_data,
            ),
        )

    invite_token = build_user_invite_token(
        user.id,
        user.login_email,
        int(selected_entity.id) if selected_entity is not None else None,
    )
    invite_link = build_user_invite_link(request, invite_token)
    if payload.clean_invite_delivery == "link":
        return CreateUserOutcome(
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
        entity_name=selected_entity.name if selected_entity is not None else "",
        invite_link=invite_link,
        invited_by_name=str(actor_user["full_name"]),
    )
    if email_sent:
        return CreateUserOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                success="Utilizador criado em estado pendente. Convite enviado por email.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
        )

    return CreateUserOutcome(
        kind="redirect",
        redirect_url=build_users_new_url(
            success="Utilizador criado em estado pendente.",
            error=f"{email_error} Link de ativação: {invite_link}",
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
    )
