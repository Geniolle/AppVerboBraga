from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.admin_subprocesses.repositories.definition_repository import (
    DefinitionAdminRepository,
)
from appverbo.admin_subprocesses.registry import get_admin_subprocess_config
from appverbo.core import SessionLocal
from appverbo.routes.profile.router import router
from appverbo.routes.profile.settings.redirects import append_settings_message_to_url_v1
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_current_user, get_session_entity_id


DEFINICOES_DEFAULT_RETURN_URL_V1 = (
    "/users/new?menu=administrativo&admin_tab=definicoes&target=admin-definicoes-card#admin-definicoes-card"
)


####################################################################################
# (1) HELPERS
####################################################################################

def _sanitize_definicoes_return_url_v1(raw_return_url: object) -> str:
    clean_return_url = str(raw_return_url or "").strip() or DEFINICOES_DEFAULT_RETURN_URL_V1

    if clean_return_url.startswith(("http://", "https://", "//")):
        clean_return_url = DEFINICOES_DEFAULT_RETURN_URL_V1

    parts = urlsplit(clean_return_url)

    if parts.path != "/users/new":
        parts = urlsplit(DEFINICOES_DEFAULT_RETURN_URL_V1)

    allowed_targets = {
        "admin-definicoes-card",
        "admin-definicoes-card-create",
        "admin-definicoes-card-inactive",
        "admin-definicoes-card-edit",
    }
    target_value = "admin-definicoes-card"

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

    preserved_params.append(("menu", "administrativo"))
    preserved_params.append(("admin_tab", "definicoes"))
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
    safe_return_url = _sanitize_definicoes_return_url_v1(return_url)
    redirect_url = append_settings_message_to_url_v1(
        safe_return_url,
        message_key,
        message,
    )

    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _ensure_admin_owner_v1(
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
            message="Apenas administradores podem gerir Definições.",
        )

    selected_entity_id = get_session_entity_id(request)
    permissions = get_user_entity_permissions(
        session,
        current_user["id"],
        current_user["login_email"],
        selected_entity_id,
    )

    if not permissions["can_manage_all_entities"]:
        return None, _redirect_with_message_v1(
            return_url=return_url,
            message_key="error",
            message="Apenas Owner pode gerir Definições.",
        )

    return current_user, None


def _build_repository_v1() -> DefinitionAdminRepository:
    config = get_admin_subprocess_config("definicoes")

    if config is None:
        raise RuntimeError("Configuração do subprocesso Definições não encontrada.")

    return DefinitionAdminRepository(config)


####################################################################################
# (2) ENDPOINT - CRIAR / EDITAR DEFINICOES
####################################################################################

@router.post("/settings/definicoes/save", response_class=HTMLResponse)
def save_admin_definicoes_v1(
    request: Request,
    subprocess_mode: str = Form(""),
    subprocess_edit_key: str = Form(""),
    definition_edit_id: str = Form(""),
    subprocess_return_url: str = Form(""),
    definition_parameter_name: str = Form(""),
    definition_type: str = Form(""),
    definition_initial_value: str = Form(""),
    definition_process: str = Form(""),
    definition_subprocess: str = Form(""),
    definition_status: str = Form("active"),
) -> RedirectResponse:
    clean_mode = str(subprocess_mode or "").strip().lower()
    clean_edit_key = str(subprocess_edit_key or definition_edit_id or "").strip()
    safe_return_url = _sanitize_definicoes_return_url_v1(subprocess_return_url)

    if clean_mode not in {"create", "edit"}:
        clean_mode = "edit" if clean_edit_key else "create"

    payload = {
        "parameter_name": definition_parameter_name,
        "parameter_type": definition_type,
        "initial_value": definition_initial_value,
        "process_name": definition_process,
        "subprocess_name": definition_subprocess,
        "status": definition_status,
    }

    repository = _build_repository_v1()

    with SessionLocal() as session:
        _, denied_response = _ensure_admin_owner_v1(
            request=request,
            session=session,
            return_url=safe_return_url,
        )

        if denied_response is not None:
            return denied_response

        try:
            if clean_mode == "edit":
                ok, error_message = repository.update_definition(
                    session=session,
                    definition_id=clean_edit_key,
                    payload=payload,
                )
                if not ok:
                    session.rollback()
                    return _redirect_with_message_v1(
                        return_url=safe_return_url,
                        message_key="error",
                        message=error_message or "Não foi possível atualizar a definição.",
                    )
                session.commit()
                return _redirect_with_message_v1(
                    return_url=safe_return_url,
                    message_key="success",
                    message="Definição atualizada com sucesso.",
                )

            ok, error_message, _ = repository.create_definition(
                session=session,
                payload=payload,
            )

            if not ok:
                session.rollback()
                return _redirect_with_message_v1(
                    return_url=safe_return_url,
                    message_key="error",
                    message=error_message or "Não foi possível criar a definição.",
                )

            session.commit()
            return _redirect_with_message_v1(
                return_url=safe_return_url,
                message_key="success",
                message="Definição criada com sucesso.",
            )
        except Exception:
            session.rollback()
            return _redirect_with_message_v1(
                return_url=safe_return_url,
                message_key="error",
                message="Ocorreu um erro ao guardar a definição.",
            )


####################################################################################
# (3) ENDPOINT - ELIMINAR DEFINICAO
####################################################################################

@router.post("/settings/definicoes/delete", response_class=HTMLResponse)
def delete_admin_definicoes_v1(
    request: Request,
    subprocess_return_url: str = Form(""),
    subprocess_edit_key: str = Form(""),
    definition_id: str = Form(""),
) -> RedirectResponse:
    clean_edit_key = str(subprocess_edit_key or definition_id or "").strip()
    safe_return_url = _sanitize_definicoes_return_url_v1(subprocess_return_url)
    repository = _build_repository_v1()

    with SessionLocal() as session:
        _, denied_response = _ensure_admin_owner_v1(
            request=request,
            session=session,
            return_url=safe_return_url,
        )

        if denied_response is not None:
            return denied_response

        try:
            ok, error_message = repository.delete_definition(
                session=session,
                definition_id=clean_edit_key,
            )

            if not ok:
                session.rollback()
                return _redirect_with_message_v1(
                    return_url=safe_return_url,
                    message_key="error",
                    message=error_message or "Não foi possível eliminar a definição.",
                )

            session.commit()
            return _redirect_with_message_v1(
                return_url=safe_return_url,
                message_key="success",
                message="Definição eliminada com sucesso.",
            )
        except Exception:
            session.rollback()
            return _redirect_with_message_v1(
                return_url=safe_return_url,
                message_key="error",
                message="Ocorreu um erro ao eliminar a definição.",
            )
