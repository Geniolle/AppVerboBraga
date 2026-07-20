from __future__ import annotations

from typing import Any

from appgenesis.services.process_settings.normalizers import _resolve_legacy_menu_alias
from appgenesis.services.process_settings.quantity_field_service import (
    normalize_menu_process_quantity_fields,
)


def _normalize_process_section_lookup_v1(raw_value: Any) -> str:
    return str(raw_value or "").strip().lower()


def _build_process_sections_field_map_v1(
    *,
    menu_key: str,
    menu_config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    fields_by_key: dict[str, dict[str, Any]] = {}
    raw_field_collections = [
        menu_config.get("process_additional_fields"),
        menu_config.get("additional_fields"),
        menu_config.get("process_field_options"),
    ]
    for raw_fields in raw_field_collections:
        if not isinstance(raw_fields, list):
            continue
        for raw_field in raw_fields:
            if not isinstance(raw_field, dict):
                continue
            field_key = _normalize_process_section_lookup_v1(raw_field.get("key"))
            if not field_key:
                continue
            existing_field = fields_by_key.get(field_key, {})
            merged_field = dict(existing_field)
            merged_field.update(raw_field)
            fields_by_key[field_key] = merged_field

    return fields_by_key


def _build_section_entry_v1(
    *,
    section_key: str,
    section_label: str,
) -> dict[str, Any]:
    clean_section_key = _normalize_process_section_lookup_v1(section_key)
    clean_section_label = str(section_label or "").strip()
    return {
        "key": clean_section_key,
        "label": clean_section_label or clean_section_key,
        "field_keys": [],
        "quantity_rule_keys": [],
    }


def resolve_process_sections_v1(setting: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(setting, dict):
        return []

    clean_menu_key = _resolve_legacy_menu_alias(setting.get("key"))
    menu_config = setting if isinstance(setting, dict) else {}
    fields_by_key = _build_process_sections_field_map_v1(
        menu_key=clean_menu_key,
        menu_config=menu_config,
    )
    header_labels = {
        field_key: str(field.get("label") or "").strip()
        for field_key, field in fields_by_key.items()
        if _normalize_process_section_lookup_v1(field.get("field_type")) == "header"
    }

    sections_by_key: dict[str, dict[str, Any]] = {}
    section_order: list[str] = []
    seen_field_keys: set[str] = set()

    def ensure_section(section_key: str, section_label: str) -> dict[str, Any]:
        clean_section_key = _normalize_process_section_lookup_v1(section_key)
        if not clean_section_key:
            return _build_section_entry_v1(section_key="__geral__", section_label="Geral")
        section = sections_by_key.get(clean_section_key)
        if section is None:
            section = _build_section_entry_v1(
                section_key=clean_section_key,
                section_label=section_label,
            )
            sections_by_key[clean_section_key] = section
            section_order.append(clean_section_key)
        elif section_label and not str(section.get("label") or "").strip():
            section["label"] = section_label
        return section

    raw_visible_rows = setting.get("process_visible_field_rows")
    if isinstance(raw_visible_rows, list):
        for raw_row in raw_visible_rows:
            if not isinstance(raw_row, dict):
                continue
            field_key = _normalize_process_section_lookup_v1(raw_row.get("field_key"))
            if not field_key or field_key in seen_field_keys:
                continue
            field_meta = fields_by_key.get(field_key)
            header_key = _normalize_process_section_lookup_v1(raw_row.get("header_key"))
            section_key = header_key or "__geral__"
            field_type = _normalize_process_section_lookup_v1(
                field_meta.get("field_type") if field_meta else ""
            )
            if field_type == "header":
                continue
            fallback_field_label = str(raw_row.get("field_label") or "").strip() or field_key
            section_label = header_labels.get(section_key) or (
                "Geral"
                if section_key == "__geral__"
                else str((field_meta or {}).get("label") or fallback_field_label or section_key)
            )
            section = ensure_section(section_key, section_label)
            section["field_keys"].append(field_key)
            seen_field_keys.add(field_key)

    normalized_quantity_rules = normalize_menu_process_quantity_fields(
        setting.get("process_quantity_fields")
    )
    for quantity_rule in normalized_quantity_rules:
        if not isinstance(quantity_rule, dict):
            continue
        rule_key = _normalize_process_section_lookup_v1(quantity_rule.get("key"))
        header_key = _normalize_process_section_lookup_v1(quantity_rule.get("header_key"))
        if not rule_key or not header_key:
            continue

        header_meta = fields_by_key.get(header_key)
        if not header_meta:
            continue
        if _normalize_process_section_lookup_v1(header_meta.get("field_type")) != "header":
            continue

        quantity_field_key = _normalize_process_section_lookup_v1(
            quantity_rule.get("quantity_field_key")
        )
        quantity_field_meta = fields_by_key.get(quantity_field_key)
        if not quantity_field_meta:
            continue
        if _normalize_process_section_lookup_v1(quantity_field_meta.get("field_type")) != "number":
            continue

        repeated_field_keys: list[str] = []
        seen_repeated: set[str] = set()
        for raw_repeated_field_key in quantity_rule.get("repeated_field_keys") or []:
            clean_repeated_field_key = _normalize_process_section_lookup_v1(
                raw_repeated_field_key
            )
            if not clean_repeated_field_key or clean_repeated_field_key in seen_repeated:
                continue
            repeated_field_meta = fields_by_key.get(clean_repeated_field_key)
            if not repeated_field_meta:
                continue
            if _normalize_process_section_lookup_v1(repeated_field_meta.get("field_type")) == "header":
                continue
            seen_repeated.add(clean_repeated_field_key)
            repeated_field_keys.append(clean_repeated_field_key)

        if not repeated_field_keys:
            continue

        section_label = str(header_meta.get("label") or header_key).strip() or header_key
        section = ensure_section(header_key, section_label)
        if rule_key not in section["quantity_rule_keys"]:
            section["quantity_rule_keys"].append(rule_key)

    resolved_sections = [
        sections_by_key[section_key]
        for section_key in section_order
        if section_key in sections_by_key
        and (sections_by_key[section_key]["field_keys"] or sections_by_key[section_key]["quantity_rule_keys"])
    ]
    return resolved_sections


def resolve_process_section_fields_v1(
    setting: dict[str, Any] | None,
    section_key: str,
) -> list[dict[str, Any]]:
    if not isinstance(setting, dict):
        return []

    clean_section_key = _normalize_process_section_lookup_v1(section_key)
    if not clean_section_key:
        return []

    sections = resolve_process_sections_v1(setting)
    section = next(
        (
            row
            for row in sections
            if _normalize_process_section_lookup_v1(row.get("key")) == clean_section_key
        ),
        None,
    )
    if section is None:
        return []

    field_meta_map = _build_process_sections_field_map_v1(
        menu_key=_resolve_legacy_menu_alias(setting.get("key")),
        menu_config=setting,
    )
    result: list[dict[str, Any]] = []
    for raw_field_key in section.get("field_keys") or []:
        clean_field_key = _normalize_process_section_lookup_v1(raw_field_key)
        if not clean_field_key:
            continue
        field_meta = field_meta_map.get(clean_field_key)
        if not field_meta:
            result.append(
                {
                    "key": clean_field_key,
                    "label": clean_field_key,
                    "header_key": clean_section_key,
                    "header_label": clean_section_key,
                    "field_type": "text",
                    "input_type": "text",
                    "required": False,
                    "size": None,
                    "list_source_type": "manual",
                    "manual_list_key": "",
                    "list_key": "",
                    "automatic_source_process_key": "",
                    "automatic_source_section_key": "",
                    "automatic_source_field_key": "",
                    "automatic_only_active": False,
                    "manual_list_items": [],
                    "manual_list_options": [],
                    "manual_list_items_csv": "",
                    "options": [],
                }
            )
            continue
        if _normalize_process_section_lookup_v1(field_meta.get("field_type")) == "header":
            continue
        result.append(dict(field_meta))

    return result
