from __future__ import annotations

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.profile.router import router
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.sessoes.delete_session import (
    execute_delete_session_v1,
    normalize_delete_session_input_v1,
)
from appverbo.use_cases.sessoes.list_sessions import (
    execute_get_sidebar_refresh_version_v1,
    execute_get_sidebar_sections_data_v1,
)
from appverbo.use_cases.sessoes.move_session import (
    execute_move_session_v1,
    normalize_move_session_input_v1,
)
from appverbo.use_cases.sessoes.save_session import (
    execute_bulk_save_sessions_v1,
    execute_save_session_v1,
    normalize_bulk_sessions_input_v1,
    normalize_save_session_input_v1,
)


# ###################################################################################
# (1) ENDPOINT GET - VERSAO GLOBAL DO SIDEBAR
# ###################################################################################

@router.get("/settings/menu/sidebar-refresh-version")
def get_sidebar_refresh_version_v1(request: Request) -> JSONResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return JSONResponse(
                {"authenticated": False, "version": ""},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        refresh_version = execute_get_sidebar_refresh_version_v1(session=session)

        return JSONResponse(
            {
                "authenticated": True,
                "version": refresh_version,
            }
        )


# ###################################################################################
# (2) ENDPOINT GET - DADOS DE SESSOES
# ###################################################################################

@router.get("/settings/menu/sidebar-sections-data")
def get_sidebar_sections_data_v6(request: Request) -> JSONResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return JSONResponse(
                {
                    "ok": False,
                    "sections": [],
                    "error": "Efetue login para continuar.",
                },
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            sections = execute_get_sidebar_sections_data_v1(session=session)

            return JSONResponse(
                {
                    "ok": True,
                    "sections": sections,
                }
            )
        except Exception as exc:
            return JSONResponse(
                {
                    "ok": False,
                    "sections": [],
                    "error": str(exc),
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ###################################################################################
# (3) ENDPOINT POST - CRIAR/EDITAR UMA SESSAO
# ###################################################################################

@router.post("/settings/menu/sidebar-section-save", response_class=HTMLResponse)
def save_one_sidebar_section_v19(
    request: Request,
    section_mode: str = Form("create"),
    original_section_key: str = Form(""),
    section_label: str = Form(""),
    section_visibility_scope_mode: str = Form("all"),
    section_status: str = Form("ativo"),
    section_status_override_v19: str = Form(""),
    sidebar_section_return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_save_session_input_v1(
        section_mode=section_mode,
        original_section_key=original_section_key,
        section_label=section_label,
        section_visibility_scope_mode=section_visibility_scope_mode,
        section_status=section_status,
        section_status_override=section_status_override_v19,
        sidebar_section_return_url=sidebar_section_return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_save_session_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )


# ###################################################################################
# (4) ENDPOINT POST - MOVER UMA SESSAO
# ###################################################################################

@router.post("/settings/menu/sidebar-section-move-one", response_class=HTMLResponse)
def move_one_sidebar_section_v25(
    request: Request,
    section_key: str = Form(""),
    key: str = Form(""),
    direction: str = Form(""),
    sidebar_section_return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_move_session_input_v1(
        section_key=section_key,
        key=key,
        direction=direction,
        sidebar_section_return_url=sidebar_section_return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_move_session_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )


# ###################################################################################
# (5) ENDPOINT POST - COMPATIBILIDADE TEMPORARIA (BULK)
# ###################################################################################

@router.post("/settings/menu/sidebar-sections", response_class=HTMLResponse)
def edit_sidebar_sections_v2(
    request: Request,
    section_key: list[str] = Form(default=[]),
    section_label: list[str] = Form(default=[]),
    section_visibility_scope_mode: list[str] = Form(default=[]),
    section_status: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    payload_sections = normalize_bulk_sessions_input_v1(
        section_key=section_key,
        section_label=section_label,
        section_visibility_scope_mode=section_visibility_scope_mode,
        section_status=section_status,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_bulk_save_sessions_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            redirect_menu=str(redirect_menu or "administrativo"),
            redirect_target=str(redirect_target or "#settings-menu-edit-card"),
            payload_sections=payload_sections,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )


# ###################################################################################
# (6) ENDPOINT POST - ELIMINAR UMA SESSAO
# ###################################################################################

@router.post("/settings/menu/sidebar-section-delete-one", response_class=HTMLResponse)
def delete_one_sidebar_section_v26(
    request: Request,
    section_key: str = Form(""),
    sidebar_section_return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_delete_session_input_v1(
        section_key=section_key,
        sidebar_section_return_url=sidebar_section_return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_delete_session_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )
