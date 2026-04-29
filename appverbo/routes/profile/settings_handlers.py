# ###################################################################################
# (1) ATUALIZAÇÃO DOS CAMPOS ADICIONAIS DO PROCESSO MENU - V1
# ###################################################################################

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.requests import Request as RequestType

from appverbo.routes.profile.router import router

# ###################################################################################
# (2) MOVER CAMPO ADICIONAL NO FORMULÁRIO - V1
# ###################################################################################

from appverbo.menu_settings import move_sidebar_menu_additional_field
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