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

# APPVERBO_SETTINGS_HANDLERS_SESSOES_MOVED_V1_START
# O subprocesso Sessões/Menu foi movido para:
# appverbo/routes/profile/settings/sidebar_sections_handlers.py
# APPVERBO_SETTINGS_HANDLERS_SESSOES_MOVED_V1_END

# APPVERBO_SETTINGS_HANDLERS_MENU_CRUD_MOVED_V1_START
# O CRUD principal do Menu foi movido para:
# appverbo/routes/profile/settings/menu_crud_handlers.py
# Rotas movidas: /settings/menu/edit, /settings/menu/create, /settings/menu/delete, /settings/menu/move
# APPVERBO_SETTINGS_HANDLERS_MENU_CRUD_MOVED_V1_END

# APPVERBO_SETTINGS_HANDLERS_ADDITIONAL_FIELDS_MOVED_V1_START
# Campos adicionais do Menu movidos para:
# appverbo/routes/profile/settings/additional_fields_handlers.py
# Rotas movidas: /settings/menu/field-move, /settings/menu/process-additional-fields
# APPVERBO_SETTINGS_HANDLERS_ADDITIONAL_FIELDS_MOVED_V1_END

# APPVERBO_SETTINGS_HANDLERS_PROCESS_FIELDS_MOVED_V1_START
# Campos do Processo/Menu movidos para:
# appverbo/routes/profile/settings/process_fields_handlers.py
# Rotas movidas: /settings/menu/process-fields
# APPVERBO_SETTINGS_HANDLERS_PROCESS_FIELDS_MOVED_V1_END

# APPVERBO_SETTINGS_HANDLERS_PROCESS_LISTS_MOVED_V1_START
# Listas do Processo/Menu movidas para:
# appverbo/routes/profile/settings/process_lists_handlers.py
# Rotas movidas: /settings/menu/process-lists
# APPVERBO_SETTINGS_HANDLERS_PROCESS_LISTS_MOVED_V1_END

# APPVERBO_SETTINGS_HANDLERS_PROCESS_QUANTITY_MOVED_V1_START
# Campos de Quantidade do Processo/Menu movidos para:
# appverbo/routes/profile/settings/process_quantity_handlers.py
# Rotas movidas: /settings/menu/process-quantity-fields
# APPVERBO_SETTINGS_HANDLERS_PROCESS_QUANTITY_MOVED_V1_END
