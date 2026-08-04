from __future__ import annotations

import json
import re
import unicodedata
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from appgenesis.services.process_settings.normalizers import (
    ADDITIONAL_FIELD_DEFAULT_SIZE,
    ADDITIONAL_FIELD_DEFAULT_TYPE,
    ADDITIONAL_FIELD_TEXTUAL_TYPES,
    ADDITIONAL_FIELD_MAX_SIZE,
    MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY,
    SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS,
    _build_custom_field_key_from_label,
    _build_group_scoped_custom_field_key,
    _fix_common_mojibake,
    _get_additional_field_group_key,
    _load_menu_config,
    _menu_exists,
    _normalize_additional_field_type,
    _normalize_custom_field_key,
    _normalize_menu_key,
    _normalize_sentence_case_text,
    _resolve_legacy_menu_alias,
    ensure_sidebar_menu_settings_defaults,
)


PT_PT_LABEL_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bACRONIMO\b", "ACRÓNIMO"),
    (r"\bCODIGO\b", "CÓDIGO"),
    (r"\bPAIS\b", "PAÍS"),
    (r"\bNUMERO\b", "NÚMERO"),
    (r"\bRESPONSAVEL\b", "RESPONSÁVEL"),
    (r"\bFREGESIA\b", "FREGUESIA"),
    (r"\bSOCIAS\b", "SOCIAIS"),
    (r"\bENDERECO\b", "ENDEREÇO"),
    (r"\bDESCRICAO\b", "DESCRIÇÃO"),
    (r"\bINFORMACOES\b", "INFORMAÇÕES"),
    (r"\bCONFIGURACOES\b", "CONFIGURAÇÕES"),
    (r"\bENTEDIDADE\b", "ENTIDADE"),
)


def _normalize_additional_field_label(raw_label: Any) -> str:
    clean_label = _fix_common_mojibake(str(raw_label or ""))
    clean_label = " ".join(clean_label.strip().split())
    if not clean_label:
        return ""
    clean_label = clean_label.upper()
    for pattern, replacement in PT_PT_LABEL_REPLACEMENTS:
        clean_label = re.sub(pattern, replacement, clean_label)
    return _normalize_sentence_case_text(clean_label)


def _normalize_additional_field_size(raw_size: Any, field_type: str) -> int | None:
    if field_type not in ADDITIONAL_FIELD_TEXTUAL_TYPES:
        return None
    try:
        parsed_size = int(str(raw_size or "").strip())
    except (TypeError, ValueError):
        parsed_size = ADDITIONAL_FIELD_DEFAULT_SIZE
    parsed_size = max(1, min(parsed_size, ADDITIONAL_FIELD_MAX_SIZE))
    return parsed_size


def _normalize_additional_field_required(raw_required: Any) -> bool:
    if isinstance(raw_required, bool):
        return raw_required
    clean_value = str(raw_required or "").strip().lower()
    return clean_value in {"1", "true", "sim", "yes", "on"}


def _normalize_manual_list_options_v1(raw_manual_list_options: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_manual_list_options, (list, tuple)):
        return []

    normalized_options: list[dict[str, Any]] = []
    seen_values: set[str] = set()

    for raw_option in raw_manual_list_options:
        if isinstance(raw_option, dict):
            clean_value = str(
                raw_option.get("value")
                or raw_option.get("key")
                or raw_option.get("label")
                or ""
            ).strip()
            clean_label = str(
                raw_option.get("label")
                or raw_option.get("value")
                or raw_option.get("key")
                or ""
            ).strip()
            clean_status = str(raw_option.get("status") or "active").strip() or "active"
        else:
            clean_value = str(raw_option or "").strip()
            clean_label = clean_value
            clean_status = "active"

        if not clean_value or not clean_label:
            continue

        option_lookup = clean_value.lower()
        if option_lookup in seen_values:
            continue
        seen_values.add(option_lookup)

        normalized_options.append(
            {
                "value": clean_value,
                "label": clean_label,
                "status": clean_status,
            }
        )

    return normalized_options


def get_menu_process_additional_fields(
    menu_config: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(menu_config, dict):
        return []
    return normalize_menu_process_additional_fields(
        menu_config.get("additional_fields")
    )


def _get_additional_field_group_key_v1(field_type: Any) -> str:
    return _get_additional_field_group_key(field_type)


def normalize_menu_process_additional_fields_v1(
    raw_fields: Any,
) -> list[dict[str, Any]]:
    if not isinstance(raw_fields, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    seen_labels_by_group: dict[str, set[str]] = {"header": set(), "field": set()}
    label_groups: dict[str, set[str]] = {}

    for raw_item in raw_fields:
        if isinstance(raw_item, dict):
            item_label = _normalize_additional_field_label(raw_item.get("label"))
            item_type = _normalize_additional_field_type(
                raw_item.get("field_type", raw_item.get("type"))
            )
        else:
            item_label = _normalize_additional_field_label(raw_item)
            item_type = ADDITIONAL_FIELD_DEFAULT_TYPE

        if not item_label:
            continue

        label_groups.setdefault(item_label.lower(), set()).add(
            _get_additional_field_group_key_v1(item_type)
        )

    for row_index, raw_item in enumerate(raw_fields):
        item_label = ""
        item_key = ""
        item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
        item_size: int | None = None
        item_is_required = False
        item_list_key = ""
        item_manual_list_options: list[dict[str, Any]] = []

        if isinstance(raw_item, dict):
            item_label = _normalize_additional_field_label(raw_item.get("label"))
            item_key = _normalize_custom_field_key(str(raw_item.get("key") or ""))
            item_type = _normalize_additional_field_type(
                raw_item.get("field_type", raw_item.get("type"))
            )
            item_size = _normalize_additional_field_size(
                raw_item.get("size", raw_item.get("max_length")),
                item_type,
            )
            item_is_required = _normalize_additional_field_required(
                raw_item.get("is_required", raw_item.get("required"))
            )
            item_list_key = _normalize_menu_key(
                raw_item.get("list_key", raw_item.get("listKey", ""))
            )
            item_manual_list_options = _normalize_manual_list_options_v1(
                raw_item.get("manual_list_options")
                or raw_item.get("manualListOptions")
            )
        else:
            item_label = _normalize_additional_field_label(raw_item)
            item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
            item_size = _normalize_additional_field_size(
                ADDITIONAL_FIELD_DEFAULT_SIZE,
                item_type,
            )
            item_is_required = False

        if not item_label:
            continue

        field_group_key = _get_additional_field_group_key_v1(item_type)
        normalized_label_key = item_label.lower()
        if normalized_label_key in seen_labels_by_group[field_group_key]:
            continue

        seen_labels_by_group[field_group_key].add(normalized_label_key)

        candidate_key = item_key or (
            _build_group_scoped_custom_field_key(item_label, item_type)
            if len(label_groups.get(normalized_label_key, set())) > 1
            else _build_custom_field_key_from_label(item_label)
        )
        unique_key = candidate_key
        suffix_index = 2

        while unique_key in seen_keys:
            unique_key = f"{candidate_key}_{suffix_index}"
            suffix_index += 1

        seen_keys.add(unique_key)

        normalized_item: dict[str, Any] = {
            "key": unique_key,
            "label": item_label,
            "field_type": item_type,
            "is_required": bool(item_is_required and item_type != "header"),
            "display_order": row_index,
        }

        if item_size is not None:
            normalized_item["size"] = item_size

        if item_type == "list" and item_list_key:
            normalized_item["list_key"] = item_list_key
        if item_type == "list" and item_manual_list_options:
            normalized_item["manual_list_options"] = item_manual_list_options

        normalized.append(normalized_item)

    return normalized


def _rebuild_menu_process_hierarchy_from_additional_fields_v1(
    menu_config: dict[str, Any],
    normalized_fields: list[dict[str, Any]],
) -> dict[str, Any]:
    previous_additional_fields = normalize_menu_process_additional_fields_v1(
        menu_config.get("additional_fields")
    )

    previous_field_keys = {
        str(item.get("key") or "").strip().lower()
        for item in previous_additional_fields
        if str(item.get("key") or "").strip()
    }

    existing_visible_raw = menu_config.get("process_visible_fields")
    has_existing_visible_config = isinstance(existing_visible_raw, list) and bool(
        existing_visible_raw
    )

    existing_visible_keys = {
        str(raw_key or "").strip().lower()
        for raw_key in (existing_visible_raw or [])
        if str(raw_key or "").strip()
    }

    visible_order: list[str] = []
    visible_headers: list[str] = []
    visible_rows: list[dict[str, Any]] = []
    field_header_map: dict[str, str] = {}

    active_header_key = ""

    for field_index, field_item in enumerate(normalized_fields):
        field_key = str(field_item.get("key") or "").strip().lower()

        if not field_key:
            continue

        field_type = str(field_item.get("field_type") or "").strip().lower()
        is_new_field = field_key not in previous_field_keys

        should_be_visible = (
            not has_existing_visible_config
            or field_key in existing_visible_keys
            or is_new_field
            or field_type == "header"
        )

        if field_type == "header":
            active_header_key = field_key

            if should_be_visible and field_key not in visible_order:
                visible_order.append(field_key)

            if should_be_visible and field_key not in visible_headers:
                visible_headers.append(field_key)

            continue

        if not should_be_visible:
            continue

        if field_key not in visible_order:
            visible_order.append(field_key)

        if active_header_key:
            field_header_map[field_key] = active_header_key

        visible_rows.append(
            {
                "field_key": field_key,
                "header_key": active_header_key,
                "display_order": field_index,
            }
        )

    used_headers = {
        str(row.get("header_key") or "").strip().lower()
        for row in visible_rows
        if str(row.get("header_key") or "").strip()
    }

    visible_order = [
        field_key
        for field_key in visible_order
        if field_key not in visible_headers or field_key in used_headers
    ]

    visible_headers = [
        header_key for header_key in visible_headers if header_key in used_headers
    ]

    menu_config["additional_fields"] = normalized_fields
    menu_config["process_visible_fields"] = visible_order
    menu_config["process_visible_headers"] = visible_headers
    menu_config["process_visible_field_rows"] = visible_rows
    menu_config["process_visible_field_header_map"] = field_header_map
    menu_config["process_visible_fields_configured"] = True

    legacy_visible_fields: list[str] = []
    emitted_legacy_keys: set[str] = set()
    active_header_key = ""

    for row in visible_rows:
        field_key = str(row.get("field_key") or "").strip().lower()
        header_key = str(row.get("header_key") or "").strip().lower()

        if header_key and header_key != active_header_key:
            if header_key not in emitted_legacy_keys:
                legacy_visible_fields.append(header_key)
                emitted_legacy_keys.add(header_key)

            active_header_key = header_key

        if not header_key:
            active_header_key = ""

        if not field_key or field_key in emitted_legacy_keys:
            continue

        legacy_visible_fields.append(field_key)
        emitted_legacy_keys.add(field_key)

    menu_config["visible_fields"] = legacy_visible_fields
    menu_config["visible_field_headers"] = field_header_map

    return menu_config


def update_sidebar_menu_additional_fields_v4(
    session: Session,
    menu_key: str,
    fields: list[dict[str, Any]],
) -> tuple[bool, str]:
    # APPGENESIS_PROCESS_CREATE_EDIT_FLOW_V4_ADDITIONAL_FIELDS_SAVE_START
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if not clean_menu_key:
        return False, "Menu inválido."

    # APPGENESIS_PROCESS_CREATE_EDIT_FLOW_V6_PROTECTED_GUARD
    if clean_menu_key in SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS:
        return False, "Este processo nao permite campos adicionais."

    ensure_sidebar_menu_settings_defaults(session)

    if not _menu_exists(session, clean_menu_key):
        return False, "Menu não encontrado."

    menu_config = _load_menu_config(session, clean_menu_key)

    normalized_fields = normalize_menu_process_additional_fields(fields)
    menu_config = _rebuild_menu_process_hierarchy_from_additional_fields_v1(
        menu_config,
        normalized_fields,
    )

    refresh_token = str(uuid4())
    menu_config["process_additional_fields_refresh_version"] = refresh_token
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
    # APPGENESIS_PROCESS_CREATE_EDIT_FLOW_V4_ADDITIONAL_FIELDS_SAVE_END


def update_sidebar_menu_additional_fields_v1(
    session: Session,
    menu_key: str,
    fields: list[dict[str, Any]],
) -> tuple[bool, str]:
    return update_sidebar_menu_additional_fields_v4(
        session,
        menu_key,
        fields,
    )


def move_sidebar_menu_additional_field(
    session: Session,
    menu_key: str,
    field_key: str,
    direction: str,
) -> tuple[bool, str]:
    """
    Move um campo adicional para cima ou para baixo no formulário.
    Se o campo for do tipo 'header' (Cabeçalho), move o bloco inteiro junto com os campos abaixo.
    """
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if not clean_menu_key:
        return False, "Menu inválido."

    if clean_menu_key in SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS:
        return False, "Este processo não permite mover campos."

    clean_direction = str(direction or "").strip().lower()
    if clean_direction not in {"up", "down"}:
        return False, "Direção inválida."

    if not _menu_exists(session, clean_menu_key):
        return False, "Menu não encontrado."

    raw_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": clean_menu_key},
    ).scalar_one_or_none()

    menu_config: dict[str, Any] = {}

    if isinstance(raw_config, str) and raw_config.strip():
        try:
            parsed_config = json.loads(raw_config)
            if isinstance(parsed_config, dict):
                menu_config = parsed_config
        except json.JSONDecodeError:
            menu_config = {}

    normalized_fields = normalize_menu_process_additional_fields_v1(
        menu_config.get("additional_fields")
    )

    if not normalized_fields:
        return False, "Nenhum campo adicional encontrado."

    clean_field_key = str(field_key or "").strip().lower()

    # Encontrar o índice do campo
    field_index = None
    for idx, field in enumerate(normalized_fields):
        if str(field.get("key") or "").strip().lower() == clean_field_key:
            field_index = idx
            break

    if field_index is None:
        return False, "Campo não encontrado."

    field_type = (
        str(normalized_fields[field_index].get("field_type") or "").strip().lower()
    )

    # Determinar o bloco a mover
    if field_type == "header":
        # Se for header, mover o bloco inteiro (header + campos seguintes até próximo header)
        block_start = field_index
        block_end = field_index
        for idx in range(field_index + 1, len(normalized_fields)):
            next_field_type = (
                str(normalized_fields[idx].get("field_type") or "").strip().lower()
            )
            if next_field_type == "header":
                break
            block_end = idx
        block_size = block_end - block_start + 1
    else:
        # Campo normal, mover apenas ele
        block_start = field_index
        block_end = field_index
        block_size = 1

    # Calcular o alvo
    if clean_direction == "up":
        if block_start <= 0:
            return False, "Este campo já está no topo."
        target_index = block_start - 1
    else:
        if block_end >= len(normalized_fields) - 1:
            return False, "Este campo já está no fim."
        target_index = block_end + 1

    # Se o alvo é um header, ajustar
    target_type = (
        str(normalized_fields[target_index].get("field_type") or "").strip().lower()
    )
    if target_type == "header":
        if clean_direction == "up":
            # Mover para antes do header
            target_index = target_index
        else:
            # Mover para depois do bloco do header
            for idx in range(target_index + 1, len(normalized_fields)):
                next_field_type = (
                    str(normalized_fields[idx].get("field_type") or "").strip().lower()
                )
                if next_field_type == "header":
                    break
                target_index = idx
            target_index = min(target_index + 1, len(normalized_fields) - 1)

    # Executar a troca
    if clean_direction == "up":
        # Remover bloco atual e inserir antes do alvo
        block = normalized_fields[block_start : block_end + 1]
        normalized_fields = (
            normalized_fields[:target_index]
            + block
            + normalized_fields[target_index:block_start]
            + normalized_fields[block_end + 1 :]
        )
    else:
        # Remover bloco atual e inserir depois do alvo
        block = normalized_fields[block_start : block_end + 1]
        normalized_fields = (
            normalized_fields[:block_start]
            + normalized_fields[block_end + 1 : target_index + 1]
            + block
            + normalized_fields[target_index + 1 :]
        )

    # Reconstruir a hierarquia e salvar
    menu_config = _rebuild_menu_process_hierarchy_from_additional_fields_v1(
        menu_config,
        normalized_fields,
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
    session.commit()

    return True, ""


def _normalize_process_list_key_v8(raw_key: Any) -> str:
    clean_value = str(raw_key or "").strip().lower()
    clean_value = (
        unicodedata.normalize("NFKD", clean_value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    clean_value = re.sub(r"[^a-z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")
    return clean_value


def _normalize_additional_field_list_source_type_v1(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value in {"automatic", "field_list", "active_menus", "profile_menu_tabs"}:
        return clean_value
    return "manual"


def _normalize_additional_field_source_key_v1(raw_value: Any) -> str:
    return _normalize_menu_key(raw_value)


def normalize_menu_process_additional_fields(raw_fields: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_fields, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_labels_by_group: dict[str, set[str]] = {"header": set(), "field": set()}
    seen_keys: set[str] = set()
    label_groups: dict[str, set[str]] = {}

    for raw_item in raw_fields:
        if isinstance(raw_item, dict):
            item_label = _normalize_additional_field_label(raw_item.get("label"))
            item_type = _normalize_additional_field_type(
                raw_item.get("field_type", raw_item.get("type"))
            )
        else:
            item_label = _normalize_additional_field_label(raw_item)
            item_type = ADDITIONAL_FIELD_DEFAULT_TYPE

        if not item_label:
            continue

        label_groups.setdefault(item_label.lower(), set()).add(
            _get_additional_field_group_key_v1(item_type)
        )

    for raw_item in raw_fields:
        item_label = ""
        item_key = ""
        item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
        item_size: int | None = None
        item_is_required = False
        item_list_key = ""
        item_manual_list_options: list[dict[str, Any]] = []
        item_list_source_type = "manual"
        item_manual_list_key = ""
        item_manual_list_items: list[str] = []
        item_manual_list_items_csv = ""
        item_automatic_source_process_key = ""
        item_automatic_source_section_key = ""
        item_automatic_source_field_key = ""
        item_automatic_only_active = False

        if isinstance(raw_item, dict):
            item_label = _normalize_additional_field_label(raw_item.get("label"))
            item_key = _normalize_custom_field_key(str(raw_item.get("key") or ""))
            item_type = _normalize_additional_field_type(
                raw_item.get("field_type", raw_item.get("type"))
            )
            item_size = _normalize_additional_field_size(
                raw_item.get("size", raw_item.get("max_length")),
                item_type,
            )
            item_is_required = _normalize_additional_field_required(
                raw_item.get("is_required", raw_item.get("required"))
            )
            item_list_key = _normalize_process_list_key_v8(
                raw_item.get("list_key")
                or raw_item.get("listKey")
                or raw_item.get("process_list_key")
                or raw_item.get("processListKey")
            )
            item_manual_list_key = _normalize_process_list_key_v8(
                raw_item.get("manual_list_key")
                or raw_item.get("manualListKey")
                or item_list_key
            )
            item_manual_list_options = _normalize_manual_list_options_v1(
                raw_item.get("manual_list_options")
                or raw_item.get("manualListOptions")
            )
            item_automatic_source_process_key = (
                _normalize_additional_field_source_key_v1(
                    raw_item.get("automatic_source_process_key")
                    or raw_item.get("automaticSourceProcessKey")
                )
            )
            item_automatic_source_section_key = (
                _normalize_additional_field_source_key_v1(
                    raw_item.get("automatic_source_section_key")
                    or raw_item.get("automaticSourceSectionKey")
                )
            )
            item_automatic_source_field_key = _normalize_additional_field_source_key_v1(
                raw_item.get("automatic_source_field_key")
                or raw_item.get("automaticSourceFieldKey")
            )
            item_automatic_only_active = _normalize_additional_field_required(
                raw_item.get("automatic_only_active")
                or raw_item.get("automaticOnlyActive")
            )
            item_list_source_type = _normalize_additional_field_list_source_type_v1(
                raw_item.get("list_source_type")
                or raw_item.get("listSourceType")
                or (
                    "automatic"
                    if (
                        item_automatic_source_process_key
                        or item_automatic_source_section_key
                        or item_automatic_source_field_key
                    )
                    else "manual"
                )
            )
            raw_manual_items = (
                raw_item.get("manual_list_items")
                or raw_item.get("manualListItems")
                or raw_item.get("manual_list_items_csv")
                or raw_item.get("manualListItemsCsv")
            )
            if isinstance(raw_manual_items, str):
                raw_values = [v.strip() for v in raw_manual_items.split(",")]
            elif isinstance(raw_manual_items, (list, tuple)):
                raw_values = [str(v).strip() for v in raw_manual_items]
            else:
                raw_values = []
            _seen_items: set[str] = set()
            for _v in raw_values:
                if _v and _v.lower() not in _seen_items:
                    _seen_items.add(_v.lower())
                    item_manual_list_items.append(_v)
            item_manual_list_items_csv = ", ".join(item_manual_list_items)
        else:
            item_label = _normalize_additional_field_label(raw_item)
            item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
            item_size = _normalize_additional_field_size(
                ADDITIONAL_FIELD_DEFAULT_SIZE,
                item_type,
            )
            item_is_required = False

        if not item_label:
            continue

        field_group_key = _get_additional_field_group_key_v1(item_type)
        normalized_label_key = item_label.lower()

        if normalized_label_key in seen_labels_by_group[field_group_key]:
            continue

        seen_labels_by_group[field_group_key].add(normalized_label_key)

        candidate_key = item_key or (
            _build_group_scoped_custom_field_key(item_label, item_type)
            if len(label_groups.get(normalized_label_key, set())) > 1
            else _build_custom_field_key_from_label(item_label)
        )
        unique_key = candidate_key
        suffix_index = 2

        while unique_key in seen_keys:
            unique_key = f"{candidate_key}_{suffix_index}"
            suffix_index += 1

        seen_keys.add(unique_key)

        if item_type == "list":
            if not item_manual_list_key:
                item_manual_list_key = item_list_key
            if item_list_source_type == "manual" and not item_manual_list_key:
                item_manual_list_key = _normalize_process_list_key_v8(item_label)
            item_list_key = (
                item_manual_list_key if item_list_source_type == "manual" else ""
            )

        normalized_item: dict[str, Any] = {
            "key": unique_key,
            "label": item_label,
            "field_type": item_type,
            "is_required": bool(item_is_required and item_type != "header"),
        }

        if item_size is not None:
            normalized_item["size"] = item_size

        if item_type == "list":
            normalized_item["list_source_type"] = item_list_source_type
            normalized_item["manual_list_key"] = item_manual_list_key
            normalized_item["list_key"] = item_list_key
            if item_manual_list_options:
                normalized_item["manual_list_options"] = item_manual_list_options
            if item_manual_list_items:
                normalized_item["manual_list_items"] = item_manual_list_items
                normalized_item["manual_list_items_csv"] = item_manual_list_items_csv
            if item_list_source_type in {
                "automatic",
                "field_list",
                "profile_menu_tabs",
            }:
                normalized_item["automatic_source_process_key"] = (
                    item_automatic_source_process_key
                )
                normalized_item["automatic_source_section_key"] = (
                    item_automatic_source_section_key
                )
                normalized_item["automatic_source_field_key"] = (
                    item_automatic_source_field_key
                )
                if item_list_source_type == "automatic":
                    normalized_item["automatic_only_active"] = bool(
                        item_automatic_only_active
                    )

        normalized.append(normalized_item)

    if not normalized:
        return normalized

    header_items = [
        dict(item)
        for item in normalized
        if str(item.get("field_type") or "").strip().lower() == "header"
    ]
    non_header_items = [
        dict(item)
        for item in normalized
        if str(item.get("field_type") or "").strip().lower() != "header"
    ]
    return header_items + non_header_items
