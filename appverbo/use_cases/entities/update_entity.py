from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.entities.outcome import EntityActionOutcome
from appverbo.use_cases.entities.policies import (
    ensure_actor_can_manage_entities_v1,
    ensure_can_set_owner_scope_v1,
    ensure_entity_in_scope_v1,
)


# ###################################################################################
# (1) MODELO DE ENTRADA
# ###################################################################################

@dataclass(frozen=True)
class UpdateEntityInput:
    clean_entity_id: str
    clean_status: str
    form_data: dict[str, str]
    invalid_profile_scope: bool
    remove_logo: bool
    include_description: bool
    entity_logo_file: Any | None


def normalize_update_entity_input_v1(
    *,
    entity_id: str,
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
    description: str | None,
    entity_status: str = "active",
    entity_profile_scope: str,
    remove_logo: str | None,
    entity_logo_file: Any | None,
) -> UpdateEntityInput:
    clean_entity_id = str(entity_id or "").strip()
    clean_status = str(entity_status or "").strip().lower()

    if clean_status not in {"active", "inactive"}:
        clean_status = "active"

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

    return UpdateEntityInput(
        clean_entity_id=clean_entity_id,
        clean_status=clean_status,
        form_data=form_data,
        invalid_profile_scope=invalid_profile_scope,
        remove_logo=str(remove_logo or "").strip() == "1",
        include_description=isinstance(description, str),
        entity_logo_file=entity_logo_file,
    )


# ###################################################################################
# (2) HELPERS DE REDIRECT E FICHEIROS
# ###################################################################################

def _build_entity_update_redirect_v1(
    *,
    entity_success: str = "",
    entity_error: str = "",
    entity_edit_id: int | None = None,
    anchor: str = "#edit-entity-card",
) -> str:
    query_kwargs: dict[str, str] = {
        "entity_success": entity_success,
        "entity_error": entity_error,
        "menu": "administrativo",
        "admin_tab": "entidade",
    }

    if entity_edit_id is not None:
        query_kwargs["entity_edit_id"] = str(entity_edit_id)

    return build_users_new_url(**query_kwargs) + anchor


def _remove_local_logo_if_exists_v1(logo_url: str) -> None:
    clean_logo_url = str(logo_url or "").strip()

    if not clean_logo_url.startswith("/static/entities/"):
        return

    local_logo_path = BASE_DIR / clean_logo_url.lstrip("/")
    local_logo_path.unlink(missing_ok=True)


# ###################################################################################
# (3) USE CASE PRINCIPAL
# ###################################################################################

def execute_update_entity_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: UpdateEntityInput,
) -> EntityActionOutcome:
    if not payload.clean_entity_id.isdigit():
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_update_redirect_v1(
                entity_error="Entidade inválida para edição.",
                anchor="#edit-entity-card",
            ),
        )

    parsed_entity_id = int(payload.clean_entity_id)
    repository = EntityAdminRepository(ENTIDADE_CONFIG)

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

    permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    scope_error = ensure_entity_in_scope_v1(
        entity_id=parsed_entity_id,
        permissions=permissions,
        action_label="editar",
    )

    if scope_error:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_update_redirect_v1(
                entity_error=scope_error,
                anchor="#recent-entities-card",
            ),
        )

    entity = repository.get_by_id(
        session=session,
        entity_id=parsed_entity_id,
    )

    if entity is None:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_update_redirect_v1(
                entity_error="Entidade não encontrada.",
                anchor="#create-entity-card",
            ),
        )

    clean_status = payload.clean_status

    if not permissions.get("can_manage_all_entities"):
        clean_status = "active" if bool(entity.is_active) else "inactive"

    required_field_labels = validate_entity_required_fields_v1(payload.form_data)

    if payload.invalid_profile_scope:
        required_field_labels.append("Perfil de partilha")

    if required_field_labels:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_update_redirect_v1(
                entity_error=(
                    "Preencha os campos obrigatórios: "
                    + ", ".join(required_field_labels)
                    + "."
                ),
                entity_edit_id=parsed_entity_id,
            ),
        )

    duplicate_entity_id = repository.find_duplicate_name_id(
        session=session,
        name=payload.form_data.get("name", ""),
        ignore_entity_id=parsed_entity_id,
    )

    if duplicate_entity_id is not None:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_update_redirect_v1(
                entity_error="Já existe outra entidade com este nome.",
                entity_edit_id=parsed_entity_id,
            ),
        )

    owner_scope_error = ensure_can_set_owner_scope_v1(
        repository=repository,
        session=session,
        target_profile_scope=payload.form_data.get("profile_scope", ""),
        permissions=permissions,
        ignore_entity_id=parsed_entity_id,
    )

    if owner_scope_error:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_update_redirect_v1(
                entity_error=owner_scope_error,
                entity_edit_id=parsed_entity_id,
            ),
        )

    current_logo_url = str(entity.logo_url or "").strip()
    stored_logo_url, logo_error = save_entity_logo_upload(payload.entity_logo_file)

    if logo_error:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_update_redirect_v1(
                entity_error=logo_error,
                entity_edit_id=parsed_entity_id,
            ),
        )

    delete_old_logo_after_commit = ""

    if stored_logo_url:
        entity.logo_url = stored_logo_url

        if (
            current_logo_url.startswith("/static/entities/")
            and current_logo_url != stored_logo_url
        ):
            delete_old_logo_after_commit = current_logo_url
    elif payload.remove_logo:
        entity.logo_url = None

        if current_logo_url.startswith("/static/entities/"):
            delete_old_logo_after_commit = current_logo_url

    repository.update_entity(
        session=session,
        entity=entity,
        form_data=payload.form_data,
        clean_status=clean_status,
        include_description=payload.include_description,
    )

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        _remove_local_logo_if_exists_v1(stored_logo_url)

        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_update_redirect_v1(
                entity_error="Não foi possível gravar alterações da entidade.",
                entity_edit_id=parsed_entity_id,
            ),
        )

    if delete_old_logo_after_commit:
        _remove_local_logo_if_exists_v1(delete_old_logo_after_commit)

    return EntityActionOutcome(
        kind="redirect",
        redirect_url=_build_entity_update_redirect_v1(
            entity_success="Entidade atualizada com sucesso.",
            anchor="#create-entity-card",
        ),
    )

