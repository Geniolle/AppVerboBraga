from __future__ import annotations

import unicodedata
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4
from urllib.parse import parse_qsl, urlencode, urlsplit

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
    Department,
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    Profile,
    Song,
    User,
    UserAccountStatus,
    UserProfile,
)
from appverbo.services.songs import (
    build_song_field_mapping_v1,
    get_song_by_id_v1,
    is_song_process_menu_v1,
    normalize_song_lyrics_source_v1,
    normalize_song_lyrics_status_v1,
    transcribe_song_from_youtube_v1,
)
from appverbo.services.contact_membership_import import (
    parse_contact_membership_import_file_v1,
)
from appverbo.services.process_view_authorization import (
    build_effective_sidebar_visibility_v1,
    build_process_view_authorization_history_rows_v1,
    delete_process_view_authorization_rule_v1,
    is_process_view_authorization_section_v1,
    save_process_view_authorization_rule_v1,
)

from appverbo.routes.profile.router import router

PROCESS_FIELD_TYPES = {"text", "textarea", "number", "email", "phone", "date", "time", "flag", "list", "link"}
PROCESS_TEXTUAL_FIELD_TYPES = {"text", "textarea", "number", "email", "phone", "link"}
PROCESS_DEFAULT_FIELD_TYPE = "text"
MEU_PERFIL_BUILTIN_DUPLICATE_LABELS = {
    **dict(MENU_MEU_PERFIL_FIELD_LABELS),
    "pais": "País",
}




def _remove_local_entity_logo_if_exists_v1(logo_url: str) -> None:
    clean_logo_url = str(logo_url or "").strip()

    if not clean_logo_url.startswith("/static/entities/"):
        return

    local_logo_path = BASE_DIR / clean_logo_url.lstrip("/")
    local_logo_path.unlink(missing_ok=True)


def _safe_process_flow_debug_value_v1(raw_value: Any, max_size: int = 2000) -> str:
    clean_value = str(raw_value or "")
    if len(clean_value) > max_size:
        return clean_value[:max_size] + "...[TRUNCATED]"
    return clean_value


def _build_process_flow_form_snapshot_v1(submitted_form: Any) -> dict[str, Any]:
    import json

    blocked_fragments = (
        "password",
        "senha",
        "token",
        "csrf",
        "secret",
        "cookie",
        "authorization",
    )

    if hasattr(submitted_form, "multi_items"):
        raw_items = list(submitted_form.multi_items())
    elif hasattr(submitted_form, "items"):
        raw_items = list(submitted_form.items())
    else:
        raw_items = []

    general_fields: dict[str, Any] = {}
    process_fields: dict[str, Any] = {}
    quantity_payloads: dict[str, Any] = {}

    for raw_name, raw_value in raw_items:
        clean_name = str(raw_name or "").strip()
        clean_name_lower = clean_name.lower()
        if not clean_name:
            continue

        if any(fragment in clean_name_lower for fragment in blocked_fragments):
            clean_value: Any = "[FILTERED]"
        else:
            clean_value = _safe_process_flow_debug_value_v1(raw_value)

        if clean_name.startswith("process_quantity_payload__"):
            parsed_payload: Any = None
            parsed_error = ""
            try:
                parsed_payload = json.loads(str(raw_value or "[]"))
            except Exception as exc:
                parsed_error = repr(exc)

            quantity_payloads[clean_name] = {
                "raw": clean_value,
                "parsed": parsed_payload,
                "parse_error": parsed_error,
            }
            continue

        if clean_name.startswith("process_field__"):
            process_fields[clean_name] = clean_value
            continue

        general_fields[clean_name] = clean_value

    return {
        "general_fields": general_fields,
        "process_fields": process_fields,
        "quantity_payloads": quantity_payloads,
    }


def _write_meu_perfil_process_flow_debug_log_v1(
    request: Request,
    stage: str,
    *,
    submitted_form: Any | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    import json
    import os
    from pathlib import Path
    from datetime import datetime, timezone

    try:
        log_dir = Path(
            os.environ.get(
                "APPVERBO_PROFILE_SAVE_LOG_DIR",
                "appverbo_runtime_logs",
            )
        )
        log_dir.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "logger": "APPVERBO_MEU_PERFIL_PROCESS_FLOW_DEBUG_V1",
            "stage": str(stage or "").strip(),
            "request": {
                "method": str(getattr(request, "method", "") or ""),
                "path": str(getattr(getattr(request, "url", None), "path", "") or ""),
                "url": str(getattr(request, "url", "") or ""),
                "client": str(getattr(getattr(request, "client", None), "host", "") or ""),
            },
            "form_snapshot": (
                _build_process_flow_form_snapshot_v1(submitted_form)
                if submitted_form is not None
                else {}
            ),
            "data": data or {},
        }

        log_line = json.dumps(log_entry, ensure_ascii=False, default=str, sort_keys=True)
        log_path = log_dir / "meu_perfil_process_flow.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(log_line + "\n")

        print("APPVERBO_MEU_PERFIL_PROCESS_FLOW_DEBUG " + log_line, flush=True)
    except Exception as exc:
        print("APPVERBO_MEU_PERFIL_PROCESS_FLOW_DEBUG_ERROR " + repr(exc), flush=True)


# APPVERBO_MEU_PERFIL_SAVE_LOGGER_V2_START
def _safe_meu_perfil_logger_value_v2(raw_value: Any, max_size: int = 1500) -> Any:
    clean_value = str(raw_value or "")

    if len(clean_value) > max_size:
        return clean_value[:max_size] + "...[TRUNCATED]"

    return clean_value


def _append_meu_perfil_logger_value_v2(target: dict[str, Any], key: str, value: Any) -> None:
    clean_key = str(key or "").strip()

    if not clean_key:
        return

    if clean_key in target:
        if not isinstance(target[clean_key], list):
            target[clean_key] = [target[clean_key]]
        target[clean_key].append(value)
        return

    target[clean_key] = value


def _build_meu_perfil_form_debug_snapshot_v2(submitted_form: Any) -> dict[str, Any]:
    import json

    blocked_fragments = (
        "password",
        "senha",
        "token",
        "csrf",
        "secret",
        "cookie",
        "authorization",
    )

    if hasattr(submitted_form, "multi_items"):
        raw_items = list(submitted_form.multi_items())
    elif hasattr(submitted_form, "items"):
        raw_items = list(submitted_form.items())
    else:
        raw_items = []

    general_fields: dict[str, Any] = {}
    custom_fields: dict[str, Any] = {}
    quantity_payloads: dict[str, Any] = {}
    quantity_live_fields: dict[str, Any] = {}

    for raw_name, raw_value in raw_items:
        clean_name = str(raw_name or "").strip()
        clean_name_lower = clean_name.lower()

        if not clean_name:
            continue

        if any(fragment in clean_name_lower for fragment in blocked_fragments):
            clean_value = "[FILTERED]"
        else:
            clean_value = _safe_meu_perfil_logger_value_v2(raw_value)

        if clean_name.startswith("process_quantity_payload__"):
            parsed_payload: Any = None
            parsed_error = ""

            try:
                parsed_payload = json.loads(str(raw_value or "[]"))
            except Exception as exc:
                parsed_error = repr(exc)

            _append_meu_perfil_logger_value_v2(
                quantity_payloads,
                clean_name,
                {
                    "raw": clean_value,
                    "parsed": parsed_payload,
                    "parse_error": parsed_error,
                },
            )
            continue

        if clean_name.startswith("process_quantity_field__"):
            _append_meu_perfil_logger_value_v2(
                quantity_live_fields,
                clean_name,
                clean_value,
            )
            continue

        if clean_name.startswith("custom_field__"):
            _append_meu_perfil_logger_value_v2(
                custom_fields,
                clean_name,
                clean_value,
            )
            continue

        _append_meu_perfil_logger_value_v2(
            general_fields,
            clean_name,
            clean_value,
        )

    return {
        "general_fields": general_fields,
        "custom_fields": custom_fields,
        "quantity_payloads": quantity_payloads,
        "quantity_live_fields": quantity_live_fields,
        "all_field_names": [
            str(raw_name or "").strip()
            for raw_name, _raw_value in raw_items
            if str(raw_name or "").strip()
        ],
    }


def _write_meu_perfil_save_debug_log_v2(
    request: Request,
    submitted_form: Any,
    stage: str,
    data: dict[str, Any] | None = None,
) -> None:
    import json
    import os
    from pathlib import Path
    from datetime import datetime, timezone

    try:
        log_dir = Path(
            os.environ.get(
                "APPVERBO_PROFILE_SAVE_LOG_DIR",
                "appverbo_runtime_logs",
            )
        )
        log_dir.mkdir(parents=True, exist_ok=True)

        request_url = ""
        request_path = ""
        request_method = ""
        request_client = ""

        try:
            request_url = str(request.url)
            request_path = str(request.url.path)
            request_method = str(request.method)
            request_client = str(getattr(request.client, "host", "") or "")
        except Exception:
            pass

        log_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "logger": "APPVERBO_MEU_PERFIL_SAVE_LOGGER_V2",
            "stage": str(stage or "").strip(),
            "request": {
                "method": request_method,
                "path": request_path,
                "url": request_url,
                "client": request_client,
            },
            "form_snapshot": _build_meu_perfil_form_debug_snapshot_v2(submitted_form),
            "data": data or {},
        }

        log_line = json.dumps(
            log_entry,
            ensure_ascii=False,
            default=str,
            sort_keys=True,
        )

        log_path = log_dir / "meu_perfil_save_debug.log"

        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(log_line + "\n")

        print("APPVERBO_MEU_PERFIL_SAVE_DEBUG " + log_line, flush=True)

    except Exception as exc:
        print(
            "APPVERBO_MEU_PERFIL_SAVE_DEBUG_ERROR " + repr(exc),
            flush=True,
        )
# APPVERBO_MEU_PERFIL_SAVE_LOGGER_V2_END


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
        return 4000 if field_type == "textarea" else 255
    max_size = 4000 if field_type == "textarea" else 255
    return max(1, min(parsed_size, max_size))

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

def _is_single_record_process(
    menu_key: str,
    process_setting: dict[str, Any] | None = None,
    section_key: str = "",
) -> bool:
    normalized_menu_key = _normalize_lookup_text(menu_key).replace(" ", "_")
    parts = [_normalize_lookup_text(menu_key), _normalize_lookup_text(section_key)]
    if isinstance(process_setting, dict):
        parts.append(_normalize_lookup_text(process_setting.get("label")))
    joined = " ".join(part for part in parts if part)
    if not normalized_menu_key and not joined:
        return False
    return (
        normalized_menu_key in {"empresa", "meu_perfil", "perfil"}
        or "meu perfil" in joined
        or "perfil pessoal" in joined
    )

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
    if _is_single_record_process(menu_key, process_setting, section_key):
        return False
    return True

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


_ENTITY_NUMBER_FIELD_PATTERNS = [
    "n entidade", "num entidade", "numero entidade", "nr entidade", "n. entidade", "entidade",
]
_ENTITY_NUMBER_FIELD_KEYS = {
    "numero_entidade", "custom_n_entidade", "entity_internal_number", "custom_n_cliente",
}

def _is_entity_number_field_v1(field_key: str, field_label: str) -> bool:
    normalized_label = _normalize_lookup_text(field_label)
    normalized_key = str(field_key or "").strip().lower()
    if normalized_key in _ENTITY_NUMBER_FIELD_KEYS:
        return True
    for p in _ENTITY_NUMBER_FIELD_PATTERNS:
        if p in normalized_label or p in normalized_key:
            return True
    return False


def _resolve_department_name_field_key_v1(
    field_keys: list[str],
    field_meta_by_key: dict[str, dict[str, Any]],
) -> str:
    for raw_field_key in field_keys:
        field_key = str(raw_field_key or "").strip().lower()
        if not field_key:
            continue
        field_meta = field_meta_by_key.get(field_key) or {}
        if _normalize_process_field_type(field_meta.get("field_type")) == "header":
            continue
        joined_lookup = " ".join(
            part
            for part in (
                _normalize_lookup_text(field_key),
                _normalize_lookup_text(field_meta.get("label")),
            )
            if part
        )
        if "departamento" not in joined_lookup:
            continue
        if "nome" not in joined_lookup:
            continue
        return field_key
    return ""


def _extract_department_name_value_v1(
    values_by_field: dict[str, Any],
    field_keys: list[str],
    field_meta_by_key: dict[str, dict[str, Any]],
) -> str:
    if not isinstance(values_by_field, dict):
        return ""
    department_name_field_key = _resolve_department_name_field_key_v1(
        field_keys,
        field_meta_by_key,
    )
    if not department_name_field_key:
        return ""
    clean_name = " ".join(
        str(values_by_field.get(department_name_field_key) or "").strip().split()
    )
    if not clean_name:
        return ""
    return clean_name[:150]


def _parse_department_id_value_v1(raw_value: Any) -> int | None:
    try:
        parsed_id = int(str(raw_value or "").strip())
    except (TypeError, ValueError):
        return None
    if parsed_id <= 0:
        return None
    return parsed_id


def _resolve_selected_entity_id_for_process_v1(
    request: Request,
    session: Session,
    current_user: dict[str, Any],
) -> tuple[int | None, str]:
    selected_entity_id = get_session_entity_id(request)
    entity_permissions = get_user_entity_permissions(
        session,
        int(current_user["id"]),
        str(current_user.get("login_email") or ""),
        selected_entity_id,
    )
    resolved_entity_id = entity_permissions.get("selected_entity_id")

    if resolved_entity_id is None:
        return None, "Nenhuma entidade ativa foi encontrada para atualizar."

    if not is_entity_within_permissions(int(resolved_entity_id), entity_permissions):
        return None, "Sem permissao para atualizar esta entidade."

    return int(resolved_entity_id), ""


def _find_department_by_entity_and_name_v1(
    session: Session,
    entity_id: int,
    department_name: str,
) -> Department | None:
    clean_department_name = " ".join(str(department_name or "").strip().split())
    if not clean_department_name:
        return None

    return session.execute(
        select(Department).where(
            Department.entity_id == int(entity_id),
            func.lower(func.trim(Department.name)) == clean_department_name.lower(),
        )
    ).scalar_one_or_none()


def _upsert_department_for_process_v1(
    session: Session,
    *,
    entity_id: int,
    department_name: str,
    is_active: bool,
    preferred_department_id: int | None = None,
) -> Department | None:
    clean_department_name = " ".join(str(department_name or "").strip().split())[:150]
    if not clean_department_name:
        return None

    department_by_id: Department | None = None
    if preferred_department_id is not None:
        possible_department = session.get(Department, int(preferred_department_id))
        if (
            possible_department is not None
            and int(possible_department.entity_id) == int(entity_id)
        ):
            department_by_id = possible_department

    department_by_name = _find_department_by_entity_and_name_v1(
        session,
        int(entity_id),
        clean_department_name,
    )
    if department_by_name is not None:
        department_by_name.name = clean_department_name
        department_by_name.is_active = bool(is_active)
        if (
            department_by_id is not None
            and int(department_by_id.id) != int(department_by_name.id)
        ):
            department_by_id.is_active = False
        return department_by_name

    if department_by_id is not None:
        department_by_id.name = clean_department_name
        department_by_id.is_active = bool(is_active)
        return department_by_id

    created_department = Department(
        entity_id=int(entity_id),
        name=clean_department_name,
        is_active=bool(is_active),
    )
    session.add(created_department)
    session.flush()
    return created_department


def _deactivate_department_for_process_v1(
    session: Session,
    *,
    entity_id: int,
    department_id: int | None,
    department_name: str,
) -> Department | None:
    target_department: Department | None = None

    if department_id is not None:
        possible_department = session.get(Department, int(department_id))
        if (
            possible_department is not None
            and int(possible_department.entity_id) == int(entity_id)
        ):
            target_department = possible_department

    if target_department is None and department_name:
        target_department = _find_department_by_entity_and_name_v1(
            session,
            int(entity_id),
            department_name,
        )

    if target_department is not None:
        target_department.is_active = False

    return target_department

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



# APPVERBO_MEU_PERFIL_SUBSEQUENT_RULES_RESOLVER_V1_START
def _resolve_process_subsequent_rules_from_setting_v1(
    process_setting: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(process_setting, dict):
        return []

    resolved_rules: list[dict[str, Any]] = []

    for storage_key in (
        "process_subsequent_fields",
        "subsequent_fields",
        "process_subsequent_rules",
    ):
        raw_rules = process_setting.get(storage_key)

        if not isinstance(raw_rules, list):
            continue

        for raw_rule in raw_rules:
            if isinstance(raw_rule, dict):
                resolved_rules.append(raw_rule)

    return resolved_rules
# APPVERBO_MEU_PERFIL_SUBSEQUENT_RULES_RESOLVER_V1_END


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
    clean_rule_key = str(rule_key or "").strip().lower()
    if not clean_rule_key:
        return []

    payload_field_name = f"process_quantity_payload__{clean_rule_key}"

    # APPVERBO_MEU_PERFIL_QUANTITY_LIVE_FIELDS_PRIORITY_V1_START
    # O formulario pode submeter mais de um input oculto
    # process_quantity_payload__<rule_key>.
    #
    # No caso dos Dados de agregados foi detetado conflito:
    #   1) um payload oculto com valores novos
    #   2) outro payload oculto duplicado com valores antigos
    #
    # Como os campos visiveis process_quantity_field__<rule_key>__<idx>__<field>
    # sao a fonte mais fiel no momento do submit, o backend deve priorizar
    # os campos vivos quando eles existem.
    collected_quantity_items = _collect_process_quantity_items_from_form(
        submitted_form,
        clean_rule_key,
    )

    if collected_quantity_items:
        return collected_quantity_items
    # APPVERBO_MEU_PERFIL_QUANTITY_LIVE_FIELDS_PRIORITY_V1_END

    if hasattr(submitted_form, "getlist"):
        raw_payload_values = [
            str(raw_value or "").strip()
            for raw_value in submitted_form.getlist(payload_field_name)
        ]
    else:
        raw_payload_value = (
            submitted_form.get(payload_field_name)
            if hasattr(submitted_form, "get")
            else ""
        )
        raw_payload_values = [str(raw_payload_value or "").strip()]

    # APPVERBO_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V3_START
    # Se ainda nao existem campos vivos, tentamos aproveitar os payloads ocultos.
    # Para evitar que um payload antigo sobrescreva um payload novo, percorremos
    # os valores na ordem recebida e escolhemos o primeiro payload preenchido valido.
    for raw_payload_value in raw_payload_values:
        if not raw_payload_value or raw_payload_value == "[]":
            continue

        parsed_quantity_items = parse_menu_process_quantity_values(raw_payload_value)

        if parsed_quantity_items:
            return parsed_quantity_items
    # APPVERBO_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V3_END

    # Se o payload "[]" foi submetido explicitamente, isto significa que o utilizador
    # limpou a quantidade ou removeu todos os pares.
    if any(raw_payload_value == "[]" for raw_payload_value in raw_payload_values):
        return []

    return []



# APPVERBO_RETURN_URL_POST_SAVE_V4_START
def _sanitize_users_new_return_url_post_save_v4(
    raw_return_url: Any,
    extra_params: dict[str, Any] | None = None,
) -> str:
    clean_return_url = str(raw_return_url or "").strip()

    if not clean_return_url:
        return ""

    try:
        parsed_url = urlsplit(clean_return_url)
    except Exception:
        return ""

    if parsed_url.scheme or parsed_url.netloc:
        return ""

    path = parsed_url.path or "/users/new"

    if path != "/users/new":
        return ""

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
    query_params["appverbo_after_save"] = "1"

    for raw_key, raw_value in (extra_params or {}).items():
        clean_key = str(raw_key or "").strip()
        clean_value = str(raw_value or "").strip()

        if clean_key and clean_value:
            query_params[clean_key] = clean_value

    query_string = urlencode(query_params)
    fragment = f"#{parsed_url.fragment}" if parsed_url.fragment else ""

    return f"{path}?{query_string}{fragment}" if query_string else f"{path}{fragment}"


def _append_after_save_marker_to_users_new_url_v4(raw_url: str) -> str:
    clean_url = str(raw_url or "").strip()

    if not clean_url:
        return clean_url

    try:
        parsed_url = urlsplit(clean_url)
    except Exception:
        return clean_url

    if parsed_url.scheme or parsed_url.netloc:
        return clean_url

    path = parsed_url.path or "/users/new"

    if path != "/users/new":
        return clean_url

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
    query_params["appverbo_after_save"] = "1"

    query_string = urlencode(query_params)
    fragment = f"#{parsed_url.fragment}" if parsed_url.fragment else ""

    return f"{path}?{query_string}{fragment}" if query_string else f"{path}{fragment}"


def _build_users_new_url_with_return_context_v4(
    submitted_form: Any,
    **params: Any,
) -> str:
    raw_return_url = ""

    if hasattr(submitted_form, "get"):
        raw_return_url = str(submitted_form.get("return_url") or "").strip()

    safe_return_url = _sanitize_users_new_return_url_post_save_v4(
        raw_return_url,
        params,
    )

    if safe_return_url:
        return safe_return_url

    return _append_after_save_marker_to_users_new_url_v4(
        build_users_new_url(**params)
    )
# APPVERBO_RETURN_URL_POST_SAVE_V4_END


# APPVERBO_BACKEND_RETURN_URL_POST_SAVE_V6_START
def _sanitize_users_new_return_url_post_save_v6(
    raw_return_url: Any,
    extra_params: dict[str, Any] | None = None,
) -> str:
    clean_return_url = str(raw_return_url or "").strip()

    if not clean_return_url:
        return ""

    try:
        parsed_url = urlsplit(clean_return_url)
    except Exception:
        return ""

    if parsed_url.scheme or parsed_url.netloc:
        return ""

    path = parsed_url.path or "/users/new"

    if path != "/users/new":
        return ""

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))

    for raw_key, raw_value in (extra_params or {}).items():
        clean_key = str(raw_key or "").strip()
        clean_value = str(raw_value or "").strip()

        if clean_key and clean_value:
            query_params[clean_key] = clean_value

    query_params["appverbo_after_save"] = "1"

    query_string = urlencode(query_params)
    fragment = f"#{parsed_url.fragment}" if parsed_url.fragment else ""

    return f"{path}?{query_string}{fragment}" if query_string else f"{path}{fragment}"


def _append_after_save_marker_to_users_new_url_v6(raw_url: str) -> str:
    clean_url = str(raw_url or "").strip()

    if not clean_url:
        return clean_url

    try:
        parsed_url = urlsplit(clean_url)
    except Exception:
        return clean_url

    if parsed_url.scheme or parsed_url.netloc:
        return clean_url

    path = parsed_url.path or "/users/new"

    if path != "/users/new":
        return clean_url

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
    query_params["appverbo_after_save"] = "1"

    query_string = urlencode(query_params)
    fragment = f"#{parsed_url.fragment}" if parsed_url.fragment else ""

    return f"{path}?{query_string}{fragment}" if query_string else f"{path}{fragment}"


def _build_post_save_redirect_url_v6(
    submitted_form: Any,
    **params: Any,
) -> str:
    raw_return_url = ""

    if hasattr(submitted_form, "get"):
        raw_return_url = str(submitted_form.get("return_url") or "").strip()

    return _build_post_save_redirect_url_from_raw_return_url_v6(
        raw_return_url,
        **params,
    )


def _build_post_save_redirect_url_from_raw_return_url_v6(
    raw_return_url: Any,
    **params: Any,
) -> str:
    clean_raw_return_url = str(raw_return_url or "").strip()

    safe_return_url = _sanitize_users_new_return_url_post_save_v6(
        clean_raw_return_url,
        params,
    )

    if safe_return_url:
        return safe_return_url

    normalized_params = dict(params)

    has_profile_context = any(
        str(normalized_params.get(key) or "").strip()
        for key in (
            "profile_success",
            "profile_error",
            "profile_tab",
            "profile_section",
        )
    )

    if has_profile_context:
        normalized_params.setdefault("menu", MENU_MEU_PERFIL_KEY)
        normalized_params.setdefault("target", "#perfil-pessoal-card")
        normalized_params.setdefault("profile_tab", "pessoal")

    return _append_after_save_marker_to_users_new_url_v6(
        build_users_new_url(**normalized_params)
    )


def _build_post_save_stable_url_from_raw_return_url_v1(
    raw_return_url: Any,
    **params: Any,
) -> str:
    clean_raw_return_url = str(raw_return_url or "").strip()

    if clean_raw_return_url:
        try:
            parsed_url = urlsplit(clean_raw_return_url)
        except Exception:
            parsed_url = None

        if (
            parsed_url is not None
            and not parsed_url.scheme
            and not parsed_url.netloc
            and (parsed_url.path or "/users/new") == "/users/new"
        ):
            query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
            query_params.pop("appverbo_after_save", None)
            query_params.pop("profile_success", None)
            query_params.pop("profile_error", None)

            for raw_key, raw_value in params.items():
                clean_key = str(raw_key or "").strip()
                clean_value = str(raw_value or "").strip()
                if not clean_key:
                    continue
                if clean_value:
                    query_params[clean_key] = clean_value
                else:
                    query_params.pop(clean_key, None)

            clean_target = str(query_params.get("target") or "").strip()
            query_string = urlencode(query_params)
            fragment = clean_target if clean_target.startswith("#") else (
                f"#{parsed_url.fragment}" if parsed_url.fragment else ""
            )

            return (
                f"/users/new?{query_string}{fragment}"
                if query_string
                else f"/users/new{fragment}"
            )

    return build_users_new_url(**params)


def _build_post_save_stable_url_v1(
    submitted_form: Any,
    **params: Any,
) -> str:
    raw_return_url = ""

    if hasattr(submitted_form, "get"):
        raw_return_url = str(submitted_form.get("return_url") or "").strip()

    return _build_post_save_stable_url_from_raw_return_url_v1(
        raw_return_url,
        **params,
    )


def _is_dynamic_process_silent_refresh_request_v1(request: Request) -> bool:
    clean_header = str(request.headers.get("x-appverbo-silent-refresh") or "").strip()
    if clean_header == "1":
        return True

    requested_with = str(request.headers.get("x-requested-with") or "").strip().lower()
    return requested_with == "xmlhttprequest"


def _build_dynamic_process_runtime_snapshot_v1(
    *,
    clean_menu_key: str,
    process_setting: dict[str, Any],
    existing_profile_fields: dict[str, str],
    history_rows_override: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    visible_rows = (
        process_setting.get("process_visible_field_rows")
        if isinstance(process_setting.get("process_visible_field_rows"), list)
        else []
    )
    values_by_field: dict[str, str] = {}
    for raw_row in visible_rows:
        if not isinstance(raw_row, dict):
            continue
        field_key = str(raw_row.get("field_key") or "").strip().lower()
        if not field_key:
            continue
        storage_key = build_menu_process_field_storage_key(clean_menu_key, field_key)
        if not storage_key:
            continue
        storage_value = existing_profile_fields.get(storage_key)
        if storage_value is None:
            continue
        values_by_field[field_key] = str(storage_value)

    quantity_values_by_rule: dict[str, list[dict[str, str]]] = {}
    for quantity_rule in process_setting.get("process_quantity_fields") or []:
        if not isinstance(quantity_rule, dict):
            continue
        rule_key = str(quantity_rule.get("key") or "").strip().lower()
        if not rule_key:
            continue
        quantity_storage_key = build_menu_process_quantity_storage_key(clean_menu_key, rule_key)
        if not quantity_storage_key:
            continue
        quantity_values = parse_menu_process_quantity_values(
            existing_profile_fields.get(quantity_storage_key)
        )
        if quantity_values:
            quantity_values_by_rule[rule_key] = quantity_values

    history_rows: list[dict[str, Any]] = []
    if isinstance(history_rows_override, list):
        history_rows = [
            dict(raw_row)
            for raw_row in history_rows_override
            if isinstance(raw_row, dict)
        ]
    else:
        history_storage_key = build_menu_process_records_storage_key(clean_menu_key)
        if history_storage_key:
            history_rows = parse_menu_process_records(
                existing_profile_fields.get(history_storage_key)
            )

    return {
        "values_by_field": values_by_field,
        "quantity_values_by_rule": quantity_values_by_rule,
        "history_rows": history_rows,
    }


def _build_dynamic_process_silent_refresh_payload_v1(
    *,
    submitted_form: Any,
    clean_menu_key: str,
    requested_section_key: str,
    process_setting: dict[str, Any],
    existing_profile_fields: dict[str, str],
    success_message: str,
    history_rows_override: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    runtime_snapshot = _build_dynamic_process_runtime_snapshot_v1(
        clean_menu_key=clean_menu_key,
        process_setting=process_setting,
        existing_profile_fields=existing_profile_fields,
        history_rows_override=history_rows_override,
    )
    clean_section_key = str(requested_section_key or "").strip()
    redirect_url = _build_post_save_redirect_url_v6(
        submitted_form,
        menu=clean_menu_key,
        profile_success=success_message,
    )
    stable_url = _build_post_save_stable_url_v1(
        submitted_form,
        menu=clean_menu_key,
        target="#dynamic-process-card",
        dynamic_process_section=clean_section_key,
        section_key=clean_section_key,
    )

    return {
        "success": True,
        "message": success_message,
        "menuKey": clean_menu_key,
        "sectionKey": clean_section_key,
        "redirectUrl": redirect_url,
        "stableUrl": stable_url,
        "valuesByField": runtime_snapshot["values_by_field"],
        "quantityValuesByRule": runtime_snapshot["quantity_values_by_rule"],
        "historyRows": runtime_snapshot["history_rows"],
    }
# APPVERBO_BACKEND_RETURN_URL_POST_SAVE_V6_END


# ###################################################################################
# (MUSICAS) PERSISTENCIA DEDICADA POR ENTIDADE
# ###################################################################################

def _handle_song_process_submission_v1(
    *,
    request: Request,
    session: Session,
    current_user: dict[str, Any],
    submitted_form: Any,
    clean_menu_key: str,
    process_setting: dict[str, Any],
    requested_history_action: str,
    requested_history_record_id: str,
    active_section_field_keys: list[str],
    field_meta_by_key: dict[str, dict[str, Any]],
) -> RedirectResponse:
    resolved_entity_id, resolve_entity_error = _resolve_selected_entity_id_for_process_v1(
        request,
        session,
        current_user,
    )
    if resolve_entity_error:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_error=resolve_entity_error,
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    song_field_mapping = build_song_field_mapping_v1(process_setting)
    required_roles = {
        "name": "Nome da música",
        "version": "Versão",
        "youtube_url": "URL do YouTube",
        "lyrics": "Letra",
        "lyrics_source": "Fonte da letra",
        "lyrics_status": "Estado da letra",
    }

    if requested_history_action == "delete":
        try:
            parsed_song_id = int(str(requested_history_record_id or "").strip())
        except (TypeError, ValueError):
            parsed_song_id = 0
        if parsed_song_id <= 0:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    menu=clean_menu_key,
                    profile_error="Música inválida para eliminar.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        target_song = get_song_by_id_v1(session, int(resolved_entity_id), parsed_song_id)
        if target_song is None:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    menu=clean_menu_key,
                    profile_error="Música não encontrada para eliminar.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        if bool(target_song.is_active):
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    menu=clean_menu_key,
                    profile_error="Somente músicas inativas podem ser eliminadas.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        session.delete(target_song)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    menu=clean_menu_key,
                    profile_error="Falha ao eliminar a música.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_success="Música eliminada com sucesso.",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    missing_roles = [
        role_label
        for role_key, role_label in required_roles.items()
        if not str(song_field_mapping.get(role_key) or "").strip()
    ]
    if missing_roles:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_error="Configuração incompleta do processo Músicas: " + ", ".join(missing_roles) + ".",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    submitted_values_by_field: dict[str, str] = {}
    for field_key in active_section_field_keys:
        field_meta = field_meta_by_key.get(field_key) or {}
        field_type = _normalize_process_field_type(field_meta.get("field_type"))
        field_size = _normalize_process_field_size(field_meta.get("size"), field_type)
        input_name = f"process_field__{field_key}"
        if field_type == "flag":
            submitted_values_by_field[field_key] = (
                "1" if str(submitted_form.get(input_name) or "").strip() == "1" else "0"
            )
            continue
        clean_value = str(submitted_form.get(input_name) or "").strip()
        if isinstance(field_size, int) and field_size > 0:
            clean_value = clean_value[:field_size]
        submitted_values_by_field[field_key] = clean_value

    clean_name = str(submitted_values_by_field.get(song_field_mapping["name"]) or "").strip()
    clean_version = str(submitted_values_by_field.get(song_field_mapping["version"]) or "").strip()
    clean_youtube_url = str(submitted_values_by_field.get(song_field_mapping["youtube_url"]) or "").strip()
    clean_lyrics = str(submitted_values_by_field.get(song_field_mapping["lyrics"]) or "").strip()
    clean_source = normalize_song_lyrics_source_v1(
        submitted_values_by_field.get(song_field_mapping["lyrics_source"])
    )
    clean_status = normalize_song_lyrics_status_v1(
        submitted_values_by_field.get(song_field_mapping["lyrics_status"])
    )
    song_ai_lyrics_generated = str(submitted_form.get("song_ai_lyrics_generated") or "").strip().lower() in {
        "1",
        "true",
        "sim",
        "yes",
        "on",
    }

    missing_labels: list[str] = []
    if not clean_name:
        missing_labels.append("Nome da música")
    if not clean_version:
        missing_labels.append("Versão")
    if not clean_youtube_url:
        missing_labels.append("URL do YouTube")
    if not clean_lyrics:
        missing_labels.append("Letra")
    if missing_labels:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_error="Preencha os campos obrigatórios: " + ", ".join(missing_labels) + ".",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if song_ai_lyrics_generated:
        clean_source = "audio_transcription"
        clean_status = "rascunho"
    elif not clean_source:
        clean_source = "manual"
    elif clean_source == "audio_transcription" and requested_history_action == "create":
        clean_status = "rascunho"

    song_is_active = _normalize_process_state(submitted_form.get("process_state")) == "ativo"

    song_for_save: Song | None = None
    if requested_history_action == "update":
        try:
            parsed_song_id = int(str(requested_history_record_id or "").strip())
        except (TypeError, ValueError):
            parsed_song_id = 0
        if parsed_song_id <= 0:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    menu=clean_menu_key,
                    profile_error="Música inválida para editar.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        song_for_save = get_song_by_id_v1(session, int(resolved_entity_id), parsed_song_id)
        if song_for_save is None:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    menu=clean_menu_key,
                    profile_error="Música não encontrada para editar.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
    else:
        song_for_save = Song(entity_id=int(resolved_entity_id))
        session.add(song_for_save)

    song_for_save.name = clean_name
    song_for_save.version = clean_version
    song_for_save.youtube_url = clean_youtube_url
    song_for_save.lyrics = clean_lyrics
    song_for_save.lyrics_source = clean_source
    song_for_save.lyrics_status = clean_status
    song_for_save.is_active = bool(song_is_active)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_error="Falha ao gravar os dados da música.",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    success_message = (
        "Música atualizada com sucesso."
        if requested_history_action == "update"
        else "Música criada com sucesso."
    )
    return RedirectResponse(
        url=_build_post_save_redirect_url_v6(
            submitted_form,
            menu=clean_menu_key,
            profile_success=success_message,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ###################################################################################
# (CONTACTO GERAL) IMPORTACAO MASSIVA DE DADOS DE MEMBRESIA
# ###################################################################################

def _resolve_contact_membership_import_config_v1(
    menu_key: str,
    process_setting: dict[str, Any],
    requested_section_key: str,
    field_meta_by_key: dict[str, dict[str, Any]],
    field_section_map: dict[str, str],
) -> dict[str, str]:
    if _normalize_lookup_text(menu_key) != "contacto_geral":
        return {}

    options_by_key = {
        str((raw_option or {}).get("key") or "").strip().lower(): (raw_option or {})
        for raw_option in (process_setting.get("process_field_options") or [])
        if str((raw_option or {}).get("key") or "").strip()
    }
    header_labels_by_key = {
        option_key: str((raw_option or {}).get("label") or "").strip()
        for option_key, raw_option in options_by_key.items()
        if str((raw_option or {}).get("field_type") or "").strip().lower() == "header"
    }

    input_section_key = ""
    target_section_key = ""
    upload_field_key = ""
    name_field_key = ""
    phone_field_key = ""
    email_field_key = ""

    for header_key, header_label in header_labels_by_key.items():
        joined_lookup = " ".join(
            part
            for part in (
                _normalize_lookup_text(header_key),
                _normalize_lookup_text(header_label),
            )
            if part
        )
        if not input_section_key and "input ficheiro" in joined_lookup:
            input_section_key = header_key
        if not target_section_key and "dados membresia" in joined_lookup:
            target_section_key = header_key

    if not input_section_key or not target_section_key:
        return {}
    if str(requested_section_key or "").strip().lower() != input_section_key:
        return {}

    for field_key, field_meta in (field_meta_by_key or {}).items():
        section_key = str(field_section_map.get(field_key) or "").strip().lower()
        label_lookup = " ".join(
            part
            for part in (
                _normalize_lookup_text(field_key),
                _normalize_lookup_text(field_meta.get("label")),
            )
            if part
        )
        if section_key == input_section_key and not upload_field_key and "ficheiro" in label_lookup:
            upload_field_key = field_key
            continue
        if section_key != target_section_key:
            continue
        if not name_field_key and "nome" in label_lookup:
            name_field_key = field_key
            continue
        if not phone_field_key and ("telefone" in label_lookup or "telemovel" in label_lookup or "celular" in label_lookup):
            phone_field_key = field_key
            continue
        if not email_field_key and "email" in label_lookup:
            email_field_key = field_key

    if not upload_field_key or not name_field_key or not phone_field_key or not email_field_key:
        return {}

    return {
        "input_section_key": input_section_key,
        "target_section_key": target_section_key,
        "upload_field_key": upload_field_key,
        "name_field_key": name_field_key,
        "phone_field_key": phone_field_key,
        "email_field_key": email_field_key,
    }


async def _handle_contact_membership_import_v1(
    *,
    session: Session,
    submitted_form: Any,
    member: Member,
    clean_menu_key: str,
    import_config: dict[str, str],
    existing_profile_fields: dict[str, str],
    existing_records: list[dict[str, Any]],
    records_storage_key: str,
    active_entity_internal_number: str | None = None,
) -> RedirectResponse:
    upload_field_key = str(import_config.get("upload_field_key") or "").strip().lower()
    target_section_key = str(import_config.get("target_section_key") or "").strip()
    input_section_key = str(import_config.get("input_section_key") or "").strip()
    if not upload_field_key or not target_section_key or not records_storage_key:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_error="Configuração incompleta para importação de contactos.",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    raw_upload_file = submitted_form.get(f"process_field__{upload_field_key}")
    upload_filename = str(getattr(raw_upload_file, "filename", "") or "").strip()
    if not upload_filename:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_error="Selecione um ficheiro CSV ou XLSX para importar.",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        import_result = await parse_contact_membership_import_file_v1(raw_upload_file)
    except ValueError as exc:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_error=str(exc),
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    imported_rows = list(import_result.get("rows") or [])
    skipped_rows = int(import_result.get("skipped_rows") or 0)
    if not imported_rows:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_error="Nenhuma linha válida foi encontrada no ficheiro enviado.",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    timestamp_label = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    name_field_key = str(import_config.get("name_field_key") or "").strip().lower()
    phone_field_key = str(import_config.get("phone_field_key") or "").strip().lower()
    email_field_key = str(import_config.get("email_field_key") or "").strip().lower()

    for imported_row in imported_rows:
        row_values = {
            name_field_key: str(imported_row.get("name") or "").strip(),
            phone_field_key: str(imported_row.get("phone") or "").strip(),
            email_field_key: str(imported_row.get("email") or "").strip(),
            "__estado": "ativo",
        }
        if active_entity_internal_number is not None:
            row_values["custom_n_cliente"] = active_entity_internal_number

        existing_records.append(
            {
                "record_id": uuid4().hex,
                "created_at": timestamp_label,
                "section_key": target_section_key,
                "values": row_values,
            }
        )

    input_values = {
        upload_field_key: f"{upload_filename} ({len(imported_rows)} importados)",
        "__estado": "ativo",
    }
    if active_entity_internal_number is not None:
        input_values["custom_n_cliente"] = active_entity_internal_number

    existing_records.append(
        {
            "record_id": uuid4().hex,
            "created_at": timestamp_label,
            "section_key": input_section_key,
            "values": input_values,
        }
    )

    serialized_records = serialize_menu_process_records(existing_records)
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
            url=_build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_error="Falha ao importar os dados do ficheiro.",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    success_message = f"{len(imported_rows)} dados de membresia importados com sucesso."
    if skipped_rows > 0:
        success_message += f" {skipped_rows} linhas foram ignoradas."

    redirect_url = _append_after_save_marker_to_users_new_url_v6(
        build_users_new_url(
            menu=clean_menu_key,
            target="#dynamic-process-card",
            dynamic_process_section=target_section_key,
            section_key=target_section_key,
            profile_success=success_message,
        )
    )
    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/users/profile/personal")
async def update_personal_profile(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
    # APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V2_START
    _write_meu_perfil_save_debug_log_v2(
        request,
        submitted_form,
        "01_form_received",
        {
            "message": "Formulario recebido no endpoint /users/profile/personal antes de qualquer processamento.",
        },
    )
    # APPVERBO_MEU_PERFIL_SAVE_LOGGER_FORM_RECEIVED_V2_END


    # APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START
    # Este endpoint grava sempre dados do Meu perfil. Depois de gravar,
    # o utilizador deve continuar no Meu perfil e na aba onde estava.
    redirect_menu = MENU_MEU_PERFIL_KEY
    redirect_target = str(submitted_form.get("target") or "#perfil-pessoal-card").strip() or "#perfil-pessoal-card"
    redirect_profile_section = str(submitted_form.get("profile_section") or "").strip().lower()
    # APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_END
    def _form_has_field_v1(field_name: str) -> bool:
        try:
            return field_name in submitted_form
        except Exception:
            return False

    def _date_to_pt_text_v1(raw_date: date | None) -> str:
        if raw_date is None:
            return ""
        return raw_date.strftime("%d/%m/%Y")

    has_full_name = _form_has_field_v1("full_name")
    has_primary_phone = _form_has_field_v1("primary_phone")
    has_login_email = _form_has_field_v1("login_email") or _form_has_field_v1("email")
    has_country = _form_has_field_v1("country")
    has_birth_date = _form_has_field_v1("birth_date")
    has_whatsapp_notice_opt_in = _form_has_field_v1("whatsapp_notice_opt_in")

    submitted_full_name = str(submitted_form.get("full_name") or "").strip()
    submitted_primary_phone = str(submitted_form.get("primary_phone") or "").strip()
    submitted_login_email = str(
        submitted_form.get("login_email") or submitted_form.get("email") or ""
    ).strip().lower()
    submitted_country = str(submitted_form.get("country") or "").strip()
    submitted_birth_date = str(submitted_form.get("birth_date") or "").strip()
    submitted_whatsapp_notice_opt_in = str(submitted_form.get("whatsapp_notice_opt_in") or "").strip()

    clean_full_name = ""
    clean_primary_phone = ""
    clean_login_email = ""
    clean_country = ""
    clean_birth_date = ""
    parsed_birth_date: date | None = None
    parsed_whatsapp_notice_opt_in = False

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
                url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        user_account = session.get(User, current_user["id"])
        if user_account is None:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Conta de utilizador não encontrada.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # ###################################################################################
        # (MEU_PERFIL) PERMITIR GRAVACAO POR ABA
        # ###################################################################################
        clean_full_name = (
            submitted_full_name
            if has_full_name
            else str(member.full_name or "").strip()
        )
        clean_primary_phone = (
            submitted_primary_phone
            if has_primary_phone
            else str(member.primary_phone or "").strip()
        )
        clean_login_email = (
            submitted_login_email
            if has_login_email
            else str(user_account.login_email or member.email or "").strip().lower()
        )
        clean_country = (
            submitted_country
            if has_country
            else str(member.country or "").strip()
        )

        if has_birth_date:
            clean_birth_date = submitted_birth_date
            try:
                parsed_birth_date = parse_optional_date_pt(clean_birth_date)
            except ValueError:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(
                        submitted_form,
                        profile_error="Data de nascimento inválida. Use o formato dd/mm/aaaa.",
                        profile_tab="pessoal",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
        else:
            parsed_birth_date = member.birth_date
            clean_birth_date = _date_to_pt_text_v1(parsed_birth_date)

        parsed_whatsapp_notice_opt_in = bool(member.whatsapp_notice_opt_in)
        if has_whatsapp_notice_opt_in:
            parsed_whatsapp_notice_opt_in = submitted_whatsapp_notice_opt_in == "1"
        elif (
            has_full_name
            or has_primary_phone
            or has_login_email
            or has_country
            or has_birth_date
        ):
            parsed_whatsapp_notice_opt_in = False

        if not clean_full_name:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    profile_error="Nome completo é obrigatório.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not clean_primary_phone:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    profile_error="Telefone principal é obrigatório.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not clean_login_email:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    profile_error="Email é obrigatório.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if "@" not in clean_login_email:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    profile_error="Email inválido.",
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
                url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Este email já está associado a outro utilizador.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        sidebar_menu_settings = get_sidebar_menu_settings(
            session,
            selected_entity_id=get_session_entity_id(request),
        )
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
        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V2_START
        _write_meu_perfil_save_debug_log_v2(
            request,
            submitted_form,
            "02_quantity_context_loaded",
            {
                "current_user_id": current_user.get("id") if isinstance(current_user, dict) else None,
                "member_id": getattr(member, "id", None),
                "quantity_rules": quantity_rules,
                "quantity_repeated_field_keys": sorted(list(quantity_repeated_field_keys)),
                "process_options_count": len(process_options),
            },
        )
        # APPVERBO_MEU_PERFIL_SAVE_LOGGER_QUANTITY_CONTEXT_V2_END


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
        profile_section_order: list[str] = []
        seen_profile_sections: set[str] = set()
        for raw_row in (meu_perfil_setting or {}).get("process_visible_field_rows", []):
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            if not field_key:
                continue
            header_key = str(raw_row.get("header_key") or "").strip().lower()
            visible_field_section_map[field_key] = header_key
            if header_key and header_key not in seen_profile_sections:
                seen_profile_sections.add(header_key)
                profile_section_order.append(header_key)

        default_profile_section_key = profile_section_order[0] if profile_section_order else ""
        active_profile_section_key = str(redirect_profile_section or "").strip().lower()
        if (
            active_profile_section_key
            and profile_section_order
            and active_profile_section_key not in seen_profile_sections
        ):
            active_profile_section_key = default_profile_section_key
        if not active_profile_section_key:
            active_profile_section_key = default_profile_section_key

        # ###################################################################################
        # (MEU_PERFIL) ALINHAR MAPA DE ABA COM A UI (FALLBACK PARA A PRIMEIRA ABA)
        # ###################################################################################
        if default_profile_section_key:
            for option_key in option_keys:
                clean_option_key = str(option_key or "").strip().lower()
                if not clean_option_key:
                    continue
                current_section_key = str(
                    visible_field_section_map.get(clean_option_key) or ""
                ).strip().lower()
                if not current_section_key:
                    visible_field_section_map[clean_option_key] = default_profile_section_key

        all_visible_custom_keys = [
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
        visible_custom_keys = list(all_visible_custom_keys)
        if active_profile_section_key:
            visible_custom_keys = [
                clean_key
                for clean_key in visible_custom_keys
                if str(visible_field_section_map.get(clean_key) or "").strip().lower()
                == active_profile_section_key
            ]
        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        existing_custom_fields = {
            key: value
            for key, value in existing_profile_fields.items()
            if key.startswith("custom_")
        }

        current_meu_perfil_values: dict[str, str] = {
            "nome": clean_full_name,
            "telefone": clean_primary_phone,
            "email": clean_login_email,
            "pais": clean_country,
            "data_nascimento": clean_birth_date,
            "autorizacao_whatsapp": "1" if parsed_whatsapp_notice_opt_in else "0",
        }
        for custom_key in all_visible_custom_keys:
            field_name = f"custom_field__{custom_key}"
            field_meta = custom_field_meta.get(custom_key) or {}
            field_type = str(field_meta.get("field_type") or "text").strip().lower()
            if field_type == "flag":
                if field_name in submitted_form:
                    current_meu_perfil_values[custom_key] = (
                        "1" if str(submitted_form.get(field_name) or "").strip() == "1" else "0"
                    )
                else:
                    current_meu_perfil_values[custom_key] = str(
                        existing_custom_fields.get(custom_key) or "0"
                    ).strip() or "0"
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
            clean_custom_value = ", ".join(clean_values)
            if clean_custom_value:
                current_meu_perfil_values[custom_key] = clean_custom_value
            else:
                current_meu_perfil_values[custom_key] = str(
                    existing_custom_fields.get(custom_key) or ""
                ).strip()
        meu_perfil_subsequent_rules = _resolve_process_subsequent_rules_from_setting_v1(
            meu_perfil_setting
        )
        hidden_meu_perfil_targets = get_hidden_process_targets_from_rules(
            meu_perfil_subsequent_rules,
            current_meu_perfil_values,
        )
        visible_custom_keys_set = set(visible_custom_keys)
        active_custom_keys = filter_process_fields_by_hidden_targets(
            visible_custom_keys,
            hidden_meu_perfil_targets,
            visible_field_section_map,
        )
        active_custom_keys_set = set(active_custom_keys)
        submitted_custom_values_by_key: dict[str, str] = {}
        submitted_custom_presence: set[str] = set()
        for custom_key in all_visible_custom_keys:
            field_name = f"custom_field__{custom_key}"
            field_meta = custom_field_meta.get(custom_key) or {}
            field_type = str(field_meta.get("field_type") or "text").strip().lower()
            field_size = field_meta.get("size")

            if field_type == "flag":
                if field_name in submitted_form:
                    submitted_custom_presence.add(custom_key)
                    submitted_custom_values_by_key[custom_key] = (
                        "1" if str(submitted_form.get(field_name) or "").strip() == "1" else "0"
                    )
                continue

            if hasattr(submitted_form, "getlist"):
                raw_submitted_values = submitted_form.getlist(field_name)
            else:
                raw_submitted_values = [submitted_form.get(field_name)]

            has_submitted_value = (
                field_name in submitted_form
                or any(raw_value is not None for raw_value in raw_submitted_values)
            )
            if has_submitted_value:
                submitted_custom_presence.add(custom_key)

            submitted_values = [
                str(raw_value or "").strip()
                for raw_value in raw_submitted_values
            ]
            clean_values = [value for value in submitted_values if value]
            if isinstance(field_size, int) and field_size > 0:
                clean_values = [value[:field_size] for value in clean_values]
            clean_custom_value = ", ".join(clean_values)

            if clean_custom_value:
                submitted_custom_values_by_key[custom_key] = clean_custom_value

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
            field_meta = custom_field_meta.get(custom_key) or {}
            field_type = str(field_meta.get("field_type") or "text").strip().lower()
            field_required = bool(field_meta.get("is_required"))
            if field_type == "flag":
                if custom_key in submitted_custom_presence:
                    updated_custom_fields[custom_key] = submitted_custom_values_by_key.get(custom_key, "0")
                else:
                    updated_custom_fields[custom_key] = str(
                        existing_custom_fields.get(custom_key) or "0"
                    ).strip() or "0"
                continue

            clean_custom_value = submitted_custom_values_by_key.get(custom_key, "")
            if field_required and not clean_custom_value:
                field_label = option_labels_by_key.get(custom_key) or custom_key
                if field_label not in missing_required_custom_labels:
                    missing_required_custom_labels.append(field_label)
                continue
            if clean_custom_value:
                updated_custom_fields[custom_key] = clean_custom_value

        # APPVERBO_MEU_PERFIL_CLEAR_HIDDEN_SUBSEQUENT_VALUES_V1_START
        # Quando um campo fica oculto por regra de Campos Subsequentes,
        # o valor antigo deve ser removido para não apresentar informação incorreta.
        for hidden_custom_key in visible_custom_keys:
            if hidden_custom_key in active_custom_keys_set:
                continue

            updated_custom_fields.pop(hidden_custom_key, None)
        # APPVERBO_MEU_PERFIL_CLEAR_HIDDEN_SUBSEQUENT_VALUES_V1_END

        # APPVERBO_MEU_PERFIL_PERSIST_SUBMITTED_FIELDS_V1_START
        # Preserva campos efetivamente submetidos mesmo quando profile_section chega desalinhado.
        # Mantem a prioridade da regra de campos subsequentes ocultos.
        for submitted_custom_key, submitted_custom_value in submitted_custom_values_by_key.items():
            if submitted_custom_key not in visible_custom_keys_set:
                continue
            if submitted_custom_key in hidden_meu_perfil_targets:
                continue
            if not submitted_custom_value:
                continue
            updated_custom_fields[submitted_custom_key] = submitted_custom_value
        # APPVERBO_MEU_PERFIL_PERSIST_SUBMITTED_FIELDS_V1_END

        active_quantity_rule_keys: set[str] = set()
        for quantity_rule in quantity_rules:
            rule_key = str(quantity_rule.get("key") or "").strip().lower()
            rule_header_key = str(quantity_rule.get("header_key") or "").strip().lower()
            quantity_field_key = str(quantity_rule.get("quantity_field_key") or "").strip().lower()
            if not rule_key or not quantity_field_key:
                continue

            applies_to_current_section = True
            if active_profile_section_key:
                quantity_field_section_key = str(
                    visible_field_section_map.get(quantity_field_key) or ""
                ).strip().lower()
                if rule_header_key:
                    applies_to_current_section = (
                        rule_header_key == active_profile_section_key
                    )
                elif quantity_field_section_key:
                    applies_to_current_section = (
                        quantity_field_section_key == active_profile_section_key
                    )

            if not applies_to_current_section:
                continue

            if (
                quantity_field_key in hidden_meu_perfil_targets
                or visible_field_section_map.get(quantity_field_key) in hidden_meu_perfil_targets
            ):
                storage_key = build_menu_process_quantity_storage_key(MENU_MEU_PERFIL_KEY, rule_key)

                if storage_key:
                    updated_quantity_values.pop(storage_key, None)

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
                url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Preencha os campos obrigatórios: " + ", ".join(missing_required_custom_labels) + ".",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )


        # APPVERBO_MEU_PERFIL_QUANTITY_PERSISTENCE_V1_START
        # Reforco de persistencia dos Campos Quantidade do Meu perfil.
        #
        # O frontend envia:
        #   process_quantity_payload__<rule_key> = JSON array
        #
        # O valor deve ficar em Member.profile_custom_fields com a chave:
        #   quantity__meu_perfil__<rule_key>
        #
        # Este bloco e intencionalmente executado imediatamente antes de regravar
        # existing_profile_fields, para garantir que o ultimo payload submetido
        # prevalece sobre valores antigos.
        for quantity_rule in quantity_rules:
            rule_key = str(quantity_rule.get("key") or "").strip().lower()
            if not rule_key:
                continue
            if rule_key not in active_quantity_rule_keys:
                continue

            storage_key = build_menu_process_quantity_storage_key(
                MENU_MEU_PERFIL_KEY,
                rule_key,
            )
            if not storage_key:
                continue

            payload_field_name = f"process_quantity_payload__{rule_key}"
            payload_was_submitted = payload_field_name in submitted_form

            parsed_quantity_items = _resolve_submitted_process_quantity_items(
                submitted_form,
                rule_key,
            )

            allowed_repeated_fields = {
                str(field_key or "").strip().lower()
                for field_key in quantity_rule.get("repeated_field_keys", [])
                if str(field_key or "").strip()
            }

            try:
                max_quantity_items = int(str(quantity_rule.get("max_items") or "1").strip())
            except (TypeError, ValueError):
                max_quantity_items = 1

            max_quantity_items = max(1, min(max_quantity_items, 50))

            cleaned_quantity_items: list[dict[str, str]] = []

            for raw_item in parsed_quantity_items[:max_quantity_items]:
                if not isinstance(raw_item, dict):
                    continue

                clean_item: dict[str, str] = {}

                for raw_field_key, raw_field_value in raw_item.items():
                    clean_field_key = str(raw_field_key or "").strip().lower()
                    clean_field_value = str(raw_field_value or "").strip()

                    if not clean_field_key or clean_field_key not in allowed_repeated_fields:
                        continue

                    if not clean_field_value:
                        continue

                    clean_item[clean_field_key] = clean_field_value

                if clean_item:
                    cleaned_quantity_items.append(clean_item)

            serialized_quantity_items = serialize_menu_process_quantity_values(
                cleaned_quantity_items
            )

            if serialized_quantity_items:
                updated_quantity_values[storage_key] = serialized_quantity_items
            elif payload_was_submitted:
                updated_quantity_values.pop(storage_key, None)
        # APPVERBO_MEU_PERFIL_QUANTITY_PERSISTENCE_V1_END


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
                url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Falha ao gravar dados pessoais.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    request.session["user_name"] = clean_full_name
    request.session["login_email"] = clean_login_email
    request.session["user_email"] = clean_login_email
    return RedirectResponse(
        url=_build_post_save_redirect_url_v6(submitted_form, profile_success="Dados pessoais atualizados com sucesso.",
            profile_tab="pessoal",
            menu=redirect_menu,
            target=redirect_target,
            profile_section=redirect_profile_section,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/users/profile/process-data")
async def update_dynamic_process_profile(request: Request):
    submitted_form = await request.form()
    clean_menu_key = resolve_menu_key_alias(submitted_form.get("menu_key"))
    requested_section_key = str(submitted_form.get("section_key") or "").strip()
    requested_history_action = str(submitted_form.get("history_action") or "").strip().lower()
    requested_history_record_id = str(submitted_form.get("history_record_id") or "").strip()
    silent_refresh_requested = _is_dynamic_process_silent_refresh_request_v1(request)
    _write_meu_perfil_process_flow_debug_log_v1(
        request,
        "01_process_form_received",
        submitted_form=submitted_form,
        data={
            "clean_menu_key": clean_menu_key,
            "requested_section_key": requested_section_key,
            "requested_history_action": requested_history_action,
            "requested_history_record_id": requested_history_record_id,
            "return_url": str(submitted_form.get("return_url") or "").strip(),
            "target": str(submitted_form.get("target") or "").strip(),
        },
    )

    if not clean_menu_key:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(submitted_form, menu="home",
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
                url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                    profile_error="Membro associado ao utilizador não encontrado.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        sidebar_menu_settings = get_sidebar_menu_settings(
            session,
            selected_entity_id=get_session_entity_id(request),
        )
        active_entity_id = get_session_entity_id(request)
        active_entity_internal_number = None
        if active_entity_id is not None:
            active_entity_internal_number = session.scalar(
                select(Entity.internal_number).where(Entity.id == active_entity_id)
            )
        if active_entity_internal_number is not None:
            active_entity_internal_number = str(active_entity_internal_number)
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
                url=_build_post_save_redirect_url_v6(submitted_form, menu="home",
                    profile_error="Processo não encontrado.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        visibility_context = build_effective_sidebar_visibility_v1(
            session,
            actor_user_id=int(current_user["id"]),
            actor_login_email=str(current_user.get("login_email") or ""),
            selected_entity_id=get_session_entity_id(request),
            sidebar_menu_settings=sidebar_menu_settings,
        )
        effective_visible_menu_keys = {
            str(raw_key or "").strip().lower()
            for raw_key in (visibility_context.get("visible_sidebar_menu_keys") or [])
            if str(raw_key or "").strip()
        }
        if clean_menu_key not in effective_visible_menu_keys:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    menu="home",
                    profile_error="Sem permissão para aceder a este processo.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        if clean_menu_key == "empresa":
            # ###################################################################################
            # (1) RESOLVER ENTIDADE ATIVA E PERMISSOES
            # ###################################################################################
            selected_entity_id = get_session_entity_id(request)
            entity_permissions = get_user_entity_permissions(
                session,
                int(current_user["id"]),
                str(current_user.get("login_email") or ""),
                selected_entity_id,
            )
            resolved_entity_id = entity_permissions.get("selected_entity_id")

            if resolved_entity_id is None:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(
                        submitted_form,
                        menu=clean_menu_key,
                        profile_error="Nenhuma entidade ativa foi encontrada para atualizar.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            if not is_entity_within_permissions(int(resolved_entity_id), entity_permissions):
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(
                        submitted_form,
                        menu=clean_menu_key,
                        profile_error="Sem permissao para atualizar esta entidade.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            entity = session.get(Entity, int(resolved_entity_id))
            if entity is None:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(
                        submitted_form,
                        menu=clean_menu_key,
                        profile_error="Entidade selecionada nao encontrada.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            # ###################################################################################
            # (2) LER E NORMALIZAR CAMPOS EDITAVEIS DA ABA EMPRESA
            # ###################################################################################
            def _read_empresa_process_field_v1(field_key: str, max_size: int) -> str:
                input_name = f"process_field__{field_key}"
                clean_value = str(submitted_form.get(input_name) or "").strip()
                if max_size > 0:
                    clean_value = clean_value[:max_size]
                return clean_value

            def _optional_or_none_v1(clean_value: str) -> str | None:
                return clean_value or None

            clean_name = _read_empresa_process_field_v1("entity_name", 150)
            clean_acronym = _read_empresa_process_field_v1("entity_acronym", 30)
            clean_tax_id = _read_empresa_process_field_v1("entity_tax_id", 40)
            clean_email = _read_empresa_process_field_v1("entity_email", 150)
            clean_address = _read_empresa_process_field_v1("entity_address", 255)
            clean_door_number = _read_empresa_process_field_v1("entity_door_number", 30)
            clean_freguesia = _read_empresa_process_field_v1("entity_freguesia", 120)
            clean_postal_code = _read_empresa_process_field_v1("entity_postal_code", 30)
            clean_city = _read_empresa_process_field_v1("entity_city", 120)
            clean_country = _read_empresa_process_field_v1("entity_country", 120)
            clean_phone = _read_empresa_process_field_v1("entity_phone", 30)
            clean_responsible_name = _read_empresa_process_field_v1("entity_responsible_name", 200)
            clean_profile_scope_raw = _read_empresa_process_field_v1("entity_profile_scope", 20).lower()
            raw_logo_file = submitted_form.get("process_field__entity_logo_file")
            clean_remove_logo_raw = str(submitted_form.get("process_field__entity_logo_remove") or "").strip().lower()
            remove_logo_requested = clean_remove_logo_raw in {"1", "true", "sim", "yes", "on"}

            clean_profile_scope = ""
            if clean_profile_scope_raw in {"owner", "legado"}:
                clean_profile_scope = clean_profile_scope_raw

            required_empresa_fields_v1: tuple[tuple[str, str], ...] = (
                ("Nome da entidade", clean_name),
                ("Nº Identificação Fiscal", clean_tax_id),
                ("Perfil da entidade", clean_profile_scope),
                ("Email", clean_email),
                ("Telefone", clean_phone),
                ("Nome do responsável", clean_responsible_name),
                ("Morada", clean_address),
                ("Nº da porta", clean_door_number),
                ("Freguesia", clean_freguesia),
                ("Código postal", clean_postal_code),
                ("Cidade", clean_city),
                ("País", clean_country),
            )
            missing_required_labels = [
                label
                for label, clean_value in required_empresa_fields_v1
                if not str(clean_value or "").strip()
            ]
            if missing_required_labels:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(
                        submitted_form,
                        menu=clean_menu_key,
                        profile_error="Preencha os campos obrigatórios: " + ", ".join(missing_required_labels) + ".",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            stored_logo_url = ""
            logo_upload_error = ""
            if raw_logo_file is not None and str(getattr(raw_logo_file, "filename", "") or "").strip():
                stored_logo_url, logo_upload_error = save_entity_logo_upload(raw_logo_file)

            if logo_upload_error:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(
                        submitted_form,
                        menu=clean_menu_key,
                        profile_error=logo_upload_error,
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            current_logo_url = str(entity.logo_url or "").strip()
            delete_old_logo_after_commit = ""

            # ###################################################################################
            # (3) PERSISTIR EM ENTITIES E REDIRECIONAR
            # ###################################################################################
            entity.name = clean_name
            entity.acronym = _optional_or_none_v1(clean_acronym)
            entity.tax_id = _optional_or_none_v1(clean_tax_id)
            entity.email = _optional_or_none_v1(clean_email)
            entity.address = _optional_or_none_v1(clean_address)
            entity.door_number = _optional_or_none_v1(clean_door_number)
            entity.freguesia = _optional_or_none_v1(clean_freguesia)
            entity.postal_code = _optional_or_none_v1(clean_postal_code)
            entity.city = _optional_or_none_v1(clean_city)
            entity.country = _optional_or_none_v1(clean_country)
            entity.phone = _optional_or_none_v1(clean_phone)
            entity.responsible_name = _optional_or_none_v1(clean_responsible_name)
            if stored_logo_url:
                entity.logo_url = stored_logo_url
                if (
                    current_logo_url.startswith("/static/entities/")
                    and current_logo_url != stored_logo_url
                ):
                    delete_old_logo_after_commit = current_logo_url
            elif remove_logo_requested:
                entity.logo_url = None
                if current_logo_url.startswith("/static/entities/"):
                    delete_old_logo_after_commit = current_logo_url

            if bool(entity_permissions.get("can_manage_all_entities")) and clean_profile_scope:
                entity.profile_scope = clean_profile_scope

            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                if stored_logo_url:
                    _remove_local_entity_logo_if_exists_v1(stored_logo_url)
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(
                        submitted_form,
                        menu=clean_menu_key,
                        profile_error="Falha ao atualizar os dados da Empresa.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            if delete_old_logo_after_commit:
                _remove_local_entity_logo_if_exists_v1(delete_old_logo_after_commit)

            raw_session_entity_id = request.session.get("entity_id")
            parsed_session_entity_id = None
            try:
                parsed_session_entity_id = int(raw_session_entity_id)
            except (TypeError, ValueError):
                parsed_session_entity_id = None
            if parsed_session_entity_id == int(entity.id):
                request.session["entity_logo_url"] = str(entity.logo_url or "")

            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    menu=clean_menu_key,
                    profile_success="Dados da Empresa atualizados com sucesso.",
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
        department_history_mode = (
            history_process_mode
            and not absence_process_mode
            and "departamento" in _normalize_lookup_text(
                " ".join(
                    [
                        clean_menu_key,
                        str(process_setting.get("label") or ""),
                        requested_section_key,
                    ]
                )
            )
        )
        record_label_singular = (
            "departamento"
            if department_history_mode
            else ("ausência" if absence_process_mode else "registo")
        )
        process_view_authorization_mode = (
            history_process_mode
            and is_process_view_authorization_section_v1(
                clean_menu_key,
                requested_section_key,
            )
        )
        if requested_history_action not in {"", "create", "update", "delete"}:
            requested_history_action = "create"
        if not history_process_mode:
            requested_history_action = "create"
        process_view_authorization_scope_entity_id = (
            visibility_context.get("selected_entity_id")
            if process_view_authorization_mode
            else None
        )
        if process_view_authorization_mode:
            existing_records = build_process_view_authorization_history_rows_v1(
                session,
                selected_entity_id=process_view_authorization_scope_entity_id,
                section_key=requested_section_key,
            )

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
                url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
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
        contact_membership_import_config = _resolve_contact_membership_import_config_v1(
            clean_menu_key,
            process_setting,
            requested_section_key,
            field_meta_by_key,
            field_section_map,
        )
        if contact_membership_import_config:
            return await _handle_contact_membership_import_v1(
                session=session,
                submitted_form=submitted_form,
                member=member,
                clean_menu_key=clean_menu_key,
                import_config=contact_membership_import_config,
                existing_profile_fields=existing_profile_fields,
                existing_records=existing_records,
                records_storage_key=records_storage_key,
                active_entity_internal_number=active_entity_internal_number,
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

        if is_song_process_menu_v1(
            clean_menu_key,
            process_setting.get("label"),
            requested_section_key,
        ):
            return _handle_song_process_submission_v1(
                request=request,
                session=session,
                current_user=current_user,
                submitted_form=submitted_form,
                clean_menu_key=clean_menu_key,
                process_setting=process_setting,
                requested_history_action=requested_history_action,
                requested_history_record_id=requested_history_record_id,
                active_section_field_keys=active_section_field_keys,
                field_meta_by_key=field_meta_by_key,
            )

        if history_process_mode and requested_history_action == "delete":
            if process_view_authorization_mode:
                if not requested_history_record_id:
                    return RedirectResponse(
                        url=_build_post_save_redirect_url_v6(
                            submitted_form,
                            menu=clean_menu_key,
                            profile_error="Registo inválido para eliminar.",
                        ),
                        status_code=status.HTTP_303_SEE_OTHER,
                    )

                success_message, refreshed_authorization_rows, authorization_error = (
                    delete_process_view_authorization_rule_v1(
                        session,
                        selected_entity_id=process_view_authorization_scope_entity_id,
                        requested_history_record_id=requested_history_record_id,
                        section_key=requested_section_key,
                    )
                )
                if authorization_error:
                    return RedirectResponse(
                        url=_build_post_save_redirect_url_v6(
                            submitted_form,
                            menu=clean_menu_key,
                            profile_error=authorization_error,
                        ),
                        status_code=status.HTTP_303_SEE_OTHER,
                    )

                if silent_refresh_requested:
                    return JSONResponse(
                        _build_dynamic_process_silent_refresh_payload_v1(
                            submitted_form=submitted_form,
                            clean_menu_key=clean_menu_key,
                            requested_section_key=requested_section_key,
                            process_setting=process_setting,
                            existing_profile_fields=existing_profile_fields,
                            success_message=success_message,
                            history_rows_override=refreshed_authorization_rows,
                        ),
                        status_code=status.HTTP_200_OK,
                    )

                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(
                        submitted_form,
                        menu=clean_menu_key,
                        profile_success=success_message,
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            if not requested_history_record_id:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                        profile_error=f"{record_label_singular.capitalize()} inválido para eliminar.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            target_record = next(
                (
                    row
                    for row in existing_records
                    if str(row.get("record_id") or "").strip() == requested_history_record_id
                ),
                None,
            )
            if target_record is None:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                        profile_error=f"{record_label_singular.capitalize()} não encontrado para eliminar.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            if department_history_mode:
                target_values = (
                    target_record.get("values")
                    if isinstance(target_record.get("values"), dict)
                    else {}
                )
                target_state = _normalize_process_state(target_values.get("__estado"))
                if target_state != "inativo":
                    return RedirectResponse(
                        url=_build_post_save_redirect_url_v6(
                            submitted_form,
                            menu=clean_menu_key,
                            profile_error="Somente departamentos inativos podem ser eliminados.",
                        ),
                        status_code=status.HTTP_303_SEE_OTHER,
                    )
                target_department_id = _parse_department_id_value_v1(
                    target_values.get("__department_id")
                )
                target_department_name = _extract_department_name_value_v1(
                    target_values,
                    list(target_values.keys()),
                    field_meta_by_key,
                )
                if target_department_id is not None or target_department_name:
                    resolved_entity_id, resolve_entity_error = (
                        _resolve_selected_entity_id_for_process_v1(
                            request,
                            session,
                            current_user,
                        )
                    )
                    if resolve_entity_error:
                        return RedirectResponse(
                            url=_build_post_save_redirect_url_v6(
                                submitted_form,
                                menu=clean_menu_key,
                                profile_error=resolve_entity_error,
                            ),
                            status_code=status.HTTP_303_SEE_OTHER,
                        )
                    _deactivate_department_for_process_v1(
                        session,
                        entity_id=int(resolved_entity_id),
                        department_id=target_department_id,
                        department_name=target_department_name,
                    )

            filtered_records = [
                row
                for row in existing_records
                if str(row.get("record_id") or "").strip() != requested_history_record_id
            ]

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
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                        profile_error=f"Falha ao eliminar o {record_label_singular}.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            success_message = f"{record_label_singular.capitalize()} eliminado com sucesso."
            if silent_refresh_requested:
                return JSONResponse(
                    _build_dynamic_process_silent_refresh_payload_v1(
                        submitted_form=submitted_form,
                        clean_menu_key=clean_menu_key,
                        requested_section_key=requested_section_key,
                        process_setting=process_setting,
                        existing_profile_fields=existing_profile_fields,
                        success_message=success_message,
                    ),
                    status_code=status.HTTP_200_OK,
                )

            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    menu=clean_menu_key,
                    profile_success=success_message,
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # ── auto-populate entity-number fields before required check ──────────
        # Fields matching the entity number pattern are auto-filled from the session
        # entity even if not present in the submitted form (e.g. when the JS renders
        # them in a different section than the server expects).
        entity_auto_populated_keys: set[str] = set()
        if active_entity_internal_number is not None and history_process_mode and not absence_process_mode:
            for _fk in active_section_field_keys:
                _fm = field_meta_by_key.get(_fk) or {}
                _ft = _normalize_process_field_type(_fm.get("field_type"))
                if _ft in ("flag", "file", "header"):
                    continue
                _input_name = f"process_field__{_fk}"
                if str(submitted_form.get(_input_name) or "").strip():
                    continue  # user submitted a value — don't override
                if _is_entity_number_field_v1(_fk, str(_fm.get("label") or "")):
                    entity_auto_populated_keys.add(_fk)

        missing_required_labels: list[str] = []
        for field_key in active_section_field_keys:
            field_meta = field_meta_by_key.get(field_key) or {}
            field_type = _normalize_process_field_type(field_meta.get("field_type"))
            if field_type == "flag":
                continue
            if not bool(field_meta.get("is_required")):
                continue
            if field_key in entity_auto_populated_keys:
                continue  # will be auto-populated from session entity
            input_name = f"process_field__{field_key}"
            clean_value = str(submitted_form.get(input_name) or "").strip()
            if clean_value:
                continue
            field_label = str(field_meta.get("label") or field_key).strip() or field_key
            if field_label not in missing_required_labels:
                missing_required_labels.append(field_label)
        if missing_required_labels:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
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
                url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                    profile_error="Preencha os campos obrigatórios: " + ", ".join(missing_required_quantity_labels) + ".",
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
            if not clean_value and field_key in entity_auto_populated_keys:
                clean_value = str(active_entity_internal_number or "").strip()
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
                url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                    profile_error=f"Preencha ao menos um campo do {record_label_singular}.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        if history_process_mode and not absence_process_mode:
            submitted_section_values["__estado"] = _normalize_process_state(
                submitted_form.get("process_state")
            )
            if active_entity_internal_number is not None:
                submitted_section_values["__numero_entidade"] = active_entity_internal_number
            if clean_menu_key == "contacto_geral" and active_entity_internal_number is not None:
                submitted_section_values["custom_n_cliente"] = active_entity_internal_number
            if clean_menu_key == "extrato" and active_entity_internal_number is not None:
                submitted_section_values["numero_entidade"] = active_entity_internal_number

            if clean_menu_key == "contacto_geral" and requested_section_key == "custom_dados_membresia":
                if requested_history_action == "update" and requested_history_record_id:
                    # Resolve record_for_update early to preserve its custom_n_user
                    ref_record = next(
                        (
                            row
                            for row in existing_records
                            if str(row.get("record_id") or "").strip() == requested_history_record_id
                        ),
                        None,
                    )
                    existing_n_user = ""
                    if ref_record and isinstance(ref_record, dict):
                        existing_n_user = str(ref_record.get("values", {}).get("custom_n_user") or "").strip()
                    submitted_section_values["custom_n_user"] = existing_n_user
                else:
                    # Create mode - generate sequence number unique per entity
                    max_seq = 0
                    if active_entity_id is not None and active_entity_internal_number is not None:
                        records_storage_key = build_menu_process_records_storage_key("contacto_geral")
                        members_of_entity = session.scalars(
                            select(Member).join(MemberEntity, MemberEntity.member_id == Member.id)
                            .where(MemberEntity.entity_id == active_entity_id)
                            .where(Member.profile_custom_fields.like(f'%"{records_storage_key}"%'))
                        ).all()

                        target_str = str(active_entity_internal_number).strip()
                        for m in members_of_entity:
                            m_fields = parse_member_profile_fields(m.profile_custom_fields)
                            m_records = parse_menu_process_records(m_fields.get(records_storage_key))
                            for r in m_records:
                                r_section = str(r.get("section_key") or "").strip()
                                if r_section == "custom_dados_membresia":
                                    r_values = r.get("values") or {}
                                    if str(r_values.get("custom_n_cliente") or "").strip() == target_str:
                                        val_str = str(r_values.get("custom_n_user") or "").strip()
                                        if val_str.isdigit():
                                            max_seq = max(max_seq, int(val_str))
                    next_seq = max_seq + 1
                    submitted_section_values["custom_n_user"] = f"{next_seq:05d}"
        record_for_update = None
        if (
            history_process_mode
            and requested_history_action == "update"
            and requested_history_record_id
        ):
            record_for_update = next(
                (
                    row
                    for row in existing_records
                    if str(row.get("record_id") or "").strip() == requested_history_record_id
                ),
                None,
            )
        if process_view_authorization_mode and requested_history_action in {"create", "update"}:
            success_message, refreshed_authorization_rows, authorization_error = (
                save_process_view_authorization_rule_v1(
                    session,
                    sidebar_menu_settings=sidebar_menu_settings,
                    selected_entity_id=process_view_authorization_scope_entity_id,
                    current_user_id=int(current_user["id"]),
                    requested_history_action=requested_history_action,
                    requested_history_record_id=requested_history_record_id,
                    submitted_section_values=submitted_section_values,
                    section_key=requested_section_key,
                )
            )
            if authorization_error:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(
                        submitted_form,
                        menu=clean_menu_key,
                        profile_error=authorization_error,
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            redirect_url = _build_post_save_redirect_url_v6(
                submitted_form,
                menu=clean_menu_key,
                profile_success=success_message,
            )
            _write_meu_perfil_process_flow_debug_log_v1(
                request,
                "03_process_authorization_redirect_success",
                submitted_form=submitted_form,
                data={
                    "clean_menu_key": clean_menu_key,
                    "requested_section_key": requested_section_key,
                    "requested_history_action": requested_history_action,
                    "requested_history_record_id": requested_history_record_id,
                    "redirect_url": redirect_url,
                    "success_message": success_message,
                },
            )
            if silent_refresh_requested:
                return JSONResponse(
                    _build_dynamic_process_silent_refresh_payload_v1(
                        submitted_form=submitted_form,
                        clean_menu_key=clean_menu_key,
                        requested_section_key=requested_section_key,
                        process_setting=process_setting,
                        existing_profile_fields=existing_profile_fields,
                        success_message=success_message,
                        history_rows_override=refreshed_authorization_rows,
                    ),
                    status_code=status.HTTP_200_OK,
                )

            return RedirectResponse(
                url=redirect_url,
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if (
            history_process_mode
            and department_history_mode
            and requested_history_action in {"create", "update"}
        ):
            department_name = _extract_department_name_value_v1(
                submitted_section_values,
                active_section_field_keys,
                field_meta_by_key,
            )
            if department_name:
                if requested_history_action == "update" and requested_history_record_id and record_for_update is None:
                    return RedirectResponse(
                        url=_build_post_save_redirect_url_v6(
                            submitted_form,
                            menu=clean_menu_key,
                            profile_error=f"{record_label_singular.capitalize()} nao encontrado para editar.",
                        ),
                        status_code=status.HTTP_303_SEE_OTHER,
                    )
                previous_values = (
                    record_for_update.get("values")
                    if isinstance(record_for_update, dict)
                    and isinstance(record_for_update.get("values"), dict)
                    else {}
                )
                previous_department_id = _parse_department_id_value_v1(
                    previous_values.get("__department_id")
                )
                resolved_entity_id, resolve_entity_error = (
                    _resolve_selected_entity_id_for_process_v1(
                        request,
                        session,
                        current_user,
                    )
                )
                if resolve_entity_error:
                    return RedirectResponse(
                        url=_build_post_save_redirect_url_v6(
                            submitted_form,
                            menu=clean_menu_key,
                            profile_error=resolve_entity_error,
                        ),
                        status_code=status.HTTP_303_SEE_OTHER,
                    )
                synced_department = _upsert_department_for_process_v1(
                    session,
                    entity_id=int(resolved_entity_id),
                    department_name=department_name,
                    is_active=submitted_section_values.get("__estado") == "ativo",
                    preferred_department_id=previous_department_id,
                )
                if synced_department is not None:
                    submitted_section_values["__department_id"] = str(synced_department.id)

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
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
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
                        url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
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

        _write_meu_perfil_process_flow_debug_log_v1(
            request,
            "02_process_before_commit",
            submitted_form=submitted_form,
            data={
                "clean_menu_key": clean_menu_key,
                "requested_section_key": requested_section_key,
                "history_process_mode": history_process_mode,
                "absence_process_mode": absence_process_mode,
                "record_label_singular": record_label_singular,
                "active_section_field_keys": list(active_section_field_keys),
                "hidden_process_targets": sorted(list(hidden_process_targets)),
                "submitted_section_values": dict(submitted_section_values),
                "submitted_quantity_values_by_rule": dict(submitted_quantity_values_by_rule),
                "records_storage_key": records_storage_key,
                "existing_records_count": len(existing_records),
                "success_message": success_message,
            },
        )
        member.profile_custom_fields = serialize_member_profile_fields(existing_profile_fields)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                    profile_error="Falha ao gravar os dados do processo.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    redirect_url = _build_post_save_redirect_url_v6(
        submitted_form,
        menu=clean_menu_key,
        profile_success=success_message,
    )
    _write_meu_perfil_process_flow_debug_log_v1(
        request,
        "03_process_redirect_success",
        submitted_form=submitted_form,
        data={
            "clean_menu_key": clean_menu_key,
            "requested_section_key": requested_section_key,
            "redirect_url": redirect_url,
            "success_message": success_message,
        },
    )
    if silent_refresh_requested:
        return JSONResponse(
            _build_dynamic_process_silent_refresh_payload_v1(
                submitted_form=submitted_form,
                clean_menu_key=clean_menu_key,
                requested_section_key=requested_section_key,
                process_setting=process_setting,
                existing_profile_fields=existing_profile_fields,
                success_message=success_message,
            ),
            status_code=status.HTTP_200_OK,
        )

    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/api/songs/transcribe-audio")
async def transcribe_song_audio_v1(request: Request) -> JSONResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return JSONResponse(
                {
                    "success": False,
                    "message": "Efetue login para continuar.",
                },
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            payload = await request.json()
        except Exception:
            payload = {}

    transcribed_ok, response_payload = transcribe_song_from_youtube_v1(
        youtube_url=(payload or {}).get("youtubeUrl"),
        song_name=(payload or {}).get("songName"),
        version=(payload or {}).get("version"),
    )
    return JSONResponse(
        response_payload,
        status_code=status.HTTP_200_OK if transcribed_ok else status.HTTP_400_BAD_REQUEST,
    )

@router.post("/users/profile/address")
def update_address_profile(
    request: Request,
    address: str = Form(""),
    city: str = Form(""),
    freguesia: str = Form(""),
    postal_code: str = Form(""),
    return_url: str = Form(""),
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
                url=_build_post_save_redirect_url_from_raw_return_url_v6(
                    return_url,
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="morada",
                    target="#perfil-morada-card",
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
                url=_build_post_save_redirect_url_from_raw_return_url_v6(
                    return_url,
                    profile_error="Falha ao gravar dados de morada.",
                    profile_tab="morada",
                    target="#perfil-morada-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=_build_post_save_redirect_url_from_raw_return_url_v6(
            return_url,
            profile_success="Dados de morada atualizados com sucesso.",
            profile_tab="morada",
            target="#perfil-morada-card",
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
    return_url: str = Form(""),
) -> RedirectResponse:
    clean_training_outros = training_outros.strip()
    is_outros_enabled = training_outros_enabled == "1"

    if is_outros_enabled and not clean_training_outros:
        return RedirectResponse(
            url=_build_post_save_redirect_url_from_raw_return_url_v6(
                return_url,
                profile_error="Preencha o campo Outros para gravar o treinamento.",
                profile_tab="treinamento",
                target="#dados-treinamento-card",
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
                url=_build_post_save_redirect_url_from_raw_return_url_v6(
                    return_url,
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="treinamento",
                    target="#dados-treinamento-card",
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
                url=_build_post_save_redirect_url_from_raw_return_url_v6(
                    return_url,
                    profile_error="Falha ao gravar dados de treinamento.",
                    profile_tab="treinamento",
                    target="#dados-treinamento-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=_build_post_save_redirect_url_from_raw_return_url_v6(
            return_url,
            profile_success="Dados de treinamento atualizados com sucesso.",
            profile_tab="treinamento",
            target="#dados-treinamento-card",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/users/profile/whatsapp/verify")
def verify_whatsapp_profile(
    request: Request,
    return_url: str = Form(""),
    profile_section: str = Form(""),
) -> RedirectResponse:
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
                url=_build_post_save_redirect_url_from_raw_return_url_v6(
                    return_url,
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="pessoal",
                    profile_section=profile_section,
                    target="#perfil-pessoal-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        normalized_phone = normalize_whatsapp_recipient(member.primary_phone or "")
        if not normalized_phone:
            return RedirectResponse(
                url=_build_post_save_redirect_url_from_raw_return_url_v6(
                    return_url,
                    profile_error=(
                        "Telefone inválido para WhatsApp. Use formato internacional "
                        "(ex.: +351912345678)."
                    ),
                    profile_tab="pessoal",
                    profile_section=profile_section,
                    target="#perfil-pessoal-card",
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
                url=_build_post_save_redirect_url_from_raw_return_url_v6(
                    return_url,
                    profile_error=f"Não foi possível iniciar verificação WhatsApp: {error_message}",
                    profile_tab="pessoal",
                    profile_section=profile_section,
                    target="#perfil-pessoal-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        session.commit()
        return RedirectResponse(
            url=_build_post_save_redirect_url_from_raw_return_url_v6(
                return_url,
                profile_success=(
                    "Verificação WhatsApp iniciada. O estado será atualizado automaticamente "
                    "quando o webhook receber a confirmação."
                ),
                profile_tab="pessoal",
                profile_section=profile_section,
                target="#perfil-pessoal-card",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

# APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ENDPOINT_V2_START
@router.post("/debug/global-message-auto-dismiss")
async def appverbo_global_message_auto_dismiss_debug_v2(request: Request) -> JSONResponse:
    import json
    import os
    from datetime import datetime, timezone
    from pathlib import Path

    try:
        try:
            payload = await request.json()
        except Exception as exc:
            payload = {
                "json_error": repr(exc),
            }

        request_url = ""
        request_path = ""
        request_client = ""

        try:
            request_url = str(request.url)
            request_path = str(request.url.path)
            request_client = str(getattr(request.client, "host", "") or "")
        except Exception:
            pass

        log_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "logger": "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_V2",
            "request": {
                "method": str(request.method),
                "path": request_path,
                "url": request_url,
                "client": request_client,
            },
            "payload": payload,
        }

        log_dir = Path(
            os.environ.get(
                "APPVERBO_GLOBAL_MESSAGE_LOG_DIR",
                "appverbo_runtime_logs",
            )
        )
        log_dir.mkdir(parents=True, exist_ok=True)

        log_line = json.dumps(
            log_entry,
            ensure_ascii=False,
            default=str,
            sort_keys=True,
        )

        with (log_dir / "global_message_auto_dismiss_debug.log").open("a", encoding="utf-8") as log_file:
            log_file.write(log_line + "\n")

        print("APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG " + log_line, flush=True)

        return JSONResponse({"ok": True})

    except Exception as exc:
        print(
            "APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ERROR " + repr(exc),
            flush=True,
        )
        return JSONResponse(
            {
                "ok": False,
                "error": repr(exc),
            },
            status_code=500,
        )
# APPVERBO_GLOBAL_MESSAGE_AUTO_DISMISS_DEBUG_ENDPOINT_V2_END


# APPVERBO_UTILIZADOR_ACTION_FLOW_DEBUG_ENDPOINT_V1_START
@router.post("/debug/utilizador-action-flow")
async def appverbo_utilizador_action_flow_debug_v1(request: Request) -> JSONResponse:
    import json
    import os
    from datetime import datetime, timezone
    from pathlib import Path

    try:
        try:
            payload = await request.json()
        except Exception as exc:
            payload = {
                "json_error": repr(exc),
            }

        request_url = ""
        request_path = ""
        request_client = ""

        try:
            request_url = str(request.url)
            request_path = str(request.url.path)
            request_client = str(getattr(request.client, "host", "") or "")
        except Exception:
            pass

        log_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "logger": "APPVERBO_UTILIZADOR_ACTION_FLOW_DEBUG_V1",
            "request": {
                "method": str(request.method),
                "path": request_path,
                "url": request_url,
                "client": request_client,
            },
            "payload": payload,
        }

        log_dir = Path(
            os.environ.get(
                "APPVERBO_UTILIZADOR_ACTION_FLOW_LOG_DIR",
                "appverbo_runtime_logs",
            )
        )
        log_dir.mkdir(parents=True, exist_ok=True)

        log_line = json.dumps(
            log_entry,
            ensure_ascii=False,
            default=str,
            sort_keys=True,
        )

        with (log_dir / "utilizador_action_flow_debug.log").open("a", encoding="utf-8") as log_file:
            log_file.write(log_line + "\n")

        print("APPVERBO_UTILIZADOR_ACTION_FLOW_DEBUG " + log_line, flush=True)

        return JSONResponse({"ok": True})

    except Exception as exc:
        print(
            "APPVERBO_UTILIZADOR_ACTION_FLOW_DEBUG_ERROR " + repr(exc),
            flush=True,
        )
        return JSONResponse(
            {
                "ok": False,
                "error": repr(exc),
            },
            status_code=500,
        )


# APPVERBO_UTILIZADOR_ACTION_FLOW_DEBUG_ENDPOINT_V1_END
