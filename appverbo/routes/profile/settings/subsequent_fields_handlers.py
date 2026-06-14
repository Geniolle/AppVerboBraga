from __future__ import annotations

from urllib.parse import parse_qsl, urlsplit

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.profile.router import router
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.menu.update_menu_subsequent_fields import (
    execute_update_menu_subsequent_fields_v1,
    normalize_update_menu_subsequent_fields_input_v1,
)

_SILENT_REFRESH_HEADER = "X-AppVerbo-Silent-Refresh"


def _is_silent_request(request: Request) -> bool:
    return request.headers.get(_SILENT_REFRESH_HEADER) == "1"


def _parse_outcome_message(redirect_url: str) -> tuple[bool, str]:
    params = dict(parse_qsl(urlsplit(redirect_url).query))
    if "settings_success" in params:
        return True, params["settings_success"]
    return False, params.get("settings_error", "Não foi possível atualizar os campos subsequentes.")


# ###################################################################################
# (1) ENDPOINT - CAMPOS SUBSEQUENTES
# ###################################################################################


@router.post("/settings/menu/process-subsequent-fields", response_class=HTMLResponse, response_model=None)
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
    subprocess_return_url: str = Form(""),
    return_url: str = Form(""),
) -> RedirectResponse | JSONResponse:
    silent = _is_silent_request(request)

    payload = normalize_update_menu_subsequent_fields_input_v1(
        menu_key=menu_key,
        subsequent_field_key=list(subsequent_field_key or []),
        subsequent_trigger_field=list(subsequent_trigger_field or []),
        subsequent_field=list(subsequent_field or []),
        subsequent_operator=list(subsequent_operator or []),
        subsequent_trigger_value=list(subsequent_trigger_value or []),
        redirect_menu=redirect_menu,
        redirect_target=redirect_target,
        subprocess_return_url=subprocess_return_url or return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            if silent:
                return JSONResponse(
                    {"success": False, "message": "Sessão expirada. Efetue login para continuar."},
                    status_code=status.HTTP_200_OK,
                )
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

    if silent:
        is_success, message = _parse_outcome_message(outcome.redirect_url)
        if is_success:
            return JSONResponse({"success": True, "message": message}, status_code=status.HTTP_200_OK)
        return JSONResponse(
            {"success": False, "message": message, "redirectUrl": outcome.redirect_url},
            status_code=status.HTTP_200_OK,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )
