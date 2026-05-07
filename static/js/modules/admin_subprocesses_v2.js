// APPVERBO_ADMIN_SUBPROCESSES_V2_START
(function () {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeTextV2(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  //###################################################################################
  // (2) VISUALIZAR DETALHES
  //###################################################################################

  function setupViewActionsV2() {
    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-v2-view]");

      if (!button) {
        return;
      }

      event.preventDefault();

      const title = button.getAttribute("data-view-title") || "Detalhes";
      const details = button.getAttribute("data-view-details") || "";

      alert(title + (details ? "\n" + details : ""));
    });
  }

  //###################################################################################
  // (3) CANCELAR CRIACAO
  //###################################################################################

  function setupCancelCreateV2() {
    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-v2-cancel-create]");

      if (!button) {
        return;
      }

      event.preventDefault();

      const form = button.closest("form");
      const details = button.closest("details");

      if (form) {
        form.reset();
      }

      if (details) {
        details.open = false;
      }
    });
  }

  //###################################################################################
  // (4) CONFIRMACAO
  //###################################################################################

  function setupConfirmActionsV2() {
    document.addEventListener("submit", function (event) {
      const submitter = event.submitter || document.activeElement;
      const message = submitter && submitter.getAttribute
        ? safeTextV2(submitter.getAttribute("data-confirm-message"))
        : "";

      if (message && !window.confirm(message)) {
        event.preventDefault();
      }
    }, true);
  }


  //###################################################################################
  // (5) PESQUISA NAS TABELAS
  //###################################################################################

  function normalizeSearchTextV2(value) {
    return safeTextV2(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getRowSearchTextV2(row) {
    if (!row) {
      return "";
    }

    if (!row.dataset.adminSubprocessSearchTextV2) {
      row.dataset.adminSubprocessSearchTextV2 = normalizeSearchTextV2(row.textContent);
    }

    return row.dataset.adminSubprocessSearchTextV2;
  }

  function ensureNoResultsElementV2(card) {
    let element = card.querySelector("[data-admin-subprocess-v2-no-search-results]");

    if (element) {
      return element;
    }

    element = document.createElement("p");
    element.className = "admin-subprocess-no-search-results-v2";
    element.dataset.adminSubprocessV2NoSearchResults = "1";
    element.textContent = "Sem resultados para a pesquisa.";

    const tableWrap = card.querySelector(".admin-subprocess-table-wrap-v2");

    if (tableWrap && tableWrap.parentNode) {
      tableWrap.parentNode.insertBefore(element, tableWrap.nextSibling);
    } else {
      card.appendChild(element);
    }

    return element;
  }

  function applyTableSearchV2(input) {
    const card = input.closest(".admin-subprocess-table-card-v2");

    if (!card) {
      return;
    }

    const query = normalizeSearchTextV2(input.value);
    const rows = Array.from(card.querySelectorAll("tbody tr"));
    let visibleCount = 0;

    rows.forEach(function (row) {
      const rowText = getRowSearchTextV2(row);
      const isVisible = !query || rowText.includes(query);

      row.hidden = !isVisible;
      row.style.display = isVisible ? "" : "none";

      if (isVisible) {
        visibleCount += 1;
      }
    });

    const noResults = ensureNoResultsElementV2(card);
    const hasNoResults = rows.length > 0 && visibleCount === 0;

    noResults.classList.toggle("is-visible", hasNoResults);

    const tableWrap = card.querySelector(".admin-subprocess-table-wrap-v2");

    if (tableWrap) {
      tableWrap.hidden = hasNoResults;
      tableWrap.style.display = hasNoResults ? "none" : "";
    }
  }

  function setupTableSearchV2() {
    document.addEventListener("input", function (event) {
      const input = event.target.closest("[data-admin-subprocess-v2-search]");

      if (!input) {
        return;
      }

      applyTableSearchV2(input);
    }, true);

    document.querySelectorAll("[data-admin-subprocess-v2-search]").forEach(function (input) {
      applyTableSearchV2(input);
    });
  }

  //###################################################################################
  // (5) INICIAR
  //###################################################################################

  function setupAdminSubprocessesV2() {
    if (window.__appverboAdminSubprocessesV2 === true) {
      return;
    }

    window.__appverboAdminSubprocessesV2 = true;

    setupViewActionsV2();
    setupCancelCreateV2();
    setupConfirmActionsV2();
    setupTableSearchV2();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAdminSubprocessesV2);
  } else {
    setupAdminSubprocessesV2();
  }
})();
// APPVERBO_ADMIN_SUBPROCESSES_V2_END
