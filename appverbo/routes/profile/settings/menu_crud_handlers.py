from __future__ import annotations

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.profile.router import router
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.menu.create_menu import (
    execute_create_menu_v1,
    normalize_create_menu_input_v1,
)
from appverbo.use_cases.menu.delete_menu import (
    execute_delete_menu_v1,
    normalize_delete_menu_input_v1,
)
from appverbo.use_cases.menu.move_menu import (
    execute_move_menu_v1,
    normalize_move_menu_input_v1,
)
from appverbo.use_cases.menu.update_menu import (
    execute_update_menu_v1,
    normalize_update_menu_input_v1,
)


# ###################################################################################
# (1) ENDPOINT LEGADO - EDITAR MENU
# ###################################################################################


@router.post("/settings/menu/edit", response_class=HTMLResponse)
def edit_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    menu_label: str = Form(...),
    menu_status: str = Form("ativo"),
    menu_visibility_scope: str = Form("all"),
    menu_sidebar_section: str = Form(""),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
    subprocess_return_url: str = Form(""),
    return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_update_menu_input_v1(
        menu_key=menu_key,
        menu_label=menu_label,
        menu_status=menu_status,
        menu_visibility_scope=menu_visibility_scope,
        menu_sidebar_section=menu_sidebar_section,
        redirect_menu=redirect_menu,
        redirect_target=redirect_target,
        subprocess_return_url=subprocess_return_url or return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_update_menu_v1(
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
# (2) ENDPOINT LEGADO - CRIAR MENU
# ###################################################################################


@router.post("/settings/menu/create", response_class=HTMLResponse)
def create_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_label: str = Form(...),
    menu_visibility_scope: str = Form("all"),
    menu_section: str = Form(""),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-menu-card"),
    subprocess_return_url: str = Form(""),
    return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_create_menu_input_v1(
        menu_label=menu_label,
        menu_visibility_scope=menu_visibility_scope,
        menu_section=menu_section,
        redirect_menu=redirect_menu,
        redirect_target=redirect_target,
        subprocess_return_url=subprocess_return_url or return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_create_menu_v1(
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
# (3) ENDPOINT LEGADO - ELIMINAR MENU
# ###################################################################################


@router.post("/settings/menu/delete", response_class=HTMLResponse)
def delete_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-menu-card-inactive"),
    subprocess_return_url: str = Form(""),
    return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_delete_menu_input_v1(
        menu_key=menu_key,
        redirect_menu=redirect_menu,
        redirect_target=redirect_target,
        subprocess_return_url=subprocess_return_url or return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_delete_menu_v1(
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
# (4) ENDPOINT LEGADO - MOVER MENU
# ###################################################################################


@router.post("/settings/menu/move", response_class=HTMLResponse)
def move_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    direction: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-menu-card"),
    subprocess_return_url: str = Form(""),
    return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_move_menu_input_v1(
        menu_key=menu_key,
        direction=direction,
        redirect_menu=redirect_menu,
        redirect_target=redirect_target,
        subprocess_return_url=subprocess_return_url or return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_move_menu_v1(
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
# (5) ENDPOINT NOVO - SAVE ÚNICO DE MENU
# ###################################################################################


@router.post("/settings/menu/save", response_class=HTMLResponse)
def save_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_mode: str = Form(""),
    subprocess_mode: str = Form(""),
    menu_key: str = Form(""),
    menu_label: str = Form(""),
    menu_status: str = Form("ativo"),
    menu_visibility_scope: str = Form("all"),
    menu_sidebar_section: str = Form(""),
    menu_section: str = Form(""),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-menu-card"),
    subprocess_return_url: str = Form(""),
) -> RedirectResponse:
    clean_mode = str(menu_mode or subprocess_mode or "").strip().lower()

    if clean_mode not in {"create", "edit"}:
        clean_mode = "edit" if str(menu_key or "").strip() else "create"

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if clean_mode == "edit":
            payload = normalize_update_menu_input_v1(
                menu_key=menu_key,
                menu_label=menu_label,
                menu_status=menu_status,
                menu_visibility_scope=menu_visibility_scope,
                menu_sidebar_section=menu_sidebar_section or menu_section,
                redirect_menu=redirect_menu,
                redirect_target=(
                    redirect_target
                    if str(redirect_target or "").strip() and str(redirect_target or "").strip() != "#admin-menu-card"
                    else "#settings-menu-edit-card"
                ),
                subprocess_return_url=subprocess_return_url,
            )
            outcome = execute_update_menu_v1(
                session=session,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                payload=payload,
            )
        else:
            payload = normalize_create_menu_input_v1(
                menu_label=menu_label,
                menu_visibility_scope=menu_visibility_scope,
                menu_section=menu_sidebar_section or menu_section,
                redirect_menu=redirect_menu,
                redirect_target=redirect_target or "#admin-menu-card",
                subprocess_return_url=subprocess_return_url,
            )
            outcome = execute_create_menu_v1(
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
# (6) ENDPOINTS DE COMPATIBILIDADE ADMIN-SUBPROCESS
# ###################################################################################


@router.post("/settings/menu/admin-create", response_class=HTMLResponse)
def create_sidebar_menu_setting_admin_subprocess_handler(
    request: Request,
    menu_label: str = Form(...),
    menu_visibility_scope: str = Form("all"),
    menu_section: str = Form(""),
    subprocess_return_url: str = Form(""),
    return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_create_menu_input_v1(
        menu_label=menu_label,
        menu_visibility_scope=menu_visibility_scope,
        menu_section=menu_section,
        redirect_menu="administrativo",
        redirect_target="#admin-menu-card",
        subprocess_return_url=subprocess_return_url or return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_create_menu_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )


@router.post("/settings/menu/admin-move", response_class=HTMLResponse)
def move_sidebar_menu_setting_admin_subprocess_handler(
    request: Request,
    menu_key: str = Form(...),
    direction: str = Form(...),
    subprocess_return_url: str = Form(""),
    return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_move_menu_input_v1(
        menu_key=menu_key,
        direction=direction,
        redirect_menu="administrativo",
        redirect_target="#admin-menu-card",
        subprocess_return_url=subprocess_return_url or return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_move_menu_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )


@router.post("/settings/menu/admin-delete", response_class=HTMLResponse)
def delete_sidebar_menu_setting_admin_subprocess_handler(
    request: Request,
    menu_key: str = Form(...),
    subprocess_return_url: str = Form(""),
    return_url: str = Form(""),
) -> RedirectResponse:
    payload = normalize_delete_menu_input_v1(
        menu_key=menu_key,
        redirect_menu="administrativo",
        redirect_target="#admin-menu-card-inactive",
        subprocess_return_url=subprocess_return_url or return_url,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_delete_menu_v1(
            session=session,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )
