# ###################################################################################
# (1) ATUALIZACAO DOS CAMPOS ADICIONAIS DO PROCESSO MENU - V1
# ###################################################################################

import json

from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import text
from starlette.requests import Request as RequestType

from appverbo.routes.profile.router import router

# ###################################################################################
# (2) MOVER CAMPO ADICIONAL NO FORMULÁRIO - V1
# ###################################################################################

from appverbo.menu_settings import (
    create_sidebar_menu_setting,
    delete_sidebar_menu_setting,
    move_sidebar_menu_setting,
    move_sidebar_menu_additional_field,
    resolve_menu_key_alias,
    set_sidebar_menu_visibility,
    update_sidebar_menu_label,
    update_sidebar_menu_additional_fields_v1,
    update_sidebar_menu_process_fields,
    update_sidebar_menu_process_lists,
    update_sidebar_menu_subsequent_fields,
    update_sidebar_sections_v2,
    get_sidebar_global_refresh_version_v1,
)
from appverbo.core import SessionLocal
from appverbo.services.session import get_current_user
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_session_entity_id
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER


def _build_settings_redirect_url(
    error_message: str = "",
    success_message: str = "",
    redirect_menu: str = "administrativo",
    redirect_target: str = "#admin-account-status-card",
    settings_edit_key: str = "",
    settings_action: str = "",
    settings_tab: str = "",
) -> str:
    params = []
    if error_message:
        params.append(f"error={error_message}")
    if success_message:
        params.append(f"success={success_message}")
    if redirect_menu:
        params.append(f"menu={redirect_menu}")
    if redirect_target:
        params.append(f"target={redirect_target.lstrip('#')}")
    if settings_edit_key:
        params.append(f"settings_edit_key={settings_edit_key}")
    if settings_action:
        params.append(f"settings_action={settings_action}")
    if settings_tab:
        params.append(f"settings_tab={settings_tab}")
    return f"/users/new?{chr(38).join(params)}"


def _require_menu_settings_owner_v1(
    session,
    request: Request,
    redirect_menu: str,
    redirect_target: str,
    settings_edit_key: str = "",
    settings_action: str = "edit",
    settings_tab: str = "geral",
) -> RedirectResponse | None:
    current_user = get_current_user(request, session)

    if current_user is None:
        return RedirectResponse(
            url="/login?error=Efetue login para continuar.",
            status_code=HTTP_302_FOUND,
        )

    if not is_admin_user(session, current_user["id"], current_user["login_email"]):
        return RedirectResponse(
            url=_build_settings_redirect_url(
                error_message="Apenas administradores podem alterar definições do menu.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=settings_edit_key,
                settings_action=settings_action,
                settings_tab=settings_tab,
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
                error_message="Apenas Owner pode alterar definições do menu.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=settings_edit_key,
                settings_action=settings_action,
                settings_tab=settings_tab,
            ),
            status_code=HTTP_303_SEE_OTHER,
        )

    return None


# APPVERBO_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_START

# ###################################################################################
# (SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1) CONSULTAR VERSAO GLOBAL DO SIDEBAR
# ###################################################################################

@router.get("/settings/menu/sidebar-refresh-version")
def get_sidebar_refresh_version_v1(request: Request) -> JSONResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return JSONResponse(
                {"authenticated": False, "version": ""},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        refresh_version = get_sidebar_global_refresh_version_v1(session)

        return JSONResponse(
            {
                "authenticated": True,
                "version": refresh_version,
            }
        )

# APPVERBO_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_END

# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START

# ###################################################################################
# (SIDEBAR_SECTIONS_HANDLER_V2) GRAVAR SESSOES E PROPAGAR VISIBILIDADE AOS MENUS
# ###################################################################################

@router.post("/settings/menu/sidebar-sections", response_class=HTMLResponse)
def edit_sidebar_sections_v2(
    request: Request,
    section_key: list[str] = Form(default=[]),
    section_label: list[str] = Form(default=[]),
    section_visibility_scope_mode: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
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
                    error_message="Apenas administradores podem alterar sessões do sidebar.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
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
                    error_message="Apenas Owner pode alterar sessões do sidebar.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        rows_count = max(
            len(section_key),
            len(section_label),
            len(section_visibility_scope_mode),
        )

        payload_sections: list[dict[str, str]] = []

        for row_index in range(rows_count):
            payload_sections.append(
                {
                    "key": section_key[row_index] if row_index < len(section_key) else "",
                    "label": section_label[row_index] if row_index < len(section_label) else "",
                    "visibility_scope_mode": (
                        section_visibility_scope_mode[row_index]
                        if row_index < len(section_visibility_scope_mode)
                        else ""
                    ),
                }
            )

        ok, error_message = update_sidebar_sections_v2(
            session,
            payload_sections,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível gravar as sessões do sidebar.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Sessões do sidebar e visibilidade dos menus atualizadas com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key="administrativo",
                settings_action="edit",
                settings_tab="sessoes",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_END


# ###################################################################################
# (MENU_SETTINGS_CRUD_V1) GRAVAR CONFIGURACOES GERAIS DAS PASTAS
# ###################################################################################

@router.post("/settings/menu/edit", response_class=HTMLResponse)
def edit_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    menu_label: str = Form(...),
    menu_status: str = Form("ativo"),
    menu_visibility_scope: str = Form("all"),
    menu_sidebar_section: str = Form(""),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)
    clean_status = str(menu_status or "").strip().lower()
    make_visible = clean_status not in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
            settings_edit_key=clean_menu_key,
            settings_action="edit",
            settings_tab="geral",
        )
        if blocked_response is not None:
            return blocked_response

        if not make_visible:
            ok, error_message = set_sidebar_menu_visibility(
                session,
                clean_menu_key,
                False,
            )
            if not ok:
                return RedirectResponse(
                    url=_build_settings_redirect_url(
                        error_message=error_message or "Não foi possível atualizar o estado do menu.",
                        redirect_menu=redirect_menu,
                        redirect_target=redirect_target,
                        settings_edit_key=clean_menu_key,
                        settings_action="edit",
                        settings_tab="geral",
                    ),
                    status_code=HTTP_303_SEE_OTHER,
                )

        ok, error_message = update_sidebar_menu_label(
            session,
            clean_menu_key,
            menu_label,
            menu_visibility_scope,
            menu_sidebar_section,
        )
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar o menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="geral",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        if make_visible:
            ok, error_message = set_sidebar_menu_visibility(
                session,
                clean_menu_key,
                True,
            )
            if not ok:
                return RedirectResponse(
                    url=_build_settings_redirect_url(
                        error_message=error_message or "Não foi possível atualizar o estado do menu.",
                        redirect_menu=redirect_menu,
                        redirect_target=redirect_target,
                        settings_edit_key=clean_menu_key,
                        settings_action="edit",
                        settings_tab="geral",
                    ),
                    status_code=HTTP_303_SEE_OTHER,
                )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Menu atualizado com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="geral",
            ),
            status_code=HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/create", response_class=HTMLResponse)
def create_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_label: str = Form(...),
    menu_visibility_scope: str = Form("all"),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-account-status-card"),
) -> RedirectResponse:
    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
            settings_action="create",
        )
        if blocked_response is not None:
            return blocked_response

        ok, error_message, new_menu_key = create_sidebar_menu_setting(
            session,
            menu_label,
            menu_visibility_scope,
        )
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível criar a pasta.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Pasta criada com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=(
                    new_menu_key
                    if str(redirect_target or "").lstrip("#") == "settings-menu-edit-card"
                    else ""
                ),
                settings_action=(
                    "edit"
                    if str(redirect_target or "").lstrip("#") == "settings-menu-edit-card"
                    else ""
                ),
                settings_tab=(
                    "geral"
                    if str(redirect_target or "").lstrip("#") == "settings-menu-edit-card"
                    else ""
                ),
            ),
            status_code=HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/move", response_class=HTMLResponse)
def move_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    direction: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-account-status-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
        )
        if blocked_response is not None:
            return blocked_response

        ok, error_message = move_sidebar_menu_setting(
            session,
            clean_menu_key,
            direction,
        )
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível mover a pasta.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Ordem da pasta atualizada com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
            ),
            status_code=HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/delete", response_class=HTMLResponse)
def delete_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-account-status-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
        )
        if blocked_response is not None:
            return blocked_response

        ok, error_message = delete_sidebar_menu_setting(session, clean_menu_key)
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível eliminar a pasta.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Pasta eliminada com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
            ),
            status_code=HTTP_303_SEE_OTHER,
        )


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


@router.post("/settings/menu/process-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_fields_handler(
    request: Request,
    menu_key: str = Form(...),
    visible_fields: list[str] = Form(default=[]),
    visible_headers: list[str] = Form(default=[]),
    visible_rows_json: str = Form(""),
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
                    settings_tab="campos-config",
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
                    error_message="Apenas Owner pode configurar campos do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-config",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )





        # APPVERBO_PROCESS_FIELDS_HEADER_ROWS_JSON_V4_START
        clean_visible_fields: list[str] = []
        clean_visible_headers: list[str] = []
        seen_visible_fields: set[str] = set()

        raw_rows_json_text = str(visible_rows_json or "").strip()

        if raw_rows_json_text:
            try:
                parsed_visible_rows = json.loads(raw_rows_json_text)
            except (TypeError, ValueError, json.JSONDecodeError):
                parsed_visible_rows = []
        else:
            parsed_visible_rows = []

        if isinstance(parsed_visible_rows, list):
            for raw_row in parsed_visible_rows:
                if not isinstance(raw_row, dict):
                    continue

                field_key = str(
                    raw_row.get("field_key")
                    or raw_row.get("fieldKey")
                    or raw_row.get("key")
                    or ""
                ).strip().lower()

                header_key = str(
                    raw_row.get("header_key")
                    or raw_row.get("headerKey")
                    or raw_row.get("header")
                    or ""
                ).strip().lower()

                if not field_key:
                    continue

                if field_key in seen_visible_fields:
                    continue

                seen_visible_fields.add(field_key)
                clean_visible_fields.append(field_key)
                clean_visible_headers.append(header_key)

        if not clean_visible_fields:
            raw_visible_fields_list = list(visible_fields or [])
            raw_visible_headers_list = list(visible_headers or [])

            for row_index, raw_field_key in enumerate(raw_visible_fields_list):
                field_key = str(raw_field_key or "").strip().lower()

                if not field_key:
                    continue

                if field_key in seen_visible_fields:
                    continue

                raw_header_key = (
                    raw_visible_headers_list[row_index]
                    if row_index < len(raw_visible_headers_list)
                    else ""
                )
                header_key = str(raw_header_key or "").strip().lower()

                seen_visible_fields.add(field_key)
                clean_visible_fields.append(field_key)
                clean_visible_headers.append(header_key)
        # APPVERBO_PROCESS_FIELDS_HEADER_ROWS_JSON_V4_END

        ok, error_message = update_sidebar_menu_process_fields(
            session=session,
            menu_key=clean_menu_key,
            visible_fields=clean_visible_fields,
            visible_headers=clean_visible_headers,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar a configuração dos campos.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-config",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Configuração dos campos atualizada com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="campos-config",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/process-lists", response_class=HTMLResponse)
def edit_sidebar_menu_process_lists_handler(
    request: Request,
    menu_key: str = Form(...),
    process_list_key: list[str] = Form(default=[]),
    process_list_label: list[str] = Form(default=[]),
    process_list_items_csv: list[str] = Form(default=[]),
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
                    error_message="Apenas administradores podem alterar listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
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
                    error_message="Apenas Owner pode configurar listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        rows_count = max(
            len(process_list_key),
            len(process_list_label),
            len(process_list_items_csv),
        )

        payload_lists: list[dict[str, str]] = []

        for row_index in range(rows_count):
            label = process_list_label[row_index] if row_index < len(process_list_label) else ""
            items_csv = (
                process_list_items_csv[row_index]
                if row_index < len(process_list_items_csv)
                else ""
            )

            if not str(label or "").strip() and not str(items_csv or "").strip():
                continue

            payload_lists.append(
                {
                    "key": process_list_key[row_index] if row_index < len(process_list_key) else "",
                    "label": label,
                    "items_csv": items_csv,
                }
            )

        ok, error_message = update_sidebar_menu_process_lists(
            session=session,
            menu_key=clean_menu_key,
            raw_lists=payload_lists,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar as listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Listas do processo atualizadas com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="lista",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


# ###################################################################################
# (4) CAMPOS SUBSEQUENTES - V1
# ###################################################################################

@router.post("/settings/menu/process-subsequent-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_subsequent_fields_handler(
    request: Request,
    menu_key: str = Form(...),
    subsequent_field_key: list[str] = Form(default=[]),
    subsequent_trigger_field: list[str] = Form(default=[]),
    subsequent_field: list[str] = Form(default=[]),
    subsequent_operator: list[str] = Form(default=[]),
    subsequent_trigger_value: list[str] = Form(default=[]),
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
                    error_message="Apenas administradores podem alterar campos subsequentes.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos_subsequentes",
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
                    error_message="Apenas Owner pode configurar campos subsequentes.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos_subsequentes",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        rows_count = max(
            len(subsequent_field_key),
            len(subsequent_trigger_field),
            len(subsequent_field),
            len(subsequent_operator),
            len(subsequent_trigger_value),
        )

        payload_fields: list[dict[str, str]] = []

        for row_index in range(rows_count):
            if row_index < len(subsequent_trigger_field) and row_index < len(subsequent_field):
                payload_fields.append(
                    {
                        "key": subsequent_field_key[row_index] if row_index < len(subsequent_field_key) else "",
                        "trigger_field": subsequent_trigger_field[row_index] if row_index < len(subsequent_trigger_field) else "",
                        "field_key": subsequent_field[row_index] if row_index < len(subsequent_field) else "",
                        "operator": subsequent_operator[row_index] if row_index < len(subsequent_operator) else "",
                        "trigger_value": subsequent_trigger_value[row_index] if row_index < len(subsequent_trigger_value) else "",
                    }
                )

        ok, error_message = update_sidebar_menu_subsequent_fields(
            session,
            clean_menu_key,
            payload_fields,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar os campos subsequentes.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos_subsequentes",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Campos subsequentes atualizados com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="campos_subsequentes",
            ),
            status_code=HTTP_303_SEE_OTHER,
        )
