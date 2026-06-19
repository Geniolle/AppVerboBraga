
from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.users.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.users import execute_delete_user


logger = logging.getLogger(__name__)


@router.post("/users/delete", response_class=HTMLResponse)
def delete_user_v1(
    request: Request,
    user_id: str = Form(...),
) -> RedirectResponse:
    clean_user_id = user_id.strip()

    if not clean_user_id.isdigit():
        return RedirectResponse(
            url=build_users_new_url(
                error="Utilizador inválido para eliminação.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        with SessionLocal() as session:
            current_user = get_current_user(request, session)

            if current_user is None:
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            outcome = execute_delete_user(
                session=session,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                user_id=int(clean_user_id),
            )

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "Erro inesperado ao eliminar utilizador: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=build_users_new_url(
                error="Erro ao eliminar utilizador. Consulte os logs recentes do serviço web.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )


delete_user = delete_user_v1
