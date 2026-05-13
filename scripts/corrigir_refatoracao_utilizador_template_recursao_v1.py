from __future__ import annotations

from pathlib import Path


ROOT = Path(".")


def read_text_v1(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def write_text_v1(path: str, content: str) -> None:
    file_path = ROOT / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


####################################################################################
# (3.1) CORRIGIR IMPORTAÇÃO CIRCULAR DOS PARTIALS DE UTILIZADOR
####################################################################################

active_users_card = r'''
{% macro render_active_users_card_v1(rows=None) %}
{% set _unused_kwargs = kwargs %}
{% set user_rows = rows %}
{% if user_rows is none %}
  {% set user_rows = kwargs.get("active_created_users") %}
{% endif %}
{% if user_rows is none %}
  {% set user_rows = kwargs.get("created_users") %}
{% endif %}
{% if user_rows is none and active_created_users is defined %}
  {% set user_rows = active_created_users %}
{% endif %}
{% if user_rows is none %}
  {% set user_rows = [] %}
{% endif %}

<section id="admin-users-created-card" class="card" data-menu-scope="administrativo">
  <h2>Utilizadores criados</h2>

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
'''

inactive_users_card = r'''
{% macro render_inactive_users_card_v1(rows=None) %}
{% set _unused_kwargs = kwargs %}
{% set user_rows = rows %}
{% if user_rows is none %}
  {% set user_rows = kwargs.get("inactive_users") %}
{% endif %}
{% if user_rows is none and inactive_users is defined %}
  {% set user_rows = inactive_users %}
{% endif %}
{% if user_rows is none %}
  {% set user_rows = [] %}
{% endif %}

<section id="inactive-users-card" class="card" data-menu-scope="administrativo">
  <h2>Utilizadores inativos</h2>

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
            <form method="post" action="/users/delete" onsubmit="return confirm('Tem a certeza que pretende eliminar este utilizador');">
              <input type="hidden" name="user_id" value="{{ row.id }}">
              <button
                type="submit"
                class="table-icon-btn table-icon-btn-danger"
                title="Eliminar utilizador"
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
'''

write_text_v1("templates/admin/users/active_users_card.html", active_users_card)
write_text_v1("templates/admin/users/inactive_users_card.html", inactive_users_card)


####################################################################################
# (3.2) REPOR FUNÇÕES ANTIGAS DE COMPATIBILIDADE NOS REPOSITÓRIOS
####################################################################################

member_entity_path = "appverbo/repositories/member_entity_repository.py"
member_entity_content = read_text_v1(member_entity_path)

if "def get_active_member_entity_links(" not in member_entity_content:
    member_entity_content += r'''

def get_active_member_entity_links(session: Session, member_id: int) -> list[MemberEntity]:
    return list(
        session.execute(
            select(MemberEntity).where(
                MemberEntity.member_id == int(member_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
        ).scalars().all()
    )


def get_primary_entity_name(session: Session, member_id: int) -> str:
    _, entity_name = get_primary_entity_for_member(session, int(member_id))
    return "" if entity_name == "-" else entity_name
'''

write_text_v1(member_entity_path, member_entity_content)


user_profile_path = "appverbo/repositories/user_profile_repository.py"
user_profile_content = read_text_v1(user_profile_path)

if "from sqlalchemy import delete, select" not in user_profile_content:
    user_profile_content = user_profile_content.replace(
        "from sqlalchemy import delete",
        "from sqlalchemy import delete, select",
    )

if "from appverbo.models import Profile, UserProfile" not in user_profile_content:
    user_profile_content = user_profile_content.replace(
        "from appverbo.models import UserProfile",
        "from appverbo.models import Profile, UserProfile",
    )

if "def get_active_profile_ids_by_user(" not in user_profile_content:
    user_profile_content += r'''

def get_active_profile_ids_by_user(session: Session, user_id: int) -> list[int]:
    return [
        int(raw_id)
        for raw_id in session.execute(
            select(UserProfile.profile_id).where(
                UserProfile.user_id == int(user_id),
                UserProfile.is_active.is_(True),
            )
        ).scalars().all()
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
'''

write_text_v1(user_profile_path, user_profile_content)


####################################################################################
# (3.3) REPOR ALIASES ANTIGOS NOS USE CASES
####################################################################################

aliases = {
    "appverbo/use_cases/users/update_user.py": "\n\nexecute_update_user_v1 = execute_update_user\n",
    "appverbo/use_cases/users/delete_user.py": "\n\nexecute_delete_user_v1 = execute_delete_user\n",
    "appverbo/use_cases/users/list_admin_users.py": "\n\nexecute_list_admin_users_v1 = list_admin_users_v1\n",
    "appverbo/use_cases/users/get_user_edit_data.py": "\n\nexecute_get_user_edit_data_v1 = get_user_edit_data_v1\n",
    "appverbo/use_cases/users/resolve_user_entity.py": "\n\nexecute_resolve_user_entity_v1 = resolve_entity_from_user_email_v1\n",
    "appverbo/use_cases/users/user_permissions.py": "\n\nexecute_get_user_permissions_v1 = allowed_entity_ids_v1\n",
}

for path, alias_line in aliases.items():
    content = read_text_v1(path)
    alias_name = alias_line.strip().split(" = ", 1)[0]

    if alias_name not in content:
        content += alias_line
        write_text_v1(path, content)


init_path = "appverbo/use_cases/users/__init__.py"
init_content = read_text_v1(init_path)

extra_imports = {
    "execute_update_user_v1": "from appverbo.use_cases.users.update_user import execute_update_user_v1",
    "execute_delete_user_v1": "from appverbo.use_cases.users.delete_user import execute_delete_user_v1",
    "execute_list_admin_users_v1": "from appverbo.use_cases.users.list_admin_users import execute_list_admin_users_v1",
    "execute_get_user_edit_data_v1": "from appverbo.use_cases.users.get_user_edit_data import execute_get_user_edit_data_v1",
    "execute_resolve_user_entity_v1": "from appverbo.use_cases.users.resolve_user_entity import execute_resolve_user_entity_v1",
    "execute_get_user_permissions_v1": "from appverbo.use_cases.users.user_permissions import execute_get_user_permissions_v1",
}

for name, import_line in extra_imports.items():
    if import_line not in init_content:
        init_content += "\n" + import_line

if "__all__" in init_content:
    for name in extra_imports:
        quoted = f'"{name}"'
        if quoted not in init_content:
            init_content = init_content.replace(
                "__all__ = [",
                "__all__ = [\n    " + quoted + ",",
                1,
            )

write_text_v1(init_path, init_content)


####################################################################################
# (3.4) VALIDAR QUE A RECURSÃO FOI REMOVIDA
####################################################################################

active_content = read_text_v1("templates/admin/users/active_users_card.html")
inactive_content = read_text_v1("templates/admin/users/inactive_users_card.html")

require_v1(
    'from "partials/admin_user_table_v1.html"' not in active_content,
    "ERRO: active_users_card ainda importa admin_user_table_v1.html.",
)

require_v1(
    'from "partials/admin_user_table_v1.html"' not in inactive_content,
    "ERRO: inactive_users_card ainda importa admin_user_table_v1.html.",
)

require_v1(
    "render_active_users_card_v1" in active_content,
    "ERRO: macro render_active_users_card_v1 não existe.",
)

require_v1(
    "render_inactive_users_card_v1" in inactive_content,
    "ERRO: macro render_inactive_users_card_v1 não existe.",
)

print("OK: recursão dos templates corrigida e compatibilidade reposta.")
