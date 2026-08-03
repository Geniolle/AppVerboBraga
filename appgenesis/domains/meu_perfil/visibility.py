from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appgenesis.models import Member, User
from appgenesis.services.profile import get_hidden_process_targets_from_rules


def _normalize_subsequent_key_v2(raw_value: Any) -> str:
    return str(raw_value or "").strip().lower()


def _normalize_subsequent_lookup_v2(raw_value: Any) -> str:
    return str(raw_value or "").strip().lower()


def _collect_meu_perfil_subsequent_rules_v2(sidebar_item: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(sidebar_item, dict):
        return []

    collected_rules: list[dict[str, Any]] = []

    for storage_key in (
        "process_subsequent_fields",
        "subsequent_fields",
        "process_subsequent_rules",
    ):
        raw_rules = sidebar_item.get(storage_key)

        if not isinstance(raw_rules, list):
            continue

        for raw_rule in raw_rules:
            if isinstance(raw_rule, dict):
                collected_rules.append(raw_rule)

    return collected_rules


def _get_subsequent_rule_trigger_field_v2(rule: dict[str, Any]) -> str:
    return _normalize_subsequent_key_v2(
        rule.get("trigger_field")
        or rule.get("trigger_field_key")
        or rule.get("subsequent_trigger_field")
        or rule.get("triggerField")
        or rule.get("triggerFieldKey")
    )


def _get_subsequent_rule_target_field_v2(rule: dict[str, Any]) -> str:
    return _normalize_subsequent_key_v2(
        rule.get("field_key")
        or rule.get("subsequent_field")
        or rule.get("subsequent_field_key")
        or rule.get("fieldKey")
        or rule.get("target_field")
        or rule.get("targetFieldKey")
    )


def _get_subsequent_rule_operator_v2(rule: dict[str, Any]) -> str:
    return _normalize_subsequent_key_v2(
        rule.get("operator")
        or rule.get("condition")
        or rule.get("subsequent_operator")
        or "equals"
    )


def _get_subsequent_rule_trigger_value_v2(rule: dict[str, Any]) -> str:
    operator = _get_subsequent_rule_operator_v2(rule)

    if operator in {"is_empty", "is_not_empty"}:
        return ""

    return str(
        rule.get("trigger_value")
        or rule.get("subsequent_trigger_value")
        or rule.get("triggerValue")
        or ""
    ).strip()


def _is_subsequent_rule_met_v2(rule: dict[str, Any], values_by_field: dict[str, str]) -> bool:
    trigger_field = _get_subsequent_rule_trigger_field_v2(rule)
    operator = _get_subsequent_rule_operator_v2(rule)
    trigger_value = _get_subsequent_rule_trigger_value_v2(rule)

    current_value = str(values_by_field.get(trigger_field) or "").strip()

    if operator == "is_empty":
        return current_value == ""

    if operator == "is_not_empty":
        return current_value != ""

    normalized_current = _normalize_subsequent_lookup_v2(current_value)
    normalized_trigger = _normalize_subsequent_lookup_v2(trigger_value)

    if operator == "not_equals":
        return normalized_current != normalized_trigger

    return normalized_current == normalized_trigger


def _target_has_specific_rule_v2(target_field: str, rules: list[dict[str, Any]]) -> bool:
    clean_target_field = _normalize_subsequent_key_v2(target_field)

    return any(
        _get_subsequent_rule_target_field_v2(rule) == clean_target_field
        for rule in rules
    )


def _target_has_specific_rule_met_v2(
    target_field: str,
    rules: list[dict[str, Any]],
    values_by_field: dict[str, str],
) -> bool:
    clean_target_field = _normalize_subsequent_key_v2(target_field)

    return any(
        _get_subsequent_rule_target_field_v2(rule) == clean_target_field
        and _is_subsequent_rule_met_v2(rule, values_by_field)
        for rule in rules
    )


def _format_profile_visibility_date_v2(raw_value: Any) -> str:
    if raw_value is None:
        return ""

    if hasattr(raw_value, "strftime"):
        return raw_value.strftime("%d/%m/%Y")

    return str(raw_value or "").strip()


def _build_meu_perfil_visibility_values_v2(
    session: Session,
    actor_user_id: int | None,
    actor_profile_fields: dict[str, str],
) -> dict[str, str]:
    values_by_field: dict[str, str] = dict(actor_profile_fields or {})

    if actor_user_id is None:
        return values_by_field

    row = session.execute(
        select(
            Member.full_name,
            Member.primary_phone,
            Member.email,
            Member.country,
            Member.birth_date,
            User.login_email,
        )
        .join(User, User.member_id == Member.id)
        .where(User.id == actor_user_id)
        .limit(1)
    ).one_or_none()

    if row is None:
        return values_by_field

    values_by_field["nome"] = str(row.full_name or "").strip()
    values_by_field["telefone"] = str(row.primary_phone or "").strip()
    values_by_field["email"] = str(row.login_email or row.email or "").strip().lower()
    values_by_field["pais"] = str(row.country or "").strip()
    values_by_field["data_nascimento"] = _format_profile_visibility_date_v2(row.birth_date)

    return values_by_field


def _filter_meu_perfil_fields_by_subsequent_rules_v2(
    visible_fields: list[str],
    hidden_targets: set[str],
    field_header_map: dict[str, str],
    rules: list[dict[str, Any]],
    values_by_field: dict[str, str],
) -> list[str]:
    clean_hidden_targets = {
        _normalize_subsequent_key_v2(hidden_target)
        for hidden_target in hidden_targets
        if _normalize_subsequent_key_v2(hidden_target)
    }

    filtered_fields: list[str] = []

    for raw_field_key in visible_fields:
        field_key = _normalize_subsequent_key_v2(raw_field_key)

        if not field_key:
            continue

        header_key = _normalize_subsequent_key_v2(field_header_map.get(field_key))

        field_has_specific_rule = _target_has_specific_rule_v2(field_key, rules)
        field_has_specific_rule_met = _target_has_specific_rule_met_v2(
            field_key,
            rules,
            values_by_field,
        )

        if field_has_specific_rule and not field_has_specific_rule_met:
            continue

        if field_key in clean_hidden_targets and not field_has_specific_rule_met:
            continue

        if header_key in clean_hidden_targets and not field_has_specific_rule_met:
            continue

        filtered_fields.append(field_key)

    return filtered_fields


def apply_meu_perfil_subsequent_visibility_v2(
    session: Session,
    actor_user_id: int | None,
    sidebar_item: dict[str, Any] | None,
    actor_profile_fields: dict[str, str],
    visible_fields: list[str],
    field_header_map: dict[str, str],
) -> list[str]:
    if not visible_fields:
        return []

    rules = _collect_meu_perfil_subsequent_rules_v2(sidebar_item)

    if not rules:
        return visible_fields

    values_by_field = _build_meu_perfil_visibility_values_v2(
        session,
        actor_user_id,
        actor_profile_fields,
    )

    hidden_targets = get_hidden_process_targets_from_rules(
        rules,
        values_by_field,
    )

    return _filter_meu_perfil_fields_by_subsequent_rules_v2(
        visible_fields=visible_fields,
        hidden_targets=set(hidden_targets or set()),
        field_header_map=field_header_map,
        rules=rules,
        values_by_field=values_by_field,
    )
