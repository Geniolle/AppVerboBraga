from __future__ import annotations

import json

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import text
from starlette.requests import Request as RequestType
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER

from appverbo.core import SessionLocal
from appverbo.menu_settings import *  # noqa: F403,F401
from appverbo.routes.profile.router import router
from appverbo.routes.profile.settings.permissions import require_menu_settings_owner_v1
from appverbo.routes.profile.settings.redirects import build_settings_redirect_url_v1
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_current_user, get_session_entity_id


####################################################################################
# (1) ALIASES TEMPORÁRIOS PARA COMPATIBILIDADE COM O CÓDIGO MIGRADO
####################################################################################

_build_settings_redirect_url = build_settings_redirect_url_v1
_require_menu_settings_owner_v1 = require_menu_settings_owner_v1


@router.post("/settings/menu/field-move", response_class=HTMLResponse)
def move_sidebar_menu_additional_field_handler(
    request: Request,
    menu_key: str = Form(...),
    field_key: str = Form(...),
    direction: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem mover campos.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode mover campos.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        ok, error_message = move_sidebar_menu_additional_field(
            session,
            clean_menu_key,
            field_key,
            direction,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível mover o campo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Campo movido com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="campos-adicionais",
            ),
            status_code=HTTP_303_SEE_OTHER,
        )




# APPVERBO_PRESERVE_HEADER_ASSIGNMENTS_V1_START

# ###################################################################################
# (PRESERVE_HEADER_ASSIGNMENTS_V1) PRESERVAR ATRIBUICAO CAMPO -> CABECALHO
# ###################################################################################

def _normalize_menu_key_local_v1(value: object) -> str:
    return str(value or "").strip().lower()


def _read_sidebar_menu_config_v1(session, menu_key: str) -> dict:
    clean_menu_key = _normalize_menu_key_local_v1(menu_key)

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

    if not raw_config:
        return {}

    try:
        parsed_config = json.loads(raw_config)
    except (TypeError, ValueError):
        return {}

    return parsed_config if isinstance(parsed_config, dict) else {}


def _write_sidebar_menu_config_v1(session, menu_key: str, menu_config: dict) -> None:
    clean_menu_key = _normalize_menu_key_local_v1(menu_key)

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


def _get_header_assignments_from_config_v1(menu_config: dict) -> dict[str, str]:
    assignments: dict[str, str] = {}

    raw_rows = menu_config.get("process_visible_field_rows")
    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue

            field_key = _normalize_menu_key_local_v1(raw_row.get("field_key"))
            header_key = _normalize_menu_key_local_v1(raw_row.get("header_key"))

            if not field_key or not header_key:
                continue

            assignments[field_key] = header_key

    raw_header_map = menu_config.get("process_visible_field_header_map")
    if isinstance(raw_header_map, dict):
        for raw_field_key, raw_header_key in raw_header_map.items():
            field_key = _normalize_menu_key_local_v1(raw_field_key)
            header_key = _normalize_menu_key_local_v1(raw_header_key)

            if not field_key or not header_key:
                continue

            assignments[field_key] = header_key

    return assignments


def _get_header_keys_from_config_v1(menu_config: dict) -> set[str]:
    header_keys: set[str] = set()

    raw_fields = menu_config.get("additional_fields")
    if not isinstance(raw_fields, list):
        return header_keys

    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            continue

        field_key = _normalize_menu_key_local_v1(raw_field.get("key"))
        field_type = _normalize_menu_key_local_v1(raw_field.get("field_type") or raw_field.get("type"))

        if field_key and field_type == "header":
            header_keys.add(field_key)

    return header_keys


def _get_visible_fields_from_config_v1(menu_config: dict) -> list[str]:
    visible_fields: list[str] = []
    seen_fields: set[str] = set()

    raw_visible_fields = menu_config.get("process_visible_fields")
    if isinstance(raw_visible_fields, list):
        for raw_field_key in raw_visible_fields:
            field_key = _normalize_menu_key_local_v1(raw_field_key)

            if not field_key or field_key in seen_fields:
                continue

            seen_fields.add(field_key)
            visible_fields.append(field_key)

    raw_rows = menu_config.get("process_visible_field_rows")
    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue

            field_key = _normalize_menu_key_local_v1(raw_row.get("field_key"))

            if not field_key or field_key in seen_fields:
                continue

            seen_fields.add(field_key)
            visible_fields.append(field_key)

    return visible_fields


def _restore_menu_header_assignments_after_additional_fields_v1(
    session,
    menu_key: str,
    old_menu_config: dict,
) -> None:
    old_assignments = _get_header_assignments_from_config_v1(old_menu_config)

    if not old_assignments:
        return

    current_config = _read_sidebar_menu_config_v1(session, menu_key)
    if not current_config:
        return

    current_header_keys = _get_header_keys_from_config_v1(current_config)
    current_visible_fields = _get_visible_fields_from_config_v1(current_config)

    if not current_visible_fields:
        return

    restored_header_map: dict[str, str] = {}
    restored_rows: list[dict[str, str]] = []

    for field_key in current_visible_fields:
        if field_key in current_header_keys:
            continue

        header_key = old_assignments.get(field_key, "")
        if header_key not in current_header_keys:
            header_key = ""

        if header_key:
            restored_header_map[field_key] = header_key

        restored_rows.append(
            {
                "field_key": field_key,
                "header_key": header_key,
            }
        )

    current_config["process_visible_field_header_map"] = restored_header_map
    current_config["process_visible_field_rows"] = restored_rows

    _write_sidebar_menu_config_v1(session, menu_key, current_config)
    session.commit()


def _update_sidebar_menu_additional_fields_preserve_headers_v1(
    session,
    menu_key: str,
    payload_fields: list[dict[str, str]],
) -> tuple[bool, str]:
    old_menu_config = _read_sidebar_menu_config_v1(session, menu_key)

    ok, error_message = update_sidebar_menu_additional_fields_v1(
        session,
        menu_key,
        payload_fields,
    )

    if not ok:
        return ok, error_message

    _restore_menu_header_assignments_after_additional_fields_v1(
        session,
        menu_key,
        old_menu_config,
    )

    return ok, error_message


# APPVERBO_PRESERVE_HEADER_ASSIGNMENTS_V1_END


@router.post("/settings/menu/process-additional-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_additional_fields_v1(
    request: Request,
    menu_key: str = Form(...),
    additional_field_key: list[str] = Form(default=[]),
    additional_field_label: list[str] = Form(default=[]),
    additional_field_type: list[str] = Form(default=[]),
    additional_field_required: list[str] = Form(default=[]),
    additional_field_size: list[str] = Form(default=[]),
    additional_field_list_key: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar definições do menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode configurar campos adicionais por processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        rows_count = max(
            len(additional_field_key),
            len(additional_field_label),
            len(additional_field_type),
            len(additional_field_required),
            len(additional_field_size),
            len(additional_field_list_key),
        )

        payload_fields: list[dict[str, str]] = []

        for row_index in range(rows_count):
            payload_fields.append(
                {
                    "key": additional_field_key[row_index] if row_index < len(additional_field_key) else "",
                    "label": additional_field_label[row_index] if row_index < len(additional_field_label) else "",
                    "field_type": additional_field_type[row_index] if row_index < len(additional_field_type) else "",
                    "is_required": additional_field_required[row_index] if row_index < len(additional_field_required) else "",
                    "size": additional_field_size[row_index] if row_index < len(additional_field_size) else "",
                    "list_key": additional_field_list_key[row_index] if row_index < len(additional_field_list_key) else "",
                }
            )

        ok, error_message = _update_sidebar_menu_additional_fields_preserve_headers_v1(
            session,
            clean_menu_key,
            payload_fields,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar os campos adicionais do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Campos adicionais e hierarquia do processo atualizados com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="campos-adicionais",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
