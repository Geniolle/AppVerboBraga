import json

from fastapi import Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appgenesis.routes.profile.router import router

from appgenesis.menu_settings import (
    resolve_menu_key_alias,
    update_sidebar_menu_process_fields,
)
from appgenesis.core import SessionLocal
from appgenesis.services.session import get_current_user, get_session_entity_id
from appgenesis.services.auth import is_admin_user
from appgenesis.services.permissions import get_user_entity_permissions

from appgenesis.routes.profile.process_settings.common import (
    _build_settings_redirect_url,
    _build_settings_editor_stay_redirect_url_v1,
    _SETTINGS_MENU_EDITOR_STAY_TARGET_V1,
    _log_process_editor_flow_v1,
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
    return_url: str = Form(""),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    _log_process_editor_flow_v1(
        request,
        "process_fields:received",
        menu_key=menu_key,
        clean_menu_key=clean_menu_key,
        redirect_menu=redirect_menu,
        redirect_target=redirect_target,
        return_url=return_url,
    )

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
                    return_url=return_url,
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

        if not permissions.get(
            "can_manage_tenant_structure",
            permissions.get("can_manage_all_entities", False),
        ):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode configurar campos do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-config",
                    return_url=return_url,
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # APPGENESIS_PROCESS_FIELDS_HEADER_ROWS_JSON_V4_START
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

                field_key = (
                    str(
                        raw_row.get("field_key")
                        or raw_row.get("fieldKey")
                        or raw_row.get("key")
                        or ""
                    )
                    .strip()
                    .lower()
                )

                header_key = (
                    str(
                        raw_row.get("header_key")
                        or raw_row.get("headerKey")
                        or raw_row.get("header")
                        or ""
                    )
                    .strip()
                    .lower()
                )

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
        # APPGENESIS_PROCESS_FIELDS_HEADER_ROWS_JSON_V4_END

        ok, error_message = update_sidebar_menu_process_fields(
            session=session,
            menu_key=clean_menu_key,
            visible_fields=clean_visible_fields,
            visible_headers=clean_visible_headers,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message
                    or "Não foi possível atualizar a configuração dos campos.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-config",
                    return_url=return_url,
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        success_redirect_url = _build_settings_editor_stay_redirect_url_v1(
            success_message="Configuração dos campos atualizada com sucesso.",
            redirect_menu=redirect_menu,
            settings_edit_key=clean_menu_key,
            settings_tab="campos-config",
            return_url=return_url,
        )
        _log_process_editor_flow_v1(
            request,
            "process_fields:success_redirect",
            redirect_menu=redirect_menu,
            redirect_target=_SETTINGS_MENU_EDITOR_STAY_TARGET_V1,
            final_url=success_redirect_url,
            return_url=return_url,
        )

        return RedirectResponse(
            url=success_redirect_url,
            status_code=status.HTTP_303_SEE_OTHER,
        )
