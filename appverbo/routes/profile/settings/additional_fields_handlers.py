from __future__ import annotations

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.profile.router import router
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.menu.update_menu_additional_fields import (
    execute_move_menu_additional_field_v1,
    execute_update_menu_additional_fields_v1,
    normalize_move_menu_additional_field_input_v1,
    normalize_update_menu_additional_fields_input_v1,
)


# ###################################################################################
# (1) ENDPOINT - MOVER CAMPO ADICIONAL
# ###################################################################################


@router.post("/settings/menu/field-move", response_class=HTMLResponse)
def move_sidebar_menu_additional_field_handler(
    request: Request,
    menu_key: str = Form(...),
    field_key: str = Form(...),
    direction: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    payload = normalize_move_menu_additional_field_input_v1(
        menu_key=menu_key,
        field_key=field_key,
        direction=direction,
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

        outcome = execute_move_menu_additional_field_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )


# ###################################################################################
# (2) ENDPOINT - GRAVAR CAMPOS ADICIONAIS
# ###################################################################################


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
    payload = normalize_update_menu_additional_fields_input_v1(
        menu_key=menu_key,
        additional_field_key=list(additional_field_key or []),
        additional_field_label=list(additional_field_label or []),
        additional_field_type=list(additional_field_type or []),
        additional_field_required=list(additional_field_required or []),
        additional_field_size=list(additional_field_size or []),
        additional_field_list_key=list(additional_field_list_key or []),
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

        outcome = execute_update_menu_additional_fields_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )
