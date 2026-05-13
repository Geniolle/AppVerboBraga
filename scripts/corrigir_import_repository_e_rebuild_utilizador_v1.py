from __future__ import annotations

import re
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
# (3.1) REESCREVER MEMBER_ENTITY_REPOSITORY COM TODAS AS FUNÇÕES NECESSÁRIAS
####################################################################################

write_text_v1(
    "appverbo/repositories/member_entity_repository.py",
    r'''
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, MemberEntityStatus


def get_active_member_entity_links(session: Session, member_id: int) -> list[MemberEntity]:
    return list(
        session.execute(
            select(MemberEntity)
            .where(
                MemberEntity.member_id == int(member_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
            .order_by(MemberEntity.id.asc())
        )
        .scalars()
        .all()
    )


def get_primary_member_entity_link(session: Session, member_id: int) -> MemberEntity | None:
    return session.execute(
        select(MemberEntity)
        .where(MemberEntity.member_id == int(member_id))
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).scalar_one_or_none()


def get_member_entity_link(
    session: Session,
    member_id: int,
    entity_id: int,
) -> MemberEntity | None:
    return session.execute(
        select(MemberEntity)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.entity_id == int(entity_id),
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).scalar_one_or_none()


def upsert_active_member_entity_link(
    session: Session,
    member_id: int,
    entity_id: int,
    *,
    replace_primary: bool = False,
) -> MemberEntity:
    if replace_primary:
        link = get_primary_member_entity_link(session, member_id)
    else:
        link = get_member_entity_link(session, member_id, entity_id)

    if link is None:
        link = MemberEntity(
            member_id=int(member_id),
            entity_id=int(entity_id),
            status=MemberEntityStatus.ACTIVE.value,
            entry_date=date.today(),
        )
        session.add(link)
        return link

    link.entity_id = int(entity_id)
    link.status = MemberEntityStatus.ACTIVE.value

    if link.entry_date is None:
        link.entry_date = date.today()

    return link


def get_primary_entity_for_member(session: Session, member_id: int) -> tuple[int | None, str]:
    row = session.execute(
        select(Entity.id, Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).one_or_none()

    if row is None:
        return None, "-"

    return int(row.id), str(row.name or "-")


def get_primary_entity_name(session: Session, member_id: int) -> str:
    _, entity_name = get_primary_entity_for_member(session, int(member_id))
    return "" if entity_name == "-" else entity_name


def get_active_entity_ids_for_member(session: Session, member_id: int) -> list[int]:
    rows = session.scalars(
        select(MemberEntity.entity_id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
    ).all()

    entity_ids: list[int] = []
    seen: set[int] = set()

    for raw_id in rows:
        if raw_id is None:
            continue

        entity_id = int(raw_id)

        if entity_id in seen:
            continue

        seen.add(entity_id)
        entity_ids.append(entity_id)

    return entity_ids
''',
)


####################################################################################
# (3.2) REESCREVER USER_PROFILE_REPOSITORY COM COMPATIBILIDADE
####################################################################################

write_text_v1(
    "appverbo/repositories/user_profile_repository.py",
    r'''
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from appverbo.models import Profile, UserProfile


def get_active_profile_ids_by_user(session: Session, user_id: int) -> list[int]:
    return [
        int(raw_id)
        for raw_id in session.execute(
            select(UserProfile.profile_id).where(
                UserProfile.user_id == int(user_id),
                UserProfile.is_active.is_(True),
            )
        )
        .scalars()
        .all()
        if raw_id is not None
    ]


def get_active_profile_names_by_user(session: Session, user_id: int) -> list[str]:
    rows = session.execute(
        select(Profile.name)
        .join(UserProfile, UserProfile.profile_id == Profile.id)
        .where(
            UserProfile.user_id == int(user_id),
            UserProfile.is_active.is_(True),
        )
        .order_by(Profile.name.asc())
    ).scalars().all()

    return [str(name or "").strip() for name in rows if str(name or "").strip()]


def replace_user_profile(
    session: Session,
    user_id: int,
    profile_id: int,
    *,
    is_active: bool = True,
) -> None:
    session.execute(delete(UserProfile).where(UserProfile.user_id == int(user_id)))
    session.add(
        UserProfile(
            user_id=int(user_id),
            profile_id=int(profile_id),
            is_active=bool(is_active),
        )
    )


def delete_user_profiles(session: Session, user_id: int) -> None:
    session.execute(delete(UserProfile).where(UserProfile.user_id == int(user_id)))
''',
)


####################################################################################
# (3.3) GARANTIR EXPORTS DO REPOSITORIES __INIT__
####################################################################################

repositories_init = r'''
from appverbo.repositories.entity_repository import (
    get_active_entities,
    get_entity_by_id,
    get_entity_by_name_ci,
)
from appverbo.repositories.member_entity_repository import (
    get_active_entity_ids_for_member,
    get_active_member_entity_links,
    get_member_entity_link,
    get_primary_entity_for_member,
    get_primary_entity_name,
    get_primary_member_entity_link,
    upsert_active_member_entity_link,
)
from appverbo.repositories.member_repository import (
    get_duplicate_member_id_by_email_ci,
    get_member_by_email_ci,
    get_member_by_id,
)
from appverbo.repositories.profile_repository import get_profile_by_id
from appverbo.repositories.user_profile_repository import (
    delete_user_profiles,
    get_active_profile_ids_by_user,
    get_active_profile_names_by_user,
    replace_user_profile,
)
from appverbo.repositories.user_repository import (
    get_duplicate_user_id_by_email_ci,
    get_user_by_email_ci,
    get_user_by_id,
    null_created_by_for_deleted_user,
)

__all__ = [
    "delete_user_profiles",
    "get_active_entities",
    "get_active_entity_ids_for_member",
    "get_active_member_entity_links",
    "get_active_profile_ids_by_user",
    "get_active_profile_names_by_user",
    "get_duplicate_member_id_by_email_ci",
    "get_duplicate_user_id_by_email_ci",
    "get_entity_by_id",
    "get_entity_by_name_ci",
    "get_member_by_email_ci",
    "get_member_by_id",
    "get_member_entity_link",
    "get_primary_entity_for_member",
    "get_primary_entity_name",
    "get_primary_member_entity_link",
    "get_profile_by_id",
    "get_user_by_email_ci",
    "get_user_by_id",
    "null_created_by_for_deleted_user",
    "replace_user_profile",
    "upsert_active_member_entity_link",
]
'''

write_text_v1("appverbo/repositories/__init__.py", repositories_init)


####################################################################################
# (3.4) CORRIGIR WRAPPERS ANTIGOS COM ASSINATURAS COMPATÍVEIS
####################################################################################

write_text_v1(
    "appverbo/use_cases/users/get_user_edit_data.py",
    r'''
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.services.page import get_page_data, get_user_edit_data, get_user_edit_defaults


def get_user_edit_data_v1(
    session: Session,
    *,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
    user_edit_id: int | None,
) -> dict[str, Any]:
    if user_edit_id is None:
        return get_user_edit_defaults()

    page_data = get_page_data(
        session,
        actor_user_id=int(actor_user_id),
        actor_login_email=str(actor_login_email),
        selected_entity_id=selected_entity_id,
    )

    return page_data.get("user_edit_data") or get_user_edit_defaults()


def execute_get_user_edit_data_v1(
    *,
    session: Session,
    user_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, Any]:
    return get_user_edit_data(
        session=session,
        user_id=user_id,
        allowed_entity_ids=allowed_entity_ids,
    )
''',
)

write_text_v1(
    "appverbo/use_cases/users/list_admin_users.py",
    r'''
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.services.page import get_page_data


def list_admin_users_v1(
    session: Session,
    *,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
) -> dict[str, Any]:
    page_data = get_page_data(
        session,
        actor_user_id=int(actor_user_id),
        actor_login_email=str(actor_login_email),
        selected_entity_id=selected_entity_id,
    )

    return {
        "created_users": page_data.get("created_users", []),
        "active_created_users": page_data.get("active_created_users", []),
        "inactive_users": page_data.get("inactive_users", []),
        "pending_users": page_data.get("pending_users", []),
    }


def execute_list_admin_users_v1(
    *,
    session: Session,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    from appverbo.admin_subprocesses.repositories.user_repository import UserAdminRepository
    from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG

    repository = UserAdminRepository(UTILIZADOR_CONFIG)
    return repository.list_rows(session, context or {})
''',
)

write_text_v1(
    "appverbo/use_cases/users/resolve_user_entity.py",
    r'''
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, MemberEntityStatus
from appverbo.repositories.member_entity_repository import get_primary_entity_for_member


def extract_email_domain_v1(raw_email: str) -> str:
    clean_email = (raw_email or "").strip().lower()

    if "@" not in clean_email:
        return ""

    _, domain = clean_email.split("@", 1)
    return domain.strip()


def _allowed_entity_ids_v1(permissions: dict[str, Any]) -> set[int]:
    return {
        int(raw_id)
        for raw_id in (permissions.get("allowed_entity_ids") or set())
        if str(raw_id).strip().isdigit()
    }


def resolve_selected_entity_fallback_v1(
    session: Session,
    selected_entity_id: int | None,
    permissions: dict[str, Any],
) -> Entity | None:
    parsed_entity_id: int | None = None

    if selected_entity_id is not None:
        try:
            parsed_entity_id = int(selected_entity_id)
        except (TypeError, ValueError):
            parsed_entity_id = None

    if parsed_entity_id is not None and parsed_entity_id > 0:
        if not permissions.get("can_manage_all_entities"):
            allowed_ids = _allowed_entity_ids_v1(permissions)
            if parsed_entity_id not in allowed_ids:
                return None

        selected_entity = session.execute(
            select(Entity).where(
                Entity.id == parsed_entity_id,
                Entity.is_active.is_(True),
            )
        ).scalar_one_or_none()

        if selected_entity is not None:
            return selected_entity

    stmt = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())

    if not permissions.get("can_manage_all_entities"):
        allowed_ids = sorted(_allowed_entity_ids_v1(permissions))
        if not allowed_ids:
            return None
        stmt = stmt.where(Entity.id.in_(allowed_ids))

    return session.execute(stmt.limit(1)).scalar_one_or_none()


def resolve_entity_from_user_email_v1(
    session: Session,
    user_email: str,
    permissions: dict[str, Any],
    selected_entity_id: int | None = None,
) -> tuple[Entity | None, str]:
    clean_email = (user_email or "").strip().lower()

    if clean_email and "@" in clean_email:
        stmt = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())

        if not permissions.get("can_manage_all_entities"):
            allowed_ids = sorted(_allowed_entity_ids_v1(permissions))
            if allowed_ids:
                stmt = stmt.where(Entity.id.in_(allowed_ids))
            else:
                return None, "Sem entidades disponíveis para este utilizador."

        entities = list(session.execute(stmt).scalars().all())

        exact_matches = [
            entity
            for entity in entities
            if (entity.email or "").strip().lower() == clean_email
        ]

        if len(exact_matches) == 1:
            return exact_matches[0], ""

        if len(exact_matches) > 1:
            return None, "Existem múltiplas entidades com o mesmo email. Corrija os dados das entidades."

        email_domain = extract_email_domain_v1(clean_email)

        if email_domain:
            domain_matches = [
                entity
                for entity in entities
                if extract_email_domain_v1(entity.email or "") == email_domain
            ]

            if len(domain_matches) == 1:
                return domain_matches[0], ""

            if len(domain_matches) > 1:
                return None, "Existem múltiplas entidades com este domínio de email. Ajuste o email das entidades."

    fallback_entity = resolve_selected_entity_fallback_v1(
        session=session,
        selected_entity_id=selected_entity_id,
        permissions=permissions,
    )

    if fallback_entity is not None:
        return fallback_entity, ""

    return None, "Não foi possível determinar uma entidade ativa para este convite."


def resolve_edit_entity_v1(
    session: Session,
    *,
    email: str,
    clean_entity_id: str,
    member_id: int,
    permissions: dict[str, Any],
) -> tuple[Entity | None, str]:
    selected_entity, error = resolve_entity_from_user_email_v1(
        session=session,
        user_email=email,
        permissions=permissions,
        selected_entity_id=None,
    )

    if selected_entity is not None:
        return selected_entity, ""

    if clean_entity_id.strip().isdigit():
        explicit_entity = session.get(Entity, int(clean_entity_id))

        if explicit_entity is not None:
            can_use = bool(permissions.get("can_manage_all_entities"))

            if not can_use:
                can_use = int(explicit_entity.id) in _allowed_entity_ids_v1(permissions)

            if can_use:
                return explicit_entity, ""

    current_entity_stmt = (
        select(Entity)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(MemberEntity.member_id == int(member_id))
        .order_by(MemberEntity.id.asc())
    )

    if not permissions.get("can_manage_all_entities"):
        allowed_ids = sorted(_allowed_entity_ids_v1(permissions))

        if allowed_ids:
            current_entity_stmt = current_entity_stmt.where(Entity.id.in_(allowed_ids))
        else:
            current_entity_stmt = current_entity_stmt.where(Entity.id == -1)

    current_entity = session.execute(current_entity_stmt.limit(1)).scalar_one_or_none()

    if current_entity is not None:
        return current_entity, ""

    current_entity_id, _ = get_primary_entity_for_member(session, member_id)

    if current_entity_id is not None:
        entity = session.get(Entity, current_entity_id)
        if entity is not None:
            return entity, ""

    return None, error


def execute_resolve_user_entity_v1(
    *,
    session: Session,
    member_id: int,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, Any]:
    stmt = (
        select(Entity.id, Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.desc())
    )

    if allowed_entity_ids is not None:
        if allowed_entity_ids:
            stmt = stmt.where(Entity.id.in_(sorted(allowed_entity_ids)))
        else:
            return {"entity_id": None, "entity_name": ""}

    row = session.execute(stmt.limit(1)).one_or_none()

    if row is None:
        return {"entity_id": None, "entity_name": ""}

    return {"entity_id": int(row.id), "entity_name": str(row.name or "")}
''',
)

write_text_v1(
    "appverbo/use_cases/users/user_permissions.py",
    r'''
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, MemberEntityStatus, Profile, User, UserAccountStatus
from appverbo.repositories.member_entity_repository import get_active_entity_ids_for_member
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions


def allowed_entity_ids_v1(permissions: dict[str, Any]) -> set[int]:
    return {
        int(raw_id)
        for raw_id in (permissions.get("allowed_entity_ids") or set())
        if str(raw_id).strip().isdigit()
    }


def member_is_within_permissions_v1(
    session: Session,
    member_id: int,
    permissions: dict[str, Any],
) -> bool:
    if permissions.get("can_manage_all_entities"):
        return True

    allowed_ids = sorted(allowed_entity_ids_v1(permissions))

    if not allowed_ids:
        return False

    scoped_link_id = session.scalar(
        select(MemberEntity.id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            MemberEntity.entity_id.in_(allowed_ids),
        )
        .limit(1)
    )

    return scoped_link_id is not None


def is_admin_profile_v1(profile: Profile | None) -> bool:
    if profile is None:
        return False

    clean_name = (profile.name or "").strip().lower()

    return clean_name in {"admin", "administrador"}


def _has_other_active_admin_for_entity_v1(
    session: Session,
    entity_id: int,
    excluded_user_id: int,
) -> bool:
    rows = session.execute(
        select(User.id, User.login_email)
        .join(MemberEntity, MemberEntity.member_id == User.member_id)
        .where(
            MemberEntity.entity_id == int(entity_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            User.id != int(excluded_user_id),
            User.account_status == UserAccountStatus.ACTIVE.value,
        )
        .order_by(User.id.asc())
    ).all()

    for row in rows:
        if is_admin_user(session, int(row.id), str(row.login_email or "")):
            return True

    return False


def ensure_not_last_active_admin_for_member_v1(
    session: Session,
    member_id: int,
    excluded_user_id: int,
) -> tuple[bool, str]:
    entity_ids = get_active_entity_ids_for_member(session, int(member_id))

    if not entity_ids:
        return True, ""

    for entity_id in entity_ids:
        if _has_other_active_admin_for_entity_v1(session, entity_id, excluded_user_id):
            continue

        entity_name = session.scalar(
            select(Entity.name).where(Entity.id == int(entity_id)).limit(1)
        )
        display_name = str(entity_name or f"ID {entity_id}")

        return (
            False,
            (
                "Tem de existir pelo menos um Admin ativo por entidade. "
                f"A entidade '{display_name}' ficaria sem Admin ativo."
            ),
        )

    return True, ""


def execute_get_user_permissions_v1(
    *,
    session: Session,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
) -> dict[str, Any]:
    return get_user_entity_permissions(
        session,
        int(actor_user_id),
        str(actor_login_email),
        selected_entity_id,
    )
''',
)


####################################################################################
# (3.5) CORRIGIR MACROS ACTIVE/INACTIVE PARA ACEITAREM STATE OU LISTA
####################################################################################

write_text_v1(
    "templates/admin/users/active_users_card.html",
    r'''
{% macro render_active_users_card_v1(state_or_rows=None) %}
{% set is_state = state_or_rows is not none and state_or_rows.active_rows is defined %}
{% if is_state %}
  {% set user_rows = state_or_rows.active_rows %}
  {% set card_title = state_or_rows.config.active_title if state_or_rows.config is defined else "Utilizadores criados" %}
  {% set card_id = "admin-user-shadow-readonly-card" %}
{% elif state_or_rows is not none %}
  {% set user_rows = state_or_rows %}
  {% set card_title = "Utilizadores criados" %}
  {% set card_id = "admin-users-created-card" %}
{% elif active_created_users is defined %}
  {% set user_rows = active_created_users %}
  {% set card_title = "Utilizadores criados" %}
  {% set card_id = "admin-users-created-card" %}
{% else %}
  {% set user_rows = [] %}
  {% set card_title = "Utilizadores criados" %}
  {% set card_id = "admin-users-created-card" %}
{% endif %}

<section id="{{ card_id }}" class="card admin-user-shadow-readonly-card-v1" data-menu-scope="administrativo" data-admin-subprocess-shadow="utilizador">
  <h2>{{ card_title }}</h2>

  {% if user_rows %}
  <table id="admin-users-table">
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
          <span class="entity-status entity-status-active">
            {{ row.account_status_label if row.account_status_label is defined else "Ativo" }}
          </span>
        </td>
        <td>{{ row.created_at }}</td>
        <td>
          <div class="table-actions">
            <a class="table-icon-btn" href="/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id={{ row.id }}&user_view=1#edit-user-card" title="Exibir utilizador">&#128065;</a>
            <a class="table-icon-btn" href="/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id={{ row.id }}#edit-user-card" title="Modificar utilizador">&#9998;</a>
          </div>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="empty">Sem utilizadores ativos.</p>
  {% endif %}
</section>
{% endmacro %}

{% if active_created_users is defined %}
  {{ render_active_users_card_v1(active_created_users) }}
{% endif %}
''',
)

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
            <a class="table-icon-btn" href="/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id={{ row.id }}&user_view=1#edit-user-card" title="Exibir utilizador">&#128065;</a>
            <a class="table-icon-btn" href="/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id={{ row.id }}#edit-user-card" title="Modificar utilizador">&#9998;</a>
            <form method="post" action="/users/delete" onsubmit="return confirm('Tem a certeza que pretende eliminar este utilizador');">
              <input type="hidden" name="user_id" value="{{ row.id }}">
              <button type="submit" class="table-icon-btn table-icon-btn-danger" title="Eliminar utilizador">&#128465;</button>
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
# (3.6) GARANTIR EXPORTS USE_CASES USERS
####################################################################################

init_content = read_text_v1("appverbo/use_cases/users/__init__.py")

required_imports = [
    "from appverbo.use_cases.users.update_user import execute_update_user_v1",
    "from appverbo.use_cases.users.delete_user import execute_delete_user_v1",
    "from appverbo.use_cases.users.list_admin_users import execute_list_admin_users_v1",
    "from appverbo.use_cases.users.get_user_edit_data import execute_get_user_edit_data_v1",
    "from appverbo.use_cases.users.resolve_user_entity import execute_resolve_user_entity_v1",
    "from appverbo.use_cases.users.user_permissions import execute_get_user_permissions_v1",
]

for import_line in required_imports:
    if import_line not in init_content:
        init_content += "\n" + import_line

write_text_v1("appverbo/use_cases/users/__init__.py", init_content)


####################################################################################
# (3.7) VALIDAÇÕES
####################################################################################

member_entity_content = read_text_v1("appverbo/repositories/member_entity_repository.py")
repositories_init_content = read_text_v1("appverbo/repositories/__init__.py")
active_template = read_text_v1("templates/admin/users/active_users_card.html")
inactive_template = read_text_v1("templates/admin/users/inactive_users_card.html")

require_v1("def get_active_member_entity_links(" in member_entity_content, "ERRO: get_active_member_entity_links não existe.")
require_v1("def get_primary_entity_name(" in member_entity_content, "ERRO: get_primary_entity_name não existe.")
require_v1("get_active_member_entity_links" in repositories_init_content, "ERRO: repositories __init__ não exporta get_active_member_entity_links.")
require_v1('from "partials/admin_user_table_v1.html"' not in active_template, "ERRO: active_users_card mantém import circular.")
require_v1('from "partials/admin_user_table_v1.html"' not in inactive_template, "ERRO: inactive_users_card mantém import circular.")
require_v1("state_or_rows.active_rows" in active_template, "ERRO: active_users_card não aceita state.")
require_v1("state_or_rows.inactive_rows" in inactive_template, "ERRO: inactive_users_card não aceita state.")

print("OK: imports, compatibilidade e templates corrigidos.")
