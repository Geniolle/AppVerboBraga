from __future__ import annotations

import json
import re
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from appgenesis.services.process_settings.normalizers import (
    MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY,
    MENU_MEU_PERFIL_KEY,
    MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS,
    MENU_PROCESS_DEFAULT_VISIBLE_FIELDS_BY_KEY,
    MENU_PROCESS_FIELD_OPTIONS_BY_KEY,
    _load_menu_config,
    _menu_exists,
    _resolve_legacy_menu_alias,
    ensure_sidebar_menu_settings_defaults,
)
from appgenesis.services.process_settings.additional_field_service import (
    get_menu_process_additional_fields,
)


def get_menu_process_field_options(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    raw_options = MENU_PROCESS_FIELD_OPTIONS_BY_KEY.get(clean_menu_key, tuple())
    additional_options = get_menu_process_additional_fields(menu_config)
    if (
        clean_menu_key not in MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS
        and additional_options
    ):
        return [dict(item) for item in additional_options]
    options = [dict(item) for item in raw_options]
    if additional_options:
        options.extend(additional_options)
    return options


def get_menu_process_field_types_map(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> dict[str, str]:
    types_map: dict[str, str] = {}
    for item in get_menu_process_field_options(menu_key, menu_config):
        clean_key = str(item.get("key") or "").strip().lower()
        if not clean_key:
            continue
        clean_type = str(item.get("field_type") or "").strip().lower()
        types_map[clean_key] = clean_type
    return types_map


def get_menu_process_header_options(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    types_map = get_menu_process_field_types_map(menu_key, menu_config)
    return [
        dict(item)
        for item in get_menu_process_field_options(menu_key, menu_config)
        if str(types_map.get(str(item.get("key") or "").strip().lower()) or "")
        .strip()
        .lower()
        == "header"
    ]


def get_menu_process_selectable_field_options(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    types_map = get_menu_process_field_types_map(menu_key, menu_config)
    return [
        dict(item)
        for item in get_menu_process_field_options(menu_key, menu_config)
        if str(types_map.get(str(item.get("key") or "").strip().lower()) or "")
        .strip()
        .lower()
        != "header"
    ]


def get_menu_process_default_visible_fields_v4(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    # APPGENESIS_PROCESS_CREATE_EDIT_FLOW_V4_DEFAULTS_START
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    clean_menu_config = menu_config if isinstance(menu_config, dict) else {}

    selectable_options = get_menu_process_selectable_field_options(
        clean_menu_key,
        clean_menu_config,
    )

    selectable_keys = [
        str(item.get("key") or "").strip().lower()
        for item in selectable_options
        if str(item.get("key") or "").strip()
    ]

    if not selectable_keys:
        return []

    allowed_keys = set(selectable_keys)
    configured_defaults = MENU_PROCESS_DEFAULT_VISIBLE_FIELDS_BY_KEY.get(
        clean_menu_key,
        [],
    )

    normalized_defaults: list[str] = []
    seen_keys: set[str] = set()

    for raw_key in configured_defaults:
        field_key = str(raw_key or "").strip().lower()

        if not field_key:
            continue

        if field_key in seen_keys:
            continue

        if field_key not in allowed_keys:
            continue

        seen_keys.add(field_key)
        normalized_defaults.append(field_key)

    if normalized_defaults:
        return normalized_defaults

    return [selectable_keys[0]]
    # APPGENESIS_PROCESS_CREATE_EDIT_FLOW_V4_DEFAULTS_END


def get_menu_process_default_visible_fields(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    return get_menu_process_default_visible_fields_v4(
        menu_key,
        menu_config,
    )


def normalize_menu_process_visible_fields_v4(
    menu_key: str,
    raw_fields: Any = None,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    # APPGENESIS_PROCESS_CREATE_EDIT_FLOW_V4_NORMALIZE_START
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if isinstance(raw_fields, dict) and menu_config is None:
        clean_menu_config = raw_fields
        raw_visible_fields = clean_menu_config.get("process_visible_fields")
    else:
        clean_menu_config = menu_config if isinstance(menu_config, dict) else {}
        raw_visible_fields = raw_fields

    if raw_visible_fields is None:
        raw_visible_fields = clean_menu_config.get("process_visible_fields")

    selectable_options = get_menu_process_selectable_field_options(
        clean_menu_key,
        clean_menu_config,
    )

    allowed_field_keys = {
        str(item.get("key") or "").strip().lower()
        for item in selectable_options
        if str(item.get("key") or "").strip()
    }

    if not allowed_field_keys:
        return []

    has_explicit_config = isinstance(clean_menu_config, dict) and (
        "process_visible_fields" in clean_menu_config
        or bool(clean_menu_config.get("process_visible_fields_configured"))
    )

    if isinstance(raw_visible_fields, str):
        raw_items = [
            chunk
            for chunk in re.split(r"[,;\n\r]+", raw_visible_fields)
            if str(chunk or "").strip()
        ]
    elif isinstance(raw_visible_fields, (list, tuple, set)):
        raw_items = list(raw_visible_fields)
    else:
        raw_items = []

    normalized_fields: list[str] = []
    seen_fields: set[str] = set()

    for raw_field in raw_items:
        field_key = str(raw_field or "").strip().lower()

        if not field_key:
            continue

        if field_key in seen_fields:
            continue

        if field_key not in allowed_field_keys:
            continue

        seen_fields.add(field_key)
        normalized_fields.append(field_key)

    if normalized_fields:
        return normalized_fields

    if has_explicit_config:
        return []

    return get_menu_process_default_visible_fields(
        clean_menu_key,
        clean_menu_config,
    )
    # APPGENESIS_PROCESS_CREATE_EDIT_FLOW_V4_NORMALIZE_END


def normalize_menu_process_visible_fields(
    menu_key: str,
    raw_fields: Any = None,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    return normalize_menu_process_visible_fields_v4(
        menu_key,
        raw_fields,
        menu_config,
    )


def normalize_meu_perfil_visible_fields(raw_fields: Any) -> list[str]:
    return normalize_menu_process_visible_fields(MENU_MEU_PERFIL_KEY, raw_fields)


def get_menu_process_visible_field_header_map(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> dict[str, str]:
    if not isinstance(menu_config, dict):
        return {}

    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    types_map = get_menu_process_field_types_map(clean_menu_key, menu_config)
    header_keys = {
        key for key, field_type in types_map.items() if field_type == "header"
    }
    selectable_field_keys = {
        key for key, field_type in types_map.items() if field_type != "header"
    }
    if not selectable_field_keys:
        return {}

    # Prefer the modern structured storage first; keep the legacy map only as a
    # compatibility fallback for older rows that have not been rewritten yet.
    mapped: dict[str, str] = {}

    raw_rows = menu_config.get("process_visible_field_rows")
    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            header_key = str(raw_row.get("header_key") or "").strip().lower()
            if field_key in selectable_field_keys and header_key in header_keys:
                mapped[field_key] = header_key

    raw_process_map = menu_config.get("process_visible_field_header_map")
    if isinstance(raw_process_map, dict):
        for raw_field_key, raw_header_key in raw_process_map.items():
            field_key = str(raw_field_key or "").strip().lower()
            header_key = str(raw_header_key or "").strip().lower()
            if (
                field_key in selectable_field_keys
                and header_key in header_keys
                and field_key not in mapped
            ):
                mapped[field_key] = header_key

    raw_map = menu_config.get("visible_field_headers")
    if isinstance(raw_map, dict):
        for raw_field_key, raw_header_key in raw_map.items():
            field_key = str(raw_field_key or "").strip().lower()
            header_key = str(raw_header_key or "").strip().lower()
            if (
                field_key in selectable_field_keys
                and header_key in header_keys
                and field_key not in mapped
            ):
                mapped[field_key] = header_key

    visible_fields = normalize_menu_process_visible_fields(
        clean_menu_key,
        menu_config.get("visible_fields"),
        menu_config,
    )
    active_header = ""
    for raw_field in visible_fields:
        clean_field = str(raw_field or "").strip().lower()
        if clean_field in header_keys:
            active_header = clean_field
            continue
        if (
            clean_field in selectable_field_keys
            and clean_field not in mapped
            and active_header
        ):
            mapped[clean_field] = active_header

    return mapped


def get_menu_process_visible_field_rows(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    selectable_options = get_menu_process_selectable_field_options(
        clean_menu_key, menu_config
    )
    header_options = get_menu_process_header_options(clean_menu_key, menu_config)
    selectable_keys = {
        str(item.get("key") or "").strip().lower()
        for item in selectable_options
        if str(item.get("key") or "").strip()
    }
    header_keys = {
        str(item.get("key") or "").strip().lower()
        for item in header_options
        if str(item.get("key") or "").strip()
    }
    if not selectable_keys:
        return []

    normalized_rows: list[dict[str, str]] = []
    seen_raw_row_fields: set[str] = set()
    raw_rows = (
        menu_config.get("process_visible_field_rows")
        if isinstance(menu_config, dict)
        else None
    )
    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue

            clean_field = str(raw_row.get("field_key") or "").strip().lower()
            if clean_field not in selectable_keys or clean_field in seen_raw_row_fields:
                continue

            clean_header = str(raw_row.get("header_key") or "").strip().lower()
            if clean_header not in header_keys:
                clean_header = ""

            seen_raw_row_fields.add(clean_field)
            normalized_rows.append(
                {
                    "field_key": clean_field,
                    "header_key": clean_header,
                }
            )

    if normalized_rows:
        return normalized_rows

    visible_fields = normalize_menu_process_visible_fields(
        clean_menu_key,
        None
        if not isinstance(menu_config, dict)
        else menu_config.get("visible_fields"),
        menu_config,
    )
    header_map = get_menu_process_visible_field_header_map(clean_menu_key, menu_config)

    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_field in visible_fields:
        clean_field = str(raw_field or "").strip().lower()
        if clean_field not in selectable_keys:
            continue
        if clean_field in seen:
            continue
        seen.add(clean_field)
        rows.append(
            {
                "field_key": clean_field,
                "header_key": str(header_map.get(clean_field) or "").strip().lower(),
            }
        )

    if rows:
        return rows

    defaults = get_menu_process_default_visible_fields(clean_menu_key, menu_config)
    default_rows = [
        {"field_key": field_key, "header_key": ""}
        for field_key in defaults
        if field_key in selectable_keys
    ]
    if default_rows:
        return default_rows

    first_option = selectable_options[0]
    return [
        {
            "field_key": str(first_option.get("key") or "").strip().lower(),
            "header_key": "",
        }
    ]


def repair_profile_authorization_menu_config_v1(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    if clean_menu_key != "perfil_de_autorizacao" or not isinstance(menu_config, dict):
        return (dict(menu_config) if isinstance(menu_config, dict) else {}, False)

    normalized_fields = get_menu_process_additional_fields(menu_config)
    fields_by_key: dict[str, dict[str, Any]] = {}
    original_field_order: list[str] = []

    for raw_field in normalized_fields:
        field_key = str(raw_field.get("key") or "").strip().lower()
        if not field_key:
            continue
        if field_key not in fields_by_key:
            original_field_order.append(field_key)
        fields_by_key[field_key] = dict(raw_field)

    def upsert_field(template: dict[str, Any]) -> bool:
        field_key = str(template.get("key") or "").strip().lower()
        if not field_key:
            return False

        existing_field = fields_by_key.get(field_key)
        if existing_field is None:
            fields_by_key[field_key] = dict(template)
            return True

        merged_field = dict(template)
        for raw_key, raw_value in existing_field.items():
            if raw_key == "key":
                continue
            if raw_value not in (None, "", [], {}):
                merged_field[raw_key] = raw_value

        fields_by_key[field_key] = merged_field
        return merged_field != existing_field

    changed = False
    changed = upsert_field(
        {
            "key": "custom_nome_do_perfil",
            "label": "Nome do perfil",
            "field_type": "list",
            "list_source_type": "manual",
            "manual_list_key": "list_perfil",
            "list_key": "list_perfil",
        }
    ) or changed
    changed = upsert_field(
        {
            "key": "custom_processo",
            "label": "Processo",
            "field_type": "list",
            "list_source_type": "profile_menu_tabs",
            "automatic_source_field_key": "custom_nome_do_perfil",
        }
    ) or changed
    changed = upsert_field(
        {
            "key": "custom_subprocesso",
            "label": "Autorização",
            "field_type": "list",
            "list_source_type": "profile_menu_tabs",
            "automatic_source_field_key": "custom_processo",
        }
    ) or changed

    canonical_field_order = [
        "custom_perfil",
        "custom_field_perfil",
        "custom_objeto_de_autorizacao",
        "custom_nome_do_perfil",
        "custom_processo",
        "custom_subprocesso",
    ]
    ordered_field_keys: list[str] = []
    seen_field_keys: set[str] = set()

    for field_key in canonical_field_order:
        if field_key in fields_by_key and field_key not in seen_field_keys:
            ordered_field_keys.append(field_key)
            seen_field_keys.add(field_key)

    for field_key in original_field_order:
        if field_key in fields_by_key and field_key not in seen_field_keys:
            ordered_field_keys.append(field_key)
            seen_field_keys.add(field_key)

    repaired_fields = [dict(fields_by_key[field_key]) for field_key in ordered_field_keys]
    if repaired_fields != normalized_fields:
        changed = True

    canonical_visible_rows: list[dict[str, str]] = []
    visible_field_headers: dict[str, str] = {}
    preserved_headerless_rows: list[dict[str, str]] = []

    raw_rows = menu_config.get("process_visible_field_rows")
    remapped_keys = {
        "custom_field_perfil",
        "custom_nome_do_perfil",
        "custom_processo",
        "custom_subprocesso",
    }

    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            header_key = str(raw_row.get("header_key") or "").strip().lower()
            if not field_key:
                continue
            if field_key in remapped_keys:
                continue
            if header_key:
                canonical_visible_rows.append(
                    {
                        "field_key": field_key,
                        "header_key": header_key,
                    }
                )
                visible_field_headers[field_key] = header_key
            else:
                preserved_headerless_rows.append(
                    {
                        "field_key": field_key,
                        "header_key": "",
                    }
                )

    if "custom_field_perfil" in fields_by_key:
        canonical_visible_rows = [
            {
                "field_key": "custom_field_perfil",
                "header_key": "custom_perfil",
            }
        ] + canonical_visible_rows
        visible_field_headers["custom_field_perfil"] = "custom_perfil"

    for field_key in ("custom_nome_do_perfil", "custom_processo", "custom_subprocesso"):
        if field_key in fields_by_key:
            canonical_visible_rows.append(
                {
                    "field_key": field_key,
                    "header_key": "custom_objeto_de_autorizacao",
                }
            )
            visible_field_headers[field_key] = "custom_objeto_de_autorizacao"

    repaired_rows = canonical_visible_rows + preserved_headerless_rows
    repaired_visible_fields: list[str] = []
    seen_visible_keys: set[str] = set()

    for row in repaired_rows:
        header_key = str(row.get("header_key") or "").strip().lower()
        field_key = str(row.get("field_key") or "").strip().lower()
        if header_key and header_key not in seen_visible_keys:
            repaired_visible_fields.append(header_key)
            seen_visible_keys.add(header_key)
        if field_key and field_key not in seen_visible_keys:
            repaired_visible_fields.append(field_key)
            seen_visible_keys.add(field_key)

    if not changed:
        return dict(menu_config), False

    repaired_menu_config = dict(menu_config)
    repaired_menu_config["additional_fields"] = repaired_fields
    repaired_menu_config["process_visible_fields"] = repaired_visible_fields
    repaired_menu_config["process_visible_field_rows"] = repaired_rows
    repaired_menu_config["process_visible_field_header_map"] = dict(visible_field_headers)
    repaired_menu_config["visible_fields"] = repaired_visible_fields
    repaired_menu_config["visible_field_headers"] = dict(visible_field_headers)
    repaired_menu_config["process_visible_fields_configured"] = True
    repaired_menu_config["process_visible_fields_refresh_version"] = str(uuid4())
    repaired_menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = str(uuid4())

    return repaired_menu_config, True


def update_sidebar_menu_process_fields_v4(
    session: Session,
    menu_key: str,
    visible_fields: list[str] | tuple[str, ...] | set[str],
    visible_headers: list[str] | tuple[str, ...] | set[str] | None = None,
) -> tuple[bool, str]:
    # APPGENESIS_PROCESS_CREATE_EDIT_FLOW_V4_PROCESS_FIELDS_SAVE_START
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if not clean_menu_key:
        return False, "Menu inválido."

    ensure_sidebar_menu_settings_defaults(session)

    if not _menu_exists(session, clean_menu_key):
        return False, "Menu não encontrado."

    menu_config = _load_menu_config(session, clean_menu_key)

    selectable_options = get_menu_process_selectable_field_options(
        clean_menu_key,
        menu_config,
    )
    header_options = get_menu_process_header_options(
        clean_menu_key,
        menu_config,
    )

    selectable_keys = {
        str(item.get("key") or "").strip().lower()
        for item in selectable_options
        if str(item.get("key") or "").strip()
    }
    header_keys = {
        str(item.get("key") or "").strip().lower()
        for item in header_options
        if str(item.get("key") or "").strip()
    }

    if not selectable_keys and not header_keys:
        return False, "Este processo não possui campos configuráveis."

    raw_visible_fields = (
        list(visible_fields) if isinstance(visible_fields, (list, tuple, set)) else []
    )
    raw_visible_headers = (
        list(visible_headers) if isinstance(visible_headers, (list, tuple, set)) else []
    )

    # APPGENESIS_PROCESS_FIELDS_PRESERVE_HEADERS_V13_START
    existing_header_map: dict[str, str] = {}

    existing_rows = menu_config.get("process_visible_field_rows")
    if isinstance(existing_rows, list):
        for existing_row in existing_rows:
            if not isinstance(existing_row, dict):
                continue

            existing_field_key = (
                str(existing_row.get("field_key") or "").strip().lower()
            )
            existing_header_key = (
                str(existing_row.get("header_key") or "").strip().lower()
            )

            if existing_field_key and existing_header_key:
                existing_header_map[existing_field_key] = existing_header_key

    existing_process_header_map = menu_config.get("process_visible_field_header_map")
    if isinstance(existing_process_header_map, dict):
        for raw_field_key, raw_header_key in existing_process_header_map.items():
            existing_field_key = str(raw_field_key or "").strip().lower()
            existing_header_key = str(raw_header_key or "").strip().lower()

            if existing_field_key and existing_header_key:
                existing_header_map[existing_field_key] = existing_header_key

    existing_legacy_header_map = menu_config.get("visible_field_headers")
    if isinstance(existing_legacy_header_map, dict):
        for raw_field_key, raw_header_key in existing_legacy_header_map.items():
            existing_field_key = str(raw_field_key or "").strip().lower()
            existing_header_key = str(raw_header_key or "").strip().lower()

            if existing_field_key and existing_header_key:
                existing_header_map[existing_field_key] = existing_header_key

    incoming_has_any_header = any(
        str(raw_header_key or "").strip() for raw_header_key in raw_visible_headers
    )

    should_preserve_existing_headers = not incoming_has_any_header and bool(
        existing_header_map
    )
    # APPGENESIS_PROCESS_FIELDS_PRESERVE_HEADERS_V13_END

    normalized_rows: list[dict[str, str]] = []
    seen_fields: set[str] = set()

    for row_index, raw_field in enumerate(raw_visible_fields):
        field_key = str(raw_field or "").strip().lower()

        if not field_key:
            continue

        if field_key in seen_fields:
            continue

        if field_key not in selectable_keys:
            continue

        header_key = (
            str(
                raw_visible_headers[row_index]
                if row_index < len(raw_visible_headers)
                else ""
            )
            .strip()
            .lower()
        )

        if header_key not in header_keys:
            header_key = ""

        # APPGENESIS_PROCESS_FIELDS_RESTORE_HEADER_ON_BLANK_SUBMIT_V13_START
        if not header_key and should_preserve_existing_headers:
            header_key = existing_header_map.get(field_key, "")

            if header_key not in header_keys:
                header_key = ""
        # APPGENESIS_PROCESS_FIELDS_RESTORE_HEADER_ON_BLANK_SUBMIT_V13_END

        seen_fields.add(field_key)
        normalized_rows.append(
            {
                "field_key": field_key,
                "header_key": header_key,
            }
        )

    process_visible_fields = [row["field_key"] for row in normalized_rows]

    process_visible_field_header_map = {
        row["field_key"]: row["header_key"]
        for row in normalized_rows
        if row.get("header_key")
    }

    legacy_visible_fields: list[str] = []
    emitted_legacy_keys: set[str] = set()
    active_header_key = ""

    for row in normalized_rows:
        field_key = row["field_key"]
        header_key = row["header_key"]

        if header_key and header_key != active_header_key:
            if header_key not in emitted_legacy_keys:
                legacy_visible_fields.append(header_key)
                emitted_legacy_keys.add(header_key)

            active_header_key = header_key

        if not header_key:
            active_header_key = ""

        if field_key in emitted_legacy_keys:
            continue

        legacy_visible_fields.append(field_key)
        emitted_legacy_keys.add(field_key)

    refresh_token = str(uuid4())

    menu_config["process_visible_fields"] = process_visible_fields
    menu_config["process_visible_field_header_map"] = process_visible_field_header_map
    menu_config["process_visible_field_rows"] = normalized_rows
    menu_config["process_visible_fields_configured"] = True
    menu_config["process_visible_fields_refresh_version"] = refresh_token

    menu_config["visible_fields"] = legacy_visible_fields
    menu_config["visible_field_headers"] = process_visible_field_header_map

    menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = refresh_token

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
    session.commit()

    return True, ""
    # APPGENESIS_PROCESS_CREATE_EDIT_FLOW_V4_PROCESS_FIELDS_SAVE_END


def update_sidebar_menu_process_fields(
    session: Session,
    menu_key: str,
    visible_fields: list[str] | tuple[str, ...] | set[str],
    visible_headers: list[str] | tuple[str, ...] | set[str] | None = None,
) -> tuple[bool, str]:
    return update_sidebar_menu_process_fields_v4(
        session,
        menu_key,
        visible_fields,
        visible_headers,
    )
