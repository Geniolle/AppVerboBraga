from __future__ import annotations

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
# (2) CRIAR CSS ISOLADO PARA A TABELA NATIVA DO UTILIZADOR
####################################################################################

css_path = ROOT / "static" / "css" / "modules" / "admin_user_shadow_table_v1.css"

css_content = """\
.admin-user-shadow-readonly-card-v1 {
  margin-bottom: 16px;
}

.admin-user-shadow-readonly-card-v1 .profile-card-header {
  margin-bottom: 16px;
}

.admin-user-shadow-toolbar-v1 {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  margin: 0 0 12px;
}

.admin-user-shadow-search-wrap-v1 {
  width: min(260px, 100%);
}

.admin-user-shadow-search-wrap-v1 .admin-table-search-input {
  width: 100%;
  min-height: 34px;
}

.admin-user-shadow-table-shell-v1 {
  width: 100%;
}

.admin-user-shadow-table-v1 {
  width: 100%;
  table-layout: auto;
}

.admin-user-shadow-table-v1 th,
.admin-user-shadow-table-v1 td {
  vertical-align: middle;
  white-space: nowrap;
}

.admin-user-shadow-table-v1 th:nth-child(2),
.admin-user-shadow-table-v1 td:nth-child(2),
.admin-user-shadow-table-v1 th:nth-child(3),
.admin-user-shadow-table-v1 td:nth-child(3) {
  white-space: normal;
}

.admin-user-shadow-actions-v1 {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  white-space: nowrap;
}

.admin-user-shadow-action-btn-v1 {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 28px;
  padding: 0 8px;
  border: 1px solid #c8d5ef;
  border-radius: 8px;
  background: #f3f7ff;
  color: #174ea6;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  text-decoration: none;
}

.admin-user-shadow-action-btn-v1:hover,
.admin-user-shadow-action-btn-v1:focus {
  background: #e8f0ff;
  border-color: #8fb3ef;
  color: #0d47a1;
  text-decoration: none;
}

.admin-user-shadow-status-v1 {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  padding: 3px 8px;
  border-radius: 999px;
  background: #e7f8ee;
  color: #16723a;
  border: 1px solid #a8e2bd;
  font-size: 11px;
  font-weight: 800;
  line-height: 1.2;
}

.admin-user-shadow-status-v1.status-pill-inactive,
.admin-user-shadow-status-v1.status-pill-inativo {
  background: #f2f4f7;
  color: #596579;
  border-color: #d5dbe7;
}

.admin-user-shadow-status-v1.status-pill-pending,
.admin-user-shadow-status-v1.status-pill-pendente {
  background: #fff7e6;
  color: #8a5a00;
  border-color: #f1d08a;
}

.admin-user-shadow-status-v1.status-pill-blocked,
.admin-user-shadow-status-v1.status-pill-bloqueado {
  background: #fdecec;
  color: #a61b1b;
  border-color: #efb4b4;
}

.admin-user-shadow-footer-v1 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.admin-user-shadow-page-size-label-v1 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #536176;
  font-size: 13px;
  white-space: nowrap;
}

.admin-user-shadow-page-size-label-v1 select {
  width: 72px;
  min-width: 72px;
  max-width: 72px;
  height: 34px;
  padding: 4px 8px;
  border: 1px solid #cdd7ea;
  border-radius: 8px;
  background: #ffffff;
  color: #172033;
}

.admin-user-shadow-pagination-v1 {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: #536176;
  font-size: 13px;
  margin-left: auto;
}

.admin-user-shadow-pagination-actions-v1 {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.admin-user-shadow-pagination-actions-v1 button,
.admin-user-shadow-pagination-actions-v1 span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
}

.admin-user-shadow-pagination-actions-v1 button {
  border: 1px solid #d7e0f0;
  background: #ffffff;
  color: #2c4a73;
  cursor: pointer;
}

.admin-user-shadow-pagination-actions-v1 button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.admin-user-shadow-pagination-actions-v1 span {
  border: 1px solid #1f5fbf;
  background: #1f5fbf;
  color: #ffffff;
}

@media (max-width: 900px) {
  .admin-user-shadow-toolbar-v1 {
    justify-content: stretch;
  }

  .admin-user-shadow-search-wrap-v1 {
    width: 100%;
  }

  .admin-user-shadow-footer-v1 {
    align-items: flex-start;
    flex-direction: column;
  }

  .admin-user-shadow-pagination-v1 {
    margin-left: 0;
  }
}
"""

write_text(css_path, css_content)


####################################################################################
# (3) ATUALIZAR PARTIAL COM ESTRUTURA DE LAYOUT CORRETA
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"

partial_content = '''\
{% macro render_admin_user_shadow_cell_v4(row, column) %}
  {% set value = row.get(column.source, "-") %}
  {% if column.source == "status_label" %}
    <span class="admin-user-shadow-status-v1 status-pill-{{ row.get('status', '') }}">{{ value }}</span>
  {% else %}
    {{ value }}
  {% endif %}
{% endmacro %}

{% macro render_admin_user_shadow_actions_v3(row) %}
  {% set user_id = row.get('id', '') %}
  {% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_readonly=1&readonly=1&mode=view&target=edit-user-card#edit-user-card" %}
  {% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&target=edit-user-card#edit-user-card" %}

  <div class="admin-user-shadow-actions-v1" role="group" aria-label="Ações do utilizador">
    <a
      class="admin-user-shadow-action-btn-v1 admin-user-shadow-action-view-v1"
      href="{{ view_url }}"
      title="Visualizar utilizador"
      aria-label="Visualizar utilizador"
    >Ver</a>
    <a
      class="admin-user-shadow-action-btn-v1 admin-user-shadow-action-edit-v1"
      href="{{ edit_url }}"
      title="Editar utilizador"
      aria-label="Editar utilizador"
    >Editar</a>
  </div>
{% endmacro %}

{% macro render_admin_user_shadow_table_v4(table_key, rows, columns) %}
<div
  class="admin-user-shadow-table-shell-v1"
  data-admin-user-shadow-table
  data-admin-user-shadow-table-key="{{ table_key }}"
>
  <div class="admin-user-shadow-toolbar-v1">
    <div class="admin-user-shadow-search-wrap-v1">
      <label class="sr-only" for="admin-user-shadow-search-{{ table_key }}">Procurar</label>
      <input
        id="admin-user-shadow-search-{{ table_key }}"
        class="admin-table-search-input"
        type="search"
        placeholder="Procurar"
        data-admin-user-shadow-search
      >
    </div>
  </div>

  <div class="admin-table-wrap">
    <table class="admin-subprocess-table-v1 admin-user-shadow-table-v1">
      <thead>
        <tr>
          {% for column in columns %}
          <th>{{ column.label }}</th>
          {% endfor %}
          <th>AÇÕES</th>
        </tr>
      </thead>
      <tbody>
        {% for row in rows %}
        <tr data-admin-user-shadow-row="{{ row.get('id', '') }}">
          {% for column in columns %}
          <td>{{ render_admin_user_shadow_cell_v4(row, column) }}</td>
          {% endfor %}
          <td>{{ render_admin_user_shadow_actions_v3(row) }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="admin-user-shadow-footer-v1">
    <label class="admin-user-shadow-page-size-label-v1">
      <select data-admin-user-shadow-page-size>
        <option value="5" selected>5</option>
        <option value="10">10</option>
        <option value="25">25</option>
        <option value="50">50</option>
      </select>
      entradas por página
    </label>

    <div class="admin-user-shadow-pagination-v1">
      <span data-admin-user-shadow-summary></span>
      <div class="admin-user-shadow-pagination-actions-v1">
        <button type="button" data-admin-user-shadow-prev aria-label="Página anterior">‹</button>
        <span data-admin-user-shadow-current-page>1</span>
        <button type="button" data-admin-user-shadow-next aria-label="Próxima página">›</button>
      </div>
    </div>
  </div>
</div>
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v4(state) %}
<link rel="stylesheet" href="/static/css/modules/admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v4">

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
        Validação do novo processo único. Este bloco usa a leitura nativa com pesquisa, paginação e ações legadas.
      </p>
    </div>
  </div>

  <div class="admin-subsection">
    <h3>{{ state.config.active_title }}</h3>
    <p class="muted">Total: {{ state.active_rows|length }}</p>

    {% if state.active_rows %}
      {{ render_admin_user_shadow_table_v4("active", state.active_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores ativos no processo nativo.</p>
    {% endif %}
  </div>

  <div class="admin-subsection">
    <h3>{{ state.config.inactive_title }}</h3>

    {% if state.inactive_rows %}
      {{ render_admin_user_shadow_table_v4("inactive", state.inactive_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores inativos, pendentes ou bloqueados no processo nativo.</p>
    {% endif %}
  </div>

  <script src="/static/js/modules/admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v1" defer></script>
</section>
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v3(state) %}
  {{ render_admin_user_shadow_readonly_v4(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v2(state) %}
  {{ render_admin_user_shadow_readonly_v4(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v1(state) %}
  {{ render_admin_user_shadow_readonly_v4(state) }}
{% endmacro %}
'''

write_text(partial_path, partial_content)


####################################################################################
# (4) ATUALIZAR NEW_USER.HTML PARA MACRO V4
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v3 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v4 %}',
)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v2 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v4 %}',
)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v1 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v4 %}',
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v3(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v4(admin_subprocess_shadow_state)",
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v2(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v4(admin_subprocess_shadow_state)",
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v1(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v4(admin_subprocess_shadow_state)",
)

if "render_admin_user_shadow_readonly_v4(admin_subprocess_shadow_state)" not in template_content:
    raise RuntimeError("Render V4 do Utilizador shadow não encontrado no new_user.html")

write_text(template_path, template_content)


####################################################################################
# (5) ATUALIZAR VALIDAÇÃO JINJA
####################################################################################

jinja_check_path = ROOT / "scripts" / "check_template_jinja_utilizador_shadow_v1.py"

jinja_check_content = '''\
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))

env.get_template("new_user.html")
env.get_template("partials/admin_user_shadow_readonly_v1.html")

partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(
    encoding="utf-8"
)

css_source = (root / "static" / "css" / "modules" / "admin_user_shadow_table_v1.css").read_text(
    encoding="utf-8"
)

required_partial_tokens = (
    "render_admin_user_shadow_readonly_v4",
    "render_admin_user_shadow_table_v4",
    "render_admin_user_shadow_actions_v3",
    "admin-user-shadow-toolbar-v1",
    "admin-user-shadow-footer-v1",
    "admin-user-shadow-page-size-label-v1",
    "admin_user_shadow_table_v1.css",
)

required_css_tokens = (
    ".admin-user-shadow-toolbar-v1",
    ".admin-user-shadow-search-wrap-v1",
    ".admin-user-shadow-footer-v1",
    ".admin-user-shadow-page-size-label-v1 select",
    ".admin-user-shadow-pagination-v1",
    ".admin-user-shadow-action-btn-v1",
)

missing_partial_tokens = [
    token
    for token in required_partial_tokens
    if token not in partial_source
]

missing_css_tokens = [
    token
    for token in required_css_tokens
    if token not in css_source
]

if missing_partial_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

if missing_css_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no CSS do Utilizador: "
        + ", ".join(missing_css_tokens)
    )

print("OK: templates Jinja carregados com sucesso.")
print("OK: layout nativo do Utilizador validado.")
'''

write_text(jinja_check_path, jinja_check_content)


####################################################################################
# (6) RESULTADO
####################################################################################

print("OK: layout do bloco nativo do Utilizador corrigido.")
print("OK: CSS isolado criado/atualizado.")
print("OK: new_user.html atualizado para macro render_admin_user_shadow_readonly_v4.")
