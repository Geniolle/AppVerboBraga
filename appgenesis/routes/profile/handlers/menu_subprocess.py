from fastapi import (
    Request,
    Form,
)
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from appgenesis.routes.profile.router import router
from appgenesis.menu_settings import (
    create_sidebar_menu_setting,
    delete_sidebar_menu_setting,
    move_sidebar_menu_setting,
    resolve_menu_key_alias,
)
from appgenesis.db.session import SessionLocal
from appgenesis.services.session import get_current_user
from appgenesis.services.auth import is_admin_user
from appgenesis.services.session import get_session_entity_id
from starlette.status import (
    HTTP_302_FOUND,
    HTTP_303_SEE_OTHER,
)
from appgenesis.routes.profile.process_settings.common import (
    _build_settings_redirect_url,
    _require_menu_settings_owner_v1,
)

# APPGENESIS_SIDEBAR_SECTIONS_HANDLER_V2_END

# ###################################################################################
# (MENU_SETTINGS_CRUD_V1) GRAVAR CONFIGURACOES GERAIS DAS PASTAS -- movido para
# appgenesis/routes/profile/process_settings/general_handlers.py (Fase 8)
# ###################################################################################

# (1)/(2) CAMPOS ADICIONAIS DO PROCESSO MENU + PRESERVE_HEADER_ASSIGNMENTS_V1 --
# movidos para appgenesis/routes/profile/process_settings/additional_field_handlers.py
# (Fase 8)

# (3) CONFIGURACAO DOS CAMPOS DO PROCESSO MENU -- movido para
# appgenesis/routes/profile/process_settings/field_handlers.py (Fase 8)

# (4) CAMPOS QUANTIDADE DO PROCESSO MENU -- movido para
# appgenesis/routes/profile/process_settings/quantity_field_handlers.py (Fase 8)

# (5) LISTAS DO PROCESSO MENU -- movido para
# appgenesis/routes/profile/process_settings/list_handlers.py (Fase 8)

# (4) CAMPOS SUBSEQUENTES -- movido para
# appgenesis/routes/profile/process_settings/subsequent_field_handlers.py (Fase 8)

_MENU_SUBPROCESS_DEFAULT_RETURN_URL = (
    "/users/new?menu=sessoes&admin_tab=contas&target=menu-subprocess-card-active"
    "#menu-subprocess-card-active"
)

@router.post("/settings/menu/menu-save", response_class=HTMLResponse)
def menu_subprocess_save_handler_v1(
    request: Request,
    menu_label: str = Form(...),
    menu_visibility_scope: str = Form("all"),
    subprocess_mode: str = Form("create"),
    subprocess_edit_key: str = Form(""),
    subprocess_return_url: str = Form(_MENU_SUBPROCESS_DEFAULT_RETURN_URL),
) -> RedirectResponse:
    clean_return_url = (
        str(subprocess_return_url or "").strip() or _MENU_SUBPROCESS_DEFAULT_RETURN_URL
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=f"{clean_return_url}&error=Apenas administradores podem alterar definições do menu.",
                status_code=HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        if selected_entity_id is None:
            return RedirectResponse(
                url=f"{clean_return_url}&error=Não foi possível identificar a entidade ativa.",
                status_code=HTTP_303_SEE_OTHER,
            )

        ok, error_message, _new_key = create_sidebar_menu_setting(
            session,
            selected_entity_id,
            menu_label,
            menu_visibility_scope,
        )

        if not ok:
            return RedirectResponse(
                url=f"{clean_return_url}&error={error_message or 'Não foi possível criar o menu.'}",
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=f"{clean_return_url}&success=Menu criado com sucesso.",
            status_code=HTTP_303_SEE_OTHER,
        )

@router.post("/settings/menu/menu-move", response_class=HTMLResponse)
def menu_subprocess_move_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    direction: str = Form(...),
    subprocess_return_url: str = Form(_MENU_SUBPROCESS_DEFAULT_RETURN_URL),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)
    clean_return_url = (
        str(subprocess_return_url or "").strip() or _MENU_SUBPROCESS_DEFAULT_RETURN_URL
    )

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            "sessoes",
            "#menu-subprocess-card-active",
            return_url=clean_return_url,
        )
        if blocked_response is not None:
            return blocked_response

        ok, error_message = move_sidebar_menu_setting(
            session, clean_menu_key, direction
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível mover o menu.",
                    redirect_menu="sessoes",
                    redirect_target="#menu-subprocess-card-active",
                    return_url=clean_return_url,
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Ordem do menu atualizada com sucesso.",
                redirect_menu="sessoes",
                redirect_target="#menu-subprocess-card-active",
                return_url=clean_return_url,
            ),
            status_code=HTTP_303_SEE_OTHER,
        )

@router.post("/settings/menu/menu-delete", response_class=HTMLResponse)
def menu_subprocess_delete_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    subprocess_return_url: str = Form(_MENU_SUBPROCESS_DEFAULT_RETURN_URL),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)
    clean_return_url = (
        str(subprocess_return_url or "").strip() or _MENU_SUBPROCESS_DEFAULT_RETURN_URL
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=f"{clean_return_url}&error=Apenas administradores podem alterar definições do menu.",
                status_code=HTTP_303_SEE_OTHER,
            )

        ok, error_message = delete_sidebar_menu_setting(session, clean_menu_key)

        if not ok:
            return RedirectResponse(
                url=f"{clean_return_url}&error={error_message or 'Não foi possível eliminar o menu.'}",
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=f"{clean_return_url}&success=Menu eliminado com sucesso.",
            status_code=HTTP_303_SEE_OTHER,
        )
