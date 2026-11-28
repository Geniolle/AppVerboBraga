from __future__ import annotations

from typing import Any
from urllib.parse import (
    parse_qsl,
    urlsplit,
)
from fastapi import (
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from appgenesis.admin_subprocesses.registry import get_admin_subprocess_config
from appgenesis.admin_subprocesses.repositories.auth_profile_repository import (
    AUTH_PROFILE_MENU_KEY,
    AuthorizationProfileAdminRepository,
)
from appgenesis.db.session import SessionLocal
from appgenesis.services.access_actions import serialize_actions
from appgenesis.services.auth_profile_entity_scope import (
    build_auth_profile_entity_context_v1,
    get_entity_profile_scope_v1,
    resolve_visibility_scope_for_entity_v1,
)
from appgenesis.services.page import (
    build_users_new_url,
    resolve_visible_menu_keys_v1,
)
from appgenesis.services.permissions import get_user_entity_permissions
from appgenesis.services.session import (
    get_current_user,
    get_session_entity_id,
)
from appgenesis.models import Entity
from appgenesis.routes.profile.router import router
from appgenesis.routes.profile.handlers.profile_common import (
    _append_after_save_marker_to_users_new_url_v6,
    _normalize_process_state,
    _sanitize_users_new_return_url_post_save_v6,
)
# APPGENESIS_BACKEND_RETURN_URL_POST_SAVE_V6_END


@router.post("/users/profile/auth-profile-save")
async def save_authorization_profile_subprocess(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
    requested_mode = str(submitted_form.get("auth_profile_mode") or "").strip().lower()
    if requested_mode not in {"create", "edit"}:
        requested_mode = "create"

    requested_edit_key = str(
        submitted_form.get("original_auth_profile_key") or ""
    ).strip().lower()
    dynamic_field_values: dict[str, str] = {}
    for _field_name, _field_value in submitted_form.multi_items():
        _clean_fname = str(_field_name or "").strip()
        if _clean_fname.startswith("process_field__"):
            _fkey = _clean_fname[len("process_field__"):]
            if _fkey:
                dynamic_field_values[_fkey] = str(_field_value or "").strip()

    clean_label = str(submitted_form.get("auth_profile_label") or "").strip()
    if not clean_label and dynamic_field_values:
        clean_label = next(
            (v for v in dynamic_field_values.values() if v),
            "",
        )
    clean_scope_mode = str(
        submitted_form.get("auth_profile_visibility_scope_mode") or ""
    ).strip().lower()
    clean_session_origin = str(
        submitted_form.get("auth_profile_session_origin") or ""
    ).strip().lower()
    clean_menu_origin = str(
        submitted_form.get("auth_profile_menu_origin") or ""
    ).strip().lower()
    clean_tab_origin = str(
        submitted_form.get("auth_profile_tab_origin") or ""
    ).strip().lower()
    clean_authorization_level = serialize_actions(
        submitted_form.getlist("auth_profile_authorization_level")
    )
    clean_status = _normalize_process_state(
        submitted_form.get("auth_profile_status")
    )
    raw_return_url = str(
        submitted_form.get("auth_profile_return_url") or ""
    ).strip()

    def _read_auth_profile_return_param(param_name: str) -> str:
        clean_param_name = str(param_name or "").strip()

        if not clean_param_name:
            return ""

        try:
            parsed_return_url = urlsplit(raw_return_url)
        except Exception:
            return ""

        if parsed_return_url.scheme or parsed_return_url.netloc:
            return ""

        path = parsed_return_url.path or "/users/new"

        if path != "/users/new":
            return ""

        return str(
            dict(parse_qsl(parsed_return_url.query, keep_blank_values=True)).get(clean_param_name) or ""
        ).strip()

    def _build_auth_profile_fallback_url(
        *,
        target_form_card: bool = False,
        include_edit_key: bool = False,
        extra_params: dict[str, Any] | None = None,
    ) -> str:
        resolved_target = "#auth-profile-form-card" if target_form_card else "#auth-profile-active-card"
        params = {
            "menu": AUTH_PROFILE_MENU_KEY,
            "target": resolved_target,
        }

        resolved_dynamic_section = _read_auth_profile_return_param("dynamic_process_section")

        if resolved_dynamic_section:
            params["dynamic_process_section"] = resolved_dynamic_section

        if include_edit_key and requested_edit_key:
            params["auth_profile_edit_key"] = requested_edit_key

        for raw_key, raw_value in (extra_params or {}).items():
            clean_key = str(raw_key or "").strip()
            clean_value = str(raw_value or "").strip()
            if clean_key and clean_value:
                params[clean_key] = clean_value
        return _append_after_save_marker_to_users_new_url_v6(
            build_users_new_url(**params)
        )

    def _redirect_with_profile_feedback(message: str, *, is_error: bool) -> RedirectResponse:
        extra_params = {
            ("profile_error" if is_error else "profile_success"): message,
        }
        if is_error and requested_mode == "edit" and requested_edit_key:
            extra_params["target"] = "#auth-profile-form-card"
            extra_params["auth_profile_edit_key"] = requested_edit_key
        safe_url = _sanitize_users_new_return_url_post_save_v6(
            raw_return_url,
            extra_params,
        )
        return RedirectResponse(
            url=safe_url or _build_auth_profile_fallback_url(
                target_form_card=is_error and requested_mode == "edit" and bool(requested_edit_key),
                include_edit_key=is_error and requested_mode == "edit" and bool(requested_edit_key),
                extra_params=extra_params,
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

        selected_entity_id = get_session_entity_id(request)
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        resolved_selected_entity_id = entity_permissions.get("selected_entity_id")
        visible_menu_keys = resolve_visible_menu_keys_v1(
            session, current_user["id"], current_user["login_email"], resolved_selected_entity_id
        )
        # Perfil de autorizacao pode ser gerido pelo menu proprio ou pela aba do Administrativo.
        if not ({AUTH_PROFILE_MENU_KEY, "administrativo"} & visible_menu_keys):
            return RedirectResponse(
                url=build_users_new_url(
                    menu="home",
                    error="Sem permissão para aceder ao Perfil de autorização.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not clean_label:
            return _redirect_with_profile_feedback(
                "Informe o perfil.",
                is_error=True,
            )

        auth_profile_config = get_admin_subprocess_config(AUTH_PROFILE_MENU_KEY)
        if auth_profile_config is None:
            return _redirect_with_profile_feedback(
                "Configuração do Perfil de autorização não encontrada.",
                is_error=True,
            )

        entity_number = ""
        if resolved_selected_entity_id is not None:
            resolved_entity_number = session.execute(
                select(Entity.entity_number)
                .where(Entity.id == resolved_selected_entity_id)
                .limit(1)
            ).scalar_one_or_none()
            if resolved_entity_number is not None:
                entity_number = str(resolved_entity_number)

        auth_profile_entity_context = build_auth_profile_entity_context_v1(
            session,
            selected_entity_id=resolved_selected_entity_id,
            permissions=entity_permissions,
        )
        from appgenesis.services.profile import (
            resolve_active_menu_options_v1,
            resolve_active_session_options_v1,
            resolve_active_tab_options_v1,
        )
        from appgenesis.menu_settings import get_sidebar_menu_settings

        sidebar_settings_for_origin = get_sidebar_menu_settings(session)
        allowed_session_origins = {
            option["value"]
            for option in resolve_active_session_options_v1(sidebar_settings_for_origin)
        }
        if clean_session_origin not in allowed_session_origins:
            return _redirect_with_profile_feedback(
                "Definição da origem inválida ou inativa.",
                is_error=True,
            )
        allowed_menu_origins = {
            option["value"]
            for option in resolve_active_menu_options_v1(sidebar_settings_for_origin)
            if option["section"] == clean_session_origin
        }
        if clean_menu_origin not in allowed_menu_origins:
            return _redirect_with_profile_feedback(
                "Menu de origem inválido ou não pertence à sessão escolhida.",
                is_error=True,
            )
        allowed_tab_origins = {
            option["value"]
            for option in resolve_active_tab_options_v1(sidebar_settings_for_origin)
            if option["menu"] == clean_menu_origin
        }
        if clean_tab_origin not in allowed_tab_origins:
            return _redirect_with_profile_feedback(
                "Cabeçalho (aba) inválido ou não pertence ao menu escolhido.",
                is_error=True,
            )
        if not clean_authorization_level:
            return _redirect_with_profile_feedback(
                "Autorização inválida.",
                is_error=True,
            )

        auth_profile_repo = AuthorizationProfileAdminRepository(auth_profile_config)
        save_ok, save_reason, saved_key = auth_profile_repo.save_row(
            session,
            {
                "label": clean_label,
                "visibility_scope_mode": resolve_visibility_scope_for_entity_v1(
                    clean_scope_mode,
                    get_entity_profile_scope_v1(session, get_session_entity_id(request)),
                ),
                "status": clean_status,
                "session_origin": clean_session_origin,
                "menu_origin": clean_menu_origin,
                "tab_origin": clean_tab_origin,
                "authorization_level": clean_authorization_level,
                "dynamic_values": dynamic_field_values,
            },
            context={
                "user_id": current_user["id"],
                "entity_number": entity_number,
                "selected_entity_id": resolved_selected_entity_id,
                "entity_permissions": entity_permissions,
                "auth_profile_entity_context": auth_profile_entity_context,
            },
            edit_key=requested_edit_key if requested_mode == "edit" else "",
        )

        if not save_ok:
            error_message = "Falha ao guardar o perfil."
            if save_reason == "empty_label":
                error_message = "Informe o perfil."
            elif save_reason == "duplicate_key":
                error_message = "Já existe um perfil com esse nome."
            elif save_reason == "duplicate_operation":
                error_message = "Já existe um perfil ativo para esta sessão, menu e cabeçalho. Altere o perfil existente."
            elif save_reason == "edit_key_not_found":
                error_message = "Perfil não encontrado para edição."
            elif save_reason == "member_not_found":
                error_message = "Membro associado ao utilizador não encontrado."
            return _redirect_with_profile_feedback(
                error_message,
                is_error=True,
            )

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return _redirect_with_profile_feedback(
                "Falha ao guardar o perfil.",
                is_error=True,
            )

    success_message = (
        "Perfil atualizado com sucesso."
        if requested_mode == "edit" and requested_edit_key
        else "Perfil criado com sucesso."
    )
    return RedirectResponse(
        url=_sanitize_users_new_return_url_post_save_v6(
            raw_return_url,
            {"profile_success": success_message},
        ) or _build_auth_profile_fallback_url(
            target_form_card=requested_mode == "edit",
            extra_params={"profile_success": success_message},
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/profile/auth-profile-delete")
async def delete_authorization_profile_subprocess(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
    requested_delete_key = str(submitted_form.get("auth_profile_key") or "").strip().lower()
    raw_return_url = str(submitted_form.get("auth_profile_return_url") or "").strip()

    def _read_auth_profile_return_param(param_name: str) -> str:
        clean_param_name = str(param_name or "").strip()
        if not clean_param_name:
            return ""
        try:
            parsed_return_url = urlsplit(raw_return_url)
        except Exception:
            return ""
        if parsed_return_url.scheme or parsed_return_url.netloc:
            return ""
        path = parsed_return_url.path or "/users/new"
        if path != "/users/new":
            return ""
        return str(
            dict(parse_qsl(parsed_return_url.query, keep_blank_values=True)).get(clean_param_name) or ""
        ).strip()

    def _build_auth_profile_delete_fallback_url(
        *,
        extra_params: dict[str, Any] | None = None,
    ) -> str:
        params = {
            "menu": AUTH_PROFILE_MENU_KEY,
            "target": "#auth-profile-active-card",
        }
        resolved_dynamic_section = _read_auth_profile_return_param("dynamic_process_section")
        if resolved_dynamic_section:
            params["dynamic_process_section"] = resolved_dynamic_section
        for raw_key, raw_value in (extra_params or {}).items():
            clean_key = str(raw_key or "").strip()
            clean_value = str(raw_value or "").strip()
            if clean_key and clean_value:
                params[clean_key] = clean_value
        return _append_after_save_marker_to_users_new_url_v6(build_users_new_url(**params))

    def _redirect_with_profile_delete_feedback(message: str, *, is_error: bool) -> RedirectResponse:
        extra_params = {
            ("profile_error" if is_error else "profile_success"): message,
        }
        safe_url = _sanitize_users_new_return_url_post_save_v6(raw_return_url, extra_params)
        return RedirectResponse(
            url=safe_url or _build_auth_profile_delete_fallback_url(extra_params=extra_params),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        selected_entity_id = get_session_entity_id(request)
        visible_menu_keys = resolve_visible_menu_keys_v1(
            session, current_user["id"], current_user["login_email"], selected_entity_id
        )
        # Perfil de autorizacao pode ser gerido pelo menu proprio ou pela aba do Administrativo.
        if not ({AUTH_PROFILE_MENU_KEY, "administrativo"} & visible_menu_keys):
            return RedirectResponse(
                url=build_users_new_url(
                    menu="home",
                    error="Sem permissão para aceder ao Perfil de autorização.",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not requested_delete_key:
            return _redirect_with_profile_delete_feedback(
                "Perfil inválido para eliminar.",
                is_error=True,
            )

        selected_entity_id = get_session_entity_id(request)
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        resolved_selected_entity_id = entity_permissions.get("selected_entity_id")
        auth_profile_entity_context = build_auth_profile_entity_context_v1(
            session,
            selected_entity_id=resolved_selected_entity_id,
            permissions=entity_permissions,
        )
        auth_profile_config = get_admin_subprocess_config(AUTH_PROFILE_MENU_KEY)
        if auth_profile_config is None:
            return _redirect_with_profile_delete_feedback(
                "Configuração do Perfil de autorização não encontrada.",
                is_error=True,
            )

        auth_profile_repo = AuthorizationProfileAdminRepository(auth_profile_config)
        delete_ok, delete_reason = auth_profile_repo.delete_row(
            session,
            requested_delete_key,
            context={
                "user_id": current_user["id"],
                "entity_number": auth_profile_entity_context.get("selected_entity_number", ""),
            },
        )

        if not delete_ok:
            error_message = "Falha ao eliminar o perfil."
            if delete_reason == "delete_key_not_found":
                error_message = "Perfil não encontrado para eliminar."
            elif delete_reason == "member_not_found":
                error_message = "Membro associado ao utilizador não encontrado."
            return _redirect_with_profile_delete_feedback(
                error_message,
                is_error=True,
            )

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return _redirect_with_profile_delete_feedback(
                "Falha ao eliminar o perfil.",
                is_error=True,
            )

    return _redirect_with_profile_delete_feedback(
        "Perfil eliminado com sucesso.",
        is_error=False,
    )
