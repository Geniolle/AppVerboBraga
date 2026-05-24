from __future__ import annotations

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.profile.router import router
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.menu.update_menu_process_fields import (
    execute_update_menu_process_fields_v1,
    normalize_update_menu_process_fields_input_v1,
)


# ###################################################################################
# (1) ENDPOINT - CAMPOS DO PROCESSO
# ###################################################################################


@router.post("/settings/menu/process-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_fields_handler(
    request: Request,
    menu_key: str = Form(...),
    visible_fields: list[str] = Form(default=[]),
    visible_headers: list[str] = Form(default=[]),
    visible_rows_json: str = Form(""),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
    subprocess_return_url: str = Form(""),
    return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_update_menu_process_fields_input_v1(
        menu_key=menu_key,
        visible_fields=list(visible_fields or []),
        visible_headers=list(visible_headers or []),
        visible_rows_json=visible_rows_json,
        redirect_menu=redirect_menu,
        redirect_target=redirect_target,
        subprocess_return_url=subprocess_return_url or return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_update_menu_process_fields_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )
