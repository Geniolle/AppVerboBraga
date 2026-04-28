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
from appverbo.models import (
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

from appverbo.routes.profile.router import router


def _resolve_first_dynamic_section_key(menu_row: dict[str, Any] | None) -> str:
    if not isinstance(menu_row, dict):
        return "__empty__"
    raw_rows = menu_row.get("process_visible_field_rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        return "__empty__"

    section_order: list[str] = []
    seen_sections: set[str] = set()
    first_field_key = ""
    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            continue
        field_key = str(raw_row.get("field_key") or "").strip().lower()
        if not field_key:
            continue
        if not first_field_key:
            first_field_key = field_key
        header_key = str(raw_row.get("header_key") or "").strip().lower()
        section_key = header_key or "__geral__"
        if section_key in seen_sections:
            continue
        seen_sections.add(section_key)
        section_order.append(section_key)

    if not section_order:
        return "__empty__"
    if len(section_order) == 1 and section_order[0] == "__geral__":
        return f"field:{first_field_key}" if first_field_key else "__empty__"
    return section_order[0]


def _resolve_initial_menu_target(
    resolved_menu: str,
    resolved_profile_tab: str,
    resolved_admin_tab: str,
    settings_edit_key: str,
    can_manage_all_entities: bool,
    sidebar_menu_settings: list[dict[str, Any]],
) -> tuple[str, str]:
    clean_menu_key = str(resolved_menu or "").strip().lower()
    settings_by_key = {
        str(raw_row.get("key") or "").strip().lower(): raw_row
        for raw_row in sidebar_menu_settings
        if isinstance(raw_row, dict) and str(raw_row.get("key") or "").strip()
    }

    if clean_menu_key == "home":
        return "#home-summary-card", ""
    if clean_menu_key == "perfil":
        if resolved_profile_tab == "morada":
            return "#perfil-morada-card", ""
        if resolved_profile_tab == "treinamento":
            return "#dados-treinamento-card", ""
        return "#perfil-pessoal-card", ""
    if clean_menu_key == "administrativo":
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        if resolved_admin_tab == "contas":
            return "#admin-account-status-card", ""
        if resolved_admin_tab == "utilizador":
            return "#create-user-card", ""
        return "#create-entity-card", ""
    if clean_menu_key == "configuracao":
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        return "#admin-account-status-card", ""
    if clean_menu_key == "documentos":
        return "#perfil-pessoal-card", ""

    matched_menu_row = settings_by_key.get(clean_menu_key)
    if matched_menu_row is not None:
        return "#dynamic-process-card", _resolve_first_dynamic_section_key(matched_menu_row)
    return "", ""


@router.get("/users/new", response_class=HTMLResponse)
def new_user_page(
    request: Request,
    success: str | None = None,
    error: str | None = None,
    invite_link: str | None = None,
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
    settings_tab: str = "",
) -> HTMLResponse:
    resolved_profile_tab = profile_tab.strip().lower()
    if resolved_profile_tab not in {"pessoal", "morada", "treinamento"}:
        resolved_profile_tab = "pessoal"
    resolved_menu = menu.strip().lower()
    if not resolved_menu:
        resolved_menu = "home"
    if resolved_menu == "configuracao":
        resolved_menu = "administrativo"
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
    if clean_settings_action not in {"toggle", "edit", "delete", "create"}:
        clean_settings_action = "edit"
    clean_settings_tab = settings_tab.strip().lower()
    if clean_settings_tab not in {"geral", "campos-config", "campos-adicionais", "sessoes-sidebar"}:
        clean_settings_tab = ""

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
        visible_menu_keys = {
            str(raw_key or "").strip().lower()
            for raw_key in page_data.get("visible_sidebar_menu_keys", [])
            if str(raw_key or "").strip()
        }
        if resolved_menu != "perfil" and resolved_menu not in visible_menu_keys:
            resolved_menu = "home"
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

    initial_menu_target, initial_dynamic_process_section = _resolve_initial_menu_target(
        resolved_menu=resolved_menu,
        resolved_profile_tab=resolved_profile_tab,
        resolved_admin_tab=resolved_admin_tab,
        settings_edit_key=clean_settings_edit_key,
        can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
        sidebar_menu_settings=list(page_data.get("sidebar_menu_settings", [])),
    )

    context = {
        "request": request,
        "errors": [error] if error else [],
        "success": success or "",
        "generated_invite_link": (invite_link or "").strip(),
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
        "settings_tab": clean_settings_tab,
        "profile_tab": resolved_profile_tab,
        "initial_menu": resolved_menu,
        "initial_menu_target": initial_menu_target,
        "initial_dynamic_process_section": initial_dynamic_process_section,
        "admin_tab": resolved_admin_tab,
        "current_user_can_manage_all_entities": bool(
            entity_permissions["can_manage_all_entities"]
        ),
        **page_data,
    }
    return templates.TemplateResponse(request, "new_user.html", context)
