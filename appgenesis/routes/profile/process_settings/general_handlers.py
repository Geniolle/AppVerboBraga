# ###################################################################################
# (MENU_SETTINGS_CRUD_V1) GRAVAR CONFIGURACOES GERAIS DAS PASTAS
# ###################################################################################

from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from appgenesis.routes.profile.router import router
from appgenesis.routes.profile.process_settings.common import (
    _build_settings_redirect_url,
    _build_settings_editor_stay_redirect_url_v1,
    _require_menu_settings_owner_v1,
    _SETTINGS_MENU_EDITOR_STAY_TARGET_V1,
)
from appgenesis.menu_settings import (
    create_sidebar_menu_setting,
    delete_sidebar_menu_setting,
    move_sidebar_menu_setting,
    resolve_menu_key_alias,
    set_sidebar_menu_visibility,
    update_sidebar_menu_label,
)
from appgenesis.core import SessionLocal
from appgenesis.services.session import get_session_entity_id
from appgenesis.repositories.entity_repository import get_entity_by_id


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
    return_url: str = Form(""),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)
    clean_status = str(menu_status or "").strip().lower()
    make_visible = clean_status not in {
        "inativo",
        "inactive",
        "0",
        "false",
        "no",
        "nao",
        "não",
        "off",
    }

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
            settings_edit_key=clean_menu_key,
            settings_action="edit",
            settings_tab="geral",
            return_url=return_url,
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
                        error_message=error_message
                        or "Não foi possível atualizar o estado do menu.",
                        redirect_menu=redirect_menu,
                        redirect_target=redirect_target,
                        settings_edit_key=clean_menu_key,
                        settings_action="edit",
                        settings_tab="geral",
                        return_url=return_url,
                    ),
                    status_code=HTTP_303_SEE_OTHER,
                )

        _session_entity_id = get_session_entity_id(request)
        _session_entity = (
            get_entity_by_id(session, _session_entity_id)
            if _session_entity_id is not None
            else None
        )
        _session_entity_number = (
            _session_entity.entity_number if _session_entity is not None else None
        )

        ok, error_message = update_sidebar_menu_label(
            session,
            clean_menu_key,
            menu_label,
            menu_visibility_scope,
            menu_sidebar_section,
            entity_number=_session_entity_number,
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
                    return_url=return_url,
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
                        error_message=error_message
                        or "Não foi possível atualizar o estado do menu.",
                        redirect_menu=redirect_menu,
                        redirect_target=redirect_target,
                        settings_edit_key=clean_menu_key,
                        settings_action="edit",
                        settings_tab="geral",
                        return_url=return_url,
                    ),
                    status_code=HTTP_303_SEE_OTHER,
                )

        # O hidden "redirect_target" enviado pela aba Geral distingue permanecer no editor
        # (valor legado "settings-menu-edit-card") de sair para a lista de origem (qualquer
        # outro alvo, resolvido no template a partir do menu/aba de onde o editor foi aberto).
        clean_redirect_target = str(redirect_target or "").strip().lstrip("#")

        if clean_redirect_target == _SETTINGS_MENU_EDITOR_STAY_TARGET_V1:
            success_redirect_url = _build_settings_editor_stay_redirect_url_v1(
                success_message="Menu atualizado com sucesso.",
                redirect_menu=redirect_menu,
                settings_edit_key=clean_menu_key,
                settings_tab="geral",
                return_url=return_url,
            )
        else:
            success_redirect_url = _build_settings_redirect_url(
                success_message="Menu atualizado com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                return_url=return_url,
            )

        return RedirectResponse(
            url=success_redirect_url,
            status_code=HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/create", response_class=HTMLResponse)
def create_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_label: str = Form(...),
    menu_visibility_scope: str = Form("all"),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-account-status-card"),
    return_url: str = Form(""),
) -> RedirectResponse:
    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
            settings_action="create",
            return_url=return_url,
        )
        if blocked_response is not None:
            return blocked_response

        selected_entity_id = get_session_entity_id(request)
        if selected_entity_id is None:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Não foi possível identificar a entidade ativa.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        ok, error_message, new_menu_key = create_sidebar_menu_setting(
            session,
            selected_entity_id,
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
                    if str(redirect_target or "").lstrip("#")
                    == "settings-menu-edit-card"
                    else ""
                ),
                settings_action=(
                    "edit"
                    if str(redirect_target or "").lstrip("#")
                    == "settings-menu-edit-card"
                    else ""
                ),
                settings_tab=(
                    "geral"
                    if str(redirect_target or "").lstrip("#")
                    == "settings-menu-edit-card"
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
    return_url: str = Form(""),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
            return_url=return_url,
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
