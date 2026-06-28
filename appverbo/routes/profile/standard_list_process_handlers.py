from __future__ import annotations

import unicodedata
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from appverbo.core import *  # noqa: F403,F401
from appverbo.menu_settings import get_sidebar_menu_settings, resolve_menu_key_alias
from appverbo.models import Member, User
from appverbo.routes.profile.router import router
from appverbo.services.profile import (
    build_menu_process_records_storage_key,
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_member_profile_fields,
    serialize_menu_process_records,
)


# ###################################################################################
# (1) NORMALIZAÇÃO DO PROCESSO LISTÁVEL STANDARD
# ###################################################################################


def _normalize_standard_list_text_v1(value: Any) -> str:
    normalized = (
        unicodedata.normalize("NFKD", str(value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    return " ".join(normalized.replace("_", " ").replace("-", " ").split())


def _is_truthy_standard_list_value_v1(value: Any) -> bool:
    if value is True:
        return True
    return _normalize_standard_list_text_v1(value) in {"1", "true", "sim", "yes", "on", "list"}


def _is_standard_list_process_setting_v1(process_setting: dict[str, Any] | None) -> bool:
    if not isinstance(process_setting, dict):
        return False

    explicit_layout = _normalize_standard_list_text_v1(
        process_setting.get("process_layout")
        or process_setting.get("layout")
        or process_setting.get("processLayout")
        or process_setting.get("process_mode")
        or process_setting.get("processMode")
    )

    if explicit_layout in {"list", "lista", "standard list", "standard_list", "gestao", "gestão"}:
        return True

    for flag_key in (
        "is_list_process",
        "isListProcess",
        "standard_list_process",
        "standardListProcess",
    ):
        if _is_truthy_standard_list_value_v1(process_setting.get(flag_key)):
            return True

    joined = " ".join(
        part
        for part in (
            _normalize_standard_list_text_v1(process_setting.get("key")),
            _normalize_standard_list_text_v1(process_setting.get("label")),
            _normalize_standard_list_text_v1(process_setting.get("title")),
        )
        if part
    )
    return bool(joined) and "perfil" in joined and "autorizacao" in joined


def _normalize_standard_process_state_v1(value: Any) -> str:
    clean_value = _normalize_standard_list_text_v1(value)
    if clean_value in {"inativo", "inactive", "0", "false", "off", "nao", "não"}:
        return "inativo"
    return "ativo"


def _normalize_standard_process_system_v1(value: Any) -> str:
    clean_value = _normalize_standard_list_text_v1(value)
    if clean_value == "owner":
        return "owner"
    if clean_value == "legado":
        return "legado"
    return "all"


# ###################################################################################
# (2) CAMPOS DA ABA LISTÁVEL
# ###################################################################################


def _standard_process_field_meta_by_key_v1(process_setting: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    raw_options = process_setting.get("process_field_options") or []
    if not isinstance(raw_options, list):
        return result

    for raw_option in raw_options:
        if not isinstance(raw_option, dict):
            continue
        field_key = str(raw_option.get("key") or "").strip().lower()
        if not field_key:
            continue
        field_type = str(raw_option.get("field_type") or raw_option.get("fieldType") or "text").strip().lower()
        result[field_key] = {
            "label": str(raw_option.get("label") or field_key).strip() or field_key,
            "field_type": field_type,
            "is_required": _is_truthy_standard_list_value_v1(
                raw_option.get("is_required", raw_option.get("required"))
            ),
        }
    return result


def _build_standard_process_sections_v1(process_setting: dict[str, Any]) -> list[dict[str, Any]]:
    field_meta_by_key = _standard_process_field_meta_by_key_v1(process_setting)
    raw_rows = process_setting.get("process_visible_field_rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raw_visible_fields = process_setting.get("process_visible_fields") or []
        sections: list[dict[str, Any]] = []
        if isinstance(raw_visible_fields, list):
            for raw_field_key in raw_visible_fields:
                field_key = str(raw_field_key or "").strip().lower()
                if not field_key:
                    continue
                meta = field_meta_by_key.get(field_key, {})
                if str(meta.get("field_type") or "text").strip().lower() == "header":
                    continue
                sections.append({"key": f"field:{field_key}", "fields": [field_key]})
        return sections

    section_map: dict[str, list[str]] = {}
    section_order: list[str] = []
    first_field_key = ""

    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            continue
        field_key = str(raw_row.get("field_key") or "").strip().lower()
        if not field_key:
            continue
        meta = field_meta_by_key.get(field_key, {})
        if str(meta.get("field_type") or "text").strip().lower() == "header":
            continue
        if not first_field_key:
            first_field_key = field_key
        section_key = str(raw_row.get("header_key") or "").strip().lower() or "__geral__"
        if section_key not in section_map:
            section_map[section_key] = []
            section_order.append(section_key)
        section_map[section_key].append(field_key)

    sections = [{"key": section_key, "fields": section_map[section_key]} for section_key in section_order]
    if len(sections) == 1 and sections[0]["key"] == "__geral__":
        return [
            {"key": f"field:{field_key}", "fields": [field_key]}
            for field_key in sections[0]["fields"]
        ]
    return sections


def _resolve_standard_process_section_fields_v1(
    process_setting: dict[str, Any],
    requested_section_key: str,
) -> list[str]:
    sections = _build_standard_process_sections_v1(process_setting)
    if not sections:
        return []

    clean_section_key = str(requested_section_key or "").strip()
    selected_section = next(
        (section for section in sections if str(section.get("key") or "") == clean_section_key),
        None,
    )
    if selected_section is None:
        selected_section = sections[0]

    return [
        str(field_key or "").strip().lower()
        for field_key in selected_section.get("fields", [])
        if str(field_key or "").strip()
    ]


# ###################################################################################
# (3) REDIRECT COM CONTEXTO DO PROCESSO
# ###################################################################################


def _build_standard_process_redirect_url_v1(
    raw_url: Any,
    menu_key: str,
    *,
    success: str = "",
    error: str = "",
) -> str:
    clean_menu_key = str(menu_key or "").strip().lower()
    default_target = f"#{clean_menu_key}-standard-active-card"
    clean_raw_url = str(raw_url or "").strip()
    if not clean_raw_url:
        clean_raw_url = f"/users/new?menu={clean_menu_key}&target={default_target}{default_target}"

    split_url = urlsplit(clean_raw_url)
    query_values = dict(parse_qsl(split_url.query, keep_blank_values=True))
    query_values["menu"] = query_values.get("menu") or clean_menu_key
    query_values["target"] = query_values.get("target") or default_target
    query_values["appverbo_after_save"] = "1"

    if success:
        query_values["profile_success"] = success
        query_values.pop("profile_error", None)
    if error:
        query_values["profile_error"] = error
        query_values.pop("profile_success", None)

    return urlunsplit(
        (
            split_url.scheme,
            split_url.netloc,
            split_url.path or "/users/new",
            urlencode(query_values),
            split_url.fragment or default_target.lstrip("#"),
        )
    )


# ###################################################################################
# (4) GRAVAÇÃO STANDARD REUTILIZÁVEL
# ###################################################################################


@router.post("/users/profile/standard-list-process-save")
async def save_standard_list_process_profile(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
    clean_menu_key = resolve_menu_key_alias(submitted_form.get("menu_key"))
    requested_section_key = str(submitted_form.get("section_key") or "").strip()
    requested_action = str(submitted_form.get("history_action") or "create").strip().lower()
    requested_record_id = str(submitted_form.get("history_record_id") or "").strip()
    raw_return_url = submitted_form.get("process_return_url") or submitted_form.get("return_url")

    if not clean_menu_key:
        return RedirectResponse(
            url=_build_standard_process_redirect_url_v1(
                raw_return_url,
                "home",
                error="Processo inválido.",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if requested_action not in {"create", "update"}:
        requested_action = "create"

    with SessionLocal() as session:  # noqa: F405
        current_user = get_current_user(request, session)  # noqa: F405
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member)
            .join(User, User.member_id == Member.id)
            .where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=_build_standard_process_redirect_url_v1(
                    raw_return_url,
                    clean_menu_key,
                    error="Membro associado ao utilizador não encontrado.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        process_setting = next(
            (
                row
                for row in get_sidebar_menu_settings(session)
                if resolve_menu_key_alias(row.get("key")) == clean_menu_key
            ),
            None,
        )
        if not _is_standard_list_process_setting_v1(process_setting):
            return RedirectResponse(
                url=_build_standard_process_redirect_url_v1(
                    raw_return_url,
                    clean_menu_key,
                    error="Processo listável não encontrado.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        field_meta_by_key = _standard_process_field_meta_by_key_v1(process_setting or {})
        active_section_fields = _resolve_standard_process_section_fields_v1(
            process_setting or {},
            requested_section_key,
        )

        submitted_values: dict[str, str] = {}
        missing_required_labels: list[str] = []
        for field_key in active_section_fields:
            input_name = f"process_field__{field_key}"
            clean_value = str(submitted_form.get(input_name) or "").strip()
            field_meta = field_meta_by_key.get(field_key, {})
            if not clean_value and bool(field_meta.get("is_required")):
                missing_required_labels.append(str(field_meta.get("label") or field_key))
                continue
            if clean_value:
                submitted_values[field_key] = clean_value

        if missing_required_labels:
            return RedirectResponse(
                url=_build_standard_process_redirect_url_v1(
                    raw_return_url,
                    clean_menu_key,
                    error="Preencha os campos obrigatórios: " + ", ".join(missing_required_labels) + ".",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not submitted_values:
            return RedirectResponse(
                url=_build_standard_process_redirect_url_v1(
                    raw_return_url,
                    clean_menu_key,
                    error="Preencha ao menos um campo do registo.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        submitted_values["__system"] = _normalize_standard_process_system_v1(
            submitted_form.get("process_system")
        )
        submitted_values["__estado"] = _normalize_standard_process_state_v1(
            submitted_form.get("process_state")
        )

        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        records_storage_key = build_menu_process_records_storage_key(clean_menu_key)
        existing_records = parse_menu_process_records(existing_profile_fields.get(records_storage_key))

        success_message = "Registo criado com sucesso."
        if requested_action == "update" and requested_record_id:
            updated = False
            for row in existing_records:
                if str(row.get("record_id") or "").strip() != requested_record_id:
                    continue
                row["section_key"] = requested_section_key
                row["values"] = dict(submitted_values)
                updated = True
                break
            if not updated:
                return RedirectResponse(
                    url=_build_standard_process_redirect_url_v1(
                        raw_return_url,
                        clean_menu_key,
                        error="Registo não encontrado para editar.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            success_message = "Registo atualizado com sucesso."
        else:
            existing_records.insert(
                0,
                {
                    "record_id": uuid4().hex,
                    "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    "section_key": requested_section_key,
                    "values": dict(submitted_values),
                },
            )

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
                url=_build_standard_process_redirect_url_v1(
                    raw_return_url,
                    clean_menu_key,
                    error="Falha ao gravar os dados do processo.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=_build_standard_process_redirect_url_v1(
            raw_return_url,
            clean_menu_key,
            success=success_message,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
