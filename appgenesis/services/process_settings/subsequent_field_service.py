from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from appgenesis.services.process_settings.normalizers import (
    SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS,
    _menu_exists,
    _normalize_menu_key,
    _resolve_legacy_menu_alias,
)


def _normalize_subsequent_field_operator_v3(raw_operator: Any) -> str:
    clean_operator = str(raw_operator or "").strip().lower()
    clean_operator = clean_operator.replace("-", "_")
    clean_operator = clean_operator.replace(" ", "_")

    operator_aliases = {
        "": "is_empty",
        "vazio": "is_empty",
        "empty": "is_empty",
        "blank": "is_empty",
        "is_empty": "is_empty",
        "esta_vazio": "is_empty",
        "preenchido": "is_not_empty",
        "not_empty": "is_not_empty",
        "filled": "is_not_empty",
        "is_filled": "is_not_empty",
        "is_not_empty": "is_not_empty",
        "esta_preenchido": "is_not_empty",
        "igual": "equals",
        "igual_a": "equals",
        "equals": "equals",
        "equal": "equals",
        "eq": "equals",
        "diferente": "not_equals",
        "diferente_de": "not_equals",
        "not_equal": "not_equals",
        "not_equals": "not_equals",
        "neq": "not_equals",
    }

    return operator_aliases.get(clean_operator, "is_empty")


def _build_subsequent_field_key_v3(
    trigger_field_key: str,
    subsequent_field_key: str,
    operator: str,
    trigger_value: str,
) -> str:
    base_key = "_".join(
        [
            str(trigger_field_key or "").strip().lower(),
            str(subsequent_field_key or "").strip().lower(),
            str(operator or "").strip().lower(),
            str(trigger_value or "").strip().lower(),
        ]
    )
    base_key = re.sub(r"[^a-z0-9_]+", "_", base_key)
    base_key = re.sub(r"_+", "_", base_key).strip("_")

    if not base_key:
        return ""

    return f"subseq_{base_key}"


def normalize_menu_process_subsequent_fields(raw_fields: Any) -> list[dict[str, str]]:
    if not isinstance(raw_fields, (list, tuple)):
        return []

    allowed_operators = {
        "is_empty",
        "is_not_empty",
        "equals",
        "not_equals",
    }

    normalized_fields: list[dict[str, str]] = []
    seen_fields: set[tuple[str, str, str, str]] = set()

    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            continue

        trigger_field_key = _normalize_menu_key(
            raw_field.get("trigger_field")
            or raw_field.get("trigger_field_key")
            or raw_field.get("triggerField")
            or raw_field.get("triggerFieldKey")
            or raw_field.get("campo_acionador")
            or raw_field.get("campoAcionador")
        )

        subsequent_field_key = _normalize_menu_key(
            raw_field.get("field_key")
            or raw_field.get("subsequent_field")
            or raw_field.get("subsequent_field_key")
            or raw_field.get("subsequentField")
            or raw_field.get("subsequentFieldKey")
            or raw_field.get("target_field_key")
            or raw_field.get("targetFieldKey")
            or raw_field.get("campo_subsequente")
            or raw_field.get("campoSubsequente")
        )

        operator = _normalize_subsequent_field_operator_v3(
            raw_field.get("operator")
            or raw_field.get("condition")
            or raw_field.get("condicao")
            or raw_field.get("condição")
        )

        trigger_value = str(
            raw_field.get("trigger_value")
            or raw_field.get("triggerValue")
            or raw_field.get("value")
            or raw_field.get("valor_acionador")
            or raw_field.get("valorAcionador")
            or ""
        ).strip()

        if operator not in allowed_operators:
            operator = "is_empty"

        if operator in {"is_empty", "is_not_empty"}:
            trigger_value = ""

        if operator in {"equals", "not_equals"} and not trigger_value:
            operator = "is_empty"
            trigger_value = ""

        if not trigger_field_key or not subsequent_field_key:
            continue

        clean_key = _normalize_menu_key(
            raw_field.get("key")
            or raw_field.get("subsequent_field_key")
            or raw_field.get("id")
        )

        if not clean_key:
            clean_key = _build_subsequent_field_key_v3(
                trigger_field_key,
                subsequent_field_key,
                operator,
                trigger_value,
            )

        field_signature = (
            trigger_field_key,
            subsequent_field_key,
            operator,
            trigger_value,
        )

        if field_signature in seen_fields:
            continue

        seen_fields.add(field_signature)

        normalized_fields.append(
            {
                "key": clean_key,
                "trigger_field": trigger_field_key,
                "trigger_field_key": trigger_field_key,
                "field_key": subsequent_field_key,
                "subsequent_field": subsequent_field_key,
                "subsequent_field_key": subsequent_field_key,
                "operator": operator,
                "condition": operator,
                "trigger_value": trigger_value,
            }
        )

    return normalized_fields


def update_sidebar_menu_subsequent_fields(
    session: Session,
    menu_key: str,
    raw_fields: Any,
) -> tuple[bool, str]:
    """Atualiza os campos subsequentes de um menu."""
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if not clean_menu_key:
        return False, "Menu inválido."

    if clean_menu_key in SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS:
        return False, "Este processo não permite campos subsequentes."

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

    normalized_fields = normalize_menu_process_subsequent_fields(raw_fields)
    menu_config["subsequent_fields"] = normalized_fields

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
