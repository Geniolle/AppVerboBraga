from __future__ import annotations

import json
import re
import unicodedata
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from appgenesis.admin_subprocesses.registry import get_admin_subprocess_config
from appgenesis.dynamic_process_layout import (
    resolve_dynamic_process_layout_config,
)
from appgenesis.services.process_settings.normalizers import (
    ADDITIONAL_FIELD_DEFAULT_SIZE,
    ADDITIONAL_FIELD_DEFAULT_TYPE,
    ADDITIONAL_FIELD_MAX_SIZE,
    ADDITIONAL_FIELD_TEXTUAL_TYPES,
    ADDITIONAL_FIELD_TYPE_KEYS,
    ADDITIONAL_FIELD_TYPES,
    MENU_CONFIG_DISPLAY_ORDER_KEY,
    MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY,
    MENU_CONFIG_SIDEBAR_SECTION_KEY,
    MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
    MENU_LEGACY_KEY_ALIAS,
    MENU_MEU_PERFIL_FIELD_KEYS,
    MENU_MEU_PERFIL_FIELD_LABELS,
    MENU_MEU_PERFIL_FIELD_OPTIONS,
    MENU_MEU_PERFIL_FIELDS_DEFAULT,
    MENU_MEU_PERFIL_KEY,
    MENU_MEU_PERFIL_LEGACY_KEY,
    MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS,
    MENU_PROCESS_DEFAULT_VISIBLE_FIELDS_BY_KEY,
    MENU_PROCESS_FIELD_OPTIONS_BY_KEY,
    MENU_SECTION_BY_SYSTEM_MENU_KEY,
    MENU_SECTION_DEFAULT_KEY,
    MENU_SECTION_LABELS,
    MENU_SECTION_OPTIONS,
    MENU_VISIBILITY_SCOPE_ALL,
    MENU_VISIBILITY_SCOPES,
    SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS,
    SIDEBAR_MENU_DEFAULTS,
    SIDEBAR_MENU_DELETE_PROTECTED_KEYS,
    SIDEBAR_MENU_KEYS,
    SIDEBAR_MENU_PROTECTED_KEYS,
    SIDEBAR_SECTION_DEFAULTS,
    SIDEBAR_SECTION_DEFAULTS_BY_KEY,
    SIDEBAR_SECTION_DELETE_PROTECTED_KEYS,
    _build_admin_subprocess_sidebar_metadata,
    _build_custom_field_key_from_label,
    _build_group_scoped_custom_field_key,
    _build_menu_key_from_label,
    _build_sidebar_section_key_from_label,
    _build_sidebar_section_payload,
    _fix_common_mojibake,
    _get_additional_field_group_key,
    _is_sidebar_section_delete_protected,
    _load_menu_config,
    _menu_exists,
    _normalize_additional_field_type,
    _normalize_custom_field_key,
    _normalize_menu_display_order,
    _normalize_menu_key,
    _normalize_menu_label_preserve_case,
    _normalize_menu_visibility_scope_value,
    _normalize_sentence_case_text,
    _normalize_sidebar_section_key,
    _normalize_sidebar_section_label,
    _normalize_sidebar_section_status_v5,
    _normalize_sidebar_section_visibility_scopes,
    _normalize_visibility_scope_mode,
    _parse_menu_config,
    _resolve_default_sidebar_section_key,
    _resolve_legacy_menu_alias,
    _resolve_sidebar_menu_settings_entity_id,
    _resolve_visibility_scope_label_from_mode,
    _resolve_visibility_scope_mode_from_scopes,
    _sidebar_menu_defaults_by_key,
    _sidebar_section_status_label_v5,
    _visibility_scope_mode_to_scopes,
    ensure_sidebar_menu_settings_defaults,
    get_menu_section_label,
    get_menu_visibility_scope_label,
    get_menu_visibility_scope_mode,
    get_menu_visibility_scopes,
    get_sidebar_section_visibility_scope_label,
    get_sidebar_section_visibility_scope_mode,
    get_sidebar_section_visibility_scopes,
    normalize_menu_section_key,
    normalize_menu_visibility_scopes,
    normalize_sidebar_sections,
    resolve_menu_key_alias,
    resolve_menu_sidebar_section_key,
)
from appgenesis.services.process_settings.additional_field_service import (
    PT_PT_LABEL_REPLACEMENTS,
    _get_additional_field_group_key_v1,
    _normalize_additional_field_label,
    _normalize_additional_field_list_source_type_v1,
    _normalize_additional_field_required,
    _normalize_additional_field_size,
    _normalize_additional_field_source_key_v1,
    _normalize_process_list_key_v8,
    _rebuild_menu_process_hierarchy_from_additional_fields_v1,
    get_menu_process_additional_fields,
    move_sidebar_menu_additional_field,
    normalize_menu_process_additional_fields,
    normalize_menu_process_additional_fields_v1,
    update_sidebar_menu_additional_fields_v1,
    update_sidebar_menu_additional_fields_v4,
)
from appgenesis.services.process_settings.quantity_field_service import (
    _build_process_quantity_rule_key_v1,
    _normalize_process_quantity_max_items_v1,
    normalize_menu_process_quantity_fields,
    update_sidebar_menu_process_quantity_fields_v1,
)
from appgenesis.services.process_settings.subsequent_field_service import (
    _build_subsequent_field_key_v3,
    _normalize_subsequent_field_operator_v3,
    normalize_menu_process_subsequent_fields,
    update_sidebar_menu_subsequent_fields,
)
from appgenesis.services.process_settings.list_service import (
    _build_process_list_key_from_label_v1,
    _build_process_list_key_from_label_v2,
    _normalize_process_list_items_csv_v1,
    _normalize_process_list_items_csv_v2,
    _normalize_process_list_key_v1,
    _normalize_process_list_key_v2,
    _normalize_process_list_key_v3,
    get_menu_process_lists_v1,
    get_menu_process_lists_v2,
    get_process_list_source_menus_v1,
    normalize_menu_process_lists_v1,
    normalize_menu_process_lists_v2,
    normalize_menu_process_lists_v3,
    normalize_menu_process_lists_v4,
)
from appgenesis.services.process_settings.field_service import (
    get_menu_process_default_visible_fields,
    get_menu_process_default_visible_fields_v4,
    get_menu_process_field_options,
    get_menu_process_field_types_map,
    get_menu_process_header_options,
    get_menu_process_selectable_field_options,
    get_menu_process_visible_field_header_map,
    get_menu_process_visible_field_rows,
    normalize_menu_process_visible_fields,
    normalize_menu_process_visible_fields_v4,
    normalize_meu_perfil_visible_fields,
    update_sidebar_menu_process_fields,
    update_sidebar_menu_process_fields_v4,
)


def _is_menu_delete_protected(menu_key: Any, menu_label: Any = "") -> bool:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    if clean_menu_key in SIDEBAR_MENU_DELETE_PROTECTED_KEYS:
        return True
    clean_menu_label = _normalize_sentence_case_text(menu_label)
    if clean_menu_label in {"Configuração", "Configuracao"}:
        return True
    return False


def _normalize_system_menu_label(menu_key: Any, menu_label: Any) -> str:
    clean_menu_label = _normalize_menu_label_preserve_case(menu_label)
    return clean_menu_label


def get_sidebar_menu_settings(session: Session) -> list[dict[str, Any]]:
    ensure_sidebar_menu_settings_defaults(session)
    defaults_by_key = _sidebar_menu_defaults_by_key()
    rows = session.execute(
        text(
            """
            SELECT menu_key, menu_label, is_active, is_deleted, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).all()
    db_by_key = {
        _normalize_menu_key(row.menu_key): row
        for row in rows
        if _normalize_menu_key(row.menu_key)
    }

    settings: list[dict[str, Any]] = []
    for default_index, item in enumerate(SIDEBAR_MENU_DEFAULTS):
        menu_key = str(item["key"])
        row = db_by_key.get(menu_key)
        if row is None:
            menu_label = _normalize_system_menu_label(menu_key, item["label"])
            is_active = True
            is_deleted = False
        else:
            menu_label = _normalize_system_menu_label(
                menu_key,
                row.menu_label or item["label"],
            ) or _normalize_system_menu_label(menu_key, item["label"])
            is_active = bool(row.is_active)
            is_deleted = bool(row.is_deleted)

        menu_config = _parse_menu_config(None if row is None else row.menu_config)
        process_additional_fields = get_menu_process_additional_fields(menu_config)
        process_subsequent_fields = menu_config.get("subsequent_fields", [])
        explicit_display_order = _normalize_menu_display_order(
            menu_config.get(MENU_CONFIG_DISPLAY_ORDER_KEY)
        )
        effective_display_order = (
            explicit_display_order
            if explicit_display_order is not None
            else default_index
        )
        process_visible_fields = normalize_menu_process_visible_fields(
            menu_key,
            menu_config.get("visible_fields"),
            menu_config,
        )
        process_field_options = get_menu_process_field_options(menu_key, menu_config)
        process_selectable_field_options = get_menu_process_selectable_field_options(
            menu_key, menu_config
        )
        process_header_options = get_menu_process_header_options(menu_key, menu_config)
        process_visible_field_header_map = get_menu_process_visible_field_header_map(
            menu_key, menu_config
        )
        process_visible_field_rows = get_menu_process_visible_field_rows(
            menu_key, menu_config
        )
        process_layout_config = resolve_dynamic_process_layout_config(
            menu_key,
            menu_label,
            menu_config,
            visible_field_rows=process_visible_field_rows,
            field_options=process_field_options,
        )

        settings.append(
            {
                "key": menu_key,
                "label": menu_label,
                "default_label": _normalize_system_menu_label(
                    menu_key,
                    defaults_by_key[menu_key]["label"],
                ),
                "requires_admin": bool(item["requires_admin"]),
                "is_active": bool(is_active),
                "is_deleted": bool(is_deleted),
                "can_delete": not _is_menu_delete_protected(menu_key, menu_label),
                "menu_config": menu_config,
                "visibility_scopes": get_menu_visibility_scopes(menu_config),
                "visibility_scope_mode": get_menu_visibility_scope_mode(menu_config),
                "visibility_scope_label": get_menu_visibility_scope_label(menu_config),
                "process_additional_fields": process_additional_fields,
                "process_subsequent_fields": process_subsequent_fields,
                "process_visible_fields": process_visible_fields,
                "process_visible_field_header_map": process_visible_field_header_map,
                "process_visible_field_rows": process_visible_field_rows,
                "process_field_options": process_field_options,
                "process_selectable_field_options": process_selectable_field_options,
                "process_header_options": process_header_options,
                "process_layout": process_layout_config["layout"],
                "is_list_process": process_layout_config["is_list_process"],
                "uses_record_history": process_layout_config["uses_record_history"],
                "process_record_singular_label": process_layout_config[
                    "singular_label"
                ],
                "process_record_plural_label": process_layout_config["plural_label"],
                "process_record_create_title": process_layout_config["create_title"],
                "process_record_edit_title": process_layout_config["edit_title"],
                "process_record_active_title": process_layout_config["active_title"],
                "process_record_inactive_title": process_layout_config[
                    "inactive_title"
                ],
                "process_record_empty_active_message": process_layout_config[
                    "empty_active_message"
                ],
                "process_record_empty_inactive_message": process_layout_config[
                    "empty_inactive_message"
                ],
                "process_record_state_enabled": process_layout_config["state_enabled"],
                "process_record_status_field_key": process_layout_config[
                    "status_field_key"
                ],
                "process_record_show_system_column": process_layout_config[
                    "show_system_column"
                ],
                "process_record_include_remaining_fields": process_layout_config[
                    "include_remaining_fields"
                ],
                "process_list_columns": process_layout_config["list_columns"],
                "additional_field_type_options": [
                    dict(item) for item in ADDITIONAL_FIELD_TYPES
                ],
                **_build_admin_subprocess_sidebar_metadata(menu_key),
                "_fallback_order": default_index,
                "_has_explicit_order": explicit_display_order is not None,
                "_effective_order": effective_display_order,
            }
        )

    extra_db_keys = sorted(
        key for key in db_by_key.keys() if key not in defaults_by_key
    )
    for extra_index, menu_key in enumerate(extra_db_keys):
        row = db_by_key.get(menu_key)
        if row is None:
            continue

        menu_label = (
            _normalize_system_menu_label(menu_key, row.menu_label or menu_key)
            or menu_key
        )
        is_active = bool(row.is_active)
        is_deleted = bool(row.is_deleted)
        menu_config = _parse_menu_config(row.menu_config)
        requires_admin = bool(menu_config.get("requires_admin", True))
        process_additional_fields = get_menu_process_additional_fields(menu_config)
        fallback_order = len(SIDEBAR_MENU_DEFAULTS) + extra_index
        explicit_display_order = _normalize_menu_display_order(
            menu_config.get(MENU_CONFIG_DISPLAY_ORDER_KEY)
        )
        effective_display_order = (
            explicit_display_order
            if explicit_display_order is not None
            else fallback_order
        )
        process_visible_fields = normalize_menu_process_visible_fields(
            menu_key,
            menu_config.get("visible_fields"),
            menu_config,
        )
        process_field_options = get_menu_process_field_options(menu_key, menu_config)
        process_selectable_field_options = get_menu_process_selectable_field_options(
            menu_key, menu_config
        )
        process_header_options = get_menu_process_header_options(menu_key, menu_config)
        process_visible_field_header_map = get_menu_process_visible_field_header_map(
            menu_key, menu_config
        )
        process_visible_field_rows = get_menu_process_visible_field_rows(
            menu_key, menu_config
        )
        process_layout_config = resolve_dynamic_process_layout_config(
            menu_key,
            menu_label,
            menu_config,
            visible_field_rows=process_visible_field_rows,
            field_options=process_field_options,
        )

        settings.append(
            {
                "key": menu_key,
                "label": menu_label,
                "default_label": menu_label,
                "requires_admin": requires_admin,
                "is_active": is_active,
                "is_deleted": is_deleted,
                "can_delete": not _is_menu_delete_protected(menu_key, menu_label),
                "menu_config": menu_config,
                "visibility_scopes": get_menu_visibility_scopes(menu_config),
                "visibility_scope_mode": get_menu_visibility_scope_mode(menu_config),
                "visibility_scope_label": get_menu_visibility_scope_label(menu_config),
                "process_additional_fields": process_additional_fields,
                "process_visible_fields": process_visible_fields,
                "process_visible_field_header_map": process_visible_field_header_map,
                "process_visible_field_rows": process_visible_field_rows,
                "process_field_options": process_field_options,
                "process_selectable_field_options": process_selectable_field_options,
                "process_header_options": process_header_options,
                "process_layout": process_layout_config["layout"],
                "is_list_process": process_layout_config["is_list_process"],
                "uses_record_history": process_layout_config["uses_record_history"],
                "process_record_singular_label": process_layout_config[
                    "singular_label"
                ],
                "process_record_plural_label": process_layout_config["plural_label"],
                "process_record_create_title": process_layout_config["create_title"],
                "process_record_edit_title": process_layout_config["edit_title"],
                "process_record_active_title": process_layout_config["active_title"],
                "process_record_inactive_title": process_layout_config[
                    "inactive_title"
                ],
                "process_record_empty_active_message": process_layout_config[
                    "empty_active_message"
                ],
                "process_record_empty_inactive_message": process_layout_config[
                    "empty_inactive_message"
                ],
                "process_record_state_enabled": process_layout_config["state_enabled"],
                "process_record_status_field_key": process_layout_config[
                    "status_field_key"
                ],
                "process_record_show_system_column": process_layout_config[
                    "show_system_column"
                ],
                "process_record_include_remaining_fields": process_layout_config[
                    "include_remaining_fields"
                ],
                "process_list_columns": process_layout_config["list_columns"],
                "additional_field_type_options": [
                    dict(item) for item in ADDITIONAL_FIELD_TYPES
                ],
                **_build_admin_subprocess_sidebar_metadata(menu_key),
                "_fallback_order": fallback_order,
                "_has_explicit_order": explicit_display_order is not None,
                "_effective_order": effective_display_order,
            }
        )

    settings.sort(
        key=lambda item: (
            int(item.get("_effective_order", 0)),
            0 if bool(item.get("_has_explicit_order")) else 1,
            int(item.get("_fallback_order", 0)),
            str(item.get("label") or "").lower(),
        )
    )
    active_menu_keys = [
        str(item.get("key") or "").strip().lower()
        for item in settings
        if item.get("is_active") and not item.get("is_deleted")
    ]
    active_positions = {
        menu_key: index for index, menu_key in enumerate(active_menu_keys)
    }
    for order_index, setting_row in enumerate(settings):
        setting_row["order_index"] = order_index
        clean_menu_key = str(setting_row.get("key") or "").strip().lower()
        if (
            setting_row.get("is_active")
            and not setting_row.get("is_deleted")
            and clean_menu_key in active_positions
        ):
            active_index = active_positions[clean_menu_key]
            setting_row["can_move_up"] = active_index > 0
            setting_row["can_move_down"] = active_index < (len(active_menu_keys) - 1)
        else:
            setting_row["can_move_up"] = False
            setting_row["can_move_down"] = False
        setting_row["display_order"] = int(
            setting_row.get("_effective_order", order_index)
        )
        setting_row.pop("_fallback_order", None)
        setting_row.pop("_has_explicit_order", None)
        setting_row.pop("_effective_order", None)

    administrativo_row = next(
        (
            row
            for row in settings
            if str(row.get("key") or "").strip().lower() == "administrativo"
        ),
        None,
    )
    sidebar_section_options = normalize_sidebar_sections(
        (administrativo_row or {})
        .get("menu_config", {})
        .get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )
    sidebar_section_keys = [
        str(item.get("key") or "").strip().lower()
        for item in sidebar_section_options
        if str(item.get("key") or "").strip()
    ]
    sidebar_section_keys_set = set(sidebar_section_keys)
    sidebar_section_labels_by_key = {
        str(item.get("key") or "").strip().lower(): str(item.get("label") or "").strip()
        for item in sidebar_section_options
        if str(item.get("key") or "").strip()
    }
    for setting_row in settings:
        clean_menu_key = str(setting_row.get("key") or "").strip().lower()
        menu_config = setting_row.get("menu_config")
        configured_section_key = resolve_menu_sidebar_section_key(
            clean_menu_key,
            menu_config,
            sidebar_section_keys_set,
            sidebar_section_keys,
        )
        setting_row["sidebar_section_key"] = configured_section_key
        setting_row["sidebar_section_label"] = (
            sidebar_section_labels_by_key.get(configured_section_key)
            or SIDEBAR_SECTION_DEFAULTS_BY_KEY.get(configured_section_key)
            or configured_section_key
        )
        setting_row["menu_section"] = configured_section_key
        setting_row["menu_section_label"] = setting_row["sidebar_section_label"]

    return settings


def _persist_sidebar_menu_display_order(
    session: Session,
    ordered_menu_keys: list[str],
) -> None:
    changed = False
    for order_index, raw_menu_key in enumerate(ordered_menu_keys):
        clean_menu_key = _normalize_menu_key(raw_menu_key)
        if not clean_menu_key:
            continue
        menu_config = _load_menu_config(session, clean_menu_key)
        current_order = _normalize_menu_display_order(
            menu_config.get(MENU_CONFIG_DISPLAY_ORDER_KEY)
        )
        if current_order == order_index:
            continue
        menu_config[MENU_CONFIG_DISPLAY_ORDER_KEY] = order_index
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": clean_menu_key,
                "menu_config": json.dumps(menu_config, ensure_ascii=False),
            },
        )
        changed = True
    if changed:
        session.commit()


def move_sidebar_menu_setting(
    session: Session,
    menu_key: str,
    direction: str,
) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    clean_direction = str(direction or "").strip().lower()
    if clean_direction not in {"up", "down"}:
        return False, "Direção inválida."

    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."

    settings = get_sidebar_menu_settings(session)
    ordered_menu_keys = [
        str(item.get("key") or "").strip().lower()
        for item in settings
        if str(item.get("key") or "").strip()
    ]
    active_ordered_menu_keys = [
        key
        for key, item in zip(ordered_menu_keys, settings)
        if item.get("is_active") and not item.get("is_deleted")
    ]
    if clean_menu_key not in active_ordered_menu_keys:
        return False, "Menu inválido."

    current_index = active_ordered_menu_keys.index(clean_menu_key)
    if clean_direction == "up":
        if current_index <= 0:
            return False, "Esta pasta já está no topo."
        target_menu_key = active_ordered_menu_keys[current_index - 1]
    else:
        if current_index >= (len(active_ordered_menu_keys) - 1):
            return False, "Esta pasta já está no fim."
        target_menu_key = active_ordered_menu_keys[current_index + 1]

    current_index_full = ordered_menu_keys.index(clean_menu_key)
    target_index_full = ordered_menu_keys.index(target_menu_key)
    ordered_menu_keys[current_index_full], ordered_menu_keys[target_index_full] = (
        ordered_menu_keys[target_index_full],
        ordered_menu_keys[current_index_full],
    )
    _persist_sidebar_menu_display_order(session, ordered_menu_keys)
    return True, ""


def get_visible_sidebar_menu_keys(
    settings: list[dict[str, Any]],
    current_user_is_admin: bool,
    current_entity_scope: str | None = None,
) -> set[str]:
    clean_entity_scope = _normalize_menu_visibility_scope_value(current_entity_scope)
    visible_keys: set[str] = set()
    for item in settings:
        if item.get("requires_admin") and not current_user_is_admin:
            continue
        if not item.get("is_active") or item.get("is_deleted"):
            continue
        visibility_scopes = normalize_menu_visibility_scopes(
            item.get("visibility_scopes")
        )
        if clean_entity_scope and clean_entity_scope not in visibility_scopes:
            continue
        visible_keys.add(str(item["key"]))
    if "home" not in visible_keys:
        visible_keys.add("home")
    return visible_keys


def set_sidebar_menu_visibility(
    session: Session, menu_key: str, make_visible: bool
) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."
    if clean_menu_key in SIDEBAR_MENU_PROTECTED_KEYS and not make_visible:
        return False, "Não é permitido ocultar este menu."

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET is_active = :is_active,
                is_deleted = :is_deleted
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": clean_menu_key,
            "is_active": bool(make_visible),
            "is_deleted": False,
        },
    )
    session.commit()
    return True, ""


def update_sidebar_menu_label(
    session: Session,
    menu_key: str,
    menu_label: str,
    visibility_scope_mode: str | None = None,
    sidebar_section_key: str | None = None,
    entity_number: int | None = None,
) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    clean_menu_label = _normalize_menu_label_preserve_case(menu_label)
    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."
    if not clean_menu_label:
        return False, "Nome do menu é obrigatório."

    menu_config = _load_menu_config(session, clean_menu_key)
    clean_scope_mode = str(visibility_scope_mode or "").strip().lower()
    if clean_scope_mode:
        if clean_scope_mode == MENU_VISIBILITY_SCOPE_ALL:
            normalized_visibility_scopes = list(MENU_VISIBILITY_SCOPES)
        elif clean_scope_mode in MENU_VISIBILITY_SCOPES:
            normalized_visibility_scopes = [clean_scope_mode]
        else:
            return False, "Escopo de exibição inválido."
        menu_config["visibility_scopes"] = normalized_visibility_scopes
    else:
        menu_config["visibility_scopes"] = get_menu_visibility_scopes(menu_config)

    administrative_config = _load_menu_config(session, "administrativo")
    section_options = normalize_sidebar_sections(
        administrative_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )
    section_keys = [
        str(item.get("key") or "").strip().lower()
        for item in section_options
        if str(item.get("key") or "").strip()
    ]
    section_keys_set = set(section_keys)
    requested_section_key = _normalize_sidebar_section_key(sidebar_section_key)
    if requested_section_key:
        if requested_section_key not in section_keys_set:
            return False, "Sessão inválida."
        menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = requested_section_key
    elif section_keys:
        current_section_key = _normalize_sidebar_section_key(
            menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY)
        )
        if current_section_key not in section_keys_set:
            menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = (
                _resolve_default_sidebar_section_key(
                    clean_menu_key,
                    section_keys_set,
                    section_keys,
                )
            )
        else:
            menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = current_section_key

    menu_config.pop("menu_section", None)

    if entity_number is not None:
        menu_config["entity_number"] = int(entity_number)

    if clean_menu_key == "administrativo":
        menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = (
            build_sidebar_global_refresh_version_v1()
        )

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_label = :menu_label,
                menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_label": clean_menu_label,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )

    if clean_menu_key != "administrativo":
        administrative_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = (
            build_sidebar_global_refresh_version_v1()
        )
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": "administrativo",
                "menu_config": json.dumps(administrative_config, ensure_ascii=False),
            },
        )

    session.commit()
    return True, ""


def update_sidebar_menu_sidebar_sections(
    session: Session,
    sidebar_sections: list[Any] | tuple[Any, ...] | set[Any] | str,
    menu_section_map: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    ensure_sidebar_menu_settings_defaults(session)
    normalized_sidebar_sections = normalize_sidebar_sections(sidebar_sections)
    section_keys = [
        str(item.get("key") or "").strip().lower()
        for item in normalized_sidebar_sections
        if str(item.get("key") or "").strip()
    ]
    section_keys_set = set(section_keys)
    if not section_keys:
        return False, "Defina ao menos uma sessão do sidebar."

    normalized_section_map: dict[str, str] = {}
    if isinstance(menu_section_map, dict):
        for raw_menu_key, raw_section_key in menu_section_map.items():
            clean_menu_key = _normalize_menu_key(raw_menu_key)
            clean_section_key = _normalize_sidebar_section_key(raw_section_key)
            if not clean_menu_key:
                continue
            normalized_section_map[clean_menu_key] = clean_section_key

    settings = get_sidebar_menu_settings(session)
    changed = False

    administrativo_config = _load_menu_config(session, "administrativo")
    if (
        administrativo_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
        != normalized_sidebar_sections
    ):
        administrativo_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = (
            normalized_sidebar_sections
        )
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = 'administrativo'
                """
            ),
            {"menu_config": json.dumps(administrativo_config, ensure_ascii=False)},
        )
        changed = True

    # When no explicit menu->section mapping is sent, this operation manages only
    # the session definitions and must not reassign menus.
    should_update_menu_mapping = bool(normalized_section_map)

    if should_update_menu_mapping:
        for setting_row in settings:
            clean_menu_key = _normalize_menu_key(setting_row.get("key"))
            if not clean_menu_key:
                continue
            desired_section_key = _normalize_sidebar_section_key(
                normalized_section_map.get(clean_menu_key)
            )
            if desired_section_key not in section_keys_set:
                desired_section_key = _resolve_default_sidebar_section_key(
                    clean_menu_key,
                    section_keys_set,
                    section_keys,
                )
            if not desired_section_key:
                continue

            menu_config = _load_menu_config(session, clean_menu_key)
            current_section_key = _normalize_sidebar_section_key(
                menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY)
            )
            if current_section_key == desired_section_key:
                continue

            menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = desired_section_key
            session.execute(
                text(
                    """
                    UPDATE sidebar_menu_settings
                    SET menu_config = :menu_config
                    WHERE lower(trim(menu_key)) = :menu_key
                    """
                ),
                {
                    "menu_key": clean_menu_key,
                    "menu_config": json.dumps(menu_config, ensure_ascii=False),
                },
            )
            changed = True

    if changed:
        session.commit()
    return True, ""


def update_sidebar_menu_process_lists(
    session: Session,
    menu_key: str,
    raw_lists: Any,
    raw_columns: Any = None,
    active_entity_id: int | None = None,
) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if not clean_menu_key:
        return False, "Menu inválido."

    resolved_entity_id = active_entity_id
    if resolved_entity_id is None:
        resolved_entity_id = _resolve_sidebar_menu_settings_entity_id(session)

    if resolved_entity_id is None:
        return False, "Entidade ativa inválida."

    target_row = (
        session.execute(
            text(
                """
                SELECT menu_config
                FROM sidebar_menu_settings
                WHERE entity_id = :entity_id
                  AND lower(trim(menu_key)) = :menu_key
                  AND COALESCE(is_deleted, false) = false
                LIMIT 1
                """
            ),
            {
                "entity_id": int(resolved_entity_id),
                "menu_key": clean_menu_key,
            },
        )
        .mappings()
        .one_or_none()
    )

    if target_row is None:
        return False, "Menu não encontrado."

    menu_config = _parse_menu_config(target_row.get("menu_config"))
    existing_lists = normalize_menu_process_lists_v4(menu_config.get("process_lists"))
    legacy_automatic_keys = {
        str(item.get("key") or "")
        for item in existing_lists
        if item.get("field_type") == "automatic" and not item.get("source_menu_key")
    }
    available_source_menu_keys = {
        item["menu_key"]
        for item in get_process_list_source_menus_v1(session, int(resolved_entity_id))
    }
    normalized_lists = normalize_menu_process_lists_v4(raw_lists)

    for process_list in normalized_lists:
        if process_list.get("field_type") != "automatic":
            continue

        source_menu_key = str(process_list.get("source_menu_key") or "").strip()
        process_list_key = str(process_list.get("key") or "").strip()

        if not source_menu_key and process_list_key in legacy_automatic_keys:
            continue
        if not source_menu_key:
            return False, "Selecione o menu de origem da lista automática."
        if source_menu_key not in available_source_menu_keys:
            return False, "O menu de origem selecionado não está disponível."

    menu_config["process_lists"] = normalized_lists

    if raw_columns is not None:
        selectable_options = get_menu_process_selectable_field_options(
            clean_menu_key, menu_config
        )
        selectable_labels = {
            str(item.get("key") or "").strip().lower(): str(
                item.get("label") or ""
            ).strip()
            for item in selectable_options
            if isinstance(item, dict)
        }
        normalized_columns: list[dict[str, Any]] = []
        seen_field_keys: set[str] = set()

        for raw_column in raw_columns if isinstance(raw_columns, list) else []:
            if not isinstance(raw_column, dict):
                continue
            field_key = str(raw_column.get("field_key") or "").strip().lower()
            if field_key not in selectable_labels or field_key in seen_field_keys:
                continue
            seen_field_keys.add(field_key)
            try:
                responsive_priority = max(
                    0,
                    min(99, int(raw_column.get("responsive_priority") or 0)),
                )
            except (TypeError, ValueError):
                responsive_priority = 0
            normalized_columns.append(
                {
                    "key": str(raw_column.get("key") or field_key).strip().lower(),
                    "label": str(
                        raw_column.get("label") or selectable_labels[field_key]
                    ).strip(),
                    "source_kind": "field",
                    "field_key": field_key,
                    "always_visible": str(raw_column.get("always_visible") or "")
                    .strip()
                    .lower()
                    in {"1", "true", "yes", "on"},
                    "responsive_priority": responsive_priority,
                }
            )

        menu_config["process_list_columns"] = normalized_columns
        process_list_config = menu_config.get("process_list_config")
        if isinstance(process_list_config, dict):
            process_list_config = dict(process_list_config)
            process_list_config["columns"] = normalized_columns
            menu_config["process_list_config"] = process_list_config

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
              AND entity_id = :entity_id
              AND COALESCE(is_deleted, false) = false
            """
        ),
        {
            "menu_key": clean_menu_key,
            "entity_id": int(resolved_entity_id),
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    session.commit()
    return True, ""


def delete_sidebar_menu_setting(session: Session, menu_key: str) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."

    existing_label = session.execute(
        text(
            """
            SELECT menu_label
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": clean_menu_key},
    ).scalar_one_or_none()

    if _is_menu_delete_protected(clean_menu_key, existing_label):
        return False, "Não é permitido excluir este menu."

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET is_active = FALSE,
                is_deleted = TRUE
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {"menu_key": clean_menu_key},
    )
    session.commit()
    return True, ""


def delete_sidebar_section(session: Session, section_key: str) -> tuple[bool, str]:
    clean_section_key = _normalize_sidebar_section_key(section_key)

    if not clean_section_key:
        return False, "Sessão inválida."

    administrativo_row = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": "administrativo"},
    ).scalar_one_or_none()

    if administrativo_row is None:
        return False, "Sessão inválida."

    current_menu_config = _parse_sidebar_menu_config_v2(administrativo_row)
    current_sections = normalize_sidebar_sections(
        current_menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )

    target_section = next(
        (
            dict(section)
            for section in current_sections
            if _normalize_sidebar_section_key(section.get("key")) == clean_section_key
        ),
        None,
    )

    if target_section is None:
        return False, "Sessão inválida."

    if _is_sidebar_section_delete_protected(clean_section_key):
        return False, "Não é permitido eliminar esta sessão."

    if _normalize_sidebar_section_status_v5(target_section.get("status")) != "inativo":
        return False, "A sessão deve estar inativa antes de ser eliminada."

    remaining_sections = [
        {
            "key": section.get("key"),
            "label": section.get("label"),
            "visibility_scope_mode": section.get("visibility_scope_mode"),
            "status": section.get("status"),
        }
        for section in current_sections
        if _normalize_sidebar_section_key(section.get("key")) != clean_section_key
    ]

    return update_sidebar_sections_v2(session, remaining_sections)


####################################################################################
# HOTFIX V2 - CRIACAO DE PASTA COM REATIVACAO DE REGISTO ELIMINADO
####################################################################################


def create_sidebar_menu_setting(
    session: Session,
    entity_id: int,
    menu_label: str,
    visibility_scope_mode: str = "all",
) -> tuple[bool, str, str]:
    ####################################################################################
    # (1) NORMALIZAR NOME E CHAVE DA PASTA
    ####################################################################################

    clean_menu_label = _normalize_menu_label_preserve_case(menu_label)
    if not clean_menu_label:
        return False, "Informe o nome da pasta.", ""

    clean_menu_key = _resolve_legacy_menu_alias(
        _build_menu_key_from_label(clean_menu_label)
    )
    if not clean_menu_key:
        return False, "Informe um nome valido para a pasta.", ""

    ####################################################################################
    # (2) CALCULAR PROXIMA ORDEM DE EXIBICAO
    ####################################################################################

    def _next_display_order_v2() -> int:
        rows = session.execute(
            text(
                """
                SELECT menu_config
                FROM sidebar_menu_settings
                """
            )
        ).all()

        max_display_order = -1
        for row in rows:
            menu_config = _parse_menu_config(row.menu_config)
            display_order = _normalize_menu_display_order(
                menu_config.get(MENU_CONFIG_DISPLAY_ORDER_KEY)
            )
            if display_order is not None:
                max_display_order = max(max_display_order, display_order)

        return max_display_order + 1

    administrative_config = _load_menu_config(session, "administrativo")
    available_sidebar_section_options = normalize_sidebar_sections(
        administrative_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )
    available_sidebar_section_keys = [
        str(item.get("key") or "").strip().lower()
        for item in available_sidebar_section_options
        if str(item.get("key") or "").strip()
    ]
    if not available_sidebar_section_keys:
        available_sidebar_section_keys = list(MENU_SECTION_LABELS.keys())
    available_sidebar_section_keys_set = set(available_sidebar_section_keys)

    ####################################################################################
    # (3) MONTAR OU ATUALIZAR CONFIGURACAO DA PASTA
    ####################################################################################

    def _build_menu_config_v2(
        existing_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        menu_config = dict(existing_config or {})

        menu_config["requires_admin"] = True
        menu_config["visibility_scopes"] = normalize_menu_visibility_scopes(
            visibility_scope_mode
        )

        if not isinstance(menu_config.get("additional_fields"), list):
            menu_config["additional_fields"] = []

        if not isinstance(menu_config.get("visible_fields"), list):
            menu_config["visible_fields"] = []

        if not isinstance(menu_config.get("visible_field_headers"), dict):
            menu_config["visible_field_headers"] = {}

        display_order = _normalize_menu_display_order(
            menu_config.get(MENU_CONFIG_DISPLAY_ORDER_KEY)
        )
        if display_order is None:
            menu_config[MENU_CONFIG_DISPLAY_ORDER_KEY] = _next_display_order_v2()

        menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = resolve_menu_sidebar_section_key(
            clean_menu_key,
            menu_config,
            available_sidebar_section_keys_set,
            available_sidebar_section_keys,
        )
        menu_config.pop("menu_section", None)

        return menu_config

    ####################################################################################
    # (4) PROCURAR REGISTO EXISTENTE, INCLUINDO ELIMINADOS
    ####################################################################################

    existing_row = (
        session.execute(
            text(
                """
            SELECT menu_key, menu_label, is_active, is_deleted, menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
               OR lower(trim(menu_label)) = :menu_label
            ORDER BY
                CASE WHEN lower(trim(menu_key)) = :menu_key THEN 0 ELSE 1 END,
                CASE WHEN COALESCE(is_deleted, false) THEN 1 ELSE 0 END
            LIMIT 1
            """
            ),
            {
                "menu_key": clean_menu_key,
                "menu_label": clean_menu_label.strip().lower(),
            },
        )
        .mappings()
        .first()
    )

    ####################################################################################
    # (5) SE EXISTE ATIVO, BLOQUEAR
    ####################################################################################

    if existing_row is not None and not bool(existing_row.get("is_deleted")):
        return (
            False,
            "Ja existe uma pasta com este nome.",
            str(existing_row.get("menu_key") or clean_menu_key),
        )

    ####################################################################################
    # (6) SE EXISTE ELIMINADO, REATIVAR
    ####################################################################################

    if existing_row is not None and bool(existing_row.get("is_deleted")):
        existing_menu_key = (
            str(existing_row.get("menu_key") or clean_menu_key).strip().lower()
        )
        existing_config = _parse_menu_config(existing_row.get("menu_config"))
        menu_config = _build_menu_config_v2(existing_config)

        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_label = :menu_label,
                    is_active = :is_active,
                    is_deleted = :is_deleted,
                    menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": existing_menu_key,
                "menu_label": clean_menu_label,
                "is_active": True,
                "is_deleted": False,
                "menu_config": json.dumps(menu_config, ensure_ascii=False),
            },
        )

        if existing_menu_key != "administrativo":
            administrative_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = (
                build_sidebar_global_refresh_version_v1()
            )
            session.execute(
                text(
                    """
                    UPDATE sidebar_menu_settings
                    SET menu_config = :menu_config
                    WHERE lower(trim(menu_key)) = :menu_key
                    """
                ),
                {
                    "menu_key": "administrativo",
                    "menu_config": json.dumps(administrative_config, ensure_ascii=False),
                },
            )

        session.commit()
        return True, "", existing_menu_key

    ####################################################################################
    # (7) SE NAO EXISTE, CRIAR NOVA PASTA
    ####################################################################################

    menu_config = _build_menu_config_v2({})

    session.execute(
        text(
            """
            INSERT INTO sidebar_menu_settings
                (entity_id, menu_key, menu_label, is_active, is_deleted, menu_config)
            VALUES
                (:entity_id, :menu_key, :menu_label, :is_active, :is_deleted, :menu_config)
            """
        ),
        {
            "entity_id": entity_id,
            "menu_key": clean_menu_key,
            "menu_label": clean_menu_label,
            "is_active": True,
            "is_deleted": False,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )

    if clean_menu_key != "administrativo":
        administrative_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = (
            build_sidebar_global_refresh_version_v1()
        )
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": "administrativo",
                "menu_config": json.dumps(administrative_config, ensure_ascii=False),
            },
        )

    session.commit()

    return True, "", clean_menu_key


if "_original_get_sidebar_menu_settings_for_lists_v1" not in globals():
    _original_get_sidebar_menu_settings_for_lists_v1 = get_sidebar_menu_settings


def get_sidebar_menu_settings_v2(session: Session) -> list[dict[str, Any]]:
    settings = _original_get_sidebar_menu_settings_for_lists_v1(session)

    rows = session.execute(
        text(
            """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).all()

    config_by_key = {
        _normalize_menu_key(row.menu_key): _parse_menu_config(row.menu_config)
        for row in rows
        if _normalize_menu_key(row.menu_key)
    }

    for item in settings:
        clean_key = _normalize_menu_key(item.get("key"))
        menu_config = config_by_key.get(clean_key, {})
        process_lists = get_menu_process_lists_v1(menu_config)
        item["process_lists"] = process_lists
        item["process_list_options"] = [
            {"key": process_list["key"], "label": process_list["label"]}
            for process_list in process_lists
        ]

    return settings


get_sidebar_menu_settings = get_sidebar_menu_settings_v2

if "_original_get_sidebar_menu_settings_for_lists_v2" not in globals():
    _original_get_sidebar_menu_settings_for_lists_v2 = get_sidebar_menu_settings


def get_sidebar_menu_settings_v3(session: Session) -> list[dict[str, Any]]:
    settings = _original_get_sidebar_menu_settings_for_lists_v2(session)

    rows = session.execute(
        text(
            """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).all()

    config_by_key = {
        _normalize_menu_key(row.menu_key): _parse_menu_config(row.menu_config)
        for row in rows
        if _normalize_menu_key(row.menu_key)
    }

    for item in settings:
        clean_key = _normalize_menu_key(item.get("key"))
        menu_config = config_by_key.get(clean_key, {})
        process_lists = get_menu_process_lists_v2(menu_config)
        item["process_lists"] = process_lists
        item["process_list_options"] = [
            {"key": process_list["key"], "label": process_list["label"]}
            for process_list in process_lists
        ]

    return settings


get_sidebar_menu_settings = get_sidebar_menu_settings_v3

if "_original_get_sidebar_menu_settings_for_lists_v3" not in globals():
    _original_get_sidebar_menu_settings_for_lists_v3 = get_sidebar_menu_settings


def get_sidebar_menu_settings_v4(session: Session) -> list[dict[str, Any]]:
    settings = _original_get_sidebar_menu_settings_for_lists_v3(session)

    rows = session.execute(
        text(
            """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).all()

    config_by_key = {
        _normalize_menu_key(row.menu_key): _parse_menu_config(row.menu_config)
        for row in rows
        if _normalize_menu_key(row.menu_key)
    }

    for item in settings:
        clean_key = _normalize_menu_key(item.get("key"))
        menu_config = config_by_key.get(clean_key, {})
        process_lists = normalize_menu_process_lists_v4(
            menu_config.get("process_lists")
        )
        process_subsequent_fields = normalize_menu_process_subsequent_fields(
            menu_config.get("subsequent_fields")
        )
        process_quantity_fields = normalize_menu_process_quantity_fields(
            menu_config.get("process_quantity_fields")
        )
        item["process_lists"] = process_lists
        item["process_subsequent_fields"] = process_subsequent_fields
        item["process_quantity_fields"] = process_quantity_fields
        item["process_list_options"] = [
            {"key": process_list["key"], "label": process_list["label"]}
            for process_list in process_lists
        ]

    return settings


get_sidebar_menu_settings = get_sidebar_menu_settings_v4


# //###################################################################################
# (MENU) HIERARQUIA DOS CAMPOS ADICIONAIS - PATCH SEGURO V2
# //###################################################################################


# ###################################################################################
# (SIDEBAR_GLOBAL_REFRESH_V1) VERSAO GLOBAL PARA REFRESH DOS UTILIZADORES LOGADOS
# ###################################################################################


def build_sidebar_global_refresh_version_v1() -> str:
    from time import time as _appgenesis_time

    return str(int(_appgenesis_time() * 1000))


def get_sidebar_global_refresh_version_v1(session: Session) -> str:
    row = (
        session.execute(
            text(
                """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
            ),
            {"menu_key": "administrativo"},
        )
        .mappings()
        .one_or_none()
    )

    if row is None:
        return ""

    try:
        menu_config = json.loads(row.get("menu_config") or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        menu_config = {}

    if not isinstance(menu_config, dict):
        return ""

    return str(menu_config.get(MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY) or "")


# APPGENESIS_SIDEBAR_SECTIONS_UPDATE_V2_START

# ###################################################################################
# (SIDEBAR_SECTIONS_UPDATE_V2) GRAVAR SESSOES E PROPAGAR VISIBILIDADE AOS MENUS
# ###################################################################################


def _parse_sidebar_menu_config_v2(raw_menu_config: Any) -> dict[str, Any]:
    try:
        parsed_config = json.loads(raw_menu_config or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed_config = {}

    if not isinstance(parsed_config, dict):
        return {}

    return parsed_config


def _resolve_menu_sidebar_section_key_v2(
    menu_key: Any,
    menu_config: dict[str, Any],
    section_keys: set[str],
    ordered_section_keys: list[str],
) -> str:
    return resolve_menu_sidebar_section_key(
        menu_key,
        menu_config,
        section_keys,
        ordered_section_keys,
    )


def update_sidebar_sections_v2(
    session: Session,
    raw_sections: list[dict[str, Any]],
) -> tuple[bool, str]:
    payload_sections: list[dict[str, Any]] = []

    for raw_section in raw_sections:
        if not isinstance(raw_section, dict):
            continue

        clean_label = _normalize_sidebar_section_label(raw_section.get("label"))
        if not clean_label:
            continue

        clean_key = _normalize_sidebar_section_key(raw_section.get("key"))
        if not clean_key:
            clean_key = _build_sidebar_section_key_from_label(clean_label)

        if not clean_key:
            continue

        scope_mode = (
            raw_section.get("visibility_scope_mode")
            or raw_section.get("scope_mode")
            or raw_section.get("scope")
            or raw_section.get("visibility")
            or MENU_VISIBILITY_SCOPE_ALL
        )

        payload_sections.append(
            _build_sidebar_section_payload(
                clean_key,
                clean_label,
                _visibility_scope_mode_to_scopes(scope_mode),
                raw_section.get("status"),
            )
        )

    normalized_sections = normalize_sidebar_sections(payload_sections)

    if not normalized_sections:
        return False, "Informe pelo menos uma sessão válida."

    section_keys = {
        str(section.get("key") or "").strip().lower()
        for section in normalized_sections
        if str(section.get("key") or "").strip()
    }
    ordered_section_keys = [
        str(section.get("key") or "").strip().lower()
        for section in normalized_sections
        if str(section.get("key") or "").strip()
    ]
    section_scope_map = {
        str(section.get("key") or "").strip().lower(): normalize_menu_visibility_scopes(
            section.get("visibility_scopes")
        )
        for section in normalized_sections
        if str(section.get("key") or "").strip()
    }

    menu_rows = (
        session.execute(
            text(
                """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
            )
        )
        .mappings()
        .all()
    )

    if not menu_rows:
        return False, "Não existem menus para atualizar."

    updated_menus_count = 0

    for menu_row in menu_rows:
        clean_menu_key = _normalize_menu_key(menu_row.get("menu_key"))
        if not clean_menu_key:
            continue

        menu_config = _parse_sidebar_menu_config_v2(menu_row.get("menu_config"))
        sidebar_section_key = _resolve_menu_sidebar_section_key_v2(
            clean_menu_key,
            menu_config,
            section_keys,
            ordered_section_keys,
        )

        if sidebar_section_key not in section_scope_map:
            continue

        inherited_scopes = normalize_menu_visibility_scopes(
            section_scope_map.get(sidebar_section_key)
        )
        inherited_scope_mode = _resolve_visibility_scope_mode_from_scopes(
            inherited_scopes
        )

        menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = sidebar_section_key
        menu_config["visibility_scopes"] = inherited_scopes
        menu_config["visibility_scope_mode"] = inherited_scope_mode
        menu_config["visibility_scope_label"] = (
            _resolve_visibility_scope_label_from_mode(inherited_scope_mode)
        )

        if clean_menu_key == "administrativo":
            menu_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = normalized_sections
            menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = (
                build_sidebar_global_refresh_version_v1()
            )

        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": clean_menu_key,
                "menu_config": json.dumps(menu_config, ensure_ascii=False),
            },
        )
        updated_menus_count += 1

    session.commit()

    if updated_menus_count <= 0:
        return False, "Nenhum menu foi atualizado com a visibilidade das sessões."

    return True, ""


# APPGENESIS_SIDEBAR_SECTIONS_UPDATE_V2_END
