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
