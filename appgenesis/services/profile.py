from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appgenesis.menu_settings import get_sidebar_menu_settings
from appgenesis.models import Entity, Member, MemberEntity, MemberEntityStatus, User

PROCESS_SUBSEQUENT_ALLOWED_OPERATORS = {
    "equals",
    "not_equals",
    "is_empty",
    "is_not_empty",
}
PROCESS_QUANTITY_ALLOWED_FIELD_TYPES = {"text", "number", "email", "phone", "date", "flag", "list"}


def _normalize_process_rule_lookup_text(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if not clean_value:
        return ""
    normalized = unicodedata.normalize("NFD", clean_value)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _normalize_meu_perfil_duplicate_lookup_text(raw_value: Any) -> str:
    normalized = _normalize_process_rule_lookup_text(raw_value)
    if not normalized:
        return ""
    return " ".join(normalized.replace("_", " ").replace("-", " ").split())


def is_meu_perfil_builtin_duplicate_field(
    field_key: Any,
    field_label: Any,
    builtin_field_labels: dict[str, str] | None = None,
) -> bool:
    clean_key = str(field_key or "").strip().lower()
    if not clean_key.startswith("custom_"):
        return False

    builtin_labels = builtin_field_labels or {}
    builtin_lookup_values: set[str] = set()

    for builtin_key, builtin_label in builtin_labels.items():
        normalized_key = _normalize_meu_perfil_duplicate_lookup_text(builtin_key)
        normalized_label = _normalize_meu_perfil_duplicate_lookup_text(builtin_label)

        if normalized_key:
            builtin_lookup_values.add(normalized_key)
        if normalized_label:
            builtin_lookup_values.add(normalized_label)

    if not builtin_lookup_values:
        return False

    normalized_custom_key = _normalize_meu_perfil_duplicate_lookup_text(clean_key.removeprefix("custom_"))
    normalized_custom_label = _normalize_meu_perfil_duplicate_lookup_text(field_label)

    return (
        (normalized_custom_key in builtin_lookup_values if normalized_custom_key else False)
        or (normalized_custom_label in builtin_lookup_values if normalized_custom_label else False)
    )


def resolve_meu_perfil_builtin_duplicate_field_key(
    field_key: Any,
    field_label: Any,
    builtin_field_labels: dict[str, str] | None = None,
) -> str:
    clean_key = str(field_key or "").strip().lower()
    if not clean_key.startswith("custom_"):
        return ""

    builtin_labels = builtin_field_labels or {}
    builtin_lookup_by_key: dict[str, str] = {}

    for builtin_key, builtin_label in builtin_labels.items():
        normalized_key = _normalize_meu_perfil_duplicate_lookup_text(builtin_key)
        normalized_label = _normalize_meu_perfil_duplicate_lookup_text(builtin_label)

        if normalized_key:
            builtin_lookup_by_key[normalized_key] = str(builtin_key or "").strip().lower()
        if normalized_label:
            builtin_lookup_by_key[normalized_label] = str(builtin_key or "").strip().lower()

    normalized_custom_key = _normalize_meu_perfil_duplicate_lookup_text(clean_key.removeprefix("custom_"))
    normalized_custom_label = _normalize_meu_perfil_duplicate_lookup_text(field_label)

    if normalized_custom_key and normalized_custom_key in builtin_lookup_by_key:
        return builtin_lookup_by_key[normalized_custom_key]
    if normalized_custom_label and normalized_custom_label in builtin_lookup_by_key:
        return builtin_lookup_by_key[normalized_custom_label]
    return ""


def normalize_process_subsequent_operator(raw_value: Any) -> str:
    clean_value = str(raw_value or "equals").strip().lower()
    if clean_value in PROCESS_SUBSEQUENT_ALLOWED_OPERATORS:
        return clean_value
    return "equals"


def normalize_process_subsequent_rules(raw_rules: Any) -> list[dict[str, str]]:
    if not isinstance(raw_rules, (list, tuple, set)):
        return []

    normalized_rules: list[dict[str, str]] = []
    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            continue
        rule_key = str(raw_rule.get("key") or "").strip().lower()
        trigger_field = str(
            raw_rule.get("trigger_field")
            or raw_rule.get("trigger_field_key")
            or raw_rule.get("subsequent_trigger_field")
            or raw_rule.get("triggerField")
            or raw_rule.get("triggerFieldKey")
            or ""
        ).strip().lower()
        target_field = str(
            raw_rule.get("field_key")
            or raw_rule.get("subsequent_field")
            or raw_rule.get("subsequent_field_key")
            or raw_rule.get("fieldKey")
            or raw_rule.get("target_field")
            or raw_rule.get("targetFieldKey")
            or ""
        ).strip().lower()
        operator = normalize_process_subsequent_operator(
            raw_rule.get("operator") or raw_rule.get("condition")
        )
        trigger_value = str(
            raw_rule.get("trigger_value")
            or raw_rule.get("subsequent_trigger_value")
            or raw_rule.get("triggerValue")
            or ""
        ).strip()
        if operator in {"is_empty", "is_not_empty"}:
            trigger_value = ""
        if not trigger_field or not target_field:
            continue
        normalized_rules.append(
            {
                "key": rule_key,
                "trigger_field": trigger_field,
                "field_key": target_field,
                "operator": operator,
                "trigger_value": trigger_value,
            }
        )
    return normalized_rules


def is_process_subsequent_rule_met(
    rule: dict[str, Any],
    values_by_field: dict[str, Any] | None,
) -> bool:
    current_values = values_by_field or {}
    trigger_field = str(rule.get("trigger_field") or "").strip().lower()
    if not trigger_field:
        return True
    operator = normalize_process_subsequent_operator(rule.get("operator"))
    current_value = str(current_values.get(trigger_field) or "").strip()
    normalized_current_value = _normalize_process_rule_lookup_text(current_value)
    normalized_rule_value = _normalize_process_rule_lookup_text(rule.get("trigger_value"))

    if operator == "is_empty":
        return current_value == ""
    if operator == "is_not_empty":
        return current_value != ""
    if operator == "not_equals":
        return normalized_current_value != normalized_rule_value
    return normalized_current_value == normalized_rule_value


def get_hidden_process_targets_from_rules(
    raw_rules: Any,
    values_by_field: dict[str, Any] | None,
) -> set[str]:
    rules = normalize_process_subsequent_rules(raw_rules)
    grouped_rules: dict[str, list[dict[str, str]]] = {}
    for rule in rules:
        target_field = str(rule.get("field_key") or "").strip().lower()
        if not target_field:
            continue
        grouped_rules.setdefault(target_field, []).append(rule)

    hidden_targets: set[str] = set()
    for target_field, target_rules in grouped_rules.items():
        if not all(is_process_subsequent_rule_met(rule, values_by_field) for rule in target_rules):
            hidden_targets.add(target_field)
    return hidden_targets


def filter_process_fields_by_hidden_targets(
    field_keys: list[str] | tuple[str, ...],
    hidden_targets: set[str] | None,
    field_section_map: dict[str, str] | None = None,
) -> list[str]:
    hidden = {
        str(field_key or "").strip().lower()
        for field_key in (hidden_targets or set())
        if str(field_key or "").strip()
    }
    section_map = {
        str(field_key or "").strip().lower(): str(section_key or "").strip().lower()
        for field_key, section_key in (field_section_map or {}).items()
        if str(field_key or "").strip()
    }
    filtered_fields: list[str] = []
    for raw_field_key in field_keys or []:
        field_key = str(raw_field_key or "").strip().lower()
        if not field_key:
            continue
        section_key = section_map.get(field_key, "")
        if field_key in hidden or (section_key and section_key in hidden):
            continue
        filtered_fields.append(field_key)
    return filtered_fields

def _normalize_profile_field_value(raw_field_value: Any) -> str:
    if raw_field_value is None:
        return ""
    if isinstance(raw_field_value, bool):
        return "1" if raw_field_value else "0"
    if isinstance(raw_field_value, (int, float)):
        return str(raw_field_value).strip()
    return str(raw_field_value).strip()


def _normalize_member_profile_field_map(values: dict[str, Any] | None) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for raw_key, raw_field_value in (values or {}).items():
        clean_key = str(raw_key or "").strip().lower()
        if not clean_key:
            continue
        clean_field_value = _normalize_profile_field_value(raw_field_value)
        if not clean_field_value:
            continue
        normalized[clean_key] = clean_field_value
    return normalized


def parse_member_profile_fields(raw_value: Any) -> dict[str, str]:
    if not isinstance(raw_value, str):
        return {}
    clean_value = raw_value.strip()
    if not clean_value:
        return {}
    try:
        parsed = json.loads(clean_value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}

    return _normalize_member_profile_field_map(parsed)

def serialize_member_profile_fields(values: dict[str, str]) -> str | None:
    normalized = _normalize_member_profile_field_map(values)
    if not normalized:
        return None
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True)


def merge_member_profile_fields_v1(
    existing_values: Any,
    updated_values: dict[str, Any] | None = None,
    *,
    removed_keys: set[str] | None = None,
    removed_prefixes: tuple[str, ...] = (),
) -> dict[str, str]:
    if isinstance(existing_values, str):
        merged_fields = parse_member_profile_fields(existing_values)
    elif isinstance(existing_values, dict):
        merged_fields = _normalize_member_profile_field_map(existing_values)
    else:
        merged_fields = {}

    normalized_removed_keys = {
        str(raw_key or "").strip().lower()
        for raw_key in (removed_keys or set())
        if str(raw_key or "").strip()
    }
    normalized_removed_prefixes = tuple(
        str(raw_prefix or "").strip().lower()
        for raw_prefix in removed_prefixes
        if str(raw_prefix or "").strip()
    )

    if normalized_removed_keys or normalized_removed_prefixes:
        for existing_key in list(merged_fields.keys()):
            if existing_key in normalized_removed_keys:
                merged_fields.pop(existing_key, None)
                continue
            if any(existing_key.startswith(prefix) for prefix in normalized_removed_prefixes):
                merged_fields.pop(existing_key, None)

    merged_fields.update(_normalize_member_profile_field_map(updated_values))
    return merged_fields


def merge_member_profile_fields_v1(
    existing_values: Any,
    updated_values: dict[str, Any] | None = None,
    *,
    removed_keys: set[str] | None = None,
    removed_prefixes: tuple[str, ...] = (),
) -> dict[str, str]:
    if isinstance(existing_values, str):
        merged_fields = parse_member_profile_fields(existing_values)
    elif isinstance(existing_values, dict):
        merged_fields = _normalize_member_profile_field_map(existing_values)
    else:
        merged_fields = {}

    normalized_removed_keys = {
        str(raw_key or "").strip().lower()
        for raw_key in (removed_keys or set())
        if str(raw_key or "").strip()
    }
    normalized_removed_prefixes = tuple(
        str(raw_prefix or "").strip().lower()
        for raw_prefix in removed_prefixes
        if str(raw_prefix or "").strip()
    )

    if normalized_removed_keys or normalized_removed_prefixes:
        for existing_key in list(merged_fields.keys()):
            if existing_key in normalized_removed_keys:
                merged_fields.pop(existing_key, None)
                continue
            if any(existing_key.startswith(prefix) for prefix in normalized_removed_prefixes):
                merged_fields.pop(existing_key, None)

    merged_fields.update(_normalize_member_profile_field_map(updated_values))
    return merged_fields

def build_menu_process_field_storage_key(menu_key: str, field_key: str) -> str:
    clean_menu_key = str(menu_key or "").strip().lower()
    clean_field_key = str(field_key or "").strip().lower()
    if not clean_menu_key or not clean_field_key:
        return ""
    return f"process__{clean_menu_key}__{clean_field_key}"

def build_menu_process_records_storage_key(menu_key: str) -> str:
    clean_menu_key = str(menu_key or "").strip().lower()
    if not clean_menu_key:
        return ""
    return f"process_records__{clean_menu_key}"


def build_menu_process_quantity_storage_key(menu_key: str, rule_key: str) -> str:
    clean_menu_key = str(menu_key or "").strip().lower()
    clean_rule_key = str(rule_key or "").strip().lower()
    if not clean_menu_key or not clean_rule_key:
        return ""
    return f"quantity__{clean_menu_key}__{clean_rule_key}"


def parse_menu_process_quantity_values(raw_value: Any) -> list[dict[str, str]]:
    if not isinstance(raw_value, str):
        return []
    clean_value = raw_value.strip()
    if not clean_value:
        return []
    try:
        parsed = json.loads(clean_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []

    normalized_items: list[dict[str, str]] = []
    for raw_item in parsed:
        if not isinstance(raw_item, dict):
            continue
        clean_item: dict[str, str] = {}
        for raw_key, raw_field_value in raw_item.items():
            clean_key = str(raw_key or "").strip().lower()
            if not clean_key:
                continue
            clean_field_value = _normalize_profile_field_value(raw_field_value)
            if not clean_field_value:
                continue
            clean_item[clean_key] = clean_field_value
        normalized_items.append(clean_item)
    return normalized_items


def serialize_menu_process_quantity_values(
    values: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> str | None:
    normalized_items: list[dict[str, str]] = []
    for raw_item in values or []:
        if not isinstance(raw_item, dict):
            continue
        clean_item: dict[str, str] = {}
        for raw_key, raw_value in raw_item.items():
            clean_key = str(raw_key or "").strip().lower()
            if not clean_key:
                continue
            clean_field_value = _normalize_profile_field_value(raw_value)
            if not clean_field_value:
                continue
            clean_item[clean_key] = clean_field_value
        normalized_items.append(clean_item)
    return json.dumps(normalized_items, ensure_ascii=False) if normalized_items else None


def get_menu_process_quantity_repeated_field_keys(raw_rules: Any) -> set[str]:
    if not isinstance(raw_rules, list):
        return set()

    repeated_field_keys: set[str] = set()
    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            continue
        for raw_field_key in raw_rule.get("repeated_field_keys") or []:
            clean_field_key = str(raw_field_key or "").strip().lower()
            if clean_field_key:
                repeated_field_keys.add(clean_field_key)
    return repeated_field_keys

def parse_menu_process_records(raw_value: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_value, str):
        return []
    clean_value = raw_value.strip()
    if not clean_value:
        return []
    try:
        parsed = json.loads(clean_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []

    normalized_records: list[dict[str, Any]] = []
    for raw_item in parsed:
        if not isinstance(raw_item, dict):
            continue
        record_id = str(raw_item.get("record_id", raw_item.get("id")) or "").strip()
        created_at = str(raw_item.get("created_at") or "").strip()
        section_key = str(raw_item.get("section_key") or "").strip()
        raw_values = raw_item.get("values")
        if not isinstance(raw_values, dict):
            continue
        values: dict[str, str] = {}
        for raw_key, raw_field_value in raw_values.items():
            clean_key = str(raw_key or "").strip().lower()
            if not clean_key:
                continue
            clean_field_value = _normalize_profile_field_value(raw_field_value)
            if not clean_field_value:
                continue
            values[clean_key] = clean_field_value
        if not values:
            continue
        if not record_id:
            seed_value = f"{created_at}|{section_key}|{json.dumps(values, ensure_ascii=False, sort_keys=True)}|{len(normalized_records)}"
            record_id = hashlib.sha1(seed_value.encode("utf-8")).hexdigest()[:16]
        normalized_records.append(
            {
                "record_id": record_id,
                "created_at": created_at,
                "section_key": section_key,
                "values": values,
            }
        )
    return normalized_records

def serialize_menu_process_records(values: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> str | None:
    normalized_records: list[dict[str, Any]] = []
    for row_index, raw_item in enumerate(values or []):
        if not isinstance(raw_item, dict):
            continue
        record_id = str(raw_item.get("record_id", raw_item.get("id")) or "").strip()
        created_at = str(raw_item.get("created_at") or "").strip()
        section_key = str(raw_item.get("section_key") or "").strip()
        raw_values = raw_item.get("values")
        if not isinstance(raw_values, dict):
            continue
        clean_values: dict[str, str] = {}
        for raw_key, raw_field_value in raw_values.items():
            clean_key = str(raw_key or "").strip().lower()
            if not clean_key:
                continue
            clean_field_value = _normalize_profile_field_value(raw_field_value)
            if not clean_field_value:
                continue
            clean_values[clean_key] = clean_field_value
        if not clean_values:
            continue
        if not record_id:
            seed_value = f"{created_at}|{section_key}|{json.dumps(clean_values, ensure_ascii=False, sort_keys=True)}|{row_index}"
            record_id = hashlib.sha1(seed_value.encode("utf-8")).hexdigest()[:16]
        normalized_records.append(
            {
                "record_id": record_id,
                "created_at": created_at,
                "section_key": section_key,
                "values": clean_values,
            }
        )
    if not normalized_records:
        return None
    return json.dumps(normalized_records, ensure_ascii=False)


def normalize_process_list_source_type_v1(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value in {"automatic", "field_list", "active_menus", "profile_menu_tabs"}:
        return clean_value
    return "manual"


def _normalize_process_list_source_key_v1(raw_value: Any) -> str:
    return str(raw_value or "").strip().lower()


def _normalize_process_record_state_v1(raw_value: Any) -> str:
    clean_value = _normalize_process_list_source_key_v1(raw_value)
    if clean_value in {"inactive", "inativo", "0", "false", "off"}:
        return "inactive"
    return "active"


def _normalize_visible_sidebar_menu_keys_for_list_resolver_v1(
    raw_keys: set[str] | list[str] | tuple[str, ...] | None,
) -> set[str]:
    if not isinstance(raw_keys, (set, list, tuple)):
        return set()
    return {
        clean_key
        for clean_key in (
            _normalize_process_list_source_key_v1(raw_key)
            for raw_key in raw_keys
        )
        if clean_key
    }


def _resolve_active_sidebar_menu_list_options_v1(
    *,
    sidebar_menu_settings: list[dict[str, Any]],
    visible_sidebar_menu_keys: set[str],
) -> list[dict[str, str]]:
    resolved_options: list[dict[str, str]] = []
    seen_keys: set[str] = set()

    for raw_setting in sidebar_menu_settings:
        if not isinstance(raw_setting, dict):
            continue

        menu_key = _normalize_process_list_source_key_v1(raw_setting.get("key"))
        if not menu_key or menu_key in seen_keys:
            continue

        if visible_sidebar_menu_keys and menu_key not in visible_sidebar_menu_keys:
            continue

        if not bool(raw_setting.get("is_active")) or bool(raw_setting.get("is_deleted")):
            continue

        menu_label = str(raw_setting.get("label") or menu_key).strip() or menu_key
        seen_keys.add(menu_key)
        resolved_options.append(
            {
                "value": menu_key,
                "label": menu_label,
                "status": "active",
            }
        )

    return resolved_options


def _resolve_source_setting_first_section_key_v1(
    source_setting: dict[str, Any] | None,
) -> str:
    if not isinstance(source_setting, dict):
        return ""

    raw_rows = source_setting.get("process_visible_field_rows")
    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue
            header_key = _normalize_process_list_source_key_v1(raw_row.get("header_key"))
            if header_key:
                return header_key

    for collection_key in ("process_field_options", "process_additional_fields"):
        raw_fields = source_setting.get(collection_key)
        if not isinstance(raw_fields, list):
            continue
        for raw_field in raw_fields:
            if not isinstance(raw_field, dict):
                continue
            field_type = _normalize_process_list_source_key_v1(
                raw_field.get("field_type") or raw_field.get("type")
            )
            if field_type == "header":
                field_key = _normalize_process_list_source_key_v1(raw_field.get("key"))
                if field_key:
                    return field_key

    return ""


def _build_automatic_source_section_candidates_v1(
    source_section_key: str,
    *,
    source_setting: dict[str, Any] | None = None,
) -> list[str]:
    candidates: list[str] = []

    source_setting_first_section_key = _resolve_source_setting_first_section_key_v1(
        source_setting
    )

    for candidate in (
        source_section_key,
        f"{source_section_key}_header" if source_section_key and not source_section_key.endswith("_header") else "",
        source_section_key[: -len("_header")] if source_section_key.endswith("_header") else "",
        source_setting_first_section_key,
        f"{source_setting_first_section_key}_header"
        if source_setting_first_section_key and not source_setting_first_section_key.endswith("_header")
        else "",
        source_setting_first_section_key[: -len("_header")]
        if source_setting_first_section_key.endswith("_header")
        else "",
    ):
        clean_candidate = _normalize_process_list_source_key_v1(candidate)
        if clean_candidate and clean_candidate not in candidates:
            candidates.append(clean_candidate)

    return candidates


def _build_source_field_meta_by_key_v1(
    source_setting: dict[str, Any],
) -> dict[str, dict[str, str]]:
    field_meta_by_key: dict[str, dict[str, str]] = {}

    for collection_key in ("process_field_options", "process_additional_fields"):
        raw_fields = source_setting.get(collection_key)
        if not isinstance(raw_fields, list):
            continue

        for raw_field in raw_fields:
            if not isinstance(raw_field, dict):
                continue

            field_key = _normalize_process_list_source_key_v1(raw_field.get("key"))
            if not field_key or field_key in field_meta_by_key:
                continue

            field_meta_by_key[field_key] = {
                "key": field_key,
                "label": str(raw_field.get("label") or "").strip(),
                "field_type": _normalize_process_list_source_key_v1(
                    raw_field.get("field_type") or raw_field.get("type")
                ),
            }

    return field_meta_by_key


def _build_automatic_source_field_candidates_v1(
    *,
    source_setting: dict[str, Any],
    source_section_key: str,
    source_field_key: str,
) -> list[str]:
    field_meta_by_key = _build_source_field_meta_by_key_v1(source_setting)
    non_header_field_keys = {
        key
        for key, meta in field_meta_by_key.items()
        if meta.get("field_type") != "header"
    }
    configured_field_meta = field_meta_by_key.get(source_field_key)
    section_field_keys = {
        _normalize_process_list_source_key_v1(raw_row.get("field_key"))
        for raw_row in (source_setting.get("process_visible_field_rows") or [])
        if isinstance(raw_row, dict)
        and _normalize_process_list_source_key_v1(raw_row.get("header_key")) == source_section_key
        and _normalize_process_list_source_key_v1(raw_row.get("field_key"))
    }
    candidates: list[str] = []

    def append_candidate(raw_key: Any) -> None:
        clean_key = _normalize_process_list_source_key_v1(raw_key)
        if clean_key and clean_key not in candidates:
            candidates.append(clean_key)

    if source_field_key in non_header_field_keys:
        append_candidate(source_field_key)
    elif configured_field_meta and configured_field_meta.get("field_type") == "header":
        configured_label_lookup = _normalize_process_rule_lookup_text(
            configured_field_meta.get("label")
        )
        for key, meta in field_meta_by_key.items():
            if key not in non_header_field_keys:
                continue
            if section_field_keys and key not in section_field_keys:
                continue
            if _normalize_process_rule_lookup_text(meta.get("label")) != configured_label_lookup:
                continue
            append_candidate(key)
    else:
        append_candidate(source_field_key)

    for base_candidate in list(candidates):
        legacy_alias = re.sub(r"_\d+$", "", base_candidate)
        if legacy_alias != base_candidate:
            append_candidate(legacy_alias)

    return candidates


def _is_legacy_profile_menu_tabs_config_v1(
    *,
    current_menu_key: str,
    field_definition: dict[str, Any],
    list_source_type: str,
) -> bool:
    if list_source_type != "automatic":
        return False

    if _normalize_process_list_source_key_v1(current_menu_key) != "perfil_de_autorizacao":
        return False

    field_key = _normalize_process_list_source_key_v1(field_definition.get("key"))
    source_process_key = _normalize_process_list_source_key_v1(
        field_definition.get("automatic_source_process_key")
        or field_definition.get("automaticSourceProcessKey")
    )
    source_field_key = _normalize_process_list_source_key_v1(
        field_definition.get("automatic_source_field_key")
        or field_definition.get("automaticSourceFieldKey")
    )

    return (
        field_key == "custom_processo"
        and source_process_key == "perfil_de_autorizacao"
        and source_field_key in {"custom_perfil", "custom_perfil_2", "custom_nome_do_perfil"}
    )


def _build_visible_sidebar_menu_meta_v1(
    *,
    sidebar_menu_settings: list[dict[str, Any]],
    visible_sidebar_menu_keys: set[str],
) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    menu_meta_by_key: dict[str, dict[str, str]] = {}
    menu_key_by_label_lookup: dict[str, str] = {}

    for raw_setting in sidebar_menu_settings:
        if not isinstance(raw_setting, dict):
            continue

        menu_key = _normalize_process_list_source_key_v1(raw_setting.get("key"))
        if not menu_key:
            continue

        if visible_sidebar_menu_keys and menu_key not in visible_sidebar_menu_keys:
            continue

        if not bool(raw_setting.get("is_active")) or bool(raw_setting.get("is_deleted")):
            continue

        menu_label = str(raw_setting.get("label") or menu_key).strip() or menu_key
        menu_meta_by_key[menu_key] = {
            "key": menu_key,
            "label": menu_label,
        }
        menu_label_lookup = _normalize_process_rule_lookup_text(menu_label)
        if menu_label_lookup and menu_label_lookup not in menu_key_by_label_lookup:
            menu_key_by_label_lookup[menu_label_lookup] = menu_key

    return menu_meta_by_key, menu_key_by_label_lookup


def _resolve_auth_profile_menu_key_v1(
    *,
    values: dict[str, Any],
    menu_meta_by_key: dict[str, dict[str, str]],
    menu_key_by_label_lookup: dict[str, str],
) -> str:
    explicit_candidates = (
        values.get("__menu_key"),
        values.get("custom_perfil"),
        values.get("custom_nome_do_perfil"),
    )

    for raw_candidate in explicit_candidates:
        clean_menu_key = _normalize_process_list_source_key_v1(raw_candidate)
        if clean_menu_key and clean_menu_key in menu_meta_by_key:
            return clean_menu_key

    for label_key in ("custom_nome_do_perfil", "custom_perfil"):
        clean_label = str(values.get(label_key) or "").strip()
        if not clean_label:
            continue

        resolved_menu_key = menu_key_by_label_lookup.get(
            _normalize_process_rule_lookup_text(clean_label)
        )
        if resolved_menu_key:
            return resolved_menu_key

    return ""


_PROFILE_MENU_TABS_ALL_OPTION_V1 = {
    "value": "Todas as autorizações",
    "label": "Todas as autorizações",
    "status": "active",
}


def _prepend_profile_menu_tabs_all_option_v1(
    options: list[dict[str, str]] | None,
) -> list[dict[str, str]]:
    if not options:
        return []

    resolved_options: list[dict[str, str]] = [dict(_PROFILE_MENU_TABS_ALL_OPTION_V1)]
    seen_lookups: set[str] = {
        _normalize_process_rule_lookup_text(_PROFILE_MENU_TABS_ALL_OPTION_V1["value"])
    }

    for raw_option in options or []:
        if not isinstance(raw_option, dict):
            continue

        clean_value = str(raw_option.get("value") or "").strip()
        clean_label = str(raw_option.get("label") or clean_value).strip()
        if not clean_value and not clean_label:
            continue

        option_lookup = _normalize_process_rule_lookup_text(clean_value or clean_label)
        if option_lookup in seen_lookups:
            continue
        seen_lookups.add(option_lookup)

        resolved_options.append(
            {
                "value": clean_value or clean_label,
                "label": clean_label or clean_value,
                "status": str(raw_option.get("status") or "active").strip() or "active",
            }
        )

    return resolved_options


def _normalize_manual_list_options_v1(raw_options: Any) -> list[dict[str, str]]:
    if not isinstance(raw_options, (list, tuple)):
        return []

    from appgenesis.services.process_tabs import _normalize_render_options_v1

    normalized_options = _normalize_render_options_v1(list(raw_options))
    if not normalized_options:
        return []

    return [
        {
            **option,
            "status": str(option.get("status") or "active").strip() or "active",
        }
        for option in normalized_options
    ]


def _resolve_profile_menu_tabs_options_v1(
    *,
    menu_key: str,
    sidebar_menu_settings: list[dict[str, Any]],
    visible_sidebar_menu_keys: set[str],
) -> list[dict[str, str]]:
    from appgenesis.services.process_tabs import resolve_process_tab_options_v1

    return _prepend_profile_menu_tabs_all_option_v1(
        resolve_process_tab_options_v1(
            menu_key,
            sidebar_menu_settings,
            visible_sidebar_menu_keys=visible_sidebar_menu_keys,
        )
    )


def _build_auth_profile_menu_entries_v1(
    *,
    sidebar_menu_settings: list[dict[str, Any]],
    visible_sidebar_menu_keys: set[str],
    menu_process_history_map: dict[str, list[dict[str, Any]]] | None,
) -> list[dict[str, str]]:
    history_rows = (
        menu_process_history_map.get("perfil_de_autorizacao")
        if isinstance(menu_process_history_map, dict)
        else []
    )
    if not isinstance(history_rows, list) or not history_rows:
        return []

    menu_meta_by_key, menu_key_by_label_lookup = _build_visible_sidebar_menu_meta_v1(
        sidebar_menu_settings=sidebar_menu_settings,
        visible_sidebar_menu_keys=visible_sidebar_menu_keys,
    )
    if not menu_meta_by_key and visible_sidebar_menu_keys:
        return []

    resolved_entries: list[dict[str, str]] = []
    seen_labels: set[str] = set()
    section_candidates = _build_automatic_source_section_candidates_v1("custom_perfil")

    for raw_row in history_rows:
        if not isinstance(raw_row, dict):
            continue

        row_section_key = _normalize_process_list_source_key_v1(raw_row.get("section_key"))
        if section_candidates and row_section_key not in section_candidates:
            continue

        values = raw_row.get("values")
        if not isinstance(values, dict):
            continue

        profile_label = (
            str(values.get("custom_nome_do_perfil") or "").strip()
            or str(values.get("custom_perfil") or "").strip()
        )
        if not profile_label:
            continue

        profile_lookup = _normalize_process_rule_lookup_text(profile_label)
        if not profile_lookup or profile_lookup in seen_labels:
            continue

        seen_labels.add(profile_lookup)
        resolved_entries.append(
            {
                "profile_label": profile_label,
                "menu_key": _resolve_auth_profile_menu_key_v1(
                    values=values,
                    menu_meta_by_key=menu_meta_by_key,
                    menu_key_by_label_lookup=menu_key_by_label_lookup,
                ),
            }
        )

    return resolved_entries


def _build_profile_menu_tabs_controller_key_candidates_v1(
    *,
    current_menu_key: str,
    field_definition: dict[str, Any],
) -> list[str]:
    candidates: list[str] = []

    def append_candidate(raw_candidate: Any) -> None:
        clean_candidate = _normalize_process_list_source_key_v1(raw_candidate)
        if clean_candidate and clean_candidate not in candidates:
            candidates.append(clean_candidate)

    if (
        _normalize_process_list_source_key_v1(current_menu_key) == "perfil_de_autorizacao"
        and _normalize_process_list_source_key_v1(field_definition.get("header_key"))
        == "custom_objeto_de_autorizacao"
    ):
        append_candidate("custom_processo")

    for raw_candidate in (
        field_definition.get("profile_source_field_key"),
        field_definition.get("profileSourceFieldKey"),
        field_definition.get("automatic_source_field_key"),
        field_definition.get("automaticSourceFieldKey"),
        "custom_nome_do_perfil",
        "custom_perfil",
    ):
        append_candidate(raw_candidate)

    return candidates


def _resolve_profile_menu_tabs_controller_value_v1(
    *,
    current_menu_key: str,
    field_definition: dict[str, Any],
    current_field_values: dict[str, Any] | None,
) -> str:
    if not isinstance(current_field_values, dict):
        return ""

    normalized_values = {
        _normalize_process_list_source_key_v1(raw_key): str(raw_value or "").strip()
        for raw_key, raw_value in current_field_values.items()
        if _normalize_process_list_source_key_v1(raw_key)
    }
    controller_key_candidates = _build_profile_menu_tabs_controller_key_candidates_v1(
        current_menu_key=current_menu_key,
        field_definition=field_definition,
    )

    for clean_candidate in controller_key_candidates:
        resolved_value = normalized_values.get(clean_candidate, "")
        if resolved_value:
            return resolved_value

    return ""


def build_profile_menu_tabs_dependency_map_v1(
    *,
    sidebar_menu_settings: list[dict[str, Any]] | None,
    visible_sidebar_menu_keys: set[str] | list[str] | tuple[str, ...] | None = None,
    menu_process_history_map: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, list[dict[str, str]]]:
    def register_dependency_aliases(
        options_map: dict[str, list[dict[str, str]]],
        aliases: list[str] | tuple[str, ...],
        options: list[dict[str, str]],
    ) -> None:
        for raw_alias in aliases:
            clean_alias = str(raw_alias or "").strip()
            if clean_alias and clean_alias not in options_map:
                options_map[clean_alias] = options

    settings = [
        dict(item)
        for item in (sidebar_menu_settings or [])
        if isinstance(item, dict)
    ]
    visible_keys = _normalize_visible_sidebar_menu_keys_for_list_resolver_v1(
        visible_sidebar_menu_keys
    )
    dependency_map: dict[str, list[dict[str, str]]] = {}

    if not settings:
        return dependency_map

    profile_entries = _build_auth_profile_menu_entries_v1(
        sidebar_menu_settings=settings,
        visible_sidebar_menu_keys=visible_keys,
        menu_process_history_map=menu_process_history_map,
    )
    if not profile_entries:
        profile_entries = []

    menu_meta_by_key, _menu_key_by_label_lookup = _build_visible_sidebar_menu_meta_v1(
        sidebar_menu_settings=settings,
        visible_sidebar_menu_keys=visible_keys,
    )
    resolved_options_by_menu_key: dict[str, list[dict[str, str]]] = {}

    for entry in profile_entries:
        profile_label = str(entry.get("profile_label") or "").strip()
        menu_key = _normalize_process_list_source_key_v1(entry.get("menu_key"))
        if not profile_label:
            continue

        if menu_key not in resolved_options_by_menu_key:
            resolved_options_by_menu_key[menu_key] = (
                _resolve_profile_menu_tabs_options_v1(
                    menu_key=menu_key,
                    sidebar_menu_settings=settings,
                    visible_sidebar_menu_keys=visible_keys,
                )
                if menu_key
                else []
            )
        menu_label = str((menu_meta_by_key.get(menu_key) or {}).get("label") or "").strip()
        register_dependency_aliases(
            dependency_map,
            [profile_label, menu_key, menu_label],
            resolved_options_by_menu_key.get(menu_key, []),
        )

    for menu_key, menu_meta in menu_meta_by_key.items():
        if menu_key not in resolved_options_by_menu_key:
            resolved_options_by_menu_key[menu_key] = _resolve_profile_menu_tabs_options_v1(
                menu_key=menu_key,
                sidebar_menu_settings=settings,
                visible_sidebar_menu_keys=visible_keys,
            )
        register_dependency_aliases(
            dependency_map,
            [menu_key, menu_meta.get("label")],
            resolved_options_by_menu_key.get(menu_key, []),
        )

    return dependency_map


def _resolve_profile_menu_tabs_list_options_v1(
    *,
    current_menu_key: str,
    field_definition: dict[str, Any],
    sidebar_menu_settings: list[dict[str, Any]],
    visible_sidebar_menu_keys: set[str],
    menu_process_history_map: dict[str, list[dict[str, Any]]] | None,
    current_field_values: dict[str, Any] | None,
) -> list[dict[str, str]]:
    controller_value = _resolve_profile_menu_tabs_controller_value_v1(
        current_menu_key=current_menu_key,
        field_definition=field_definition,
        current_field_values=current_field_values,
    )
    if not controller_value:
        return []

    controller_lookup = _normalize_process_rule_lookup_text(controller_value)
    if not controller_lookup:
        return []

    profile_entries = _build_auth_profile_menu_entries_v1(
        sidebar_menu_settings=sidebar_menu_settings,
        visible_sidebar_menu_keys=visible_sidebar_menu_keys,
        menu_process_history_map=menu_process_history_map,
    )
    menu_key = next(
        (
            _normalize_process_list_source_key_v1(entry.get("menu_key"))
            for entry in profile_entries
            if _normalize_process_rule_lookup_text(entry.get("profile_label")) == controller_lookup
        ),
        "",
    )

    if not menu_key:
        menu_meta_by_key, menu_key_by_label_lookup = _build_visible_sidebar_menu_meta_v1(
            sidebar_menu_settings=sidebar_menu_settings,
            visible_sidebar_menu_keys=visible_sidebar_menu_keys,
        )
        direct_menu_key = _normalize_process_list_source_key_v1(controller_value)
        if direct_menu_key in menu_meta_by_key:
            menu_key = direct_menu_key
        else:
            menu_key = menu_key_by_label_lookup.get(controller_lookup, "")

    if not menu_key:
        return []

    return _resolve_profile_menu_tabs_options_v1(
        menu_key=menu_key,
        sidebar_menu_settings=sidebar_menu_settings,
        visible_sidebar_menu_keys=visible_sidebar_menu_keys,
    )


def _resolve_automatic_process_list_options_from_history_v1(
    *,
    current_menu_key: str,
    field_definition: dict[str, Any],
    process_list: dict[str, Any],
    settings_by_key: dict[str, dict[str, Any]],
    menu_process_history_map: dict[str, list[dict[str, Any]]] | None,
) -> list[dict[str, str]]:
    source_menu_key = _normalize_process_list_source_key_v1(
        process_list.get("source_menu_key") or process_list.get("sourceMenuKey")
    )
    if not source_menu_key:
        # Listas automáticas normalizadas com "all_sessions" podem ficar sem menu de origem
        # explícito. Nesse caso, a própria lista continua a pertencer ao menu atual.
        source_menu_key = _normalize_process_list_source_key_v1(current_menu_key)
    if not source_menu_key:
        return []

    source_setting = settings_by_key.get(source_menu_key)
    if not isinstance(source_setting, dict):
        return []

    source_section_key = _normalize_process_list_source_key_v1(
        process_list.get("source_subprocess_key") or process_list.get("sourceSubprocessKey")
    )
    only_active = (
        str(
            process_list.get("automatic_only_active")
            or process_list.get("automaticOnlyActive")
            or field_definition.get("automatic_only_active")
            or field_definition.get("automaticOnlyActive")
            or ""
        )
        .strip()
        .lower()
        in {"1", "true", "sim", "yes", "on"}
    )
    source_field_key = _normalize_process_list_source_key_v1(field_definition.get("key"))
    if not source_field_key:
        return []

    source_field_candidates = _build_automatic_source_field_candidates_v1(
        source_setting=source_setting,
        source_section_key=source_section_key,
        source_field_key=source_field_key,
    )
    if not source_field_candidates:
        return []

    history_rows = (
        menu_process_history_map.get(source_menu_key)
        if isinstance(menu_process_history_map, dict)
        else []
    )
    if not isinstance(history_rows, list):
        return []

    status_field_key = _normalize_process_list_source_key_v1(
        source_setting.get("process_record_status_field_key") or "__estado"
    ) or "__estado"
    section_candidates = (
        _build_automatic_source_section_candidates_v1(
            source_section_key,
            source_setting=source_setting,
        )
        if source_section_key
        else []
    )

    def collect_options(*, enforce_section_match: bool) -> list[dict[str, str]]:
        resolved_options: list[dict[str, str]] = []
        seen_lookup: set[str] = set()

        for raw_row in history_rows:
            if not isinstance(raw_row, dict):
                continue

            row_section_key = _normalize_process_list_source_key_v1(raw_row.get("section_key"))
            if enforce_section_match and section_candidates and row_section_key not in section_candidates:
                continue

            values = raw_row.get("values")
            if not isinstance(values, dict):
                continue

            raw_option_value = ""
            for candidate_field_key in source_field_candidates:
                raw_option_value = str(values.get(candidate_field_key) or "").strip()
                if raw_option_value:
                    break
            if not raw_option_value:
                continue

            option_lookup = _normalize_process_rule_lookup_text(raw_option_value)
            if not option_lookup or option_lookup in seen_lookup:
                continue

            seen_lookup.add(option_lookup)
            option_status = _normalize_process_record_state_v1(
                values.get(status_field_key, values.get("__estado"))
            )
            if only_active and option_status != "active":
                continue
            resolved_options.append(
                {
                    "value": raw_option_value,
                    "label": raw_option_value,
                    "status": option_status,
                }
            )

        return resolved_options

    resolved_options = collect_options(enforce_section_match=True)
    if resolved_options:
        return resolved_options

    return []


def resolve_field_list_options_v1(
    *,
    active_entity_id: int | None = None,
    current_menu_key: str,
    field_definition: dict[str, Any] | None,
    sidebar_menu_settings: list[dict[str, Any]] | None,
    visible_sidebar_menu_keys: set[str] | list[str] | tuple[str, ...] | None = None,
    menu_process_history_map: dict[str, list[dict[str, Any]]] | None = None,
    current_field_values: dict[str, Any] | None = None,
    _visited: frozenset[tuple[str, str]] | None = None,
) -> list[dict[str, str]]:
    if not isinstance(field_definition, dict):
        return []

    field_type = _normalize_process_list_source_key_v1(
        field_definition.get("field_type") or field_definition.get("type")
    )
    if field_type != "list":
        return []

    settings = [
        dict(item)
        for item in (sidebar_menu_settings or [])
        if isinstance(item, dict)
    ]
    settings_by_key = {
        clean_key: item
        for item in settings
        for clean_key in [_normalize_process_list_source_key_v1(item.get("key"))]
        if clean_key
    }
    clean_current_menu_key = _normalize_process_list_source_key_v1(current_menu_key)
    current_field_key = _normalize_process_list_source_key_v1(field_definition.get("key"))
    _safe_visited = _visited or frozenset()
    _visit_key = (clean_current_menu_key, current_field_key)
    if current_field_key and _visit_key in _safe_visited:
        return []

    current_setting = settings_by_key.get(clean_current_menu_key, {})
    list_source_type = normalize_process_list_source_type_v1(
        field_definition.get("list_source_type")
        or field_definition.get("listSourceType")
        or ("automatic" if (
            field_definition.get("automatic_source_process_key")
            or field_definition.get("automaticSourceProcessKey")
            or field_definition.get("automatic_source_field_key")
            or field_definition.get("automaticSourceFieldKey")
        ) else "manual")
    )
    if _is_legacy_profile_menu_tabs_config_v1(
        current_menu_key=clean_current_menu_key,
        field_definition=field_definition,
        list_source_type=list_source_type,
    ):
        list_source_type = "profile_menu_tabs"
    visible_keys = _normalize_visible_sidebar_menu_keys_for_list_resolver_v1(
        visible_sidebar_menu_keys
    )

    if list_source_type == "active_menus":
        return _resolve_active_sidebar_menu_list_options_v1(
            sidebar_menu_settings=settings,
            visible_sidebar_menu_keys=visible_keys,
        )

    if list_source_type == "profile_menu_tabs":
        return _resolve_profile_menu_tabs_list_options_v1(
            current_menu_key=clean_current_menu_key,
            field_definition=field_definition,
            sidebar_menu_settings=settings,
            visible_sidebar_menu_keys=visible_keys,
            menu_process_history_map=menu_process_history_map,
            current_field_values=current_field_values,
        )

    if list_source_type == "manual":
        inline_options_raw = (
            field_definition.get("manual_list_options")
            or field_definition.get("manualListOptions")
        )
        if inline_options_raw is not None:
            resolved_inline_options = _normalize_manual_list_options_v1(inline_options_raw)
            if resolved_inline_options:
                return resolved_inline_options

        inline_items_raw = (
            field_definition.get("manual_list_items")
            or field_definition.get("manualListItems")
        )
        if inline_items_raw is None:
            inline_csv = str(
                field_definition.get("manual_list_items_csv")
                or field_definition.get("manualListItemsCsv")
                or ""
            ).strip()
            if inline_csv:
                inline_items_raw = [v.strip() for v in inline_csv.split(",") if v.strip()]
        if isinstance(inline_items_raw, (list, tuple)) and inline_items_raw:
            clean_inline = [str(v).strip() for v in inline_items_raw if str(v).strip()]
            if clean_inline:
                return [
                    {"value": v, "label": v, "status": "active"}
                    for v in clean_inline
                ]

        manual_list_key = _normalize_process_list_source_key_v1(
            field_definition.get("manual_list_key")
            or field_definition.get("manualListKey")
            or field_definition.get("list_key")
            or field_definition.get("listKey")
        )
        if not manual_list_key:
            return []

        for process_list in current_setting.get("process_lists") or []:
            if not isinstance(process_list, dict):
                continue
            process_list_key = _normalize_process_list_source_key_v1(
                process_list.get("key")
            )
            if process_list_key != manual_list_key:
                continue
            resolved_manual_options = [
                {
                    "value": clean_value,
                    "label": clean_value,
                    "status": "active",
                }
                for clean_value in [
                    str(raw_item or "").strip()
                    for raw_item in (process_list.get("items") or [])
                ]
                if clean_value
            ]
            if resolved_manual_options:
                return resolved_manual_options
            if str(process_list.get("field_type") or "").strip().lower() == "automatic":
                process_list_source_session_key = _normalize_process_list_source_key_v1(
                    process_list.get("source_session_key")
                    or process_list.get("sourceSidebarSectionKey")
                )
                process_list_source_menu_key = _normalize_process_list_source_key_v1(
                    process_list.get("source_menu_key") or process_list.get("sourceMenuKey")
                )
                process_list_source_subprocess_key = _normalize_process_list_source_key_v1(
                    process_list.get("source_subprocess_key")
                    or process_list.get("sourceSubprocessKey")
                )
                if (
                    process_list_source_session_key == "all_sessions"
                    and not process_list_source_menu_key
                    and not process_list_source_subprocess_key
                ):
                    return _resolve_active_sidebar_menu_list_options_v1(
                        sidebar_menu_settings=settings,
                        visible_sidebar_menu_keys=visible_keys,
                    )
                return _resolve_automatic_process_list_options_from_history_v1(
                    current_menu_key=current_menu_key,
                    field_definition=field_definition,
                    process_list=process_list,
                    settings_by_key=settings_by_key,
                    menu_process_history_map=menu_process_history_map,
                )
            return []
        return []

    if list_source_type == "field_list":
        fl_process_key = _normalize_process_list_source_key_v1(
            field_definition.get("automatic_source_process_key")
            or field_definition.get("automaticSourceProcessKey")
        )
        fl_field_key = _normalize_process_list_source_key_v1(
            field_definition.get("automatic_source_field_key")
            or field_definition.get("automaticSourceFieldKey")
        )
        if not fl_process_key or not fl_field_key:
            return []
        if visible_keys and fl_process_key not in visible_keys:
            return []
        fl_source_setting = settings_by_key.get(fl_process_key)
        if not isinstance(fl_source_setting, dict):
            return []
        fl_source_field_def: dict[str, Any] | None = None
        for _coll in ("process_field_options", "process_additional_fields"):
            for _raw in (fl_source_setting.get(_coll) or []):
                if not isinstance(_raw, dict):
                    continue
                if _normalize_process_list_source_key_v1(_raw.get("key")) != fl_field_key:
                    continue
                _ft = _normalize_process_list_source_key_v1(
                    _raw.get("field_type") or _raw.get("type")
                )
                if _ft != "list":
                    return []
                fl_source_field_def = dict(_raw)
                break
            if fl_source_field_def is not None:
                break
        if fl_source_field_def is None:
            return []
        return resolve_field_list_options_v1(
            current_menu_key=fl_process_key,
            field_definition=fl_source_field_def,
            sidebar_menu_settings=sidebar_menu_settings,
            visible_sidebar_menu_keys=visible_sidebar_menu_keys,
            menu_process_history_map=menu_process_history_map,
            current_field_values=current_field_values,
            _visited=_safe_visited | {_visit_key},
        )

    source_process_key = _normalize_process_list_source_key_v1(
        field_definition.get("automatic_source_process_key")
        or field_definition.get("automaticSourceProcessKey")
    )
    source_section_key = _normalize_process_list_source_key_v1(
        field_definition.get("automatic_source_section_key")
        or field_definition.get("automaticSourceSectionKey")
    )
    source_field_key = _normalize_process_list_source_key_v1(
        field_definition.get("automatic_source_field_key")
        or field_definition.get("automaticSourceFieldKey")
    )
    only_active = str(
        field_definition.get("automatic_only_active")
        or field_definition.get("automaticOnlyActive")
        or ""
    ).strip().lower() in {"1", "true", "sim", "yes", "on"}

    if not source_process_key or not source_section_key or not source_field_key:
        return []
    if visible_keys and source_process_key not in visible_keys:
        return []

    source_setting = settings_by_key.get(source_process_key)
    if not isinstance(source_setting, dict):
        return []

    source_section_candidates = _build_automatic_source_section_candidates_v1(
        source_section_key
    )
    source_field_candidates = _build_automatic_source_field_candidates_v1(
        source_setting=source_setting,
        source_section_key=source_section_key,
        source_field_key=source_field_key,
    )
    if not source_field_candidates:
        return []

    history_rows = (
        menu_process_history_map.get(source_process_key)
        if isinstance(menu_process_history_map, dict)
        else []
    )
    if not isinstance(history_rows, list):
        return []

    status_field_key = _normalize_process_list_source_key_v1(
        source_setting.get("process_record_status_field_key") or "__estado"
    ) or "__estado"
    resolved_options: list[dict[str, str]] = []
    seen_lookup: set[str] = set()

    for raw_row in history_rows:
        if not isinstance(raw_row, dict):
            continue

        row_section_key = _normalize_process_list_source_key_v1(
            raw_row.get("section_key")
        )
        if source_section_candidates and row_section_key not in source_section_candidates:
            continue

        values = raw_row.get("values")
        if not isinstance(values, dict):
            continue

        raw_option_value = ""
        for candidate_field_key in source_field_candidates:
            raw_option_value = str(values.get(candidate_field_key) or "").strip()
            if raw_option_value:
                break
        if not raw_option_value:
            continue

        option_status = _normalize_process_record_state_v1(
            values.get(status_field_key, values.get("__estado"))
        )
        if only_active and option_status != "active":
            continue

        option_lookup = _normalize_process_rule_lookup_text(raw_option_value)
        if not option_lookup or option_lookup in seen_lookup:
            continue

        seen_lookup.add(option_lookup)
        resolved_options.append(
            {
                "value": raw_option_value,
                "label": raw_option_value,
                "status": option_status,
            }
        )

    return resolved_options


def parse_profile_custom_fields(raw_value: Any) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for clean_key, clean_field_value in parse_member_profile_fields(raw_value).items():
        if not clean_key.startswith("custom_"):
            continue
        normalized[clean_key] = clean_field_value
    return normalized

def serialize_profile_custom_fields(values: dict[str, str]) -> str | None:
    custom_only: dict[str, str] = {}
    for raw_key, raw_value in (values or {}).items():
        clean_key = str(raw_key or "").strip().lower()
        if not clean_key.startswith("custom_"):
            continue
        if not clean_key:
            continue
        clean_value = _normalize_profile_field_value(raw_value)
        if not clean_value:
            continue
        custom_only[clean_key] = clean_value
    return serialize_member_profile_fields(custom_only)

def format_whatsapp_status(status_value: str | None) -> str:
    status_lookup = {
        "unknown": "Não verificado",
        "pending": "Verificação pendente",
        "active": "Ativo no WhatsApp",
        "invalid": "Número sem WhatsApp",
        "failed": "Falha na verificação",
    }
    normalized = (status_value or "unknown").strip().lower()
    return status_lookup.get(normalized, "Não verificado")

def format_optional_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def format_optional_date_pt(value: date | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%d/%m/%Y")

def parse_optional_date_pt(raw_value: str) -> date | None:
    clean_value = (raw_value or "").strip()
    if not clean_value:
        return None
    return datetime.strptime(clean_value, "%d/%m/%Y").date()

def get_user_personal_data(
    session: Session,
    user_id: int,
    selected_entity_id: int | None = None,
) -> dict[str, Any]:
    row = session.execute(
        select(
            Member.full_name,
            User.login_email,
            Member.primary_phone,
            Member.country,
            Member.birth_date,
            Member.address,
            Member.city,
            Member.freguesia,
            Member.postal_code,
            Member.whatsapp_verification_status,
            Member.whatsapp_notice_opt_in,
            Member.whatsapp_last_check_at,
            Member.whatsapp_last_error,
            Member.training_discipulado_verbo_vida,
            Member.training_ebvv,
            Member.training_rhema,
            Member.training_escola_ministerial,
            Member.training_escola_missoes,
            Member.training_outros,
            Member.profile_custom_fields,
            Member.member_status,
            User.account_status,
            Member.is_collaborator,
        )
       .join(User, User.member_id == Member.id)
       .where(User.id == user_id)
    ).one_or_none()

    if row is None:
        return {
            "full_name": "-",
            "login_email": "-",
            "primary_phone": "-",
            "country": "-",
            "birth_date": "-",
            "address": "-",
            "city": "-",
            "freguesia": "-",
            "postal_code": "-",
            "whatsapp_verification_status": format_whatsapp_status("unknown"),
            "whatsapp_notice_opt_in": "Não autorizado",
            "whatsapp_notice_opt_in_raw": False,
            "whatsapp_last_check_at": "-",
            "whatsapp_last_error": "-",
            "training_discipulado_verbo_vida": False,
            "training_ebvv": False,
            "training_rhema": False,
            "training_escola_ministerial": False,
            "training_escola_missoes": False,
            "training_outros": "",
            "training_selected": [],
            "member_status": "-",
            "account_status": "-",
            "is_collaborator": "-",
            "custom_fields": {},
            "entities": "-",
            "primary_entity_name": "-",
            "primary_entity_address": "-",
            "primary_entity_phone": "-",
            "primary_entity_logo_url": "",
        }

    entity_rows = session.execute(
        select(Entity.id, Entity.name, Entity.address, Entity.phone, Entity.logo_url)
       .join(MemberEntity, MemberEntity.entity_id == Entity.id)
       .join(User, User.member_id == MemberEntity.member_id)
       .where(
            User.id == user_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            Entity.is_active.is_(True),
        )
       .order_by(MemberEntity.id.asc())
    ).all()
    entities = ", ".join(row_entity.name for row_entity in entity_rows) if entity_rows else "-"

    primary_entity_data: dict[str, str] | None = None
    if selected_entity_id is not None:
        for linked_entity in entity_rows:
            if int(linked_entity.id) == selected_entity_id:
                primary_entity_data = {
                    "name": linked_entity.name or "",
                    "address": linked_entity.address or "",
                    "phone": linked_entity.phone or "",
                    "logo_url": linked_entity.logo_url or "",
                }
                break

    if primary_entity_data is None and selected_entity_id is not None:
        selected_entity_row = session.execute(
            select(Entity.name, Entity.address, Entity.phone, Entity.logo_url)
           .where(Entity.id == selected_entity_id, Entity.is_active.is_(True))
           .limit(1)
        ).one_or_none()
        if selected_entity_row is not None:
            primary_entity_data = {
                "name": selected_entity_row.name or "",
                "address": selected_entity_row.address or "",
                "phone": selected_entity_row.phone or "",
                "logo_url": selected_entity_row.logo_url or "",
            }

    if primary_entity_data is None and entity_rows:
        first_linked_entity = entity_rows[0]
        primary_entity_data = {
            "name": first_linked_entity.name or "",
            "address": first_linked_entity.address or "",
            "phone": first_linked_entity.phone or "",
            "logo_url": first_linked_entity.logo_url or "",
        }

    if entities == "-" and primary_entity_data is not None:
        entities = primary_entity_data.get("name") or "-"
    training_selected: list[str] = []
    if row.training_discipulado_verbo_vida:
        training_selected.append("DISCIPULADO VERBO DA VIDA")
    if row.training_ebvv:
        training_selected.append("EBVV")
    if row.training_rhema:
        training_selected.append("RHEMA")
    if row.training_escola_ministerial:
        training_selected.append("ESCOLA MINISTERIAL")
    if row.training_escola_missoes:
        training_selected.append("ESCOLA DE MISSÕES")
    clean_training_outros = (row.training_outros or "").strip()
    if clean_training_outros:
        training_selected.append(f"OUTROS: {clean_training_outros}")
    custom_fields = parse_profile_custom_fields(row.profile_custom_fields)

    return {
        "full_name": row.full_name or "-",
        "login_email": row.login_email or "-",
        "primary_phone": row.primary_phone or "-",
        "country": row.country or "-",
        "birth_date": format_optional_date_pt(row.birth_date),
        "address": row.address or "-",
        "city": row.city or "-",
        "freguesia": row.freguesia or "-",
        "postal_code": row.postal_code or "-",
        "whatsapp_verification_status": format_whatsapp_status(row.whatsapp_verification_status),
        "whatsapp_notice_opt_in": "Autorizado" if row.whatsapp_notice_opt_in else "Não autorizado",
        "whatsapp_notice_opt_in_raw": bool(row.whatsapp_notice_opt_in),
        "whatsapp_last_check_at": format_optional_datetime(row.whatsapp_last_check_at),
        "whatsapp_last_error": row.whatsapp_last_error or "-",
        "training_discipulado_verbo_vida": bool(row.training_discipulado_verbo_vida),
        "training_ebvv": bool(row.training_ebvv),
        "training_rhema": bool(row.training_rhema),
        "training_escola_ministerial": bool(row.training_escola_ministerial),
        "training_escola_missoes": bool(row.training_escola_missoes),
        "training_outros": clean_training_outros,
        "training_selected": training_selected,
        "member_status": row.member_status or "-",
        "account_status": row.account_status or "-",
        "is_collaborator": "Sim" if row.is_collaborator else "Não",
        "custom_fields": custom_fields,
        "entities": entities,
        "primary_entity_name": (
            primary_entity_data["name"] if primary_entity_data and primary_entity_data.get("name") else "-"
        ),
        "primary_entity_address": (
            primary_entity_data["address"] if primary_entity_data and primary_entity_data.get("address") else "-"
        ),
        "primary_entity_phone": (
            primary_entity_data["phone"] if primary_entity_data and primary_entity_data.get("phone") else "-"
        ),
        "primary_entity_logo_url": (
            primary_entity_data["logo_url"] if primary_entity_data and primary_entity_data.get("logo_url") else ""
        ),
    }

__all__ = [
    "normalize_process_subsequent_operator",
    "normalize_process_subsequent_rules",
    "is_process_subsequent_rule_met",
    "get_hidden_process_targets_from_rules",
    "filter_process_fields_by_hidden_targets",
    "is_meu_perfil_builtin_duplicate_field",
    "parse_member_profile_fields",
    "serialize_member_profile_fields",
    "merge_member_profile_fields_v1",
    "build_menu_process_field_storage_key",
    "build_menu_process_records_storage_key",
    "build_menu_process_quantity_storage_key",
    "get_menu_process_quantity_repeated_field_keys",
    "parse_menu_process_quantity_values",
    "serialize_menu_process_quantity_values",
    "parse_menu_process_records",
    "serialize_menu_process_records",
    "normalize_process_list_source_type_v1",
    "build_profile_menu_tabs_dependency_map_v1",
    "resolve_field_list_options_v1",
    "parse_profile_custom_fields",
    "serialize_profile_custom_fields",
    "format_whatsapp_status",
    "format_optional_datetime",
    "format_optional_date_pt",
    "parse_optional_date_pt",
    "get_user_personal_data",
]
