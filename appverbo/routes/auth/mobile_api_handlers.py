from __future__ import annotations

from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from appverbo.core import SessionLocal
from appverbo.models import Member, MemberEntity, MemberEntityStatus, User, UserAccountStatus
from appverbo.routes.auth.router import router
from appverbo.schemas.auth import LoginFormSchema
from appverbo.services.auth import is_admin_user, verify_password
from appverbo.services.page import get_home_dashboard_data, get_page_data
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.profile import get_user_personal_data
from appverbo.services.session import (
    get_current_user,
    get_entity_context_for_user,
    get_session_entity_id,
    set_session_entity_context,
)


# ###################################################################################
# (1) HELPERS DE RESPOSTA E CONTEXTO DE SESSAO
# ###################################################################################
def _json_error(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        {
            "ok": False,
            "error": message,
        },
        status_code=status_code,
    )


def _build_auth_payload(request: Request, user_data: dict[str, Any]) -> dict[str, Any]:
    raw_entity_id = request.session.get("entity_id")
    entity_id = int(raw_entity_id) if isinstance(raw_entity_id, int) else None

    if entity_id is None and isinstance(raw_entity_id, str) and raw_entity_id.isdigit():
        entity_id = int(raw_entity_id)

    return {
        "ok": True,
        "user": {
            "id": int(user_data["id"]),
            "full_name": str(user_data["full_name"] or ""),
            "email": str(user_data["login_email"] or ""),
        },
        "entity": {
            "id": entity_id,
            "name": str(request.session.get("entity_name") or ""),
            "logo_url": str(request.session.get("entity_logo_url") or ""),
        },
    }


def _build_mobile_menu_items(page_data: dict[str, Any]) -> list[dict[str, Any]]:
    raw_visible_keys = page_data.get("visible_sidebar_menu_keys") or []
    visible_keys = {
        str(raw_key or "").strip().lower()
        for raw_key in raw_visible_keys
        if str(raw_key or "").strip()
    }
    raw_menu_rows = page_data.get("sidebar_menu_settings") or []

    menu_items: list[dict[str, Any]] = []
    for raw_menu_row in raw_menu_rows:
        menu_row = dict(raw_menu_row or {})
        clean_menu_key = str(menu_row.get("key") or "").strip().lower()
        if not clean_menu_key or clean_menu_key not in visible_keys:
            continue

        menu_items.append(
            {
                "key": clean_menu_key,
                "label": str(menu_row.get("label") or clean_menu_key).strip() or clean_menu_key,
                "section_key": str(menu_row.get("sidebar_section_key") or "").strip().lower(),
                "section_label": str(menu_row.get("sidebar_section_label") or "").strip(),
                "requires_admin": bool(menu_row.get("requires_admin")),
                "is_active": bool(menu_row.get("is_active")),
                "web_path": f"/users/new?menu={clean_menu_key}",
            }
        )

    return menu_items


def _build_mobile_profile_summary(user_personal_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "full_name": str(user_personal_data.get("full_name") or ""),
        "login_email": str(user_personal_data.get("login_email") or ""),
        "primary_phone": str(user_personal_data.get("primary_phone") or ""),
        "country": str(user_personal_data.get("country") or ""),
        "birth_date": str(user_personal_data.get("birth_date") or ""),
        "entities": str(user_personal_data.get("entities") or ""),
        "primary_entity_name": str(user_personal_data.get("primary_entity_name") or ""),
        "primary_entity_logo_url": str(user_personal_data.get("primary_entity_logo_url") or ""),
        "member_status": str(user_personal_data.get("member_status") or ""),
        "account_status": str(user_personal_data.get("account_status") or ""),
        "is_collaborator": str(user_personal_data.get("is_collaborator") or ""),
    }


# ###################################################################################
# (2) ENDPOINTS MOBILE DE AUTENTICACAO (JSON)
# ###################################################################################
@router.post("/api/auth/login", response_class=JSONResponse)
def mobile_login_v1(request: Request, payload: LoginFormSchema) -> JSONResponse:
    clean_email = payload.email.strip().lower()
    clean_password = payload.password
    requested_mode = "admin" if payload.login_mode.strip().lower() == "admin" else "login"
    clean_entity_id = payload.entity_id.strip() if requested_mode == "admin" else ""

    if not clean_email or not clean_password:
        return _json_error(
            "Informe email e palavra-passe.",
            status.HTTP_400_BAD_REQUEST,
        )

    parsed_entity_id: int | None = None
    if requested_mode == "admin":
        if not clean_entity_id:
            return _json_error(
                "Selecione a entidade para entrar como administrador.",
                status.HTTP_400_BAD_REQUEST,
            )
        try:
            parsed_entity_id = int(clean_entity_id)
        except ValueError:
            return _json_error(
                "Entidade selecionada invalida.",
                status.HTTP_400_BAD_REQUEST,
            )

    selected_entity_context: dict[str, Any] | None = None
    row: Any = None

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is not None:
            return JSONResponse(_build_auth_payload(request, current_user))

        row = session.execute(
            select(
                User.id,
                User.login_email,
                User.password_hash,
                User.account_status,
                User.member_id,
                Member.full_name,
            )
            .join(Member, Member.id == User.member_id)
            .where(func.lower(User.login_email) == clean_email)
        ).one_or_none()

        if row is None or not verify_password(clean_password, row.password_hash):
            return _json_error(
                "Credenciais invalidas.",
                status.HTTP_401_UNAUTHORIZED,
            )

        if row.account_status != UserAccountStatus.ACTIVE.value:
            return _json_error(
                f"Conta com estado '{row.account_status}'. Contacte o administrador.",
                status.HTTP_403_FORBIDDEN,
            )

        current_user_is_admin = is_admin_user(session, row.id, row.login_email)
        if requested_mode == "admin" and not current_user_is_admin:
            return _json_error(
                "Acesso administrativo disponivel apenas para utilizadores administradores.",
                status.HTTP_403_FORBIDDEN,
            )

        if requested_mode == "admin":
            linked_entity_ids_rows = session.scalars(
                select(MemberEntity.entity_id)
                .where(
                    MemberEntity.member_id == int(row.member_id),
                    MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                )
                .order_by(MemberEntity.id.asc())
            ).all()

            linked_entity_ids = [
                int(linked_entity_id)
                for linked_entity_id in linked_entity_ids_rows
                if isinstance(linked_entity_id, int)
            ]

            if not linked_entity_ids:
                return _json_error(
                    "Utilizador sem entidade ativa associada.",
                    status.HTTP_403_FORBIDDEN,
                )

            if parsed_entity_id not in linked_entity_ids:
                return _json_error(
                    "Nao e permitido entrar com uma entidade diferente da associada ao seu utilizador.",
                    status.HTTP_403_FORBIDDEN,
                )

            selected_entity_context = get_entity_context_for_user(
                session,
                row.id,
                row.login_email,
                parsed_entity_id,
            )
        else:
            selected_entity_context = get_entity_context_for_user(
                session,
                row.id,
                row.login_email,
                None,
            )

        if selected_entity_context is None:
            return _json_error(
                "Utilizador sem entidade ativa associada.",
                status.HTTP_403_FORBIDDEN,
            )

    request.session["user_id"] = int(row.id)
    request.session["user_name"] = str(row.full_name or "")
    request.session["user_email"] = str(row.login_email or "")
    set_session_entity_context(request, selected_entity_context)

    return JSONResponse(
        _build_auth_payload(
            request,
            {
                "id": int(row.id),
                "full_name": str(row.full_name or ""),
                "login_email": str(row.login_email or ""),
            },
        )
    )


@router.get("/api/auth/me", response_class=JSONResponse)
def mobile_me_v1(request: Request) -> JSONResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return _json_error("Sessao expirada ou inexistente.", status.HTTP_401_UNAUTHORIZED)

        entity_context = get_entity_context_for_user(
            session,
            int(current_user["id"]),
            str(current_user["login_email"]),
            get_session_entity_id(request),
        )
        set_session_entity_context(request, entity_context)
        return JSONResponse(_build_auth_payload(request, current_user))


@router.post("/api/auth/logout", response_class=JSONResponse)
def mobile_logout_v1(request: Request) -> JSONResponse:
    request.session.clear()
    return JSONResponse({"ok": True})


# ###################################################################################
# (3) ENDPOINT HOME PARA O APP MOBILE
# ###################################################################################
@router.get("/api/mobile/home", response_class=JSONResponse)
def mobile_home_v1(request: Request) -> JSONResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return _json_error("Sessao expirada ou inexistente.", status.HTTP_401_UNAUTHORIZED)

        selected_entity_id = get_session_entity_id(request)
        page_data = get_page_data(
            session,
            actor_user_id=int(current_user["id"]),
            actor_login_email=str(current_user["login_email"]),
            selected_entity_id=selected_entity_id,
        )
        user_personal_data = get_user_personal_data(
            session,
            user_id=int(current_user["id"]),
            selected_entity_id=selected_entity_id,
        )
        entity_permissions = get_user_entity_permissions(
            session,
            user_id=int(current_user["id"]),
            login_email=str(current_user["login_email"]),
            selected_entity_id=selected_entity_id,
        )

        entity_context = get_entity_context_for_user(
            session,
            int(current_user["id"]),
            str(current_user["login_email"]),
            entity_permissions.get("selected_entity_id"),
        )
        set_session_entity_context(request, entity_context)

        allowed_entity_ids = {
            int(raw_id)
            for raw_id in (entity_permissions.get("allowed_entity_ids") or set())
            if isinstance(raw_id, int) or str(raw_id).isdigit()
        }

        return JSONResponse(
            {
                "ok": True,
                "session": _build_auth_payload(request, current_user),
                "permissions": {
                    "is_admin": bool(entity_permissions.get("is_admin")),
                    "has_owner_membership": bool(entity_permissions.get("has_owner_membership")),
                    "can_manage_all_entities": bool(entity_permissions.get("can_manage_all_entities")),
                    "selected_entity_id": entity_permissions.get("selected_entity_id"),
                    "allowed_entity_ids": sorted(allowed_entity_ids),
                },
                "home": {
                    "dashboard_data": get_home_dashboard_data(
                        session,
                        allowed_entity_ids=allowed_entity_ids,
                    ),
                    "menu_items": _build_mobile_menu_items(page_data),
                    "profile_summary": _build_mobile_profile_summary(user_personal_data),
                },
            }
        )
