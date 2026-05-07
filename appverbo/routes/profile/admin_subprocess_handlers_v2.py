from __future__ import annotations

from typing import Any

from fastapi import Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError

from appverbo.core import *  # noqa: F403,F401
from appverbo.routes.profile.router import router
from appverbo.admin_subprocesses.v2_registry import get_admin_subprocess_config_v2
from appverbo.admin_subprocesses.v2_service import (
    add_admin_subprocess_message_v2,
    build_admin_subprocess_state_v2,
    create_admin_subprocess_repository_v2,
    default_admin_subprocess_return_url_v2,
    sanitize_admin_subprocess_return_url_v2,
)


# ###################################################################################
# (1) HELPERS
# ###################################################################################

def get_current_admin_user_or_redirect_v2(request: Request, session: Any) -> tuple[dict[str, Any] | None, RedirectResponse | None]:
    current_user = get_current_user(request, session)

    if current_user is None:
        return None, RedirectResponse(
            url="/login?error=Efetue login para continuar.",
            status_code=status.HTTP_302_FOUND,
        )

    current_user_is_admin = is_admin_user(
        session,
        current_user["id"],
        current_user["login_email"],
    )

    if not current_user_is_admin:
        return None, RedirectResponse(
            url="/users/new?menu=home&error=Apenas administradores podem aceder a este subprocesso.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return current_user, None


def build_redirect_after_admin_subprocess_action_v2(
    *,
    config: Any,
    raw_return_url: Any,
    success: str = "",
    error: str = "",
) -> RedirectResponse:
    fallback_url = default_admin_subprocess_return_url_v2(config)
    safe_return_url = sanitize_admin_subprocess_return_url_v2(raw_return_url, fallback_url)
    redirect_url = add_admin_subprocess_message_v2(
        safe_return_url,
        config=config,
        success=success,
        error=error,
    )

    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ###################################################################################
# (2) PAGINA STANDALONE GENERICA
# ###################################################################################

@router.get("/admin/subprocess-v2/{subprocess_key}", response_class=HTMLResponse)
def admin_subprocess_standalone_page_v2(
    subprocess_key: str,
    request: Request,
    edit_key: str = "",
    entity_edit_id: str = "",
) -> HTMLResponse:
    config = get_admin_subprocess_config_v2(subprocess_key)

    if config is None:
        return HTMLResponse("Subprocesso não encontrado.", status_code=404)

    with SessionLocal() as session:
        current_user, redirect_response = get_current_admin_user_or_redirect_v2(request, session)

        if redirect_response is not None:
            return redirect_response

        state = build_admin_subprocess_state_v2(
            key=config.key,
            session=session,
            request=request,
            current_user=current_user,
            edit_key=edit_key or entity_edit_id,
            success=str(request.query_params.get(f"{config.key}_success") or ""),
            error=str(request.query_params.get(f"{config.key}_error") or ""),
            return_url=f"/admin/subprocess-v2/{config.key}",
        )

        return templates.TemplateResponse(
            request,
            "admin_subprocess_v2_standalone.html",
            {
                "request": request,
                "state": state,
                "current_user": current_user,
            },
        )


# ###################################################################################
# (3) ACOES GENERICAS
# ###################################################################################

@router.post("/admin/subprocess-v2/{subprocess_key}/create")
async def create_admin_subprocess_record_v2(
    subprocess_key: str,
    request: Request,
) -> RedirectResponse:
    config = get_admin_subprocess_config_v2(subprocess_key)

    if config is None:
        return RedirectResponse(
            url="/users/new?menu=administrativo&error=Subprocesso não encontrado.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    submitted_form = await request.form()
    raw_return_url = submitted_form.get(config.return_url_field)

    with SessionLocal() as session:
        current_user, redirect_response = get_current_admin_user_or_redirect_v2(request, session)

        if redirect_response is not None:
            return redirect_response

        repository = create_admin_subprocess_repository_v2(
            config=config,
            session=session,
            request=request,
            current_user=current_user,
        )

        data = repository.clean_form(submitted_form)
        errors = repository.validate_create(data)

        if errors:
            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                error=" ".join(errors),
            )

        try:
            result = repository.create(data)

            if not result.get("ok", False):
                session.rollback()
                return build_redirect_after_admin_subprocess_action_v2(
                    config=config,
                    raw_return_url=raw_return_url,
                    error=str(result.get("message") or "Não foi possível criar o registo."),
                )

            session.commit()

            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                success=str(result.get("message") or "Registo criado com sucesso."),
            )
        except IntegrityError:
            session.rollback()
            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                error="Não foi possível criar o registo por conflito de dados.",
            )


@router.post("/admin/subprocess-v2/{subprocess_key}/update")
async def update_admin_subprocess_record_v2(
    subprocess_key: str,
    request: Request,
) -> RedirectResponse:
    config = get_admin_subprocess_config_v2(subprocess_key)

    if config is None:
        return RedirectResponse(
            url="/users/new?menu=administrativo&error=Subprocesso não encontrado.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    submitted_form = await request.form()
    raw_return_url = submitted_form.get(config.return_url_field)
    edit_key = str(submitted_form.get(config.edit_key_field) or "").strip()

    with SessionLocal() as session:
        current_user, redirect_response = get_current_admin_user_or_redirect_v2(request, session)

        if redirect_response is not None:
            return redirect_response

        repository = create_admin_subprocess_repository_v2(
            config=config,
            session=session,
            request=request,
            current_user=current_user,
        )

        data = repository.clean_form(submitted_form)
        errors = repository.validate_update(edit_key, data)

        if errors:
            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                error=" ".join(errors),
            )

        try:
            result = repository.update(edit_key, data)

            if not result.get("ok", False):
                session.rollback()
                return build_redirect_after_admin_subprocess_action_v2(
                    config=config,
                    raw_return_url=raw_return_url,
                    error=str(result.get("message") or "Não foi possível atualizar o registo."),
                )

            session.commit()

            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                success=str(result.get("message") or "Registo atualizado com sucesso."),
            )
        except IntegrityError:
            session.rollback()
            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                error="Não foi possível atualizar o registo por conflito de dados.",
            )


@router.post("/admin/subprocess-v2/{subprocess_key}/delete")
async def delete_admin_subprocess_record_v2(
    subprocess_key: str,
    request: Request,
) -> RedirectResponse:
    config = get_admin_subprocess_config_v2(subprocess_key)

    if config is None:
        return RedirectResponse(
            url="/users/new?menu=administrativo&error=Subprocesso não encontrado.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    submitted_form = await request.form()
    raw_return_url = submitted_form.get(config.return_url_field)
    edit_key = str(submitted_form.get(config.edit_key_field) or "").strip()

    with SessionLocal() as session:
        current_user, redirect_response = get_current_admin_user_or_redirect_v2(request, session)

        if redirect_response is not None:
            return redirect_response

        repository = create_admin_subprocess_repository_v2(
            config=config,
            session=session,
            request=request,
            current_user=current_user,
        )

        try:
            result = repository.delete(edit_key)

            if not result.get("ok", False):
                session.rollback()
                return build_redirect_after_admin_subprocess_action_v2(
                    config=config,
                    raw_return_url=raw_return_url,
                    error=str(result.get("message") or "Não foi possível eliminar o registo."),
                )

            session.commit()

            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                success=str(result.get("message") or "Registo eliminado com sucesso."),
            )
        except IntegrityError:
            session.rollback()
            return build_redirect_after_admin_subprocess_action_v2(
                config=config,
                raw_return_url=raw_return_url,
                error="Não foi possível eliminar o registo porque existem dados relacionados.",
            )
