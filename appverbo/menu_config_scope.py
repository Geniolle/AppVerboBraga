from __future__ import annotations

import copy
from typing import Any


MENU_CONFIG_ENTITY_SCOPES_KEY_V1 = "entity_scoped_overrides_v1"
MENU_CONFIG_SCOPE_MENU_LABEL_KEY_V1 = "menu_label"
MENU_CONFIG_SCOPE_SIDEBAR_SECTIONS_KEY_V1 = "sidebar_sections"
MENU_CONFIG_SCOPE_KEYS_V1 = frozenset(
    {
        "additional_fields",
        "visible_fields",
        "visible_field_headers",
        "process_visible_fields",
        "process_visible_headers",
        "process_visible_field_rows",
        "process_visible_field_header_map",
        "process_visible_fields_configured",
        "process_visible_fields_refresh_version",
        "process_additional_fields_refresh_version",
        "process_lists",
        "process_quantity_fields",
        "subsequent_fields",
        "sidebar_section",
        MENU_CONFIG_SCOPE_SIDEBAR_SECTIONS_KEY_V1,
        "sidebar_global_refresh_version",
        MENU_CONFIG_SCOPE_MENU_LABEL_KEY_V1,
    }
)


# ###################################################################################
# (1) NORMALIZACAO DOS OVERRIDES POR ENTIDADE
# ###################################################################################


def coerce_entity_scope_id_v1(value: object) -> int | None:
    clean_value = str(value or "").strip()

    if not clean_value.isdigit():
        return None

    parsed_value = int(clean_value)
    if parsed_value <= 0:
        return None

    return parsed_value


def _clone_menu_scope_value_v1(value: Any) -> Any:
    return copy.deepcopy(value)


def _normalize_keyed_menu_scope_row_v1(value: Any) -> tuple[str, Any]:
    if not isinstance(value, dict):
        return "", None

    clean_key = str(value.get("key") or "").strip().lower()

    if not clean_key:
        return "", None

    return clean_key, _clone_menu_scope_value_v1(value)


def _merge_scoped_sidebar_sections_v1(
    base_value: Any,
    scoped_value: Any,
) -> list[Any]:
    base_items = list(base_value) if isinstance(base_value, list) else []
    scoped_items = list(scoped_value) if isinstance(scoped_value, list) else []
    merged_items: list[Any] = []
    merged_index_by_key: dict[str, int] = {}

    for raw_item in base_items:
        clean_key, cloned_item = _normalize_keyed_menu_scope_row_v1(raw_item)

        if not clean_key or cloned_item is None:
            continue

        merged_index_by_key[clean_key] = len(merged_items)
        merged_items.append(cloned_item)

    for raw_item in scoped_items:
        clean_key, cloned_item = _normalize_keyed_menu_scope_row_v1(raw_item)

        if not clean_key or cloned_item is None:
            continue

        if clean_key in merged_index_by_key:
            merged_items[merged_index_by_key[clean_key]] = cloned_item
            continue

        merged_index_by_key[clean_key] = len(merged_items)
        merged_items.append(cloned_item)

    return merged_items


def _build_effective_menu_scope_value_v1(
    scope_key: str,
    base_value: Any,
    scoped_value: Any,
) -> Any:
    if scope_key == MENU_CONFIG_SCOPE_SIDEBAR_SECTIONS_KEY_V1:
        return _merge_scoped_sidebar_sections_v1(base_value, scoped_value)

    return _clone_menu_scope_value_v1(scoped_value)


def normalize_menu_entity_scopes_v1(
    menu_config: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    raw_menu_config = menu_config or {}
    raw_scopes = raw_menu_config.get(MENU_CONFIG_ENTITY_SCOPES_KEY_V1)

    if not isinstance(raw_scopes, dict):
        return {}

    normalized_scopes: dict[str, dict[str, Any]] = {}

    for raw_entity_id, raw_scope_values in raw_scopes.items():
        parsed_entity_id = coerce_entity_scope_id_v1(raw_entity_id)

        if parsed_entity_id is None or not isinstance(raw_scope_values, dict):
            continue

        normalized_scope_values: dict[str, Any] = {}

        for raw_scope_key, raw_scope_value in raw_scope_values.items():
            scope_key = str(raw_scope_key or "").strip()

            if not scope_key or scope_key not in MENU_CONFIG_SCOPE_KEYS_V1:
                continue

            normalized_scope_values[scope_key] = _clone_menu_scope_value_v1(raw_scope_value)

        normalized_scopes[str(parsed_entity_id)] = normalized_scope_values

    return normalized_scopes


def get_menu_entity_scope_overrides_v1(
    menu_config: dict[str, Any] | None,
    *,
    selected_entity_id: object,
) -> dict[str, Any]:
    parsed_selected_entity_id = coerce_entity_scope_id_v1(selected_entity_id)

    if parsed_selected_entity_id is None:
        return {}

    normalized_scopes = normalize_menu_entity_scopes_v1(menu_config)
    return dict(normalized_scopes.get(str(parsed_selected_entity_id), {}))


# ###################################################################################
# (2) RESOLUCAO DO CONFIG EFETIVO
# ###################################################################################


def build_effective_menu_config_v1(
    menu_config: dict[str, Any] | None,
    *,
    selected_entity_id: object,
) -> dict[str, Any]:
    effective_menu_config = _clone_menu_scope_value_v1(menu_config or {})
    scoped_overrides = get_menu_entity_scope_overrides_v1(
        effective_menu_config,
        selected_entity_id=selected_entity_id,
    )

    for scope_key in MENU_CONFIG_SCOPE_KEYS_V1:
        if scope_key == MENU_CONFIG_SCOPE_MENU_LABEL_KEY_V1:
            continue

        if scope_key not in scoped_overrides:
            continue

        effective_menu_config[scope_key] = _build_effective_menu_scope_value_v1(
            scope_key,
            effective_menu_config.get(scope_key),
            scoped_overrides[scope_key],
        )

    return effective_menu_config


def build_effective_menu_label_v1(
    menu_label: object,
    menu_config: dict[str, Any] | None,
    *,
    selected_entity_id: object,
) -> str:
    scoped_overrides = get_menu_entity_scope_overrides_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
    )
    scoped_menu_label = str(
        scoped_overrides.get(MENU_CONFIG_SCOPE_MENU_LABEL_KEY_V1) or ""
    ).strip()

    if scoped_menu_label:
        return scoped_menu_label

    return str(menu_label or "").strip()


# ###################################################################################
# (3) ESCRITA DOS OVERRIDES POR ENTIDADE
# ###################################################################################


def apply_entity_scoped_menu_config_updates_v1(
    menu_config: dict[str, Any] | None,
    *,
    selected_entity_id: object,
    updates: dict[str, Any] | None,
) -> dict[str, Any]:
    updated_menu_config = _clone_menu_scope_value_v1(menu_config or {})
    clean_updates = {
        str(raw_key or "").strip(): _clone_menu_scope_value_v1(raw_value)
        for raw_key, raw_value in (updates or {}).items()
        if str(raw_key or "").strip() in MENU_CONFIG_SCOPE_KEYS_V1
    }

    if not clean_updates:
        return updated_menu_config

    parsed_selected_entity_id = coerce_entity_scope_id_v1(selected_entity_id)

    if parsed_selected_entity_id is None:
        for scope_key, scope_value in clean_updates.items():
            if scope_key == MENU_CONFIG_SCOPE_MENU_LABEL_KEY_V1:
                continue

            updated_menu_config[scope_key] = scope_value

        return updated_menu_config

    normalized_scopes = normalize_menu_entity_scopes_v1(updated_menu_config)
    current_scope_values = dict(
        normalized_scopes.get(str(parsed_selected_entity_id), {})
    )

    for scope_key, scope_value in clean_updates.items():
        current_scope_values[scope_key] = scope_value

    normalized_scopes[str(parsed_selected_entity_id)] = current_scope_values
    updated_menu_config[MENU_CONFIG_ENTITY_SCOPES_KEY_V1] = normalized_scopes

    return updated_menu_config
