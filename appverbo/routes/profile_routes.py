from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.core import *  # noqa: F403,F401
from appverbo.menu_settings import (
    delete_sidebar_menu_setting,
    get_sidebar_menu_settings,
    set_sidebar_menu_visibility,
    update_sidebar_menu_additional_fields,
    update_sidebar_menu_label,
    update_sidebar_menu_process_fields,
)
from appverbo.services import *  # noqa: F403,F401
from membrisia import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    Profile,
    User,
    UserAccountStatus,
    UserProfile,
)

router = APIRouter()


def _build_settings_redirect_url(
    success_message: str = "",
    error_message: str = "",
    redirect_menu: str = "administrativo",
    redirect_target: str = "#admin-account-status-card",
    settings_edit_key: str = "",
    settings_action: str = "",
) -> str:
    clean_menu = (redirect_menu or "").strip().lower()
    if clean_menu not in {
        "administrativo",
        "documentos",
        "funcionarios",
        "financeiro",
        "relatorios",
        "links",
        "contato",
        "tutorial",
        "home",
        "perfil",
    }:
        clean_menu = "administrativo"

    clean_target = (redirect_target or "").strip()
    if not clean_target:
        clean_target = "#admin-account-status-card"
    if not clean_target.startswith("#"):
        clean_target = f"#{clean_target}"

    query_params: dict[str, str] = {
        "menu": clean_menu,
        "settings_success": success_message,
        "settings_error": error_message,
    }
    clean_settings_edit_key = (settings_edit_key or "").strip().lower()
    if clean_settings_edit_key:
        query_params["settings_edit_key"] = clean_settings_edit_key
    clean_settings_action = (settings_action or "").strip().lower()
    if clean_settings_action in {"toggle", "edit", "delete"}:
        query_params["settings_action"] = clean_settings_action
    if clean_menu == "administrativo":
        query_params["admin_tab"] = "contas"
    return build_users_new_url(**query_params) + clean_target


@router.get("/users/new", response_class=HTMLResponse)
def new_user_page(
    request: Request,
    success: str | None = None,
    error: str | None = None,
    entity_success: str | None = None,
    entity_error: str | None = None,
    profile_success: str | None = None,
    profile_error: str | None = None,
    settings_success: str | None = None,
    settings_error: str | None = None,
    profile_tab: str = "pessoal",
    menu: str = "home",
    admin_tab: str = "utilizador",
    entity_edit_id: str = "",
    user_edit_id: str = "",
    entity_view: str = "",
    user_view: str = "",
    settings_edit_key: str = "",
    settings_action: str = "",
) -> HTMLResponse:
    resolved_profile_tab = profile_tab.strip().lower()
    if resolved_profile_tab not in {"pessoal", "morada", "treinamento"}:
        resolved_profile_tab = "pessoal"
    resolved_menu = menu.strip().lower()
    if resolved_menu not in {
        "home",
        "perfil",
        "administrativo",
        "documentos",
        "funcionarios",
        "financeiro",
        "relatorios",
        "links",
        "contato",
        "tutorial",
    }:
        resolved_menu = "home"
    resolved_admin_tab = admin_tab.strip().lower()
    if resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes"}:
        resolved_admin_tab = "utilizador"
    if resolved_admin_tab == "definicoes":
        resolved_admin_tab = "contas"
    parsed_entity_edit_id: int | None = None
    clean_entity_edit_id = entity_edit_id.strip()
    if clean_entity_edit_id.isdigit():
        parsed_entity_edit_id = int(clean_entity_edit_id)
    parsed_user_edit_id: int | None = None
    clean_user_edit_id = user_edit_id.strip()
    if clean_user_edit_id.isdigit():
        parsed_user_edit_id = int(clean_user_edit_id)
    readonly_truthy_values = {"1", "true", "sim", "yes", "on"}
    entity_readonly_mode = (
        entity_view.strip().lower() in readonly_truthy_values
        and parsed_entity_edit_id is not None
    )
    user_readonly_mode = (
        user_view.strip().lower() in readonly_truthy_values
        and parsed_user_edit_id is not None
    )
    clean_settings_edit_key = settings_edit_key.strip().lower()
    clean_settings_action = settings_action.strip().lower()
    if clean_settings_action not in {"toggle", "edit", "delete"}:
        clean_settings_action = "edit"

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
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        page_data = get_page_data(
            session,
            actor_user_id=current_user["id"],
            actor_login_email=current_user["login_email"],
            selected_entity_id=selected_entity_id,
        )
        user_personal_data = get_user_personal_data(session, current_user["id"], selected_entity_id)
        next_entity_internal_number = get_next_entity_internal_number(session)
        entity_edit_data = get_entity_edit_data(
            session,
            parsed_entity_edit_id,
            allowed_entity_ids=entity_permissions["allowed_entity_ids"],
        )
        user_edit_data = get_user_edit_data(
            session,
            parsed_user_edit_id,
            allowed_entity_ids=entity_permissions["allowed_entity_ids"],
        )

    settings_edit_data: dict[str, Any] | None = None
    if clean_settings_edit_key:
        for row in page_data.get("sidebar_menu_settings", []):
            row_key = str(row.get("key", "")).strip().lower()
            if row_key == clean_settings_edit_key:
                settings_edit_data = dict(row)
                break

    context = {
        "request": request,
        "errors": [error] if error else [],
        "success": success or "",
        "form_data": get_form_defaults(),
        "entity_form_data": get_entity_form_defaults(),
        "entity_edit_data": entity_edit_data,
        "user_edit_data": user_edit_data,
        "entity_readonly_mode": bool(entity_readonly_mode),
        "user_readonly_mode": bool(user_readonly_mode),
        "current_user": current_user,
        "current_user_is_admin": current_user_is_admin,
        "user_personal_data": user_personal_data,
        "entity_success": entity_success or "",
        "entity_error": entity_error or "",
        "next_entity_internal_number": str(next_entity_internal_number),
        "profile_success": profile_success or "",
        "profile_error": profile_error or "",
        "settings_success": settings_success or "",
        "settings_error": settings_error or "",
        "settings_edit_data": settings_edit_data,
        "settings_edit_key": clean_settings_edit_key,
        "settings_action": clean_settings_action,
        "profile_tab": resolved_profile_tab,
        "initial_menu": resolved_menu,
        "admin_tab": resolved_admin_tab,
        "current_user_can_manage_all_entities": bool(
            entity_permissions["can_manage_all_entities"]
        ),
        **page_data,
    }
    return templates.TemplateResponse(request, "new_user.html", context)


@router.post("/settings/menu/toggle", response_class=HTMLResponse)
def toggle_sidebar_menu(
    request: Request,
    menu_key: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-account-status-card"),
) -> RedirectResponse:
    clean_menu_key = menu_key.strip().lower()
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        selected_entity_id = get_session_entity_id(request)
        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar definições do menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="toggle",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        settings = get_sidebar_menu_settings(session)
        selected_setting = next((item for item in settings if item["key"] == clean_menu_key), None)
        if selected_setting is None:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Menu inválido.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="toggle",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        make_visible = not (bool(selected_setting["is_active"]) and not bool(selected_setting["is_deleted"]))
        ok, error_message = set_sidebar_menu_visibility(session, clean_menu_key, make_visible)
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar visibilidade do menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="toggle",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Visibilidade do menu atualizada com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="toggle",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/edit", response_class=HTMLResponse)
def edit_sidebar_menu_label(
    request: Request,
    menu_key: str = Form(...),
    menu_label: str = Form(...),
    menu_status: str = Form(""),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-account-status-card"),
) -> RedirectResponse:
    clean_menu_key = menu_key.strip().lower()
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        selected_entity_id = get_session_entity_id(request)
        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar definições do menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode editar os dados gerais do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        ok, error_message = update_sidebar_menu_label(session, clean_menu_key, menu_label)
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível editar o menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        clean_status = menu_status.strip().lower()
        if clean_status in {"ativo", "active", "1", "true", "sim", "yes", "on"}:
            desired_visibility = True
        elif clean_status in {"inativo", "inactive", "0", "false", "nao", "não", "no", "off"}:
            desired_visibility = False
        elif clean_status:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Estado inválido. Use Ativo ou Inativo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        else:
            desired_visibility = None

        if desired_visibility is not None:
            settings = get_sidebar_menu_settings(session)
            selected_setting = next((item for item in settings if item["key"] == clean_menu_key), None)
            if selected_setting is not None:
                current_visibility = bool(selected_setting["is_active"]) and not bool(selected_setting["is_deleted"])
                if current_visibility != desired_visibility:
                    status_ok, status_error = set_sidebar_menu_visibility(
                        session,
                        clean_menu_key,
                        desired_visibility,
                    )
                    if not status_ok:
                        return RedirectResponse(
                            url=_build_settings_redirect_url(
                                error_message=status_error or "Não foi possível atualizar o estado do menu.",
                                redirect_menu=redirect_menu,
                                redirect_target=redirect_target,
                                settings_edit_key=clean_menu_key,
                                settings_action="edit",
                            ),
                            status_code=status.HTTP_303_SEE_OTHER,
                        )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Dados gerais do processo atualizados com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/process-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_fields(
    request: Request,
    menu_key: str = Form(...),
    visible_fields: list[str] = Form(default=[]),
    visible_headers: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = menu_key.strip().lower()
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar definições do menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode configurar campos disponíveis por processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        ok, error_message = update_sidebar_menu_process_fields(
            session,
            clean_menu_key,
            visible_fields,
            visible_headers,
        )
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar os campos do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Campos visíveis do processo atualizados com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/process-additional-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_additional_fields(
    request: Request,
    menu_key: str = Form(...),
    additional_field_key: list[str] = Form(default=[]),
    additional_field_label: list[str] = Form(default=[]),
    additional_field_type: list[str] = Form(default=[]),
    additional_field_size: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = menu_key.strip().lower()
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar definições do menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode configurar campos adicionais por processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        rows_count = max(
            len(additional_field_label),
            len(additional_field_type),
            len(additional_field_size),
            len(additional_field_key),
        )
        payload_fields: list[dict[str, str]] = []
        for row_index in range(rows_count):
            payload_fields.append(
                {
                    "key": additional_field_key[row_index] if row_index < len(additional_field_key) else "",
                    "label": additional_field_label[row_index] if row_index < len(additional_field_label) else "",
                    "field_type": additional_field_type[row_index] if row_index < len(additional_field_type) else "",
                    "size": additional_field_size[row_index] if row_index < len(additional_field_size) else "",
                }
            )

        ok, error_message = update_sidebar_menu_additional_fields(
            session,
            clean_menu_key,
            payload_fields,
        )
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar os campos adicionais do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Campos adicionais do processo atualizados com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/delete", response_class=HTMLResponse)
def delete_sidebar_menu(
    request: Request,
    menu_key: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-account-status-card"),
) -> RedirectResponse:
    clean_menu_key = menu_key.strip().lower()
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        selected_entity_id = get_session_entity_id(request)
        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar definições do menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="delete",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Excluir menu está disponível apenas para Owner.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="delete",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        ok, error_message = delete_sidebar_menu_setting(session, clean_menu_key)
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível excluir o menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="delete",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Menu excluído com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/users/profile/personal")
async def update_personal_profile(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
    clean_full_name = str(submitted_form.get("full_name") or "").strip()
    clean_primary_phone = str(submitted_form.get("primary_phone") or "").strip()
    clean_birth_date = str(submitted_form.get("birth_date") or "").strip()
    whatsapp_notice_opt_in = str(submitted_form.get("whatsapp_notice_opt_in") or "").strip()

    try:
        parsed_birth_date = parse_optional_date_pt(clean_birth_date)
    except ValueError:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Data de nascimento inválida. Use o formato dd/mm/aaaa.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    parsed_whatsapp_notice_opt_in = whatsapp_notice_opt_in == "1"

    if not clean_full_name:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Nome completo é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    if not clean_primary_phone:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Telefone principal é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member).join(User, User.member_id == Member.id).where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        sidebar_menu_settings = get_sidebar_menu_settings(session)
        documentos_setting = next(
            (
                row
                for row in sidebar_menu_settings
                if str(row.get("key") or "").strip().lower() == "documentos"
            ),
            None,
        )
        option_keys = {
            str(item.get("key") or "").strip().lower()
            for item in (documentos_setting or {}).get("process_field_options", [])
            if str(item.get("key") or "").strip()
        }
        custom_field_meta: dict[str, dict[str, Any]] = {}
        for raw_item in (documentos_setting or {}).get("process_additional_fields", []):
            clean_key = str(raw_item.get("key") or "").strip().lower()
            if not clean_key.startswith("custom_"):
                continue
            if clean_key not in option_keys:
                continue
            field_type = str(raw_item.get("field_type") or "text").strip().lower()
            if field_type not in {"text", "number", "email", "phone", "date", "flag", "header"}:
                field_type = "text"
            size_value: int | None = None
            if field_type in {"text", "number", "email", "phone"}:
                try:
                    parsed_size = int(str(raw_item.get("size") or "").strip())
                except (TypeError, ValueError):
                    parsed_size = 30
                size_value = max(1, min(parsed_size, 255))
            custom_field_meta[clean_key] = {
                "field_type": field_type,
                "size": size_value,
            }
        visible_custom_keys = [
            clean_key
            for clean_key in (
                str(raw_key or "").strip().lower()
                for raw_key in (documentos_setting or {}).get("process_visible_fields", [])
            )
            if clean_key.startswith("custom_")
            and clean_key in option_keys
            and str((custom_field_meta.get(clean_key) or {}).get("field_type") or "") != "header"
        ]
        visible_custom_keys_set = set(visible_custom_keys)

        existing_custom_fields = parse_profile_custom_fields(member.profile_custom_fields)
        updated_custom_fields = {
            key: value
            for key, value in existing_custom_fields.items()
            if key not in visible_custom_keys_set
        }
        for custom_key in visible_custom_keys:
            field_name = f"custom_field__{custom_key}"
            field_meta = custom_field_meta.get(custom_key) or {}
            field_type = str(field_meta.get("field_type") or "text").strip().lower()
            field_size = field_meta.get("size")
            if field_type == "flag":
                updated_custom_fields[custom_key] = "1" if str(submitted_form.get(field_name) or "").strip() == "1" else "0"
                continue

            clean_custom_value = str(submitted_form.get(field_name) or "").strip()
            if isinstance(field_size, int) and field_size > 0:
                clean_custom_value = clean_custom_value[:field_size]
            if clean_custom_value:
                updated_custom_fields[custom_key] = clean_custom_value

        previous_phone = (member.primary_phone or "").strip()
        member.full_name = clean_full_name
        member.primary_phone = clean_primary_phone
        member.birth_date = parsed_birth_date
        member.whatsapp_notice_opt_in = parsed_whatsapp_notice_opt_in
        member.profile_custom_fields = serialize_profile_custom_fields(updated_custom_fields)
        if previous_phone != clean_primary_phone:
            member.whatsapp_verification_status = "unknown"
            member.whatsapp_last_check_at = None
            member.whatsapp_last_error = None
            member.whatsapp_last_wa_id = None
            member.whatsapp_last_message_id = None

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Falha ao gravar dados pessoais.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    request.session["user_name"] = clean_full_name
    return RedirectResponse(
        url=build_users_new_url(
            profile_success="Dados pessoais atualizados com sucesso.",
            profile_tab="pessoal",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/profile/address")
def update_address_profile(
    request: Request,
    address: str = Form(""),
    city: str = Form(""),
    freguesia: str = Form(""),
    postal_code: str = Form(""),
) -> RedirectResponse:
    clean_address = address.strip()
    clean_city = city.strip()
    clean_freguesia = freguesia.strip()
    clean_postal_code = postal_code.strip()

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member).join(User, User.member_id == Member.id).where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="morada",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        member.address = clean_address or None
        member.city = clean_city or None
        member.freguesia = clean_freguesia or None
        member.postal_code = clean_postal_code or None

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Falha ao gravar dados de morada.",
                    profile_tab="morada",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_users_new_url(
            profile_success="Dados de morada atualizados com sucesso.",
            profile_tab="morada",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/profile/training")
def update_training_profile(
    request: Request,
    training_discipulado_verbo_vida: str | None = Form(default=None),
    training_ebvv: str | None = Form(default=None),
    training_rhema: str | None = Form(default=None),
    training_escola_ministerial: str | None = Form(default=None),
    training_escola_missoes: str | None = Form(default=None),
    training_outros_enabled: str | None = Form(default=None),
    training_outros: str = Form(""),
) -> RedirectResponse:
    clean_training_outros = training_outros.strip()
    is_outros_enabled = training_outros_enabled == "1"

    if is_outros_enabled and not clean_training_outros:
        return RedirectResponse(
            url=build_users_new_url(
                profile_error="Preencha o campo Outros para gravar o treinamento.",
                profile_tab="treinamento",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member).join(User, User.member_id == Member.id).where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="treinamento",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        member.training_discipulado_verbo_vida = training_discipulado_verbo_vida == "1"
        member.training_ebvv = training_ebvv == "1"
        member.training_rhema = training_rhema == "1"
        member.training_escola_ministerial = training_escola_ministerial == "1"
        member.training_escola_missoes = training_escola_missoes == "1"
        member.training_outros = clean_training_outros if is_outros_enabled else None

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Falha ao gravar dados de treinamento.",
                    profile_tab="treinamento",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_users_new_url(
            profile_success="Dados de treinamento atualizados com sucesso.",
            profile_tab="treinamento",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/profile/whatsapp/verify")
def verify_whatsapp_profile(request: Request) -> RedirectResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member).join(User, User.member_id == Member.id).where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        normalized_phone = normalize_whatsapp_recipient(member.primary_phone or "")
        if not normalized_phone:
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error=(
                        "Telefone inválido para WhatsApp. Use formato internacional "
                        "(ex.: +351912345678)."
                    ),
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        is_sent, message_id, error_message = send_whatsapp_verification_template(normalized_phone)
        member.whatsapp_last_check_at = datetime.now(timezone.utc)
        member.whatsapp_last_message_id = message_id or None
        member.whatsapp_last_error = error_message or None
        member.whatsapp_verification_status = "pending" if is_sent else "failed"

        if not is_sent:
            session.commit()
            return RedirectResponse(
                url=build_users_new_url(
                    profile_error=f"Não foi possível iniciar verificação WhatsApp: {error_message}",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        session.commit()
        return RedirectResponse(
            url=build_users_new_url(
                profile_success=(
                    "Verificação WhatsApp iniciada. O estado será atualizado automaticamente "
                    "quando o webhook receber a confirmação."
                ),
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
