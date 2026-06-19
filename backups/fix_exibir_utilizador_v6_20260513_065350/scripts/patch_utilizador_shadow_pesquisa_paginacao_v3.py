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
# (2) CRIAR JAVASCRIPT ISOLADO DA TABELA NATIVA DO UTILIZADOR
####################################################################################

js_path = ROOT / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js?v=20260513-utilizador-view-toggle-v5"

js_content = """\
(function () {
  "use strict";

  function normalizeText(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\\u0300-\\u036f]/g, "");
  }

  function resolvePageSize(tableRoot) {
    const pageSizeSelect = tableRoot.querySelector("[data-admin-user-shadow-page-size]");
    const parsedValue = Number.parseInt(pageSizeSelect ? pageSizeSelect.value : "5", 10);

    if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
      return 5;
    }

    return parsedValue;
  }

  function updateTable(tableRoot) {
    const searchInput = tableRoot.querySelector("[data-admin-user-shadow-search]");
    const rows = Array.from(tableRoot.querySelectorAll("[data-admin-user-shadow-row]"));
    const summary = tableRoot.querySelector("[data-admin-user-shadow-summary]");
    const currentPageLabel = tableRoot.querySelector("[data-admin-user-shadow-current-page]");
    const prevButton = tableRoot.querySelector("[data-admin-user-shadow-prev]");
    const nextButton = tableRoot.querySelector("[data-admin-user-shadow-next]");

    const query = normalizeText(searchInput ? searchInput.value : "");
    const pageSize = resolvePageSize(tableRoot);
    let currentPage = Number.parseInt(tableRoot.dataset.adminUserShadowPage || "1", 10);

    if (!Number.isFinite(currentPage) || currentPage <= 0) {
      currentPage = 1;
    }

    const matchingRows = rows.filter(function (row) {
      const rowText = normalizeText(row.textContent);
      return !query || rowText.includes(query);
    });

    const totalRows = matchingRows.length;
    const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));

    if (currentPage > totalPages) {
      currentPage = totalPages;
    }

    tableRoot.dataset.adminUserShadowPage = String(currentPage);

    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;

    rows.forEach(function (row) {
      row.hidden = true;
    });

    matchingRows.slice(startIndex, endIndex).forEach(function (row) {
      row.hidden = false;
    });

    if (summary) {
      if (totalRows === 0) {
        summary.textContent = "Sem resultados";
      } else {
        const visibleStart = startIndex + 1;
        const visibleEnd = Math.min(endIndex, totalRows);
        summary.textContent = "A mostrar " + visibleStart + "-" + visibleEnd + " de " + totalRows;
      }
    }

    if (currentPageLabel) {
      currentPageLabel.textContent = String(currentPage);
    }

    if (prevButton) {
      prevButton.disabled = currentPage <= 1;
    }

    if (nextButton) {
      nextButton.disabled = currentPage >= totalPages;
    }
  }

  function initTable(tableRoot) {
    if (!tableRoot || tableRoot.dataset.adminUserShadowReady === "1") {
      return;
    }

    tableRoot.dataset.adminUserShadowReady = "1";
    tableRoot.dataset.adminUserShadowPage = "1";

    const searchInput = tableRoot.querySelector("[data-admin-user-shadow-search]");
    const pageSizeSelect = tableRoot.querySelector("[data-admin-user-shadow-page-size]");
    const prevButton = tableRoot.querySelector("[data-admin-user-shadow-prev]");
    const nextButton = tableRoot.querySelector("[data-admin-user-shadow-next]");

    if (searchInput) {
      searchInput.addEventListener("input", function () {
        tableRoot.dataset.adminUserShadowPage = "1";
        updateTable(tableRoot);
      });
    }

    if (pageSizeSelect) {
      pageSizeSelect.addEventListener("change", function () {
        tableRoot.dataset.adminUserShadowPage = "1";
        updateTable(tableRoot);
      });
    }

    if (prevButton) {
      prevButton.addEventListener("click", function () {
        const currentPage = Number.parseInt(tableRoot.dataset.adminUserShadowPage || "1", 10);
        tableRoot.dataset.adminUserShadowPage = String(Math.max(1, currentPage - 1));
        updateTable(tableRoot);
      });
    }

    if (nextButton) {
      nextButton.addEventListener("click", function () {
        const currentPage = Number.parseInt(tableRoot.dataset.adminUserShadowPage || "1", 10);
        tableRoot.dataset.adminUserShadowPage = String(currentPage + 1);
        updateTable(tableRoot);
      });
    }

    updateTable(tableRoot);
  }

  function initAllTables() {
    document
      .querySelectorAll("[data-admin-user-shadow-table]")
      .forEach(initTable);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAllTables);
  } else {
    initAllTables();
  }
})();
"""

write_text(js_path, js_content)


####################################################################################
# (3) ATUALIZAR PARTIAL COM PESQUISA, ENTRADAS E PAGINAÇÃO
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"

partial_content = '''\
{% macro render_admin_user_shadow_cell_v3(row, column) %}
  {% set value = row.get(column.source, "-") %}
  {% if column.source == "status_label" %}
    <span class="status-pill status-pill-{{ row.get('status', '') }}">{{ value }}</span>
  {% else %}
    {{ value }}
  {% endif %}
{% endmacro %}

{% macro render_admin_user_shadow_actions_v2(row) %}
  {% set user_id = row.get('id', '') %}
  {% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_readonly=1&readonly=1&mode=view&target=edit-user-card#edit-user-card" %}
  {% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&target=edit-user-card#edit-user-card" %}

  <div class="admin-user-shadow-actions-v1" role="group" aria-label="Ações do utilizador">
    <a
      class="action-icon-btn action-icon-btn-view"
      href="{{ view_url }}"
      title="Visualizar utilizador"
      aria-label="Visualizar utilizador"
    >Ver</a>
    <a
      class="action-icon-btn action-icon-btn-edit"
      href="{{ edit_url }}"
      title="Editar utilizador"
      aria-label="Editar utilizador"
    >Editar</a>
  </div>
{% endmacro %}

{% macro render_admin_user_shadow_table_v3(table_key, rows, columns) %}
<div
  class="admin-user-shadow-table-shell-v1"
  data-admin-user-shadow-table
  data-admin-user-shadow-table-key="{{ table_key }}"
>
  <div class="admin-user-shadow-toolbar-v1">
    <label class="sr-only" for="admin-user-shadow-search-{{ table_key }}">Procurar</label>
    <input
      id="admin-user-shadow-search-{{ table_key }}"
      class="admin-table-search-input"
      type="search"
      placeholder="Procurar"
      data-admin-user-shadow-search
    >

    <label class="admin-user-shadow-page-size-label-v1">
      <select data-admin-user-shadow-page-size>
        <option value="5" selected>5</option>
        <option value="10">10</option>
        <option value="25">25</option>
        <option value="50">50</option>
      </select>
      entradas por página
    </label>
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
          <td>{{ render_admin_user_shadow_cell_v3(row, column) }}</td>
          {% endfor %}
          <td>{{ render_admin_user_shadow_actions_v2(row) }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="admin-user-shadow-pagination-v1">
    <span data-admin-user-shadow-summary></span>
    <div class="admin-user-shadow-pagination-actions-v1">
      <button type="button" data-admin-user-shadow-prev aria-label="Página anterior">‹</button>
      <span data-admin-user-shadow-current-page>1</span>
      <button type="button" data-admin-user-shadow-next aria-label="Próxima página">›</button>
    </div>
  </div>
</div>
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v3(state) %}
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
      {{ render_admin_user_shadow_table_v3("active", state.active_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores ativos no processo nativo.</p>
    {% endif %}
  </div>

  <div class="admin-subsection">
    <h3>{{ state.config.inactive_title }}</h3>

    {% if state.inactive_rows %}
      {{ render_admin_user_shadow_table_v3("inactive", state.inactive_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores inativos, pendentes ou bloqueados no processo nativo.</p>
    {% endif %}
  </div>

  <script src="/static/js/modules/$120260513-utilizador-view-toggle-v5" defer></script>
</section>
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v2(state) %}
  {{ render_admin_user_shadow_readonly_v3(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v1(state) %}
  {{ render_admin_user_shadow_readonly_v3(state) }}
{% endmacro %}
'''

write_text(partial_path, partial_content)


####################################################################################
# (4) ATUALIZAR NEW_USER.HTML PARA MACRO V3
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v2 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v3 %}',
)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v1 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v3 %}',
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v2(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v3(admin_subprocess_shadow_state)",
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v1(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v3(admin_subprocess_shadow_state)",
)

if "render_admin_user_shadow_readonly_v3(admin_subprocess_shadow_state)" not in template_content:
    raise RuntimeError("Render V3 do Utilizador shadow não encontrado no new_user.html")

write_text(template_path, template_content)


####################################################################################
# (5) ATUALIZAR SCRIPT DE VALIDAÇÃO JINJA
####################################################################################

jinja_check_path = ROOT / "scripts" / "check_template_jinja_utilizador_shadow_v1.py"

jinja_check_content = '''\
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))

env.get_template("new_user.html")
partial = env.get_template("partials/admin_user_shadow_readonly_v1.html")

partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(
    encoding="utf-8"
)

required_tokens = (
    "render_admin_user_shadow_readonly_v3",
    "render_admin_user_shadow_table_v3",
    "render_admin_user_shadow_actions_v2",
    "data-admin-user-shadow-table",
    "data-admin-user-shadow-search",
    "data-admin-user-shadow-page-size",
    "data-admin-user-shadow-prev",
    "data-admin-user-shadow-next",
    "admin_user_shadow_table_v1.js?v=20260513-utilizador-view-toggle-v5",
)

missing_tokens = [
    token
    for token in required_tokens
    if token not in partial_source
]

if missing_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial do Utilizador: "
        + ", ".join(missing_tokens)
    )

print("OK: templates Jinja carregados com sucesso.")
print("OK: pesquisa e paginação nativas do Utilizador validadas.")
'''

write_text(jinja_check_path, jinja_check_content)


####################################################################################
# (6) RESULTADO
####################################################################################

print("OK: pesquisa e paginação adicionadas ao bloco nativo do Utilizador.")
print("OK: new_user.html atualizado para macro render_admin_user_shadow_readonly_v3.")
print("OK: JavaScript isolado criado em static/js/modules/admin_user_shadow_table_v1.js?v=20260513-utilizador-view-toggle-v5.")
