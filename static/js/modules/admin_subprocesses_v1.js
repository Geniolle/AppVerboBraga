// APPVERBO_ADMIN_SUBPROCESSES_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) VISUALIZAR DETALHES GENERICO
  //###################################################################################

  function instalarVisualizarAdminSubprocessV1() {
    if (window.__appverboAdminSubprocessViewV1 === true) {
      return;
    }

    window.__appverboAdminSubprocessViewV1 = true;

    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-view]");

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
  // (2) ORDENACAO POR CLIQUE NO CABECALHO DA TABELA
  //###################################################################################

  function normalizarTextoAdminSubprocessV1(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  function obterRotuloCabecalhoAdminSubprocessV1(value) {
    const normalizedValue = normalizarTextoAdminSubprocessV1(value);

    if (normalizedValue === "numero da entidade") {
      return "N" + String.fromCharCode(186) + " DA ENTIDADE";
    }

    return String(value || "").trim();
  }

  function obterNumeroAdminSubprocessV1(value) {
    const textoLimpo = String(value || "")
      .replace(/\s+/g, "")
      .replace(/[^\d,.-]/g, "")
      .replace(/\.(?=\d{3}(\D|$))/g, "")
      .replace(",", ".");
    const numero = Number(textoLimpo);

    return Number.isFinite(numero) ? numero : 0;
  }

  function obterValorCelulaAdminSubprocessV1(row, columnIndex) {
    const cell = row.cells[columnIndex];
    return cell ? String(cell.dataset.sortValue || cell.textContent || "") : "";
  }

  function colunaNumericaAdminSubprocessV1(headerText) {
    const normalizedHeader = normalizarTextoAdminSubprocessV1(headerText);
    return normalizedHeader.includes("numero") || normalizedHeader.includes("n da entidade");
  }

  function compararLinhasAdminSubprocessV1(rowA, rowB, columnIndex, isNumericColumn) {
    const rawA = obterValorCelulaAdminSubprocessV1(rowA, columnIndex).trim();
    const rawB = obterValorCelulaAdminSubprocessV1(rowB, columnIndex).trim();
    const emptyA = rawA === "";
    const emptyB = rawB === "";

    if (emptyA !== emptyB) {
      return emptyA ? 1 : -1;
    }

    if (isNumericColumn) {
      return obterNumeroAdminSubprocessV1(rawA) - obterNumeroAdminSubprocessV1(rawB);
    }

    return normalizarTextoAdminSubprocessV1(rawA).localeCompare(
      normalizarTextoAdminSubprocessV1(rawB),
      "pt",
      { numeric: true, sensitivity: "base" }
    );
  }

  function atualizarIndicadoresAdminSubprocessV1(table, activeButton, direction) {
    table.querySelectorAll("[data-admin-subprocess-sort-button]").forEach(function (button) {
      const indicator = button.querySelector(".admin-subprocess-sort-indicator-v1");
      const header = button.closest("th");
      const isActive = button === activeButton;

      button.dataset.sortDirection = isActive ? direction : "none";

      if (indicator) {
        indicator.textContent = isActive ? (direction === "asc" ? "▲" : "▼") : "⇅";
      }

      if (header) {
        header.setAttribute("aria-sort", isActive ? (direction === "asc" ? "ascending" : "descending") : "none");
      }
    });
  }

  function ordenarTabelaAdminSubprocessV1(table, button) {
    const tbody = table.querySelector("tbody");
    const columnIndex = Number(button.dataset.sortIndex || "0");
    const headerText = button.dataset.sortHeader || button.textContent || "";
    const isNumericColumn = colunaNumericaAdminSubprocessV1(headerText);
    const currentDirection = button.dataset.sortDirection === "asc" ? "asc" : "desc";
    const nextDirection = currentDirection === "asc" ? "desc" : "asc";

    if (!tbody) {
      return;
    }

    const rows = Array.from(tbody.querySelectorAll("tr"));

    rows.forEach(function (row, rowIndex) {
      if (!row.dataset.adminSubprocessOriginalIndex) {
        row.dataset.adminSubprocessOriginalIndex = String(rowIndex);
      }
    });

    rows.sort(function (rowA, rowB) {
      let result = compararLinhasAdminSubprocessV1(rowA, rowB, columnIndex, isNumericColumn);

      if (result === 0) {
        result = Number(rowA.dataset.adminSubprocessOriginalIndex || "0") - Number(rowB.dataset.adminSubprocessOriginalIndex || "0");
      }

      return nextDirection === "asc" ? result : -result;
    });

    rows.forEach(function (row) {
      tbody.appendChild(row);
    });

    atualizarIndicadoresAdminSubprocessV1(table, button, nextDirection);
  }

  function prepararTabelaOrdenavelAdminSubprocessV1(table) {
    if (!table || table.dataset.adminSubprocessSortableReady === "true") {
      return;
    }

    const headers = Array.from(table.querySelectorAll("thead th"));

    headers.forEach(function (header, index) {
      const rawLabel = String(header.textContent || "").trim();
      const visibleLabel = obterRotuloCabecalhoAdminSubprocessV1(rawLabel);
      const normalizedLabel = normalizarTextoAdminSubprocessV1(rawLabel);
      const isActionsHeader = normalizedLabel === "acoes" || index === headers.length - 1;

      if (!rawLabel || isActionsHeader) {
        return;
      }

      const defaultDirection = colunaNumericaAdminSubprocessV1(rawLabel) ? "asc" : "none";
      const defaultIndicator = defaultDirection === "asc" ? "▲" : "⇅";
      const button = document.createElement("button");
      const labelSpan = document.createElement("span");
      const indicatorSpan = document.createElement("span");

      header.textContent = "";
      header.classList.add("admin-subprocess-sortable-th-v1");
      header.setAttribute("aria-sort", defaultDirection === "asc" ? "ascending" : "none");

      button.type = "button";
      button.className = "admin-subprocess-sort-btn-v1";
      button.dataset.adminSubprocessSortButton = "true";
      button.dataset.sortIndex = String(index);
      button.dataset.sortHeader = rawLabel;
      button.dataset.sortDirection = defaultDirection;
      button.setAttribute("aria-label", "Ordenar por " + visibleLabel);

      labelSpan.textContent = visibleLabel;

      indicatorSpan.className = "admin-subprocess-sort-indicator-v1";
      indicatorSpan.setAttribute("aria-hidden", "true");
      indicatorSpan.textContent = defaultIndicator;

      button.appendChild(labelSpan);
      button.appendChild(indicatorSpan);
      header.appendChild(button);
    });

    table.dataset.adminSubprocessSortableReady = "true";
  }

  function instalarOrdenacaoAdminSubprocessV1() {
    if (window.__appverboAdminSubprocessSortV1 === true) {
      document.querySelectorAll(".admin-subprocess-table-v1").forEach(prepararTabelaOrdenavelAdminSubprocessV1);
      return;
    }

    window.__appverboAdminSubprocessSortV1 = true;

    document.querySelectorAll(".admin-subprocess-table-v1").forEach(prepararTabelaOrdenavelAdminSubprocessV1);

    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-sort-button]");

      if (!button) {
        return;
      }

      const table = button.closest("table");

      if (!table) {
        return;
      }

      event.preventDefault();
      ordenarTabelaAdminSubprocessV1(table, button);
    });
  }

  //###################################################################################
  // (3) INICIAR
  //###################################################################################

  function iniciarAdminSubprocessV1() {
    instalarVisualizarAdminSubprocessV1();
    instalarOrdenacaoAdminSubprocessV1();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarAdminSubprocessV1);
  }
  else {
    iniciarAdminSubprocessV1();
  }
})();
// APPVERBO_ADMIN_SUBPROCESSES_V1_END
