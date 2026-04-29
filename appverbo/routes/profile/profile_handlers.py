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
    delete_sidebar_menu_setting,
    get_sidebar_menu_settings,
    set_sidebar_menu_visibility,
    update_sidebar_menu_additional_fields,
    update_sidebar_menu_label,
    update_sidebar_menu_process_fields,
)
from appverbo.services import *  # noqa: F403,F401
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

PROCESS_FIELD_TYPES = {"text", "number", "email", "phone", "date", "flag"}
PROCESS_TEXTUAL_FIELD_TYPES = {"text", "number", "email", "phone"}
PROCESS_DEFAULT_FIELD_TYPE = "text"

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

@router.post("/users/profile/personal")
async def update_personal_profile(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
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
        documentos_setting = next(
            (
                row
                for row in sidebar_menu_settings
                if str(row.get("key") or "").strip().lower() == "documentos"
            ),
            None,
        )
        process_options = (documentos_setting or {}).get("process_field_options", [])
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
        for raw_item in (documentos_setting or {}).get("process_additional_fields", []):
            clean_key = str(raw_item.get("key") or "").strip().lower()
            if not clean_key.startswith("custom_"):
                continue
            if clean_key not in option_keys:
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
        for raw_row in (documentos_setting or {}).get("process_visible_field_rows", []):
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
                for raw_key in (documentos_setting or {}).get("process_visible_fields", [])
            )
            if clean_key.startswith("custom_")
            and clean_key in option_keys
            and str((custom_field_meta.get(clean_key) or {}).get("field_type") or "") != "header"
        ]
        current_documents_values: dict[str, str] = {
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
                current_documents_values[custom_key] = (
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
            current_documents_values[custom_key] = ", ".join(clean_values)
        hidden_document_targets = get_hidden_process_targets_from_rules(
            (documentos_setting or {}).get("process_subsequent_fields"),
            current_documents_values,
        )
        visible_custom_keys_set = set(visible_custom_keys)
        active_custom_keys = filter_process_fields_by_hidden_targets(
            visible_custom_keys,
            hidden_document_targets,
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
        existing_profile_fields.update(updated_custom_fields)
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
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/users/profile/process-data")
async def update_dynamic_process_profile(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
    clean_menu_key = str(submitted_form.get("menu_key") or "").strip().lower()
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

        for field_key in active_section_field_keys:
            storage_key = build_menu_process_field_storage_key(clean_menu_key, field_key)
            if storage_key:
                existing_profile_fields.pop(storage_key, None)

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
