from __future__ import annotations

import secrets
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


def _extract_email_domain(raw_email: str) -> str:
    clean_email = (raw_email or "").strip().lower()
    if "@" not in clean_email:
        return ""
    _, domain = clean_email.split("@", 1)
    return domain.strip()


def _resolve_entity_from_user_email(
    session: Session,
    user_email: str,
    permissions: dict[str, Any],
) -> tuple[Entity | None, str]:
    clean_email = (user_email or "").strip().lower()
    if not clean_email or "@" not in clean_email:
        return None, "Email inválido para determinar entidade."

    query = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())
    if not permissions.get("can_manage_all_entities"):
        allowed_entity_ids = sorted(set(permissions.get("allowed_entity_ids") or set()))
        if not allowed_entity_ids:
            return None, "Sem entidades disponíveis para este utilizador."
        query = query.where(Entity.id.in_(allowed_entity_ids))

    scoped_entities = list(session.execute(query).scalars().all())
    if not scoped_entities:
        return None, "Sem entidades ativas disponíveis para atribuição."

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
            "Existem múltiplas entidades com o mesmo email. Corrija os dados das entidades.",
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
                "Existem múltiplas entidades com este domínio de email. Ajuste o email das entidades.",
            )

    if not permissions.get("can_manage_all_entities") and len(scoped_entities) == 1:
        return scoped_entities[0], ""

    return (
        None,
        "Não foi possível determinar a entidade pelo email. "
        "Verifique o email da entidade (domínio) ou ajuste os dados.",
    )


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


def _get_primary_entity_name_for_member(session: Session, member_id: int) -> str:
    _, entity_name = _get_primary_entity_for_member(session, member_id)
    return entity_name


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


def _is_admin_profile(profile: Profile | None) -> bool:
    if profile is None:
        return False
    profile_name = (profile.name or "").strip().lower()
    if not profile_name:
        return False
    return profile_name in ADMIN_PROFILE_NAMES


def _get_active_entity_ids_for_member(session: Session, member_id: int) -> list[int]:
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


def _has_other_active_admin_for_entity(
    session: Session,
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


def _ensure_not_last_active_admin_for_member(
    session: Session,
    member_id: int,
    excluded_user_id: int,
) -> tuple[bool, str]:
    entity_ids = _get_active_entity_ids_for_member(session, member_id)
    if not entity_ids:
        return True, ""

    for entity_id in entity_ids:
        if _has_other_active_admin_for_entity(session, entity_id, excluded_user_id):
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


@router.post("/users/new", response_class=HTMLResponse)
def create_user(
    request: Request,
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    profile_id: str = Form(""),
) -> HTMLResponse:
    errors: list[str] = []

    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_profile_id = profile_id.strip()

    form_data = {
        "full_name": clean_full_name,
        "primary_phone": clean_primary_phone,
        "email": clean_email,
        "entity_id": "",
        "entity_name": "",
        "profile_id": clean_profile_id,
    }

    if not clean_full_name:
        errors.append("Nome completo é obrigatório.")
    if not clean_primary_phone:
        errors.append("Telefone principal é obrigatório.")
    if not clean_email:
        errors.append("Email é obrigatório.")

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        selected_entity_id = get_session_entity_id(request)

        current_user_is_admin = is_admin_user(
            session, current_user["id"], current_user["login_email"]
        )
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        page_data = get_page_data(
            session,
            actor_user_id=current_user["id"],
            actor_login_email=current_user["login_email"],
            selected_entity_id=selected_entity_id,
        )
        user_personal_data = get_user_personal_data(session, current_user["id"], selected_entity_id)
        next_entity_internal_number = get_next_entity_internal_number(session)

        if not current_user_is_admin:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Apenas administradores podem criar utilizadores.",
                    menu="perfil",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        selected_entity, entity_resolution_error = _resolve_entity_from_user_email(
            session,
            clean_email,
            entity_permissions,
        )
        if selected_entity is not None:
            form_data["entity_id"] = str(selected_entity.id)
            form_data["entity_name"] = selected_entity.name or ""
        elif entity_resolution_error:
            errors.append(entity_resolution_error)

        existing_member: Member | None = None
        existing_user_row: Any | None = None
        if clean_email:
            existing_member = session.execute(
                select(Member).where(func.lower(Member.email) == clean_email)
            ).scalar_one_or_none()
            existing_user_row = session.execute(
                select(User.id, User.account_status, User.login_email, User.member_id)
               .where(func.lower(User.login_email) == clean_email)
            ).one_or_none()

            if existing_user_row is not None:
                _, existing_user_entity_name = _get_primary_entity_for_member(
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

            if existing_user_row is not None:
                existing_status = str(existing_user_row.account_status or "").strip().lower()
                if existing_status == UserAccountStatus.PENDING.value:
                    invite_token = build_user_invite_token(
                        int(existing_user_row.id),
                        str(existing_user_row.login_email),
                    )
                    invite_link = build_user_invite_link(request, invite_token)
                    email_sent, email_error = send_user_invite_email(
                        recipient_email=clean_email,
                        recipient_name=clean_full_name,
                        entity_name=linked_entity_name,
                        invite_link=invite_link,
                        invited_by_name=current_user["full_name"],
                    )
                    if email_sent:
                        return RedirectResponse(
                            url=build_users_new_url(
                                success="Utilizador já estava pendente. Convite reenviado por email.",
                                menu="administrativo",
                                admin_tab="utilizador",
                            )
                            + "#create-user-card",
                            status_code=status.HTTP_303_SEE_OTHER,
                        )
                    return RedirectResponse(
                        url=build_users_new_url(
                            success="Utilizador já estava pendente.",
                            error=f"{email_error} Link de ativação: {invite_link}",
                            menu="administrativo",
                            admin_tab="utilizador",
                        )
                        + "#create-user-card",
                        status_code=status.HTTP_303_SEE_OTHER,
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

        selected_profile: Profile | None = None
        if clean_profile_id:
            try:
                selected_profile = session.get(Profile, int(clean_profile_id))
            except ValueError:
                errors.append("Perfil selecionado inválido.")
            if selected_profile is None and not errors:
                errors.append("Perfil selecionado não existe.")
            elif not is_allowed_global_profile(selected_profile):
                errors.append("Perfil global inválido. Escolha ADMIN, SUPER USER ou USER.")

        if errors:
            context = {
                "request": request,
                "errors": errors,
                "success": "",
                "form_data": form_data,
                "entity_form_data": get_entity_form_defaults(),
                "entity_edit_data": get_entity_edit_defaults(),
                "user_edit_data": get_user_edit_defaults(),
                    "current_user": current_user,
                    "current_user_is_admin": current_user_is_admin,
                    "current_user_can_manage_all_entities": bool(
                        entity_permissions["can_manage_all_entities"]
                    ),
                    "user_personal_data": user_personal_data,
                    "entity_success": "",
                    "entity_error": "",
                    "next_entity_internal_number": str(next_entity_internal_number),
                "profile_success": "",
                "profile_error": "",
                "profile_tab": "pessoal",
                "initial_menu": "administrativo",
                "admin_tab": "utilizador",
                **page_data,
            }
            return templates.TemplateResponse(
                request,
                "new_user.html",
                context,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if selected_profile is None:
            selected_profile = get_or_create_entity_superuser_profile(session)

        if existing_member is None:
            member = Member(
                full_name=clean_full_name,
                primary_phone=clean_primary_phone,
                email=clean_email,
                member_status=MemberStatus.ACTIVE.value,
                is_collaborator=True,
            )
            session.add(member)
            session.flush()
        else:
            member = existing_member
            member.full_name = clean_full_name
            member.primary_phone = clean_primary_phone
            member.email = clean_email
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

        user = User(
            member_id=member.id,
            login_email=clean_email,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            account_status=UserAccountStatus.PENDING.value,
            created_by_user_id=current_user["id"],
        )
        session.add(user)
        session.flush()

        session.add(
            UserProfile(
                user_id=user.id,
                profile_id=selected_profile.id,
                is_active=True,
            )
        )

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            context = {
                "request": request,
                "errors": ["Falha ao gravar no banco. Verifique dados duplicados e tente novamente."],
                "success": "",
                "form_data": form_data,
                "entity_form_data": get_entity_form_defaults(),
                "entity_edit_data": get_entity_edit_defaults(),
                "user_edit_data": get_user_edit_defaults(),
                "current_user": current_user,
                "current_user_is_admin": current_user_is_admin,
                "user_personal_data": user_personal_data,
                "entity_success": "",
                "entity_error": "",
                "next_entity_internal_number": str(next_entity_internal_number),
                "profile_success": "",
                "profile_error": "",
                "profile_tab": "pessoal",
                "initial_menu": "administrativo",
                "admin_tab": "utilizador",
                **page_data,
            }
            return templates.TemplateResponse(
                request,
                "new_user.html",
                context,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        invite_token = build_user_invite_token(user.id, user.login_email)
        invite_link = build_user_invite_link(request, invite_token)
        email_sent, email_error = send_user_invite_email(
            recipient_email=clean_email,
            recipient_name=clean_full_name,
            entity_name=selected_entity.name if selected_entity is not None else "",
            invite_link=invite_link,
            invited_by_name=current_user["full_name"],
        )

    if email_sent:
        return RedirectResponse(
            url=build_users_new_url(
                success="Utilizador criado em estado pendente. Convite enviado por email.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url=build_users_new_url(
            success="Utilizador criado em estado pendente.",
            error=f"{email_error} Link de ativação: {invite_link}",
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/resend-invite", response_class=HTMLResponse)
def resend_user_invite(
    request: Request,
    user_id: str = Form(...),
) -> RedirectResponse:
    clean_user_id = user_id.strip()
    if not clean_user_id.isdigit():
        return RedirectResponse(
            url=build_users_new_url(
                error="Utilizador inválido para reenvio de convite.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
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
                url=build_users_new_url(
                    error="Apenas administradores podem reenviar convites.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        user_row = session.execute(
            select(User.id, User.login_email, User.account_status, User.member_id)
           .where(User.id == parsed_user_id)
        ).one_or_none()
        if user_row is None:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Utilizador não encontrado.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if str(user_row.account_status or "").strip().lower() != UserAccountStatus.PENDING.value:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Só é possível reenviar convite para utilizadores pendentes.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not _member_is_within_permissions(
            session,
            int(user_row.member_id),
            entity_permissions,
        ):
            return RedirectResponse(
                url=build_users_new_url(
                    error="Sem permissão para reenviar convite deste utilizador.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        member = session.get(Member, int(user_row.member_id))
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Membro associado ao utilizador não encontrado.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        entity_name = _get_primary_entity_name_for_member(session, int(user_row.member_id))
        invite_token = build_user_invite_token(int(user_row.id), str(user_row.login_email))
        invite_link = build_user_invite_link(request, invite_token)
        email_sent, email_error = send_user_invite_email(
            recipient_email=str(user_row.login_email),
            recipient_name=str(member.full_name or user_row.login_email),
            entity_name=entity_name,
            invite_link=invite_link,
            invited_by_name=current_user["full_name"],
        )

    if email_sent:
        return RedirectResponse(
            url=build_users_new_url(
                success="Convite reenviado com sucesso.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url=build_users_new_url(
            success="Não foi possível enviar email automático.",
            error=f"{email_error} Link de ativação: {invite_link}",
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/update", response_class=HTMLResponse)
def update_user(
    request: Request,
    user_id: str = Form(...),
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    entity_id: str = Form(""),
    account_status: str = Form(UserAccountStatus.ACTIVE.value),
    profile_id: str = Form(""),
) -> RedirectResponse:
    clean_user_id = user_id.strip()
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_account_status = account_status.strip().lower()
    clean_profile_id = profile_id.strip()

    if not clean_user_id.isdigit():
        return RedirectResponse(
            url=build_users_new_url(
                error="Utilizador inválido para edição.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
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
                url=build_users_new_url(
                    error="Apenas administradores podem editar utilizadores.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
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
                url=build_users_new_url(
                    error="Utilizador não encontrado.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not _member_is_within_permissions(
            session,
            int(user.member_id),
            entity_permissions,
        ):
            return RedirectResponse(
                url=build_users_new_url(
                    error="Sem permissão para editar este utilizador.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        member = session.get(Member, user.member_id)
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Membro associado ao utilizador não encontrado.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
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

        selected_entity, entity_resolution_error = _resolve_entity_from_user_email(
            session,
            clean_email,
            entity_permissions,
        )
        if selected_entity is None and entity_resolution_error:
            errors.append(entity_resolution_error)

        selected_profile: Profile | None = None
        if clean_profile_id:
            try:
                selected_profile = session.get(Profile, int(clean_profile_id))
            except ValueError:
                errors.append("Perfil selecionado inválido.")
            if selected_profile is None and not errors:
                errors.append("Perfil selecionado não existe.")
            elif not is_allowed_global_profile(selected_profile):
                errors.append("Perfil global inválido. Escolha ADMIN, SUPER USER ou USER.")

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
                url=build_users_new_url(
                    error=" ".join(errors),
                    menu="administrativo",
                    admin_tab="utilizador",
                    user_edit_id=str(parsed_user_id),
                )
                + "#edit-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if selected_profile is None:
            selected_profile = get_or_create_entity_superuser_profile(session)

        current_is_active_admin = (
            str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
            and is_admin_user(session, int(user.id), str(user.login_email or ""))
        )
        resulting_is_admin = (
            (bool(ADMIN_LOGIN_EMAIL) and clean_email == ADMIN_LOGIN_EMAIL)
            or _is_admin_profile(selected_profile)
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
                    url=build_users_new_url(
                        error=admin_state_error,
                        menu="administrativo",
                        admin_tab="utilizador",
                        user_edit_id=str(parsed_user_id),
                    )
                    + "#edit-user-card",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        member.full_name = clean_full_name
        member.primary_phone = clean_primary_phone
        member.email = clean_email
        user.login_email = clean_email
        user.account_status = clean_account_status

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

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_users_new_url(
                    error="Não foi possível atualizar utilizador.",
                    menu="administrativo",
                    admin_tab="utilizador",
                    user_edit_id=str(parsed_user_id),
                )
                + "#edit-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_users_new_url(
            success="Utilizador atualizado com sucesso.",
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/delete", response_class=HTMLResponse)
def delete_user(
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
                url=build_users_new_url(
                    error="Apenas administradores podem eliminar utilizadores.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if parsed_user_id == int(current_user["id"]):
            return RedirectResponse(
                url=build_users_new_url(
                    error="Não é permitido eliminar o próprio utilizador ligado.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        user = session.get(User, parsed_user_id)
        if user is None:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Utilizador não encontrado.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not _member_is_within_permissions(
            session,
            int(user.member_id),
            entity_permissions,
        ):
            return RedirectResponse(
                url=build_users_new_url(
                    error="Sem permissão para eliminar este utilizador.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        target_is_active_admin = (
            str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
            and is_admin_user(session, int(user.id), str(user.login_email or ""))
        )
        if target_is_active_admin:
            can_delete_admin, admin_delete_error = _ensure_not_last_active_admin_for_member(
                session,
                int(user.member_id),
                int(user.id),
            )
            if not can_delete_admin:
                return RedirectResponse(
                    url=build_users_new_url(
                        error=admin_delete_error,
                        menu="administrativo",
                        admin_tab="utilizador",
                    )
                    + "#create-user-card",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        session.execute(
            update(User)
           .where(User.created_by_user_id == parsed_user_id)
           .values(created_by_user_id=None)
        )
        session.execute(delete(UserProfile).where(UserProfile.user_id == parsed_user_id))
        session.delete(user)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_users_new_url(
                    error="Não foi possível eliminar utilizador.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_users_new_url(
            success="Utilizador eliminado com sucesso.",
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
        status_code=status.HTTP_303_SEE_OTHER,
    )
