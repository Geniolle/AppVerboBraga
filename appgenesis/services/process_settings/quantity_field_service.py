from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from appgenesis.services.process_settings.menu_config_repository import (
    load_menu_config,
    save_menu_config,
)
from appgenesis.services.process_settings.normalizers import (
    SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS,
    _menu_exists,
    _normalize_custom_field_key,
    _normalize_menu_key,
    _normalize_sentence_case_text,
    _resolve_legacy_menu_alias,
    _resolve_sidebar_menu_settings_entity_id,
    ensure_sidebar_menu_settings_defaults,
)
from appgenesis.services.process_settings.additional_field_service import (
    normalize_menu_process_additional_fields,
)


def _build_process_quantity_rule_key_v1(rule_label: str, fallback_index: int) -> str:
    clean_key = _normalize_menu_key(rule_label)
    if clean_key:
        return f"qty_{clean_key}"
    return f"qty_regra_{fallback_index + 1}"


def _normalize_process_quantity_max_items_v1(raw_value: Any) -> int:
    try:
        parsed_value = int(str(raw_value or "").strip())
    except (TypeError, ValueError):
        return 1
    return max(1, min(parsed_value, 50))


def _normalize_process_quantity_interaction_mode_v1(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value in {"quantity", "dynamic_list"}:
        return clean_value
    return "quantity"


def normalize_menu_process_quantity_fields(raw_fields: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_fields, (list, tuple, set)):
        return []

    normalized_fields: list[dict[str, Any]] = []
    seen_rule_keys: set[str] = set()

    for row_index, raw_item in enumerate(raw_fields):
        if not isinstance(raw_item, dict):
            continue

        rule_label = _normalize_sentence_case_text(
            raw_item.get("label") or raw_item.get("rule_label") or raw_item.get("name")
        )
        quantity_field_key = _normalize_custom_field_key(
            raw_item.get("quantity_field_key")
            or raw_item.get("quantityFieldKey")
            or raw_item.get("field_key")
        )
        raw_repeated_field_keys = (
            raw_item.get("repeated_field_keys")
            or raw_item.get("repeatedFieldKeys")
            or raw_item.get("field_keys")
            or []
        )
        if isinstance(raw_repeated_field_keys, str):
            try:
                parsed_repeated_field_keys = json.loads(raw_repeated_field_keys)
            except (TypeError, ValueError, json.JSONDecodeError):
                parsed_repeated_field_keys = [
                    chunk
                    for chunk in re.split(r"[,;\n\r]+", raw_repeated_field_keys)
                    if str(chunk or "").strip()
                ]
        else:
            parsed_repeated_field_keys = raw_repeated_field_keys

        repeated_field_keys: list[str] = []
        seen_repeated_field_keys: set[str] = set()
        if isinstance(parsed_repeated_field_keys, (list, tuple, set)):
            for raw_field_key in parsed_repeated_field_keys:
                clean_field_key = _normalize_custom_field_key(raw_field_key)
                if not clean_field_key or clean_field_key in seen_repeated_field_keys:
                    continue
                seen_repeated_field_keys.add(clean_field_key)
                repeated_field_keys.append(clean_field_key)

        header_key = _normalize_custom_field_key(
            raw_item.get("header_key") or raw_item.get("headerKey")
        )
        max_items = _normalize_process_quantity_max_items_v1(
            raw_item.get("max_items") or raw_item.get("maxItems")
        )
        interaction_mode = _normalize_process_quantity_interaction_mode_v1(
            raw_item.get("interaction_mode")
            or raw_item.get("interactionMode")
        )
        item_label = (
            _normalize_sentence_case_text(
                raw_item.get("item_label") or raw_item.get("itemLabel") or "Item"
            )
            or "Item"
        )

        rule_key = _normalize_menu_key(
            raw_item.get("key") or raw_item.get("rule_key") or raw_item.get("ruleKey")
        )
        if not rule_key:
            rule_key = _build_process_quantity_rule_key_v1(
                rule_label or item_label, row_index
            )

        if (
            not rule_label
            or not quantity_field_key
            or not repeated_field_keys
            or rule_key in seen_rule_keys
        ):
            continue

        seen_rule_keys.add(rule_key)
        normalized_fields.append(
            {
                "key": rule_key,
                "label": rule_label,
                "quantity_field_key": quantity_field_key,
                "repeated_field_keys": repeated_field_keys,
                "header_key": header_key,
                "max_items": max_items,
                "item_label": item_label,
                **(
                    {"interaction_mode": interaction_mode}
                    if interaction_mode != "quantity"
                    else {}
                ),
            }
        )

    return normalized_fields


def update_sidebar_menu_process_quantity_fields_v1(
    session: Session,
    menu_key: str,
    raw_fields: Any,
    entity_id: int | None = None,
) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    resolved_entity_id = entity_id
    if resolved_entity_id is None:
        resolved_entity_id = _resolve_sidebar_menu_settings_entity_id(session)

    if not clean_menu_key:
        return False, "Menu inválido."

    if clean_menu_key in SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS:
        return False, "Este processo não permite Campos Quantidade."

    ensure_sidebar_menu_settings_defaults(session)

    if not _menu_exists(session, clean_menu_key):
        return False, "Menu não encontrado."

    menu_config = load_menu_config(session, resolved_entity_id, clean_menu_key)
    additional_fields = normalize_menu_process_additional_fields(
        menu_config.get("additional_fields")
    )
    additional_fields_by_key = {
        str(field.get("key") or "").strip().lower(): field
        for field in additional_fields
        if str(field.get("key") or "").strip()
    }
    header_keys = {
        field_key
        for field_key, field in additional_fields_by_key.items()
        if str(field.get("field_type") or "").strip().lower() == "header"
    }

    normalized_fields = normalize_menu_process_quantity_fields(raw_fields)
    validated_fields: list[dict[str, Any]] = []
    seen_rule_keys: set[str] = set()

    for row_index, item in enumerate(normalized_fields):
        rule_key = str(item.get("key") or "").strip().lower()
        rule_label = str(item.get("label") or "").strip()
        quantity_field_key = str(item.get("quantity_field_key") or "").strip().lower()
        repeated_field_keys = [
            str(raw_field_key or "").strip().lower()
            for raw_field_key in (item.get("repeated_field_keys") or [])
            if str(raw_field_key or "").strip()
        ]
        header_key = str(item.get("header_key") or "").strip().lower()
        item_label = str(item.get("item_label") or "").strip() or "Item"
        max_items = _normalize_process_quantity_max_items_v1(item.get("max_items"))
        interaction_mode = _normalize_process_quantity_interaction_mode_v1(
            item.get("interaction_mode")
        )

        if not rule_label:
            return False, f"Informe o nome da regra na linha {row_index + 1}."

        if not rule_key:
            return False, f"Regra inválida na linha {row_index + 1}."

        if rule_key in seen_rule_keys:
            return False, f"Já existe uma regra com a chave '{rule_key}'."
        seen_rule_keys.add(rule_key)

        quantity_field_meta = additional_fields_by_key.get(quantity_field_key)
        if quantity_field_meta is None:
            return (
                False,
                f"O campo origem da regra '{rule_label}' deve existir em Campos adicionais.",
            )
        if str(quantity_field_meta.get("field_type") or "").strip().lower() != "number":
            return False, f"O campo origem da regra '{rule_label}' deve ser numérico."

        if not repeated_field_keys:
            return False, f"Selecione os campos repetidos da regra '{rule_label}'."

        validated_repeated_field_keys: list[str] = []
        seen_repeated_field_keys: set[str] = set()
        for repeated_field_key in repeated_field_keys:
            repeated_field_meta = additional_fields_by_key.get(repeated_field_key)
            if repeated_field_meta is None:
                return (
                    False,
                    f"Os campos repetidos da regra '{rule_label}' devem existir em Campos adicionais.",
                )
            repeated_field_type = (
                str(repeated_field_meta.get("field_type") or "").strip().lower()
            )
            if repeated_field_type == "header":
                return False, f"A regra '{rule_label}' não pode repetir cabeçalhos."
            if repeated_field_key == quantity_field_key:
                return (
                    False,
                    f"A regra '{rule_label}' não pode repetir o próprio campo de quantidade.",
                )
            if repeated_field_key in seen_repeated_field_keys:
                continue
            seen_repeated_field_keys.add(repeated_field_key)
            validated_repeated_field_keys.append(repeated_field_key)

        if header_key and header_key not in header_keys:
            return (
                False,
                f"O cabeçalho da regra '{rule_label}' deve existir em Campos adicionais.",
            )

        validated_fields.append(
            {
                "key": rule_key,
                "label": rule_label,
                "quantity_field_key": quantity_field_key,
                "repeated_field_keys": validated_repeated_field_keys,
                "header_key": header_key,
                "max_items": max_items,
                "item_label": item_label,
                **(
                    {"interaction_mode": interaction_mode}
                    if interaction_mode != "quantity"
                    else {}
                ),
            }
        )

    menu_config["process_quantity_fields"] = validated_fields

    return save_menu_config(session, resolved_entity_id, clean_menu_key, menu_config)
