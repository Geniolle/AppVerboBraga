from __future__ import annotations

from pathlib import Path


ROOT = Path(".")


def write_text_v1(path: str, content: str) -> None:
    file_path = ROOT / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content.strip() + "\n", encoding="utf-8")


def read_text_v1(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


####################################################################################
# (3.1) PARTIAL REUTILIZÁVEL DA TABELA COM DELETE ROBUSTO
####################################################################################

write_text_v1(
    "templates/partials/admin_user_table_v1.html",
    r'''
{% macro render_admin_user_table_v1(arg1, arg2=None, arg3=None, allow_delete=False) %}
{% if arg1 is string %}
  {% set table_mode = arg1 %}
  {% set rows = arg2 %}
  {% set table_id = "inactive-users-table" if table_mode == "inactive" else "admin-users-table" %}
  {% set empty_message = "Sem utilizadores inativos." if table_mode == "inactive" else "Sem utilizadores ativos." %}
  {% set delete_enabled = allow_delete or table_mode == "inactive" %}
{% else %}
  {% set rows = arg1 %}
  {% set table_id = arg2 if arg2 else "admin-users-table" %}
  {% set empty_message = arg3 if arg3 else "Sem utilizadores." %}
  {% set delete_enabled = allow_delete or table_id == "inactive-users-table" %}
{% endif %}

{% if rows %}
<table id="{{ table_id }}">
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
    {% for row in rows %}
    <tr>
      <td>{{ row.id }}</td>
      <td>{{ row.full_name }}</td>
      <td>{{ row.login_email }}</td>
      <td>{{ row.primary_phone }}</td>
      <td>{{ row.entity_name }}</td>
      <td>{{ row.profile_name }}</td>
      <td>
        {% if row.account_status_is_active or row.account_status == "active" %}
        <span class="entity-status entity-status-active">
          {{ row.account_status_label if row.account_status_label is defined else "Ativo" }}
        </span>
        {% elif row.account_status_is_inactive or row.account_status == "inactive" %}
        <span class="entity-status entity-status-inactive">
          {{ row.account_status_label if row.account_status_label is defined else "Inativo" }}
        </span>
        {% else %}
        <span class="entity-status entity-status-inactive">
          {{ row.account_status_label if row.account_status_label is defined else row.account_status }}
        </span>
        {% endif %}
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

          {% if delete_enabled %}
          <form
            id="delete-user-form-{{ row.id }}"
            class="admin-user-delete-form-v1"
            method="post"
            action="/users/delete"
            style="display:inline-flex;margin:0;padding:0;"
            data-user-id="{{ row.id }}"
            data-user-email="{{ row.login_email }}"
          >
            <input type="hidden" name="user_id" value="{{ row.id }}">
            <button
              type="submit"
              class="table-icon-btn table-icon-btn-danger admin-user-delete-button-v1"
              title="Eliminar utilizador"
              aria-label="Eliminar utilizador {{ row.login_email }}"
            >&#128465;</button>
          </form>
          {% endif %}
        </div>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<div class="table-footer admin-status-table-footer-v1 admin-users-table-footer">
  <select aria-label="Entradas por página">
    <option selected>5</option>
  </select>
  <span>entradas por página</span>
  <div class="pagination">
    <button type="button" disabled>&lsaquo;</button>
    <button type="button" class="active">1</button>
    <button type="button" disabled>&rsaquo;</button>
  </div>
</div>
{% else %}
<p class="empty">{{ empty_message }}</p>
{% endif %}

<script>
(function () {
  if (window.APPVERBO_DELETE_USER_CLICK_V3) {
    return;
  }

  window.APPVERBO_DELETE_USER_CLICK_V3 = true;

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".admin-user-delete-button-v1");

    if (!button) {
      return;
    }

    var form = button.closest("form.admin-user-delete-form-v1");

    if (!form) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    var userEmail = form.getAttribute("data-user-email") || "";
    var message = "Tem a certeza que pretende eliminar este utilizador inativo?";

    if (userEmail) {
      message = "Tem a certeza que pretende eliminar este utilizador inativo?\n\n" + userEmail;
    }

    if (!window.confirm(message)) {
      return;
    }

    console.log("APPVERBO_DELETE_USER_CLICK_V3 submit", {
      userId: form.getAttribute("data-user-id"),
      userEmail: userEmail
    });

    form.submit();
  }, true);
})();
</script>
{% endmacro %}
''',
)


####################################################################################
# (3.2) CARD DE ATIVOS SEM ELIMINAR
####################################################################################

write_text_v1(
    "templates/admin/users/active_users_card.html",
    r'''
{% from "partials/admin_user_table_v1.html" import render_admin_user_table_v1 %}

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
  {{ render_admin_user_table_v1(
    user_rows,
    "admin-users-table",
    "Sem utilizadores ativos.",
    false
  ) }}
</section>
{% endmacro %}

{% if active_created_users is defined %}
  {{ render_active_users_card_v1(active_created_users) }}
{% endif %}
''',
)


####################################################################################
# (3.3) CARD DE INATIVOS COM ELIMINAR ATIVO
####################################################################################

write_text_v1(
    "templates/admin/users/inactive_users_card.html",
    r'''
{% from "partials/admin_user_table_v1.html" import render_admin_user_table_v1 %}

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
  {{ render_admin_user_table_v1(
    user_rows,
    "inactive-users-table",
    "Sem utilizadores inativos.",
    true
  ) }}
</section>
{% endmacro %}

{% if inactive_users is defined %}
  {{ render_inactive_users_card_v1(inactive_users) }}
{% endif %}
''',
)


####################################################################################
# (3.4) VALIDAÇÕES
####################################################################################

partial = read_text_v1("templates/partials/admin_user_table_v1.html")
active_card = read_text_v1("templates/admin/users/active_users_card.html")
inactive_card = read_text_v1("templates/admin/users/inactive_users_card.html")
delete_handler = read_text_v1("appverbo/routes/users/delete_handler.py")
delete_use_case = read_text_v1("appverbo/use_cases/users/delete_user.py")

require_v1("admin-user-delete-button-v1" in partial, "ERRO: botão eliminar não existe no partial.")
require_v1('action="/users/delete"' in partial, "ERRO: partial não aponta para /users/delete.")
require_v1("APPVERBO_DELETE_USER_CLICK_V3" in partial, "ERRO: JS V3 de delete não existe no partial.")
require_v1("true" in inactive_card and "inactive-users-table" in inactive_card, "ERRO: card de inativos não ativa delete.")
require_v1("false" in active_card and "admin-users-table" in active_card, "ERRO: card de ativos não está sem delete.")
require_v1("APPVERBO_DELETE_USER_ROUTE_V1" in delete_handler, "ERRO: delete_handler sem logs.")
require_v1("APPVERBO_DELETE_USER_USE_CASE_V1" in delete_use_case, "ERRO: delete use case sem logs.")

print("OK: botão eliminar reposto no partial reutilizável e ativo apenas nos inativos.")
