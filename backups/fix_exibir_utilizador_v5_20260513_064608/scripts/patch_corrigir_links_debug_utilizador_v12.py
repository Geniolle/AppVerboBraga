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


def replace_marked_block(
    content: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
) -> tuple[str, bool]:
    if start_marker not in content:
        return content, False

    start_index = content.index(start_marker)
    end_index = content.index(end_marker, start_index)
    line_end_index = content.find("\n", end_index)

    if line_end_index == -1:
        line_end_index = len(content)
    else:
        line_end_index += 1

    return content[:start_index] + replacement + content[line_end_index:], True


####################################################################################
# (2) CORRIGIR PAGE_HANDLER COMO ORQUESTRADOR DO UTILIZADOR
####################################################################################

page_handler_path = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
page_content = read_text(page_handler_path)

target_guard_block = '''\
    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_START
    if (
        resolved_menu == "administrativo"
        and resolved_admin_tab == "utilizador"
        and parsed_user_edit_id is not None
    ):
        initial_menu_target = "#edit-user-card"
        initial_dynamic_process_section = ""
    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_END

'''

for old_start, old_end in (
    (
        "    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V1_START",
        "    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V1_END",
    ),
    (
        "    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_START",
        "    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_END",
    ),
):
    page_content, replaced = replace_marked_block(
        page_content,
        old_start,
        old_end,
        target_guard_block,
    )

    if replaced:
        break
else:
    anchor = '''\
    if clean_target_from_query:
        initial_menu_target = clean_target_from_query

'''

    if anchor not in page_content:
        raise RuntimeError("Ponto seguro não encontrado para inserir target guard no page_handler.py.")

    page_content = page_content.replace(anchor, anchor + target_guard_block, 1)


debug_block = '''\
    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V2_START
    if (
        resolved_menu == "administrativo"
        and resolved_admin_tab == "utilizador"
        and parsed_user_edit_id is not None
    ):
        import json as _appverbo_json

        print(
            "APPVERBO_UTILIZADOR_ACTION_DEBUG_V1 "
            + _appverbo_json.dumps(
                {
                    "menu": resolved_menu,
                    "admin_tab": resolved_admin_tab,
                    "raw_user_edit_id": user_edit_id,
                    "parsed_user_edit_id": parsed_user_edit_id,
                    "user_view": user_view,
                    "user_readonly_mode": user_readonly_mode,
                    "has_user_edit_data": user_edit_data is not None,
                    "user_edit_data_type": type(user_edit_data).__name__ if user_edit_data is not None else "",
                    "initial_menu_target": initial_menu_target,
                    "initial_dynamic_process_section": initial_dynamic_process_section,
                    "clean_target_from_query": clean_target_from_query,
                    "request_url": str(request.url),
                },
                ensure_ascii=False,
                default=str,
            ),
            flush=True,
        )
    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V2_END

'''

for old_start, old_end in (
    (
        "    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_START",
        "    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V1_END",
    ),
    (
        "    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V2_START",
        "    # APPVERBO_UTILIZADOR_ACTION_DEBUG_V2_END",
    ),
):
    page_content, replaced = replace_marked_block(
        page_content,
        old_start,
        old_end,
        debug_block,
    )

    if replaced:
        break
else:
    anchors = (
        "    context = {",
        "    template_context = {",
        "    return templates.TemplateResponse(",
        "    return TemplateResponse(",
    )

    for anchor in anchors:
        if anchor in page_content:
            page_content = page_content.replace(anchor, debug_block + anchor, 1)
            break
    else:
        raise RuntimeError("Ponto seguro não encontrado para inserir debug no page_handler.py.")

if "APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_START" not in page_content:
    raise RuntimeError("Target guard V2 não foi aplicado.")

if "APPVERBO_UTILIZADOR_ACTION_DEBUG_V2_START" not in page_content:
    raise RuntimeError("Debug V2 não foi aplicado.")

if "import json as _appverbo_json" not in page_content:
    raise RuntimeError("Import local de json não foi aplicado.")

write_text(page_handler_path, page_content)


####################################################################################
# (3) RECRIAR PARTIAL NATIVO COM LINKS HTML REAIS
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"

partial_content = '''\
{% macro render_admin_user_shadow_cell_v12(row, column) %}
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

{% macro render_admin_user_shadow_actions_v12(row) %}
  {% set user_id = row.get('id', '') %}
  {% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_view=1&target=edit-user-card#edit-user-card" %}
  {% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&target=edit-user-card#edit-user-card" %}

  <div class="table-actions">
    <a
      class="table-icon-btn"
      href="{{ view_url }}"
      title="Exibir utilizador"
      aria-label="Exibir utilizador"
      data-admin-user-shadow-real-link="view"
    >
      &#128065;
    </a>
    <a
      class="table-icon-btn"
      href="{{ edit_url }}"
      title="Modificar utilizador"
      aria-label="Modificar utilizador"
      data-admin-user-shadow-real-link="edit"
    >
      &#9998;
    </a>
  </div>
{% endmacro %}

{% macro render_admin_user_shadow_table_v12(table_key, rows, columns) %}
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
          <td>{{ render_admin_user_shadow_cell_v12(row, column) }}</td>
          {% endfor %}
          <td>{{ render_admin_user_shadow_actions_v12(row) }}</td>
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

{% macro render_admin_user_shadow_readonly_v12(state) %}
<link rel="stylesheet" href="/static/css/modules/admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v12">

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
      {{ render_admin_user_shadow_table_v12("active", state.active_rows, state.config.columns) }}
    {% else %}
      <p class="empty">Sem utilizadores ativos no processo nativo.</p>
    {% endif %}
  </div>
</section>

<section
  id="admin-user-shadow-inactive-card"
  class="card admin-user-shadow-readonly-card-v1 admin-user-shadow-inactive-card-v1"
  data-menu-scope="administrativo"
  data-admin-subprocess-shadow="utilizador-inactive"
>
  <h3>{{ state.config.inactive_title }}</h3>

  {% if state.inactive_rows %}
    {{ render_admin_user_shadow_table_v12("inactive", state.inactive_rows, state.config.columns) }}
  {% else %}
    <p class="empty">Sem utilizadores inativos, pendentes ou bloqueados no processo nativo.</p>
  {% endif %}

  <script src="/static/js/modules/admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v12" defer></script>
</section>
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v11(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v10(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v9(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v8(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v7(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v6(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v5(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v4(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v3(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v2(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}

{% macro render_admin_user_shadow_readonly_v1(state) %}
  {{ render_admin_user_shadow_readonly_v12(state) }}
{% endmacro %}
'''

write_text(partial_path, partial_content)


####################################################################################
# (4) ATUALIZAR NEW_USER.HTML PARA USAR MACRO V12
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

template_content = re.sub(
    r'{%\s*from\s+"partials/admin_user_shadow_readonly_v1.html"\s+import\s+render_admin_user_shadow_readonly_v\d+\s*%}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v12 %}',
    template_content,
)

template_content = re.sub(
    r'render_admin_user_shadow_readonly_v\d+\(admin_subprocess_shadow_state\)',
    'render_admin_user_shadow_readonly_v12(admin_subprocess_shadow_state)',
    template_content,
)

if "render_admin_user_shadow_readonly_v12(admin_subprocess_shadow_state)" not in template_content:
    raise RuntimeError("Render V12 não encontrado no new_user.html.")

write_text(template_path, template_content)


####################################################################################
# (5) REESCREVER JS SEM INTERCEPTAR OLHO/LÁPIS
####################################################################################

js_path = ROOT / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js"

js_content = '''\
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
      currentPageLabel.classList.add("active");
      currentPageLabel.disabled = true;
    }

    if (prevButton) {
      prevButton.classList.remove("active");
      prevButton.disabled = currentPage <= 1;
    }

    if (nextButton) {
      nextButton.classList.remove("active");
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

  function findCreateActionsCard() {
    const cards = Array.from(document.querySelectorAll(".card"));

    return cards.find(function (card) {
      const text = normalizeText(card.textContent);
      return text.includes("criar utilizador") && text.includes("gerar link");
    }) || null;
  }

  function moveCreateActionsCardToTop() {
    const params = new URLSearchParams(window.location.search);

    if (params.get("menu") !== "administrativo" || params.get("admin_tab") !== "utilizador") {
      return;
    }

    const shadowCard = document.getElementById("admin-user-shadow-readonly-card");
    const actionsCard = findCreateActionsCard();

    if (!shadowCard || !actionsCard || actionsCard === shadowCard) {
      return;
    }

    actionsCard.classList.add("admin-user-actions-top-card-v1");

    if (actionsCard.nextElementSibling === shadowCard) {
      return;
    }

    shadowCard.parentNode.insertBefore(actionsCard, shadowCard);
  }

  function initAll() {
    document
      .querySelectorAll("[data-admin-user-shadow-table]")
      .forEach(initTable);

    moveCreateActionsCardToTop();
    window.setTimeout(moveCreateActionsCardToTop, 250);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
'''

write_text(js_path, js_content)


####################################################################################
# (6) CRIAR VALIDAÇÕES
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

new_user_source = (root / "templates" / "new_user.html").read_text(encoding="utf-8")
partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(encoding="utf-8")
js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js").read_text(encoding="utf-8")

required_partial_tokens = (
    "render_admin_user_shadow_readonly_v12",
    "render_admin_user_shadow_actions_v12",
    "href=\\"{{ view_url }}\\"",
    "href=\\"{{ edit_url }}\\"",
    "user_view=1&target=edit-user-card#edit-user-card",
    "target=edit-user-card#edit-user-card",
    "data-admin-user-shadow-real-link",
)

missing_partial_tokens = [
    token
    for token in required_partial_tokens
    if token not in partial_source
]

if missing_partial_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial nativo do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

if "render_admin_user_shadow_readonly_v12(admin_subprocess_shadow_state)" not in new_user_source:
    raise RuntimeError("new_user.html não usa render_admin_user_shadow_readonly_v12.")

if "handleNativeActionClick" in js_source or "handleShadowActionClick" in js_source:
    raise RuntimeError("JS ainda intercepta clique dos botões olho/lápis.")

if "preventDefault" in js_source or "stopImmediatePropagation" in js_source:
    raise RuntimeError("JS ainda contém prevenção de navegação.")

print("OK: templates Jinja carregados com sucesso.")
print("OK: botões olho/lápis são links HTML reais sem interceptação JS.")
'''

write_text(jinja_check_path, jinja_check_content)


render_check_path = ROOT / "scripts" / "check_render_utilizador_shadow_links_v1.py"

render_check_content = '''\
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))
template = env.get_template("partials/admin_user_shadow_readonly_v1.html")

columns = (
    SimpleNamespace(label="ID", source="id"),
    SimpleNamespace(label="NOME", source="full_name"),
    SimpleNamespace(label="EMAIL", source="login_email"),
    SimpleNamespace(label="ESTADO", source="status_label"),
)

state = SimpleNamespace(
    config=SimpleNamespace(
        active_title="Utilizadores ativos",
        inactive_title="Utilizadores inativos",
        columns=columns,
    ),
    active_rows=[
        {
            "id": 25,
            "full_name": "Teste Utilizador",
            "login_email": "teste@appverbo.local",
            "status": "active",
            "status_label": "Ativo",
        }
    ],
    inactive_rows=[],
)

html = template.module.render_admin_user_shadow_readonly_v12(state)

required_fragments = (
    '/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=25&user_view=1&target=edit-user-card#edit-user-card',
    '/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=25&target=edit-user-card#edit-user-card',
    'data-admin-user-shadow-real-link="view"',
    'data-admin-user-shadow-real-link="edit"',
)

missing_fragments = [
    fragment
    for fragment in required_fragments
    if fragment not in html
]

if missing_fragments:
    raise RuntimeError(
        "Links renderizados ausentes: "
        + ", ".join(missing_fragments)
    )

print("OK: hrefs renderizados do olho/lápis estão corretos.")
'''

write_text(render_check_path, render_check_content)


####################################################################################
# (7) RESULTADO
####################################################################################

print("OK: V12 aplicado.")
print("OK: page_handler com debug local sem erro de json.")
print("OK: partial nativo recriado com links reais.")
print("OK: JS recriado sem interceptar clique.")
print("OK: validação de href renderizado criada.")
