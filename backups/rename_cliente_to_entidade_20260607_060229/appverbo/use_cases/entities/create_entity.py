from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.entidade.configuracao import ENTIDADE_CONFIG
from appverbo.admin_subprocesses.repositories.entity_repository import EntityAdminRepository
from appverbo.core import BASE_DIR
from appverbo.services.entities import (
    clean_entity_form_data_v1,
    save_entity_logo_upload,
    validate_entity_required_fields_v1,
)
from appverbo.services.page import (
    build_users_new_url,
    get_form_defaults,
    get_page_data,
)
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.profile import get_user_personal_data
from appverbo.use_cases.entities.get_entity_edit import get_entity_edit_defaults_v1
from appverbo.use_cases.entities.outcome import EntityActionOutcome
from appverbo.use_cases.entities.policies import (
    ensure_actor_can_create_entity_v1,
    ensure_actor_can_manage_entities_v1,
    ensure_can_set_owner_scope_v1,
)


# ###################################################################################
# (1) MODELO DE ENTRADA
# ###################################################################################

@dataclass(frozen=True)
class CreateEntityInput:
    form_data: dict[str, str]
    invalid_profile_scope: bool
    entity_logo_file: Any | None


def normalize_create_entity_input_v1(
    *,
    name: str,
    acronym: str = "",
    tax_id: str,
    email: str,
    responsible_name: str,
    door_number: str,
    address: str,
    city: str,
    freguesia: str,
    postal_code: str,
    country: str,
    phone: str,
    entity_profile_scope: str,
    description: str | None,
    entity_logo_file: Any | None,
) -> CreateEntityInput:
    form_data, invalid_profile_scope = clean_entity_form_data_v1(
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

    return CreateEntityInput(
        form_data=form_data,
        invalid_profile_scope=invalid_profile_scope,
        entity_logo_file=entity_logo_file,
    )


# ###################################################################################
# (2) HELPERS DE CONTEXTO E REDIRECT
# ###################################################################################

def _build_entity_create_redirect_v1(
    *,
    entity_success: str = "",
    entity_error: str = "",
    menu: str = "administrativo",
) -> str:
    return (
        build_users_new_url(
            entity_success=entity_success,
            entity_error=entity_error,
            menu=menu,
            admin_tab="entidade" if menu == "administrativo" else "",
        )
        + "#create-entity-card"
    )


def _remove_local_logo_if_exists_v1(logo_url: str) -> None:
    clean_logo_url = str(logo_url or "").strip()

    if not clean_logo_url.startswith("/static/entities/"):
        return

    local_logo_path = BASE_DIR / clean_logo_url.lstrip("/")
    local_logo_path.unlink(missing_ok=True)


def _build_template_context_v1(
    *,
    session: Session,
    request: Request,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    entity_form_data: dict[str, str],
    entity_error: str,
    repository: EntityAdminRepository,
    permissions: dict[str, Any],
) -> dict[str, Any]:
    page_data = get_page_data(
        session,
        actor_user_id=int(actor_user["id"]),
        actor_login_email=str(actor_user["login_email"]),
        selected_entity_id=selected_entity_id,
    )
    user_personal_data = get_user_personal_data(
        session,
        int(actor_user["id"]),
        selected_entity_id,
    )

    return {
        "request": request,
        "errors": [],
        "success": "",
        "form_data": get_form_defaults(),
        "entity_form_data": entity_form_data,
        "entity_edit_data": get_entity_edit_defaults_v1(),
        "current_user": actor_user,
        "current_user_is_admin": bool(permissions.get("is_admin")),
        "current_user_can_manage_all_entities": bool(permissions.get("can_manage_all_entities")),
        "user_personal_data": user_personal_data,
        "entity_success": "",
        "entity_error": entity_error,
        "next_entity_internal_number": str(repository.get_next_internal_number(session=session)),
        "profile_success": "",
        "profile_error": "",
        "profile_tab": "pessoal",
        "initial_menu": "administrativo",
        "admin_tab": "entidade",
        **page_data,
    }


# ###################################################################################
# (3) USE CASE PRINCIPAL
# ###################################################################################

def execute_create_entity_v1(
    *,
    session: Session,
    request: Request,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: CreateEntityInput,
) -> EntityActionOutcome:
    repository = EntityAdminRepository(ENTIDADE_CONFIG)

    permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    admin_error = ensure_actor_can_manage_entities_v1(
        session=session,
        actor_user=actor_user,
    )

    if admin_error:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                entity_error=admin_error,
                menu="perfil",
            ),
        )

    create_permission_error = ensure_actor_can_create_entity_v1(permissions=permissions)

    if create_permission_error:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_create_redirect_v1(
                entity_error=create_permission_error,
            ),
        )

    required_field_labels = validate_entity_required_fields_v1(payload.form_data)

    if payload.invalid_profile_scope:
        required_field_labels.append("Perfil de partilha")

    if required_field_labels:
        return EntityActionOutcome(
            kind="template",
            template_context=_build_template_context_v1(
                session=session,
                request=request,
                actor_user=actor_user,
                selected_entity_id=selected_entity_id,
                entity_form_data=payload.form_data,
                entity_error=(
                    "Preencha os campos obrigatórios: "
                    + ", ".join(required_field_labels)
                    + "."
                ),
                repository=repository,
                permissions=permissions,
            ),
        )

    duplicate_entity_id = repository.find_duplicate_name_id(
        session=session,
        name=payload.form_data.get("name", ""),
    )

    if duplicate_entity_id is not None:
        return EntityActionOutcome(
            kind="template",
            template_context=_build_template_context_v1(
                session=session,
                request=request,
                actor_user=actor_user,
                selected_entity_id=selected_entity_id,
                entity_form_data=payload.form_data,
                entity_error="Já existe uma entidade com este nome.",
                repository=repository,
                permissions=permissions,
            ),
        )

    owner_scope_error = ensure_can_set_owner_scope_v1(
        repository=repository,
        session=session,
        target_profile_scope=payload.form_data.get("profile_scope", ""),
        permissions=permissions,
        ignore_entity_id=None,
    )

    if owner_scope_error:
        return EntityActionOutcome(
            kind="template",
            template_context=_build_template_context_v1(
                session=session,
                request=request,
                actor_user=actor_user,
                selected_entity_id=selected_entity_id,
                entity_form_data=payload.form_data,
                entity_error=owner_scope_error,
                repository=repository,
                permissions=permissions,
            ),
        )

    stored_logo_url, logo_error = save_entity_logo_upload(payload.entity_logo_file)

    if logo_error:
        return EntityActionOutcome(
            kind="template",
            template_context=_build_template_context_v1(
                session=session,
                request=request,
                actor_user=actor_user,
                selected_entity_id=selected_entity_id,
                entity_form_data=payload.form_data,
                entity_error=logo_error,
                repository=repository,
                permissions=permissions,
            ),
        )

    entity = repository.create_entity(
        session=session,
        form_data=payload.form_data,
        logo_url=stored_logo_url,
        is_active=True,
    )

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        _remove_local_logo_if_exists_v1(stored_logo_url)

        return EntityActionOutcome(
            kind="template",
            template_context=_build_template_context_v1(
                session=session,
                request=request,
                actor_user=actor_user,
                selected_entity_id=selected_entity_id,
                entity_form_data=payload.form_data,
                entity_error="Não foi possível criar a entidade. Tente novamente.",
                repository=repository,
                permissions=permissions,
            ),
        )

    created_internal_number = (
        int(entity.internal_number)
        if isinstance(entity.internal_number, int)
        else repository.get_next_internal_number(session=session)
    )

    return EntityActionOutcome(
        kind="redirect",
        redirect_url=_build_entity_create_redirect_v1(
            entity_success=f"Entidade criada com sucesso. Nº Cliente: {created_internal_number}.",
        ),
    )
