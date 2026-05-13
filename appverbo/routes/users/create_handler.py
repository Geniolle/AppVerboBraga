from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.admin_subprocesses.utilizador.create_service import (
    execute_create_user,
    normalize_create_user_input_v1,
)
from appverbo.core import SessionLocal, templates
from appverbo.routes.users.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id


logger = logging.getLogger(__name__)


# ###################################################################################
# (1) ROTA DE CRIACAO DE UTILIZADOR
# ###################################################################################

@router.post("/users/new", response_class=HTMLResponse, response_model=None)
def create_user_v1(
    request: Request,
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    entity_id: str = Form(""),
    profile_id: str = Form(""),
    invite_delivery: str = Form("email"),
):
    try:
        clean_entity_id = (entity_id or "").strip()
        clean_profile_id = (profile_id or "").strip()

        if not clean_entity_id:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Entidade é obrigatória.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not clean_profile_id:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Perfil global é obrigatório.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        explicit_entity_id: int | None = None
        if clean_entity_id.isdigit():
            explicit_entity_id = int(clean_entity_id)
        else:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Entidade inválida.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        payload = normalize_create_user_input_v1(
            full_name=full_name,
            primary_phone=primary_phone,
            email=email,
            entity_id=entity_id,
            profile_id=profile_id,
            invite_delivery=invite_delivery,
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
                explicit_entity_id=explicit_entity_id,
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
            url=build_users_new_url(
                error=safe_error,
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )


create_user = create_user_v1
