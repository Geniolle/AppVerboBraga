from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.admin_subprocesses.sessoes.common import build_sessoes_admin_return_url_v2
from appverbo.admin_subprocesses.repositories.profile_repository import (
    ProfileAdminRepository,
)
from appverbo.admin_subprocesses.registry import get_admin_subprocess_config
from appverbo.core import SessionLocal
from appverbo.routes.profile.router import router
from appverbo.routes.profile.settings.redirects import append_settings_message_to_url_v1
from appverbo.services.auth import is_admin_user
from appverbo.services.session import get_current_user, get_session_entity_id


PERFIL_DEFAULT_RETURN_URL_V1 = (
    build_sessoes_admin_return_url_v2(
        admin_tab="perfil",
        target="admin-perfil-card",
    )
)


####################################################################################
# (1) HELPERS
####################################################################################

def _sanitize_perfil_return_url_v1(raw_return_url: object) -> str:
    clean_return_url = str(raw_return_url or "").strip() or PERFIL_DEFAULT_RETURN_URL_V1

    if clean_return_url.startswith(("http://", "https://", "//")):
        clean_return_url = PERFIL_DEFAULT_RETURN_URL_V1

    parts = urlsplit(clean_return_url)

    if parts.path != "/users/new":
        parts = urlsplit(PERFIL_DEFAULT_RETURN_URL_V1)

    allowed_targets = {
        "admin-perfil-card",
        "admin-perfil-card-create",
        "admin-perfil-card-inactive",
        "admin-perfil-card-edit",
    }
    target_value = "admin-perfil-card"

    preserved_params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in {"menu", "admin_tab", "target", "success", "error", "settings_success", "settings_error"}
    ]

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key != "target":
            continue
        clean_target = str(value or "").strip().lstrip("#")
        if clean_target in allowed_targets:
            target_value = clean_target
        break

    preserved_params.append(("menu", "sessoes"))
    preserved_params.append(("admin_tab", "perfil"))
    preserved_params.append(("target", target_value))

    clean_fragment = str(parts.fragment or "").strip().lstrip("#")
    if clean_fragment not in allowed_targets:
        clean_fragment = target_value

    return urlunsplit((
        "",
        "",
        "/users/new",
        urlencode(preserved_params),
        clean_fragment,
    ))


def _redirect_with_message_v1(
    *,
    return_url: object,
    message_key: str,
    message: str,
) -> RedirectResponse:
    safe_return_url = _sanitize_perfil_return_url_v1(return_url)
    redirect_url = append_settings_message_to_url_v1(
        safe_return_url,
        message_key,
        message,
    )
    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _ensure_admin_v1(
    *,
    request: Request,
    session,
    return_url: object,
) -> tuple[dict[str, object] | None, RedirectResponse | None]:
    current_user = get_current_user(request, session)

    if current_user is None:
        return None, RedirectResponse(
            url="/login?error=Efetue login para continuar.",
            status_code=status.HTTP_302_FOUND,
        )

    if not is_admin_user(session, current_user["id"], current_user["login_email"]):
        return None, _redirect_with_message_v1(
            return_url=return_url,
            message_key="error",
            message="Apenas administradores podem gerir Perfis.",
        )

    return current_user, None


def _build_repository_v1() -> ProfileAdminRepository:
    config = get_admin_subprocess_config("perfil")
    if config is None:
        raise RuntimeError("Configuração do subprocesso Perfil não encontrada.")
    return ProfileAdminRepository(config)


####################################################################################
# (2) ENDPOINT - CRIAR / EDITAR PERFIL
####################################################################################

@router.post("/settings/perfil/save", response_class=HTMLResponse)
def save_admin_perfil_v1(
    request: Request,
    subprocess_mode: str = Form(""),
    subprocess_edit_key: str = Form(""),
    profile_edit_id: str = Form(""),
    subprocess_return_url: str = Form(""),
    profile_name: str = Form(""),
    profile_description: str = Form(""),
    section_visibility_scope_mode: str = Form("entity"),
    profile_status: str = Form("ativo"),
) -> RedirectResponse:
    clean_mode = str(subprocess_mode or "").strip().lower()
    clean_edit_key = str(subprocess_edit_key or profile_edit_id or "").strip()
    safe_return_url = _sanitize_perfil_return_url_v1(subprocess_return_url)

    if clean_mode not in {"create", "edit"}:
        clean_mode = "edit" if clean_edit_key else "create"

    payload = {
        "name": profile_name,
        "description": profile_description,
        "visibility_scope_mode": section_visibility_scope_mode,
        "status": profile_status,
    }

    repository = _build_repository_v1()

    with SessionLocal() as session:
        _, denied_response = _ensure_admin_v1(
            request=request,
            session=session,
            return_url=safe_return_url,
        )
        if denied_response is not None:
            return denied_response

        selected_entity_id = get_session_entity_id(request)

        try:
            if clean_mode == "edit":
                ok, error_message = repository.update_profile(
                    session=session,
                    profile_id=clean_edit_key,
                    payload=payload,
                    selected_entity_id=selected_entity_id,
                )
                if not ok:
                    session.rollback()
                    return _redirect_with_message_v1(
                        return_url=safe_return_url,
                        message_key="error",
                        message=error_message or "Não foi possível atualizar o perfil.",
                    )
                session.commit()
                return _redirect_with_message_v1(
                    return_url=safe_return_url,
                    message_key="success",
                    message="Perfil atualizado com sucesso.",
                )

            ok, error_message, _ = repository.create_profile(
                session=session,
                payload=payload,
                selected_entity_id=selected_entity_id,
            )
            if not ok:
                session.rollback()
                return _redirect_with_message_v1(
                    return_url=safe_return_url,
                    message_key="error",
                    message=error_message or "Não foi possível criar o perfil.",
                )
            session.commit()
            return _redirect_with_message_v1(
                return_url=safe_return_url,
                message_key="success",
                message="Perfil criado com sucesso.",
            )
        except Exception:
            session.rollback()
            return _redirect_with_message_v1(
                return_url=safe_return_url,
                message_key="error",
                message="Ocorreu um erro ao guardar o perfil.",
            )


####################################################################################
# (3) ENDPOINT - ELIMINAR PERFIL
####################################################################################

@router.post("/settings/perfil/delete", response_class=HTMLResponse)
def delete_admin_perfil_v1(
    request: Request,
    subprocess_return_url: str = Form(""),
    subprocess_edit_key: str = Form(""),
    profile_id: str = Form(""),
) -> RedirectResponse:
    clean_edit_key = str(subprocess_edit_key or profile_id or "").strip()
    safe_return_url = _sanitize_perfil_return_url_v1(subprocess_return_url)
    repository = _build_repository_v1()

    with SessionLocal() as session:
        _, denied_response = _ensure_admin_v1(
            request=request,
            session=session,
            return_url=safe_return_url,
        )
        if denied_response is not None:
            return denied_response

        selected_entity_id = get_session_entity_id(request)

        try:
            ok, error_message = repository.delete_profile(
                session=session,
                profile_id=clean_edit_key,
                selected_entity_id=selected_entity_id,
            )
            if not ok:
                session.rollback()
                return _redirect_with_message_v1(
                    return_url=safe_return_url,
                    message_key="error",
                    message=error_message or "Não foi possível eliminar o perfil.",
                )
            session.commit()
            return _redirect_with_message_v1(
                return_url=safe_return_url,
                message_key="success",
                message="Perfil eliminado com sucesso.",
            )
        except Exception:
            session.rollback()
            return _redirect_with_message_v1(
                return_url=safe_return_url,
                message_key="error",
                message="Ocorreu um erro ao eliminar o perfil.",
            )
