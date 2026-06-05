from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.entities.router import router
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.entities.delete_entity import (
    build_entity_delete_unexpected_error_redirect_v1,
    execute_delete_entity_v1,
)


logger = logging.getLogger(__name__)


# ###################################################################################
# (1) ROTA DE ELIMINACAO DE ENTIDADE
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
            "APPVERBO_DELETE_ENTITY_ROUTE_V2 unexpected_error entity_id=%s error=%s\n%s",
            clean_entity_id,
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=build_entity_delete_unexpected_error_redirect_v1(
                entity_error=(
                    "Erro ao eliminar entidade. Consulte os logs recentes do serviço web."
                ),
                clean_entity_id=clean_entity_id,
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


delete_entity = delete_entity_v1
