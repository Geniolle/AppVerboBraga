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

from appverbo.routes.entities.router import router

@router.post("/entities/update", response_class=HTMLResponse)
def update_entity(
    request: Request,
    entity_id: str = Form(...),
    name: str = Form(...),
    acronym: str = Form(""),
    tax_id: str = Form(...),
    email: str = Form(...),
    responsible_name: str = Form(...),
    door_number: str = Form(...),
    address: str = Form(...),
    freguesia: str = Form(...),
    postal_code: str = Form(...),
    country: str = Form(...),
    phone: str = Form(...),
    description: str | None = Form(default=None),
    entity_status: str = Form("active"),
    entity_profile_scope: str = Form(ENTITY_PROFILE_SCOPE_LEGADO),
    remove_logo: str | None = Form(default=None),
    entity_logo_file: UploadFile | None = File(default=None),
) -> HTMLResponse:
    clean_entity_id = entity_id.strip()
    clean_name = name.strip()
    clean_acronym = acronym.strip()
    clean_tax_id = tax_id.strip()
    clean_email = email.strip()
    clean_responsible_name = responsible_name.strip()
    clean_door_number = door_number.strip()
    clean_address = address.strip()
    clean_freguesia = freguesia.strip()
    clean_postal_code = postal_code.strip()
    clean_country = country.strip()
    clean_phone = phone.strip()
    clean_profile_scope = entity_profile_scope.strip().lower()
    clean_description = description.strip() if isinstance(description, str) else None
    clean_status = entity_status.strip().lower()
    invalid_profile_scope = clean_profile_scope not in ALLOWED_ENTITY_PROFILE_SCOPE

    if not clean_entity_id.isdigit():
        return RedirectResponse(
            url=build_users_new_url(
                entity_error="Entidade inválida para edição.",
                menu="administrativo",
                admin_tab="entidade",
            )
            + "#edit-entity-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    parsed_entity_id = int(clean_entity_id)
    if clean_status not in {"active", "inactive"}:
        clean_status = "active"
    if invalid_profile_scope:
        clean_profile_scope = ENTITY_PROFILE_SCOPE_LEGADO

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
        if not current_user_is_admin:
            return RedirectResponse(
                url=build_users_new_url(
                    entity_error="Apenas administradores podem editar entidades.",
                    menu="perfil",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        can_manage_all_entities = bool(entity_permissions["can_manage_all_entities"])
        if not is_entity_within_permissions(parsed_entity_id, entity_permissions):
            return RedirectResponse(
                url=build_users_new_url(
                    entity_error="Sem permissão para editar esta entidade.",
                    menu="administrativo",
                    admin_tab="entidade",
                )
                + "#recent-entities-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        entity = session.get(Entity, parsed_entity_id)
        if entity is None:
            return RedirectResponse(
                url=build_users_new_url(
                    entity_error="Entidade não encontrada.",
                    menu="administrativo",
                    admin_tab="entidade",
                )
                + "#create-entity-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        if not can_manage_all_entities:
            clean_status = "active" if entity.is_active else "inactive"

        required_field_labels = []
        if not clean_name:
            required_field_labels.append("Nome da entidade")
        if not clean_email:
            required_field_labels.append("Email")
        if not clean_tax_id:
            required_field_labels.append("Nº Identificacao Fiscal")
        if not clean_phone:
            required_field_labels.append("Telefone")
        if not clean_responsible_name:
            required_field_labels.append("Nome do responsavel")
        if not clean_address:
            required_field_labels.append("Morada")
        if not clean_door_number:
            required_field_labels.append("Nº da porta")
        if not clean_freguesia:
            required_field_labels.append("Freguesia")
        if not clean_postal_code:
            required_field_labels.append("Código postal")
        if not clean_country:
            required_field_labels.append("País")

        if required_field_labels:
            return RedirectResponse(
                url=build_users_new_url(
                    entity_error=(
                        "Preencha os campos obrigatórios: "
                        + ", ".join(required_field_labels)
                        + "."
                    ),
                    menu="administrativo",
                    admin_tab="entidade",
                    entity_edit_id=str(parsed_entity_id),
                )
                + "#edit-entity-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        if invalid_profile_scope:
            return RedirectResponse(
                url=build_users_new_url(
                    entity_error="Perfil de partilha inválido.",
                    menu="administrativo",
                    admin_tab="entidade",
                    entity_edit_id=str(parsed_entity_id),
                )
                + "#edit-entity-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        duplicate_id = session.scalar(
            select(Entity.id)
           .where(func.lower(Entity.name) == clean_name.lower(), Entity.id != parsed_entity_id)
           .limit(1)
        )
        if duplicate_id is not None:
            return RedirectResponse(
                url=build_users_new_url(
                    entity_error="Já existe outra entidade com este nome.",
                    menu="administrativo",
                    admin_tab="entidade",
                    entity_edit_id=str(parsed_entity_id),
                )
                + "#edit-entity-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if clean_profile_scope == ENTITY_PROFILE_SCOPE_OWNER:
            if not entity_permissions["can_manage_all_entities"]:
                return RedirectResponse(
                    url=build_users_new_url(
                        entity_error="Apenas a entidade Owner pode definir perfil Owner.",
                        menu="administrativo",
                        admin_tab="entidade",
                        entity_edit_id=str(parsed_entity_id),
                    )
                    + "#edit-entity-card",
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            existing_owner_id = session.scalar(
                select(Entity.id)
               .where(
                    Entity.profile_scope == ENTITY_PROFILE_SCOPE_OWNER,
                    Entity.id != parsed_entity_id,
                )
               .limit(1)
            )
            if existing_owner_id is not None:
                return RedirectResponse(
                    url=build_users_new_url(
                        entity_error="Já existe outra entidade com perfil Owner. Apenas uma é permitida.",
                        menu="administrativo",
                        admin_tab="entidade",
                        entity_edit_id=str(parsed_entity_id),
                    )
                    + "#edit-entity-card",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        current_logo_url = entity.logo_url or ""
        stored_logo_url, logo_error = save_entity_logo_upload(entity_logo_file)
        if logo_error:
            return RedirectResponse(
                url=build_users_new_url(
                    entity_error=logo_error,
                    menu="administrativo",
                    admin_tab="entidade",
                    entity_edit_id=str(parsed_entity_id),
                )
                + "#edit-entity-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        delete_old_logo_after_commit = ""
        if stored_logo_url:
            entity.logo_url = stored_logo_url
            if current_logo_url.startswith("/static/entities/") and current_logo_url != stored_logo_url:
                delete_old_logo_after_commit = current_logo_url
        elif remove_logo == "1":
            entity.logo_url = None
            if current_logo_url.startswith("/static/entities/"):
                delete_old_logo_after_commit = current_logo_url

        entity.name = clean_name
        entity.acronym = clean_acronym or None
        entity.tax_id = clean_tax_id or None
        entity.email = clean_email or None
        entity.responsible_name = clean_responsible_name or None
        entity.door_number = clean_door_number or None
        entity.address = clean_address or None
        entity.freguesia = clean_freguesia or None
        entity.postal_code = clean_postal_code or None
        entity.country = clean_country or None
        entity.phone = clean_phone or None
        entity.profile_scope = clean_profile_scope
        if clean_description is not None:
            entity.description = clean_description or None
        if can_manage_all_entities:
            entity.is_active = clean_status == "active"

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            if stored_logo_url.startswith("/static/entities/"):
                (BASE_DIR / stored_logo_url.lstrip("/")).unlink(missing_ok=True)
            return RedirectResponse(
                url=build_users_new_url(
                    entity_error="Não foi possível gravar alterações da entidade.",
                    menu="administrativo",
                    admin_tab="entidade",
                    entity_edit_id=str(parsed_entity_id),
                )
                + "#edit-entity-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    if delete_old_logo_after_commit:
        (BASE_DIR / delete_old_logo_after_commit.lstrip("/")).unlink(missing_ok=True)

    return RedirectResponse(
        url=build_users_new_url(
            entity_success="Entidade atualizada com sucesso.",
            menu="administrativo",
            admin_tab="entidade",
        )
        + "#create-entity-card",
        status_code=status.HTTP_303_SEE_OTHER,
    )
