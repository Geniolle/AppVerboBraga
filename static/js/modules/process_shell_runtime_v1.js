(function initAppVerboProcessShellRuntimeV1(global) {
  "use strict";

  if (
    global &&
    global.AppVerboProcessShell &&
    typeof global.AppVerboProcessShell.createProcessHeaderController === "function" &&
    typeof global.AppVerboProcessShell.createLoadMoreTableController === "function" &&
    typeof global.AppVerboProcessShell.enhanceLoadMoreTables === "function" &&
    typeof global.AppVerboProcessShell.createSearchableTableController === "function" &&
    typeof global.AppVerboProcessShell.enhanceSearchableTableCards === "function" &&
    typeof global.AppVerboProcessShell.createTableActionsMenuController === "function" &&
    typeof global.AppVerboProcessShell.enhanceTableActionMenus === "function"
  ) {
    return;
  }

  //###################################################################################
  // (1) ESTADO PARTILHADO
  //###################################################################################

  const DEFAULT_CARD_SELECTOR = ".card";
  const DEFAULT_ROWS_SELECTOR = "tbody tr";
  const DEFAULT_TABLE_SELECTOR = "table";
  const DEFAULT_FOOTER_SELECTOR = ".admin-status-table-footer-v1, .table-limiter";
  const DEFAULT_PAGE_SIZE = 5;
  const DEFAULT_PAGE_SIZE_OPTIONS = [5, 10, 20];
  const DEFAULT_SEARCH_DEBOUNCE_MS = 150;
  const DEFAULT_ACTIONS_SELECTOR = ".table-actions";

  const headerControllersByRoot = new WeakMap();
  const tableControllersByFooter = new WeakMap();
  const tableControllersByTable = new WeakMap();
  const searchControllersByCard = new WeakMap();
  const searchControllersByTable = new WeakMap();
  const actionMenuControllersByTable = new WeakMap();
  const actionMenuInstancesByContainer = new WeakMap();

  let rowActionsDelegationReady = false;
  let currentOpenActionMenuInstance = null;

  //###################################################################################
  // (2) UTILITÁRIOS
  //###################################################################################

  function normalizeText(value, fallback) {
    const safeFallback = typeof fallback === "string" ? fallback : "";
    if (typeof value !== "string") {
      return safeFallback;
    }

    const normalizedValue = value.trim();
    return normalizedValue || safeFallback;
  }

  function normalizeActions(actions) {
    if (!actions) {
      return [];
    }

    return Array.isArray(actions) ? actions.filter(Boolean) : [actions];
  }

  function parsePositiveInteger(value, fallback) {
    const parsedValue = Number.parseInt(value, 10);
    if (Number.isFinite(parsedValue) && parsedValue > 0) {
      return parsedValue;
    }

    return fallback;
  }

  function normalizeSearchText(value) {
    const safeValue = typeof value === "string" ? value : "";
    const collapsedValue = safeValue.replace(/\s+/g, " ").trim().toLowerCase();

    if (typeof collapsedValue.normalize !== "function") {
      return collapsedValue;
    }

    return collapsedValue.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function debounce(callback, waitMs) {
    const safeCallback = typeof callback === "function" ? callback : function noop() {};
    const safeWaitMs = parsePositiveInteger(waitMs, DEFAULT_SEARCH_DEBOUNCE_MS);
    let timeoutId = 0;

    return function debouncedCallback(...args) {
      const context = this;
      global.clearTimeout(timeoutId);
      timeoutId = global.setTimeout(() => {
        safeCallback.apply(context, args);
      }, safeWaitMs);
    };
  }

  function getChildElements(parentEl) {
    if (!parentEl || !parentEl.children) {
      return [];
    }

    return Array.from(parentEl.children);
  }

  function findDirectChildElement(parentEl, predicate) {
    if (!parentEl || typeof predicate !== "function") {
      return null;
    }

    return getChildElements(parentEl).find((childEl) => {
      return Boolean(predicate(childEl));
    }) || null;
  }

  function ensureDefaultPageSizeOptions(selectEl) {
    if (!selectEl || selectEl.options.length > 1) {
      return;
    }

    const currentValue = parsePositiveInteger(
      selectEl.value || (selectEl.options[0] ? selectEl.options[0].textContent : ""),
      DEFAULT_PAGE_SIZE
    );

    const existingValues = new Set(
      Array.from(selectEl.options).map((optionEl) => {
        return String(parsePositiveInteger(optionEl.value || optionEl.textContent, currentValue));
      })
    );

    DEFAULT_PAGE_SIZE_OPTIONS.forEach((pageSizeValue) => {
      const stringValue = String(pageSizeValue);
      if (existingValues.has(stringValue)) {
        return;
      }

      const optionEl = selectEl.ownerDocument.createElement("option");
      optionEl.value = stringValue;
      optionEl.textContent = stringValue;
      selectEl.appendChild(optionEl);
    });

    selectEl.value = String(currentValue);
  }

  function resolveEntriesPerPageLabel(footerEl, fallbackLabel) {
    const labelCandidates = Array.from(footerEl.querySelectorAll("span"));
    const matchingLabel = labelCandidates.find((candidateEl) => {
      const text = normalizeText(candidateEl.textContent, "");
      return /entradas\s+por\s+página/i.test(text);
    });

    return normalizeText(matchingLabel ? matchingLabel.textContent : "", fallbackLabel);
  }

  function resolveAssociatedTable(footerEl, tableSelector) {
    if (!footerEl) {
      return null;
    }

    const selector = normalizeText(tableSelector, DEFAULT_TABLE_SELECTOR);
    const ownerDocument = footerEl.ownerDocument || global.document;

    if (footerEl.dataset && footerEl.dataset.appverboTableId && ownerDocument) {
      const explicitTable = ownerDocument.getElementById(footerEl.dataset.appverboTableId);
      if (explicitTable) {
        return explicitTable;
      }
    }

    if (footerEl.id && /-limiter$/.test(footerEl.id) && ownerDocument) {
      const implicitTable = ownerDocument.getElementById(footerEl.id.replace(/-limiter$/, "-table"));
      if (implicitTable) {
        return implicitTable;
      }
    }

    let siblingEl = footerEl.previousElementSibling;
    while (siblingEl) {
      if (typeof siblingEl.matches === "function" && siblingEl.matches(selector)) {
        return siblingEl;
      }
      siblingEl = siblingEl.previousElementSibling;
    }

    const parentEl = footerEl.parentElement;
    if (parentEl) {
      const parentTables = parentEl.querySelectorAll(selector);
      if (parentTables.length === 1) {
        return parentTables[0];
      }
    }

    const cardEl = typeof footerEl.closest === "function" ? footerEl.closest(DEFAULT_CARD_SELECTOR) : null;
    return cardEl ? cardEl.querySelector(selector) : null;
  }

  function resolveTableBody(tableEl) {
    if (!tableEl) {
      return null;
    }

    if (tableEl.tBodies && tableEl.tBodies.length) {
      return tableEl.tBodies[0];
    }

    return tableEl.querySelector("tbody");
  }

  function resolveTableColumnCount(tableEl) {
    if (!tableEl) {
      return 1;
    }

    const headerRow = tableEl.tHead ? tableEl.tHead.rows[tableEl.tHead.rows.length - 1] : null;
    if (headerRow && headerRow.cells && headerRow.cells.length) {
      return headerRow.cells.length;
    }

    const bodyRow = tableEl.querySelector("tbody tr");
    if (bodyRow && bodyRow.children && bodyRow.children.length) {
      return bodyRow.children.length;
    }

    return 1;
  }

  function resolveDirectCardHeader(cardEl) {
    return findDirectChildElement(cardEl, (childEl) => {
      return childEl.classList && childEl.classList.contains("appverbo-card-header-v1");
    });
  }

  function resolveDirectCardTitle(cardEl) {
    const directHeaderEl = resolveDirectCardHeader(cardEl);
    if (directHeaderEl) {
      return directHeaderEl.querySelector("h2");
    }

    return findDirectChildElement(cardEl, (childEl) => {
      return childEl.tagName === "H2";
    });
  }

  function resolveDirectEmptyState(cardEl) {
    return findDirectChildElement(cardEl, (childEl) => {
      return typeof childEl.matches === "function" && childEl.matches(".empty");
    });
  }

  function getActionDescriptorText(elementEl) {
    if (!elementEl) {
      return "";
    }

    const directText = normalizeText(elementEl.getAttribute("title"), "")
      || normalizeText(elementEl.getAttribute("aria-label"), "")
      || normalizeText(elementEl.textContent, "");

    const classText = typeof elementEl.className === "string" ? elementEl.className : "";
    return `${directText} ${classText}`.trim();
  }

  function resolveActionKind(elementEl) {
    const descriptorText = normalizeSearchText(getActionDescriptorText(elementEl));

    if (
      /eliminar|excluir|apagar|remover|delete|danger/.test(descriptorText)
      || (elementEl.classList && elementEl.classList.contains("table-icon-btn-danger"))
    ) {
      return "delete";
    }

    if (
      /modificar|editar|edit|atualizar|actualizar/.test(descriptorText)
    ) {
      return "edit";
    }

    if (
      /exibir|ver|visualizar|detalhe|detalhes|view/.test(descriptorText)
    ) {
      return "view";
    }

    return "custom";
  }

  function resolveActionLabel(actionKind, elementEl, labels) {
    if (actionKind === "view") {
      return labels.view;
    }

    if (actionKind === "edit") {
      return labels.edit;
    }

    if (actionKind === "delete") {
      return labels.delete;
    }

    return normalizeText(getActionDescriptorText(elementEl), labels.fallback);
  }

  function closeCurrentActionMenu(options) {
    if (!currentOpenActionMenuInstance) {
      return;
    }

    const safeOptions = options && typeof options === "object" ? options : {};
    const instance = currentOpenActionMenuInstance;
    currentOpenActionMenuInstance = null;

    if (instance.popupEl) {
      instance.popupEl.hidden = true;
    }

    if (instance.triggerEl) {
      instance.triggerEl.setAttribute("aria-expanded", "false");
      if (safeOptions.restoreFocus) {
        instance.triggerEl.focus();
      }
    }
  }

  function openActionMenu(instance) {
    if (!instance || !instance.popupEl || !instance.triggerEl) {
      return;
    }

    if (currentOpenActionMenuInstance && currentOpenActionMenuInstance !== instance) {
      closeCurrentActionMenu();
    }

    currentOpenActionMenuInstance = instance;
    instance.popupEl.hidden = false;
    instance.triggerEl.setAttribute("aria-expanded", "true");
  }

  function toggleActionMenu(instance) {
    if (!instance || !instance.popupEl) {
      return;
    }

    if (currentOpenActionMenuInstance === instance && !instance.popupEl.hidden) {
      closeCurrentActionMenu({ restoreFocus: true });
      return;
    }

    openActionMenu(instance);
  }

  function ensureRowActionsDelegation(ownerDocument) {
    if (!ownerDocument || rowActionsDelegationReady) {
      return;
    }

    ownerDocument.addEventListener("click", (event) => {
      const targetEl = event.target;
      if (!(targetEl instanceof Element)) {
        closeCurrentActionMenu();
        return;
      }

      const triggerEl = targetEl.closest(".appverbo-row-actions-trigger-v1");
      if (triggerEl) {
        const containerEl = triggerEl.closest(`${DEFAULT_ACTIONS_SELECTOR}.appverbo-row-actions-ready-v1`);
        const instance = containerEl ? actionMenuInstancesByContainer.get(containerEl) : null;
        if (instance) {
          event.preventDefault();
          event.stopPropagation();
          toggleActionMenu(instance);
        }
        return;
      }

      const activePopupEl = targetEl.closest(".appverbo-row-actions-popup-v1");
      if (activePopupEl) {
        const actionableEl = targetEl.closest("a, button");
        if (actionableEl) {
          closeCurrentActionMenu();
        }
        return;
      }

      closeCurrentActionMenu();
    });

    ownerDocument.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") {
        return;
      }

      if (!currentOpenActionMenuInstance) {
        return;
      }

      event.preventDefault();
      closeCurrentActionMenu({ restoreFocus: true });
    });

    rowActionsDelegationReady = true;
  }

  function createActionElement(action, ownerDocument) {
    if (!action || !ownerDocument) {
      return null;
    }

    if (global.Node && action instanceof global.Node) {
      return action;
    }

    if (typeof action === "string") {
      const textEl = ownerDocument.createElement("span");
      textEl.textContent = action;
      return textEl;
    }

    if (typeof action !== "object") {
      return null;
    }

    let elementEl = null;
    if (global.Node && action.element instanceof global.Node) {
      elementEl = action.element;
    } else if (action.href) {
      elementEl = ownerDocument.createElement("a");
      elementEl.href = action.href;
    } else {
      elementEl = ownerDocument.createElement("button");
      elementEl.type = "button";
    }

    if (action.className) {
      elementEl.className = action.className;
    }

    if (action.label) {
      elementEl.textContent = action.label;
    }

    if (action.title) {
      elementEl.title = action.title;
    }

    if (action.target && elementEl.tagName === "A") {
      elementEl.target = action.target;
    }

    if (action.rel && elementEl.tagName === "A") {
      elementEl.rel = action.rel;
    }

    if (action.ariaLabel) {
      elementEl.setAttribute("aria-label", action.ariaLabel);
    }

    if (action.dataset && typeof action.dataset === "object") {
      Object.keys(action.dataset).forEach((key) => {
        elementEl.dataset[key] = String(action.dataset[key]);
      });
    }

    if (typeof action.onClick === "function") {
      elementEl.addEventListener("click", action.onClick);
    }

    return elementEl;
  }

  //###################################################################################
  // (3) CONTROLLER DO CABEÇALHO DO PROCESSO
  //###################################################################################

  function createProcessHeaderController(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const rootEl = safeConfig.root || null;
    const titleEl = safeConfig.titleEl || null;
    const actionsEl = safeConfig.actionsEl || null;
    const getTitle = typeof safeConfig.getTitle === "function" ? safeConfig.getTitle : null;
    const getActions = typeof safeConfig.getActions === "function" ? safeConfig.getActions : null;

    if (rootEl && headerControllersByRoot.has(rootEl)) {
      return headerControllersByRoot.get(rootEl);
    }

    let destroyed = false;
    let currentTitle = normalizeText(getTitle ? getTitle() : "", "Processo");
    let currentActions = normalizeActions(getActions ? getActions() : []);

    function renderTitle() {
      if (!titleEl) {
        return;
      }

      titleEl.textContent = normalizeText(currentTitle, "Processo");
    }

    function renderActions() {
      if (!actionsEl) {
        return;
      }

      actionsEl.textContent = "";
      const normalizedActions = normalizeActions(currentActions);
      if (!normalizedActions.length) {
        actionsEl.hidden = true;
        return;
      }

      const fragment = actionsEl.ownerDocument.createDocumentFragment();
      normalizedActions.forEach((action) => {
        const actionEl = createActionElement(action, actionsEl.ownerDocument);
        if (actionEl) {
          fragment.appendChild(actionEl);
        }
      });

      actionsEl.appendChild(fragment);
      actionsEl.hidden = !actionsEl.childNodes.length;
    }

    function setTitle(nextTitle) {
      if (destroyed) {
        return;
      }

      currentTitle = normalizeText(nextTitle, "Processo");
      renderTitle();
    }

    function setActions(nextActions) {
      if (destroyed) {
        return;
      }

      currentActions = normalizeActions(nextActions);
      renderActions();
    }

    function clear() {
      if (destroyed) {
        return;
      }

      currentTitle = normalizeText(getTitle ? getTitle() : "", "Processo");
      currentActions = [];
      renderTitle();
      renderActions();
    }

    function destroy() {
      if (destroyed) {
        return;
      }

      destroyed = true;

      if (titleEl) {
        titleEl.textContent = "";
      }

      if (actionsEl) {
        actionsEl.textContent = "";
        actionsEl.hidden = true;
      }

      if (rootEl) {
        headerControllersByRoot.delete(rootEl);
      }
    }

    const controller = {
      setTitle,
      setActions,
      clear,
      destroy
    };

    renderTitle();
    renderActions();

    if (rootEl) {
      headerControllersByRoot.set(rootEl, controller);
    }

    return controller;
  }

  //###################################################################################
  // (4) CONTROLLER DO FOOTER "MAIS"
  //###################################################################################

  function createLoadMoreTableController(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const tableEl = safeConfig.table || null;
    const footerEl = safeConfig.footer || null;
    const rowsSelector = normalizeText(safeConfig.rowsSelector, DEFAULT_ROWS_SELECTOR);

    if (!tableEl || !footerEl) {
      return null;
    }

    if (tableControllersByFooter.has(footerEl)) {
      return tableControllersByFooter.get(footerEl);
    }

    if (tableControllersByTable.has(tableEl)) {
      return tableControllersByTable.get(tableEl);
    }

    const labels = {
      entriesPerPage: "entradas por página",
      loadMore: "Mais",
      ...(safeConfig.labels && typeof safeConfig.labels === "object" ? safeConfig.labels : {})
    };

    let destroyed = false;
    let initialized = false;
    let allRows = [];
    let filteredRows = [];
    let activeFilter = null;
    let pageSizeSelectEl = safeConfig.pageSizeSelect || footerEl.querySelector("select") || null;
    let loadMoreButtonEl = safeConfig.loadMoreButton || footerEl.querySelector(".appverbo-load-more-btn-v1") || null;
    let counterEl = safeConfig.counterEl || footerEl.querySelector(".appverbo-load-more-counter-v1") || null;
    let pageSize = parsePositiveInteger(
      (pageSizeSelectEl && pageSizeSelectEl.value) || safeConfig.initialPageSize,
      DEFAULT_PAGE_SIZE
    );
    let visibleCount = 0;

    function recacheRows() {
      allRows = Array.from(tableEl.querySelectorAll(rowsSelector)).filter((rowEl) => {
        return !rowEl.classList.contains("appverbo-table-empty-search-row-v1");
      });
    }

    function resolveFilteredRows(filterSource) {
      if (Array.isArray(filterSource)) {
        const visibleRows = new Set(filterSource);
        return allRows.filter((rowEl) => visibleRows.has(rowEl));
      }

      if (typeof filterSource === "function") {
        return allRows.filter((rowEl, index) => filterSource(rowEl, index, allRows));
      }

      return allRows.slice();
    }

    function readPageSize() {
      return parsePositiveInteger(
        pageSizeSelectEl ? pageSizeSelectEl.value : safeConfig.initialPageSize,
        DEFAULT_PAGE_SIZE
      );
    }

    function ensureFooterStructure() {
      const ownerDocument = footerEl.ownerDocument || global.document;
      if (!ownerDocument) {
        return;
      }

      if (!pageSizeSelectEl) {
        pageSizeSelectEl = ownerDocument.createElement("select");
        const optionEl = ownerDocument.createElement("option");
        optionEl.value = String(DEFAULT_PAGE_SIZE);
        optionEl.textContent = String(DEFAULT_PAGE_SIZE);
        optionEl.selected = true;
        pageSizeSelectEl.appendChild(optionEl);
      }

      ensureDefaultPageSizeOptions(pageSizeSelectEl);

      const labelText = resolveEntriesPerPageLabel(footerEl, labels.entriesPerPage);
      const pageSizeWrapperEl = ownerDocument.createElement("div");
      pageSizeWrapperEl.className = "appverbo-load-more-page-size-v1";

      const pageSizeLabelEl = ownerDocument.createElement("span");
      pageSizeLabelEl.textContent = labelText;

      const statusWrapperEl = ownerDocument.createElement("div");
      statusWrapperEl.className = "appverbo-load-more-status-v1";

      if (!loadMoreButtonEl) {
        loadMoreButtonEl = ownerDocument.createElement("button");
      }

      loadMoreButtonEl.type = "button";
      loadMoreButtonEl.className = "appverbo-load-more-btn-v1";
      loadMoreButtonEl.textContent = labels.loadMore;

      if (!counterEl) {
        counterEl = ownerDocument.createElement("span");
      }

      counterEl.className = "appverbo-load-more-counter-v1";

      footerEl.textContent = "";
      footerEl.classList.add("appverbo-load-more-footer-v1");
      footerEl.dataset.appverboLoadMoreReady = "1";

      pageSizeWrapperEl.appendChild(pageSizeSelectEl);
      pageSizeWrapperEl.appendChild(pageSizeLabelEl);

      statusWrapperEl.appendChild(loadMoreButtonEl);
      statusWrapperEl.appendChild(counterEl);

      footerEl.appendChild(pageSizeWrapperEl);
      footerEl.appendChild(statusWrapperEl);
    }

    function updateCounterAndButton() {
      const totalRows = filteredRows.length;
      const safeVisibleCount = Math.min(Math.max(visibleCount, 0), totalRows);

      if (counterEl) {
        counterEl.textContent = `[ ${safeVisibleCount} / ${totalRows} ]`;
      }

      if (loadMoreButtonEl) {
        loadMoreButtonEl.textContent = labels.loadMore;
        loadMoreButtonEl.disabled = safeVisibleCount >= totalRows || totalRows === 0;
        loadMoreButtonEl.hidden = totalRows === 0;
        loadMoreButtonEl.setAttribute(
          "aria-disabled",
          safeVisibleCount >= totalRows || totalRows === 0 ? "true" : "false"
        );

        if (tableEl.id) {
          loadMoreButtonEl.setAttribute("aria-controls", tableEl.id);
        }
      }
    }

    function renderRows() {
      const visibleRows = new Set(filteredRows.slice(0, visibleCount));
      allRows.forEach((rowEl) => {
        rowEl.style.display = visibleRows.has(rowEl) ? "" : "none";
      });
    }

    function render() {
      if (destroyed) {
        return;
      }

      footerEl.hidden = allRows.length === 0;

      if (!allRows.length) {
        visibleCount = 0;
        updateCounterAndButton();
        return;
      }

      if (!filteredRows.length) {
        visibleCount = 0;
        renderRows();
        updateCounterAndButton();
        return;
      }

      if (visibleCount <= 0) {
        visibleCount = Math.min(filteredRows.length, pageSize);
      } else {
        visibleCount = Math.min(visibleCount, filteredRows.length);
      }

      renderRows();
      updateCounterAndButton();
    }

    function setRowsFilter(predicateOrRows, options) {
      if (destroyed) {
        return [];
      }

      const safeOptions = options && typeof options === "object" ? options : {};

      if (safeOptions.recacheRows) {
        recacheRows();
      }

      activeFilter = predicateOrRows || null;
      filteredRows = resolveFilteredRows(activeFilter);
      pageSize = readPageSize();

      if (safeOptions.preserveVisibleCount) {
        visibleCount = Math.min(Math.max(visibleCount, 0), filteredRows.length);
      } else {
        visibleCount = Math.min(filteredRows.length, pageSize);
      }

      render();
      return filteredRows.slice();
    }

    function clearRowsFilter(options) {
      return setRowsFilter(null, options);
    }

    function reset(options) {
      if (destroyed) {
        return;
      }

      const safeOptions = options && typeof options === "object" ? options : {};

      if (safeOptions.recacheRows) {
        recacheRows();
      }

      pageSize = readPageSize();

      if (safeOptions.preserveFilter !== false && activeFilter) {
        filteredRows = resolveFilteredRows(activeFilter);
      } else {
        activeFilter = null;
        filteredRows = allRows.slice();
      }

      if (safeOptions.preserveVisibleCount) {
        visibleCount = Math.min(Math.max(visibleCount, 0), filteredRows.length);
      } else {
        visibleCount = Math.min(filteredRows.length, pageSize);
      }

      render();
    }

    function loadMore() {
      if (destroyed || !filteredRows.length) {
        return;
      }

      visibleCount = Math.min(filteredRows.length, visibleCount + pageSize);
      render();
    }

    function handlePageSizeChange() {
      pageSize = readPageSize();
      visibleCount = Math.min(filteredRows.length, pageSize);
      render();
    }

    function handleLoadMoreClick() {
      loadMore();
    }

    function init() {
      if (destroyed || initialized) {
        return;
      }

      ensureFooterStructure();
      recacheRows();
      filteredRows = allRows.slice();
      pageSize = readPageSize();

      if (pageSizeSelectEl) {
        pageSizeSelectEl.addEventListener("change", handlePageSizeChange);
      }

      if (loadMoreButtonEl) {
        loadMoreButtonEl.addEventListener("click", handleLoadMoreClick);
      }

      initialized = true;
      reset();
    }

    function destroy() {
      if (destroyed) {
        return;
      }

      if (pageSizeSelectEl) {
        pageSizeSelectEl.removeEventListener("change", handlePageSizeChange);
      }

      if (loadMoreButtonEl) {
        loadMoreButtonEl.removeEventListener("click", handleLoadMoreClick);
      }

      destroyed = true;
      initialized = false;
      footerEl.dataset.appverboLoadMoreReady = "0";
      tableControllersByFooter.delete(footerEl);
      tableControllersByTable.delete(tableEl);
    }

    const controller = {
      init,
      render,
      loadMore,
      reset,
      setRowsFilter,
      clearRowsFilter,
      getAllRows: () => allRows.slice(),
      getFilteredRows: () => filteredRows.slice(),
      getPageSize: () => pageSize,
      getVisibleCount: () => Math.min(visibleCount, filteredRows.length),
      getFooter: () => footerEl,
      getTable: () => tableEl,
      destroy
    };

    tableControllersByFooter.set(footerEl, controller);
    tableControllersByTable.set(tableEl, controller);

    return controller;
  }

  //###################################################################################
  // (5) CONTROLLER DA PESQUISA DOS CARDS COM TABELA
  //###################################################################################

  function createSearchableTableController(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const cardEl = safeConfig.card || null;
    const tableEl = safeConfig.table || null;
    const titleEl = safeConfig.titleEl || null;
    const inputEl = safeConfig.input || null;
    const onFilterChange =
      typeof safeConfig.onFilterChange === "function" ? safeConfig.onFilterChange : null;
    const rowsSelector = normalizeText(safeConfig.rowsSelector, DEFAULT_ROWS_SELECTOR);

    if (!cardEl || !tableEl || !titleEl || !inputEl) {
      return null;
    }

    if (searchControllersByCard.has(cardEl)) {
      return searchControllersByCard.get(cardEl);
    }

    if (searchControllersByTable.has(tableEl)) {
      return searchControllersByTable.get(tableEl);
    }

    const labels = {
      placeholder: "Pesquisar...",
      searchInPrefix: "Pesquisar em",
      empty: "Nenhum resultado encontrado.",
      ...(safeConfig.labels && typeof safeConfig.labels === "object" ? safeConfig.labels : {})
    };

    const debounceMs = parsePositiveInteger(safeConfig.debounceMs, DEFAULT_SEARCH_DEBOUNCE_MS);

    let destroyed = false;
    let currentQuery = normalizeText(inputEl.value, "");
    let rowIndex = [];
    let emptyRowEl = null;

    function ensureInputState() {
      const titleText = normalizeText(titleEl.textContent, "resultados");
      inputEl.type = "search";
      inputEl.placeholder = normalizeText(labels.placeholder, "Pesquisar...");
      inputEl.setAttribute("aria-label", `${labels.searchInPrefix} ${titleText}`);
    }

    function buildRowIndex() {
      rowIndex = Array.from(tableEl.querySelectorAll(rowsSelector))
        .filter((rowEl) => !rowEl.classList.contains("appverbo-table-empty-search-row-v1"))
        .map((rowEl) => {
          return {
            rowEl,
            searchText: normalizeSearchText(rowEl.textContent || "")
          };
        });
    }

    function removeEmptyRow() {
      if (emptyRowEl && emptyRowEl.parentNode) {
        emptyRowEl.parentNode.removeChild(emptyRowEl);
      }
    }

    function ensureEmptyRow() {
      const tbodyEl = resolveTableBody(tableEl);
      if (!tbodyEl) {
        return;
      }

      if (!emptyRowEl) {
        emptyRowEl = tbodyEl.ownerDocument.createElement("tr");
        emptyRowEl.className = "appverbo-table-empty-search-row-v1";

        const cellEl = tbodyEl.ownerDocument.createElement("td");
        emptyRowEl.appendChild(cellEl);
      }

      const cellEl = emptyRowEl.firstElementChild;
      if (cellEl) {
        cellEl.colSpan = resolveTableColumnCount(tableEl);
        cellEl.textContent = labels.empty;
      }

      if (!emptyRowEl.parentNode) {
        tbodyEl.appendChild(emptyRowEl);
      }
    }

    function resolveLoadMoreController() {
      const existingController = tableControllersByTable.get(tableEl);
      if (existingController) {
        return existingController;
      }

      const cardRoot = cardEl || (typeof tableEl.closest === "function" ? tableEl.closest(DEFAULT_CARD_SELECTOR) : null);
      const createdControllers = enhanceLoadMoreTables({
        root: cardRoot || tableEl.parentElement || tableEl.ownerDocument,
        rowsSelector
      });

      if (Array.isArray(createdControllers) && createdControllers.length) {
        return tableControllersByTable.get(tableEl) || createdControllers[0] || null;
      }

      return tableControllersByTable.get(tableEl) || null;
    }

    function applyFilter(searchValue) {
      if (destroyed) {
        return [];
      }

      currentQuery = typeof searchValue === "string" ? searchValue : "";

      const normalizedQuery = normalizeSearchText(currentQuery);
      const filteredRows = normalizedQuery
        ? rowIndex
            .filter((entry) => entry.searchText.includes(normalizedQuery))
            .map((entry) => entry.rowEl)
        : rowIndex.map((entry) => entry.rowEl);

      removeEmptyRow();

      const loadMoreController = resolveLoadMoreController();
      if (loadMoreController && typeof loadMoreController.setRowsFilter === "function") {
        if (normalizedQuery) {
          loadMoreController.setRowsFilter(filteredRows, { preserveVisibleCount: false });
        } else if (typeof loadMoreController.clearRowsFilter === "function") {
          loadMoreController.clearRowsFilter({ preserveVisibleCount: false });
        } else {
          loadMoreController.setRowsFilter(null, { preserveVisibleCount: false });
        }
      } else {
        const visibleRows = new Set(filteredRows);
        rowIndex.forEach((entry) => {
          entry.rowEl.style.display = visibleRows.has(entry.rowEl) ? "" : "none";
        });
      }

      if (!filteredRows.length && rowIndex.length) {
        ensureEmptyRow();
      }

      if (onFilterChange) {
        onFilterChange({
          query: currentQuery,
          normalizedQuery,
          rows: filteredRows.slice(),
          totalRows: rowIndex.length
        });
      }

      return filteredRows;
    }

    const handleInput = debounce(function handleInputDebounced() {
      if (destroyed) {
        return;
      }

      applyFilter(inputEl.value);
    }, debounceMs);

    function refresh(options) {
      if (destroyed) {
        return;
      }

      const safeOptions = options && typeof options === "object" ? options : {};
      buildRowIndex();

      const loadMoreController = resolveLoadMoreController();
      if (loadMoreController && typeof loadMoreController.reset === "function") {
        loadMoreController.reset({
          recacheRows: true,
          preserveFilter: true,
          preserveVisibleCount: false
        });
      }

      if (safeOptions.syncInputValue) {
        currentQuery = normalizeText(inputEl.value, "");
      }

      applyFilter(inputEl.value || currentQuery);
    }

    function clear() {
      if (destroyed) {
        return;
      }

      inputEl.value = "";
      applyFilter("");
    }

    function destroy() {
      if (destroyed) {
        return;
      }

      inputEl.removeEventListener("input", handleInput);
      removeEmptyRow();
      destroyed = true;
      searchControllersByCard.delete(cardEl);
      searchControllersByTable.delete(tableEl);
    }

    const controller = {
      applyFilter,
      refresh,
      clear,
      destroy,
      getInput: () => inputEl,
      getQuery: () => currentQuery,
      getRows: () => rowIndex.map((entry) => entry.rowEl)
    };

    ensureInputState();
    buildRowIndex();
    inputEl.addEventListener("input", handleInput);
    applyFilter(currentQuery);

    searchControllersByCard.set(cardEl, controller);
    searchControllersByTable.set(tableEl, controller);

    return controller;
  }

  //###################################################################################
  // (6) ESTRUTURA REUTILIZÁVEL DO CABEÇALHO DOS CARDS
  //###################################################################################

  function ensureCardHeaderStructure(cardEl, titleEl) {
    if (!cardEl || !titleEl) {
      return null;
    }

    const ownerDocument = cardEl.ownerDocument || global.document;
    if (!ownerDocument) {
      return null;
    }

    let headerEl = resolveDirectCardHeader(cardEl);
    if (!headerEl) {
      headerEl = ownerDocument.createElement("div");
      headerEl.className = "appverbo-card-header-v1";
      cardEl.insertBefore(headerEl, titleEl);
    }

    if (titleEl.parentElement !== headerEl) {
      headerEl.insertBefore(titleEl, headerEl.firstChild || null);
    }

    let actionsEl = findDirectChildElement(headerEl, (childEl) => {
      return childEl.classList && childEl.classList.contains("appverbo-card-header-actions-v1");
    });

    if (!actionsEl) {
      actionsEl = ownerDocument.createElement("div");
      actionsEl.className = "appverbo-card-header-actions-v1";
      headerEl.appendChild(actionsEl);
    }

    return {
      headerEl,
      actionsEl
    };
  }

  function ensureCardSearchInput(actionsEl, titleText, labels) {
    if (!actionsEl) {
      return null;
    }

    const ownerDocument = actionsEl.ownerDocument || global.document;
    if (!ownerDocument) {
      return null;
    }

    let searchWrapperEl = actionsEl.querySelector(".appverbo-card-search-v1");
    let inputEl = searchWrapperEl ? searchWrapperEl.querySelector("input[type='search'], input") : null;

    if (!searchWrapperEl) {
      searchWrapperEl = ownerDocument.createElement("label");
      searchWrapperEl.className = "appverbo-card-search-v1";

      const iconEl = ownerDocument.createElement("span");
      iconEl.className = "appverbo-card-search-icon-v1";
      iconEl.setAttribute("aria-hidden", "true");
      iconEl.textContent = "⌕";

      inputEl = ownerDocument.createElement("input");
      inputEl.type = "search";

      searchWrapperEl.appendChild(iconEl);
      searchWrapperEl.appendChild(inputEl);
      actionsEl.appendChild(searchWrapperEl);
    }

    if (!inputEl) {
      return null;
    }

    inputEl.placeholder = normalizeText(labels.placeholder, "Pesquisar...");
    inputEl.setAttribute(
      "aria-label",
      `${normalizeText(labels.searchInPrefix, "Pesquisar em")} ${normalizeText(titleText, "resultados")}`
    );

    actionsEl.hidden = false;
    return inputEl;
  }

  //###################################################################################
  // (7) INICIALIZAÇÃO AUTOMÁTICA DOS FOOTERS
  //###################################################################################

  function enhanceLoadMoreTables(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const rootNode = safeConfig.root || global.document;
    const footerSelector = normalizeText(safeConfig.footerSelector, DEFAULT_FOOTER_SELECTOR);
    const tableSelector = normalizeText(safeConfig.tableSelector, DEFAULT_TABLE_SELECTOR);

    if (!rootNode || typeof rootNode.querySelectorAll !== "function") {
      return [];
    }

    const footerEls = [];
    if (typeof rootNode.matches === "function" && rootNode.matches(footerSelector)) {
      footerEls.push(rootNode);
    }

    footerEls.push(...Array.from(rootNode.querySelectorAll(footerSelector)));

    return footerEls.reduce((controllers, footerEl) => {
      const tableEl = resolveAssociatedTable(footerEl, tableSelector);
      if (!tableEl) {
        return controllers;
      }

      let controller = tableControllersByFooter.get(footerEl) || tableControllersByTable.get(tableEl);
      if (!controller) {
        controller = createLoadMoreTableController({
          table: tableEl,
          footer: footerEl,
          rowsSelector: safeConfig.rowsSelector || DEFAULT_ROWS_SELECTOR,
          labels: safeConfig.labels
        });

        if (controller) {
          controller.init();
        }
      } else if (typeof controller.reset === "function") {
        controller.reset({
          recacheRows: true,
          preserveFilter: true,
          preserveVisibleCount: false
        });
      }

      if (controller) {
        controllers.push(controller);
      }

      return controllers;
    }, []);
  }

  //###################################################################################
  // (8) INICIALIZAÇÃO AUTOMÁTICA DA PESQUISA DOS CARDS
  //###################################################################################

  function enhanceSearchableTableCards(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const rootNode = safeConfig.root || global.document;
    const cardSelector = normalizeText(safeConfig.cardSelector, DEFAULT_CARD_SELECTOR);
    const tableSelector = normalizeText(safeConfig.tableSelector, DEFAULT_TABLE_SELECTOR);
    const rowsSelector = normalizeText(safeConfig.rowsSelector, DEFAULT_ROWS_SELECTOR);
    const skipSelector = normalizeText(safeConfig.skipSelector, "");

    if (!rootNode || typeof rootNode.querySelectorAll !== "function") {
      return [];
    }

    const cardEls = [];
    if (typeof rootNode.matches === "function" && rootNode.matches(cardSelector)) {
      cardEls.push(rootNode);
    }

    cardEls.push(...Array.from(rootNode.querySelectorAll(cardSelector)));

    return cardEls.reduce((controllers, cardEl) => {
      if (
        skipSelector &&
        typeof cardEl.matches === "function" &&
        cardEl.matches(skipSelector)
      ) {
        return controllers;
      }

      const titleEl = resolveDirectCardTitle(cardEl);
      const tableEl = cardEl.querySelector(tableSelector);
      const emptyStateEl = resolveDirectEmptyState(cardEl);
      const isListingCard = Boolean(titleEl && (tableEl || emptyStateEl));

      if (!isListingCard) {
        return controllers;
      }

      const headerParts = ensureCardHeaderStructure(cardEl, titleEl);
      if (!headerParts) {
        return controllers;
      }

      cardEl.classList.add("appverbo-searchable-card-v1");
      cardEl.dataset.appverboSearchableTable = tableEl ? "1" : "0";

      if (!tableEl) {
        headerParts.actionsEl.hidden = true;
        return controllers;
      }

      const inputEl = ensureCardSearchInput(
        headerParts.actionsEl,
        normalizeText(titleEl.textContent, "resultados"),
        {
          placeholder: "Pesquisar...",
          searchInPrefix: "Pesquisar em"
        }
      );

      if (!inputEl) {
        return controllers;
      }

      let controller = searchControllersByCard.get(cardEl) || searchControllersByTable.get(tableEl);
      if (!controller) {
        controller = createSearchableTableController({
          card: cardEl,
          table: tableEl,
          titleEl,
          input: inputEl,
          rowsSelector,
          labels: safeConfig.labels,
          onFilterChange: safeConfig.onFilterChange
        });
      } else if (typeof controller.refresh === "function") {
        controller.refresh({ syncInputValue: true });
      }

      if (controller) {
        controllers.push(controller);
      }

      return controllers;
    }, []);
  }

  //###################################################################################
  // (9) MENU REUTILIZÁVEL DA COLUNA AÇÕES
  //###################################################################################

  function normalizeActionItemElement(elementEl, label, actionKind) {
    if (!elementEl) {
      return null;
    }

    const baseClassName = "appverbo-row-actions-item-v1";
    const dangerClassName = actionKind === "delete" ? " appverbo-row-actions-danger-v1" : "";

    if (elementEl.tagName === "A" || elementEl.tagName === "BUTTON") {
      elementEl.className = `${baseClassName}${dangerClassName}`;
      elementEl.textContent = label;
      elementEl.setAttribute("role", "menuitem");
      elementEl.removeAttribute("aria-label");
      return elementEl;
    }

    if (elementEl.tagName === "INPUT") {
      elementEl.className = `${baseClassName}${dangerClassName}`;
      elementEl.value = label;
      elementEl.setAttribute("role", "menuitem");
      elementEl.removeAttribute("aria-label");
      return elementEl;
    }

    return null;
  }

  function createActionMenuInstance(actionsEl, labels) {
    if (!actionsEl || actionMenuInstancesByContainer.has(actionsEl)) {
      return actionMenuInstancesByContainer.get(actionsEl) || null;
    }

    const ownerDocument = actionsEl.ownerDocument || global.document;
    if (!ownerDocument) {
      return null;
    }

    const actionSources = getChildElements(actionsEl).filter((childEl) => {
      return typeof childEl.matches === "function" && childEl.matches("a, button, form");
    });

    if (!actionSources.length) {
      return null;
    }

    const wrapperEl = ownerDocument.createElement("div");
    wrapperEl.className = "appverbo-row-actions-menu-v1";

    const triggerEl = ownerDocument.createElement("button");
    triggerEl.type = "button";
    triggerEl.className = "appverbo-row-actions-trigger-v1";
    triggerEl.setAttribute("aria-haspopup", "menu");
    triggerEl.setAttribute("aria-expanded", "false");
    triggerEl.setAttribute("aria-label", labels.openMenu);
    triggerEl.title = labels.openMenu;
    triggerEl.textContent = "⋮";

    const popupEl = ownerDocument.createElement("div");
    popupEl.className = "appverbo-row-actions-popup-v1";
    popupEl.setAttribute("role", "menu");
    popupEl.hidden = true;

    actionSources.forEach((sourceEl) => {
      if (!sourceEl) {
        return;
      }

      if (sourceEl.tagName === "FORM") {
        const submitEl = sourceEl.querySelector("button, input[type='submit']");
        if (!submitEl) {
          return;
        }

        const actionKind = resolveActionKind(submitEl);
        const label = resolveActionLabel(actionKind, submitEl, labels);
        const normalizedSubmitEl = normalizeActionItemElement(submitEl, label, actionKind);
        if (!normalizedSubmitEl) {
          return;
        }

        sourceEl.classList.add("appverbo-row-actions-form-v1");
        popupEl.appendChild(sourceEl);
        return;
      }

      const actionKind = resolveActionKind(sourceEl);
      const label = resolveActionLabel(actionKind, sourceEl, labels);
      const normalizedItemEl = normalizeActionItemElement(sourceEl, label, actionKind);
      if (!normalizedItemEl) {
        return;
      }

      popupEl.appendChild(normalizedItemEl);
    });

    if (!popupEl.childElementCount) {
      return null;
    }

    wrapperEl.appendChild(triggerEl);
    wrapperEl.appendChild(popupEl);

    actionsEl.textContent = "";
    actionsEl.classList.add("appverbo-row-actions-ready-v1");
    actionsEl.dataset.appverboActionsMenuReady = "1";
    actionsEl.appendChild(wrapperEl);

    const instance = {
      containerEl: actionsEl,
      wrapperEl,
      triggerEl,
      popupEl
    };

    actionMenuInstancesByContainer.set(actionsEl, instance);
    ensureRowActionsDelegation(ownerDocument);
    return instance;
  }

  function createTableActionsMenuController(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const tableEl = safeConfig.table || null;
    const actionsSelector = normalizeText(safeConfig.actionsSelector, DEFAULT_ACTIONS_SELECTOR);

    if (!tableEl) {
      return null;
    }

    if (actionMenuControllersByTable.has(tableEl)) {
      return actionMenuControllersByTable.get(tableEl);
    }

    const labels = {
      openMenu: "Abrir ações",
      view: "Exibir detalhes",
      edit: "Editar informações",
      delete: "Eliminar",
      fallback: "Abrir ação",
      ...(safeConfig.labels && typeof safeConfig.labels === "object" ? safeConfig.labels : {})
    };

    let destroyed = false;

    function refresh() {
      if (destroyed) {
        return [];
      }

      const actionContainers = Array.from(tableEl.querySelectorAll(actionsSelector));
      return actionContainers.reduce((instances, actionsEl) => {
        if (
          actionsEl.dataset &&
          actionsEl.dataset.appverboActionsMenuReady === "1" &&
          actionMenuInstancesByContainer.has(actionsEl)
        ) {
          instances.push(actionMenuInstancesByContainer.get(actionsEl));
          return instances;
        }

        const instance = createActionMenuInstance(actionsEl, labels);
        if (instance) {
          instances.push(instance);
        }

        return instances;
      }, []);
    }

    function destroy() {
      destroyed = true;
      actionMenuControllersByTable.delete(tableEl);
      if (currentOpenActionMenuInstance && currentOpenActionMenuInstance.containerEl) {
        const ownerTableEl = currentOpenActionMenuInstance.containerEl.closest("table");
        if (ownerTableEl === tableEl) {
          closeCurrentActionMenu();
        }
      }
    }

    const controller = {
      refresh,
      destroy,
      getTable: () => tableEl
    };

    actionMenuControllersByTable.set(tableEl, controller);
    refresh();
    return controller;
  }

  function enhanceTableActionMenus(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const rootNode = safeConfig.root || global.document;
    const tableSelector = normalizeText(safeConfig.tableSelector, DEFAULT_TABLE_SELECTOR);
    const actionsSelector = normalizeText(safeConfig.actionsSelector, DEFAULT_ACTIONS_SELECTOR);
    const skipSelector = normalizeText(safeConfig.skipSelector, "");

    if (!rootNode || typeof rootNode.querySelectorAll !== "function") {
      return [];
    }

    const tableEls = [];
    if (typeof rootNode.matches === "function" && rootNode.matches(tableSelector)) {
      tableEls.push(rootNode);
    }

    tableEls.push(...Array.from(rootNode.querySelectorAll(tableSelector)));

    return tableEls.reduce((controllers, tableEl) => {
      if (
        skipSelector &&
        (
          (typeof tableEl.matches === "function" && tableEl.matches(skipSelector))
          || (typeof tableEl.closest === "function" && tableEl.closest(skipSelector))
        )
      ) {
        return controllers;
      }

      if (!tableEl.querySelector(actionsSelector)) {
        return controllers;
      }

      let controller = actionMenuControllersByTable.get(tableEl);
      if (!controller) {
        controller = createTableActionsMenuController({
          table: tableEl,
          actionsSelector,
          labels: safeConfig.labels
        });
      } else if (typeof controller.refresh === "function") {
        controller.refresh();
      }

      if (controller) {
        controllers.push(controller);
      }

      return controllers;
    }, []);
  }

  global.AppVerboProcessShell = {
    ...(global.AppVerboProcessShell || {}),
    createProcessHeaderController,
    createLoadMoreTableController,
    enhanceLoadMoreTables,
    createSearchableTableController,
    enhanceSearchableTableCards,
    createTableActionsMenuController,
    enhanceTableActionMenus
  };
})(typeof window !== "undefined" ? window : globalThis);
