from __future__ import annotations

import unicodedata
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.core import *  # noqa: F403,F401
from appverbo.menu_settings import (
    MENU_MEU_PERFIL_FIELD_LABELS,
    MENU_MEU_PERFIL_KEY,
    delete_sidebar_menu_setting,
    get_sidebar_menu_settings,
    resolve_menu_key_alias,
    set_sidebar_menu_visibility,
    update_sidebar_menu_additional_fields,
    update_sidebar_menu_label,
    update_sidebar_menu_process_fields,
)
from appverbo.services import *  # noqa: F403,F401
from appverbo.services.profile import (
    build_menu_process_quantity_storage_key,
    get_menu_process_quantity_repeated_field_keys,
    parse_menu_process_quantity_values,
    serialize_menu_process_quantity_values,
)
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    Profile,
    User,
    UserAccountStatus,
    UserProfile,
)

from appverbo.routes.profile.router import router

PROCESS_FIELD_TYPES = {"text", "number", "email", "phone", "date", "flag", "list"}
PROCESS_TEXTUAL_FIELD_TYPES = {"text", "number", "email", "phone"}
PROCESS_DEFAULT_FIELD_TYPE = "text"
MEU_PERFIL_BUILTIN_DUPLICATE_LABELS = {
    **dict(MENU_MEU_PERFIL_FIELD_LABELS),
    "pais": "País",
}

def _normalize_process_field_type(raw_field_type: Any) -> str:
    clean_field_type = str(raw_field_type or PROCESS_DEFAULT_FIELD_TYPE).strip().lower()
    if clean_field_type in PROCESS_FIELD_TYPES:
        return clean_field_type
    return PROCESS_DEFAULT_FIELD_TYPE

def _normalize_process_field_size(raw_size: Any, field_type: str) -> int | None:
    if field_type not in PROCESS_TEXTUAL_FIELD_TYPES:
        return None
    try:
        parsed_size = int(str(raw_size or "").strip())
    except (TypeError, ValueError):
        return 255
    return max(1, min(parsed_size, 255))

def _normalize_process_field_required(raw_required: Any) -> bool:
    if isinstance(raw_required, bool):
        return raw_required
    clean_value = str(raw_required or "").strip().lower()
    return clean_value in {"1", "true", "sim", "yes", "on"}

def _normalize_lookup_text(raw_value: Any) -> str:
    normalized = (
        unicodedata.normalize("NFKD", str(raw_value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    return " ".join(normalized.split())

def _is_absence_process(menu_key: str, process_setting: dict[str, Any] | None = None) -> bool:
    parts = [_normalize_lookup_text(menu_key)]
    if isinstance(process_setting, dict):
        parts.append(_normalize_lookup_text(process_setting.get("label")))
    joined = " ".join(part for part in parts if part)
    if not joined:
        return False
    return ("assiduidade" in joined) or ("ausencia" in joined)

def _is_history_process(
    menu_key: str,
    process_setting: dict[str, Any] | None = None,
    section_key: str = "",
) -> bool:
    parts = [_normalize_lookup_text(menu_key)]
    if isinstance(process_setting, dict):
        parts.append(_normalize_lookup_text(process_setting.get("label")))
    parts.append(_normalize_lookup_text(section_key))
    joined = " ".join(part for part in parts if part)
    if not joined:
        return False
    if _is_absence_process(menu_key, process_setting):
        return True
    return "departamento" in joined

def _is_start_date_field(field_key: str, field_label: str) -> bool:
    joined = f"{_normalize_lookup_text(field_key)} {_normalize_lookup_text(field_label)}".strip()
    if not joined:
        return False
    return ("data inicio" in joined) or (" inicio" in joined) or joined.endswith("inicio")

def _is_end_date_field(field_key: str, field_label: str) -> bool:
    joined = f"{_normalize_lookup_text(field_key)} {_normalize_lookup_text(field_label)}".strip()
    if not joined:
        return False
    return ("data fim" in joined) or (" fim" in joined) or joined.endswith("fim")

def _parse_process_date_value(raw_value: Any) -> date | None:
    clean_value = str(raw_value or "").strip()
    if not clean_value:
        return None
    for date_format in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(clean_value, date_format).date()
        except ValueError:
            continue
    return None

def _normalize_process_state(raw_value: Any) -> str:
    clean_value = _normalize_lookup_text(raw_value)
    if clean_value in {"inativo", "inactive", "0", "false", "off"}:
        return "inativo"
    return "ativo"

def _build_process_sections(process_visible_field_rows: Any) -> list[dict[str, Any]]:
    if not isinstance(process_visible_field_rows, list):
        return []

    section_map: dict[str, dict[str, Any]] = {}
    section_order: list[str] = []
    for raw_row in process_visible_field_rows:
        if not isinstance(raw_row, dict):
            continue
        field_key = str(raw_row.get("field_key") or "").strip().lower()
        if not field_key:
            continue
        header_key = str(raw_row.get("header_key") or "").strip().lower()
        section_key = header_key or "__geral__"
        if section_key not in section_map:
            section_map[section_key] = {"key": section_key, "fields": []}
            section_order.append(section_key)
        section_map[section_key]["fields"].append(field_key)

    sections = [section_map[section_key] for section_key in section_order if section_key in section_map]
    if len(sections) == 1 and str(sections[0].get("key") or "") == "__geral__":
        return [
            {"key": f"field:{field_key}", "fields": [field_key]}
            for field_key in sections[0].get("fields", [])
            if str(field_key or "").strip()
        ]
    return sections

def _resolve_process_section_fields(
    process_visible_field_rows: Any,
    requested_section_key: str,
) -> list[str]:
    sections = _build_process_sections(process_visible_field_rows)
    if not sections:
        return []

    clean_section_key = str(requested_section_key or "").strip()
    selected_section = next(
        (
            section
            for section in sections
            if str(section.get("key") or "") == clean_section_key
        ),
        None,
    )
    if selected_section is None:
        selected_section = sections[0]
    return [
        str(field_key or "").strip().lower()
        for field_key in selected_section.get("fields", [])
        if str(field_key or "").strip()
    ]


def _normalize_process_quantity_rules(raw_rules: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_rules, list):
        return []

    normalized_rules: list[dict[str, Any]] = []
    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            continue
        rule_key = str(raw_rule.get("key") or "").strip().lower()
        quantity_field_key = str(raw_rule.get("quantity_field_key") or "").strip().lower()
        header_key = str(raw_rule.get("header_key") or "").strip().lower()
        item_label = str(raw_rule.get("item_label") or "").strip() or "Item"
        try:
            max_items = int(str(raw_rule.get("max_items") or "").strip())
        except (TypeError, ValueError):
            max_items = 1
        repeated_field_keys: list[str] = []
        seen_repeated_keys: set[str] = set()
        for raw_field_key in raw_rule.get("repeated_field_keys") or []:
            clean_field_key = str(raw_field_key or "").strip().lower()
            if not clean_field_key or clean_field_key in seen_repeated_keys:
                continue
            seen_repeated_keys.add(clean_field_key)
            repeated_field_keys.append(clean_field_key)
        if not rule_key or not quantity_field_key or not repeated_field_keys:
            continue
        normalized_rules.append(
            {
                "key": rule_key,
                "label": str(raw_rule.get("label") or rule_key).strip() or rule_key,
                "quantity_field_key": quantity_field_key,
                "repeated_field_keys": repeated_field_keys,
                "header_key": header_key,
                "max_items": max(1, min(max_items, 50)),
                "item_label": item_label,
            }
        )
    return normalized_rules


def _collect_process_quantity_items_from_form(
    submitted_form: Any,
    rule_key: str,
) -> list[dict[str, str]]:
    clean_rule_key = str(rule_key or "").strip().lower()
    if not clean_rule_key:
        return []

    prefix = f"process_quantity_field__{clean_rule_key}__"
    indexed_items: dict[int, dict[str, str]] = {}
    if hasattr(submitted_form, "multi_items"):
        raw_items = list(submitted_form.multi_items())
    else:
        raw_items = list((submitted_form or {}).items())

    for raw_name, raw_value in raw_items:
        clean_name = str(raw_name or "").strip().lower()
        if not clean_name.startswith(prefix):
            continue
        suffix = clean_name[len(prefix):]
        index_part, separator, field_key = suffix.partition("__")
        if not separator:
            continue
        try:
            item_index = int(index_part)
        except (TypeError, ValueError):
            continue
        clean_field_key = str(field_key or "").strip().lower()
        clean_field_value = str(raw_value or "").strip()
        if item_index < 0 or not clean_field_key or not clean_field_value:
            continue
        indexed_items.setdefault(item_index, {})[clean_field_key] = clean_field_value

    return [
        indexed_items[item_index]
        for item_index in sorted(indexed_items.keys())
        if indexed_items.get(item_index)
    ]


def _resolve_submitted_process_quantity_items(
    submitted_form: Any,
    rule_key: str,
) -> list[dict[str, str]]:
    payload_field_name = f"process_quantity_payload__{str(rule_key or '').strip().lower()}"
    parsed_quantity_items = parse_menu_process_quantity_values(
        str(submitted_form.get(payload_field_name) or "")
    )
    if parsed_quantity_items:
        return parsed_quantity_items
    return _collect_process_quantity_items_from_form(submitted_form, rule_key)

@router.post("/users/profile/personal")
async def update_personal_profile(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
    redirect_menu = str(submitted_form.get("menu") or MENU_MEU_PERFIL_KEY).strip().lower() or MENU_MEU_PERFIL_KEY
    redirect_target = str(submitted_form.get("target") or "#perfil-pessoal-card").strip() or "#perfil-pessoal-card"
    redirect_profile_section = str(submitted_form.get("profile_section") or "").strip().lower()
    clean_full_name = str(submitted_form.get("full_name") or "").strip()
    clean_primary_phone = str(submitted_form.get("primary_phone") or "").strip()
    clean_login_email = str(submitted_form.get("login_email") or submitted_form.get("email") or "").strip().lower()
    clean_country = str(submitted_form.get("country") or "").strip()
    clean_birth_date = str(submitted_form.get("birth_date") or "").strip()
    whatsapp_notice_opt_in = str(submitted_form.get("whatsapp_notice_opt_in") or "").strip()

    try:
        parsed_birth_date = parse_optional_date_pt(clean_birth_date)
    except ValueError:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Data de nascimento inválida. Use o formato dd/mm/aaaa.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    parsed_whatsapp_notice_opt_in = whatsapp_notice_opt_in == "1"

    if not clean_full_name:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Nome completo é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    if not clean_primary_phone:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Telefone principal é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not clean_login_email:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Email é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if "@" not in clean_login_email:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Email inválido.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member).join(User, User.member_id == Member.id).where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        user_account = session.get(User, current_user["id"])
        if user_account is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Conta de utilizador não encontrada.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        email_already_exists = session.execute(
            select(User.id)
            .join(Member, Member.id == User.member_id)
            .where(
                func.lower(User.login_email) == clean_login_email,
                User.id != current_user["id"],
            )
            .limit(1)
        ).scalar_one_or_none()

        member_email_already_exists = session.execute(
            select(Member.id)
            .where(
                func.lower(Member.email) == clean_login_email,
                Member.id != member.id,
            )
            .limit(1)
        ).scalar_one_or_none()

        if email_already_exists is not None or member_email_already_exists is not None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Este email já está associado a outro utilizador.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        sidebar_menu_settings = get_sidebar_menu_settings(session)
        meu_perfil_setting = next(
            (
                row
                for row in sidebar_menu_settings
                if resolve_menu_key_alias(row.get("key")) == MENU_MEU_PERFIL_KEY
            ),
            None,
        )
        process_options = (meu_perfil_setting or {}).get("process_field_options", [])
        quantity_rules = _normalize_process_quantity_rules(
            (meu_perfil_setting or {}).get("process_quantity_fields")
        )
        quantity_repeated_field_keys = get_menu_process_quantity_repeated_field_keys(quantity_rules)
        option_keys = {
            str(item.get("key") or "").strip().lower()
            for item in process_options
            if str(item.get("key") or "").strip()
        }
        option_labels_by_key = {
            str(item.get("key") or "").strip().lower(): str(item.get("label") or "").strip()
            for item in process_options
            if str(item.get("key") or "").strip()
        }
        custom_field_meta: dict[str, dict[str, Any]] = {}
        for raw_item in (meu_perfil_setting or {}).get("process_additional_fields", []):
            clean_key = str(raw_item.get("key") or "").strip().lower()
            if not clean_key.startswith("custom_"):
                continue
            if clean_key not in option_keys:
                continue
            if is_meu_perfil_builtin_duplicate_field(
                clean_key,
                raw_item.get("label"),
                MEU_PERFIL_BUILTIN_DUPLICATE_LABELS,
            ):
                continue
            field_type = str(raw_item.get("field_type") or "text").strip().lower()
            if field_type not in {"text", "number", "email", "phone", "date", "flag", "header"}:
                field_type = "text"
            size_value: int | None = None
            if field_type in {"text", "number", "email", "phone"}:
                try:
                    parsed_size = int(str(raw_item.get("size") or "").strip())
                except (TypeError, ValueError):
                    parsed_size = 30
                size_value = max(1, min(parsed_size, 255))
            is_required = _normalize_process_field_required(
                raw_item.get("is_required", raw_item.get("required"))
            )
            if field_type == "header":
                is_required = False
            custom_field_meta[clean_key] = {
                "field_type": field_type,
                "size": size_value,
                "is_required": is_required,
            }
        visible_field_section_map: dict[str, str] = {}
        for raw_row in (meu_perfil_setting or {}).get("process_visible_field_rows", []):
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            if not field_key:
                continue
            visible_field_section_map[field_key] = str(raw_row.get("header_key") or "").strip().lower()
        visible_custom_keys = [
            clean_key
            for clean_key in (
                str(raw_key or "").strip().lower()
                for raw_key in (meu_perfil_setting or {}).get("process_visible_fields", [])
            )
            if clean_key.startswith("custom_")
            and clean_key in option_keys
            and clean_key in custom_field_meta
            and clean_key not in quantity_repeated_field_keys
            and str((custom_field_meta.get(clean_key) or {}).get("field_type") or "") != "header"
        ]
        current_meu_perfil_values: dict[str, str] = {
            "nome": clean_full_name,
            "telefone": clean_primary_phone,
            "email": clean_login_email,
            "pais": clean_country,
            "data_nascimento": clean_birth_date,
            "autorizacao_whatsapp": "1" if parsed_whatsapp_notice_opt_in else "0",
        }
        for custom_key in visible_custom_keys:
            field_name = f"custom_field__{custom_key}"
            field_meta = custom_field_meta.get(custom_key) or {}
            field_type = str(field_meta.get("field_type") or "text").strip().lower()
            if field_type == "flag":
                current_meu_perfil_values[custom_key] = (
                    "1" if str(submitted_form.get(field_name) or "").strip() == "1" else "0"
                )
                continue
            if hasattr(submitted_form, "getlist"):
                raw_submitted_values = submitted_form.getlist(field_name)
            else:
                raw_submitted_values = [submitted_form.get(field_name)]
            submitted_values = [
                str(raw_value or "").strip()
                for raw_value in raw_submitted_values
            ]
            clean_values = [value for value in submitted_values if value]
            current_meu_perfil_values[custom_key] = ", ".join(clean_values)
        hidden_meu_perfil_targets = get_hidden_process_targets_from_rules(
            (meu_perfil_setting or {}).get("process_subsequent_fields"),
            current_meu_perfil_values,
        )
        visible_custom_keys_set = set(visible_custom_keys)
        active_custom_keys = filter_process_fields_by_hidden_targets(
            visible_custom_keys,
            hidden_meu_perfil_targets,
            visible_field_section_map,
        )
        active_custom_keys_set = set(active_custom_keys)

        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        existing_custom_fields = {
            key: value
            for key, value in existing_profile_fields.items()
            if key.startswith("custom_")
        }
        updated_custom_fields = {
            key: value
            for key, value in existing_custom_fields.items()
            if key not in visible_custom_keys_set
        }
        existing_quantity_values = {
            key: value
            for key, value in existing_profile_fields.items()
            if key.startswith(f"quantity__{MENU_MEU_PERFIL_KEY}__")
        }
        updated_quantity_values = {
            key: value
            for key, value in existing_quantity_values.items()
        }
        missing_required_custom_labels: list[str] = []
        for custom_key in active_custom_keys:
            field_name = f"custom_field__{custom_key}"
            field_meta = custom_field_meta.get(custom_key) or {}
            field_type = str(field_meta.get("field_type") or "text").strip().lower()
            field_size = field_meta.get("size")
            field_required = bool(field_meta.get("is_required"))
            if field_type == "flag":
                updated_custom_fields[custom_key] = "1" if str(submitted_form.get(field_name) or "").strip() == "1" else "0"
                continue

            if hasattr(submitted_form, "getlist"):
                raw_submitted_values = submitted_form.getlist(field_name)
            else:
                raw_submitted_values = [submitted_form.get(field_name)]
            submitted_values = [
                str(raw_value or "").strip()
                for raw_value in raw_submitted_values
            ]
            clean_values = [value for value in submitted_values if value]
            if isinstance(field_size, int) and field_size > 0:
                clean_values = [value[:field_size] for value in clean_values]
            clean_custom_value = ", ".join(clean_values)
            if field_required and not clean_custom_value:
                field_label = option_labels_by_key.get(custom_key) or custom_key
                if field_label not in missing_required_custom_labels:
                    missing_required_custom_labels.append(field_label)
                continue
            if clean_custom_value:
                updated_custom_fields[custom_key] = clean_custom_value

        for hidden_custom_key in visible_custom_keys:
            if hidden_custom_key in active_custom_keys_set:
                continue
            if hidden_custom_key in existing_custom_fields:
                updated_custom_fields[hidden_custom_key] = existing_custom_fields[hidden_custom_key]

        active_quantity_rule_keys: set[str] = set()
        for quantity_rule in quantity_rules:
            rule_key = str(quantity_rule.get("key") or "").strip().lower()
            quantity_field_key = str(quantity_rule.get("quantity_field_key") or "").strip().lower()
            if not rule_key or not quantity_field_key:
                continue

            if (
                quantity_field_key in hidden_meu_perfil_targets
                or visible_field_section_map.get(quantity_field_key) in hidden_meu_perfil_targets
            ):
                continue

            parsed_quantity_items = _resolve_submitted_process_quantity_items(
                submitted_form,
                rule_key,
            )
            active_quantity_rule_keys.add(rule_key)

            storage_key = build_menu_process_quantity_storage_key(MENU_MEU_PERFIL_KEY, rule_key)
            if not storage_key:
                continue

            serialized_quantity_items = serialize_menu_process_quantity_values(parsed_quantity_items)
            if serialized_quantity_items:
                updated_quantity_values[storage_key] = serialized_quantity_items
            else:
                updated_quantity_values.pop(storage_key, None)

        if missing_required_custom_labels:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Preencha os campos obrigatórios: " + ", ".join(missing_required_custom_labels) + ".",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        previous_phone = (member.primary_phone or "").strip()
        member.full_name = clean_full_name
        member.primary_phone = clean_primary_phone
        member.email = clean_login_email
        user_account.login_email = clean_login_email
        member.country = clean_country or None
        member.birth_date = parsed_birth_date
        member.whatsapp_notice_opt_in = parsed_whatsapp_notice_opt_in
        for existing_key in list(existing_profile_fields.keys()):
            if existing_key.startswith("custom_"):
                existing_profile_fields.pop(existing_key, None)
            if existing_key.startswith(f"quantity__{MENU_MEU_PERFIL_KEY}__"):
                existing_profile_fields.pop(existing_key, None)
        existing_profile_fields.update(updated_custom_fields)
        existing_profile_fields.update(updated_quantity_values)
        member.profile_custom_fields = serialize_member_profile_fields(existing_profile_fields)
        if previous_phone != clean_primary_phone:
            member.whatsapp_verification_status = "unknown"
            member.whatsapp_last_check_at = None
            member.whatsapp_last_error = None
            member.whatsapp_last_wa_id = None
            member.whatsapp_last_message_id = None

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Falha ao gravar dados pessoais.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    request.session["user_name"] = clean_full_name
    request.session["login_email"] = clean_login_email
    request.session["user_email"] = clean_login_email
    return RedirectResponse(
        url=build_users_new_url(
            profile_success="Dados pessoais atualizados com sucesso.",
            profile_tab="pessoal",
            menu=redirect_menu,
            target=redirect_target,
            profile_section=redirect_profile_section,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/users/profile/process-data")
async def update_dynamic_process_profile(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
    clean_menu_key = resolve_menu_key_alias(submitted_form.get("menu_key"))
    requested_section_key = str(submitted_form.get("section_key") or "").strip()
    requested_history_action = str(submitted_form.get("history_action") or "").strip().lower()
    requested_history_record_id = str(submitted_form.get("history_record_id") or "").strip()

    if not clean_menu_key:
        return RedirectResponse(
            url=build_users_new_url(
                menu="home",
                profile_error="Processo inválido.",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member).join(User, User.member_id == Member.id).where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    menu=clean_menu_key,
                    profile_error="Membro associado ao utilizador não encontrado.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        sidebar_menu_settings = get_sidebar_menu_settings(session)
        process_setting = next(
            (
                row
                for row in sidebar_menu_settings
                if str(row.get("key") or "").strip().lower() == clean_menu_key
            ),
            None,
        )
        if process_setting is None:
            return RedirectResponse(
                url=build_users_new_url(
                    menu="home",
                    profile_error="Processo não encontrado.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        quantity_rules = _normalize_process_quantity_rules(
            process_setting.get("process_quantity_fields")
        )
        absence_process_mode = _is_absence_process(clean_menu_key, process_setting)
        history_process_mode = _is_history_process(
            clean_menu_key,
            process_setting,
            requested_section_key,
        )
        record_label_singular = "ausência" if absence_process_mode else "registo"
        if requested_history_action not in {"", "create", "update", "delete"}:
            requested_history_action = "create"
        if not history_process_mode:
            requested_history_action = "create"

        section_field_keys = _resolve_process_section_fields(
            process_setting.get("process_visible_field_rows"),
            requested_section_key,
        )
        quantity_repeated_field_keys = {
            repeated_field_key
            for rule in quantity_rules
            for repeated_field_key in rule.get("repeated_field_keys", [])
        }
        section_field_keys = [
            field_key
            for field_key in section_field_keys
            if field_key not in quantity_repeated_field_keys
        ]
        if not section_field_keys:
            return RedirectResponse(
                url=build_users_new_url(
                    menu=clean_menu_key,
                    profile_error="Sem campos configurados para esta aba.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        field_meta_by_key: dict[str, dict[str, Any]] = {}
        field_section_map: dict[str, str] = {}
        for raw_row in process_setting.get("process_visible_field_rows") or []:
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            if not field_key:
                continue
            field_section_map[field_key] = str(raw_row.get("header_key") or "").strip().lower()
        for raw_option in process_setting.get("process_field_options") or []:
            option_key = str(raw_option.get("key") or "").strip().lower()
            if not option_key:
                continue
            option_type = _normalize_process_field_type(raw_option.get("field_type"))
            option_size = _normalize_process_field_size(raw_option.get("size"), option_type)
            option_label = str(raw_option.get("label") or option_key).strip() or option_key
            option_required = _normalize_process_field_required(
                raw_option.get("is_required", raw_option.get("required"))
            )
            field_meta_by_key[option_key] = {
                "field_type": option_type,
                "size": option_size,
                "label": option_label,
                "is_required": option_required and option_type != "header",
            }

        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        records_storage_key = build_menu_process_records_storage_key(clean_menu_key)
        existing_records = (
            parse_menu_process_records(existing_profile_fields.get(records_storage_key))
            if records_storage_key
            else []
        )
        current_process_values_by_field: dict[str, str] = {}
        for option_key in field_meta_by_key.keys():
            storage_key = build_menu_process_field_storage_key(clean_menu_key, option_key)
            if not storage_key:
                continue
            current_process_values_by_field[option_key] = str(existing_profile_fields.get(storage_key) or "").strip()
        for field_key in section_field_keys:
            field_meta = field_meta_by_key.get(field_key) or {}
            field_type = _normalize_process_field_type(field_meta.get("field_type"))
            input_name = f"process_field__{field_key}"
            if field_type == "flag":
                current_process_values_by_field[field_key] = (
                    "1" if str(submitted_form.get(input_name) or "").strip() == "1" else "0"
                )
                continue
            current_process_values_by_field[field_key] = str(submitted_form.get(input_name) or "").strip()

        submitted_quantity_values_by_rule: dict[str, list[dict[str, str]]] = {}
        for rule in quantity_rules:
            rule_key = str(rule.get("key") or "").strip().lower()
            header_key = str(rule.get("header_key") or "").strip().lower()
            quantity_field_key = str(rule.get("quantity_field_key") or "").strip().lower()
            repeated_field_keys = [
                str(raw_field_key or "").strip().lower()
                for raw_field_key in rule.get("repeated_field_keys", [])
                if str(raw_field_key or "").strip()
            ]
            if not rule_key or not quantity_field_key or not repeated_field_keys:
                continue

            applies_to_current_section = False
            if header_key:
                applies_to_current_section = header_key == str(requested_section_key or "").strip().lower()
            else:
                applies_to_current_section = quantity_field_key in section_field_keys

            if not applies_to_current_section:
                continue

            payload_name = f"process_quantity_payload__{rule_key}"
            raw_payload = str(submitted_form.get(payload_name) or "").strip()
            if not raw_payload:
                submitted_quantity_values_by_rule[rule_key] = []
                continue

            parsed_payload = parse_menu_process_quantity_values(raw_payload)
            if not parsed_payload:
                submitted_quantity_values_by_rule[rule_key] = []
                continue

            try:
                requested_quantity = int(str(current_process_values_by_field.get(quantity_field_key) or "").strip())
            except (TypeError, ValueError):
                requested_quantity = 0

            limited_quantity = max(0, min(requested_quantity, int(rule.get("max_items") or 1)))
            limited_items = parsed_payload[:limited_quantity]
            normalized_items: list[dict[str, str]] = []

            for raw_item in limited_items:
                clean_item: dict[str, str] = {}
                for repeated_field_key in repeated_field_keys:
                    field_meta = field_meta_by_key.get(repeated_field_key) or {}
                    field_type = _normalize_process_field_type(field_meta.get("field_type"))
                    field_size = _normalize_process_field_size(field_meta.get("size"), field_type)
                    clean_value = str(raw_item.get(repeated_field_key) or "").strip()
                    if field_type == "flag":
                        clean_item[repeated_field_key] = "1" if clean_value == "1" else "0"
                        continue
                    if isinstance(field_size, int) and field_size > 0:
                        clean_value = clean_value[:field_size]
                    if clean_value:
                        clean_item[repeated_field_key] = clean_value
                normalized_items.append(clean_item)

            submitted_quantity_values_by_rule[rule_key] = normalized_items
        hidden_process_targets = get_hidden_process_targets_from_rules(
            process_setting.get("process_subsequent_fields"),
            current_process_values_by_field,
        )
        active_section_field_keys = filter_process_fields_by_hidden_targets(
            section_field_keys,
            hidden_process_targets,
            field_section_map,
        )

        if history_process_mode and requested_history_action == "delete":
            if not requested_history_record_id:
                return RedirectResponse(
                    url=build_users_new_url(
                        menu=clean_menu_key,
                        profile_error=f"{record_label_singular.capitalize()} inválido para eliminar.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            filtered_records = [
                row
                for row in existing_records
                if str(row.get("record_id") or "").strip() != requested_history_record_id
            ]
            if len(filtered_records) == len(existing_records):
                return RedirectResponse(
                    url=build_users_new_url(
                        menu=clean_menu_key,
                        profile_error=f"{record_label_singular.capitalize()} não encontrado para eliminar.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            if records_storage_key:
                serialized_records = serialize_menu_process_records(filtered_records)
                if serialized_records:
                    existing_profile_fields[records_storage_key] = serialized_records
                else:
                    existing_profile_fields.pop(records_storage_key, None)
            for field_key in active_section_field_keys:
                storage_key = build_menu_process_field_storage_key(clean_menu_key, field_key)
                if storage_key:
                    existing_profile_fields.pop(storage_key, None)
            for rule in quantity_rules:
                quantity_storage_key = build_menu_process_quantity_storage_key(
                    clean_menu_key,
                    str(rule.get("key") or "").strip().lower(),
                )
                if quantity_storage_key:
                    existing_profile_fields.pop(quantity_storage_key, None)

            member.profile_custom_fields = serialize_member_profile_fields(existing_profile_fields)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                return RedirectResponse(
                    url=build_users_new_url(
                        menu=clean_menu_key,
                        profile_error=f"Falha ao eliminar o {record_label_singular}.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            return RedirectResponse(
                url=build_users_new_url(
                    menu=clean_menu_key,
                    profile_success=f"{record_label_singular.capitalize()} eliminado com sucesso.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        missing_required_labels: list[str] = []
        for field_key in active_section_field_keys:
            field_meta = field_meta_by_key.get(field_key) or {}
            field_type = _normalize_process_field_type(field_meta.get("field_type"))
            if field_type == "flag":
                continue
            if not bool(field_meta.get("is_required")):
                continue
            input_name = f"process_field__{field_key}"
            clean_value = str(submitted_form.get(input_name) or "").strip()
            if clean_value:
                continue
            field_label = str(field_meta.get("label") or field_key).strip() or field_key
            if field_label not in missing_required_labels:
                missing_required_labels.append(field_label)
        if missing_required_labels:
            return RedirectResponse(
                url=build_users_new_url(
                    menu=clean_menu_key,
                    profile_error="Preencha os campos obrigatórios: " + ", ".join(missing_required_labels) + ".",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        missing_required_quantity_labels: list[str] = []
        for rule in quantity_rules:
            rule_key = str(rule.get("key") or "").strip().lower()
            if rule_key not in submitted_quantity_values_by_rule:
                continue
            repeated_field_keys = [
                str(raw_field_key or "").strip().lower()
                for raw_field_key in rule.get("repeated_field_keys", [])
                if str(raw_field_key or "").strip()
            ]
            for item_index, item_values in enumerate(submitted_quantity_values_by_rule.get(rule_key, []), start=1):
                for repeated_field_key in repeated_field_keys:
                    field_meta = field_meta_by_key.get(repeated_field_key) or {}
                    if not bool(field_meta.get("is_required")):
                        continue
                    field_type = _normalize_process_field_type(field_meta.get("field_type"))
                    if field_type == "flag":
                        continue
                    clean_value = str(item_values.get(repeated_field_key) or "").strip()
                    if clean_value:
                        continue
                    field_label = str(field_meta.get("label") or repeated_field_key).strip() or repeated_field_key
                    composed_label = f"{rule.get('item_label') or 'Item'} {item_index} - {field_label}"
                    if composed_label not in missing_required_quantity_labels:
                        missing_required_quantity_labels.append(composed_label)

        if missing_required_quantity_labels:
            return RedirectResponse(
                url=build_users_new_url(
                    menu=clean_menu_key,
                    profile_error="Preencha os campos obrigatÃ³rios: " + ", ".join(missing_required_quantity_labels) + ".",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        for field_key in active_section_field_keys:
            storage_key = build_menu_process_field_storage_key(clean_menu_key, field_key)
            if storage_key:
                existing_profile_fields.pop(storage_key, None)
        for rule in quantity_rules:
            rule_key = str(rule.get("key") or "").strip().lower()
            if rule_key not in submitted_quantity_values_by_rule:
                continue
            quantity_storage_key = build_menu_process_quantity_storage_key(clean_menu_key, rule_key)
            if quantity_storage_key:
                existing_profile_fields.pop(quantity_storage_key, None)

        submitted_section_values: dict[str, str] = {}
        for field_key in active_section_field_keys:
            field_meta = field_meta_by_key.get(field_key) or {}
            field_type = _normalize_process_field_type(field_meta.get("field_type"))
            field_size = _normalize_process_field_size(field_meta.get("size"), field_type)
            input_name = f"process_field__{field_key}"
            storage_key = build_menu_process_field_storage_key(clean_menu_key, field_key)
            if not storage_key:
                continue

            if field_type == "flag":
                normalized_flag_value = "1" if str(submitted_form.get(input_name) or "").strip() == "1" else "0"
                if not absence_process_mode:
                    existing_profile_fields[storage_key] = normalized_flag_value
                submitted_section_values[field_key] = normalized_flag_value
                continue

            clean_value = str(submitted_form.get(input_name) or "").strip()
            if isinstance(field_size, int) and field_size > 0:
                clean_value = clean_value[:field_size]
            if clean_value:
                if not absence_process_mode:
                    existing_profile_fields[storage_key] = clean_value
                submitted_section_values[field_key] = clean_value

        for rule in quantity_rules:
            rule_key = str(rule.get("key") or "").strip().lower()
            if rule_key not in submitted_quantity_values_by_rule:
                continue
            serialized_quantity_values = serialize_menu_process_quantity_values(
                submitted_quantity_values_by_rule.get(rule_key, [])
            )
            quantity_storage_key = build_menu_process_quantity_storage_key(clean_menu_key, rule_key)
            if history_process_mode:
                if quantity_storage_key and serialized_quantity_values:
                    submitted_section_values[quantity_storage_key] = serialized_quantity_values
                continue
            if quantity_storage_key and serialized_quantity_values:
                existing_profile_fields[quantity_storage_key] = serialized_quantity_values

        if history_process_mode and not submitted_section_values:
            return RedirectResponse(
                url=build_users_new_url(
                    menu=clean_menu_key,
                    profile_error=f"Preencha ao menos um campo do {record_label_singular}.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        if history_process_mode and not absence_process_mode:
            submitted_section_values["__estado"] = _normalize_process_state(
                submitted_form.get("process_state")
            )

        if absence_process_mode:
            start_date_value: date | None = None
            end_date_value: date | None = None
            for field_key in active_section_field_keys:
                field_meta = field_meta_by_key.get(field_key) or {}
                field_type = _normalize_process_field_type(field_meta.get("field_type"))
                if field_type != "date":
                    continue
                field_label = str(field_meta.get("label") or field_key).strip() or field_key
                raw_date_value = submitted_section_values.get(
                    field_key,
                    str(submitted_form.get(f"process_field__{field_key}") or "").strip(),
                )
                parsed_date = _parse_process_date_value(raw_date_value)
                if parsed_date is None:
                    continue
                if start_date_value is None and _is_start_date_field(field_key, field_label):
                    start_date_value = parsed_date
                if end_date_value is None and _is_end_date_field(field_key, field_label):
                    end_date_value = parsed_date
            if (
                start_date_value is not None
                and end_date_value is not None
                and end_date_value < start_date_value
            ):
                return RedirectResponse(
                    url=build_users_new_url(
                        menu=clean_menu_key,
                        profile_error="Data fim não pode ser menor que a data início.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        success_message = "Dados atualizados com sucesso."
        if history_process_mode:
            if requested_history_action == "update" and requested_history_record_id:
                updated = False
                for row in existing_records:
                    if str(row.get("record_id") or "").strip() != requested_history_record_id:
                        continue
                    row["section_key"] = str(requested_section_key or "").strip()
                    row["values"] = dict(submitted_section_values)
                    updated = True
                    break
                if not updated:
                    return RedirectResponse(
                        url=build_users_new_url(
                            menu=clean_menu_key,
                            profile_error=f"{record_label_singular.capitalize()} não encontrado para editar.",
                        ),
                        status_code=status.HTTP_303_SEE_OTHER,
                    )
                success_message = f"{record_label_singular.capitalize()} atualizado com sucesso."
            else:
                existing_records.insert(
                    0,
                    {
                        "record_id": uuid4().hex,
                        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                        "section_key": str(requested_section_key or "").strip(),
                        "values": dict(submitted_section_values),
                    },
                )
                success_message = f"{record_label_singular.capitalize()} criado com sucesso."

            if records_storage_key:
                serialized_records = serialize_menu_process_records(existing_records[:200])
                if serialized_records:
                    existing_profile_fields[records_storage_key] = serialized_records
                else:
                    existing_profile_fields.pop(records_storage_key, None)

        member.profile_custom_fields = serialize_member_profile_fields(existing_profile_fields)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_users_new_url(
                    menu=clean_menu_key,
                    profile_error="Falha ao gravar os dados do processo.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_users_new_url(
            menu=clean_menu_key,
            profile_success=success_message,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/users/profile/address")
def update_address_profile(
    request: Request,
    address: str = Form(""),
    city: str = Form(""),
    freguesia: str = Form(""),
    postal_code: str = Form(""),
) -> RedirectResponse:
    clean_address = address.strip()
    clean_city = city.strip()
    clean_freguesia = freguesia.strip()
    clean_postal_code = postal_code.strip()

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member).join(User, User.member_id == Member.id).where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="morada",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        member.address = clean_address or None
        member.city = clean_city or None
        member.freguesia = clean_freguesia or None
        member.postal_code = clean_postal_code or None

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Falha ao gravar dados de morada.",
                    profile_tab="morada",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_users_new_url(
            profile_success="Dados de morada atualizados com sucesso.",
            profile_tab="morada",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/users/profile/training")
def update_training_profile(
    request: Request,
    training_discipulado_verbo_vida: str | None = Form(default=None),
    training_ebvv: str | None = Form(default=None),
    training_rhema: str | None = Form(default=None),
    training_escola_ministerial: str | None = Form(default=None),
    training_escola_missoes: str | None = Form(default=None),
    training_outros_enabled: str | None = Form(default=None),
    training_outros: str = Form(""),
) -> RedirectResponse:
    clean_training_outros = training_outros.strip()
    is_outros_enabled = training_outros_enabled == "1"

    if is_outros_enabled and not clean_training_outros:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Preencha o campo Outros para gravar o treinamento.",
                profile_tab="treinamento",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member).join(User, User.member_id == Member.id).where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="treinamento",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        member.training_discipulado_verbo_vida = training_discipulado_verbo_vida == "1"
        member.training_ebvv = training_ebvv == "1"
        member.training_rhema = training_rhema == "1"
        member.training_escola_ministerial = training_escola_ministerial == "1"
        member.training_escola_missoes = training_escola_missoes == "1"
        member.training_outros = clean_training_outros if is_outros_enabled else None

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Falha ao gravar dados de treinamento.",
                    profile_tab="treinamento",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_users_new_url(
            profile_success="Dados de treinamento atualizados com sucesso.",
            profile_tab="treinamento",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/users/profile/whatsapp/verify")
def verify_whatsapp_profile(request: Request) -> RedirectResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member).join(User, User.member_id == Member.id).where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        normalized_phone = normalize_whatsapp_recipient(member.primary_phone or "")
        if not normalized_phone:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error=(
                        "Telefone inválido para WhatsApp. Use formato internacional "
                        "(ex.: +351912345678)."
                    ),
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        is_sent, message_id, error_message = send_whatsapp_verification_template(normalized_phone)
        member.whatsapp_last_check_at = datetime.now(timezone.utc)
        member.whatsapp_last_message_id = message_id or None
        member.whatsapp_last_error = error_message or None
        member.whatsapp_verification_status = "pending" if is_sent else "failed"

        if not is_sent:
            session.commit()
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error=f"Não foi possível iniciar verificação WhatsApp: {error_message}",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        session.commit()
        return RedirectResponse(
            url=build_users_new_url(
                profile_success=(
                    "Verificação WhatsApp iniciada. O estado será atualizado automaticamente "
                    "quando o webhook receber a confirmação."
                ),
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
