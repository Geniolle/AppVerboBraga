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
# (3.1) REESCREVER PARTIAL INATIVOS COM DELETE EXPLÍCITO + JS CAPTURE
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

<script>
(function () {
  if (window.APPVERBO_DELETE_USER_CLICK_V2) {
    return;
  }

  window.APPVERBO_DELETE_USER_CLICK_V2 = true;

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

    console.log("APPVERBO_DELETE_USER_CLICK_V2 submit", {
      userId: form.getAttribute("data-user-id"),
      userEmail: userEmail
    });

    form.submit();
  }, true);
})();
</script>
{% endmacro %}

{% if inactive_users is defined %}
  {{ render_inactive_users_card_v1(inactive_users) }}
{% endif %}
''',
)


####################################################################################
# (3.2) VALIDAR QUE OS LOGS DO BACKEND EXISTEM
####################################################################################

delete_handler = read_text_v1("appverbo/routes/users/delete_handler.py")
delete_use_case = read_text_v1("appverbo/use_cases/users/delete_user.py")
inactive_template = read_text_v1("templates/admin/users/inactive_users_card.html")

require_v1("APPVERBO_DELETE_USER_ROUTE_V1" in delete_handler, "ERRO: delete_handler sem logs APPVERBO_DELETE_USER_ROUTE_V1.")
require_v1("APPVERBO_DELETE_USER_USE_CASE_V1" in delete_use_case, "ERRO: delete_user sem logs APPVERBO_DELETE_USER_USE_CASE_V1.")
require_v1("APPVERBO_DELETE_USER_CLICK_V2" in inactive_template, "ERRO: JS de click delete não foi aplicado.")
require_v1("admin-user-delete-form-v1" in inactive_template, "ERRO: form delete não foi aplicado.")
require_v1('action="/users/delete"' in inactive_template, "ERRO: action /users/delete não foi aplicada.")
require_v1('method="post"' in inactive_template, "ERRO: method post não foi aplicado.")

print("OK: clique de eliminação reforçado no frontend.")
