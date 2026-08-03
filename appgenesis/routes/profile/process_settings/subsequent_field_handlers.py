from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER

from appgenesis.routes.profile.router import router

from appgenesis.menu_settings import (
    resolve_menu_key_alias,
    update_sidebar_menu_subsequent_fields,
)
from appgenesis.core import SessionLocal
from appgenesis.services.session import get_current_user, get_session_entity_id
from appgenesis.services.auth import is_admin_user
from appgenesis.services.permissions import get_user_entity_permissions

from appgenesis.routes.profile.process_settings.common import (
    _build_settings_redirect_url,
    _build_settings_editor_stay_redirect_url_v1,
)


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
    return_url: str = Form(""),
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
                    return_url=return_url,
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

        if not permissions.get(
            "can_manage_tenant_structure",
            permissions.get("can_manage_all_entities", False),
        ):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode configurar campos subsequentes.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos_subsequentes",
                    return_url=return_url,
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
            if row_index < len(subsequent_trigger_field) and row_index < len(
                subsequent_field
            ):
                payload_fields.append(
                    {
                        "key": subsequent_field_key[row_index]
                        if row_index < len(subsequent_field_key)
                        else "",
                        "trigger_field": subsequent_trigger_field[row_index]
                        if row_index < len(subsequent_trigger_field)
                        else "",
                        "field_key": subsequent_field[row_index]
                        if row_index < len(subsequent_field)
                        else "",
                        "operator": subsequent_operator[row_index]
                        if row_index < len(subsequent_operator)
                        else "",
                        "trigger_value": subsequent_trigger_value[row_index]
                        if row_index < len(subsequent_trigger_value)
                        else "",
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
                    error_message=error_message
                    or "Não foi possível atualizar os campos subsequentes.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos_subsequentes",
                    return_url=return_url,
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_editor_stay_redirect_url_v1(
                success_message="Campos subsequentes atualizados com sucesso.",
                redirect_menu=redirect_menu,
                settings_edit_key=clean_menu_key,
                settings_tab="campos-subsequentes",
                return_url=return_url,
            ),
            status_code=HTTP_303_SEE_OTHER,
        )
