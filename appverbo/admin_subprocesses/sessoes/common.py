from __future__ import annotations

####################################################################################
# (1) IMPORTS
####################################################################################

from dataclasses import replace
from typing import Any
from urllib.parse import urlencode

from appverbo.admin_subprocesses.models import AdminFieldConfig
from appverbo.admin_subprocesses.sessoes.config import SESSOES_CONFIG

SESSOES_PROCESS_MENU_KEY_V2 = "sessoes"
SESSOES_DEFAULT_ADMIN_TAB_V2 = "sessoes"
SESSOES_DEFAULT_TARGET_V2 = "admin-sidebar-sections-card"
SESSOES_SYSTEM_COLUMN_KEY_V2 = "system"
SESSOES_SYSTEM_FIELD_KEY_V2 = "visibility_scope_mode"
SESSOES_ENTITY_FIELD_KEY_V2 = "entity_internal_number"


####################################################################################
# (2) CENTRALIZED ACCESS TO THE SESSOES SUBPROCESS CONFIG
####################################################################################

def get_sessoes_config_v2() -> Any:
    return SESSOES_CONFIG


def get_sessoes_key_v2() -> str:
    return str(getattr(SESSOES_CONFIG, "key", "sessoes"))


def get_sessoes_title_v2() -> str:
    title = getattr(SESSOES_CONFIG, "title", None)

    if title:
        return str(title)

    label = getattr(SESSOES_CONFIG, "label", None)

    if label:
        return str(label)

    name = getattr(SESSOES_CONFIG, "name", None)

    if name:
        return str(name)

    return "Sessões"


def is_sessoes_config_v2(config: Any) -> bool:
    config_key = str(getattr(config, "key", "") or "")
    return config_key == get_sessoes_key_v2()


####################################################################################
# (3) CENTRALIZED URLS FOR THE ESTRUTURAS PROCESS
####################################################################################

def build_sessoes_admin_return_url_v2(
    *,
    admin_tab: object = SESSOES_DEFAULT_ADMIN_TAB_V2,
    target: object = SESSOES_DEFAULT_TARGET_V2,
    extra_query: dict[str, object] | None = None,
    fragment: object | None = None,
) -> str:
    clean_admin_tab = str(admin_tab or SESSOES_DEFAULT_ADMIN_TAB_V2).strip().lower()
    if not clean_admin_tab:
        clean_admin_tab = SESSOES_DEFAULT_ADMIN_TAB_V2

    clean_target = str(target or SESSOES_DEFAULT_TARGET_V2).strip().lstrip("#")
    if not clean_target:
        clean_target = SESSOES_DEFAULT_TARGET_V2

    params: list[tuple[str, str]] = [
        ("menu", SESSOES_PROCESS_MENU_KEY_V2),
        ("admin_tab", clean_admin_tab),
        ("target", clean_target),
    ]

    if clean_admin_tab == SESSOES_DEFAULT_ADMIN_TAB_V2:
        params.append(("sidebar_sections_tab", SESSOES_DEFAULT_ADMIN_TAB_V2))

    for raw_key, raw_value in (extra_query or {}).items():
        clean_key = str(raw_key or "").strip()
        clean_value = str(raw_value or "").strip()

        if not clean_key or not clean_value:
            continue

        if clean_key in {"menu", "admin_tab"}:
            continue

        if clean_key == "target":
            clean_value = clean_value.lstrip("#")

        params.append((clean_key, clean_value))

    clean_fragment = str(fragment or clean_target).strip().lstrip("#") or clean_target
    return f"/users/new?{urlencode(params)}#{clean_fragment}"


####################################################################################
# (4) CENTRALIZED ACCESS TO FIELDS AND COLUMNS
####################################################################################

def get_sessoes_fields_v2() -> list[Any]:
    fields = getattr(SESSOES_CONFIG, "fields", None)

    if not fields:
        return []

    return list(fields)


def get_sessoes_columns_v2() -> list[Any]:
    columns = getattr(SESSOES_CONFIG, "columns", None)

    if not columns:
        return []

    return list(columns)


def can_view_sessoes_system_column_v2(current_entity_scope: object) -> bool:
    clean_scope = str(current_entity_scope or "").strip().lower()
    return clean_scope == "owner"


def can_manage_sessoes_system_field_v2(current_entity_scope: object) -> bool:
    return can_view_sessoes_system_column_v2(current_entity_scope)


def get_sessoes_visible_columns_v2(current_entity_scope: object = "") -> list[Any]:
    columns = get_sessoes_columns_v2()

    if can_view_sessoes_system_column_v2(current_entity_scope):
        return columns

    return [
        column
        for column in columns
        if str(getattr(column, "key", "") or "").strip().lower() != SESSOES_SYSTEM_COLUMN_KEY_V2
    ]


def build_sessoes_entity_readonly_field_v2() -> AdminFieldConfig:
    return AdminFieldConfig(
        key=SESSOES_ENTITY_FIELD_KEY_V2,
        label="Nº Entidade",
        input_name="section_entity_internal_number_display",
        field_type="readonly",
        readonly_on_create=True,
        readonly_on_edit=True,
        css_class="admin-subprocess-scope-field-v1",
    )


def get_sessoes_visible_fields_v2(current_entity_scope: object = "") -> list[Any]:
    fields = get_sessoes_fields_v2()

    if can_manage_sessoes_system_field_v2(current_entity_scope):
        return fields

    visible_fields: list[Any] = []

    for field in fields:
        field_key = str(getattr(field, "key", "") or "").strip().lower()

        if field_key == SESSOES_SYSTEM_FIELD_KEY_V2:
            visible_fields.append(replace(field, field_type="hidden", required=False))
            continue

        if field_key == SESSOES_ENTITY_FIELD_KEY_V2:
            visible_fields.append(build_sessoes_entity_readonly_field_v2())
            continue

        visible_fields.append(field)

    return visible_fields


def get_sessoes_field_keys_v2() -> list[str]:
    field_keys: list[str] = []

    for field in get_sessoes_fields_v2():
        field_key = getattr(field, "key", None)

        if field_key:
            field_keys.append(str(field_key))

    return field_keys


def get_sessoes_column_keys_v2() -> list[str]:
    column_keys: list[str] = []

    for column in get_sessoes_columns_v2():
        column_key = getattr(column, "key", None)

        if column_key:
            column_keys.append(str(column_key))

    return column_keys


####################################################################################
# (5) SAFE CONTEXT FOR THE SESSOES SUBPROCESS
####################################################################################

def build_sessoes_context_v2(context: dict[str, Any] | None = None) -> dict[str, Any]:
    safe_context = dict(context or {})
    safe_context["subprocess_key"] = get_sessoes_key_v2()
    safe_context["subprocess_title"] = get_sessoes_title_v2()
    safe_context["subprocess_fields"] = get_sessoes_field_keys_v2()
    safe_context["subprocess_columns"] = get_sessoes_column_keys_v2()
    safe_context["uses_generic_v2_crud"] = True
    safe_context["has_custom_create_service"] = False
    safe_context["has_custom_delete_service"] = False
    safe_context["has_custom_resend_service"] = False
    return safe_context


####################################################################################
# (6) V1 COMPATIBILITY NAMES
####################################################################################

def get_sessoes_config_v1() -> Any:
    return get_sessoes_config_v2()


def get_sessoes_key_v1() -> str:
    return get_sessoes_key_v2()


def get_sessoes_title_v1() -> str:
    return get_sessoes_title_v2()


def build_sessoes_admin_return_url_v1(
    *,
    admin_tab: object = SESSOES_DEFAULT_ADMIN_TAB_V2,
    target: object = SESSOES_DEFAULT_TARGET_V2,
    extra_query: dict[str, object] | None = None,
    fragment: object | None = None,
) -> str:
    return build_sessoes_admin_return_url_v2(
        admin_tab=admin_tab,
        target=target,
        extra_query=extra_query,
        fragment=fragment,
    )


def get_sessoes_fields_v1() -> list[Any]:
    return get_sessoes_fields_v2()


def get_sessoes_columns_v1() -> list[Any]:
    return get_sessoes_columns_v2()


def can_view_sessoes_system_column_v1(current_entity_scope: object) -> bool:
    return can_view_sessoes_system_column_v2(current_entity_scope)


def get_sessoes_visible_columns_v1(current_entity_scope: object = "") -> list[Any]:
    return get_sessoes_visible_columns_v2(current_entity_scope)


def build_sessoes_context_v1(context: dict[str, Any] | None = None) -> dict[str, Any]:
    return build_sessoes_context_v2(context)
