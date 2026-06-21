from __future__ import annotations

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import delete, select

from appverbo.core import *  # noqa: F403,F401
from appverbo.services import *  # noqa: F403,F401
from appverbo.models import (
    Member,
    MemberEntity,
    User,
    UserAccountStatus,
)

from appverbo.routes.users.router import router
from appverbo.routes.users.helpers import (
    _ensure_not_last_active_admin_for_member,
    _member_is_within_permissions,
)


@router.post("/users/delete", response_class=HTMLResponse)
def delete_user(
    request: Request,
    user_id: str = Form(...),
    return_menu: str = Form(""),
    return_admin_tab: str = Form(""),
    return_target: str = Form(""),
) -> RedirectResponse:
    clean_user_id = user_id.strip()
    if not clean_user_id.isdigit():
        return RedirectResponse(
            url=build_return_url_v1(
                return_menu=return_menu,
                return_admin_tab=return_admin_tab,
                error="Utilizador inválido para eliminação.",
                default_menu="administrativo",
                default_admin_tab="utilizador",
                default_hash="#create-user-card",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    parsed_user_id = int(clean_user_id)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        selected_entity_id = get_session_entity_id(request)

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error="Apenas administradores podem eliminar utilizadores.",
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#create-user-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if parsed_user_id == int(current_user["id"]):
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error="Não é permitido eliminar o próprio utilizador ligado.",
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#create-user-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        user = session.get(User, parsed_user_id)
        if user is None:
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error="Utilizador não encontrado.",
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#create-user-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not _member_is_within_permissions(
            session,
            int(user.member_id),
            entity_permissions,
        ):
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error="Sem permissão para eliminar este utilizador.",
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#create-user-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # Impede eliminação do último administrador ativo
        target_is_active_admin = (
            str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
            and is_admin_user(session, int(user.id), str(user.login_email or ""))
        )
        if target_is_active_admin:
            can_delete_admin, admin_delete_error = _ensure_not_last_active_admin_for_member(
                session,
                int(user.member_id),
                int(user.id),
            )
            if not can_delete_admin:
                return RedirectResponse(
                    url=build_return_url_v1(
                        return_menu=return_menu,
                        return_admin_tab=return_admin_tab,
                        error=admin_delete_error,
                        default_menu="administrativo",
                        default_admin_tab="utilizador",
                        default_hash="#create-user-card",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        member_id = int(user.member_id)

        # Eliminar o utilizador
        session.delete(user)
        session.flush()

        # Verificar se o membro tem outros utilizadores
        other_users_count = session.scalar(
            select(func.count(User.id)).where(User.member_id == member_id)
        ) or 0

        if other_users_count == 0:
            # Sem outros utilizadores: apagar ligações de entidade e o próprio membro
            session.execute(delete(MemberEntity).where(MemberEntity.member_id == member_id))
            member = session.get(Member, member_id)
            if member is not None:
                session.delete(member)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_return_url_v1(
                    return_menu=return_menu,
                    return_admin_tab=return_admin_tab,
                    error="Não foi possível eliminar o utilizador. Verifique se não existem dependências.",
                    default_menu="administrativo",
                    default_admin_tab="utilizador",
                    default_hash="#create-user-card",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_return_url_v1(
            return_menu=return_menu,
            return_admin_tab=return_admin_tab,
            success="Utilizador eliminado com sucesso.",
            default_menu="administrativo",
            default_admin_tab="utilizador",
            default_hash="#create-user-card",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
