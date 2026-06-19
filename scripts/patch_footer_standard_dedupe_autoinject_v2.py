from __future__ import annotations

import re
from pathlib import Path


ROOT = Path.cwd()


####################################################################################
# (1) FUNCOES BASE
####################################################################################

def read_text_v2(relative_path: str) -> str:
    path = ROOT / relative_path

    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {relative_path}")

    return path.read_text(encoding="utf-8")


def write_text_v2(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)

    if not content.endswith("\n"):
        content += "\n"

    path.write_text(content, encoding="utf-8", newline="\n")


def replace_marker_block_v2(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    start_index = content.find(start_marker)
    end_index = content.find(end_marker)

    if start_index >= 0 and end_index >= start_index:
        end_index += len(end_marker)
        return content[:start_index].rstrip() + "\n\n" + new_block.strip() + "\n\n" + content[end_index:].lstrip()

    return content.rstrip() + "\n\n" + new_block.strip() + "\n"


def require_v2(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


####################################################################################
# (2) ATUALIZAR CSS PARA OCULTAR RODAPES LEGADOS DUPLICADOS
####################################################################################

def patch_footer_css_v2() -> None:
    relative_path = "static/css/modules/admin_table_footer_standard_v1.css"
    content = read_text_v2(relative_path)

    dedupe_block = """
/* APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_DEDUPE_V2_START */

/*
  Evita rodape duplicado quando um subprocesso ainda renderiza o rodape legado
  e o novo macro reutilizavel tambem esta ativo no mesmo card.
*/

.appverbo-sessoes-entries-per-page-v1,
.appverbo_sessoes_entries_per_page_v1,
.appverbo-sessoes-entries-per-page-footer-v1,
.appverbo_sessoes_entries_per_page_footer_v1,
.sessoes-entries-per-page-footer-v1,
.sessoes_entries_per_page_footer_v1,
[data-appverbo-sessoes-entries-per-page-v1],
[data-sessoes-entries-per-page],
[data-sessoes-entries-per-page-v1],
#active-sessoes-limiter,
#inactive-sessoes-limiter,
[id*="sessoes"][id$="-limiter"] {
  display: none !important;
}

/* APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_DEDUPE_V2_END */
"""

    content = replace_marker_block_v2(
        content,
        "/* APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_DEDUPE_V2_START */",
        "/* APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_DEDUPE_V2_END */",
        dedupe_block,
    )

    write_text_v2(relative_path, content)


####################################################################################
# (3) REESCREVER JS COM DEDUPE E AUTO-INJECAO CONTROLADA
####################################################################################

def patch_footer_js_v2() -> None:
    relative_path = "static/js/modules/admin_table_footer_standard_v1.js"

    content = r'''//###################################################################################
// APPVERBOBRAGA - ADMIN TABLE FOOTER STANDARD V2
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) SELETORES E CONFIGURACOES
  //###################################################################################

  const LEGACY_FOOTER_SELECTOR_V2 = [
    ".appverbo-sessoes-entries-per-page-v1",
    ".appverbo_sessoes_entries_per_page_v1",
    ".appverbo-sessoes-entries-per-page-footer-v1",
    ".appverbo_sessoes_entries_per_page_footer_v1",
    ".sessoes-entries-per-page-footer-v1",
    ".sessoes_entries_per_page_footer_v1",
    "[data-appverbo-sessoes-entries-per-page-v1]",
    "[data-sessoes-entries-per-page]",
    "[data-sessoes-entries-per-page-v1]",
    ".table-limiter",
    "[id$='-limiter']"
  ].join(",");

  const ADMIN_LIST_CARD_SELECTOR_V2 = [
    ".admin-subprocess-table-card-v1",
    "#admin-users-created-card",
    "#recent-users-card",
    "#inactive-users-card",
    "#active-users-card",
    "#admin-entities-created-card",
    "#recent-entities-card",
    "#inactive-entities-card",
    "#active-entities-card",
    "#admin-menu-card",
    "[data-admin-menu-card]",
    "[data-admin-subprocess]",
    ".admin-menu-card-v1"
  ].join(",");

  //###################################################################################
  // (2) FUNCOES BASE
  //###################################################################################

  function toSafeString_v2(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function toInteger_v2(value, fallback) {
    const parsed = parseInt(value, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
  }

  function clamp_v2(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function escapeAttribute_v2(value) {
    return toSafeString_v2(value)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function normalizeText_v2(value) {
    return toSafeString_v2(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  function ensureElementId_v2(element, prefix) {
    if (!element) {
      return "";
    }

    if (element.id) {
      return element.id;
    }

    const randomPart = Math.random().toString(36).slice(2, 10);
    element.id = prefix + "-" + randomPart;

    return element.id;
  }

  //###################################################################################
  // (3) HTML REUTILIZAVEL
  //###################################################################################

  function buildFooterHtml_v2(config) {
    const safeConfig = config || {};
    const tableId = toSafeString_v2(safeConfig.tableId).trim();
    const pageSize = toInteger_v2(safeConfig.pageSize, 5);
    const ariaLabel = toSafeString_v2(safeConfig.ariaLabel || "Entradas por página");

    return [
      '<div class="admin-table-footer-standard-v1 table-footer admin-status-table-footer-v1" data-admin-table-footer-standard-v1="1"' + (tableId ? ' data-admin-table-id="' + escapeAttribute_v2(tableId) + '"' : "") + '>',
      '  <div class="admin-table-footer-page-size-v1">',
      '    <select class="admin-table-footer-page-size-select-v1" aria-label="' + escapeAttribute_v2(ariaLabel) + '" data-admin-table-footer-page-size-v1="1">',
      '      <option value="5"' + (pageSize === 5 ? " selected" : "") + '>5</option>',
      '      <option value="10"' + (pageSize === 10 ? " selected" : "") + '>10</option>',
      '      <option value="20"' + (pageSize === 20 ? " selected" : "") + '>20</option>',
      '    </select>',
      '    <span class="admin-table-footer-label-v1"><span>entradas</span><span>por página</span></span>',
      '  </div>',
      '  <div class="admin-table-footer-pagination-v1 pagination" data-admin-table-footer-pagination-v1="1">',
      '    <button type="button" class="admin-table-footer-nav-btn-v1" aria-label="Página anterior" data-admin-table-footer-prev-v1="1" disabled>&#8249;</button>',
      '    <span class="admin-table-footer-page-v1 active" aria-current="page" data-admin-table-footer-page-v1="1">1</span>',
      '    <button type="button" class="admin-table-footer-nav-btn-v1" aria-label="Próxima página" data-admin-table-footer-next-v1="1" disabled>&#8250;</button>',
      '  </div>',
      '</div>'
    ].join("");
  }

  //###################################################################################
  // (4) IDENTIFICAR CARDS E TABELAS ELEGIVEIS
  //###################################################################################

  function getCardForElement_v2(element) {
    if (!element) {
      return null;
    }

    return element.closest(".card, .admin-subprocess-table-card-v1, section");
  }

  function cardLooksLikeAdminList_v2(cardEl) {
    if (!cardEl) {
      return false;
    }

    if (cardEl.matches(ADMIN_LIST_CARD_SELECTOR_V2)) {
      return true;
    }

    const titleEl = cardEl.querySelector("h2, h3");
    const titleText = normalizeText_v2(titleEl ? titleEl.textContent : "");

    if (!titleText) {
      return false;
    }

    return [
      "menus ativos",
      "menus inativos",
      "sessoes ativas",
      "sessoes inativas",
      "utilizadores criados",
      "utilizadores inativos",
      "entidades criadas",
      "entidades inativas",
      "entidades ativas"
    ].some(function (expectedTitle) {
      return titleText.indexOf(expectedTitle) >= 0;
    });
  }

  function tableHasRows_v2(tableEl) {
    const tbodyEl = tableEl ? tableEl.querySelector("tbody") : null;

    if (!tbodyEl) {
      return false;
    }

    return tbodyEl.querySelectorAll("tr").length > 0;
  }

  function isEligibleTable_v2(tableEl) {
    if (!tableEl || !tableHasRows_v2(tableEl)) {
      return false;
    }

    const cardEl = getCardForElement_v2(tableEl);

    if (!cardLooksLikeAdminList_v2(cardEl)) {
      return false;
    }

    if (tableEl.closest("form")) {
      return false;
    }

    return true;
  }

  function getTableInsertionAnchor_v2(tableEl) {
    if (!tableEl) {
      return null;
    }

    const wrapEl = tableEl.closest(".admin-subprocess-table-wrap-v1, .table-responsive, .admin-table-wrap-v1");

    if (wrapEl && getCardForElement_v2(wrapEl) === getCardForElement_v2(tableEl)) {
      return wrapEl;
    }

    return tableEl;
  }

  function findTableForFooter_v2(footerEl) {
    const tableId = toSafeString_v2(footerEl.dataset.adminTableId).trim();

    if (tableId) {
      const tableById = document.getElementById(tableId);

      if (tableById) {
        return tableById;
      }
    }

    const previousEl = footerEl.previousElementSibling;

    if (previousEl) {
      if (previousEl.matches && previousEl.matches("table")) {
        return previousEl;
      }

      const tableInsidePrevious = previousEl.querySelector ? previousEl.querySelector("table") : null;

      if (tableInsidePrevious) {
        return tableInsidePrevious;
      }
    }

    const cardEl = getCardForElement_v2(footerEl);

    if (!cardEl) {
      return null;
    }

    const tables = Array.from(cardEl.querySelectorAll("table"));

    for (let index = tables.length - 1; index >= 0; index -= 1) {
      const tableEl = tables[index];

      if (tableEl.compareDocumentPosition(footerEl) & Node.DOCUMENT_POSITION_FOLLOWING) {
        return tableEl;
      }
    }

    return tables.length ? tables[0] : null;
  }

  function getTableRows_v2(tableEl) {
    if (!tableEl) {
      return [];
    }

    const tbodyEl = tableEl.querySelector("tbody");

    if (!tbodyEl) {
      return [];
    }

    return Array.from(tbodyEl.querySelectorAll("tr"));
  }

  //###################################################################################
  // (5) REMOVER OU OCULTAR RODAPES DUPLICADOS
  //###################################################################################

  function hideElement_v2(element) {
    if (!element) {
      return;
    }

    element.setAttribute("data-admin-table-footer-hidden-duplicate-v2", "1");
    element.style.display = "none";
  }

  function hideLegacyFootersWhenStandardExists_v2(rootEl) {
    const scopeEl = rootEl || document;
    const cards = Array.from(scopeEl.querySelectorAll(".card, .admin-subprocess-table-card-v1, section"));

    cards.forEach(function (cardEl) {
      const standardFooters = Array.from(cardEl.querySelectorAll("[data-admin-table-footer-standard-v1='1']"));

      if (!standardFooters.length) {
        return;
      }

      const legacyFooters = Array.from(cardEl.querySelectorAll(LEGACY_FOOTER_SELECTOR_V2));

      legacyFooters.forEach(function (legacyEl) {
        if (legacyEl.closest("[data-admin-table-footer-standard-v1='1']")) {
          return;
        }

        hideElement_v2(legacyEl);
      });
    });
  }

  function hideDuplicateStandardFooters_v2(rootEl) {
    const scopeEl = rootEl || document;
    const cards = Array.from(scopeEl.querySelectorAll(".card, .admin-subprocess-table-card-v1, section"));

    cards.forEach(function (cardEl) {
      const footers = Array.from(cardEl.querySelectorAll("[data-admin-table-footer-standard-v1='1']"));
      const seenByTableId = new Set();

      footers.forEach(function (footerEl) {
        const tableId = toSafeString_v2(footerEl.dataset.adminTableId).trim();
        const key = tableId || "card-footer";

        if (seenByTableId.has(key)) {
          hideElement_v2(footerEl);
          return;
        }

        seenByTableId.add(key);
      });
    });
  }

  //###################################################################################
  // (6) INJETAR RODAPE PADRAO ONDE AINDA NAO EXISTE
  //###################################################################################

  function cardHasStandardFooterForTable_v2(cardEl, tableId) {
    if (!cardEl || !tableId) {
      return false;
    }

    const selector = "[data-admin-table-footer-standard-v1='1'][data-admin-table-id='" + CSS.escape(tableId) + "']";

    return Boolean(cardEl.querySelector(selector));
  }

  function insertFooterAfterTable_v2(tableEl) {
    const cardEl = getCardForElement_v2(tableEl);

    if (!cardEl || !isEligibleTable_v2(tableEl)) {
      return;
    }

    const tableId = ensureElementId_v2(tableEl, "admin-table-standard-v2");

    if (cardHasStandardFooterForTable_v2(cardEl, tableId)) {
      return;
    }

    const insertionAnchor = getTableInsertionAnchor_v2(tableEl);

    if (!insertionAnchor) {
      return;
    }

    const tempEl = document.createElement("div");
    tempEl.innerHTML = buildFooterHtml_v2({
      tableId: tableId,
      pageSize: 5,
      ariaLabel: "Entradas por página"
    });

    const footerEl = tempEl.firstElementChild;

    if (!footerEl) {
      return;
    }

    insertionAnchor.insertAdjacentElement("afterend", footerEl);
  }

  function ensureStandardFootersForTables_v2(rootEl) {
    const scopeEl = rootEl || document;
    const tables = Array.from(scopeEl.querySelectorAll("table"));

    tables.forEach(insertFooterAfterTable_v2);
  }

  //###################################################################################
  // (7) RENDERIZAR PAGINACAO
  //###################################################################################

  function renderFooterState_v2(state) {
    const rows = getTableRows_v2(state.tableEl);
    const totalRows = rows.length;
    const totalPages = Math.max(1, Math.ceil(totalRows / state.pageSize));

    state.currentPage = clamp_v2(state.currentPage, 1, totalPages);

    const startIndex = (state.currentPage - 1) * state.pageSize;
    const endIndex = startIndex + state.pageSize;

    rows.forEach(function (rowEl, index) {
      rowEl.style.display = index >= startIndex && index < endIndex ? "" : "none";
    });

    state.pageEl.textContent = String(state.currentPage);
    state.prevEl.disabled = state.currentPage <= 1;
    state.nextEl.disabled = state.currentPage >= totalPages;
  }

  function initializeFooter_v2(footerEl) {
    if (!footerEl || footerEl.dataset.adminTableFooterInitializedV2 === "1") {
      return;
    }

    if (footerEl.getAttribute("data-admin-table-footer-hidden-duplicate-v2") === "1") {
      return;
    }

    const tableEl = findTableForFooter_v2(footerEl);
    const pageSizeEl = footerEl.querySelector("[data-admin-table-footer-page-size-v1='1']");
    const prevEl = footerEl.querySelector("[data-admin-table-footer-prev-v1='1']");
    const nextEl = footerEl.querySelector("[data-admin-table-footer-next-v1='1']");
    const pageEl = footerEl.querySelector("[data-admin-table-footer-page-v1='1']");

    if (!tableEl || !pageSizeEl || !prevEl || !nextEl || !pageEl) {
      return;
    }

    const state = {
      tableEl: tableEl,
      pageSizeEl: pageSizeEl,
      prevEl: prevEl,
      nextEl: nextEl,
      pageEl: pageEl,
      currentPage: 1,
      pageSize: toInteger_v2(pageSizeEl.value, 5)
    };

    pageSizeEl.addEventListener("change", function () {
      state.pageSize = toInteger_v2(pageSizeEl.value, 5);
      state.currentPage = 1;
      renderFooterState_v2(state);
    });

    prevEl.addEventListener("click", function () {
      if (state.currentPage > 1) {
        state.currentPage -= 1;
        renderFooterState_v2(state);
      }
    });

    nextEl.addEventListener("click", function () {
      state.currentPage += 1;
      renderFooterState_v2(state);
    });

    footerEl.dataset.adminTableFooterInitializedV2 = "1";
    renderFooterState_v2(state);
  }

  function initializeFooters_v2(rootEl) {
    const scopeEl = rootEl || document;

    ensureStandardFootersForTables_v2(scopeEl);
    hideLegacyFootersWhenStandardExists_v2(scopeEl);
    hideDuplicateStandardFooters_v2(scopeEl);

    const footers = Array.from(scopeEl.querySelectorAll("[data-admin-table-footer-standard-v1='1']"));

    footers.forEach(initializeFooter_v2);
  }

  //###################################################################################
  // (8) OBSERVAR RENDERIZACOES DINAMICAS
  //###################################################################################

  let observerTimer_v2 = null;

  function scheduleInitializeFooters_v2() {
    if (observerTimer_v2) {
      window.clearTimeout(observerTimer_v2);
    }

    observerTimer_v2 = window.setTimeout(function () {
      observerTimer_v2 = null;
      initializeFooters_v2(document);
    }, 80);
  }

  function startMutationObserver_v2() {
    if (!document.body || window.AppVerboAdminTableFooterStandardObserverStarted_v2) {
      return;
    }

    const observer = new MutationObserver(function () {
      scheduleInitializeFooters_v2();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    window.AppVerboAdminTableFooterStandardObserverStarted_v2 = true;
  }

  //###################################################################################
  // (9) EXPOR API E INICIALIZAR
  //###################################################################################

  window.AppVerboAdminTableFooterStandard_v2 = {
    buildFooterHtml_v2: buildFooterHtml_v2,
    initializeFooters_v2: initializeFooters_v2
  };

  window.AppVerboAdminTableFooterStandard_v1 = {
    buildFooterHtml_v1: buildFooterHtml_v2,
    initializeFooters_v1: initializeFooters_v2
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initializeFooters_v2(document);
      startMutationObserver_v2();
    });
  } else {
    initializeFooters_v2(document);
    startMutationObserver_v2();
  }
})();
'''

    write_text_v2(relative_path, content)


####################################################################################
# (4) ATUALIZAR CACHE BUSTER NO TEMPLATE PRINCIPAL
####################################################################################

def patch_new_user_cache_v2() -> None:
    relative_path = "templates/new_user.html"
    content = read_text_v2(relative_path)

    css_tag = '<link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1.css?v=20260516-admin-footer-standard-v4-dedupe-autoinject">'
    js_tag = '<script src="/static/js/modules/admin_table_footer_standard_v1.js?v=20260516-admin-footer-standard-v4-dedupe-autoinject" defer></script>'

    if "admin_table_footer_standard_v1.css" in content:
        content = re.sub(
            r'<link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1\.css\?v=[^"]*">',
            css_tag,
            content,
            count=1,
        )
    else:
        content = content.replace("{% block head_extra %}", "{% block head_extra %}\n" + css_tag, 1)

    if "admin_table_footer_standard_v1.js" in content:
        content = re.sub(
            r'<script src="/static/js/modules/admin_table_footer_standard_v1\.js\?v=[^"]*" defer></script>',
            js_tag,
            content,
            count=1,
        )
    else:
        content = content.replace("{% endblock %}", js_tag + "\n{% endblock %}", 1)

    write_text_v2(relative_path, content)


####################################################################################
# (5) VALIDACOES
####################################################################################

def validate_no_mojibake_v2(relative_path: str) -> None:
    content = read_text_v2(relative_path)
    bad_tokens = ("Ã", "Â", "\ufffd")
    bad_lines = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        if any(token in line for token in bad_tokens):
            bad_lines.append((line_number, line))

    if bad_lines:
        print(f"ERRO: possivel mojibake em {relative_path}")
        for line_number, line in bad_lines:
            print(f"Linha {line_number}: {line}")
        raise RuntimeError(f"Possivel mojibake em {relative_path}")


def validate_content_v2() -> None:
    css = read_text_v2("static/css/modules/admin_table_footer_standard_v1.css")
    js = read_text_v2("static/js/modules/admin_table_footer_standard_v1.js")
    template = read_text_v2("templates/new_user.html")

    checks = {
        "CSS contem bloco de dedupe": "APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_DEDUPE_V2_START" in css,
        "CSS oculta rodape legado de Sessoes": "appverbo-sessoes-entries-per-page-v1" in css,
        "JS contem initializeFooters_v2": "function initializeFooters_v2" in js,
        "JS contem hideLegacyFootersWhenStandardExists_v2": "function hideLegacyFootersWhenStandardExists_v2" in js,
        "JS contem ensureStandardFootersForTables_v2": "function ensureStandardFootersForTables_v2" in js,
        "JS expoe API v2": "window.AppVerboAdminTableFooterStandard_v2" in js,
        "JS mantem alias v1": "window.AppVerboAdminTableFooterStandard_v1" in js,
        "new_user carrega CSS v4": "admin-footer-standard-v4-dedupe-autoinject" in template,
        "new_user carrega JS v4": "admin-footer-standard-v4-dedupe-autoinject" in template,
    }

    failed = [label for label, ok in checks.items() if not ok]

    if failed:
        raise RuntimeError("Validacoes falharam: " + ", ".join(failed))

    for relative_path in [
        "static/css/modules/admin_table_footer_standard_v1.css",
        "static/js/modules/admin_table_footer_standard_v1.js",
        "templates/new_user.html",
        "templates/partials/admin_table_footer_standard_v1.html",
        "templates/partials/admin_user_table_v1.html",
        "templates/macros/admin_subprocess.html",
    ]:
        validate_no_mojibake_v2(relative_path)


####################################################################################
# (6) EXECUTAR PATCH
####################################################################################

def main_v2() -> None:
    patch_footer_css_v2()
    patch_footer_js_v2()
    patch_new_user_cache_v2()
    validate_content_v2()

    print("OK: CSS atualizado para ocultar rodapes legados duplicados de Sessoes.")
    print("OK: JS atualizado com dedupe e auto-injecao controlada do rodape padrao.")
    print("OK: cache buster atualizado em templates/new_user.html.")
    print("OK: validacoes de conteudo concluidas.")


if __name__ == "__main__":
    main_v2()
