
from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.users.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.users import (
    prepare_user_invite_payload_v1,
    redirect_admin_users_v1,
    send_user_invite_v1,
)


logger = logging.getLogger(__name__)


def _generate_user_invite_v1(
    *,
    request: Request,
    user_id: str,
    raw_entity_id: str = "",
) -> RedirectResponse:
    clean_user_id = user_id.strip()

    if not clean_user_id.isdigit():
        outcome = redirect_admin_users_v1(error="Utilizador inválido para gerar convite.")
        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    try:
        with SessionLocal() as session:
            current_user = get_current_user(request, session)

            if current_user is None:
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            payload, early_outcome = prepare_user_invite_payload_v1(
                session=session,
                request=request,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                user_id=int(clean_user_id),
                raw_entity_id=raw_entity_id,
            )

        if early_outcome is not None:
            return RedirectResponse(
                url=early_outcome.redirect_url,
                status_code=early_outcome.redirect_status_code,
            )

        if payload is None:
            outcome = redirect_admin_users_v1(error="Não foi possível gerar convite.")
        else:
            outcome = send_user_invite_v1(payload)

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "Erro inesperado ao gerar convite: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=build_users_new_url(
                error="Erro ao gerar convite. Consulte os logs recentes do serviço web.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/users/generate-invite", response_class=HTMLResponse)
def generate_user_invite_v1(
    request: Request,
    user_id: str = Form(...),
    entity_id: str = Form(""),
) -> RedirectResponse:
    return _generate_user_invite_v1(
        request=request,
        user_id=user_id,
        raw_entity_id=entity_id,
    )


@router.post("/users/resend-invite", response_class=HTMLResponse)
def resend_user_invite_v1(
    request: Request,
    user_id: str = Form(...),
) -> RedirectResponse:
    return _generate_user_invite_v1(
        request=request,
        user_id=user_id,
        raw_entity_id="",
    )


generate_user_invite = generate_user_invite_v1
resend_user_invite = resend_user_invite_v1
