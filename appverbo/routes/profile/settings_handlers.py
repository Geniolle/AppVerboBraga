# ###################################################################################
# (1) ATUALIZAÇÃO DOS CAMPOS ADICIONAIS DO PROCESSO MENU - V1
# ###################################################################################

from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.requests import Request as RequestType

from appverbo.routes.profile.router import router

# ###################################################################################
# (2) MOVER CAMPO ADICIONAL NO FORMULÁRIO - V1
# ###################################################################################

from appverbo.menu_settings import (
    move_sidebar_menu_additional_field,
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

@router.post("/settings/menu/field-move", response_class=HTMLResponse)
def move_sidebar_menu_additional_field_handler(
    request: Request,
    menu_key: str = Form(...),
    field_key: str = Form(...),
    direction: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = menu_key.strip().lower()

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
    clean_menu_key = menu_key.strip().lower()

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

        ok, error_message = update_sidebar_menu_additional_fields_v1(
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
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = menu_key.strip().lower()

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

        ok, error_message = update_sidebar_menu_process_fields(
            session=session,
            menu_key=clean_menu_key,
            visible_fields=visible_fields,
            visible_headers=visible_headers,
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
    clean_menu_key = menu_key.strip().lower()

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
    clean_menu_key = menu_key.strip().lower()

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
