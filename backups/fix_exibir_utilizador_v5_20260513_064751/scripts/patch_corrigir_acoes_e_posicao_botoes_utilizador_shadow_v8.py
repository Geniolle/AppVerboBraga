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
# (2) CORRIGIR LINKS DAS AÇÕES NATIVAS
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"
partial_content = read_text(partial_path)

view_line = '{% set view_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&user_view=1&target=edit-user-card#edit-user-card" %}'
edit_line = '{% set edit_url = "/users/new?menu=administrativo&admin_tab=utilizador&user_edit_id=" ~ user_id ~ "&target=edit-user-card#edit-user-card" %}'

partial_content = re.sub(
    r'{%\s*set\s+view_url\s*=\s*".*?"\s*~\s*user_id\s*~\s*".*?"\s*%}',
    view_line,
    partial_content,
    count=1,
)

partial_content = re.sub(
    r'{%\s*set\s+edit_url\s*=\s*".*?"\s*~\s*user_id\s*~\s*".*?"\s*%}',
    edit_line,
    partial_content,
    count=1,
)

partial_content = re.sub(
    r'{%\s*macro\s+render_admin_user_shadow_actions_v\d+\(row\)\s*%}',
    '{% macro render_admin_user_shadow_actions_v8(row) %}',
    partial_content,
    count=1,
)

partial_content = re.sub(
    r'render_admin_user_shadow_actions_v\d+\(row\)',
    'render_admin_user_shadow_actions_v8(row)',
    partial_content,
)

partial_content = re.sub(
    r'{%\s*macro\s+render_admin_user_shadow_readonly_v\d+\(state\)\s*%}',
    '{% macro render_admin_user_shadow_readonly_v8(state) %}',
    partial_content,
    count=1,
)

partial_content = re.sub(
    r'{{\s*render_admin_user_shadow_readonly_v\d+\(state\)\s*}}',
    '{{ render_admin_user_shadow_readonly_v8(state) }}',
    partial_content,
)

if 'data-admin-user-shadow-action-url="{{ view_url }}"' not in partial_content:
    partial_content = partial_content.replace(
        'href="{{ view_url }}"\n      title=',
        'href="{{ view_url }}"\n      data-admin-user-shadow-action-url="{{ view_url }}"\n      title=',
        1,
    )

if 'data-admin-user-shadow-action-url="{{ edit_url }}"' not in partial_content:
    partial_content = partial_content.replace(
        'href="{{ edit_url }}"\n      title=',
        'href="{{ edit_url }}"\n      data-admin-user-shadow-action-url="{{ edit_url }}"\n      title=',
        1,
    )

partial_content = partial_content.replace(
    "$120260513-utilizador-view-toggle-v5",
    "$120260513-utilizador-view-toggle-v5",
)

partial_content = partial_content.replace(
    "$120260513-utilizador-view-toggle-v5",
    "$120260513-utilizador-view-toggle-v5",
)

partial_content = partial_content.replace(
    "$120260513-utilizador-view-toggle-v5",
    "$120260513-utilizador-view-toggle-v5",
)

if "user_view=1&target=edit-user-card#edit-user-card" not in partial_content:
    raise RuntimeError("Link de visualizar não foi corrigido.")

if "target=edit-user-card#edit-user-card" not in partial_content:
    raise RuntimeError("Link de editar não foi corrigido.")

if "data-admin-user-shadow-action-url" not in partial_content:
    raise RuntimeError("data-admin-user-shadow-action-url não foi aplicado.")

write_text(partial_path, partial_content)


####################################################################################
# (3) ATUALIZAR NEW_USER.HTML PARA MACRO V8
####################################################################################

template_path = ROOT / "templates" / "new_user.html"
template_content = read_text(template_path)

template_content = re.sub(
    r'{%\s*from\s+"partials/admin_user_shadow_readonly_v1.html"\s+import\s+render_admin_user_shadow_readonly_v\d+\s*%}',
    '{% from "partials/admin_user_shadow_readonly_v1.html" import render_admin_user_shadow_readonly_v8 %}',
    template_content,
)

template_content = re.sub(
    r'render_admin_user_shadow_readonly_v\d+\(admin_subprocess_shadow_state\)',
    'render_admin_user_shadow_readonly_v8(admin_subprocess_shadow_state)',
    template_content,
)

if "render_admin_user_shadow_readonly_v8(admin_subprocess_shadow_state)" not in template_content:
    raise RuntimeError("Render V8 não encontrado no new_user.html")

write_text(template_path, template_content)


####################################################################################
# (4) ATUALIZAR JS: CLICK FORÇADO NAS AÇÕES + MOVER CARD CRIAR/GERAR LINK
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

  function handleShadowActionClick(event) {
    const actionLink = event.target.closest("[data-admin-user-shadow-action-url]");

    if (!actionLink) {
      return;
    }

    const targetUrl = actionLink.getAttribute("data-admin-user-shadow-action-url") || actionLink.href;

    if (!targetUrl) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    window.location.assign(targetUrl);
  }

  function findLegacyCreateActionsCard() {
    const cards = Array.from(document.querySelectorAll(".card"));

    return cards
      .filter(function (card) {
        const text = normalizeText(card.textContent);
        return text.includes("criar utilizador") && text.includes("gerar link");
      })
      .sort(function (a, b) {
        return a.textContent.length - b.textContent.length;
      })[0] || null;
  }

  function moveLegacyCreateActionsCard() {
    const params = new URLSearchParams(window.location.search);

    if (params.get("menu") !== "administrativo" || params.get("admin_tab") !== "utilizador") {
      return;
    }

    const shadowCard = document.getElementById("admin-user-shadow-readonly-card");
    const legacyActionsCard = findLegacyCreateActionsCard();

    if (!shadowCard || !legacyActionsCard || legacyActionsCard === shadowCard) {
      return;
    }

    legacyActionsCard.classList.add("admin-user-actions-top-card-v1");

    if (legacyActionsCard.nextElementSibling === shadowCard) {
      return;
    }

    shadowCard.parentNode.insertBefore(legacyActionsCard, shadowCard);
  }

  function initAllTables() {
    document
      .querySelectorAll("[data-admin-user-shadow-table]")
      .forEach(initTable);

    moveLegacyCreateActionsCard();

    window.setTimeout(moveLegacyCreateActionsCard, 250);
  }

  document.addEventListener("click", handleShadowActionClick, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAllTables);
  } else {
    initAllTables();
  }
})();
"""

write_text(js_path, js_content)


####################################################################################
# (5) CSS: CARD DE AÇÕES NO TOPO
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

js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js").read_text(
    encoding="utf-8"
)

required_partial_tokens = (
    "render_admin_user_shadow_readonly_v8",
    "render_admin_user_shadow_actions_v8",
    "user_view=1&target=edit-user-card#edit-user-card",
    "target=edit-user-card#edit-user-card",
    "data-admin-user-shadow-action-url",
)

required_js_tokens = (
    "handleShadowActionClick",
    "window.location.assign",
    "moveLegacyCreateActionsCard",
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
        "Tokens esperados ausentes no partial do Utilizador: "
        + ", ".join(missing_partial_tokens)
    )

if missing_js_tokens:
    raise RuntimeError(
        "Tokens esperados ausentes no JS do Utilizador: "
        + ", ".join(missing_js_tokens)
    )

print("OK: templates Jinja carregados com sucesso.")
print("OK: ações e posição dos botões do Utilizador validadas.")
'''

write_text(jinja_check_path, jinja_check_content)


####################################################################################
# (7) RESULTADO
####################################################################################

print("OK: ações do bloco nativo corrigidas com navegação forçada.")
print("OK: card Criar utilizador/Gerar link será movido para cima via JS.")
print("OK: new_user.html atualizado para render_admin_user_shadow_readonly_v8.")
