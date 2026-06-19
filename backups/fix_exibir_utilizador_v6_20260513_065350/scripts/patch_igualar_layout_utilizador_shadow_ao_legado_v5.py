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
# (2) CSS ISOLADO - AJUSTAR SOMENTE O BLOCO NATIVO
####################################################################################

css_path = ROOT / "static" / "css" / "modules" / "admin_user_shadow_table_v1.css"

css_content = """\
.admin-user-shadow-readonly-card-v1 {
  margin-bottom: 16px;
}

.admin-user-shadow-readonly-card-v1 .sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  white-space: nowrap;
  border: 0;
  clip: rect(0, 0, 0, 0);
}

.admin-user-shadow-readonly-card-v1 .profile-card-header {
  margin-bottom: 16px;
}

.admin-user-shadow-table-shell-v1 {
  width: 100%;
}

.admin-user-shadow-toolbar-v1 {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin: 0 0 12px;
}

.admin-user-shadow-search-wrap-v1 {
  width: min(220px, 100%);
  margin-left: auto;
}

.admin-user-shadow-search-wrap-v1 .admin-table-search-input {
  width: 100%;
  min-height: 34px;
  padding: 7px 14px;
  border: 1px solid #bfcce4;
  border-radius: 999px;
  background: #ffffff;
  color: #172033;
  font-size: 13px;
  line-height: 1.2;
}

.admin-user-shadow-search-wrap-v1 .admin-table-search-input::placeholder {
  color: #6f7c91;
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

.admin-user-shadow-table-v1 .table-actions {
  justify-content: flex-end;
}

.admin-user-shadow-table-v1 .table-icon-btn {
  text-decoration: none;
}

.admin-user-shadow-footer-v1 {
  margin-top: 10px;
}

.admin-user-shadow-footer-v1.table-footer.admin-status-table-footer-v1 {
  display: flex;
  align-items: center;
  gap: 8px;
}

.admin-user-shadow-footer-v1 select {
  width: 64px;
  min-width: 64px;
  height: 34px;
}

.admin-user-shadow-footer-v1 .pagination {
  margin-left: auto;
}

.admin-user-shadow-footer-v1 .pagination button.active {
  pointer-events: none;
}

@media (max-width: 900px) {
  .admin-user-shadow-toolbar-v1 {
    justify-content: stretch;
  }

  .admin-user-shadow-search-wrap-v1 {
    width: 100%;
  }

  .admin-user-shadow-footer-v1.table-footer.admin-status-table-footer-v1 {
    flex-wrap: wrap;
  }

  .admin-user-shadow-footer-v1 .pagination {
    margin-left: 0;
  }
}
"""

write_text(css_path, css_content)


####################################################################################
# (3) PARTIAL - USAR CLASSES E ÍCONES DO LEGADO
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"

partial_content = '''\
{% macro render_admin_user_shadow_cell_v5(row, column) %}
  {% set value = row.get(column.source, "-") %}
  {% if column.source == "status_label" %}
    {% if row.get('status') == "active" or row.get('status') == "ativo" %}
      <span class="entity-status entity-status-active">{{ value }}</span>
    {% else %}
      <span class="entity-status entity-status-inactive">{{ value }}</span>
    {% endif %}
  {% else %}
    {{ value }}
  {% endif %}
{% endmacro %}

{% macro render_admin_user_shadow_actions_v4(row) %}
  {% set user_id = row.get('id', '') %}
  {% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_view=1#edit-user-card" %}
  {% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "#edit-user-card" %}

  <div class="table-actions">
    <a
      class="table-icon-btn"
      href="{{ view_url }}"
      title="Exibir utilizador"
      aria-label="Exibir utilizador"
    >
      &#128065;
    </a>
    <a
      class="table-icon-btn"
      href="{{ edit_url }}"
      title="Modificar utilizador"
      aria-label="Modificar utilizador"
    >
      &#9998;
    </a>
  </div>
{% endmacro %}

{% macro render_admin_user_shadow_table_v5(table_key, rows, columns) %}
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
          <td>{{ render_admin_user_shadow_cell_v5(row, column) }}</td>
          {% endfor %}
          <td>{{ render_admin_user_shadow_actions_v4(row) }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="table-footer admin-status-table-footer-v1 admin-user-shadow-footer-v1">
    <select aria-label="Entradas por página" data-admin-user-shadow-page-size>
      <option value="5" selected>5</option>
      <option value="10">10</option>
      <option value="25">25</option>
      <option value="50">50</option>
    </select>
    <span>entradas por página</span>
    <div class="pagination" data-admin-user-shadow-pagination>
      <button type="button" data-admin-user-shadow-prev aria-label="Página anterior">&lsaquo;</button>
      <button type="button" class="active" data-admin-user-shadow-current-page>1</button>
      <button type="button" data-admin-user-shadow-next aria-label="Próxima página">&rsaquo;</button>
    </div>
  </div>
</div>
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v5(state) %}
<link rel="stylesheet" href="/static/css/modules/admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v5">

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
      {{ render_admin_user_shadow_table_v5("active", state.active_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores ativos no processo nativo.</p>
    {% endif %}
  </div>

  <div class="admin-subsection">
    <h3>{{ state.config.inactive_title }}</h3>

    {% if state.inactive_rows %}
      {{ render_admin_user_shadow_table_v5("inactive", state.inactive_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores inativos, pendentes ou bloqueados no processo nativo.</p>
    {% endif %}
  </div>

  <script src="/static/js/modules/$120260513-utilizador-view-toggle-v5" defer></script>
</section>
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v4(state) %}
  {{ render_admin_user_shadow_readonly_v5(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v3(state) %}
  {{ render_admin_user_shadow_readonly_v5(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v2(state) %}
  {{ render_admin_user_shadow_readonly_v5(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v1(state) %}
  {{ render_admin_user_shadow_readonly_v5(state) }}
{% endmacro %}
'''

write_text(partial_path, partial_content)


####################################################################################
# (4) AJUSTAR JS PARA NÃO EXIGIR RESUMO VISÍVEL
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
# (5) ATUALIZAR NEW_USER.HTML PARA MACRO V5
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v4 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v5 %}',
)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v3 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v5 %}',
)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v2 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v5 %}',
)

template_content = template_content.replace(
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v1 %}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v5 %}',
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v4(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v5(admin_subprocess_shadow_state)",
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v3(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v5(admin_subprocess_shadow_state)",
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v2(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v5(admin_subprocess_shadow_state)",
)

template_content = template_content.replace(
    "render_admin_user_shadow_readonly_v1(admin_subprocess_shadow_state)",
    "render_admin_user_shadow_readonly_v5(admin_subprocess_shadow_state)",
)

if "render_admin_user_shadow_readonly_v5(admin_subprocess_shadow_state)" not in template_content:
    raise RuntimeError("Render V5 do Utilizador shadow não encontrado no new_user.html")

write_text(template_path, template_content)


####################################################################################
# (6) ATUALIZAR VALIDAÇÃO JINJA
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
    "render_admin_user_shadow_readonly_v5",
    "render_admin_user_shadow_table_v5",
    "render_admin_user_shadow_actions_v4",
    "table-actions",
    "table-icon-btn",
    "entity-status entity-status-active",
    "table-footer admin-status-table-footer-v1",
    "pagination",
)

required_css_tokens = (
    ".admin-user-shadow-readonly-card-v1 .sr-only",
    ".admin-user-shadow-toolbar-v1",
    ".admin-user-shadow-search-wrap-v1",
    ".admin-user-shadow-footer-v1.table-footer.admin-status-table-footer-v1",
    ".admin-user-shadow-table-v1 .table-actions",
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
print("OK: layout nativo do Utilizador igualado ao legado.")
'''

write_text(jinja_check_path, jinja_check_content)


####################################################################################
# (7) RESULTADO
####################################################################################

print("OK: layout do bloco nativo do Utilizador igualado ao legado.")
print("OK: ações agora usam table-actions/table-icon-btn.")
print("OK: estado agora usa entity-status.")
print("OK: rodapé agora usa table-footer/admin-status-table-footer-v1/pagination.")
