from __future__ import annotations

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.profile.router import router
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.menu.update_menu_quantity_fields import (
    execute_update_menu_quantity_fields_v1,
    normalize_update_menu_quantity_fields_input_v1,
)


# ###################################################################################
# (1) ENDPOINT - CAMPOS DE QUANTIDADE
# ###################################################################################


@router.post("/settings/menu/process-quantity-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_quantity_fields_handler(
    request: Request,
    menu_key: str = Form(...),
    quantity_rule_key: list[str] = Form(default=[]),
    quantity_rule_label: list[str] = Form(default=[]),
    quantity_field_key: list[str] = Form(default=[]),
    quantity_repeated_field_keys_json: list[str] = Form(default=[]),
    quantity_header_key: list[str] = Form(default=[]),
    quantity_max_items: list[str] = Form(default=[]),
    quantity_item_label: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
    subprocess_return_url: str = Form(""),
    return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_update_menu_quantity_fields_input_v1(
        menu_key=menu_key,
        quantity_rule_key=list(quantity_rule_key or []),
        quantity_rule_label=list(quantity_rule_label or []),
        quantity_field_key=list(quantity_field_key or []),
        quantity_repeated_field_keys_json=list(quantity_repeated_field_keys_json or []),
        quantity_header_key=list(quantity_header_key or []),
        quantity_max_items=list(quantity_max_items or []),
        quantity_item_label=list(quantity_item_label or []),
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

        outcome = execute_update_menu_quantity_fields_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )
