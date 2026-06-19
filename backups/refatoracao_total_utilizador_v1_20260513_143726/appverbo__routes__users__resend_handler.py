from __future__ import annotations

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.admin_subprocesses.utilizador.resend_service import (
    execute_generate_user_invite_v1,
    execute_resend_user_invite_v1,
)
from appverbo.routes.users.router import router


# ###################################################################################
# (1) ROTA PARA GERAR CONVITE DE UTILIZADOR
# ###################################################################################

@router.post("/users/generate-invite", response_class=HTMLResponse)
def generate_user_invite_v1(
    request: Request,
    user_id: str = Form(...),
    entity_id: str = Form(""),
) -> RedirectResponse:
    return execute_generate_user_invite_v1(
        request=request,
        user_id=user_id,
        entity_id=entity_id,
    )


# ###################################################################################
# (2) ROTA PARA REENVIAR CONVITE DE UTILIZADOR
# ###################################################################################

@router.post("/users/resend-invite", response_class=HTMLResponse)
def resend_user_invite_v1(
    request: Request,
    user_id: str = Form(...),
) -> RedirectResponse:
    return execute_resend_user_invite_v1(
        request=request,
        user_id=user_id,
    )


generate_user_invite = generate_user_invite_v1
resend_user_invite = resend_user_invite_v1