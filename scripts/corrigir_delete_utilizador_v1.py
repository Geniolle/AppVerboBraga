from __future__ import annotations

from pathlib import Path


ROOT = Path(".")


def read_text_v1(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def write_text_v1(path: str, content: str) -> None:
    file_path = ROOT / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content.strip() + "\n", encoding="utf-8")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


####################################################################################
# (3.1) REESCREVER PARTIAL DE UTILIZADORES INATIVOS COM FORMULÁRIO EXPLÍCITO
####################################################################################

write_text_v1(
    "templates/admin/users/inactive_users_card.html",
    r'''
{% macro render_inactive_users_card_v1(state_or_rows=None) %}
{% set is_state = state_or_rows is not none and state_or_rows.inactive_rows is defined %}
{% if is_state %}
  {% set user_rows = state_or_rows.inactive_rows %}
  {% set card_title = state_or_rows.config.inactive_title if state_or_rows.config is defined else "Utilizadores inativos" %}
  {% set card_id = "admin-user-shadow-inactive-card" %}
{% elif state_or_rows is not none %}
  {% set user_rows = state_or_rows %}
  {% set card_title = "Utilizadores inativos" %}
  {% set card_id = "inactive-users-card" %}
{% elif inactive_users is defined %}
  {% set user_rows = inactive_users %}
  {% set card_title = "Utilizadores inativos" %}
  {% set card_id = "inactive-users-card" %}
{% else %}
  {% set user_rows = [] %}
  {% set card_title = "Utilizadores inativos" %}
  {% set card_id = "inactive-users-card" %}
{% endif %}

<section id="{{ card_id }}" class="card admin-user-shadow-readonly-card-v1 admin-user-shadow-inactive-card-v1" data-menu-scope="administrativo" data-admin-subprocess-shadow="utilizador-inactive">
  <h2>{{ card_title }}</h2>

  {% if user_rows %}
  <table id="inactive-users-table">
    <thead>
      <tr>
        <th>ID</th>
        <th>Nome</th>
        <th>Email</th>
        <th>Telefone</th>
        <th>Entidade</th>
        <th>Perfil</th>
        <th>Estado</th>
        <th>Criado em</th>
        <th>Ações</th>
      </tr>
    </thead>
    <tbody>
      {% for row in user_rows %}
      <tr>
        <td>{{ row.id }}</td>
        <td>{{ row.full_name }}</td>
        <td>{{ row.login_email }}</td>
        <td>{{ row.primary_phone }}</td>
        <td>{{ row.entity_name }}</td>
        <td>{{ row.profile_name }}</td>
        <td>
          <span class="entity-status entity-status-inactive">
            {{ row.account_status_label if row.account_status_label is defined else "Inativo" }}
          </span>
        </td>
        <td>{{ row.created_at }}</td>
        <td>
          <div class="table-actions">
            <a
              class="table-icon-btn"
              href="/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id={{ row.id }}&user_view=1#edit-user-card"
              title="Exibir utilizador"
            >&#128065;</a>

            <a
              class="table-icon-btn"
              href="/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id={{ row.id }}#edit-user-card"
              title="Modificar utilizador"
            >&#9998;</a>

            <form
              id="delete-user-form-{{ row.id }}"
              class="admin-user-delete-form-v1"
              method="post"
              action="/users/delete"
              style="display:inline-flex;margin:0;padding:0;"
              data-user-id="{{ row.id }}"
              data-user-email="{{ row.login_email }}"
              onsubmit="return window.confirm('Tem a certeza que pretende eliminar este utilizador inativo?');"
            >
              <input type="hidden" name="user_id" value="{{ row.id }}">
              <button
                type="submit"
                class="admin-user-delete-button-v1"
                title="Eliminar utilizador"
                aria-label="Eliminar utilizador {{ row.login_email }}"
                style="border:0;background:transparent;cursor:pointer;padding:4px 6px;"
              >&#128465;</button>
            </form>
          </div>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="empty">Sem utilizadores inativos.</p>
  {% endif %}
</section>
{% endmacro %}

{% if inactive_users is defined %}
  {{ render_inactive_users_card_v1(inactive_users) }}
{% endif %}
''',
)


####################################################################################
# (3.2) REESCREVER DELETE_HANDLER COM LOGS E RESPOSTA ROBUSTA
####################################################################################

write_text_v1(
    "appverbo/routes/users/delete_handler.py",
    r'''
from __future__ import annotations

import logging
import traceback

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from appverbo.core import SessionLocal
from appverbo.routes.users.router import router
from appverbo.services.page import build_users_new_url
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.use_cases.users import execute_delete_user


logger = logging.getLogger(__name__)


@router.post("/users/delete", response_class=HTMLResponse)
def delete_user_v1(
    request: Request,
    user_id: str = Form(...),
) -> RedirectResponse:
    clean_user_id = user_id.strip()

    logger.info(
        "APPVERBO_DELETE_USER_ROUTE_V1 received user_id=%s path=%s",
        clean_user_id,
        request.url.path,
    )

    if not clean_user_id.isdigit():
        logger.warning(
            "APPVERBO_DELETE_USER_ROUTE_V1 invalid_user_id raw=%s",
            user_id,
        )
        return RedirectResponse(
            url=build_users_new_url(
                error="Utilizador inválido para eliminação.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#inactive-users-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        with SessionLocal() as session:
            current_user = get_current_user(request, session)

            if current_user is None:
                logger.warning(
                    "APPVERBO_DELETE_USER_ROUTE_V1 not_authenticated user_id=%s",
                    clean_user_id,
                )
                return RedirectResponse(
                    url="/login?error=Efetue login para continuar.",
                    status_code=status.HTTP_302_FOUND,
                )

            logger.info(
                "APPVERBO_DELETE_USER_ROUTE_V1 authenticated actor_id=%s target_user_id=%s",
                current_user.get("id"),
                clean_user_id,
            )

            outcome = execute_delete_user(
                session=session,
                actor_user=current_user,
                selected_entity_id=get_session_entity_id(request),
                user_id=int(clean_user_id),
            )

            logger.info(
                "APPVERBO_DELETE_USER_ROUTE_V1 outcome target_user_id=%s redirect=%s",
                clean_user_id,
                outcome.redirect_url,
            )

        return RedirectResponse(
            url=outcome.redirect_url,
            status_code=outcome.redirect_status_code,
        )

    except Exception as exc:
        logger.error(
            "APPVERBO_DELETE_USER_ROUTE_V1 unexpected_error user_id=%s error=%s\n%s",
            clean_user_id,
            exc,
            traceback.format_exc(),
        )
        return RedirectResponse(
            url=build_users_new_url(
                error="Erro ao eliminar utilizador. Consulte os logs recentes do serviço web.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#inactive-users-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )


delete_user = delete_user_v1
''',
)


####################################################################################
# (3.3) REESCREVER USE CASE DELETE COM MENSAGENS MAIS CLARAS
####################################################################################

write_text_v1(
    "appverbo/use_cases/users/delete_user.py",
    r'''
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.repositories.user_profile_repository import delete_user_profiles
from appverbo.repositories.user_repository import get_user_by_id, null_created_by_for_deleted_user
from appverbo.services.auth import is_admin_user
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.user_status import is_user_account_status_inactive_v1
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.user_permissions import member_is_within_permissions_v1


logger = logging.getLogger(__name__)


def _redirect_v1(success: str = "", error: str = "") -> UserActionOutcome:
    return UserActionOutcome(
        kind="redirect",
        redirect_url=build_users_new_url(
            success=success,
            error=error,
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#inactive-users-card",
    )


def execute_delete_user(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    user_id: int,
) -> UserActionOutcome:
    parsed_user_id = int(user_id)

    logger.info(
        "APPVERBO_DELETE_USER_USE_CASE_V1 start actor_id=%s target_user_id=%s",
        actor_user.get("id"),
        parsed_user_id,
    )

    if not is_admin_user(session, int(actor_user["id"]), str(actor_user["login_email"])):
        logger.warning(
            "APPVERBO_DELETE_USER_USE_CASE_V1 denied_not_admin actor_id=%s target_user_id=%s",
            actor_user.get("id"),
            parsed_user_id,
        )
        return _redirect_v1(error="Apenas administradores podem eliminar utilizadores.")

    if parsed_user_id == int(actor_user["id"]):
        logger.warning(
            "APPVERBO_DELETE_USER_USE_CASE_V1 denied_self_delete actor_id=%s",
            actor_user.get("id"),
        )
        return _redirect_v1(error="Não é permitido eliminar o próprio utilizador ligado.")

    entity_permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    user = get_user_by_id(session, parsed_user_id)

    if user is None:
        logger.warning(
            "APPVERBO_DELETE_USER_USE_CASE_V1 not_found target_user_id=%s",
            parsed_user_id,
        )
        return _redirect_v1(error="Utilizador não encontrado.")

    if not member_is_within_permissions_v1(
        session=session,
        member_id=int(user.member_id),
        permissions=entity_permissions,
    ):
        logger.warning(
            "APPVERBO_DELETE_USER_USE_CASE_V1 denied_scope actor_id=%s target_user_id=%s member_id=%s",
            actor_user.get("id"),
            parsed_user_id,
            user.member_id,
        )
        return _redirect_v1(error="Sem permissão para eliminar este utilizador.")

    clean_status = str(user.account_status or "").strip().lower()

    if not is_user_account_status_inactive_v1(clean_status):
        logger.warning(
            "APPVERBO_DELETE_USER_USE_CASE_V1 denied_status target_user_id=%s status=%s",
            parsed_user_id,
            clean_status,
        )
        return _redirect_v1(
            error=(
                "Só é permitido eliminar utilizadores com estado Inativo. "
                f"Estado atual: {clean_status or '-'}."
            )
        )

    null_created_by_for_deleted_user(session, parsed_user_id)
    delete_user_profiles(session, parsed_user_id)
    session.delete(user)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        logger.error(
            "APPVERBO_DELETE_USER_USE_CASE_V1 integrity_error target_user_id=%s error=%s",
            parsed_user_id,
            exc,
        )
        return _redirect_v1(
            error=(
                "Não foi possível eliminar utilizador porque existem registos relacionados. "
                "Remova ou desative as dependências associadas primeiro."
            )
        )

    logger.info(
        "APPVERBO_DELETE_USER_USE_CASE_V1 success target_user_id=%s",
        parsed_user_id,
    )

    return _redirect_v1(success="Utilizador eliminado com sucesso.")


execute_delete_user_v1 = execute_delete_user
''',
)


####################################################################################
# (3.4) VALIDAR CONTEÚDO
####################################################################################

inactive_template = read_text_v1("templates/admin/users/inactive_users_card.html")
delete_handler = read_text_v1("appverbo/routes/users/delete_handler.py")
delete_use_case = read_text_v1("appverbo/use_cases/users/delete_user.py")

require_v1("admin-user-delete-form-v1" in inactive_template, "ERRO: formulário explícito de delete não foi criado.")
require_v1('method="post"' in inactive_template, "ERRO: formulário delete não está como POST.")
require_v1('action="/users/delete"' in inactive_template, "ERRO: formulário delete não aponta para /users/delete.")
require_v1("APPVERBO_DELETE_USER_ROUTE_V1" in delete_handler, "ERRO: delete_handler sem logs de rota.")
require_v1("APPVERBO_DELETE_USER_USE_CASE_V1" in delete_use_case, "ERRO: delete_user use case sem logs.")
require_v1("#inactive-users-card" in delete_use_case, "ERRO: redirect do delete não aponta para inactive-users-card.")

print("OK: delete do subprocesso Utilizador corrigido.")
