//###################################################################################
// (ADMIN_TABLE_SEARCH_MANAGER_V1) TOOLBAR GLOBAL DE TOTAL E PESQUISA NAS LISTAGENS
//###################################################################################

(function setupAdminTableSearchManagerV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function normalizeSearchTextV1(value) {
    return String(value === null || value === undefined ? "" : value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function resolveNameColumnIndexV1(tableEl) {
    const headerCells = Array.from(tableEl.querySelectorAll("thead th"));
    if (!headerCells.length) {
      return 0;
    }
    const byNameIndex = headerCells.findIndex((cellEl) => {
      const text = normalizeSearchTextV1(cellEl.textContent || "");
      return text.includes("nome") || text.includes("name");
    });
    return byNameIndex >= 0 ? byNameIndex : 0;
  }

  //###################################################################################
  // (2) TOOLBAR
  //###################################################################################

  function buildToolbarV1() {
    const toolbarEl = document.createElement("div");
    toolbarEl.className = "admin-list-toolbar-v1";

    const totalEl = document.createElement("p");
    totalEl.className = "admin-list-total-v1";
    totalEl.textContent = "Total: 0";

    const searchWrapEl = document.createElement("div");
    searchWrapEl.className = "admin-list-search-wrap-v1";

    const inputEl = document.createElement("input");
    inputEl.type = "search";
    inputEl.className = "admin-list-search-input-v1";
    inputEl.placeholder = "Procurar";
    inputEl.setAttribute("aria-label", "Pesquisar por nome");

    searchWrapEl.appendChild(inputEl);
    toolbarEl.appendChild(totalEl);
    toolbarEl.appendChild(searchWrapEl);

    return { toolbarEl, totalEl, inputEl };
  }

  function updateToolbarTotalV1(totalEl, matchedCount, totalCount) {
    if (matchedCount === totalCount) {
      totalEl.textContent = `Total: ${totalCount}`;
      return;
    }
    totalEl.textContent = `Total: ${matchedCount} de ${totalCount}`;
  }

  //###################################################################################
  // (3) FILTRO
  //###################################################################################

  function applyFilterV1(tableEl, nameColumnIndex, queryValue) {
    const normalizedQuery = normalizeSearchTextV1(queryValue);
    const allRows = Array.from(tableEl.querySelectorAll("tbody tr"));

    if (!allRows.length) {
      tableEl.dispatchEvent(new CustomEvent("admin-table-filter-changed"));
      return { matchedCount: 0, totalCount: 0 };
    }

    if (!normalizedQuery) {
      allRows.forEach((rowEl) => {
        rowEl.dataset.adminSearchMatchV1 = "1";
        rowEl.style.display = "";
      });
      tableEl.dispatchEvent(new CustomEvent("admin-table-filter-changed"));
      return { matchedCount: allRows.length, totalCount: allRows.length };
    }

    let matchedCount = 0;
    allRows.forEach((rowEl) => {
      const cells = Array.from(rowEl.querySelectorAll("td"));
      const targetText = normalizeSearchTextV1(
        cells[nameColumnIndex] ? cells[nameColumnIndex].textContent || "" : rowEl.textContent || ""
      );
      const isMatch = targetText.includes(normalizedQuery);
      rowEl.dataset.adminSearchMatchV1 = isMatch ? "1" : "0";
      rowEl.style.display = isMatch ? "" : "none";
      if (isMatch) {
        matchedCount += 1;
      }
    });

    tableEl.dispatchEvent(new CustomEvent("admin-table-filter-changed"));
    return { matchedCount, totalCount: allRows.length };
  }

  //###################################################################################
  // (4) INICIALIZACAO
  //###################################################################################

  const selectors = [
    "#recent-entities-card",
    "#inactive-entities-card",
    "#admin-users-created-card",
    "#inactive-users-card",
    "#admin-user-shadow-readonly-card",
    "#admin-user-shadow-inactive-card",
    "[data-admin-subprocess-shadow='utilizador']",
    "[data-admin-subprocess-shadow='utilizador-inactive']",
    ".admin-user-shadow-readonly-card-v1",
    ".admin-subprocess-table-card-v1",
  ];

  const mountedCardStatesV1 = new WeakMap();

  function resolveTargetCardsV1(rootEl) {
    const scopeEl = rootEl || document;
    return selectors
      .flatMap((selector) => Array.from(scopeEl.querySelectorAll(selector)))
      .filter((cardEl, index, allCards) => allCards.indexOf(cardEl) === index);
  }

  function scheduleRefreshForCardV1(cardEl) {
    const state = mountedCardStatesV1.get(cardEl);
    if (!state) {
      return;
    }

    if (state.refreshTimer) {
      window.clearTimeout(state.refreshTimer);
    }

    state.refreshTimer = window.setTimeout(() => {
      state.refreshTimer = null;
      state.refresh();
    }, 60);
  }

  function mountSearchForCardV1(cardEl) {
    if (!cardEl || cardEl.dataset.adminListSearchMountedV1 === "1") {
      return;
    }

    const tableEl = cardEl.querySelector("table");
    if (!tableEl) {
      return;
    }

    const titleEl = cardEl.querySelector("h2");
    if (!titleEl) {
      return;
    }

    const { toolbarEl, totalEl, inputEl } = buildToolbarV1();
    titleEl.insertAdjacentElement("afterend", toolbarEl);

    //###################################################################################
    // (4.1) ESTADO DO CARD E RECALCULO DE TOTAL
    //###################################################################################

    const state = {
      tableEl,
      totalEl,
      inputEl,
      getNameColumnIndex: () => resolveNameColumnIndexV1(tableEl),
      refreshTimer: null,
      refresh: () => {
        const stats = applyFilterV1(tableEl, state.getNameColumnIndex(), inputEl.value || "");
        updateToolbarTotalV1(totalEl, stats.matchedCount, stats.totalCount);
      },
    };

    mountedCardStatesV1.set(cardEl, state);
    state.refresh();

    inputEl.addEventListener("input", () => {
      state.refresh();
    });

    tableEl.addEventListener("admin-table-data-changed", () => {
      scheduleRefreshForCardV1(cardEl);
    });

    const tbodyEl = tableEl.querySelector("tbody");
    if (tbodyEl) {
      const bodyObserver = new MutationObserver(() => {
        scheduleRefreshForCardV1(cardEl);
      });

      bodyObserver.observe(tbodyEl, {
        childList: true,
        subtree: true,
      });

      state.bodyObserver = bodyObserver;
    }

    cardEl.dataset.adminListSearchMountedV1 = "1";
  }

  function mountSearchToolbarsV1(rootEl) {
    resolveTargetCardsV1(rootEl).forEach(mountSearchForCardV1);
  }

  let observerTimerV1 = null;

  function scheduleMountV1() {
    if (observerTimerV1) {
      window.clearTimeout(observerTimerV1);
    }

    observerTimerV1 = window.setTimeout(() => {
      observerTimerV1 = null;
      mountSearchToolbarsV1(document);
    }, 80);
  }

  function startMutationObserverV1() {
    if (!document.body || window.AppVerboAdminTableSearchObserverStartedV1) {
      return;
    }

    const observer = new MutationObserver(() => {
      scheduleMountV1();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    window.AppVerboAdminTableSearchObserverStartedV1 = true;
  }

  mountSearchToolbarsV1(document);
  startMutationObserverV1();
})();
