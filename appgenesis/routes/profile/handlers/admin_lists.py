from __future__ import annotations

from typing import Any
from fastapi import (
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from appgenesis.admin_subprocesses.registry import get_admin_subprocess_config
from appgenesis.db.session import SessionLocal
from appgenesis.services.auth_profile_entity_scope import (
    build_auth_profile_entity_context_v1,
    get_entity_profile_scope_v1,
    resolve_visibility_scope_for_entity_v1,
)
from appgenesis.services.page import get_page_data
from appgenesis.services.permissions import get_user_entity_permissions
from appgenesis.services.session import (
    get_current_user,
    get_session_entity_id,
)
from appgenesis.routes.profile.router import router
from appgenesis.routes.profile.handlers.profile_common import (
    _sanitize_users_new_return_url_post_save_v6,
)


# ---------------------------------------------------------------------------
# Funções administrativas (Administrativo > Funções administrativas)
# ---------------------------------------------------------------------------

_FUNCTIONS_FALLBACK_URL = "/users/new?menu=administrativo&admin_tab=funcoes_administrativas&target=funcoes-administrativas-card#funcoes-administrativas-card"
_FUNCTIONS_ERROR_MESSAGES = {
    "label_required": "Nome da função é obrigatório.",
    "not_found": "Função não encontrada.",
    "active_function": "Só é possível eliminar funções inativas.",
    "system_profile_required": "Escolha o perfil no sistema da função.",
    "profile_required": "Escolha pelo menos um perfil de autorização.",
    "profile_duplicate": "Cada perfil de autorização só pode ser escolhido uma vez.",
    "profile_not_found": "Perfil de autorização inválido ou inativo.",
    "menu_not_found": "Menu Administrativo não configurado para esta entidade.",
    "profile_all_exclusive": "\"Todos os perfis\" não pode ser combinado com outros perfis.",
}


def _functions_redirect(return_url: str, extra: dict[str, Any]) -> RedirectResponse:
    safe_url = _sanitize_users_new_return_url_post_save_v6(return_url, extra)
    return RedirectResponse(url=safe_url or _FUNCTIONS_FALLBACK_URL, status_code=status.HTTP_303_SEE_OTHER)


def _functions_actor_allowed(request: Request, session: Session) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    current_user = get_current_user(request, session)
    if current_user is None:
        return None, {}
    selected_entity_id = get_session_entity_id(request)
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
    visible_keys = {
        str(raw_key or "").strip().lower()
        for raw_key in page_data.get("visible_sidebar_menu_keys", [])
    }
    if "administrativo" not in visible_keys:
        return None, {}
    entity_context = build_auth_profile_entity_context_v1(
        session,
        selected_entity_id=entity_permissions.get("selected_entity_id"),
        permissions=entity_permissions,
    )
    return current_user, entity_context


@router.post("/users/functions/save")
async def save_authorization_function(request: Request) -> RedirectResponse:
    from appgenesis.admin_subprocesses.repositories.functions_repository import (
        FunctionsAdminRepository,
        list_active_profile_options,
    )

    submitted_form = await request.form()
    mode = str(submitted_form.get("functions_mode") or "create").strip().lower()
    edit_key = str(submitted_form.get("original_functions_key") or "").strip().lower() if mode == "edit" else ""
    return_url = str(submitted_form.get("functions_return_url") or "").strip()

    with SessionLocal() as session:
        current_user, entity_context = _functions_actor_allowed(request, session)
        if current_user is None:
            return RedirectResponse(url="/login?error=Efetue login para continuar.", status_code=status.HTTP_302_FOUND)
        config = get_admin_subprocess_config("funcoes_administrativas")
        repo = FunctionsAdminRepository(config)
        entity_number = entity_context.get("selected_entity_number", "")
        allowed_profile_keys = [
            key
            for key, _label in list_active_profile_options(
                session,
                get_admin_subprocess_config("perfil_de_autorizacao"),
                user_id=current_user["id"],
                entity_number=entity_number,
            )
        ]
        ok, reason, _saved_key = repo.save_row(
            session,
            {
                "label": str(submitted_form.get("functions_label") or "").strip(),
                "system_profile": str(submitted_form.get("functions_system_profile") or "").strip().lower(),
                "visibility_scope_mode": resolve_visibility_scope_for_entity_v1(
                    submitted_form.get("functions_visibility_scope_mode"),
                    get_entity_profile_scope_v1(session, get_session_entity_id(request)),
                ),
                "status": str(submitted_form.get("functions_status") or "").strip(),
                "authorization_profiles": submitted_form.getlist("functions_authorization_profiles"),
            },
            context={
                "entity_id": get_session_entity_id(request),
                "entity_number": entity_number,
                "allowed_profile_keys": allowed_profile_keys,
            },
            edit_key=edit_key,
        )
        if not ok:
            return _functions_redirect(
                return_url,
                {"profile_error": _FUNCTIONS_ERROR_MESSAGES.get(reason, "Não foi possível guardar a função.")},
            )
        session.commit()

    success = "Função atualizada com sucesso." if edit_key else "Função criada com sucesso."
    return _functions_redirect(return_url, {"profile_success": success})


@router.post("/users/functions/delete")
async def delete_authorization_function(request: Request) -> RedirectResponse:
    from appgenesis.admin_subprocesses.repositories.functions_repository import FunctionsAdminRepository

    submitted_form = await request.form()
    key = str(submitted_form.get("functions_key") or "").strip().lower()
    return_url = str(submitted_form.get("functions_return_url") or "").strip()

    with SessionLocal() as session:
        current_user, _entity_context = _functions_actor_allowed(request, session)
        if current_user is None:
            return RedirectResponse(url="/login?error=Efetue login para continuar.", status_code=status.HTTP_302_FOUND)
        repo = FunctionsAdminRepository(get_admin_subprocess_config("funcoes_administrativas"))
        ok, reason = repo.delete_row(session, key, context={"entity_id": get_session_entity_id(request)})
        if not ok:
            return _functions_redirect(
                return_url,
                {"profile_error": _FUNCTIONS_ERROR_MESSAGES.get(reason, "Não foi possível eliminar a função.")},
            )
        session.commit()

    return _functions_redirect(return_url, {"profile_success": "Função eliminada com sucesso."})


# ---------------------------------------------------------------------------
# Departamentos (Sistema > Definições > Departamentos)
# ---------------------------------------------------------------------------

_DEPARTMENTS_FALLBACK_URL = "/users/new?menu=sessoes&admin_tab=departamentos&target=departamentos-card#departamentos-card"
_DEPARTMENTS_ERROR_MESSAGES = {
    "label_required": "Nome do departamento é obrigatório.",
    "not_found": "Departamento não encontrado.",
    "duplicate_name": "Já existe um departamento com este nome.",
    "active_department": "Só é possível eliminar departamentos inativos.",
    "in_use": "Departamento em uso por membros; não pode ser eliminado.",
    "menu_not_found": "Entidade ativa não identificada.",
}


def _departments_redirect(return_url: str, extra: dict[str, Any]) -> RedirectResponse:
    safe_url = _sanitize_users_new_return_url_post_save_v6(return_url, extra)
    return RedirectResponse(url=safe_url or _DEPARTMENTS_FALLBACK_URL, status_code=status.HTTP_303_SEE_OTHER)


def _departments_actor_allowed(request: Request, session: Session) -> dict[str, Any] | None:
    current_user = get_current_user(request, session)
    if current_user is None:
        return None
    selected_entity_id = get_session_entity_id(request)
    page_data = get_page_data(
        session,
        actor_user_id=current_user["id"],
        actor_login_email=current_user["login_email"],
        selected_entity_id=selected_entity_id,
    )
    visible_keys = {
        str(raw_key or "").strip().lower()
        for raw_key in page_data.get("visible_sidebar_menu_keys", [])
    }
    if "sessoes" not in visible_keys:
        return None
    return current_user


@router.post("/users/departments/save")
async def save_department(request: Request) -> RedirectResponse:
    from appgenesis.admin_subprocesses.repositories.departments_repository import DepartmentsAdminRepository

    submitted_form = await request.form()
    mode = str(submitted_form.get("departments_mode") or "create").strip().lower()
    edit_key = str(submitted_form.get("original_departments_key") or "").strip() if mode == "edit" else ""
    return_url = str(submitted_form.get("departments_return_url") or "").strip()

    with SessionLocal() as session:
        current_user = _departments_actor_allowed(request, session)
        if current_user is None:
            return RedirectResponse(url="/login?error=Efetue login para continuar.", status_code=status.HTTP_302_FOUND)
        repo = DepartmentsAdminRepository(get_admin_subprocess_config("departamentos"))
        ok, reason, _saved_key = repo.save_row(
            session,
            {
                "label": str(submitted_form.get("departments_label") or "").strip(),
                "description": str(submitted_form.get("departments_description") or "").strip(),
                "status": str(submitted_form.get("departments_status") or "").strip(),
            },
            context={"entity_id": get_session_entity_id(request)},
            edit_key=edit_key,
        )
        if not ok:
            return _departments_redirect(
                return_url,
                {"profile_error": _DEPARTMENTS_ERROR_MESSAGES.get(reason, "Não foi possível guardar o departamento.")},
            )
        session.commit()

    success = "Departamento atualizado com sucesso." if edit_key else "Departamento criado com sucesso."
    return _departments_redirect(return_url, {"profile_success": success})


@router.post("/users/departments/delete")
async def delete_department(request: Request) -> RedirectResponse:
    from appgenesis.admin_subprocesses.repositories.departments_repository import DepartmentsAdminRepository

    submitted_form = await request.form()
    key = str(submitted_form.get("departments_key") or "").strip()
    return_url = str(submitted_form.get("departments_return_url") or "").strip()

    with SessionLocal() as session:
        current_user = _departments_actor_allowed(request, session)
        if current_user is None:
            return RedirectResponse(url="/login?error=Efetue login para continuar.", status_code=status.HTTP_302_FOUND)
        repo = DepartmentsAdminRepository(get_admin_subprocess_config("departamentos"))
        ok, reason = repo.delete_row(session, key, context={"entity_id": get_session_entity_id(request)})
        if not ok:
            return _departments_redirect(
                return_url,
                {"profile_error": _DEPARTMENTS_ERROR_MESSAGES.get(reason, "Não foi possível eliminar o departamento.")},
            )
        session.commit()

    return _departments_redirect(return_url, {"profile_success": "Departamento eliminado com sucesso."})
