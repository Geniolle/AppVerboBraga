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


def remove_line_containing(content: str, token: str) -> str:
    return "\n".join(
        line
        for line in content.splitlines()
        if token not in line
    ) + "\n"


####################################################################################
# (2) CORRIGIR LINKS DO OLHO/LÁPIS NO BLOCO NATIVO
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"
partial_content = read_text(partial_path)

partial_content = re.sub(
    r'{%\s*set\s+view_url\s*=\s*".*?"\s*~\s*user_id\s*~\s*".*?"\s*%}',
    '{% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_view=1#edit-user-card" %}',
    partial_content,
    count=1,
)

partial_content = re.sub(
    r'{%\s*set\s+edit_url\s*=\s*".*?"\s*~\s*user_id\s*~\s*".*?"\s*%}',
    '{% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "#edit-user-card" %}',
    partial_content,
    count=1,
)

partial_content = re.sub(
    r'{%\s*macro\s+render_admin_user_shadow_actions_v\d+\(row\)\s*%}',
    '{% macro render_admin_user_shadow_actions_v9(row) %}',
    partial_content,
    count=1,
)

partial_content = re.sub(
    r'render_admin_user_shadow_actions_v\d+\(row\)',
    'render_admin_user_shadow_actions_v9(row)',
    partial_content,
)

partial_content = re.sub(
    r'{%\s*macro\s+render_admin_user_shadow_readonly_v\d+\(state\)\s*%}',
    '{% macro render_admin_user_shadow_readonly_v9(state) %}',
    partial_content,
    count=1,
)

partial_content = re.sub(
    r'{{\s*render_admin_user_shadow_readonly_v\d+\(state\)\s*}}',
    '{{ render_admin_user_shadow_readonly_v9(state) }}',
    partial_content,
)

partial_content = partial_content.replace(
    "admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v8",
    "admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v9",
)

partial_content = partial_content.replace(
    "admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v3",
    "admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v9",
)

partial_content = partial_content.replace(
    "admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v2",
    "admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v9",
)

partial_content = partial_content.replace(
    "admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v1",
    "admin_user_shadow_table_v1.js?v=20260512-utilizador-shadow-table-v9",
)

partial_content = partial_content.replace(
    "admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v6",
    "admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v9",
)

partial_content = partial_content.replace(
    "admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v5",
    "admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v9",
)

partial_content = partial_content.replace(
    "admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v4",
    "admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v9",
)

if "user_edit_id=" not in partial_content:
    raise RuntimeError("Link nativo não contém user_edit_id.")

if "user_view=1#edit-user-card" not in partial_content:
    raise RuntimeError("Link nativo de visualizar não está no padrão legado.")

write_text(partial_path, partial_content)


####################################################################################
# (3) REMOVER IMPORT DA TABELA ANTIGA NO NEW_USER.HTML
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

template_content = remove_line_containing(
    template_content,
    'partials/admin_user_table_v1.html',
)

template_content = re.sub(
    r'{%\s*from\s+"partials/admin_user_shadow_readonly_v1.html"\s+import\s+render_admin_user_shadow_readonly_v\d+\s*%}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v9 %}',
    template_content,
)

template_content = re.sub(
    r'render_admin_user_shadow_readonly_v\d+\(admin_subprocess_shadow_state\)',
    'render_admin_user_shadow_readonly_v9(admin_subprocess_shadow_state)',
    template_content,
)


####################################################################################
# (4) REMOVER BLOCOS LEGADOS QUE USAM render_admin_user_table_v1
####################################################################################

lines = template_content.splitlines()
remove_indexes: set[int] = set()

for index, line in enumerate(lines):
    if "render_admin_user_table_v1" not in line:
        continue

    start = index
    while start > 0:
        candidate = lines[start]
        if "<section" in candidate or '<div class="card' in candidate or "<div class='card" in candidate:
            break
        start -= 1

    end = index
    while end < len(lines) - 1:
        candidate = lines[end]
        if "</section>" in candidate:
            break
        if "</div>" in candidate and end > index:
            next_five = "\n".join(lines[end + 1:end + 6])
            if (
                "render_admin_user_table_v1" not in next_five
                and "Utilizadores inativos" not in next_five
                and "Utilizadores ativos" not in next_five
            ):
                break
        end += 1

    for remove_index in range(start, end + 1):
        remove_indexes.add(remove_index)

if not remove_indexes:
    raise RuntimeError("Nenhum bloco legado render_admin_user_table_v1 foi encontrado para remover.")

template_content = "\n".join(
    line
    for index, line in enumerate(lines)
    if index not in remove_indexes
) + "\n"

if "render_admin_user_table_v1" in template_content:
    raise RuntimeError("Ainda existe render_admin_user_table_v1 no new_user.html.")

if "partials/admin_user_table_v1.html" in template_content:
    raise RuntimeError("Ainda existe import da tabela antiga no new_user.html.")

if "render_admin_user_shadow_readonly_v9(admin_subprocess_shadow_state)" not in template_content:
    raise RuntimeError("Render V9 do bloco nativo não encontrado no new_user.html.")

write_text(template_path, template_content)


####################################################################################
# (5) APAGAR FICHEIRO DA TABELA ANTIGA
####################################################################################

old_partial_path = ROOT / "templates" / "partials" / "admin_user_table_v1.html"

if old_partial_path.exists():
    old_partial_path.unlink()


####################################################################################
# (6) ATUALIZAR JS: MOVER CRIAR/GERAR LINK PARA O TOPO E CLICAR AÇÕES NATIVAS
####################################################################################

js_path = ROOT / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js"

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

  function handleNativeActionClick(event) {
    const actionLink = event.target.closest("#admin-user-shadow-readonly-card .table-icon-btn");

    if (!actionLink) {
      return;
    }

    const targetUrl = actionLink.getAttribute("href");

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

  function initAll() {
    document
      .querySelectorAll("[data-admin-user-shadow-table]")
      .forEach(initTable);

    moveCreateActionsCardToTop();
    window.setTimeout(moveCreateActionsCardToTop, 250);
  }

  document.addEventListener("click", handleNativeActionClick, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
"""

write_text(js_path, js_content)


####################################################################################
# (7) CSS PARA CARD DE AÇÕES NO TOPO
####################################################################################

css_path = ROOT / "static" / "css" / "modules" / "admin_user_shadow_table_v1.css"
css_content = read_text(css_path) if css_path.exists() else ""

css_extra = """\

.admin-user-actions-top-card-v1 {
  margin: 0 0 12px;
}

.admin-user-actions-top-card-v1 + .admin-user-shadow-readonly-card-v1 {
  margin-top: 0;
}
"""

if ".admin-user-actions-top-card-v1" not in css_content:
    css_content = css_content.rstrip() + css_extra

write_text(css_path, css_content)


####################################################################################
# (8) ATUALIZAR VALIDAÇÃO JINJA
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

new_user_source = (root / "templates" / "new_user.html").read_text(
    encoding="utf-8"
)

partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(
    encoding="utf-8"
)

js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js").read_text(
    encoding="utf-8"
)

if "render_admin_user_table_v1" in new_user_source:
    raise RuntimeError("Tabela antiga ainda está referenciada no new_user.html.")

if "partials/admin_user_table_v1.html" in new_user_source:
    raise RuntimeError("Partial antigo ainda está importado no new_user.html.")

if (root / "templates" / "partials" / "admin_user_table_v1.html").exists():
    raise RuntimeError("Ficheiro antigo admin_user_table_v1.html ainda existe.")

required_partial_tokens = (
    "render_admin_user_shadow_readonly_v9",
    "render_admin_user_shadow_actions_v9",
    "user_view=1#edit-user-card",
    "user_edit_id",
)

required_js_tokens = (
    "handleNativeActionClick",
    "window.location.href",
    "moveCreateActionsCardToTop",
    "admin-user-actions-top-card-v1",
)

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
print("OK: tabela antiga do Utilizador removida.")
print("OK: ações nativas e card Criar/Gerar link validados.")
'''

write_text(jinja_check_path, jinja_check_content)


####################################################################################
# (9) RESULTADO
####################################################################################

print("OK: tabela antiga do Utilizador removida do new_user.html.")
print("OK: ficheiro templates/partials/admin_user_table_v1.html apagado.")
print("OK: links nativos corrigidos para padrão legado.")
print("OK: card Criar utilizador/Gerar link será movido para cima.")
