// APPVERBO_ADMIN_SUBPROCESSES_V1_START
(function () {
  "use strict";

  const TEXTO_COLLATOR_ADMIN_SUBPROCESS_V1 = new Intl.Collator("pt", {
    numeric: true,
    sensitivity: "base"
  });

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

    if (!cell) {
      return "";
    }

    if (Object.prototype.hasOwnProperty.call(cell.dataset, "sortValue")) {
      return String(cell.dataset.sortValue || "");
    }

    return String(cell.textContent || "");
  }

  function colunaNumericaAdminSubprocessV1(headerText, columnKey) {
    const normalizedHeader = normalizarTextoAdminSubprocessV1(headerText);
    const normalizedKey = normalizarTextoAdminSubprocessV1(columnKey);

    return (
      normalizedKey === "id"
      || normalizedKey === "entity_number"
      || normalizedHeader === "id"
      || normalizedHeader.includes("numero")
      || normalizedHeader.includes("n da entidade")
    );
  }

  function normalizarDirecaoOrdenacaoAdminSubprocessV1(value) {
    const cleanValue = String(value || "").trim().toLowerCase();

    return cleanValue === "asc" || cleanValue === "desc" ? cleanValue : "none";
  }

  function obterConfiguracaoCabecalhoAdminSubprocessV1(header, index, headers, hasExplicitSortableHeaders) {
    const rawLabel = String(header.textContent || "").trim();
    const columnKey = String(header.dataset.appverboColumnKey || header.dataset.adminSubprocessColumnKey || "").trim();
    const normalizedLabel = normalizarTextoAdminSubprocessV1(rawLabel);
    const normalizedKey = normalizarTextoAdminSubprocessV1(columnKey);
    const isActionsHeader = normalizedKey === "actions" || normalizedLabel === "acoes" || index === headers.length - 1;
    const explicitSortable = header.dataset.appverboSortable === "1" || header.dataset.adminSubprocessSortable === "1";
    const isSortable = hasExplicitSortableHeaders ? explicitSortable : Boolean(rawLabel && !isActionsHeader);
    const configuredSortType = String(header.dataset.appverboSortType || header.dataset.adminSubprocessSortType || "").trim().toLowerCase();
    const isNumericColumn = configuredSortType === "number" || colunaNumericaAdminSubprocessV1(rawLabel, columnKey);
    const sortType = isNumericColumn ? "number" : "text";
    const configuredDefaultSort = normalizarDirecaoOrdenacaoAdminSubprocessV1(
      header.dataset.appverboDefaultSort || header.dataset.adminSubprocessDefaultSort || ""
    );
    const defaultSort = configuredDefaultSort !== "none"
      ? configuredDefaultSort
      : (!hasExplicitSortableHeaders && isNumericColumn ? "asc" : "none");

    return {
      rawLabel: rawLabel,
      visibleLabel: obterRotuloCabecalhoAdminSubprocessV1(rawLabel),
      columnKey: columnKey,
      isSortable: isSortable,
      sortType: sortType,
      defaultSort: defaultSort,
      isActionsHeader: isActionsHeader
    };
  }

  function compararItensOrdenacaoAdminSubprocessV1(itemA, itemB, sortType, direction) {
    if (itemA.empty !== itemB.empty) {
      return itemA.empty ? 1 : -1;
    }

    let result = 0;

    if (sortType === "number") {
      result = itemA.numberValue - itemB.numberValue;
    }
    else {
      result = TEXTO_COLLATOR_ADMIN_SUBPROCESS_V1.compare(itemA.textValue, itemB.textValue);
    }

    if (result === 0) {
      result = itemA.originalIndex - itemB.originalIndex;
    }

    return direction === "asc" ? result : -result;
  }

  function atualizarIndicadoresAdminSubprocessV1(table, activeButton, direction) {
    table.querySelectorAll("[data-admin-subprocess-sort-button]").forEach(function (button) {
      const indicator = button.querySelector(".admin-subprocess-sort-indicator-v1");
      const header = button.closest("th");
      const isActive = button === activeButton;

      button.dataset.sortDirection = isActive ? direction : "none";

      if (indicator) {
        indicator.textContent = "⇅";
      }

      if (header) {
        header.setAttribute("aria-sort", isActive ? (direction === "asc" ? "ascending" : "descending") : "none");
      }
    });
  }

  function aplicarOrdenacaoTabelaAdminSubprocessV1(table, button, direction) {
    const tbody = table.querySelector("tbody");
    const columnIndex = Number(button.dataset.sortIndex || "0");
    const sortType = button.dataset.sortType === "number" ? "number" : "text";
    const cleanDirection = direction === "desc" ? "desc" : "asc";

    if (!tbody) {
      return;
    }

    const rows = Array.from(tbody.rows);

    const sortableItems = rows.map(function (row, rowIndex) {
      if (!row.dataset.adminSubprocessOriginalIndex) {
        row.dataset.adminSubprocessOriginalIndex = String(rowIndex);
      }

      const rawValue = obterValorCelulaAdminSubprocessV1(row, columnIndex).trim();

      return {
        row: row,
        empty: rawValue === "",
        numberValue: sortType === "number" ? obterNumeroAdminSubprocessV1(rawValue) : 0,
        textValue: sortType === "text" ? normalizarTextoAdminSubprocessV1(rawValue) : "",
        originalIndex: Number(row.dataset.adminSubprocessOriginalIndex || String(rowIndex))
      };
    });

    sortableItems.sort(function (itemA, itemB) {
      return compararItensOrdenacaoAdminSubprocessV1(itemA, itemB, sortType, cleanDirection);
    });

    const fragment = document.createDocumentFragment();

    sortableItems.forEach(function (item) {
      fragment.appendChild(item.row);
    });

    tbody.appendChild(fragment);
    atualizarIndicadoresAdminSubprocessV1(table, button, cleanDirection);
  }

  function ordenarTabelaAdminSubprocessV1(table, button) {
    const currentDirection = button.dataset.sortDirection === "asc" ? "asc" : "desc";
    const nextDirection = currentDirection === "asc" ? "desc" : "asc";

    aplicarOrdenacaoTabelaAdminSubprocessV1(table, button, nextDirection);
  }

  function prepararTabelaOrdenavelAdminSubprocessV1(table) {
    if (!table || table.dataset.adminSubprocessSortableReady === "true") {
      return;
    }

    const headers = Array.from(table.querySelectorAll("thead th"));
    const hasExplicitSortableHeaders = headers.some(function (header) {
      return header.dataset.appverboSortable === "1" || header.dataset.adminSubprocessSortable === "1";
    });
    let defaultSortButton = null;
    let defaultSortDirection = "none";

    headers.forEach(function (header, index) {
      const config = obterConfiguracaoCabecalhoAdminSubprocessV1(
        header,
        index,
        headers,
        hasExplicitSortableHeaders
      );

      if (!config.rawLabel || !config.isSortable || config.isActionsHeader) {
        return;
      }

      const button = document.createElement("button");
      const labelSpan = document.createElement("span");
      const indicatorSpan = document.createElement("span");

      header.textContent = "";
      header.classList.add("admin-subprocess-sortable-th-v1");
      header.setAttribute("aria-sort", config.defaultSort === "asc" ? "ascending" : (config.defaultSort === "desc" ? "descending" : "none"));

      button.type = "button";
      button.className = "admin-subprocess-sort-btn-v1";
      button.dataset.adminSubprocessSortButton = "true";
      button.dataset.sortIndex = String(index);
      button.dataset.sortHeader = config.rawLabel;
      button.dataset.sortKey = config.columnKey;
      button.dataset.sortType = config.sortType;
      button.dataset.sortDirection = config.defaultSort;
      button.setAttribute("aria-label", "Ordenar por " + config.visibleLabel);

      labelSpan.textContent = config.visibleLabel;

      indicatorSpan.className = "admin-subprocess-sort-indicator-v1";
      indicatorSpan.setAttribute("aria-hidden", "true");
      indicatorSpan.textContent = "⇅";

      button.appendChild(labelSpan);
      button.appendChild(indicatorSpan);
      header.appendChild(button);

      if (!defaultSortButton && config.defaultSort !== "none") {
        defaultSortButton = button;
        defaultSortDirection = config.defaultSort;
      }
    });

    table.dataset.adminSubprocessSortableReady = "true";

    if (defaultSortButton && defaultSortDirection !== "none") {
      aplicarOrdenacaoTabelaAdminSubprocessV1(table, defaultSortButton, defaultSortDirection);
    }
  }

  function obterTabelasOrdenaveisAdminSubprocessV1() {
    return document.querySelectorAll(".admin-subprocess-table-v1, [data-appverbo-sortable-table='1']");
  }

  function instalarOrdenacaoAdminSubprocessV1() {
    if (window.__appverboAdminSubprocessSortV1 === true) {
      obterTabelasOrdenaveisAdminSubprocessV1().forEach(prepararTabelaOrdenavelAdminSubprocessV1);
      return;
    }

    window.__appverboAdminSubprocessSortV1 = true;

    obterTabelasOrdenaveisAdminSubprocessV1().forEach(prepararTabelaOrdenavelAdminSubprocessV1);

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
