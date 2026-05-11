from __future__ import annotations

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.admin_subprocesses.utilizador.service import (
    execute_update_user_v1,
    normalize_update_user_input_v1,
)
from appverbo.models import UserAccountStatus
from appverbo.routes.users.router import router


# ###################################################################################
# (1) ROTA DE ATUALIZACAO DE UTILIZADOR
# ###################################################################################

@router.post("/users/update", response_class=HTMLResponse)
def update_user_v1(
    request: Request,
    user_id: str = Form(...),
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    entity_id: str = Form(""),
    account_status: str = Form(UserAccountStatus.ACTIVE.value),
    profile_id: str = Form(""),
) -> RedirectResponse:
    payload = normalize_update_user_input_v1(
        user_id=user_id,
        full_name=full_name,
        primary_phone=primary_phone,
        email=email,
        entity_id=entity_id,
        account_status=account_status,
        profile_id=profile_id,
    )

    return execute_update_user_v1(
        request=request,
        payload=payload,
    )


update_user = update_user_v1