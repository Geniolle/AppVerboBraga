from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appgenesis.core import SessionLocal, templates
from appgenesis.routes.users.router import router
from appgenesis.services.page import build_users_new_url
from appgenesis.services.navigation_context import build_return_url_v1
from appgenesis.services.session import get_current_user, get_session_entity_id
from appgenesis.use_cases.users import execute_create_user, normalize_create_user_input_v1

logger = logging.getLogger(__name__)


@router.post("/users/new", response_class=HTMLResponse, response_model=None)
def create_user_v1(
    request: Request,
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    entity_id: str = Form(""),
    invite_delivery: str = Form("email"),
    system_profile: str = Form("default"),
    return_menu: str = Form(""),
    return_admin_tab: str = Form(""),
    return_target: str = Form(""),
):
    try:
        payload = normalize_create_user_input_v1(
            full_name=full_name,
            primary_phone=primary_phone,
            email=email,
            entity_id=entity_id,
            invite_delivery=invite_delivery,
            system_profile=system_profile,
        )

        with SessionLocal() as session:
            current_user = get_current_user(request, session)
            if current_user is None:
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            outcome = execute_create_user(
                session=session,
                request=request,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                payload=payload,
            )

        if outcome.kind == "template":
            return templates.TemplateResponse(
                request,
                "new_user.html",
                outcome.template_context or {},
                status_code=outcome.template_status_code,
            )

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "Erro inesperado ao criar utilizador por convite: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        safe_error = (
            "Erro ao criar utilizador por convite. "
            "Consulte os logs recentes do servico web para ver o detalhe tecnico."
        )
        return RedirectResponse(
            url=build_return_url_v1(
                return_menu=return_menu,
                return_admin_tab=return_admin_tab,
                error=safe_error,
                default_menu="administrativo",
                default_admin_tab="utilizador",
                default_hash="#create-user-card",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


create_user = create_user_v1
