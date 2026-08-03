from __future__ import annotations

from fastapi import Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appgenesis.db.session import SessionLocal
from appgenesis.domains.auth.use_cases import (
    PasswordResetConfirmInvalid,
    PasswordResetConfirmSuccess,
    PasswordResetTokenInvalid,
    execute_password_reset_confirm,
    execute_password_reset_request,
    resolve_password_reset_token,
)
from appgenesis.routes.auth.router import router
from appgenesis.services.auth import parse_password_reset_token
from appgenesis.web.templates import templates


def render_password_reset_request_v1(
    request: Request,
    email: str = "",
    error: str = "",
    success: str = "",
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "password_reset_request.html",
        {
            "request": request,
            "email": email,
            "error": error,
            "success": success,
        },
        status_code=status_code,
    )


def render_password_reset_confirm_v1(
    request: Request,
    token: str = "",
    error: str = "",
    success: str = "",
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "password_reset_confirm.html",
        {
            "request": request,
            "token": token,
            "error": error,
            "success": success,
        },
        status_code=status_code,
    )


@router.get("/password/forgot", response_class=HTMLResponse)
def password_reset_request_page_v1(
    request: Request,
    email: str = Query(""),
) -> HTMLResponse:
    return render_password_reset_request_v1(
        request,
        email=(email or "").strip().lower(),
    )


@router.post("/password/forgot", response_class=HTMLResponse)
def password_reset_request_submit_v1(
    request: Request,
    email: str = Form(...),
) -> HTMLResponse:
    clean_email = (email or "").strip().lower()

    if not clean_email or "@" not in clean_email:
        return render_password_reset_request_v1(
            request,
            email=clean_email,
            error="Informe um email valido.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    with SessionLocal() as session:
        result = execute_password_reset_request(session, request, clean_email)

    if result.error:
        return render_password_reset_request_v1(
            request,
            email=clean_email,
            error=result.error,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return render_password_reset_request_v1(
        request,
        email="",
        success=(
            "Se existir uma conta ativa com este email, "
            "foi enviado um link para redefinir a palavra-passe."
        ),
    )


@router.get("/password/reset", response_class=HTMLResponse)
def password_reset_confirm_page_v1(
    request: Request,
    token: str = Query(""),
) -> HTMLResponse:
    clean_token = (token or "").strip()
    token_payload = parse_password_reset_token(clean_token)

    if token_payload is None:
        return render_password_reset_confirm_v1(
            request,
            token="",
            error="Link invalido ou expirado. Solicite uma nova redefinicao.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    with SessionLocal() as session:
        token_result = resolve_password_reset_token(session, token_payload)

    if isinstance(token_result, PasswordResetTokenInvalid):
        return render_password_reset_confirm_v1(
            request,
            token="",
            error=token_result.error,
            status_code=token_result.status_code,
        )

    return render_password_reset_confirm_v1(request, token=clean_token)


@router.post("/password/reset", response_class=HTMLResponse)
def password_reset_confirm_submit_v1(
    request: Request,
    token: str = Form(""),
    password: str = Form(...),
    confirm_password: str = Form(...),
) -> HTMLResponse:
    clean_token = (token or "").strip()
    token_payload = parse_password_reset_token(clean_token)

    if token_payload is None:
        return render_password_reset_confirm_v1(
            request,
            token="",
            error="Link invalido ou expirado. Solicite uma nova redefinicao.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    with SessionLocal() as session:
        result = execute_password_reset_confirm(
            session, token_payload, password, confirm_password
        )

    if isinstance(result, PasswordResetConfirmInvalid):
        return render_password_reset_confirm_v1(
            request,
            token=clean_token if result.keep_token else "",
            error=result.error,
            status_code=result.status_code,
        )

    assert isinstance(result, PasswordResetConfirmSuccess)
    request.session.clear()

    return RedirectResponse(
        url="/login?success=Palavra-passe redefinida com sucesso. Entre com a nova palavra-passe.",
        status_code=status.HTTP_303_SEE_OTHER,
    )
