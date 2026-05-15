from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.models import UserAccountStatus
from appverbo.routes.users.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.users import execute_update_user


logger = logging.getLogger(__name__)


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
    try:
        with SessionLocal() as session:
            current_user = get_current_user(request, session)

            if current_user is None:
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            outcome = execute_update_user(
                session=session,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                user_id=user_id,
                full_name=full_name,
                primary_phone=primary_phone,
                email=email,
                entity_id=entity_id,
                account_status=account_status,
                profile_id=profile_id,
            )

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "Erro inesperado ao atualizar utilizador: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=build_users_new_url(
                error="Erro ao atualizar utilizador. Consulte os logs recentes do serviço web.",
                menu="administrativo",
                admin_tab="utilizador",
                user_edit_id=user_id,
            )
            + "#edit-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )


update_user = update_user_v1
