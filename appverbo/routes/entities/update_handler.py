from __future__ import annotations

import logging
import traceback

from fastapi import File, Form, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.entities.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.entities.update_entity import (
    execute_update_entity_v1,
    normalize_update_entity_input_v1,
)


logger = logging.getLogger(__name__)


# ###################################################################################
# (1) ROTA DE ATUALIZAÇÃO DE ENTIDADE
# ###################################################################################

@router.post("/entities/update", response_class=HTMLResponse)
def update_entity_v1(
    request: Request,
    entity_id: str = Form(...),
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
    description: str | None = Form(default=None),
    entity_status: str = Form("active"),
    entity_profile_scope: str = Form("legado"),
    remove_logo: str | None = Form(default=None),
    entity_logo_file: UploadFile | None = File(default=None),
) -> RedirectResponse:
    try:
        payload = normalize_update_entity_input_v1(
            entity_id=entity_id,
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
            description=description,
            entity_status=entity_status,
            entity_profile_scope=entity_profile_scope,
            remove_logo=remove_logo,
            entity_logo_file=entity_logo_file,
        )

        with SessionLocal() as session:
            current_user = get_current_user(request, session)

            if current_user is None:
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            outcome = execute_update_entity_v1(
                session=session,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                payload=payload,
            )

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "Erro inesperado ao atualizar entidade: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=(
                build_users_new_url(
                    entity_error=(
                        "Erro ao atualizar entidade. Consulte os logs recentes do serviço web."
                    ),
                    menu="administrativo",
                    admin_tab="entidade",
                    entity_edit_id=str(entity_id or ""),
                )
                + "#edit-entity-card"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


update_entity = update_entity_v1
