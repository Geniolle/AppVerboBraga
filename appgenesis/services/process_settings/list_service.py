from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appgenesis.models.sidebar_menu_setting import SidebarMenuSetting

from appgenesis.services.process_settings.normalizers import (
    _build_menu_key_from_label,
    _normalize_sentence_case_text,
)


def _normalize_process_list_key_v1(raw_key: Any) -> str:
    clean_key = str(raw_key or "").strip().lower()
    clean_key = re.sub(r"[^a-z0-9_]+", "_", clean_key)
    clean_key = re.sub(r"_+", "_", clean_key).strip("_")

    if not clean_key:
        return ""

    if not clean_key.startswith("list_"):
        clean_key = f"list_{clean_key}"

    return clean_key


def _build_process_list_key_from_label_v1(label: str) -> str:
    base_key = _build_menu_key_from_label(label)

    if not base_key:
        base_key = "lista"

    return _normalize_process_list_key_v1(base_key)


def _normalize_process_list_items_csv_v1(raw_items: Any) -> list[str]:
    if isinstance(raw_items, str):
        raw_values = raw_items.split(",")
    elif isinstance(raw_items, (list, tuple, set)):
        raw_values = []
        for item in raw_items:
            if isinstance(item, str) and "," in item:
                raw_values.extend(item.split(","))
            else:
                raw_values.append(item)
    else:
        raw_values = []

    normalized: list[str] = []
    seen: set[str] = set()

    for raw_value in raw_values:
        clean_value = " ".join(str(raw_value or "").strip().split())

        if not clean_value:
            continue

        lookup_key = clean_value.lower()

        if lookup_key in seen:
            continue

        seen.add(lookup_key)
        normalized.append(clean_value)

    return normalized


def normalize_menu_process_lists_v1(raw_lists: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_lists, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    seen_labels: set[str] = set()

    for raw_item in raw_lists:
        if not isinstance(raw_item, dict):
            continue

        label = _normalize_sentence_case_text(
            raw_item.get("label", raw_item.get("name"))
        )

        if not label:
            continue

        label_lookup = label.lower()

        if label_lookup in seen_labels:
            continue

        seen_labels.add(label_lookup)

        list_key = _normalize_process_list_key_v1(
            raw_item.get("key")
        ) or _build_process_list_key_from_label_v1(label)

        base_key = list_key
        suffix = 2

        while list_key in seen_keys:
            list_key = f"{base_key}_{suffix}"
            suffix += 1

        seen_keys.add(list_key)

        items = _normalize_process_list_items_csv_v1(
            raw_item.get("items_csv", raw_item.get("items"))
        )

        normalized.append(
            {
                "key": list_key,
                "label": label,
                "items": items,
                "items_csv": ", ".join(items),
            }
        )

    return normalized


def get_menu_process_lists_v1(
    menu_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(menu_config, dict):
        return []

    return normalize_menu_process_lists_v1(menu_config.get("process_lists"))


def _normalize_process_list_key_v2(raw_key: Any) -> str:
    clean_key = str(raw_key or "").strip().lower()
    clean_key = re.sub(r"[^a-z0-9_]+", "_", clean_key)
    clean_key = re.sub(r"_+", "_", clean_key).strip("_")

    if not clean_key:
        return ""

    if not clean_key.startswith("list_"):
        clean_key = f"list_{clean_key}"

    return clean_key


def _build_process_list_key_from_label_v2(label: str) -> str:
    base_key = _build_menu_key_from_label(label)

    if not base_key:
        base_key = "lista"

    return _normalize_process_list_key_v2(base_key)


def _normalize_process_list_items_csv_v2(raw_items: Any) -> list[str]:
    if isinstance(raw_items, str):
        raw_values = raw_items.split(",")
    elif isinstance(raw_items, (list, tuple, set)):
        raw_values = []
        for item in raw_items:
            if isinstance(item, str) and "," in item:
                raw_values.extend(item.split(","))
            else:
                raw_values.append(item)
    else:
        raw_values = []

    normalized: list[str] = []
    seen: set[str] = set()

    for raw_value in raw_values:
        clean_value = " ".join(str(raw_value or "").strip().split())

        if not clean_value:
            continue

        lookup_key = clean_value.lower()

        if lookup_key in seen:
            continue

        seen.add(lookup_key)
        normalized.append(clean_value)

    return normalized


def normalize_menu_process_lists_v2(raw_lists: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_lists, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    seen_labels: set[str] = set()

    for raw_item in raw_lists:
        if not isinstance(raw_item, dict):
            continue

        label = _normalize_sentence_case_text(
            raw_item.get("label", raw_item.get("name"))
        )

        if not label:
            continue

        label_lookup = label.lower()

        if label_lookup in seen_labels:
            continue

        seen_labels.add(label_lookup)

        list_key = _normalize_process_list_key_v2(
            raw_item.get("key")
        ) or _build_process_list_key_from_label_v2(label)

        base_key = list_key
        suffix = 2

        while list_key in seen_keys:
            list_key = f"{base_key}_{suffix}"
            suffix += 1

        seen_keys.add(list_key)

        items = _normalize_process_list_items_csv_v2(
            raw_item.get("items_csv", raw_item.get("items"))
        )

        normalized.append(
            {
                "key": list_key,
                "label": label,
                "items": items,
                "items_csv": ", ".join(items),
            }
        )

    return normalized


def get_menu_process_lists_v2(
    menu_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(menu_config, dict):
        return []

    return normalize_menu_process_lists_v2(menu_config.get("process_lists"))


def _normalize_process_list_key_v3(raw_key: Any) -> str:
    clean_key = str(raw_key or "").strip().lower()
    clean_key = re.sub(r"[^a-z0-9_]+", "_", clean_key)
    clean_key = re.sub(r"_+", "_", clean_key).strip("_")

    if not clean_key:
        return ""

    if not clean_key.startswith("list_"):
        clean_key = f"list_{clean_key}"

    return clean_key


def normalize_menu_process_lists_v3(raw_lists: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_lists, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for raw_item in raw_lists:
        if not isinstance(raw_item, dict):
            continue

        label = _normalize_sentence_case_text(
            raw_item.get("label", raw_item.get("name"))
        )

        if not label:
            continue

        list_key = _normalize_process_list_key_v3(raw_item.get("key"))

        if not list_key:
            list_key = _normalize_process_list_key_v3(_build_menu_key_from_label(label))

        if not list_key:
            list_key = "list_lista"

        base_key = list_key
        suffix = 2

        while list_key in seen_keys:
            list_key = f"{base_key}_{suffix}"
            suffix += 1

        seen_keys.add(list_key)

        # determine field type (manual | automatic). Default to manual for
        # backward compatibility when missing or invalid.
        raw_field_type = str(raw_item.get("field_type") or "").strip().lower()
        field_type = "automatic" if raw_field_type == "automatic" else "manual"

        raw_items = raw_item.get("items_csv", raw_item.get("items"))
        items: list[str] = []

        if field_type == "manual":
            if isinstance(raw_items, str):
                raw_values = raw_items.split(",")
            elif isinstance(raw_items, (list, tuple, set)):
                raw_values = raw_items
            else:
                raw_values = []

            seen_items: set[str] = set()
            for raw_value in raw_values:
                clean_value = " ".join(str(raw_value or "").strip().split())

                if not clean_value:
                    continue

                lookup = clean_value.lower()

                if lookup in seen_items:
                    continue

                seen_items.add(lookup)
                items.append(clean_value)

        # for automatic lists we keep items empty (no invented source)

        normalized.append(
            {
                "key": list_key,
                "label": label,
                "field_type": field_type,
                "items": items,
                "items_csv": ", ".join(items),
            }
        )

    return normalized


# ###################################################################################
# (4) ORIGEM DE MENU PARA LISTAS AUTOMÁTICAS
# ###################################################################################


def get_process_list_source_menus_v1(
    session: Session,
    active_entity_id: int | None,
) -> list[dict[str, str]]:
    if active_entity_id is None:
        return []

    rows = session.execute(
        select(SidebarMenuSetting.menu_key, SidebarMenuSetting.menu_label)
        .where(
            SidebarMenuSetting.entity_id == int(active_entity_id),
            SidebarMenuSetting.is_deleted.is_(False),
            SidebarMenuSetting.is_active.is_(True),
        )
        .order_by(SidebarMenuSetting.menu_label, SidebarMenuSetting.menu_key)
    ).all()

    return [
        {
            "menu_key": str(row.menu_key or "").strip().lower(),
            "menu_label": str(row.menu_label or row.menu_key or "").strip(),
        }
        for row in rows
        if str(row.menu_key or "").strip()
    ]


def normalize_menu_process_lists_v4(raw_lists: Any) -> list[dict[str, Any]]:
    normalized = normalize_menu_process_lists_v3(raw_lists)
    raw_by_key: dict[str, dict[str, Any]] = {}

    for raw_item in raw_lists if isinstance(raw_lists, (list, tuple, set)) else []:
        if not isinstance(raw_item, dict):
            continue
        raw_key = _normalize_process_list_key_v3(raw_item.get("key"))
        if raw_key:
            raw_by_key[raw_key] = raw_item

    for item in normalized:
        raw_item = raw_by_key.get(str(item.get("key") or ""), {})
        field_type = str(item.get("field_type") or "manual").strip().lower()
        source_menu_key = str(raw_item.get("source_menu_key") or "").strip().lower()
        item["source_menu_key"] = source_menu_key if field_type == "automatic" else ""

        if field_type == "automatic":
            item["items"] = []
            item["items_csv"] = ""

    return normalized
