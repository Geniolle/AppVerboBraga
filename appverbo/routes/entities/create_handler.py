from __future__ import annotations

import logging
import traceback

from fastapi import File, Form, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal, templates
from appverbo.routes.entities.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.entities.create_entity import (
    execute_create_entity_v1,
    normalize_create_entity_input_v1,
)


logger = logging.getLogger(__name__)


# ###################################################################################
# (1) ROTA DE CRIAÇÃO DE ENTIDADE
# ###################################################################################

@router.post("/entities/new", response_class=HTMLResponse)
def create_entity_v1(
    request: Request,
    name: str = Form(...),
    acronym: str = Form(""),
    tax_id: str = Form(...),
    email: str = Form(...),
    responsible_name: str = Form(...),
    door_number: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    freguesia: str = Form(...),
    postal_code: str = Form(...),
    country: str = Form(...),
    phone: str = Form(...),
    entity_profile_scope: str = Form("legado"),
    entity_logo_file: UploadFile | None = File(default=None),
    description: str | None = Form(default=None),
):
    try:
        payload = normalize_create_entity_input_v1(
            name=name,
            acronym=acronym,
            tax_id=tax_id,
            email=email,
            responsible_name=responsible_name,
            door_number=door_number,
            address=address,
            city=city,
            freguesia=freguesia,
            postal_code=postal_code,
            country=country,
            phone=phone,
            entity_profile_scope=entity_profile_scope,
            description=description,
            entity_logo_file=entity_logo_file,
        )

        with SessionLocal() as session:
            current_user = get_current_user(request, session)

            if current_user is None:
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            outcome = execute_create_entity_v1(
                session=session,
                request=request,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                payload=payload,
            )

        if outcome.kind == "template":
            template_context = dict(outcome.template_context or {})
            template_context.setdefault("admin_topbar_color_hex", "#334A62")
            return templates.TemplateResponse(
                request,
                "new_user.html",
                template_context,
                status_code=outcome.template_status_code,
            )

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "Erro inesperado ao criar entidade: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=(
                build_users_new_url(
                    entity_error=(
                        "Erro ao criar entidade. Consulte os logs recentes do serviço web."
                    ),
                    menu="administrativo",
                    admin_tab="entidade",
                )
                + "#create-entity-card"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


create_entity = create_entity_v1
