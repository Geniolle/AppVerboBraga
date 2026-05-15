from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.entities.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.entities.delete_entity import execute_delete_entity_v1


logger = logging.getLogger(__name__)


# ###################################################################################
# (1) ROTA DE ELIMINAÇÃO DE ENTIDADE
# ###################################################################################

@router.post("/entities/delete", response_class=HTMLResponse)
def delete_entity_v1(
    request: Request,
    entity_id: str = Form(...),
) -> RedirectResponse:
    clean_entity_id = str(entity_id or "").strip()

    try:
        with SessionLocal() as session:
            current_user = get_current_user(request, session)

            if current_user is None:
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            outcome = execute_delete_entity_v1(
                session=session,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                entity_id=clean_entity_id,
            )

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "Erro inesperado ao eliminar entidade: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=(
                build_users_new_url(
                    entity_error=(
                        "Erro ao eliminar entidade. Consulte os logs recentes do serviço web."
                    ),
                    menu="administrativo",
                    admin_tab="entidade",
                )
                + "#recent-entities-card"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


delete_entity = delete_entity_v1
