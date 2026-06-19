from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) UTILITÁRIOS
####################################################################################

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


####################################################################################
# (2) ATUALIZAR REGISTRY COM COLUNAS NATIVAS IGUAIS A TABELA ANTIGA
####################################################################################

registry_path = ROOT / "appverbo" / "admin_subprocesses" / "registry.py"
registry_content = read_text(registry_path)

new_user_columns = '''USER_COLUMNS = (
    AdminColumnConfig(key="id", label="ID", source="id"),
    AdminColumnConfig(key="full_name", label="NOME", source="full_name"),
    AdminColumnConfig(key="email", label="EMAIL", source="login_email"),
    AdminColumnConfig(key="phone", label="TELEFONE", source="primary_phone"),
    AdminColumnConfig(key="entity", label="ENTIDADE", source="entity_name"),
    AdminColumnConfig(key="profile", label="PERFIL", source="profile_name"),
    AdminColumnConfig(key="status", label="ESTADO", source="status_label"),
    AdminColumnConfig(key="created_at", label="CRIADO EM", source="created_at_label"),
)'''

registry_content, count = re.subn(
    r"USER_COLUMNS\s*=\s*\([\s\S]*?\)\s*\n\s*\n",
    new_user_columns + "\n\n",
    registry_content,
    count=1,
)

if count != 1:
    raise RuntimeError("Não foi possível atualizar USER_COLUMNS no registry.py")

write_text(registry_path, registry_content)


####################################################################################
# (3) ATUALIZAR USER REPOSITORY COM ENTIDADE, PERFIL E CRIADO EM
####################################################################################

user_repository_path = (
    ROOT
    / "appverbo"
    / "admin_subprocesses"
    / "repositories"
    / "user_repository.py"
)

user_repository_content = '''\
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    Profile,
    User,
    UserProfile,
)
from appverbo.services.user_status import (
    is_user_account_status_active_v1,
    normalize_user_account_status_v1,
    user_account_status_label_pt_v1,
)


####################################################################################
# (1) REPOSITORY NATIVA DO SUBPROCESSO UTILIZADOR
####################################################################################

class UserAdminRepository(BaseAdminSubprocessRepository):
    """
    Repository isolada para o subprocesso Utilizador.

    Esta versão mantém a leitura segura para escala:
    - usa SELECT por colunas;
    - evita N+1 para Member, Entity e Profile;
    - respeita escopo de entidades quando recebido no context;
    - não altera criação, edição, convite ou geração de link.
    """

    def _resolve_allowed_entity_ids(
        self,
        context: dict[str, Any] | None,
    ) -> set[int] | None:
        if not isinstance(context, dict):
            return None

        raw_allowed_entity_ids = context.get("allowed_entity_ids")

        if raw_allowed_entity_ids is None:
            return None

        allowed_entity_ids: set[int] = set()

        for raw_id in raw_allowed_entity_ids:
            try:
                allowed_entity_ids.add(int(raw_id))
            except (TypeError, ValueError):
                continue

        return allowed_entity_ids

    def _resolve_scoped_member_ids(
        self,
        session: Any,
        allowed_entity_ids: set[int] | None,
    ) -> set[int] | None:
        if allowed_entity_ids is None:
            return None

        if not allowed_entity_ids:
            return set()

        rows = session.execute(
            select(MemberEntity.member_id)
            .where(
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                MemberEntity.entity_id.in_(allowed_entity_ids),
            )
            .distinct()
        ).scalars().all()

        return {
            int(member_id)
            for member_id in rows
            if member_id is not None
        }

    def _build_base_stmt(self):
        return (
            select(
                User.id.label("id"),
                User.member_id.label("member_id"),
                Member.full_name.label("full_name"),
                Member.primary_phone.label("primary_phone"),
                User.login_email.label("login_email"),
                User.account_status.label("account_status"),
                User.created_at.label("created_at"),
            )
            .join(Member, Member.id == User.member_id)
        )

    def _format_datetime_label(self, raw_value: Any) -> str:
        if raw_value is None:
            return "-"

        if isinstance(raw_value, datetime):
            return raw_value.strftime("%Y-%m-%d %H:%M")

        value = str(raw_value or "").strip()

        if not value:
            return "-"

        return value[:16]

    def _build_entity_names_by_member_id(
        self,
        session: Any,
        member_ids: set[int],
    ) -> dict[int, str]:
        if not member_ids:
            return {}

        rows = session.execute(
            select(
                MemberEntity.member_id.label("member_id"),
                Entity.name.label("entity_name"),
            )
            .join(Entity, Entity.id == MemberEntity.entity_id)
            .where(
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                MemberEntity.member_id.in_(member_ids),
            )
            .order_by(Entity.name.asc())
        ).all()

        names_by_member_id: dict[int, list[str]] = {}

        for row in rows:
            member_id = int(row.member_id)
            entity_name = str(row.entity_name or "").strip()

            if not entity_name:
                continue

            names_by_member_id.setdefault(member_id, [])

            if entity_name not in names_by_member_id[member_id]:
                names_by_member_id[member_id].append(entity_name)

        return {
            member_id: ", ".join(entity_names)
            for member_id, entity_names in names_by_member_id.items()
        }

    def _build_profile_names_by_user_id(
        self,
        session: Any,
        user_ids: set[int],
    ) -> dict[int, str]:
        if not user_ids:
            return {}

        rows = session.execute(
            select(
                UserProfile.user_id.label("user_id"),
                Profile.name.label("profile_name"),
            )
            .join(Profile, Profile.id == UserProfile.profile_id)
            .where(
                UserProfile.is_active.is_(True),
                UserProfile.user_id.in_(user_ids),
            )
            .order_by(Profile.name.asc())
        ).all()

        names_by_user_id: dict[int, list[str]] = {}

        for row in rows:
            user_id = int(row.user_id)
            profile_name = str(row.profile_name or "").strip()

            if not profile_name:
                continue

            names_by_user_id.setdefault(user_id, [])

            if profile_name not in names_by_user_id[user_id]:
                names_by_user_id[user_id].append(profile_name)

        return {
            user_id: ", ".join(profile_names)
            for user_id, profile_names in names_by_user_id.items()
        }

    def _to_row(
        self,
        row: Any,
        entity_names_by_member_id: dict[int, str] | None = None,
        profile_names_by_user_id: dict[int, str] | None = None,
    ) -> dict[str, Any]:
        entity_names_by_member_id = entity_names_by_member_id or {}
        profile_names_by_user_id = profile_names_by_user_id or {}

        normalized_status = normalize_user_account_status_v1(row.account_status)
        is_active = is_user_account_status_active_v1(normalized_status)

        user_id = int(row.id)
        member_id = int(row.member_id)
        full_name = str(row.full_name or "").strip()
        primary_phone = str(row.primary_phone or "").strip()
        login_email = str(row.login_email or "").strip().lower()
        entity_name = entity_names_by_member_id.get(member_id, "-")
        profile_name = profile_names_by_user_id.get(user_id, "-")
        created_at_label = self._format_datetime_label(row.created_at)

        return {
            "id": user_id,
            "key": str(user_id),
            "member_id": member_id,
            "full_name": full_name,
            "name": full_name,
            "label": full_name or login_email,
            "login_email": login_email,
            "email": login_email,
            "primary_phone": primary_phone or "-",
            "phone": primary_phone or "-",
            "entity_name": entity_name,
            "profile_name": profile_name,
            "account_status": normalized_status,
            "status": normalized_status,
            "status_label": user_account_status_label_pt_v1(normalized_status),
            "is_active": is_active,
            "created_at": row.created_at,
            "created_at_label": created_at_label,
        }

    def list_rows(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        allowed_entity_ids = self._resolve_allowed_entity_ids(context)
        scoped_member_ids = self._resolve_scoped_member_ids(
            session,
            allowed_entity_ids,
        )

        if scoped_member_ids is not None and not scoped_member_ids:
            return []

        stmt = self._build_base_stmt().order_by(User.id.desc())

        if scoped_member_ids is not None:
            stmt = stmt.where(User.member_id.in_(scoped_member_ids))

        rows = session.execute(stmt).all()

        user_ids = {
            int(row.id)
            for row in rows
            if row.id is not None
        }
        member_ids = {
            int(row.member_id)
            for row in rows
            if row.member_id is not None
        }

        entity_names_by_member_id = self._build_entity_names_by_member_id(
            session,
            member_ids,
        )
        profile_names_by_user_id = self._build_profile_names_by_user_id(
            session,
            user_ids,
        )

        return [
            self._to_row(
                row,
                entity_names_by_member_id=entity_names_by_member_id,
                profile_names_by_user_id=profile_names_by_user_id,
            )
            for row in rows
        ]

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_edit_key = str(edit_key or "").strip()

        if not clean_edit_key.isdigit():
            return None

        allowed_entity_ids = self._resolve_allowed_entity_ids(context)
        scoped_member_ids = self._resolve_scoped_member_ids(
            session,
            allowed_entity_ids,
        )

        if scoped_member_ids is not None and not scoped_member_ids:
            return None

        stmt = self._build_base_stmt().where(User.id == int(clean_edit_key))

        if scoped_member_ids is not None:
            stmt = stmt.where(User.member_id.in_(scoped_member_ids))

        row = session.execute(stmt).one_or_none()

        if row is None:
            return None

        member_ids = {int(row.member_id)}
        user_ids = {int(row.id)}

        entity_names_by_member_id = self._build_entity_names_by_member_id(
            session,
            member_ids,
        )
        profile_names_by_user_id = self._build_profile_names_by_user_id(
            session,
            user_ids,
        )

        return self._to_row(
            row,
            entity_names_by_member_id=entity_names_by_member_id,
            profile_names_by_user_id=profile_names_by_user_id,
        )
'''

write_text(user_repository_path, user_repository_content)


####################################################################################
# (4) ATUALIZAR PARTIAL PARA DESTACAR STATUS E MANTER RENDER GENERICO
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"

partial_content = '''\
{% macro render_admin_user_shadow_cell_v1(row, column) %}
  {% set value = row.get(column.source, "-") %}
  {% if column.source == "status_label" %}
    <span class="status-pill status-pill-{{ row.get('status', '') }}">{{ value }}</span>
  {% else %}
    {{ value }}
  {% endif %}
{% endmacro %}

{% macro render_admin_user_shadow_table_v1(rows, columns) %}
<div class="admin-table-wrap">
  <table class="admin-subprocess-table-v1 admin-user-shadow-table-v1">
    <thead>
      <tr>
        {% for column in columns %}
        <th>{{ column.label }}</th>
        {% endfor %}
      </tr>
    </thead>
    <tbody>
      {% for row in rows %}
      <tr data-admin-user-shadow-row="{{ row.get('id', '') }}">
        {% for column in columns %}
        <td>{{ render_admin_user_shadow_cell_v1(row, column) }}</td>
        {% endfor %}
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v1(state) %}
<section
  id="admin-user-shadow-readonly-card"
  class="card admin-user-shadow-readonly-card-v1"
  data-menu-scope="administrativo"
  data-admin-subprocess-shadow="utilizador"
>
  <div class="profile-card-header">
    <div>
      <h2>Utilizadores - leitura nativa</h2>
      <p class="muted">
        Validação do novo processo único. Este bloco é apenas leitura e não altera a criação, edição ou envio de convites.
      </p>
    </div>
  </div>

  <div class="admin-subsection">
    <h3>{{ state.config.active_title }}</h3>
    <p class="muted">Total: {{ state.active_rows|length }}</p>

    {% if state.active_rows %}
      {{ render_admin_user_shadow_table_v1(state.active_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores ativos no processo nativo.</p>
    {% endif %}
  </div>

  <div class="admin-subsection">
    <h3>{{ state.config.inactive_title }}</h3>

    {% if state.inactive_rows %}
      {{ render_admin_user_shadow_table_v1(state.inactive_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores inativos, pendentes ou bloqueados no processo nativo.</p>
    {% endif %}
  </div>
</section>
{% endmacro %}
'''

write_text(partial_path, partial_content)


####################################################################################
# (5) ATUALIZAR SCRIPT DE VALIDACAO PARA CONFERIR NOVAS COLUNAS
####################################################################################

check_script_path = ROOT / "scripts" / "check_admin_subprocess_utilizador_v1.py"

check_script_content = '''\
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from appverbo.admin_subprocesses.registry import require_admin_subprocess_config
from appverbo.admin_subprocesses.runtime import build_admin_subprocess_state_from_repository
from appverbo.core import SessionLocal


####################################################################################
# (1) VALIDAR STATE NATIVO DO SUBPROCESSO UTILIZADOR
####################################################################################

def main() -> None:
    config = require_admin_subprocess_config("utilizador")

    if not config.enabled:
        raise RuntimeError("Subprocesso Utilizador não está ativo no registry.")

    if not config.repository_class:
        raise RuntimeError("Subprocesso Utilizador sem repository_class.")

    expected_columns = {
        "id",
        "full_name",
        "login_email",
        "primary_phone",
        "entity_name",
        "profile_name",
        "status_label",
        "created_at_label",
    }

    configured_sources = {
        str(column.source or "").strip()
        for column in config.columns
    }

    missing_config_sources = expected_columns - configured_sources

    if missing_config_sources:
        raise RuntimeError(
            "Colunas esperadas ausentes no registry do Utilizador: "
            + ", ".join(sorted(missing_config_sources))
        )

    with SessionLocal() as session:
        state = build_admin_subprocess_state_from_repository(
            config=config,
            session=session,
            edit_key="",
            success="",
            error="",
            return_url="/users/new?menu=administrativo&admin_tab=utilizador",
            context={},
        )

    if state is None:
        raise RuntimeError("Não foi possível construir o state do Utilizador.")

    all_rows = list(state.active_rows or []) + list(state.inactive_rows or [])

    if all_rows:
        missing_row_fields = expected_columns - set(all_rows[0].keys())

        if missing_row_fields:
            raise RuntimeError(
                "Campos esperados ausentes na primeira linha do Utilizador: "
                + ", ".join(sorted(missing_row_fields))
            )

    print("OK: state do subprocesso Utilizador criado.")
    print(f"Config: {state.config.key} - {state.config.label}")
    print(f"Colunas: {', '.join(column.label for column in state.config.columns)}")
    print(f"Ativos: {len(state.active_rows)}")
    print(f"Inativos/Pendentes/Bloqueados: {len(state.inactive_rows)}")


if __name__ == "__main__":
    main()
'''

write_text(check_script_path, check_script_content)


####################################################################################
# (6) RESULTADO
####################################################################################

print("OK: Utilizador nativo enriquecido com ID, Nome, Email, Telefone, Entidade, Perfil, Estado e Criado em.")
