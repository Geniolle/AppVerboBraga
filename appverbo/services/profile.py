from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import date, datetime, timezone
from typing import Any

from appverbo.core import *  # noqa: F403,F401
from appverbo.menu_settings import get_sidebar_menu_settings

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
        trigger_field = str(raw_rule.get("trigger_field") or "").strip().lower()
        target_field = str(raw_rule.get("field_key") or raw_rule.get("subsequent_field") or "").strip().lower()
        operator = normalize_process_subsequent_operator(
            raw_rule.get("operator") or raw_rule.get("condition")
        )
        trigger_value = str(raw_rule.get("trigger_value") or "").strip()
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

    normalized: dict[str, str] = {}
    for raw_key, raw_field_value in parsed.items():
        clean_key = str(raw_key or "").strip().lower()
        if not clean_key:
            continue
        clean_field_value = _normalize_profile_field_value(raw_field_value)
        if not clean_field_value:
            continue
        normalized[clean_key] = clean_field_value
    return normalized

def serialize_member_profile_fields(values: dict[str, str]) -> str | None:
    normalized: dict[str, str] = {}
    for raw_key, raw_value in (values or {}).items():
        clean_key = str(raw_key or "").strip().lower()
        if not clean_key:
            continue
        clean_value = _normalize_profile_field_value(raw_value)
        if not clean_value:
            continue
        normalized[clean_key] = clean_value
    if not normalized:
        return None
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True)

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
    "build_menu_process_field_storage_key",
    "build_menu_process_records_storage_key",
    "build_menu_process_quantity_storage_key",
    "get_menu_process_quantity_repeated_field_keys",
    "parse_menu_process_quantity_values",
    "serialize_menu_process_quantity_values",
    "parse_menu_process_records",
    "serialize_menu_process_records",
    "parse_profile_custom_fields",
    "serialize_profile_custom_fields",
    "format_whatsapp_status",
    "format_optional_datetime",
    "format_optional_date_pt",
    "parse_optional_date_pt",
    "get_user_personal_data",
]
