from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import RedirectResponse

from appverbo.routes.profile.settings.redirects import build_settings_redirect_url_v1
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_current_user, get_session_entity_id


####################################################################################
# (1) PERMISSÃO REUTILIZÁVEL PARA CONFIGURAÇÕES DO MENU
####################################################################################

def require_menu_settings_owner_v1(
    session,
    request: Request,
    redirect_menu: str = "administrativo",
    redirect_target: str = "#settings-menu-edit-card",
    settings_edit_key: str = "",
    settings_action: str = "edit",
    settings_tab: str = "geral",
) -> RedirectResponse | None:
    current_user = get_current_user(request, session)

    if current_user is None:
        return RedirectResponse(
            url="/login?error=Efetue login para continuar.",
            status_code=status.HTTP_302_FOUND,
        )

    if not is_admin_user(session, current_user["id"], current_user["login_email"]):
        return RedirectResponse(
            url=build_settings_redirect_url_v1(
                error_message="Apenas administradores podem alterar definições do menu.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=settings_edit_key,
                settings_action=settings_action,
                settings_tab=settings_tab,
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
            url=build_settings_redirect_url_v1(
                error_message="Apenas Owner pode alterar definições do menu.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=settings_edit_key,
                settings_action=settings_action,
                settings_tab=settings_tab,
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return None
