from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, File, Form, Query, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appgenesis.core import (
    BASE_DIR,
    ENTITY_PROFILE_SCOPE_LEGADO,
    ENTITY_PROFILE_SCOPE_OWNER,
)
from appgenesis.db.session import SessionLocal
from appgenesis.services.auth import is_admin_user
from appgenesis.services.entities import (
    apply_entity_form_data_v1,
    clean_entity_form_data_v1,
    get_duplicate_entity_name_id_v1,
    get_existing_owner_entity_id_v1,
    save_entity_logo_upload,
    validate_entity_required_fields_v1,
)
from appgenesis.services.navigation_context import build_post_save_return_url_v1, build_return_url_v1
from appgenesis.services.page import build_users_new_url
from appgenesis.services.permissions import (
    get_user_entity_permissions,
    is_entity_within_permissions,
)
from appgenesis.services.session import get_current_user, get_session_entity_id
from appgenesis.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    User,
    UserAccountStatus,
)

from appgenesis.routes.entities.router import router

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
    city: str = Form(...),
    freguesia: str = Form(...),
    postal_code: str = Form(...),
    country: str = Form(...),
    phone: str = Form(...),
    description: str | None = Form(default=None),
    entity_status: str = Form("active"),
    entity_profile_scope: str = Form(ENTITY_PROFILE_SCOPE_LEGADO),
    remove_logo: str | None = Form(default=None),
    entity_logo_file: UploadFile | None = File(default=None),
    return_menu: str = Form(""),
    return_admin_tab: str = Form(""),
    return_target: str = Form(""),
) -> HTMLResponse:
    clean_entity_id = entity_id.strip()
    entity_form_data, invalid_profile_scope = clean_entity_form_data_v1(
        name=name,
        acronym=acronym,
        tax_id=tax_id,
        email=email,
        responsible_name=responsible_name,
        door_number=door_number,
        address=address,
        city=city,
        freguesia=freguesia,
        postal_code=postal_code,
        country=country,
        phone=phone,
        entity_profile_scope=entity_profile_scope,
        description=description,
    )
    clean_name = entity_form_data["name"]
    clean_profile_scope = entity_form_data["profile_scope"]
    clean_status = entity_status.strip().lower()

    if not clean_entity_id.isdigit():
        return RedirectResponse(
            url=build_return_url_v1(
                return_menu=return_menu,
                return_admin_tab=return_admin_tab,
                default_menu="administrativo",
                default_admin_tab="entidade",
                default_hash="#edit-entity-card",
                entity_error="Entidade inválida para edição.",
            ),
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
        can_manage_tenant_structure = bool(entity_permissions.get("can_manage_tenant_structure", entity_permissions.get("can_manage_all_entities", False)))
        if not is_entity_within_permissions(parsed_entity_id, entity_permissions):
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#recent-entities-card",
                    entity_error="Sem permissão para editar esta entidade.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        entity = session.get(Entity, parsed_entity_id)
        if entity is None:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#create-entity-card",
                    entity_error="Entidade não encontrada.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        if not can_manage_tenant_structure:
            clean_status = "active" if entity.is_active else "inactive"

        required_field_labels = validate_entity_required_fields_v1(entity_form_data)
        if invalid_profile_scope:
            required_field_labels.append("Perfil de partilha")

        if required_field_labels:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#edit-entity-card",
                    entity_error=(
                        "Preencha os campos obrigatórios: "
                        + ", ".join(required_field_labels)
                        + "."
                    ),
                    entity_edit_id=str(parsed_entity_id),
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        if invalid_profile_scope:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#edit-entity-card",
                    entity_error="Perfil de partilha inválido.",
                    entity_edit_id=str(parsed_entity_id),
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        duplicate_id = get_duplicate_entity_name_id_v1(
            session,
            clean_name,
            ignore_entity_id=parsed_entity_id,
        )
        if duplicate_id is not None:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#edit-entity-card",
                    entity_error="Já existe outra entidade com este nome.",
                    entity_edit_id=str(parsed_entity_id),
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if clean_profile_scope == ENTITY_PROFILE_SCOPE_OWNER:
            if not entity_permissions.get("can_manage_tenant_structure", entity_permissions.get("can_manage_all_entities", False)):
                return RedirectResponse(
                    url=build_return_url_v1(
                        return_menu=return_menu,
                        return_admin_tab=return_admin_tab,
                        default_menu="administrativo",
                        default_admin_tab="entidade",
                        default_hash="#edit-entity-card",
                        entity_error="Apenas a entidade Owner pode definir perfil Owner.",
                        entity_edit_id=str(parsed_entity_id),
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            existing_owner_id = get_existing_owner_entity_id_v1(
                session,
                ignore_entity_id=parsed_entity_id,
            )
            if existing_owner_id is not None:
                return RedirectResponse(
                    url=build_return_url_v1(
                        return_menu=return_menu,
                        return_admin_tab=return_admin_tab,
                        default_menu="administrativo",
                        default_admin_tab="entidade",
                        default_hash="#edit-entity-card",
                        entity_error="Já existe outra entidade com perfil Owner. Apenas uma é permitida.",
                        entity_edit_id=str(parsed_entity_id),
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        # ###################################################################################
        # (1) IMPEDIR OWNER INATIVA
        # ###################################################################################
        if (
            (entity.profile_scope or ENTITY_PROFILE_SCOPE_LEGADO) == ENTITY_PROFILE_SCOPE_OWNER
            and clean_status != "active"
        ):
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#edit-entity-card",
                    entity_error="A entidade Owner não pode ser definida como inativa.",
                    entity_edit_id=str(parsed_entity_id),
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        current_logo_url = entity.logo_url or ""
        stored_logo_url, logo_error = save_entity_logo_upload(entity_logo_file)
        if logo_error:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#edit-entity-card",
                    entity_error=logo_error,
                    entity_edit_id=str(parsed_entity_id),
                ),
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

        apply_entity_form_data_v1(
            entity,
            entity_form_data,
            include_description=isinstance(description, str),
        )
        if can_manage_tenant_structure:
            entity.is_active = clean_status == "active"

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            if stored_logo_url.startswith("/static/entities/"):
                (BASE_DIR / stored_logo_url.lstrip("/")).unlink(missing_ok=True)
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#edit-entity-card",
                    entity_error="Não foi possível gravar alterações da entidade.",
                    entity_edit_id=str(parsed_entity_id),
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    if delete_old_logo_after_commit:
        (BASE_DIR / delete_old_logo_after_commit.lstrip("/")).unlink(missing_ok=True)

    return RedirectResponse(
        url=build_post_save_return_url_v1(
            return_menu=return_menu,
            return_admin_tab=return_admin_tab,
            default_menu="administrativo",
            default_admin_tab="entidade",
            default_hash="#recent-entities-card",
            entity_success="Entidade atualizada com sucesso.",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
