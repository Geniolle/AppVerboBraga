from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appgenesis.core import *  # noqa: F403,F401
from appgenesis.services import *  # noqa: F403,F401
from appgenesis.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    User,
    UserAccountStatus,
)

from appgenesis.routes.entities.router import router

@router.post("/entities/delete", response_class=HTMLResponse)
def delete_entity(
    request: Request,
    entity_id: str = Form(...),
    return_menu: str = Form(""),
    return_admin_tab: str = Form(""),
    return_target: str = Form(""),
) -> HTMLResponse:
    clean_entity_id = entity_id.strip()
    if not clean_entity_id.isdigit():
        return RedirectResponse(
            url=build_return_url_v1(
                return_menu=return_menu,
                return_admin_tab=return_admin_tab,
                default_menu="administrativo",
                default_admin_tab="entidade",
                default_hash="#recent-entities-card",
                entity_error="Entidade inválida para exclusão.",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    parsed_entity_id = int(clean_entity_id)
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        selected_entity_id = get_session_entity_id(request)

        current_user_is_admin = is_admin_user(
            session, current_user["id"], current_user["login_email"]
        )
        if not current_user_is_admin:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#recent-entities-card",
                    entity_error="Apenas administradores podem excluir entidades.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        if not is_entity_within_permissions(parsed_entity_id, entity_permissions):
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#recent-entities-card",
                    entity_error="Sem permissão para eliminar esta entidade.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        entity = session.get(Entity, parsed_entity_id)
        if entity is None:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#recent-entities-card",
                    entity_error="Entidade não encontrada.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # APPGENESIS_DELETE_ONLY_INACTIVE_ENTITY_V1_START
        if entity.is_active:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#edit-entity-card",
                    entity_error="Só é permitido eliminar entidades inativas.",
                    entity_edit_id=str(parsed_entity_id),
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        # APPGENESIS_DELETE_ONLY_INACTIVE_ENTITY_V1_END

        linked_users_count = session.scalar(
            select(func.count(User.id))
           .join(MemberEntity, MemberEntity.member_id == User.member_id)
           .where(MemberEntity.entity_id == parsed_entity_id)
        )
        if linked_users_count and int(linked_users_count) > 0:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#edit-entity-card",
                    entity_error="Não pode excluir entidade com utilizadores associados. Inative a entidade.",
                    entity_edit_id=str(parsed_entity_id),
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        logo_url_to_remove = entity.logo_url or ""
        session.execute(
            delete(MemberEntity).where(MemberEntity.entity_id == parsed_entity_id)
        )
        session.delete(entity)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#recent-entities-card",
                    entity_error="Não foi possível excluir a entidade.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    if logo_url_to_remove.startswith("/static/entities/"):
        (BASE_DIR / logo_url_to_remove.lstrip("/")).unlink(missing_ok=True)

    return RedirectResponse(
        url=build_return_url_v1(
            return_menu=return_menu,
            return_admin_tab=return_admin_tab,
            default_menu="administrativo",
            default_admin_tab="entidade",
            default_hash="#recent-entities-card",
            entity_success="Entidade excluida com sucesso.",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
