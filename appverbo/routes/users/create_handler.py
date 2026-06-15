from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.admin_subprocesses.utilizador.pagina import (
    montar_estado_pagina_utilizador_v1,
)
from appverbo.use_cases.users.create_user import (
    execute_create_user,
    normalize_create_user_input_v1,
)
from appverbo.core import SessionLocal, templates
from appverbo.routes.users.router import router
from appverbo.services.page import (
    build_users_new_url,
    ensure_new_user_template_context_defaults_v1,
)
from appverbo.services.session import get_current_user, get_session_entity_id


logger = logging.getLogger(__name__)


# ###################################################################################
# (1) HIDRATACAO DE ERRO DO SUBPROCESSO UTILIZADOR
# ###################################################################################

def _hydrate_admin_user_create_error_context_v1(
    *,
    request: Request,
    session,
    template_context: dict[str, object],
) -> dict[str, object]:
    clean_context = ensure_new_user_template_context_defaults_v1(template_context)

    if str(clean_context.get("admin_tab") or "").strip().lower() != "utilizador":
        return clean_context

    entity_permissions = dict(clean_context.get("entity_permissions") or {})
    form_data = dict(clean_context.get("form_data") or {})
    form_data.setdefault("account_status", "pending")
    entity_rows = clean_context.get("entities")
    profile_rows = clean_context.get("profiles")

    allowed_entity_ids = list(entity_permissions.get("allowed_entity_ids") or [])

    if not allowed_entity_ids and bool(clean_context.get("current_user_can_manage_all_entities")):
        allowed_entity_ids = [
            int(raw_row.get("id"))
            for raw_row in (entity_rows or [])
            if str(raw_row.get("id") or "").strip().isdigit()
        ]

    selected_entity_id_for_state = get_session_entity_id(request)

    if str(form_data.get("entity_id") or "").strip().isdigit():
        selected_entity_id_for_state = int(str(form_data.get("entity_id") or "").strip())

    error_messages = [
        str(raw_error or "").strip()
        for raw_error in (clean_context.get("errors") or [])
        if str(raw_error or "").strip()
    ]
    joined_error = " ".join(error_messages)

    admin_subprocess_state = montar_estado_pagina_utilizador_v1(
        session=session,
        user_edit_id="",
        create_data=form_data,
        selected_entity_id=selected_entity_id_for_state,
        allowed_entity_ids=allowed_entity_ids,
        entity_rows=entity_rows,
        profile_rows=profile_rows,
        success=str(clean_context.get("success") or "").strip(),
        error=joined_error,
    )

    if admin_subprocess_state is not None and bool(clean_context.get("current_user_is_admin")):
        admin_subprocess_state.show_field_hints = True

    clean_context["admin_subprocess_state_utilizador_v1"] = admin_subprocess_state
    clean_context["admin_subprocess_state_utilizador"] = admin_subprocess_state
    clean_context["admin_subprocess_state"] = admin_subprocess_state
    clean_context["admin_subprocess_shadow_state_v1"] = admin_subprocess_state
    clean_context["admin_subprocess_shadow_state"] = admin_subprocess_state
    clean_context.setdefault("error", joined_error)

    return clean_context


# ###################################################################################
# (2) ROTA DE CRIACAO DE UTILIZADOR
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
            with SessionLocal() as render_session:
                template_context = _hydrate_admin_user_create_error_context_v1(
                    request=request,
                    session=render_session,
                    template_context=dict(outcome.template_context or {}),
                )
            return templates.TemplateResponse(
                request,
                "new_user.html",
                template_context,
                status_code=status.HTTP_200_OK,
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
