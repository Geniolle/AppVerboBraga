from __future__ import annotations

import json
import re
from datetime import (
    date,
    datetime,
    timezone,
)
from typing import Any
from uuid import uuid4
from fastapi import (
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from appgenesis.db.session import SessionLocal
from appgenesis.services.process_records_service import (
    ENTITY_RECORD_MENU_KEYS,
    create_process_record,
    update_process_record,
)
from appgenesis.menu_settings import (
    get_sidebar_menu_settings,
    resolve_menu_key_alias,
)
from appgenesis.services.session import (
    get_current_user,
    get_session_entity_id,
)
from appgenesis.services.profile import (
    build_menu_process_field_storage_key,
    build_menu_process_records_storage_key,
    build_menu_process_quantity_storage_key,
    filter_process_fields_by_hidden_targets,
    get_hidden_process_targets_from_rules,
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_member_profile_fields,
    serialize_menu_process_records,
    parse_menu_process_quantity_values,
    serialize_menu_process_quantity_values,
)
from appgenesis.models import (
    Member,
    User,
)
from appgenesis.dynamic_process_layout import resolve_dynamic_process_layout_config
from appgenesis.routes.profile.router import router
from appgenesis.routes.profile.handlers.profile_common import (
    _build_post_save_redirect_url_v6,
    _is_absence_process,
    _menu_action_denied_v1,
    _normalize_lookup_text,
    _normalize_process_field_required,
    _normalize_process_quantity_rules,
    _normalize_process_state,
)

PROCESS_FIELD_TYPES = {"text", "number", "email", "phone", "date", "flag", "list", "rows", "longtext"}
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

def _conditional_field_rule_met_v1(rule: Any, submitted_form: Any) -> bool:
    # Avalia editable_when / required_when: valor do campo de gatilho igual ao valor da regra.
    if not isinstance(rule, dict):
        return False
    trigger_field = str(rule.get("trigger_field") or "").strip().lower()
    trigger_value = str(rule.get("trigger_value") or "").strip().lower()
    operator = str(rule.get("operator") or "equals").strip().lower()
    submitted_trigger = str(submitted_form.get(f"process_field__{trigger_field}") or "").strip().lower()
    if not trigger_field:
        return False
    if operator == "is_not_empty":
        return bool(submitted_trigger)
    return submitted_trigger == trigger_value


def _normalize_rows_submission_v1(raw_value: Any, row_fields: list[dict[str, Any]]) -> tuple[list[dict[str, str]], list[int]]:
    # Campo "rows" (ex.: Musica + Tom): devolve as linhas preenchidas e os numeros das linhas incompletas.
    try:
        raw_rows = json.loads(str(raw_value or "[]"))
    except (TypeError, ValueError):
        return [], []
    if not isinstance(raw_rows, list):
        return [], []
    keys = [str(field.get("key") or "") for field in row_fields]
    required_keys = [str(field.get("key") or "") for field in row_fields if field.get("required")]
    clean_rows: list[dict[str, str]] = []
    incomplete_rows: list[int] = []
    for raw_row in raw_rows[:50]:
        if not isinstance(raw_row, dict):
            continue
        clean_row = {key: str(raw_row.get(key) or "").strip()[:200] for key in keys if key}
        if not any(clean_row.values()):
            continue
        row_number = len(clean_rows) + 1
        if any(not clean_row.get(key) for key in required_keys):
            incomplete_rows.append(row_number)
        clean_rows.append(clean_row)
    return [row for index, row in enumerate(clean_rows, start=1) if index not in incomplete_rows], incomplete_rows


WEEKDAY_NAMES_PT_V1 = (
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
)


def _apply_auto_document_number_v1(values: dict[str, str], field_key: str, meta: dict[str, Any]) -> None:
    """Numero calculado a partir de uma data (ex.: Entradas: R + AAMMDD da Data), como uma formula."""
    rule = meta.get("auto_document_number")
    if not isinstance(rule, dict):
        return
    date_key = str(rule.get("date_field") or "").strip().lower()
    prefix = str(rule.get("prefix") or "")
    try:
        parsed_date = datetime.strptime(str(values.get(date_key) or ""), "%Y-%m-%d")
    except ValueError:
        values.pop(field_key, None)
        return
    if str(rule.get("format") or "") == "weekday":
        values[field_key] = WEEKDAY_NAMES_PT_V1[parsed_date.weekday()]
        return
    values[field_key] = f"{prefix}{parsed_date.strftime('%y%m%d')}"


def _save_entity_process_record(
    *,
    session: Session,
    submitted_form: Any,
    process_setting: dict[str, Any],
    menu_key: str,
    section_key: str,
    section_field_keys: list[str],
    history_action: str,
    record_id: str,
    entity_id: int,
    user_id: int,
) -> RedirectResponse:
    """Criar, editar ou mudar estado de um registo de processo partilhado por entidade."""
    field_meta_by_key = {
        str(option.get("key") or "").strip().lower(): option
        for option in (process_setting.get("process_field_options") or [])
        if isinstance(option, dict)
    }
    values: dict[str, str] = {}
    missing_labels: list[str] = []
    for field_key in section_field_keys:
        meta = field_meta_by_key.get(field_key) or {}
        field_type = _normalize_process_field_type(meta.get("field_type"))
        raw_value = str(submitted_form.get(f"process_field__{field_key}") or "").strip()
        if field_type == "flag":
            values[field_key] = "1" if raw_value == "1" else "0"
            continue
        if meta.get("text_format") == "sentence" and raw_value:
            # Regra de formato: minusculas com a primeira letra em maiuscula (ex.: Musicas).
            raw_value = raw_value[:1].upper() + raw_value[1:].lower()
        for capitalize_word in meta.get("capitalize_words") or []:
            # Palavras com maiuscula fixa (ex.: Deus), em qualquer ponto do texto.
            raw_value = re.sub(rf"{re.escape(capitalize_word)}", capitalize_word, raw_value, flags=re.IGNORECASE)
        editable_rule = meta.get("editable_when")
        if editable_rule and not _conditional_field_rule_met_v1(editable_rule, submitted_form):
            # Campo nao editavel nesta situacao: nao grava valor.
            continue
        required_rule = meta.get("required_when")
        if required_rule:
            is_required_now = _conditional_field_rule_met_v1(required_rule, submitted_form)
        else:
            is_required_now = _normalize_process_field_required(meta.get("is_required", meta.get("required")))
        if field_type == "rows":
            clean_rows, incomplete_rows = _normalize_rows_submission_v1(raw_value, meta.get("row_fields") or [])
            if clean_rows:
                values[field_key] = json.dumps(clean_rows, ensure_ascii=False)
            elif is_required_now and not incomplete_rows:
                missing_labels.append(str(meta.get("label") or field_key))
            for row_number in incomplete_rows:
                missing_labels.append(f"{meta.get('label') or field_key} (linha {row_number})")
            continue
        if raw_value:
            values[field_key] = raw_value
        elif is_required_now:
            missing_labels.append(str(meta.get("label") or field_key))

    for field_key in section_field_keys:
        _apply_auto_document_number_v1(values, field_key, field_meta_by_key.get(field_key) or {})

    def _redirect(**params: Any) -> RedirectResponse:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(submitted_form, menu=menu_key, **params),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if history_action in {"update", "toggle_status"}:
        if not record_id:
            return _redirect(profile_error="Registo não identificado.")
        if history_action == "toggle_status":
            requested_state = str(submitted_form.get("history_record_state") or "").strip().lower()
            changed = update_process_record(
                session,
                entity_id=entity_id,
                menu_key=menu_key,
                record_id=record_id,
                state=requested_state or None,
            )
        else:
            if missing_labels:
                return _redirect(profile_error=f"Preencha: {', '.join(missing_labels)}.")
            changed = update_process_record(
                session,
                entity_id=entity_id,
                menu_key=menu_key,
                record_id=record_id,
                values=values,
            )
        if not changed:
            return _redirect(profile_error="Registo não encontrado.")
        session.commit()
        return _redirect(profile_success="Registo atualizado com sucesso.")

    if missing_labels:
        return _redirect(profile_error=f"Preencha: {', '.join(missing_labels)}.")
    create_process_record(
        session,
        entity_id=entity_id,
        menu_key=menu_key,
        values=values,
        section_key=section_key,
        created_by_user_id=user_id,
    )
    session.commit()
    return _redirect(profile_success="Registo criado com sucesso.")


@router.post("/users/profile/process-data")
async def update_dynamic_process_profile(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
    clean_menu_key = resolve_menu_key_alias(submitted_form.get("menu_key"))
    requested_section_key = str(submitted_form.get("section_key") or "").strip()
    requested_history_action = str(submitted_form.get("history_action") or "").strip().lower()
    requested_history_record_id = str(submitted_form.get("history_record_id") or "").strip()
    requested_history_record_state = str(
        submitted_form.get("history_record_state") or ""
    ).strip().lower()
    # Acao exigida: eliminar (delete), editar (update / estado) ou criar (novo registo).
    if requested_history_action == "delete":
        required_process_action = ("eliminar",)
    elif requested_history_action in {"update", "toggle_status"}:
        required_process_action = ("editar",)
    else:
        required_process_action = ("criar",)
    if clean_menu_key and _menu_action_denied_v1(request, clean_menu_key, required_process_action):
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key, profile_error="Sem permissão para esta ação neste processo."),
            status_code=status.HTTP_303_SEE_OTHER,
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
                url=_build_post_save_redirect_url_v6(submitted_form, menu="home",
                    profile_error="Processo não encontrado.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        quantity_rules = _normalize_process_quantity_rules(
            process_setting.get("process_quantity_fields")
        )
        dynamic_process_layout_config_v1 = resolve_dynamic_process_layout_config(
            clean_menu_key,
            str(process_setting.get("label") or clean_menu_key),
            process_setting.get("menu_config")
            if isinstance(process_setting.get("menu_config"), dict)
            else process_setting,
            visible_field_rows=process_setting.get("process_visible_field_rows"),
            field_options=process_setting.get("process_field_options"),
        )
        absence_process_mode = _is_absence_process(clean_menu_key, process_setting)
        history_process_mode = bool(
            dynamic_process_layout_config_v1.get("uses_record_history")
        )
        record_label_singular = str(
            dynamic_process_layout_config_v1.get("singular_label") or "registo"
        ).strip() or "registo"
        record_state_enabled = bool(
            dynamic_process_layout_config_v1.get("state_enabled")
        )
        if requested_history_action not in {"", "create", "update", "delete", "toggle_status"}:
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
                url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                    profile_error="Sem campos configurados para esta aba.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if clean_menu_key in ENTITY_RECORD_MENU_KEYS:
            return _save_entity_process_record(
                session=session,
                submitted_form=submitted_form,
                process_setting=process_setting,
                menu_key=clean_menu_key,
                section_key=requested_section_key,
                section_field_keys=section_field_keys,
                history_action=requested_history_action,
                record_id=requested_history_record_id,
                entity_id=get_session_entity_id(request),
                user_id=current_user["id"],
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
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
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
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
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
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                        profile_error=f"Falha ao eliminar o {record_label_singular}.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                    profile_success=f"{record_label_singular.capitalize()} eliminado com sucesso.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if history_process_mode and requested_history_action == "toggle_status":
            if not record_state_enabled:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                        profile_error=f"{record_label_singular.capitalize()} não suporta alteração de estado.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            if not requested_history_record_id:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                        profile_error=f"{record_label_singular.capitalize()} inválido para alterar estado.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            next_state = _normalize_process_state(requested_history_record_state)
            updated = False
            for row in existing_records:
                if str(row.get("record_id") or "").strip() != requested_history_record_id:
                    continue
                row_values = row.get("values") if isinstance(row.get("values"), dict) else {}
                normalized_row_values = dict(row_values)
                normalized_row_values["__estado"] = next_state
                row["values"] = normalized_row_values
                updated = True
                break

            if not updated:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                        profile_error=f"{record_label_singular.capitalize()} não encontrado para alterar estado.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

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
                    url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                        profile_error=f"Falha ao alterar o estado do {record_label_singular}.",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            status_action_label = "reativado" if next_state == "ativo" else "inativado"
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
                    profile_success=f"{record_label_singular.capitalize()} {status_action_label} com sucesso.",
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
        if history_process_mode and record_state_enabled:
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

    return RedirectResponse(
        url=_build_post_save_redirect_url_v6(submitted_form, menu=clean_menu_key,
            profile_success=success_message,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
