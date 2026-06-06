from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import urlencode
import unicodedata

from appverbo.core import *  # noqa: F403,F401
from appverbo.menu_settings import (
    MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
    MENU_MEU_PERFIL_FIELD_LABELS,
    MENU_MEU_PERFIL_FIELD_OPTIONS,
    MENU_MEU_PERFIL_FIELDS_DEFAULT,
    MENU_MEU_PERFIL_KEY,
    normalize_sidebar_sections,
    resolve_menu_key_alias,
)
from appverbo.services.entity_admin_context import (
    build_entity_admin_context_v1,
    build_entity_admin_page_payload_v1,
)
from appverbo.services.process_view_authorization import (
    PROCESS_VIEW_AUTHORIZATION_MENU_KEY,
    PROCESS_VIEW_AUTHORIZATION_SECTION_KEY,
    build_effective_sidebar_visibility_v1,
    build_process_view_authorization_history_rows_v1,
)
from appverbo.services.users.context import (
    build_user_admin_list_context_v1,
    build_user_admin_page_payload_v1,
)
from appverbo.services.profile import (
    build_menu_process_records_storage_key,
    build_menu_process_field_storage_key,
    build_menu_process_quantity_storage_key,
    filter_process_fields_by_hidden_targets,
    get_hidden_process_targets_from_rules,
    get_menu_process_quantity_repeated_field_keys,
    is_meu_perfil_builtin_duplicate_field,
    resolve_meu_perfil_builtin_duplicate_field_key,
    parse_menu_process_records,
    parse_menu_process_quantity_values,
    parse_member_profile_fields,
    serialize_menu_process_quantity_values,
)
from appverbo.services.songs import (
    is_song_process_menu_v1,
    list_entity_songs_v1,
    serialize_songs_to_history_rows_v1,
)


def _normalize_process_lookup_text_v1(raw_value: Any) -> str:
    normalized = (
        unicodedata.normalize("NFKD", str(raw_value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    return " ".join(normalized.split())


def _is_single_record_process_menu_v1(menu_key: Any, menu_label: Any) -> bool:
    normalized_menu_key = _normalize_process_lookup_text_v1(menu_key).replace(" ", "_")
    joined = " ".join(
        part
        for part in (
            _normalize_process_lookup_text_v1(menu_key),
            _normalize_process_lookup_text_v1(menu_label),
        )
        if part
    )
    if not normalized_menu_key and not joined:
        return False
    return (
        normalized_menu_key in {"empresa", "meu_perfil", "perfil"}
        or "meu perfil" in joined
        or "perfil pessoal" in joined
    )


def _is_history_process_menu_v1(menu_key: Any, menu_label: Any) -> bool:
    joined = " ".join(
        part
        for part in (
            _normalize_process_lookup_text_v1(menu_key),
            _normalize_process_lookup_text_v1(menu_label),
        )
        if part
    )
    if not joined:
        return False
    if "assiduidade" in joined or "ausencia" in joined:
        return True
    if _is_single_record_process_menu_v1(menu_key, menu_label):
        return False
    return True


def _build_legacy_history_row_v1(
    *,
    visible_rows: list[dict[str, Any]],
    menu_values: dict[str, str],
    quantity_values_by_rule: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    if not menu_values and not quantity_values_by_rule:
        return []

    section_keys = {
        str((raw_row or {}).get("header_key") or "").strip()
        for raw_row in (visible_rows or [])
        if isinstance(raw_row, dict)
    }
    section_keys.discard("")
    if len(section_keys) == 1:
        section_key = next(iter(section_keys))
    else:
        section_key = ""

    row_values = dict(menu_values)
    for rule_key, items in (quantity_values_by_rule or {}).items():
        if not rule_key:
            continue
        serialized_items = serialize_menu_process_quantity_values(items)
        if serialized_items:
            row_values[f"quantity__{str(rule_key).strip().lower()}"] = serialized_items

    if not row_values:
        return []

    if "__estado" not in row_values:
        row_values["__estado"] = "ativo"

    return [
        {
            "record_id": "legacy_current",
            "created_at": "",
            "section_key": section_key,
            "values": row_values,
        }
    ]

# ###################################################################################
# (1) PROCESSO EMPRESA - CAMPOS FIXOS DA ENTIDADE LOGADA
# ###################################################################################
MENU_EMPRESA_KEY = "empresa"
MENU_EMPRESA_SECTION_KEY = "entity_dados_entidade"

MENU_EMPRESA_PROCESS_FIELD_OPTIONS_V1: tuple[dict[str, Any], ...] = (
    {
        "key": MENU_EMPRESA_SECTION_KEY,
        "label": "Dados da entidade",
        "field_type": "header",
        "is_required": False,
    },
    {
        "key": "entity_internal_number",
        "label": "Nº Cliente",
        "field_type": "text",
        "is_required": False,
        "size": 30,
    },
    {
        "key": "entity_name",
        "label": "Nome da entidade",
        "field_type": "text",
        "is_required": True,
        "size": 150,
    },
    {
        "key": "entity_acronym",
        "label": "Acrónimo (opcional)",
        "field_type": "text",
        "is_required": False,
        "size": 30,
    },
    {
        "key": "entity_tax_id",
        "label": "Nº Identificação Fiscal",
        "field_type": "text",
        "is_required": True,
        "size": 40,
    },
    {
        "key": "entity_profile_scope",
        "label": "Perfil da entidade",
        "field_type": "text",
        "is_required": True,
        "size": 20,
    },
    {
        "key": "entity_email",
        "label": "Email",
        "field_type": "email",
        "is_required": True,
        "size": 150,
    },
    {
        "key": "entity_address",
        "label": "Morada",
        "field_type": "text",
        "is_required": True,
        "size": 255,
    },
    {
        "key": "entity_door_number",
        "label": "Nº da porta",
        "field_type": "text",
        "is_required": True,
        "size": 30,
    },
    {
        "key": "entity_freguesia",
        "label": "Freguesia",
        "field_type": "text",
        "is_required": True,
        "size": 120,
    },
    {
        "key": "entity_postal_code",
        "label": "Código postal",
        "field_type": "text",
        "is_required": True,
        "size": 30,
    },
    {
        "key": "entity_city",
        "label": "Cidade",
        "field_type": "text",
        "is_required": True,
        "size": 120,
    },
    {
        "key": "entity_country",
        "label": "País",
        "field_type": "text",
        "is_required": True,
        "size": 120,
    },
    {
        "key": "entity_phone",
        "label": "Telefone",
        "field_type": "phone",
        "is_required": True,
        "size": 30,
    },
    {
        "key": "entity_responsible_name",
        "label": "Nome do responsável",
        "field_type": "text",
        "is_required": True,
        "size": 200,
    },
    {
        "key": "entity_logo_file",
        "label": "Imagem/ícone da entidade (ficheiro opcional)",
        "field_type": "text",
        "is_required": False,
        "size": 255,
    },
    {
        "key": "entity_logo_current",
        "label": "Logo atual",
        "field_type": "text",
        "is_required": False,
        "size": 255,
    },
)

MENU_EMPRESA_VISIBLE_FIELD_KEYS_V1: tuple[str, ...] = (
    "entity_internal_number",
    "entity_name",
    "entity_acronym",
    "entity_tax_id",
    "entity_profile_scope",
    "entity_email",
    "entity_address",
    "entity_door_number",
    "entity_freguesia",
    "entity_postal_code",
    "entity_city",
    "entity_country",
    "entity_phone",
    "entity_responsible_name",
    "entity_logo_file",
    "entity_logo_current",
)


def _normalize_empresa_sidebar_setting_v1(sidebar_item: dict[str, Any]) -> dict[str, Any]:
    normalized_item = dict(sidebar_item or {})
    process_field_options = [dict(option) for option in MENU_EMPRESA_PROCESS_FIELD_OPTIONS_V1]
    process_selectable_field_options = [
        dict(option)
        for option in process_field_options
        if str(option.get("field_type") or "").strip().lower() != "header"
    ]
    process_visible_fields = list(MENU_EMPRESA_VISIBLE_FIELD_KEYS_V1)
    process_visible_field_rows = [
        {"field_key": field_key, "header_key": MENU_EMPRESA_SECTION_KEY}
        for field_key in process_visible_fields
    ]
    process_visible_field_header_map = {
        field_key: MENU_EMPRESA_SECTION_KEY
        for field_key in process_visible_fields
    }

    normalized_item["process_field_options"] = process_field_options
    normalized_item["process_additional_fields"] = [dict(option) for option in process_field_options]
    normalized_item["process_selectable_field_options"] = process_selectable_field_options
    normalized_item["process_visible_fields"] = process_visible_fields
    normalized_item["process_visible_field_rows"] = process_visible_field_rows
    normalized_item["process_visible_field_header_map"] = process_visible_field_header_map
    normalized_item["process_visible_headers"] = [MENU_EMPRESA_SECTION_KEY]
    normalized_item["visible_field_headers"] = dict(process_visible_field_header_map)

    return normalized_item


def _resolve_empresa_entity_values_v1(
    session: Session,
    selected_entity_id: int | None,
    allowed_entity_ids: set[int] | None,
) -> dict[str, str]:
    def _map_profile_scope_label_v1(raw_scope: Any) -> str:
        clean_scope = str(raw_scope or "").strip().lower()
        if clean_scope == "owner":
            return "Owner"
        if clean_scope == "legado":
            return "Legado"
        return ""

    candidate_entity_ids: list[int] = []
    allowed_ids = set(allowed_entity_ids or set())

    if selected_entity_id is not None and (not allowed_ids or selected_entity_id in allowed_ids):
        candidate_entity_ids.append(int(selected_entity_id))

    if allowed_ids:
        for entity_id in sorted(allowed_ids):
            if entity_id not in candidate_entity_ids:
                candidate_entity_ids.append(entity_id)

    for entity_id in candidate_entity_ids:
        entity_row = session.execute(
            select(
                Entity.internal_number,
                Entity.name,
                Entity.acronym,
                Entity.tax_id,
                Entity.profile_scope,
                Entity.email,
                Entity.address,
                Entity.door_number,
                Entity.freguesia,
                Entity.postal_code,
                Entity.city,
                Entity.country,
                Entity.phone,
                Entity.logo_url,
                Entity.responsible_name,
            )
            .where(Entity.id == entity_id)
            .limit(1)
        ).one_or_none()
        if entity_row is None:
            continue
        return {
            "entity_internal_number": str(entity_row.internal_number or "").strip(),
            "entity_name": str(entity_row.name or "").strip(),
            "entity_acronym": str(entity_row.acronym or "").strip(),
            "entity_tax_id": str(entity_row.tax_id or "").strip(),
            "entity_profile_scope": _map_profile_scope_label_v1(entity_row.profile_scope),
            "entity_email": str(entity_row.email or "").strip(),
            "entity_address": str(entity_row.address or "").strip(),
            "entity_door_number": str(entity_row.door_number or "").strip(),
            "entity_freguesia": str(entity_row.freguesia or "").strip(),
            "entity_postal_code": str(entity_row.postal_code or "").strip(),
            "entity_city": str(entity_row.city or "").strip(),
            "entity_country": str(entity_row.country or "").strip(),
            "entity_phone": str(entity_row.phone or "").strip(),
            "entity_logo_file": "",
            "entity_logo_current": str(entity_row.logo_url or "").strip(),
            "entity_responsible_name": str(entity_row.responsible_name or "").strip(),
        }

    return {
        "entity_internal_number": "",
        "entity_name": "",
        "entity_acronym": "",
        "entity_tax_id": "",
        "entity_profile_scope": "",
        "entity_email": "",
        "entity_address": "",
        "entity_door_number": "",
        "entity_freguesia": "",
        "entity_postal_code": "",
        "entity_city": "",
        "entity_country": "",
        "entity_phone": "",
        "entity_logo_file": "",
        "entity_logo_current": "",
        "entity_responsible_name": "",
    }


# APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_PAGE_V1_START
def _format_profile_visibility_date_v1(raw_value: Any) -> str:
    if raw_value is None:
        return ""

    if hasattr(raw_value, "strftime"):
        return raw_value.strftime("%d/%m/%Y")

    return str(raw_value or "").strip()


def _collect_meu_perfil_subsequent_rules_v1(sidebar_item: dict[str, Any] | None) -> list[dict[str, Any]]:
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


def _build_meu_perfil_visibility_values_v1(
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
    values_by_field["data_nascimento"] = _format_profile_visibility_date_v1(row.birth_date)

    return values_by_field


def _apply_meu_perfil_subsequent_visibility_v2(
    session: Session,
    actor_user_id: int | None,
    sidebar_item: dict[str, Any] | None,
    actor_profile_fields: dict[str, str],
    visible_fields: list[str],
    field_header_map: dict[str, str],
) -> list[str]:
    if not visible_fields:
        return []

    rules = _collect_meu_perfil_subsequent_rules_v1(sidebar_item)

    if not rules:
        return visible_fields

    values_by_field = _build_meu_perfil_visibility_values_v1(
        session,
        actor_user_id,
        actor_profile_fields,
    )

    hidden_targets = get_hidden_process_targets_from_rules(
        rules,
        values_by_field,
    )

    if not hidden_targets:
        return visible_fields

    return filter_process_fields_by_hidden_targets(
        visible_fields,
        hidden_targets,
        field_header_map,
    )
# APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_PAGE_V1_END



# APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_PAGE_V2_START
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


def _apply_meu_perfil_subsequent_visibility_v2(
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
# APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_PAGE_V2_END


def get_page_data(
    session: Session,
    actor_user_id: int | None = None,
    actor_login_email: str = "",
    selected_entity_id: int | None = None,
) -> dict[str, Any]:
    visibility_context = build_effective_sidebar_visibility_v1(
        session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
    )
    permissions = dict(visibility_context.get("permissions") or {})
    selected_entity_id = visibility_context.get("selected_entity_id")
    current_user_is_admin = bool(visibility_context.get("current_user_is_admin"))
    current_entity_scope = str(visibility_context.get("current_entity_scope") or "").strip().lower()
    allowed_entity_ids: set[int] | None = None
    if actor_user_id is not None:
        allowed_entity_ids = {
            int(raw_id)
            for raw_id in (permissions.get("allowed_entity_ids") or set())
        }

    # APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V3_START
    sidebar_owner_entity = {"name": "", "logo_url": ""}
    try:
        from sqlalchemy import select as _appverbo_sidebar_select
        from appverbo.models.entity import Entity as _AppverboSidebarEntity

        _appverbo_owner_stmt = (
            _appverbo_sidebar_select(_AppverboSidebarEntity)
            .where(_AppverboSidebarEntity.profile_scope == "owner")
            .order_by(_AppverboSidebarEntity.id)
        )

        if hasattr(session, "exec"):
            _appverbo_owner_entity = session.exec(_appverbo_owner_stmt).first()
        else:
            _appverbo_owner_result = session.execute(_appverbo_owner_stmt)
            _appverbo_owner_entity = _appverbo_owner_result.scalars().first()

        if _appverbo_owner_entity:
            sidebar_owner_entity = {
                "name": str(getattr(_appverbo_owner_entity, "name", "") or "").strip(),
                "logo_url": str(getattr(_appverbo_owner_entity, "logo_url", "") or "").strip(),
            }
    except Exception:
        sidebar_owner_entity = {"name": "", "logo_url": ""}
    # APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V3_END
    sidebar_menu_settings = [
        dict(raw_row or {})
        for raw_row in (visibility_context.get("sidebar_menu_settings") or [])
    ]
    normalized_sidebar_menu_settings: list[dict[str, Any]] = []
    for raw_sidebar_item in sidebar_menu_settings:
        sidebar_item = dict(raw_sidebar_item or {})
        if resolve_menu_key_alias(sidebar_item.get("key")) == MENU_EMPRESA_KEY:
            sidebar_item = _normalize_empresa_sidebar_setting_v1(sidebar_item)
        normalized_sidebar_menu_settings.append(sidebar_item)
    sidebar_menu_settings = normalized_sidebar_menu_settings

    empresa_values_by_field = _resolve_empresa_entity_values_v1(
        session,
        selected_entity_id=selected_entity_id,
        allowed_entity_ids=allowed_entity_ids,
    )

    visible_sidebar_menu_keys = {
        str(raw_key or "").strip().lower()
        for raw_key in (visibility_context.get("visible_sidebar_menu_keys") or [])
        if str(raw_key or "").strip()
    }
    administrativo_menu = next(
        (
            row
            for row in sidebar_menu_settings
            if str(row.get("key") or "").strip().lower() == "administrativo"
        ),
        None,
    )
    sidebar_section_options = normalize_sidebar_sections(
        (administrativo_menu or {}).get("menu_config", {}).get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )
    actor_profile_fields: dict[str, str] = {}
    if actor_user_id is not None:
        raw_profile_fields = session.execute(
            select(Member.profile_custom_fields)
           .join(User, User.member_id == Member.id)
           .where(User.id == actor_user_id)
           .limit(1)
        ).scalar_one_or_none()
        actor_profile_fields = parse_member_profile_fields(raw_profile_fields)
    menu_process_values_map: dict[str, dict[str, str]] = {}
    menu_process_history_map: dict[str, list[dict[str, Any]]] = {}
    menu_process_quantity_values_map: dict[str, dict[str, list[dict[str, str]]]] = {}
    for sidebar_item in sidebar_menu_settings:
        menu_key = resolve_menu_key_alias(sidebar_item.get("key"))
        # ###################################################################################
        # (MENU PROCESS MAPS) INCLUIR DADOS DINAMICOS DO ADMINISTRATIVO
        # ###################################################################################
        # O menu "administrativo" tambem pode expor subprocessos dinamicos gravados em
        # profile_custom_fields. Sem carregar estes mapas, o reload/F5 volta sem a tabela
        # atualizada e transmite a ideia de que o registo nao foi guardado.
        if not menu_key or menu_key in {"home", "perfil"}:
            continue
        if menu_key == MENU_EMPRESA_KEY:
            menu_process_values_map[menu_key] = dict(empresa_values_by_field)
            continue
        if is_song_process_menu_v1(menu_key, sidebar_item.get("label")):
            if selected_entity_id is not None:
                song_rows = serialize_songs_to_history_rows_v1(
                    list_entity_songs_v1(session, int(selected_entity_id)),
                    sidebar_item,
                )
                if song_rows:
                    menu_process_history_map[menu_key] = song_rows
            continue
        visible_rows = (
            sidebar_item.get("process_visible_field_rows")
            if isinstance(sidebar_item.get("process_visible_field_rows"), list)
            else []
        )
        menu_values: dict[str, str] = {}
        for raw_row in visible_rows:
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            if not field_key:
                continue
            storage_key = build_menu_process_field_storage_key(menu_key, field_key)
            if not storage_key:
                continue
            storage_value = actor_profile_fields.get(storage_key)
            if storage_value is None:
                continue
            menu_values[field_key] = storage_value
        if menu_values:
            menu_process_values_map[menu_key] = menu_values
        quantity_values_by_rule: dict[str, list[dict[str, str]]] = {}
        for quantity_rule in sidebar_item.get("process_quantity_fields") or []:
            if not isinstance(quantity_rule, dict):
                continue
            rule_key = str(quantity_rule.get("key") or "").strip().lower()
            if not rule_key:
                continue
            quantity_storage_key = build_menu_process_quantity_storage_key(menu_key, rule_key)
            if not quantity_storage_key:
                continue
            quantity_values = parse_menu_process_quantity_values(
                actor_profile_fields.get(quantity_storage_key)
            )
            if quantity_values:
                quantity_values_by_rule[rule_key] = quantity_values
        if quantity_values_by_rule:
            menu_process_quantity_values_map[menu_key] = quantity_values_by_rule
        history_storage_key = build_menu_process_records_storage_key(menu_key)
        if menu_key in (PROCESS_VIEW_AUTHORIZATION_MENU_KEY, "perfil_de_autorizacao"):
            resolved_section_key = (
                "custom_objeto_de_autorizacao"
                if menu_key == "perfil_de_autorizacao"
                else PROCESS_VIEW_AUTHORIZATION_SECTION_KEY
            )
            legacy_menu_history_rows = (
                parse_menu_process_records(actor_profile_fields.get(history_storage_key))
                if history_storage_key
                else []
            )
            legacy_menu_history_rows = [
                row
                for row in legacy_menu_history_rows
                if str(row.get("section_key") or "").strip().lower()
                != resolved_section_key
            ]
            authorization_history_rows = build_process_view_authorization_history_rows_v1(
                session,
                selected_entity_id=selected_entity_id,
                section_key=resolved_section_key,
            )
            combined_history_rows = authorization_history_rows + legacy_menu_history_rows
            if combined_history_rows:
                menu_process_history_map[menu_key] = combined_history_rows
            elif _is_history_process_menu_v1(menu_key, sidebar_item.get("label")):
                legacy_history_rows = _build_legacy_history_row_v1(
                    visible_rows=visible_rows,
                    menu_values=menu_values,
                    quantity_values_by_rule=quantity_values_by_rule,
                )
                if legacy_history_rows:
                    menu_process_history_map[menu_key] = legacy_history_rows
            continue
        if history_storage_key:
            menu_history_rows = parse_menu_process_records(actor_profile_fields.get(history_storage_key))
            if menu_history_rows:
                menu_process_history_map[menu_key] = menu_history_rows
            elif _is_history_process_menu_v1(menu_key, sidebar_item.get("label")):
                legacy_history_rows = _build_legacy_history_row_v1(
                    visible_rows=visible_rows,
                    menu_values=menu_values,
                    quantity_values_by_rule=quantity_values_by_rule,
                )
                if legacy_history_rows:
                    menu_process_history_map[menu_key] = legacy_history_rows
    profile_personal_visible_fields = list(MENU_MEU_PERFIL_FIELDS_DEFAULT)
    profile_personal_field_labels = dict(MENU_MEU_PERFIL_FIELD_LABELS)
    profile_personal_field_types: dict[str, str] = {}
    profile_personal_field_header_map: dict[str, str] = {}
    profile_personal_custom_field_meta: dict[str, dict[str, Any]] = {}
    profile_personal_duplicate_custom_keys: set[str] = set()
    profile_personal_effective_visible_rows: list[dict[str, str]] = []
    meu_perfil_builtin_duplicate_labels = {
        **dict(MENU_MEU_PERFIL_FIELD_LABELS),
        "pais": "País",
    }
    for sidebar_item in sidebar_menu_settings:
        if resolve_menu_key_alias(sidebar_item.get("key")) != MENU_MEU_PERFIL_KEY:
            continue
        quantity_repeated_field_keys = get_menu_process_quantity_repeated_field_keys(
            sidebar_item.get("process_quantity_fields")
        )
        process_lists_by_key = {
            str(item.get("key") or "").strip().lower(): list(item.get("items") or [])
            for item in (sidebar_item.get("process_lists") or [])
            if str(item.get("key") or "").strip()
        }
        options = sidebar_item.get("process_field_options") or []
        option_labels = {
            str(item.get("key") or "").strip().lower(): str(item.get("label") or "").strip()
            for item in options
            if str(item.get("key") or "").strip()
        }
        option_types = {
            str(item.get("key") or "").strip().lower(): str(item.get("field_type") or "").strip().lower()
            for item in options
            if str(item.get("key") or "").strip()
        }
        if option_labels:
            profile_personal_field_labels = option_labels
        if option_types:
            profile_personal_field_types = option_types
        raw_header_map = sidebar_item.get("process_visible_field_header_map")
        if isinstance(raw_header_map, dict):
            mapped_header_map: dict[str, str] = {}
            for raw_key, raw_value in raw_header_map.items():
                clean_field_key = str(raw_key or "").strip().lower()
                clean_header_key = str(raw_value or "").strip().lower()
                if not clean_field_key or not clean_header_key:
                    continue
                resolved_builtin_key = resolve_meu_perfil_builtin_duplicate_field_key(
                    clean_field_key,
                    option_labels.get(clean_field_key, ""),
                    meu_perfil_builtin_duplicate_labels,
                )
                mapped_header_map[resolved_builtin_key or clean_field_key] = clean_header_key
            profile_personal_field_header_map = mapped_header_map
        raw_visible_rows = (
            sidebar_item.get("process_visible_field_rows")
            if isinstance(sidebar_item.get("process_visible_field_rows"), list)
            else []
        )
        effective_visible_rows: list[dict[str, str]] = []
        seen_effective_field_keys: set[str] = set()
        for raw_row in raw_visible_rows:
            if not isinstance(raw_row, dict):
                continue
            clean_field_key = str(raw_row.get("field_key") or "").strip().lower()
            if not clean_field_key:
                continue
            resolved_builtin_key = resolve_meu_perfil_builtin_duplicate_field_key(
                clean_field_key,
                option_labels.get(clean_field_key, ""),
                meu_perfil_builtin_duplicate_labels,
            )
            effective_field_key = resolved_builtin_key or clean_field_key
            if effective_field_key in seen_effective_field_keys:
                continue
            if clean_field_key in quantity_repeated_field_keys:
                continue
            seen_effective_field_keys.add(effective_field_key)
            effective_visible_rows.append(
                {
                    "field_key": effective_field_key,
                    "header_key": str(raw_row.get("header_key") or "").strip().lower(),
                }
            )
        if effective_visible_rows:
            profile_personal_effective_visible_rows = effective_visible_rows
            profile_personal_field_header_map = {
                str(row.get("field_key") or "").strip().lower(): str(row.get("header_key") or "").strip().lower()
                for row in effective_visible_rows
                if str(row.get("field_key") or "").strip() and str(row.get("header_key") or "").strip()
            }
        for custom_field in sidebar_item.get("process_additional_fields") or []:
            clean_key = str(custom_field.get("key") or "").strip().lower()
            if not clean_key.startswith("custom_"):
                continue
            if is_meu_perfil_builtin_duplicate_field(
                clean_key,
                custom_field.get("label"),
                meu_perfil_builtin_duplicate_labels,
            ):
                profile_personal_duplicate_custom_keys.add(clean_key)
                continue
            field_type = str(custom_field.get("field_type") or "text").strip().lower()
            if field_type not in {"text", "number", "email", "phone", "date", "time", "flag", "header", "list"}:
                field_type = "text"
            try:
                parsed_size = int(str(custom_field.get("size") or "").strip())
            except (TypeError, ValueError):
                parsed_size = 30
            if field_type in {"text", "number", "email", "phone"}:
                field_size: int | None = max(1, min(parsed_size, 255))
            else:
                field_size = None
            raw_required = custom_field.get("is_required", custom_field.get("required"))
            if isinstance(raw_required, bool):
                is_required = raw_required
            else:
                is_required = str(raw_required or "").strip().lower() in {"1", "true", "sim", "yes", "on"}
            if field_type == "header":
                is_required = False
            list_key = str(custom_field.get("list_key") or "").strip().lower()
            profile_personal_custom_field_meta[clean_key] = {
                "field_type": field_type,
                "size": field_size,
                "is_required": is_required,
                "list_key": list_key,
                "list_options": list(process_lists_by_key.get(list_key, [])) if field_type == "list" else [],
            }
        visible_raw = sidebar_item.get("process_visible_fields") or []
        visible_fields: list[str] = []
        if profile_personal_effective_visible_rows:
            visible_fields = [
                str(row.get("field_key") or "").strip().lower()
                for row in profile_personal_effective_visible_rows
                if str(row.get("field_key") or "").strip()
            ]
        else:
            seen_visible_fields: set[str] = set()
            for raw_key in visible_raw:
                clean_field_key = str(raw_key or "").strip().lower()
                if not clean_field_key:
                    continue
                resolved_builtin_key = resolve_meu_perfil_builtin_duplicate_field_key(
                    clean_field_key,
                    option_labels.get(clean_field_key, ""),
                    meu_perfil_builtin_duplicate_labels,
                )
                effective_field_key = resolved_builtin_key or clean_field_key
                if (
                    clean_field_key not in profile_personal_field_labels
                    and effective_field_key not in profile_personal_field_labels
                    and effective_field_key not in MENU_MEU_PERFIL_FIELD_LABELS
                    and effective_field_key != "pais"
                ):
                    continue
                if effective_field_key in seen_visible_fields:
                    continue
                if clean_field_key in quantity_repeated_field_keys:
                    continue
                seen_visible_fields.add(effective_field_key)
                visible_fields.append(effective_field_key)
        if visible_fields:
            visible_fields = _apply_meu_perfil_subsequent_visibility_v2(
                session=session,
                actor_user_id=actor_user_id,
                sidebar_item=sidebar_item,
                actor_profile_fields=actor_profile_fields,
                visible_fields=visible_fields,
                field_header_map=profile_personal_field_header_map,
            )
            profile_personal_visible_fields = visible_fields
        elif profile_personal_field_labels:
            profile_personal_visible_fields = [
                field_key
                for field_key in MENU_MEU_PERFIL_FIELDS_DEFAULT
                if field_key in profile_personal_field_labels
            ]
            if not profile_personal_visible_fields:
                profile_personal_visible_fields = [next(iter(profile_personal_field_labels.keys()))]
        break

    # APPVERBO_MEU_PERFIL_HEADER_TABS_ONLY_V1_START
    profile_personal_sections: list[dict[str, str]] = []
    profile_personal_field_section_map: dict[str, str] = {}
    header_section_order: list[str] = []
    header_section_seen: set[str] = set()

    profile_header_field_keys = {
        clean_key
        for clean_key, meta in profile_personal_custom_field_meta.items()
        if clean_key.startswith("custom_")
        and str((meta or {}).get("field_type") or "").strip().lower() == "header"
    }

    def append_profile_header_section_v1(raw_header_key: Any) -> None:
        clean_header_key = str(raw_header_key or "").strip().lower()

        if not clean_header_key:
            return

        if clean_header_key in header_section_seen:
            return

        if clean_header_key not in profile_header_field_keys:
            return

        section_label = profile_personal_field_labels.get(clean_header_key, "Aba")

        profile_personal_sections.append(
            {
                "key": clean_header_key,
                "label": section_label,
            }
        )
        header_section_order.append(clean_header_key)
        header_section_seen.add(clean_header_key)

    for field_key in profile_personal_visible_fields:
        clean_field_key = str(field_key or "").strip().lower()
        append_profile_header_section_v1(clean_field_key)

    for header_key in profile_personal_field_header_map.values():
        append_profile_header_section_v1(header_key)

    first_profile_header_key = header_section_order[0] if header_section_order else ""

    for field_key in profile_personal_visible_fields:
        clean_field_key = str(field_key or "").strip().lower()

        if not clean_field_key:
            continue

        field_type = str(profile_personal_field_types.get(clean_field_key) or "").strip().lower()

        if field_type == "header":
            continue

        configured_header_key = str(
            profile_personal_field_header_map.get(clean_field_key) or ""
        ).strip().lower()

        if configured_header_key in header_section_seen:
            profile_personal_field_section_map[clean_field_key] = configured_header_key
            continue

        profile_personal_field_section_map[clean_field_key] = first_profile_header_key
    # APPVERBO_MEU_PERFIL_HEADER_TABS_ONLY_V1_END


    required_profile_fields = ["nome", "telefone", "email", "pais"]

    for required_field in required_profile_fields:
        if required_field not in profile_personal_field_labels:
            profile_personal_field_labels[required_field] = {
                "nome": "Nome",
                "telefone": "Telefone",
                "email": "Email",
                "pais": "País",
            }[required_field]

        if required_field not in profile_personal_visible_fields:
            if required_field == "pais" and "telefone" in profile_personal_visible_fields:
                profile_personal_visible_fields.insert(
                    profile_personal_visible_fields.index("telefone") + 1,
                    required_field,
                )
            elif required_field == "email" and "telefone" in profile_personal_visible_fields:
                profile_personal_visible_fields.insert(
                    profile_personal_visible_fields.index("telefone") + 1,
                    required_field,
                )
            elif required_field == "telefone" and "nome" in profile_personal_visible_fields:
                profile_personal_visible_fields.insert(
                    profile_personal_visible_fields.index("nome") + 1,
                    required_field,
                )
            else:
                profile_personal_visible_fields.append(required_field)

    # APPVERBO_MEU_PERFIL_REQUIRED_SECTION_MAP_V1_START
    default_profile_header_section_v1 = header_section_order[0] if header_section_order else ""

    if "pais" not in profile_personal_field_section_map:
        profile_personal_field_section_map["pais"] = profile_personal_field_section_map.get(
            "telefone",
            default_profile_header_section_v1,
        )

    if "nome" not in profile_personal_field_section_map:
        profile_personal_field_section_map["nome"] = default_profile_header_section_v1

    if "telefone" not in profile_personal_field_section_map:
        profile_personal_field_section_map["telefone"] = profile_personal_field_section_map.get(
            "nome",
            default_profile_header_section_v1,
        )

    if "email" not in profile_personal_field_section_map:
        profile_personal_field_section_map["email"] = profile_personal_field_section_map.get(
            "telefone",
            default_profile_header_section_v1,
        )
    # APPVERBO_MEU_PERFIL_REQUIRED_SECTION_MAP_V1_END


    entity_admin_context = build_entity_admin_context_v1(
        session=session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
    )
    entity_admin_page_payload = build_entity_admin_page_payload_v1(entity_admin_context)
    profiles_for_form = get_allowed_global_profiles_for_form(session)

    user_admin_context = build_user_admin_list_context_v1(
        session=session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
    )
    user_admin_page_payload = build_user_admin_page_payload_v1(user_admin_context)
    entity_permissions_payload = dict(
        entity_admin_page_payload.get("entity_permissions") or permissions
    )

    return {
        "entities": entity_admin_page_payload["entities"],
        "profiles": profiles_for_form,
        "account_status_summary": user_admin_page_payload["account_status_summary"],
        "all_entities": entity_admin_page_payload["all_entities"],
        "active_entities": entity_admin_page_payload["active_entities"],
        "recent_entities": entity_admin_page_payload["recent_entities"],
        "inactive_entities": entity_admin_page_payload["inactive_entities"],
        "entity_list_pagination": entity_admin_page_payload["entity_list_pagination"],
        "recent_users": user_admin_page_payload["recent_users"],
        "all_users": user_admin_page_payload["all_users"],
        "created_users": user_admin_page_payload["created_users"],
        "active_created_users": user_admin_page_payload["active_created_users"],
        "inactive_users": user_admin_page_payload["inactive_users"],
        "pending_users": user_admin_page_payload["pending_users"],
        "blocked_users": user_admin_page_payload["blocked_users"],
        "non_active_users": user_admin_page_payload["non_active_users"],
        "superuser_users": user_admin_page_payload["superuser_users"],
        "user_list_pagination": user_admin_page_payload["user_list_pagination"],
        "entity_permissions": entity_permissions_payload,
        "current_user_can_manage_all_entities": bool(
            entity_admin_page_payload["current_user_can_manage_all_entities"]
        ),
        "next_entity_internal_number": entity_admin_page_payload["next_entity_internal_number"],
        "sidebar_owner_entity": sidebar_owner_entity,
        "current_entity_scope": current_entity_scope,
        "sidebar_owner_entity_name": sidebar_owner_entity.get("name", ""),
        "sidebar_owner_entity_logo_url": sidebar_owner_entity.get("logo_url", ""),
        "sidebar_menu_settings": sidebar_menu_settings,
        "sidebar_section_options": sidebar_section_options,
        "visible_sidebar_menu_keys": sorted(visible_sidebar_menu_keys),
        "menu_process_values_map": menu_process_values_map,
        "menu_process_history_map": menu_process_history_map,
        "menu_process_quantity_values_map": menu_process_quantity_values_map,
        "profile_personal_visible_fields": profile_personal_visible_fields,
        "profile_personal_field_labels": profile_personal_field_labels,
        "profile_personal_field_section_map": profile_personal_field_section_map,
        "profile_personal_sections": profile_personal_sections,
        "profile_personal_custom_field_meta": profile_personal_custom_field_meta,
        "menu_meu_perfil_field_options": [dict(item) for item in MENU_MEU_PERFIL_FIELD_OPTIONS],
        "menu_meu_perfil_field_labels": dict(MENU_MEU_PERFIL_FIELD_LABELS),
        "dashboard_data": get_home_dashboard_data(
            session,
            allowed_entity_ids=allowed_entity_ids,
        ),
    }

def get_home_dashboard_data(
    session: Session,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, Any]:
    apply_scope_filter = allowed_entity_ids is not None
    scoped_entity_ids = sorted(allowed_entity_ids) if allowed_entity_ids is not None else []

    entity_counts_stmt = select(Entity.is_active, func.count(Entity.id)).group_by(Entity.is_active)
    if apply_scope_filter:
        if scoped_entity_ids:
            entity_counts_stmt = entity_counts_stmt.where(Entity.id.in_(scoped_entity_ids))
        else:
            entity_counts_stmt = entity_counts_stmt.where(Entity.id == -1)

    entity_counts = session.execute(entity_counts_stmt).all()
    active_entities = 0
    inactive_entities = 0
    for row in entity_counts:
        if bool(row.is_active):
            active_entities = int(row[1])
        else:
            inactive_entities = int(row[1])

    if apply_scope_filter:
        if scoped_entity_ids:
            scoped_user_ids = [
                int(raw_id)
                for raw_id in session.execute(
                    select(User.id)
                   .join(MemberEntity, MemberEntity.member_id == User.member_id)
                   .where(
                        MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                        MemberEntity.entity_id.in_(scoped_entity_ids),
                    )
                   .distinct()
                ).scalars().all()
            ]
        else:
            scoped_user_ids = []
    else:
        scoped_user_ids = []

    profile_count_map: dict[str, int] = {}
    if not apply_scope_filter or scoped_user_ids:
        user_profile_join_condition = (
            (UserProfile.profile_id == Profile.id)
            & (UserProfile.is_active.is_(True))
        )
        if apply_scope_filter:
            user_profile_join_condition = (
                user_profile_join_condition
                & (UserProfile.user_id.in_(scoped_user_ids))
            )

        profile_rows = session.execute(
            select(Profile.name, func.count(func.distinct(UserProfile.user_id)))
           .select_from(Profile)
           .outerjoin(UserProfile, user_profile_join_condition)
           .where(func.lower(Profile.name).in_(ALLOWED_GLOBAL_PROFILE_NAMES_NORMALIZED))
           .group_by(Profile.id, Profile.name)
        ).all()
        for row in profile_rows:
            profile_count_map[normalize_profile_name(row.name)] = int(row[1])

    profile_labels = list(ALLOWED_GLOBAL_PROFILE_NAMES)
    profile_values = [
        profile_count_map.get(normalize_profile_name(label), 0) for label in profile_labels
    ]

    total_entities = active_entities + inactive_entities
    if apply_scope_filter:
        total_users = len(scoped_user_ids)
    else:
        total_users = session.scalar(select(func.count(User.id))) or 0

    return {
        "entity_status": {
            "labels": ["Ativas", "Inativas"],
            "values": [active_entities, inactive_entities],
        },
        "users_by_profile": {
            "labels": profile_labels,
            "values": profile_values,
        },
        "totals": {
            "entities": int(total_entities),
            "users": int(total_users),
            "active_entities": int(active_entities),
            "inactive_entities": int(inactive_entities),
        },
    }

def get_form_defaults() -> dict[str, str]:
    return {
        "full_name": "",
        "primary_phone": "",
        "email": "",
        "entity_id": "",
        "entity_name": "",
        "account_status": UserAccountStatus.ACTIVE.value,
        "profile_id": "",
    }

def get_entity_form_defaults() -> dict[str, str]:
    return {
        "name": "",
        "acronym": "",
        "tax_id": "",
        "email": "",
        "responsible_name": "",
        "door_number": "",
        "address": "",
        "city": "",
        "freguesia": "",
        "postal_code": "",
        "country": "",
        "phone": "",
        "description": "",
        "profile_scope": ENTITY_PROFILE_SCOPE_LEGADO,
        "created_at": date.today().strftime("%d/%m/%Y"),
    }

def get_entity_edit_defaults() -> dict[str, str]:
    from appverbo.use_cases.entities.get_entity_edit import get_entity_edit_defaults_v1

    return get_entity_edit_defaults_v1()

def get_entity_edit_data(
    session: Session,
    entity_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, str]:
    from appverbo.use_cases.entities.get_entity_edit import execute_get_entity_edit_v1

    return execute_get_entity_edit_v1(
        session=session,
        entity_id=entity_id,
        allowed_entity_ids=allowed_entity_ids,
    )

def get_user_edit_defaults() -> dict[str, str]:
    from appverbo.use_cases.users.get_user_edit import get_user_edit_defaults_v1

    return get_user_edit_defaults_v1()

def get_user_edit_data(
    session: Session,
    user_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, str]:
    from appverbo.use_cases.users.get_user_edit import execute_get_user_edit_v1

    return execute_get_user_edit_v1(
        session=session,
        user_id=user_id,
        allowed_entity_ids=allowed_entity_ids,
    )

def get_next_entity_internal_number(session: Session) -> int:
    from appverbo.admin_subprocesses.entidade.configuracao import ENTIDADE_CONFIG
    from appverbo.admin_subprocesses.repositories.entity_repository import EntityAdminRepository

    repository = EntityAdminRepository(ENTIDADE_CONFIG)
    return repository.get_next_internal_number(session=session)


# ###################################################################################
# (16) DEFAULTS DE CONTEXTO PARA new_user.html
# ###################################################################################

def ensure_new_user_template_context_defaults_v1(
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    clean_context = dict(context or {})

    current_user = dict(clean_context.get("current_user") or {})
    current_user.setdefault("full_name", "")
    current_user.setdefault("login_email", "")
    clean_context["current_user"] = current_user

    entity_permissions = dict(clean_context.get("entity_permissions") or {})
    entity_permissions.setdefault("selected_entity_id", None)
    entity_permissions.setdefault("allowed_entity_ids", [])
    entity_permissions.setdefault("can_manage_all_entities", False)
    clean_context["entity_permissions"] = entity_permissions

    user_personal_data = dict(clean_context.get("user_personal_data") or {})
    user_personal_data.setdefault("primary_phone", "")
    user_personal_data.setdefault("account_status", "")
    user_personal_data.setdefault("member_status", "")
    user_personal_data.setdefault("entities", [])
    user_personal_data.setdefault("address", "")
    user_personal_data.setdefault("city", "")
    user_personal_data.setdefault("freguesia", "")
    user_personal_data.setdefault("postal_code", "")
    clean_context["user_personal_data"] = user_personal_data

    dashboard_data = dict(clean_context.get("dashboard_data") or {})
    dashboard_data.setdefault("entity_status", {"labels": [], "values": []})
    dashboard_data.setdefault("users_by_profile", {"labels": [], "values": []})
    dashboard_data.setdefault(
        "totals",
        {
            "entities": 0,
            "users": 0,
            "active_entities": 0,
            "inactive_entities": 0,
        },
    )
    clean_context["dashboard_data"] = dashboard_data

    page_state = dict(clean_context.get("page_state") or {})
    page_state.setdefault("refresh_home_url", "/users/new?menu=home")
    clean_context["page_state"] = page_state
    clean_context.setdefault(
        "page_state_refresh_home_url",
        str(page_state.get("refresh_home_url") or "/users/new?menu=home"),
    )

    clean_context.setdefault("errors", [])
    clean_context.setdefault("success", "")
    clean_context.setdefault("generated_invite_link", "")
    clean_context.setdefault("form_data", get_form_defaults())
    clean_context.setdefault("entity_form_data", get_entity_form_defaults())
    clean_context.setdefault("entity_edit_data", get_entity_edit_defaults())
    clean_context.setdefault("user_edit_data", get_user_edit_defaults())
    clean_context.setdefault("entity_readonly_mode", False)
    clean_context.setdefault("user_readonly_mode", False)
    clean_context.setdefault("current_user_is_admin", False)
    clean_context.setdefault(
        "current_user_can_manage_all_entities",
        bool(entity_permissions.get("can_manage_all_entities")),
    )
    clean_context.setdefault("entity_success", "")
    clean_context.setdefault("entity_error", "")
    clean_context.setdefault("next_entity_internal_number", "")
    clean_context.setdefault("profile_success", "")
    clean_context.setdefault("profile_error", "")
    clean_context.setdefault("settings_success", "")
    clean_context.setdefault("settings_error", "")
    clean_context.setdefault("settings_edit_data", None)
    clean_context.setdefault("settings_edit_key", "")
    clean_context.setdefault("settings_action", "edit")
    clean_context.setdefault("settings_tab", "")
    clean_context.setdefault("profile_tab", "pessoal")
    clean_context.setdefault("initial_menu", "home")
    clean_context.setdefault("initial_menu_target", "")
    clean_context.setdefault("initial_dynamic_process_section", "")
    clean_context.setdefault("initial_profile_section", "")
    clean_context.setdefault("requested_profile_section", "")
    clean_context.setdefault("requested_dynamic_process_section", "")
    clean_context.setdefault("appverbo_after_save", False)
    clean_context.setdefault("admin_process_only", False)
    clean_context.setdefault("sidebar_section_edit_key", "")
    clean_context.setdefault("sidebar_section_edit_data", None)
    clean_context.setdefault("active_sidebar_sections", [])
    clean_context.setdefault("inactive_sidebar_sections", [])
    clean_context.setdefault("sessions", [])
    clean_context.setdefault("all_sessions", [])
    clean_context.setdefault("active_sessions", [])
    clean_context.setdefault("inactive_sessions", [])
    clean_context.setdefault("pending_sessions", [])
    clean_context.setdefault("blocked_sessions", [])
    clean_context.setdefault("session_edit_data", {})
    clean_context.setdefault("session_permissions", {})
    clean_context.setdefault("session_list_pagination", {})
    clean_context.setdefault("sidebar_sections_tab", "sessoes")
    clean_context.setdefault("admin_tab", "")
    clean_context.setdefault("admin_tabs_width_ch", 24)
    clean_context.setdefault("admin_tabs_text_size_px", 13)
    clean_context.setdefault("admin_tabs_font_family", '"Segoe UI", Tahoma, Arial, sans-serif')
    clean_context.setdefault("admin_tabs_color_hex", "#1F4FA3")
    clean_context.setdefault("admin_tabs_text_color_hex", "")
    clean_context.setdefault("admin_process_title_font_size_px", 20)
    clean_context.setdefault("admin_process_title_font_family", '"Segoe UI", Tahoma, Arial, sans-serif')
    clean_context.setdefault("admin_process_title_color_hex", "#0F172A")
    clean_context.setdefault("admin_card_item_font_size_px", 12)
    clean_context.setdefault("admin_card_item_font_family", 'Inter, "Segoe UI", sans-serif')
    clean_context.setdefault("admin_card_item_color_hex", "#0F1F3A")
    clean_context.setdefault("admin_card_item_font_weight", 500)
    clean_context.setdefault("admin_card_table_head_color_hex", "#000000")
    clean_context.setdefault("admin_topbar_color_hex", "#334A62")
    clean_context.setdefault("admin_sidebar_bg_color_hex", "#F3F3F4")
    clean_context.setdefault("admin_sidebar_active_bg_color_hex", "#E4E6EA")
    clean_context.setdefault("admin_sidebar_text_color_hex", "#5C6572")
    clean_context.setdefault("admin_sidebar_text_size_px", 14)
    clean_context.setdefault("admin_sidebar_font_family", '"Segoe UI", Tahoma, Arial, sans-serif')
    clean_context.setdefault("admin_sidebar_font_weight", 500)
    clean_context.setdefault("admin_sidebar_icon_color_hex", "#5F6B7D")
    clean_context.setdefault("admin_sidebar_section_text_color_hex", "#808792")
    clean_context.setdefault("admin_subprocess_state", None)
    clean_context.setdefault("admin_subprocess_state_utilizador_v1", None)
    clean_context.setdefault("admin_subprocess_state_utilizador", None)
    clean_context.setdefault("admin_subprocess_state_definicoes_v1", None)
    clean_context.setdefault("admin_subprocess_state_definicoes", None)
    clean_context.setdefault("admin_subprocess_shadow_state_v1", None)
    clean_context.setdefault("admin_subprocess_shadow_state", None)
    clean_context.setdefault("admin_menu_state", {"success": "", "error": ""})
    clean_context.setdefault("admin_menu_template_ready_v1", False)
    clean_context.setdefault("admin_menu_template_mode", "native")
    clean_context.setdefault("account_status_summary", [])
    clean_context.setdefault("entities", [])
    clean_context.setdefault("profiles", [])
    clean_context.setdefault("all_entities", [])
    clean_context.setdefault("active_entities", [])
    clean_context.setdefault("recent_entities", [])
    clean_context.setdefault("inactive_entities", [])
    clean_context.setdefault("entity_list_pagination", {})
    clean_context.setdefault("recent_users", [])
    clean_context.setdefault("all_users", [])
    clean_context.setdefault("created_users", [])
    clean_context.setdefault("active_created_users", [])
    clean_context.setdefault("inactive_users", [])
    clean_context.setdefault("pending_users", [])
    clean_context.setdefault("blocked_users", [])
    clean_context.setdefault("non_active_users", [])
    clean_context.setdefault("superuser_users", [])
    clean_context.setdefault("user_list_pagination", {})
    clean_context.setdefault("sidebar_owner_entity", {})
    clean_context.setdefault("current_entity_scope", "")
    clean_context.setdefault("sidebar_owner_entity_name", "")
    clean_context.setdefault("sidebar_owner_entity_logo_url", "")
    clean_context.setdefault("sidebar_menu_settings", [])
    clean_context.setdefault("sidebar_section_options", [])
    clean_context.setdefault("visible_sidebar_menu_keys", [])
    clean_context.setdefault("menu_process_values_map", {})
    clean_context.setdefault("menu_process_history_map", {})
    clean_context.setdefault("menu_process_quantity_values_map", {})
    clean_context.setdefault("profile_personal_visible_fields", [])
    clean_context.setdefault("profile_personal_field_labels", {})
    clean_context.setdefault("profile_personal_field_section_map", {})
    clean_context.setdefault("profile_personal_sections", [])
    clean_context.setdefault("profile_personal_custom_field_meta", {})
    clean_context.setdefault("menu_meu_perfil_field_options", [])
    clean_context.setdefault("menu_meu_perfil_field_labels", {})

    return clean_context

def build_users_new_url(**query_params: str) -> str:
    clean_query_params = {
        key: value
        for key, value in query_params.items()
        if isinstance(value, str) and value.strip()
    }
    if not clean_query_params:
        return "/users/new"
    return f"/users/new?{urlencode(clean_query_params)}"

__all__ = [
    "get_page_data",
    "get_home_dashboard_data",
    "get_form_defaults",
    "get_entity_form_defaults",
    "get_entity_edit_defaults",
    "get_entity_edit_data",
    "get_user_edit_defaults",
    "get_user_edit_data",
    "get_next_entity_internal_number",
    "ensure_new_user_template_context_defaults_v1",
    "build_users_new_url",
]
