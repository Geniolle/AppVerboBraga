from __future__ import annotations

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal, templates
from appverbo.routes.users.router import router
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.users import execute_create_user, normalize_create_user_input


@router.post("/users/new", response_class=HTMLResponse)
def create_user(
    request: Request,
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    profile_id: str = Form(""),
    invite_delivery: str = Form("email"),
) -> HTMLResponse:
    payload = normalize_create_user_input(
        full_name=full_name,
        primary_phone=primary_phone,
        email=email,
        profile_id=profile_id,
        invite_delivery=invite_delivery,
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        outcome = execute_create_user(
            session=session,
            request=request,
            actor_user=current_user,
            selected_entity_id=get_session_entity_id(request),
            payload=payload,
        )

    if outcome.kind == "template":
        return templates.TemplateResponse(
            request,
            "new_user.html",
            outcome.template_context or {},
            status_code=outcome.template_status_code,
        )

    return RedirectResponse(
        url=outcome.redirect_url,
        status_code=outcome.redirect_status_code,
    )

