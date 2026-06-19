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
# (2) RECRIAR AÇÕES DO PARTIAL COM USER_VIEW EXPLÍCITO
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"
partial_content = read_text(partial_path)

actions_macro_v15 = '''{% macro render_admin_user_shadow_actions_v15(row) %}
  {% set user_id = row.get('id', '') %}
  {% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_view=1&target=edit-user-card#edit-user-card" %}
  {% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_view=0&target=edit-user-card#edit-user-card" %}

  <div class="table-actions">
    <a
      class="table-icon-btn"
      href="{{ view_url }}"
      title="Exibir utilizador"
      aria-label="Exibir utilizador"
      data-admin-user-shadow-real-link="view"
      data-admin-user-shadow-user-id="{{ user_id }}"
    >
      &#128065;
    </a>
    <a
      class="table-icon-btn"
      href="{{ edit_url }}"
      title="Modificar utilizador"
      aria-label="Modificar utilizador"
      data-admin-user-shadow-real-link="edit"
      data-admin-user-shadow-user-id="{{ user_id }}"
    >
      &#9998;
    </a>
  </div>
{% endmacro %}'''

partial_content = re.sub(
    r'{%\s*macro\s+render_admin_user_shadow_actions_v\d+\(row\)\s*%}.*?{%\s*endmacro\s*%}',
    actions_macro_v15,
    partial_content,
    count=1,
    flags=re.S,
)

partial_content = re.sub(
    r'render_admin_user_shadow_actions_v\d+\(row\)',
    'render_admin_user_shadow_actions_v15(row)',
    partial_content,
)

partial_content = re.sub(
    r'admin_user_shadow_table_v1\.js\?v=[^"]+',
    '$120260513-utilizador-view-toggle-v5',
    partial_content,
)

partial_content = re.sub(
    r'admin_user_shadow_table_v1\.css\?v=[^"]+',
    'admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v15',
    partial_content,
)

required_partial_tokens = (
    "render_admin_user_shadow_actions_v15",
    'data-admin-user-shadow-real-link="view"',
    'data-admin-user-shadow-real-link="edit"',
    'data-admin-user-shadow-user-id="{{ user_id }}"',
    "user_view=1&target=edit-user-card#edit-user-card",
    "user_view=0&target=edit-user-card#edit-user-card",
    "utilizador-shadow-table-v15",
)

missing_partial_tokens = [
    token
    for token in required_partial_tokens
    if token not in partial_content
]

if missing_partial_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial nativo do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

write_text(partial_path, partial_content)


####################################################################################
# (3) REESCREVER JS COM ROTA EXPLÍCITA PARA VIEW E EDIT
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

  function buildUserActionUrl(action, userId) {
    const cleanUserId = String(userId || "").trim();

    if (!cleanUserId) {
      return "";
    }

    const userViewValue = action === "view" ? "1" : "0";

    return "/users/new"
      + "?menu=administrativo"
      + "&admin_tab=utilizador"
      + "&user_edit_id=" + encodeURIComponent(cleanUserId)
      + "&user_view=" + userViewValue
      + "&target=edit-user-card"
      + "#edit-user-card";
  }

  function forceNativeActionNavigation(event) {
    const actionLink = event.target.closest(
      "#admin-user-shadow-readonly-card [data-admin-user-shadow-real-link]"
    );

    if (!actionLink) {
      return;
    }

    const action = actionLink.getAttribute("data-admin-user-shadow-real-link");
    const userId = actionLink.getAttribute("data-admin-user-shadow-user-id");
    const explicitUrl = buildUserActionUrl(action, userId);
    const fallbackUrl = actionLink.getAttribute("href") || actionLink.href;
    const targetUrl = explicitUrl || fallbackUrl;

    if (!targetUrl) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    window.location.href = targetUrl;
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

  function focusEditUserCardFromQuery() {
    const params = new URLSearchParams(window.location.search);

    if (params.get("menu") !== "administrativo") {
      return;
    }

    if (params.get("admin_tab") !== "utilizador") {
      return;
    }

    if (!params.get("user_edit_id")) {
      return;
    }

    const editCard = document.getElementById("edit-user-card");

    if (!editCard) {
      console.warn("APPVERBO_UTILIZADOR_FOCUS_DEBUG_V1 edit-user-card não encontrado.");
      return;
    }

    editCard.hidden = false;
    editCard.removeAttribute("hidden");
    editCard.style.display = "";

    window.setTimeout(function () {
      editCard.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 120);
  }

  function initAll() {
    document
      .querySelectorAll("[data-admin-user-shadow-table]")
      .forEach(initTable);

    moveCreateActionsCardToTop();
    focusEditUserCardFromQuery();

    window.setTimeout(moveCreateActionsCardToTop, 250);
    window.setTimeout(focusEditUserCardFromQuery, 350);
  }

  document.addEventListener("click", forceNativeActionNavigation, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
'''

write_text(js_path, js_content)


####################################################################################
# (4) ATUALIZAR VALIDAÇÃO JINJA/JS
####################################################################################

check_template_path = ROOT / "scripts" / "check_template_jinja_utilizador_shadow_v1.py"

check_template_content = '''\
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))

env.get_template("new_user.html")
env.get_template("partials/admin_user_shadow_readonly_v1.html")

page_handler_source = (root / "appverbo" / "routes" / "profile" / "page_handler.py").read_text(
    encoding="utf-8"
)
partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(
    encoding="utf-8"
)
js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js").read_text(
    encoding="utf-8"
)

required_page_tokens = (
    "APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_START",
    "resolved_admin_tab == \\"utilizador\\"",
    "parsed_user_edit_id is not None",
    "initial_menu_target = \\"#edit-user-card\\"",
)

required_partial_tokens = (
    "render_admin_user_shadow_actions_v15",
    "data-admin-user-shadow-real-link=\\"view\\"",
    "data-admin-user-shadow-real-link=\\"edit\\"",
    "data-admin-user-shadow-user-id=\\"{{ user_id }}\\"",
    "user_view=1&target=edit-user-card#edit-user-card",
    "user_view=0&target=edit-user-card#edit-user-card",
    "utilizador-shadow-table-v15",
)

required_js_tokens = (
    "buildUserActionUrl",
    "userViewValue = action === \\"view\\" ? \\"1\\" : \\"0\\"",
    "data-admin-user-shadow-user-id",
    "window.location.href = targetUrl",
    "focusEditUserCardFromQuery",
    "edit-user-card",
    "document.addEventListener(\\"click\\", forceNativeActionNavigation, true)",
)

missing_page_tokens = [
    token
    for token in required_page_tokens
    if token not in page_handler_source
]

missing_partial_tokens = [
    token
    for token in required_partial_tokens
    if token not in partial_source
]

missing_js_tokens = [
    token
    for token in required_js_tokens
    if token not in js_source
]

if missing_page_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no page_handler.py: "
        + ", ".join(missing_page_tokens)
    )

if missing_partial_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no partial nativo do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

if missing_js_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no JS nativo do Utilizador: "
        + ", ".join(missing_js_tokens)
    )

print("OK: templates Jinja carregados com sucesso.")
print("OK: botão lápis usa user_view=0 e navegação explícita.")
'''

write_text(check_template_path, check_template_content)


####################################################################################
# (5) ATUALIZAR CHECK DOS HREFS RENDERIZADOS
####################################################################################

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

expected_view_href = (
    "/users/new?menu=administrativo&admin_tab=utilizador"
    "&user_edit_id=25&user_view=1&target=edit-user-card#edit-user-card"
)

expected_edit_href = (
    "/users/new?menu=administrativo&admin_tab=utilizador"
    "&user_edit_id=25&user_view=0&target=edit-user-card#edit-user-card"
)

required_fragments = (
    expected_view_href,
    expected_edit_href,
    'data-admin-user-shadow-real-link="view"',
    'data-admin-user-shadow-real-link="edit"',
    'data-admin-user-shadow-user-id="25"',
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

print("OK: href do olho renderizado corretamente.")
print("OK: href do lápis renderizado corretamente com user_view=0.")
'''

write_text(render_check_path, render_check_content)


####################################################################################
# (6) RESULTADO
####################################################################################

print("OK: lápis do Utilizador corrigido para user_view=0.")
print("OK: JS agora monta rota explícita para view/edit.")
print("OK: validações atualizadas.")
