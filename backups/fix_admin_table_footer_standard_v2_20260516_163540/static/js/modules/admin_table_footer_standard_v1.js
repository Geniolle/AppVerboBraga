//###################################################################################
// APPVERBOBRAGA - ADMIN TABLE FOOTER STANDARD V1
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function toSafeString_v1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function toInteger_v1(value, fallback) {
    const parsed = parseInt(value, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
  }

  function clamp_v1(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function escapeAttribute_v1(value) {
    return toSafeString_v1(value)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  //###################################################################################
  // (2) HTML REUTILIZAVEL PARA TABELAS GERADAS POR JAVASCRIPT
  //###################################################################################

  function buildFooterHtml_v1(config) {
    const safeConfig = config || {};
    const tableId = toSafeString_v1(safeConfig.tableId).trim();
    const pageSize = toInteger_v1(safeConfig.pageSize, 5);
    const ariaLabel = toSafeString_v1(safeConfig.ariaLabel || "Entradas por página");

    return [
      '<div class="admin-table-footer-standard-v1 table-footer admin-status-table-footer-v1" data-admin-table-footer-standard-v1="1"' + (tableId ? ' data-admin-table-id="' + escapeAttribute_v1(tableId) + '"' : "") + '>',
      '  <div class="admin-table-footer-page-size-v1">',
      '    <select class="admin-table-footer-page-size-select-v1" aria-label="' + escapeAttribute_v1(ariaLabel) + '" data-admin-table-footer-page-size-v1="1">',
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
  // (3) LOCALIZAR TABELA ASSOCIADA AO RODAPE
  //###################################################################################

  function findTableForFooter_v1(footerEl) {
    const tableId = toSafeString_v1(footerEl.dataset.adminTableId).trim();

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

    const cardEl = footerEl.closest(".card, section, .admin-subprocess-card-v1");

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

  function getTableRows_v1(tableEl) {
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
  // (4) RENDERIZAR PAGINACAO
  //###################################################################################

  function renderFooterState_v1(state) {
    const rows = getTableRows_v1(state.tableEl);
    const totalRows = rows.length;
    const totalPages = Math.max(1, Math.ceil(totalRows / state.pageSize));

    state.currentPage = clamp_v1(state.currentPage, 1, totalPages);

    const startIndex = (state.currentPage - 1) * state.pageSize;
    const endIndex = startIndex + state.pageSize;

    rows.forEach(function (rowEl, index) {
      rowEl.style.display = index >= startIndex && index < endIndex ? "" : "none";
    });

    state.pageEl.textContent = String(state.currentPage);
    state.prevEl.disabled = state.currentPage <= 1;
    state.nextEl.disabled = state.currentPage >= totalPages;
  }

  function initializeFooter_v1(footerEl) {
    if (!footerEl || footerEl.dataset.adminTableFooterInitializedV1 === "1") {
      return;
    }

    const tableEl = findTableForFooter_v1(footerEl);
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
      pageSize: toInteger_v1(pageSizeEl.value, 5)
    };

    pageSizeEl.addEventListener("change", function () {
      state.pageSize = toInteger_v1(pageSizeEl.value, 5);
      state.currentPage = 1;
      renderFooterState_v1(state);
    });

    prevEl.addEventListener("click", function () {
      if (state.currentPage > 1) {
        state.currentPage -= 1;
        renderFooterState_v1(state);
      }
    });

    nextEl.addEventListener("click", function () {
      state.currentPage += 1;
      renderFooterState_v1(state);
    });

    footerEl.dataset.adminTableFooterInitializedV1 = "1";
    renderFooterState_v1(state);
  }

  function initializeFooters_v1(rootEl) {
    const scopeEl = rootEl || document;
    const footers = Array.from(scopeEl.querySelectorAll("[data-admin-table-footer-standard-v1='1']"));

    footers.forEach(initializeFooter_v1);
  }

  //###################################################################################
  // (5) EXPOR API E INICIALIZAR
  //###################################################################################

  window.AppVerboAdminTableFooterStandard_v1 = {
    buildFooterHtml_v1: buildFooterHtml_v1,
    initializeFooters_v1: initializeFooters_v1
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initializeFooters_v1(document);
    });
  } else {
    initializeFooters_v1(document);
  }
})();
