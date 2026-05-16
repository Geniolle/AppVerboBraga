from __future__ import annotations

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.profile.router import router
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.menu.update_menu_subsequent_fields import (
    execute_update_menu_subsequent_fields_v1,
    normalize_update_menu_subsequent_fields_input_v1,
)


# ###################################################################################
# (1) ENDPOINT - CAMPOS SUBSEQUENTES
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
    payload = normalize_update_menu_subsequent_fields_input_v1(
        menu_key=menu_key,
        subsequent_field_key=list(subsequent_field_key or []),
        subsequent_trigger_field=list(subsequent_trigger_field or []),
        subsequent_field=list(subsequent_field or []),
        subsequent_operator=list(subsequent_operator or []),
        subsequent_trigger_value=list(subsequent_trigger_value or []),
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

        outcome = execute_update_menu_subsequent_fields_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )
