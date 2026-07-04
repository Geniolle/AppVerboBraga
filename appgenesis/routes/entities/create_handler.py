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

@router.post("/entities/new", response_class=HTMLResponse)
def create_entity(
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
    entity_profile_scope: str = Form(ENTITY_PROFILE_SCOPE_LEGADO),
    entity_logo_file: UploadFile | None = File(default=None),
    description: str | None = Form(default=None),
    return_menu: str = Form(""),
    return_admin_tab: str = Form(""),
    return_target: str = Form(""),
) -> HTMLResponse:
    entity_form_data, invalid_profile_scope = clean_entity_form_data_v1(
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
        created_at_text=date.today().strftime("%d/%m/%Y"),
    )
    clean_name = entity_form_data["name"]
    clean_profile_scope = entity_form_data["profile_scope"]

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
                url=build_users_new_url(
                    entity_error="Apenas administradores podem criar entidades.",
                    menu="perfil",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        if not entity_permissions.get("can_create_legacy_entities", entity_permissions.get("can_manage_all_entities", False)):
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    default_menu="administrativo",
                    default_admin_tab="entidade",
                    default_hash="#create-entity-card",
                    entity_error="Apenas a entidade Owner pode criar novas entidades.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        page_data = get_page_data(
            session,
            actor_user_id=current_user["id"],
            actor_login_email=current_user["login_email"],
            selected_entity_id=selected_entity_id,
        )
        user_personal_data = get_user_personal_data(session, current_user["id"], selected_entity_id)
        next_entity_number = get_next_entity_number(session)

        required_field_labels = validate_entity_required_fields_v1(entity_form_data)
        if invalid_profile_scope:
            required_field_labels.append("Perfil de partilha")

        if required_field_labels:
            context = {
                "request": request,
                "errors": [],
                "success": "",
                "form_data": get_form_defaults(),
                "entity_form_data": entity_form_data,
                "entity_edit_data": get_entity_edit_defaults(),
                "current_user": current_user,
                "current_user_is_admin": current_user_is_admin,
                "user_personal_data": user_personal_data,
                "entity_success": "",
                "entity_error": (
                    "Preencha os campos obrigatórios: " + ", ".join(required_field_labels) + "."
                ),
                "next_entity_number": str(next_entity_number),
                "profile_success": "",
                "profile_error": "",
                "profile_tab": "pessoal",
                "initial_menu": "administrativo",
                "admin_tab": "entidade",
                **page_data,
            }
            return templates.TemplateResponse(
                request,
                "new_user.html",
                context,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        existing_entity = get_duplicate_entity_name_id_v1(session, clean_name)
        if existing_entity is not None:
            context = {
                "request": request,
                "errors": [],
                "success": "",
                "form_data": get_form_defaults(),
                "entity_form_data": entity_form_data,
                "entity_edit_data": get_entity_edit_defaults(),
                "current_user": current_user,
                "current_user_is_admin": current_user_is_admin,
                "user_personal_data": user_personal_data,
                "entity_success": "",
                "entity_error": "Já existe uma entidade com este nome.",
                "next_entity_number": str(next_entity_number),
                "profile_success": "",
                "profile_error": "",
                "profile_tab": "pessoal",
                "initial_menu": "administrativo",
                "admin_tab": "entidade",
                **page_data,
            }
            return templates.TemplateResponse(
                request,
                "new_user.html",
                context,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if clean_profile_scope == ENTITY_PROFILE_SCOPE_OWNER:
            existing_owner_id = get_existing_owner_entity_id_v1(session)
            if existing_owner_id is not None:
                context = {
                    "request": request,
                    "errors": [],
                    "success": "",
                    "form_data": get_form_defaults(),
                    "entity_form_data": entity_form_data,
                    "entity_edit_data": get_entity_edit_defaults(),
                    "current_user": current_user,
                    "current_user_is_admin": current_user_is_admin,
                    "user_personal_data": user_personal_data,
                    "entity_success": "",
                    "entity_error": "Já existe uma entidade com perfil Owner. Apenas uma é permitida.",
                    "next_entity_number": str(next_entity_number),
                    "profile_success": "",
                    "profile_error": "",
                    "profile_tab": "pessoal",
                    "initial_menu": "administrativo",
                    "admin_tab": "entidade",
                    **page_data,
                }
                return templates.TemplateResponse(
                    request,
                    "new_user.html",
                    context,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        stored_logo_url, logo_error = save_entity_logo_upload(entity_logo_file)
        if logo_error:
            context = {
                "request": request,
                "errors": [],
                "success": "",
                "form_data": get_form_defaults(),
                "entity_form_data": entity_form_data,
                "entity_edit_data": get_entity_edit_defaults(),
                "current_user": current_user,
                "current_user_is_admin": current_user_is_admin,
                "user_personal_data": user_personal_data,
                "entity_success": "",
                "entity_error": logo_error,
                "next_entity_number": str(next_entity_number),
                "profile_success": "",
                "profile_error": "",
                "profile_tab": "pessoal",
                "initial_menu": "administrativo",
                "admin_tab": "entidade",
                **page_data,
            }
            return templates.TemplateResponse(
                request,
                "new_user.html",
                context,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        entity = Entity(
            entity_number=next_entity_number,
            logo_url=stored_logo_url or None,
            is_active=True,
        )
        apply_entity_form_data_v1(entity, entity_form_data)
        session.add(entity)

        try:
            session.flush()
            created_entity_number = entity.entity_number
            session.commit()
        except IntegrityError:
            session.rollback()
            if stored_logo_url.startswith("/static/entities/"):
                local_logo_path = BASE_DIR / stored_logo_url.lstrip("/")
                local_logo_path.unlink(missing_ok=True)
            context = {
                "request": request,
                "errors": [],
                "success": "",
                "form_data": get_form_defaults(),
                "entity_form_data": entity_form_data,
                "entity_edit_data": get_entity_edit_defaults(),
                "current_user": current_user,
                "current_user_is_admin": current_user_is_admin,
                "user_personal_data": user_personal_data,
                "entity_success": "",
                "entity_error": "Não foi possível criar a entidade. Tente novamente.",
                "next_entity_number": str(get_next_entity_number(session)),
                "profile_success": "",
                "profile_error": "",
                "profile_tab": "pessoal",
                "initial_menu": "administrativo",
                "admin_tab": "entidade",
                **get_page_data(
                    session,
                    actor_user_id=current_user["id"],
                    actor_login_email=current_user["login_email"],
                    selected_entity_id=selected_entity_id,
                ),
            }
            return templates.TemplateResponse(
                request,
                "new_user.html",
                context,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    return RedirectResponse(
        url=build_return_url_v1(
            return_menu=return_menu,
            return_admin_tab=return_admin_tab,
            default_menu="administrativo",
            default_admin_tab="entidade",
            default_hash="#create-entity-card",
            entity_success=f"Entidade criada com sucesso. Nº da entidade: {created_entity_number}.",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
