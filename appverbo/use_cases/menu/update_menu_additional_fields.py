from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.menu.configuracao import MENU_CONFIG
from appverbo.admin_subprocesses.repositories.menu_repository import MenuAdminRepository
from appverbo.services.menu_additional_fields_access import (
    build_menu_additional_fields_access_v1,
)
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.menu.outcome import (
    MenuActionOutcome,
    build_menu_return_url_with_message_v1,
    build_menu_settings_redirect_url_v1,
    sanitize_menu_return_url_v1,
)
from appverbo.use_cases.menu.policies import (
    ensure_menu_additional_fields_owner_scope_v1,
    ensure_actor_can_manage_menu_v1,
    ensure_actor_is_owner_for_menu_v1,
    ensure_menu_can_edit_additional_fields_v1,
    ensure_menu_exists_v1,
    ensure_menu_in_scope_v1,
)


# ###################################################################################
# (1) MODELOS DE ENTRADA
# ###################################################################################


@dataclass(frozen=True)
class MoveMenuAdditionalFieldInput:
    menu_key: str
    field_key: str
    direction: str
    redirect_menu: str
    redirect_target: str
    subprocess_return_url: str


@dataclass(frozen=True)
class UpdateMenuAdditionalFieldsInput:
    menu_key: str
    fields: list[dict[str, str]]
    redirect_menu: str
    redirect_target: str
    subprocess_return_url: str


def normalize_move_menu_additional_field_input_v1(
    *,
    menu_key: str,
    field_key: str,
    direction: str,
    redirect_menu: str = "administrativo",
    redirect_target: str = "#settings-menu-edit-card",
    subprocess_return_url: str = "",
) -> MoveMenuAdditionalFieldInput:
    return MoveMenuAdditionalFieldInput(
        menu_key=str(menu_key or "").strip().lower(),
        field_key=str(field_key or "").strip().lower(),
        direction=str(direction or "").strip().lower(),
        redirect_menu=str(redirect_menu or "administrativo").strip() or "administrativo",
        redirect_target=str(redirect_target or "#settings-menu-edit-card").strip() or "#settings-menu-edit-card",
        subprocess_return_url=str(subprocess_return_url or "").strip(),
    )


def normalize_update_menu_additional_fields_input_v1(
    *,
    menu_key: str,
    additional_field_key: list[str],
    additional_field_label: list[str],
    additional_field_type: list[str],
    additional_field_required: list[str],
    additional_field_size: list[str],
    additional_field_list_key: list[str],
    redirect_menu: str = "administrativo",
    redirect_target: str = "#settings-menu-edit-card",
    subprocess_return_url: str = "",
) -> UpdateMenuAdditionalFieldsInput:
    rows_count = max(
        len(additional_field_key or []),
        len(additional_field_label or []),
        len(additional_field_type or []),
        len(additional_field_required or []),
        len(additional_field_size or []),
        len(additional_field_list_key or []),
    )

    fields: list[dict[str, str]] = []
    for row_index in range(rows_count):
        fields.append(
            {
                "key": additional_field_key[row_index] if row_index < len(additional_field_key or []) else "",
                "label": additional_field_label[row_index] if row_index < len(additional_field_label or []) else "",
                "field_type": additional_field_type[row_index] if row_index < len(additional_field_type or []) else "",
                "is_required": additional_field_required[row_index] if row_index < len(additional_field_required or []) else "",
                "size": additional_field_size[row_index] if row_index < len(additional_field_size or []) else "",
                "list_key": additional_field_list_key[row_index] if row_index < len(additional_field_list_key or []) else "",
            }
        )

    return UpdateMenuAdditionalFieldsInput(
        menu_key=str(menu_key or "").strip().lower(),
        fields=fields,
        redirect_menu=str(redirect_menu or "administrativo").strip() or "administrativo",
        redirect_target=str(redirect_target or "#settings-menu-edit-card").strip() or "#settings-menu-edit-card",
        subprocess_return_url=str(subprocess_return_url or "").strip(),
    )


# ###################################################################################
# (2) USE CASES
# ###################################################################################


def _build_additional_fields_return_url_v1(payload: Any) -> str:
    if str(payload.subprocess_return_url or "").strip():
        return sanitize_menu_return_url_v1(
            payload.subprocess_return_url,
            default_target=payload.redirect_target or "#settings-menu-edit-card",
        )
    return build_menu_settings_redirect_url_v1(
        redirect_menu=payload.redirect_menu,
        redirect_target=payload.redirect_target,
        settings_edit_key=payload.menu_key,
        settings_action="edit",
        settings_tab="campos-adicionais",
    )


def _validate_common_additional_field_permissions_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: Any,
    repository: MenuAdminRepository,
    return_url: str,
) -> tuple[MenuActionOutcome | None, dict[str, Any]]:
    policy_error = ensure_actor_can_manage_menu_v1(session=session, actor_user=actor_user)
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        ), {}

    permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"] or ""),
        selected_entity_id,
    )

    policy_error = ensure_actor_is_owner_for_menu_v1(permissions=permissions)
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        ), {}

    policy_error = ensure_menu_in_scope_v1(permissions=permissions)
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        ), {}

    policy_error = ensure_menu_exists_v1(
        repository=repository,
        session=session,
        menu_key=payload.menu_key,
        selected_entity_id=selected_entity_id,
    )
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        ), {}

    policy_error = ensure_menu_can_edit_additional_fields_v1(menu_key=payload.menu_key)
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        ), {}

    access = build_menu_additional_fields_access_v1(
        session=session,
        selected_entity_id=selected_entity_id,
        can_manage_all_entities=bool(permissions.get("can_manage_all_entities")),
    )
    policy_error = ensure_menu_additional_fields_owner_scope_v1(
        can_edit=bool(access.get("can_edit"))
    )
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        ), access

    return None, access


def execute_move_menu_additional_field_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: MoveMenuAdditionalFieldInput,
) -> MenuActionOutcome:
    repository = MenuAdminRepository(MENU_CONFIG)
    return_url = _build_additional_fields_return_url_v1(payload)

    blocked, access = _validate_common_additional_field_permissions_v1(
        session=session,
        actor_user=actor_user,
        selected_entity_id=selected_entity_id,
        payload=payload,
        repository=repository,
        return_url=return_url,
    )
    if blocked is not None:
        return blocked

    ok, error_message = repository.move_additional_field(
        session=session,
        menu_key=payload.menu_key,
        field_key=payload.field_key,
        direction=payload.direction,
        selected_entity_id=access.get("edit_entity_id"),
    )
    if not ok:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=error_message or "Não foi possível mover o campo adicional.",
        )

    return build_menu_return_url_with_message_v1(
        return_url=return_url,
        message_key="success",
        message="Campo adicional movido com sucesso.",
    )


def execute_update_menu_additional_fields_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: UpdateMenuAdditionalFieldsInput,
) -> MenuActionOutcome:
    repository = MenuAdminRepository(MENU_CONFIG)
    return_url = _build_additional_fields_return_url_v1(payload)

    blocked, access = _validate_common_additional_field_permissions_v1(
        session=session,
        actor_user=actor_user,
        selected_entity_id=selected_entity_id,
        payload=payload,
        repository=repository,
        return_url=return_url,
    )
    if blocked is not None:
        return blocked

    ok, error_message = repository.update_additional_fields(
        session=session,
        menu_key=payload.menu_key,
        fields=payload.fields,
        selected_entity_id=access.get("edit_entity_id"),
    )
    if not ok:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=error_message or "Não foi possível atualizar os campos adicionais.",
        )

    return build_menu_return_url_with_message_v1(
        return_url=return_url,
        message_key="success",
        message="Campos adicionais e hierarquia atualizados com sucesso.",
    )
