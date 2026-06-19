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
# (2) ATUALIZAR PARTIAL PARA CACHE BUST V13
####################################################################################

partial_path = ROOT / "templates" / "partials" / "admin_user_shadow_readonly_v1.html"
partial_content = read_text(partial_path)

partial_content = re.sub(
    r'admin_user_shadow_table_v1\.js\?v=[^"]+',
    '$120260513-utilizador-view-toggle-v5',
    partial_content,
)

partial_content = re.sub(
    r'admin_user_shadow_table_v1\.css\?v=[^"]+',
    'admin_user_shadow_table_v1.css?v=20260512-utilizador-shadow-layout-v13',
    partial_content,
)

if "data-admin-user-shadow-real-link" not in partial_content:
    raise RuntimeError("Partial não contém data-admin-user-shadow-real-link.")

write_text(partial_path, partial_content)


####################################################################################
# (3) REESCREVER JS COM HANDLER SEGURO PARA OLHO/LÁPIS
####################################################################################

js_path = ROOT / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js?v=20260513-utilizador-view-toggle-v5"

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

  function forceNativeActionNavigation(event) {
    const actionLink = event.target.closest(
      "#admin-user-shadow-readonly-card a[data-admin-user-shadow-real-link]"
    );

    if (!actionLink) {
      return;
    }

    const href = actionLink.getAttribute("href") || actionLink.href;

    if (!href) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    window.location.assign(href);
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

check_path = ROOT / "scripts" / "check_template_jinja_utilizador_shadow_v1.py"

check_content = '''\
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

root = Path.cwd()
env = Environment(loader=FileSystemLoader(str(root / "templates")))

env.get_template("new_user.html")
env.get_template("partials/admin_user_shadow_readonly_v1.html")

partial_source = (root / "templates" / "partials" / "admin_user_shadow_readonly_v1.html").read_text(encoding="utf-8")
js_source = (root / "static" / "js" / "modules" / "admin_user_shadow_table_v1.js?v=20260513-utilizador-view-toggle-v5").read_text(encoding="utf-8")

required_partial_tokens = (
    "data-admin-user-shadow-real-link",
    "user_edit_id=",
    "target=edit-user-card#edit-user-card",
    "utilizador-shadow-table-v13",
)

required_js_tokens = (
    "forceNativeActionNavigation",
    "window.location.assign",
    "focusEditUserCardFromQuery",
    "edit-user-card",
    "scrollIntoView",
    "document.addEventListener(\\"click\\", forceNativeActionNavigation, true)",
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
print("OK: clique e foco nativo do Utilizador validados.")
'''

write_text(check_path, check_content)


####################################################################################
# (5) RESULTADO
####################################################################################

print("OK: V13 aplicado.")
print("OK: clique olho/lápis agora é capturado em fase capture e navega via window.location.assign.")
print("OK: quando user_edit_id existir, JS tenta focar #edit-user-card.")
