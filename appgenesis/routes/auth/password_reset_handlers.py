from __future__ import annotations

from fastapi import Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from appgenesis.core import SessionLocal, templates
from appgenesis.models import Member, User, UserAccountStatus
from appgenesis.routes.auth.router import router
from appgenesis.services.passwords import hash_password
from appgenesis.services.auth import (
    build_password_reset_link,
    build_password_reset_token,
    is_password_reset_token_valid_for_user,
    parse_password_reset_token,
    render_login,
    send_password_reset_email,
)


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
        row = session.execute(
            select(
                User.id,
                User.login_email,
                User.password_hash,
                User.account_status,
                Member.full_name,
            )
            .join(Member, Member.id == User.member_id)
            .where(func.lower(User.login_email) == clean_email)
            .limit(1)
        ).one_or_none()

        if row is not None and row.account_status == UserAccountStatus.ACTIVE.value:
            token = build_password_reset_token(
                int(row.id),
                str(row.login_email),
                str(row.password_hash),
            )
            reset_link = build_password_reset_link(request, token)
            email_ok, email_error = send_password_reset_email(
                recipient_email=str(row.login_email),
                recipient_name=str(row.full_name or ""),
                reset_link=reset_link,
            )

            if not email_ok:
                return render_password_reset_request_v1(
                    request,
                    email=clean_email,
                    error=email_error,
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
        user = session.get(User, int(token_payload["uid"]))
        if (
            user is None
            or (user.login_email or "").strip().lower() != token_payload["email"]
            or not is_password_reset_token_valid_for_user(token_payload, user.password_hash)
        ):
            return render_password_reset_confirm_v1(
                request,
                token="",
                error="Link invalido ou expirado. Solicite uma nova redefinicao.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if user.account_status != UserAccountStatus.ACTIVE.value:
            return render_password_reset_confirm_v1(
                request,
                token="",
                error="A conta nao esta ativa. Contacte o administrador.",
                status_code=status.HTTP_403_FORBIDDEN,
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

    errors: list[str] = []

    if len(password or "") < 8:
        errors.append("A palavra-passe deve ter no minimo 8 caracteres.")

    if password != confirm_password:
        errors.append("A confirmacao da palavra-passe nao confere.")

    if errors:
        return render_password_reset_confirm_v1(
            request,
            token=clean_token,
            error=" ".join(errors),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    with SessionLocal() as session:
        user = session.get(User, int(token_payload["uid"]))
        if (
            user is None
            or (user.login_email or "").strip().lower() != token_payload["email"]
            or not is_password_reset_token_valid_for_user(token_payload, user.password_hash)
        ):
            return render_password_reset_confirm_v1(
                request,
                token="",
                error="Link invalido ou expirado. Solicite uma nova redefinicao.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if user.account_status != UserAccountStatus.ACTIVE.value:
            return render_password_reset_confirm_v1(
                request,
                token="",
                error="A conta nao esta ativa. Contacte o administrador.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        user.password_hash = hash_password(password)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return render_password_reset_confirm_v1(
                request,
                token=clean_token,
                error="Nao foi possivel redefinir a palavra-passe. Tente novamente.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    request.session.clear()

    return RedirectResponse(
        url="/login?success=Palavra-passe redefinida com sucesso. Entre com a nova palavra-passe.",
        status_code=status.HTTP_303_SEE_OTHER,
    )
