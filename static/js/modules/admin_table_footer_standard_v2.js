//###################################################################################
// APPVERBOBRAGA - ADMIN TABLE FOOTER STANDARD V2
//###################################################################################

(function setupAdminTableFooterStandardV2() {
  "use strict";

  //###################################################################################
  // (1) SELETORES E CONFIGURACOES
  //###################################################################################

  const ADMIN_LIST_CARD_SELECTOR_V2 = [
    ".admin-subprocess-table-card-v1",
    ".admin-subprocess-v2-card",
    ".admin-user-shadow-readonly-card-v1",
    "#admin-users-created-card",
    "#inactive-users-card",
    "#admin-user-shadow-readonly-card",
    "#admin-user-shadow-inactive-card",
    "#admin-menu-card",
    "#admin-menu-card-inactive",
    "#recent-entities-card",
    "#inactive-entities-card",
    "[data-admin-subprocess]",
    "[data-admin-subprocess-shadow='utilizador']",
    "[data-admin-subprocess-shadow='utilizador-inactive']",
  ].join(",");

  //###################################################################################
  // (2) FUNCOES BASE
  //###################################################################################

  function toSafeStringV2(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function toIntegerV2(value, fallback) {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
  }

  function clampV2(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function normalizeTextV2(value) {
    return toSafeStringV2(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  function escapeAttributeV2(value) {
    return toSafeStringV2(value)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function ensureElementIdV2(element, prefix) {
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
  // (3) HTML DO RODAPE PADRAO
  //###################################################################################

  function buildFooterHtmlV2(config) {
    const safeConfig = config || {};
    const tableId = toSafeStringV2(safeConfig.tableId).trim();
    const pageSize = toIntegerV2(safeConfig.pageSize, 5);
    const ariaLabel = toSafeStringV2(safeConfig.ariaLabel || "Entradas por página");

    return [
      '<div class="admin-table-footer-standard-v1 table-footer admin-status-table-footer-v1" data-admin-table-footer-standard-v1="1"' +
        (tableId ? ' data-admin-table-id="' + escapeAttributeV2(tableId) + '"' : "") +
        ">",
      '  <div class="admin-table-footer-page-size-v1">',
      '    <select class="admin-table-footer-page-size-select-v1" aria-label="' +
        escapeAttributeV2(ariaLabel) +
        '" data-admin-table-footer-page-size-v1="1">',
      '      <option value="5"' + (pageSize === 5 ? " selected" : "") + ">5</option>",
      '      <option value="10"' + (pageSize === 10 ? " selected" : "") + ">10</option>",
      '      <option value="20"' + (pageSize === 20 ? " selected" : "") + ">20</option>",
      "    </select>",
      '    <span class="admin-table-footer-label-v1"><span>entradas</span><span>por página</span></span>',
      "  </div>",
      '  <div class="admin-table-footer-pagination-v1 pagination" data-admin-table-footer-pagination-v1="1">',
      '    <button type="button" class="admin-table-footer-nav-btn-v1" aria-label="Página anterior" data-admin-table-footer-prev-v1="1" disabled>&#8249;</button>',
      '    <span class="admin-table-footer-page-v1 active" aria-current="page" data-admin-table-footer-page-v1="1">1</span>',
      '    <button type="button" class="admin-table-footer-nav-btn-v1" aria-label="Próxima página" data-admin-table-footer-next-v1="1" disabled>&#8250;</button>',
      "  </div>",
      "</div>",
    ].join("");
  }

  //###################################################################################
  // (4) ELEGIBILIDADE E INJECAO DE RODAPE
  //###################################################################################

  function getCardForElementV2(element) {
    if (!element) {
      return null;
    }

    return element.closest(
      ".card, section, .admin-subprocess-table-card-v1, .admin-subprocess-v2-card, .admin-user-shadow-readonly-card-v1"
    );
  }

  function cardLooksLikeAdminListV2(cardEl) {
    if (!cardEl) {
      return false;
    }

    if (cardEl.matches(ADMIN_LIST_CARD_SELECTOR_V2)) {
      return true;
    }

    const titleEl = cardEl.querySelector("h2, h3");
    const titleText = normalizeTextV2(titleEl ? titleEl.textContent : "");

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
      "entidades ativas",
    ].some((expectedTitle) => titleText.includes(expectedTitle));
  }

  function tableHasRowsV2(tableEl) {
    const tbodyEl = tableEl ? tableEl.querySelector("tbody") : null;

    if (!tbodyEl) {
      return false;
    }

    return tbodyEl.querySelectorAll("tr").length > 0;
  }

  function isEligibleTableV2(tableEl) {
    if (!tableEl || !tableHasRowsV2(tableEl)) {
      return false;
    }

    const cardEl = getCardForElementV2(tableEl);

    if (!cardLooksLikeAdminListV2(cardEl)) {
      return false;
    }

    if (tableEl.closest("form")) {
      return false;
    }

    return true;
  }

  function getTableInsertionAnchorV2(tableEl) {
    if (!tableEl) {
      return null;
    }

    const wrapEl = tableEl.closest(
      ".admin-subprocess-table-wrap-v1, .admin-subprocess-v2-table-wrap, .table-responsive, .admin-table-wrap-v1, .admin-menu-table-wrap-v1"
    );

    if (wrapEl && getCardForElementV2(wrapEl) === getCardForElementV2(tableEl)) {
      return wrapEl;
    }

    return tableEl;
  }

  function cardHasStandardFooterForTableV2(cardEl, tableId) {
    if (!cardEl || !tableId) {
      return false;
    }

    const footers = Array.from(
      cardEl.querySelectorAll('[data-admin-table-footer-standard-v1="1"]')
    );
    return footers.some(
      (footerEl) => toSafeStringV2(footerEl.dataset.adminTableId).trim() === tableId
    );
  }

  function insertFooterAfterTableV2(tableEl) {
    const cardEl = getCardForElementV2(tableEl);

    if (!cardEl || !isEligibleTableV2(tableEl)) {
      return;
    }

    const tableId = ensureElementIdV2(tableEl, "admin-table-standard-v2");

    if (cardHasStandardFooterForTableV2(cardEl, tableId)) {
      return;
    }

    const insertionAnchor = getTableInsertionAnchorV2(tableEl);

    if (!insertionAnchor) {
      return;
    }

    const tempEl = document.createElement("div");
    tempEl.innerHTML = buildFooterHtmlV2({
      tableId: tableId,
      pageSize: 5,
      ariaLabel: "Entradas por página",
    });

    const footerEl = tempEl.firstElementChild;

    if (!footerEl) {
      return;
    }

    insertionAnchor.insertAdjacentElement("afterend", footerEl);
  }

  function ensureStandardFootersForTablesV2(rootEl) {
    const scopeEl = rootEl || document;
    const tables = Array.from(scopeEl.querySelectorAll("table"));
    tables.forEach(insertFooterAfterTableV2);
  }

  //###################################################################################
  // (5) PAGINACAO
  //###################################################################################

  function findTableForFooterV2(footerEl) {
    const tableId = toSafeStringV2(footerEl.dataset.adminTableId).trim();

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

      const tableInsidePrevious = previousEl.querySelector
        ? previousEl.querySelector("table")
        : null;

      if (tableInsidePrevious) {
        return tableInsidePrevious;
      }
    }

    const cardEl = getCardForElementV2(footerEl);

    if (!cardEl) {
      return null;
    }

    const tables = Array.from(cardEl.querySelectorAll("table"));
    return tables.length ? tables[0] : null;
  }

  function getTableRowsV2(tableEl) {
    if (!tableEl) {
      return [];
    }

    const tbodyEl = tableEl.querySelector("tbody");
    if (!tbodyEl) {
      return [];
    }

    return Array.from(tbodyEl.querySelectorAll("tr"));
  }

  function getFilteredRowsForFooterV2(rows) {
    return rows.filter((rowEl) => rowEl.dataset.adminSearchMatchV1 !== "0");
  }

  function renderFooterStateV2(state) {
    const rows = getTableRowsV2(state.tableEl);
    const filteredRows = getFilteredRowsForFooterV2(rows);
    const totalRows = filteredRows.length;
    const totalPages = Math.max(1, Math.ceil(totalRows / state.pageSize));

    state.currentPage = clampV2(state.currentPage, 1, totalPages);

    const startIndex = (state.currentPage - 1) * state.pageSize;
    const endIndex = startIndex + state.pageSize;

    rows.forEach((rowEl) => {
      rowEl.style.display = "none";
    });

    filteredRows.forEach((rowEl, index) => {
      rowEl.style.display = index >= startIndex && index < endIndex ? "" : "none";
    });

    state.pageEl.textContent = String(state.currentPage);
    state.prevEl.disabled = state.currentPage <= 1;
    state.nextEl.disabled = state.currentPage >= totalPages;
  }

  function initializeFooterV2(footerEl) {
    if (!footerEl || footerEl.dataset.adminTableFooterInitializedV2 === "1") {
      return;
    }

    const tableEl = findTableForFooterV2(footerEl);
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
      pageSize: toIntegerV2(pageSizeEl.value, 5),
    };

    pageSizeEl.addEventListener("change", function () {
      state.pageSize = toIntegerV2(pageSizeEl.value, 5);
      state.currentPage = 1;
      renderFooterStateV2(state);
    });

    prevEl.addEventListener("click", function () {
      if (state.currentPage > 1) {
        state.currentPage -= 1;
        renderFooterStateV2(state);
      }
    });

    nextEl.addEventListener("click", function () {
      state.currentPage += 1;
      renderFooterStateV2(state);
    });

    tableEl.addEventListener("admin-table-filter-changed", function () {
      state.currentPage = 1;
      renderFooterStateV2(state);
    });

    footerEl.dataset.adminTableFooterInitializedV2 = "1";
    renderFooterStateV2(state);
  }

  function initializeFootersV2(rootEl) {
    const scopeEl = rootEl || document;

    ensureStandardFootersForTablesV2(scopeEl);

    const footers = Array.from(
      scopeEl.querySelectorAll('[data-admin-table-footer-standard-v1="1"]')
    );
    footers.forEach(initializeFooterV2);
  }

  //###################################################################################
  // (6) OBSERVAR RENDERIZACOES DINAMICAS
  //###################################################################################

  let observerTimerV2 = null;

  function scheduleInitializeFootersV2() {
    if (observerTimerV2) {
      window.clearTimeout(observerTimerV2);
    }

    observerTimerV2 = window.setTimeout(function () {
      observerTimerV2 = null;
      initializeFootersV2(document);
    }, 80);
  }

  function startMutationObserverV2() {
    if (!document.body || window.AppVerboAdminTableFooterStandardObserverStartedV2) {
      return;
    }

    const observer = new MutationObserver(function () {
      scheduleInitializeFootersV2();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    window.AppVerboAdminTableFooterStandardObserverStartedV2 = true;
  }

  //###################################################################################
  // (7) EXPOE API E INICIALIZA
  //###################################################################################

  window.AppVerboAdminTableFooterStandard_v2 = {
    buildFooterHtml_v2: buildFooterHtmlV2,
    initializeFooters_v2: initializeFootersV2,
  };

  window.AppVerboAdminTableFooterStandard_v1 = {
    buildFooterHtml_v1: buildFooterHtmlV2,
    initializeFooters_v1: initializeFootersV2,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initializeFootersV2(document);
      startMutationObserverV2();
    });
  } else {
    initializeFootersV2(document);
    startMutationObserverV2();
  }
})();
