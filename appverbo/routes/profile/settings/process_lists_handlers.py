from __future__ import annotations

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.profile.router import router
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.menu.update_menu_process_lists import (
    execute_update_menu_process_lists_v1,
    normalize_update_menu_process_lists_input_v1,
)


# ###################################################################################
# (1) ENDPOINT - LISTAS DO PROCESSO
# ###################################################################################


@router.post("/settings/menu/process-lists", response_class=HTMLResponse)
def edit_sidebar_menu_process_lists_handler(
    request: Request,
    menu_key: str = Form(...),
    process_list_key: list[str] = Form(default=[]),
    process_list_label: list[str] = Form(default=[]),
    process_list_items_csv: list[str] = Form(default=[]),
    process_list_source: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    payload = normalize_update_menu_process_lists_input_v1(
        menu_key=menu_key,
        process_list_key=list(process_list_key or []),
        process_list_label=list(process_list_label or []),
        process_list_items_csv=list(process_list_items_csv or []),
        process_list_source=list(process_list_source or []),
        redirect_menu=redirect_menu,
        redirect_target=redirect_target,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_update_menu_process_lists_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )
