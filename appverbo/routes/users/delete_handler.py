from __future__ import annotations

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.admin_subprocesses.utilizador.delete_service import execute_delete_user_v1
from appverbo.routes.users.router import router


# ###################################################################################
# (1) ROTA DE ELIMINACAO DE UTILIZADOR
# ###################################################################################

@router.post("/users/delete", response_class=HTMLResponse)
def delete_user_v1(
    request: Request,
    user_id: str = Form(...),
) -> RedirectResponse:
    return execute_delete_user_v1(
        request=request,
        user_id=user_id,
    )


delete_user = delete_user_v1