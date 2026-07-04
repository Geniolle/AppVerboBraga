(function initAppGenesisProcessShellRuntimeV1(global) {
  "use strict";

  if (
    global &&
    global.AppGenesisProcessShell &&
    typeof global.AppGenesisProcessShell.createProcessHeaderController === "function" &&
    typeof global.AppGenesisProcessShell.createLoadMoreTableController === "function" &&
    typeof global.AppGenesisProcessShell.enhanceLoadMoreTables === "function" &&
    typeof global.AppGenesisProcessShell.createSearchableTableController === "function" &&
    typeof global.AppGenesisProcessShell.enhanceSearchableTableCards === "function" &&
    typeof global.AppGenesisProcessShell.createTableActionsMenuController === "function" &&
    typeof global.AppGenesisProcessShell.enhanceTableActionMenus === "function" &&
    typeof global.AppGenesisProcessShell.createConfirmDialogController === "function" &&
    typeof global.AppGenesisProcessShell.enhanceConfirmableActions === "function" &&
    typeof global.AppGenesisProcessShell.createToastController === "function" &&
    typeof global.AppGenesisProcessShell.showToast === "function" &&
    typeof global.AppGenesisProcessShell.enhanceFeedbackToasts === "function" &&
    typeof global.AppGenesisProcessShell.createResponsiveTableColumnsController === "function" &&
    typeof global.AppGenesisProcessShell.enhanceResponsiveTableColumns === "function"
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
  let confirmDelegationReady = false;
  let activeMenuScrollHandler = null;
  let activeMenuResizeHandler = null;
  let _feedbackToastController = null;

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

    if (footerEl.dataset && footerEl.dataset.appgenesisTableId && ownerDocument) {
      const explicitTable = ownerDocument.getElementById(footerEl.dataset.appgenesisTableId);
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
      return childEl.classList && childEl.classList.contains("appgenesis-card-header-v1");
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

  function getViewportSafeMenuPosition(triggerEl, popupEl) {
    const MARGIN = 8;
    const GAP = 6;
    const triggerRect = triggerEl.getBoundingClientRect();
    const popupRect = popupEl.getBoundingClientRect();
    const popupWidth = popupRect.width || popupEl.offsetWidth || 200;
    const popupHeight = popupRect.height || popupEl.offsetHeight || 120;
    const vw = global.innerWidth || 0;
    const vh = global.innerHeight || 0;

    let top = triggerRect.bottom + GAP;
    let left = triggerRect.right - popupWidth;

    if (top + popupHeight > vh - MARGIN) {
      const topAbove = triggerRect.top - popupHeight - GAP;
      top = topAbove >= MARGIN ? topAbove : Math.max(MARGIN, vh - popupHeight - MARGIN);
    }

    if (left < MARGIN) {
      left = MARGIN;
    }
    if (left + popupWidth > vw - MARGIN) {
      left = vw - popupWidth - MARGIN;
    }

    return { top, left };
  }

  function detachMenuPositionListeners() {
    if (activeMenuScrollHandler) {
      global.removeEventListener("scroll", activeMenuScrollHandler, true);
      activeMenuScrollHandler = null;
    }
    if (activeMenuResizeHandler) {
      global.removeEventListener("resize", activeMenuResizeHandler);
      activeMenuResizeHandler = null;
    }
  }

  function attachMenuPositionListeners() {
    detachMenuPositionListeners();
    activeMenuScrollHandler = function () {
      closeCurrentActionMenu();
    };
    activeMenuResizeHandler = function () {
      closeCurrentActionMenu();
    };
    global.addEventListener("scroll", activeMenuScrollHandler, true);
    global.addEventListener("resize", activeMenuResizeHandler);
  }

  function closeCurrentActionMenu(options) {
    if (!currentOpenActionMenuInstance) {
      return;
    }

    const safeOptions = options && typeof options === "object" ? options : {};
    const instance = currentOpenActionMenuInstance;
    currentOpenActionMenuInstance = null;

    detachMenuPositionListeners();

    if (instance.popupEl) {
      const popupEl = instance.popupEl;

      popupEl.hidden = true;
      popupEl.style.top = "";
      popupEl.style.left = "";
      popupEl.style.visibility = "";
      popupEl.classList.remove("appgenesis-row-actions-popup-floating-v1");

      const placeholder = instance._portalPlaceholder;
      const originalParent = instance._portalOriginalParent;

      if (placeholder && placeholder.parentNode) {
        placeholder.parentNode.insertBefore(popupEl, placeholder);
        placeholder.parentNode.removeChild(placeholder);
      } else if (originalParent) {
        originalParent.appendChild(popupEl);
      }

      instance._portalPlaceholder = null;
      instance._portalOriginalParent = null;
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

    const popupEl = instance.popupEl;
    const triggerEl = instance.triggerEl;
    const ownerDocument = triggerEl.ownerDocument || global.document;

    const originalParent = popupEl.parentNode;
    const placeholder = ownerDocument.createComment("appgenesis-popup-placeholder");
    if (originalParent) {
      originalParent.insertBefore(placeholder, popupEl);
    }

    instance._portalPlaceholder = placeholder;
    instance._portalOriginalParent = originalParent;

    ownerDocument.body.appendChild(popupEl);
    popupEl.classList.add("appgenesis-row-actions-popup-floating-v1");

    popupEl.style.visibility = "hidden";
    popupEl.hidden = false;

    const pos = getViewportSafeMenuPosition(triggerEl, popupEl);
    popupEl.style.top = pos.top + "px";
    popupEl.style.left = pos.left + "px";
    popupEl.style.visibility = "";

    triggerEl.setAttribute("aria-expanded", "true");
    attachMenuPositionListeners();
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

      const triggerEl = targetEl.closest(".appgenesis-row-actions-trigger-v1");
      if (triggerEl) {
        const containerEl = triggerEl.closest(`${DEFAULT_ACTIONS_SELECTOR}.appgenesis-row-actions-ready-v1`);
        const instance = containerEl ? actionMenuInstancesByContainer.get(containerEl) : null;
        if (instance) {
          event.preventDefault();
          event.stopPropagation();
          toggleActionMenu(instance);
        }
        return;
      }

      const activePopupEl = targetEl.closest(".appgenesis-row-actions-popup-v1");
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
      loadLess: "Menos",
      ...(safeConfig.labels && typeof safeConfig.labels === "object" ? safeConfig.labels : {})
    };

    let destroyed = false;
    let initialized = false;
    let allRows = [];
    let filteredRows = [];
    let activeFilter = null;
    let pageSizeSelectEl = safeConfig.pageSizeSelect || footerEl.querySelector("select") || null;
    let loadMoreButtonEl = safeConfig.loadMoreButton || footerEl.querySelector(".appgenesis-load-more-btn-v1") || null;
    let loadLessButtonEl = safeConfig.loadLessButton || null;
    let counterEl = safeConfig.counterEl || footerEl.querySelector(".appgenesis-load-more-counter-v1") || null;
    let pageSize = parsePositiveInteger(
      (pageSizeSelectEl && pageSizeSelectEl.value) || safeConfig.initialPageSize,
      DEFAULT_PAGE_SIZE
    );
    let visibleCount = 0;

    function recacheRows() {
      allRows = Array.from(tableEl.querySelectorAll(rowsSelector)).filter((rowEl) => {
        return !rowEl.classList.contains("appgenesis-table-empty-search-row-v1");
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
      pageSizeWrapperEl.className = "appgenesis-load-more-page-size-v1";

      const pageSizeLabelEl = ownerDocument.createElement("span");
      pageSizeLabelEl.textContent = labelText;

      const statusWrapperEl = ownerDocument.createElement("div");
      statusWrapperEl.className = "appgenesis-load-more-status-v1";

      const loadLessWrapperEl = ownerDocument.createElement("div");
      loadLessWrapperEl.className = "appgenesis-load-more-less-v1";

      if (!loadLessButtonEl) {
        loadLessButtonEl = ownerDocument.createElement("button");
      }

      loadLessButtonEl.type = "button";
      loadLessButtonEl.className = "appgenesis-load-more-btn-v1";
      loadLessButtonEl.textContent = labels.loadLess;

      if (!loadMoreButtonEl) {
        loadMoreButtonEl = ownerDocument.createElement("button");
      }

      loadMoreButtonEl.type = "button";
      loadMoreButtonEl.className = "appgenesis-load-more-btn-v1";
      loadMoreButtonEl.textContent = labels.loadMore;

      if (!counterEl) {
        counterEl = ownerDocument.createElement("span");
      }

      counterEl.className = "appgenesis-load-more-counter-v1";

      footerEl.textContent = "";
      footerEl.classList.add("appgenesis-load-more-footer-v1");
      footerEl.dataset.appgenesisLoadMoreReady = "1";

      pageSizeWrapperEl.appendChild(pageSizeSelectEl);
      pageSizeWrapperEl.appendChild(pageSizeLabelEl);

      statusWrapperEl.appendChild(loadMoreButtonEl);
      statusWrapperEl.appendChild(counterEl);

      loadLessWrapperEl.appendChild(loadLessButtonEl);

      footerEl.appendChild(pageSizeWrapperEl);
      footerEl.appendChild(statusWrapperEl);
      footerEl.appendChild(loadLessWrapperEl);
    }

    function updateCounterAndButton() {
      const totalRows = filteredRows.length;
      const safeVisibleCount = Math.min(Math.max(visibleCount, 0), totalRows);
      const canShowMore = safeVisibleCount < totalRows;
      const canShowLess = safeVisibleCount > pageSize;

      if (counterEl) {
        counterEl.textContent = `[ ${safeVisibleCount} / ${totalRows} ]`;
      }

      if (loadMoreButtonEl) {
        loadMoreButtonEl.textContent = labels.loadMore;
        loadMoreButtonEl.disabled = !canShowMore || totalRows === 0;
        loadMoreButtonEl.hidden = totalRows === 0 || !canShowMore;
        loadMoreButtonEl.setAttribute(
          "aria-disabled",
          (!canShowMore || totalRows === 0) ? "true" : "false"
        );

        if (tableEl.id) {
          loadMoreButtonEl.setAttribute("aria-controls", tableEl.id);
        }
      }

      if (loadLessButtonEl) {
        loadLessButtonEl.textContent = labels.loadLess;
        loadLessButtonEl.disabled = !canShowLess || totalRows === 0;
        loadLessButtonEl.hidden = totalRows === 0 || !canShowLess;
        loadLessButtonEl.setAttribute(
          "aria-disabled",
          (!canShowLess || totalRows === 0) ? "true" : "false"
        );

        if (tableEl.id) {
          loadLessButtonEl.setAttribute("aria-controls", tableEl.id);
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

    function loadLess() {
      if (destroyed || !filteredRows.length) {
        return;
      }

      visibleCount = Math.max(pageSize, Math.floor((visibleCount - 1) / pageSize) * pageSize);
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

    function handleLoadLessClick() {
      loadLess();
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

      if (loadLessButtonEl) {
        loadLessButtonEl.addEventListener("click", handleLoadLessClick);
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

      if (loadLessButtonEl) {
        loadLessButtonEl.removeEventListener("click", handleLoadLessClick);
      }

      destroyed = true;
      initialized = false;
      footerEl.dataset.appgenesisLoadMoreReady = "0";
      tableControllersByFooter.delete(footerEl);
      tableControllersByTable.delete(tableEl);
    }

    const controller = {
      init,
      render,
      loadMore,
      loadLess,
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
        .filter((rowEl) => !rowEl.classList.contains("appgenesis-table-empty-search-row-v1"))
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
        emptyRowEl.className = "appgenesis-table-empty-search-row-v1";

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
      headerEl.className = "appgenesis-card-header-v1";
      cardEl.insertBefore(headerEl, titleEl);
    }

    if (titleEl.parentElement !== headerEl) {
      headerEl.insertBefore(titleEl, headerEl.firstChild || null);
    }

    let actionsEl = findDirectChildElement(headerEl, (childEl) => {
      return childEl.classList && childEl.classList.contains("appgenesis-card-header-actions-v1");
    });

    if (!actionsEl) {
      actionsEl = ownerDocument.createElement("div");
      actionsEl.className = "appgenesis-card-header-actions-v1";
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

    let searchWrapperEl = actionsEl.querySelector(".appgenesis-card-search-v1");
    let inputEl = searchWrapperEl ? searchWrapperEl.querySelector("input[type='search'], input") : null;

    if (!searchWrapperEl) {
      searchWrapperEl = ownerDocument.createElement("label");
      searchWrapperEl.className = "appgenesis-card-search-v1";

      const iconEl = ownerDocument.createElement("span");
      iconEl.className = "appgenesis-card-search-icon-v1";
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

      cardEl.classList.add("appgenesis-searchable-card-v1");
      cardEl.dataset.appgenesisSearchableTable = tableEl ? "1" : "0";

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

  function getRowActionTypeV1(actionEl) {
    if (!actionEl) {
      return "default";
    }
    const raw = [
      actionEl.getAttribute("title"),
      actionEl.getAttribute("aria-label"),
      actionEl.textContent,
      typeof actionEl.className === "string" ? actionEl.className : ""
    ].filter(Boolean).join(" ").toLowerCase();

    if (/\bsubir\b|move_up|mover.*cima/.test(raw)) {
      return "move_up";
    }
    if (/\bdescer\b|move_down|mover.*baixo/.test(raw)) {
      return "move_down";
    }
    if (/\breativar\b/.test(raw)) {
      return "reactivate";
    }
    if (/\bocultar\b/.test(raw)) {
      return "hide_menu";
    }
    if (/exibir|ver\b|visualizar|detalhe|eye/.test(raw)) {
      return "view";
    }
    if (/editar|modificar|pencil/.test(raw)) {
      return "edit";
    }
    if (/eliminar|excluir|apagar|remover|delete|trash|danger/.test(raw)) {
      return "delete";
    }
    return "default";
  }

  function getRowActionLabelV1(actionType, fallbackText) {
    if (actionType === "move_up") {
      return "Subir";
    }
    if (actionType === "move_down") {
      return "Descer";
    }
    if (actionType === "reactivate") {
      return "Reativar menu";
    }
    if (actionType === "hide_menu") {
      return "Ocultar menu";
    }
    if (actionType === "view") {
      return "Exibir detalhes";
    }
    if (actionType === "edit") {
      return "Editar informações";
    }
    if (actionType === "delete") {
      return "Eliminar";
    }
    return normalizeText(fallbackText, "Abrir");
  }

  function getRowActionIconSvgV1(actionType) {
    if (actionType === "move_up") {
      return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></svg>';
    }
    if (actionType === "move_down") {
      return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="M5 12l7 7 7-7"/></svg>';
    }
    if (actionType === "reactivate") {
      return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
    }
    if (actionType === "hide_menu") {
      return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
    }
    if (actionType === "view") {
      return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z"/><circle cx="12" cy="12" r="3"/></svg>';
    }
    if (actionType === "edit") {
      return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z"/></svg>';
    }
    if (actionType === "delete") {
      return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>';
    }
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 3"/></svg>';
  }

  function applyRowActionIconContentV1(actionEl, actionType, label) {
    if (!actionEl) {
      return;
    }
    let className = "appgenesis-row-actions-item-v1 appgenesis-row-actions-item-" + actionType + "-v1";
    if (actionType === "delete") {
      className += " appgenesis-row-actions-danger-v1";
    }
    actionEl.className = className;
    actionEl.setAttribute("role", "menuitem");
    actionEl.removeAttribute("aria-label");
    actionEl.innerHTML =
      '<span class="appgenesis-row-actions-icon-v1" aria-hidden="true">' +
      getRowActionIconSvgV1(actionType) +
      "</span>" +
      '<span class="appgenesis-row-actions-text-v1">' +
      label +
      "</span>";
  }

  function normalizeActionItemElement(elementEl, label, actionType) {
    if (!elementEl) {
      return null;
    }

    if (elementEl.tagName === "A" || elementEl.tagName === "BUTTON") {
      applyRowActionIconContentV1(elementEl, actionType, label);
      return elementEl;
    }

    if (elementEl.tagName === "INPUT") {
      let className = "appgenesis-row-actions-item-v1 appgenesis-row-actions-item-" + actionType + "-v1";
      if (actionType === "delete") {
        className += " appgenesis-row-actions-danger-v1";
      }
      elementEl.className = className;
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
    wrapperEl.className = "appgenesis-row-actions-menu-v1";

    const triggerEl = ownerDocument.createElement("button");
    triggerEl.type = "button";
    triggerEl.className = "appgenesis-row-actions-trigger-v1";
    triggerEl.setAttribute("aria-haspopup", "menu");
    triggerEl.setAttribute("aria-expanded", "false");
    triggerEl.setAttribute("aria-label", labels.openMenu);
    triggerEl.title = labels.openMenu;
    triggerEl.textContent = "⋮";

    const popupEl = ownerDocument.createElement("div");
    popupEl.className = "appgenesis-row-actions-popup-v1";
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

        const actionType = getRowActionTypeV1(submitEl);
        const fallbackText = submitEl.textContent || submitEl.value || "";
        const label = getRowActionLabelV1(actionType, fallbackText);
        const normalizedSubmitEl = normalizeActionItemElement(submitEl, label, actionType);
        if (!normalizedSubmitEl) {
          return;
        }

        sourceEl.classList.add("appgenesis-row-actions-form-v1");
        popupEl.appendChild(sourceEl);
        return;
      }

      const actionType = getRowActionTypeV1(sourceEl);
      const fallbackText = sourceEl.textContent || sourceEl.value || "";
      const label = getRowActionLabelV1(actionType, fallbackText);
      const normalizedItemEl = normalizeActionItemElement(sourceEl, label, actionType);
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
    actionsEl.classList.add("appgenesis-row-actions-ready-v1");
    actionsEl.dataset.appgenesisActionsMenuReady = "1";
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
          actionsEl.dataset.appgenesisActionsMenuReady === "1" &&
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

  //###################################################################################
  // (6) CONFIRM DIALOG
  //###################################################################################

  function createConfirmDialogController(config) {
    var existing = global.document && global.document.querySelector(".appgenesis-confirm-overlay-v1");
    if (existing && existing.parentNode) {
      existing.parentNode.removeChild(existing);
    }

    var safeConfig = (config && typeof config === "object") ? config : {};
    var title = normalizeText(safeConfig.title, "Confirmar");
    var message = normalizeText(safeConfig.message, "Tem a certeza?");
    var confirmLabel = normalizeText(safeConfig.confirmLabel, "Confirmar");
    var cancelLabel = normalizeText(safeConfig.cancelLabel, "Cancelar");
    var isDanger = safeConfig.danger !== false && safeConfig.danger !== 0 && Boolean(safeConfig.danger);

    return new Promise(function (resolve) {
      var overlay = global.document.createElement("div");
      overlay.className = "appgenesis-confirm-overlay-v1";
      overlay.setAttribute("role", "dialog");
      overlay.setAttribute("aria-modal", "true");
      overlay.setAttribute("aria-labelledby", "appgenesis-confirm-title-v1");

      var dialog = global.document.createElement("div");
      dialog.className = "appgenesis-confirm-dialog-v1";

      var titleEl = global.document.createElement("h3");
      titleEl.className = "appgenesis-confirm-title-v1";
      titleEl.id = "appgenesis-confirm-title-v1";
      titleEl.textContent = title;

      var messageEl = global.document.createElement("p");
      messageEl.className = "appgenesis-confirm-message-v1";
      messageEl.textContent = message;

      var actionsEl = global.document.createElement("div");
      actionsEl.className = "appgenesis-confirm-actions-v1";

      var cancelBtn = global.document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.className = "appgenesis-confirm-cancel-v1";
      cancelBtn.textContent = cancelLabel;

      var confirmBtn = global.document.createElement("button");
      confirmBtn.type = "button";
      confirmBtn.className = "appgenesis-confirm-action-v1" + (isDanger ? " appgenesis-confirm-action-danger-v1" : "");
      confirmBtn.textContent = confirmLabel;

      actionsEl.appendChild(cancelBtn);
      actionsEl.appendChild(confirmBtn);
      dialog.appendChild(titleEl);
      dialog.appendChild(messageEl);
      dialog.appendChild(actionsEl);
      overlay.appendChild(dialog);

      function closeDialog(result) {
        if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
        global.document.removeEventListener("keydown", onKeydown);
        resolve(result);
      }

      function onKeydown(e) {
        if (e.key === "Escape") closeDialog(false);
      }

      cancelBtn.addEventListener("click", function () { closeDialog(false); });
      confirmBtn.addEventListener("click", function () { closeDialog(true); });

      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) closeDialog(false);
      });

      global.document.addEventListener("keydown", onKeydown);
      global.document.body.appendChild(overlay);
      confirmBtn.focus();
    });
  }

  function enhanceConfirmableActions(config) {
    if (confirmDelegationReady) return;

    if (!global.document || typeof global.document.addEventListener !== "function") return;

    global.document.addEventListener("submit", function (e) {
      var form = e.target;
      if (!form || typeof form.getAttribute !== "function") return;
      if (!form.getAttribute("data-appgenesis-confirm")) return;
      if (form.getAttribute("data-appgenesis-confirming")) return;

      e.preventDefault();
      e.stopImmediatePropagation();

      createConfirmDialogController({
        title: form.getAttribute("data-appgenesis-confirm-title") || "Confirmar",
        message: form.getAttribute("data-appgenesis-confirm-message") || "Tem a certeza?",
        confirmLabel: form.getAttribute("data-appgenesis-confirm-action-label") || "Confirmar",
        cancelLabel: form.getAttribute("data-appgenesis-confirm-cancel-label") || "Cancelar",
        danger: !!form.getAttribute("data-appgenesis-confirm-danger"),
      }).then(function (confirmed) {
        if (!confirmed) return;
        form.setAttribute("data-appgenesis-confirming", "1");
        form.submit();
      });
    }, true);

    confirmDelegationReady = true;
  }

  //###################################################################################
  // (10) TOAST NOTIFICATIONS
  //###################################################################################

  function createToastController(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const root = safeConfig.root || (global.document && global.document.body) || null;
    const position = normalizeText(safeConfig.position, "bottom-right");
    const defaultAutoCloseMs = parsePositiveInteger(safeConfig.autoCloseMs, 4500);

    if (!root) {
      return null;
    }

    const ownerDocument = root.ownerDocument || global.document;
    if (!ownerDocument) {
      return null;
    }

    let viewportEl = ownerDocument.querySelector(".appgenesis-toast-viewport-v1");
    if (!viewportEl) {
      viewportEl = ownerDocument.createElement("div");
      viewportEl.className = "appgenesis-toast-viewport-v1 appgenesis-toast-" + position + "-v1";
      viewportEl.setAttribute("aria-live", "polite");
      viewportEl.setAttribute("aria-atomic", "false");
      root.appendChild(viewportEl);
    }

    let destroyed = false;

    function resolveTypeConfig(type) {
      const safeType = normalizeText(type, "info");
      if (safeType === "success") {
        return { title: "Sucesso", icon: "✓", className: "appgenesis-toast-success-v1" };
      }
      if (safeType === "error") {
        return { title: "Erro", icon: "✕", className: "appgenesis-toast-error-v1" };
      }
      if (safeType === "warning") {
        return { title: "Aviso", icon: "⚠", className: "appgenesis-toast-warning-v1" };
      }
      return { title: "Informação", icon: "ℹ", className: "appgenesis-toast-info-v1" };
    }

    function showToast(options) {
      if (destroyed || !viewportEl) {
        return null;
      }

      const safeOptions = options && typeof options === "object" ? options : {};
      const type = normalizeText(safeOptions.type, "info");
      const message = normalizeText(safeOptions.message, "");
      const autoCloseMs = parsePositiveInteger(safeOptions.autoCloseMs, defaultAutoCloseMs);

      if (!message) {
        return null;
      }

      const typeConfig = resolveTypeConfig(type);
      const customTitle = typeof safeOptions.title === "string" ? safeOptions.title : typeConfig.title;

      const toastEl = ownerDocument.createElement("div");
      toastEl.className = "appgenesis-toast-v1 " + typeConfig.className;
      toastEl.setAttribute("role", "status");

      const iconEl = ownerDocument.createElement("div");
      iconEl.className = "appgenesis-toast-icon-v1";
      iconEl.setAttribute("aria-hidden", "true");
      iconEl.textContent = typeConfig.icon;

      const contentEl = ownerDocument.createElement("div");
      contentEl.className = "appgenesis-toast-content-v1";

      if (customTitle) {
        const titleEl = ownerDocument.createElement("div");
        titleEl.className = "appgenesis-toast-title-v1";
        titleEl.textContent = customTitle;
        contentEl.appendChild(titleEl);
      }

      const messageEl = ownerDocument.createElement("div");
      messageEl.className = "appgenesis-toast-message-v1";
      messageEl.textContent = message;
      contentEl.appendChild(messageEl);

      const closeBtnEl = ownerDocument.createElement("button");
      closeBtnEl.type = "button";
      closeBtnEl.className = "appgenesis-toast-close-v1";
      closeBtnEl.setAttribute("aria-label", "Fechar mensagem");
      closeBtnEl.textContent = "×";

      toastEl.appendChild(iconEl);
      toastEl.appendChild(contentEl);
      toastEl.appendChild(closeBtnEl);
      viewportEl.appendChild(toastEl);

      let timerId = 0;

      function removeToastEl() {
        global.clearTimeout(timerId);
        if (toastEl.parentNode) {
          toastEl.parentNode.removeChild(toastEl);
        }
      }

      closeBtnEl.addEventListener("click", removeToastEl);

      if (autoCloseMs > 0) {
        timerId = global.setTimeout(removeToastEl, autoCloseMs);
      }

      return { el: toastEl, remove: removeToastEl };
    }

    function clearToasts() {
      if (viewportEl) {
        viewportEl.textContent = "";
      }
    }

    function destroy() {
      if (destroyed) {
        return;
      }

      destroyed = true;
      clearToasts();

      if (viewportEl && viewportEl.parentNode) {
        viewportEl.parentNode.removeChild(viewportEl);
      }
    }

    return { showToast, clearToasts, destroy };
  }

  function getOrCreateFeedbackToastController() {
    if (!_feedbackToastController) {
      _feedbackToastController = createToastController({
        position: "bottom-right",
        autoCloseMs: 4500
      });
    }

    return _feedbackToastController;
  }

  function showToast(options) {
    const controller = getOrCreateFeedbackToastController();
    return controller ? controller.showToast(options) : null;
  }

  function enhanceFeedbackToasts(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const source = normalizeText(safeConfig.source, "url");

    if (source !== "url") {
      return;
    }

    let url;
    try {
      url = new URL(global.location.href);
    } catch (e) {
      return;
    }

    const feedbackMessages = [];

    url.searchParams.forEach(function (rawValue, rawKey) {
      const key = String(rawKey || "").trim().toLowerCase();
      const message = String(rawValue || "").trim();

      if (!message) {
        return;
      }

      let type = "";
      if (key === "success" || key.endsWith("_success")) {
        type = "success";
      } else if (key === "error" || key.endsWith("_error")) {
        type = "error";
      }

      if (type) {
        feedbackMessages.push({ type: type, message: message });
      }
    });

    if (!feedbackMessages.length) {
      return;
    }

    const controller = getOrCreateFeedbackToastController();
    if (!controller) {
      return;
    }

    feedbackMessages.forEach(function (feedback) {
      controller.showToast({ type: feedback.type, message: feedback.message });
    });

    const docRoot = global.document;
    if (docRoot && docRoot.body) {
      docRoot.body.classList.add("appgenesis-url-feedback-active-v1");
    }
  }

  //###################################################################################
  // (11) RESPONSIVE TABLE COLUMNS
  //###################################################################################

  const responsiveTableControllersByTable = new WeakMap();
  const _activeResponsiveControllers = new Set();
  let _responsiveWindowListenerAdded = false;

  function _normalizeColKey(text) {
    return String(text || "")
      .toLowerCase()
      .trim()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^\w]/g, "");
  }

  function createResponsiveTableColumnsController(config) {
    config = config || {};
    const table = config.table;
    const card = config.card;
    if (!table || !card) {
      return null;
    }
    if (responsiveTableControllersByTable.has(table)) {
      return responsiveTableControllersByTable.get(table);
    }

    const mandatoryKeys = Array.isArray(config.mandatoryColumnKeys)
      ? config.mandatoryColumnKeys.map(_normalizeColKey)
      : ["estado", "acoes", "actions", "status"];

    const headerRow = table.querySelector("thead tr");
    if (!headerRow) {
      return null;
    }
    const ths = Array.from(headerRow.querySelectorAll("th"));
    if (!ths.length) {
      return null;
    }

    const columns = ths.map(function (th, i) {
      const keyAttr = _normalizeColKey(th.dataset.appgenesisColumnKey || "");
      const textKey = _normalizeColKey(th.textContent);
      const key = keyAttr || textKey;
      const hideOrder = parseInt(th.dataset.appgenesisHideOrder || "0", 10);
      const mandatoryAttr = th.dataset.appgenesisColumnMandatory === "1";
      const mandatory = mandatoryAttr || mandatoryKeys.some(function (mk) {
        return mk === key || mk === keyAttr || mk === textKey;
      });
      return { th: th, index: i + 1, key: key, hideOrder: hideOrder, mandatory: mandatory };
    });

    const hideable = columns
      .filter(function (c) { return !c.mandatory && c.hideOrder > 0; })
      .sort(function (a, b) { return a.hideOrder - b.hideOrder; });

    let destroyed = false;
    let rafId = null;
    let currentHidden = new Set();

    function _applyHidden(newHidden) {
      columns.forEach(function (col) {
        const hide = newHidden.has(col.index);
        const was = currentHidden.has(col.index);
        if (hide && !was) {
          table.classList.add("appgenesis-hide-col-" + col.index);
        } else if (!hide && was) {
          table.classList.remove("appgenesis-hide-col-" + col.index);
        }
      });
      currentHidden = new Set(newHidden);
    }

    function _recalc() {
      if (destroyed) {
        return;
      }
      _applyHidden(new Set());

      var cardWidth = card.clientWidth;
      if (!cardWidth) {
        return;
      }
      var tableWidth = table.scrollWidth;
      if (tableWidth <= cardWidth) {
        return;
      }

      var colWidths = columns.map(function (c) { return c.th.offsetWidth || 0; });
      var excess = tableWidth - cardWidth;
      var newHidden = new Set();

      for (var i = 0; i < hideable.length; i++) {
        if (excess <= 0) {
          break;
        }
        var col = hideable[i];
        newHidden.add(col.index);
        excess -= colWidths[col.index - 1];
      }

      _applyHidden(newHidden);
    }

    function schedule() {
      if (destroyed || rafId !== null) {
        return;
      }
      rafId = requestAnimationFrame(function () {
        rafId = null;
        _recalc();
      });
    }

    var ro = null;
    if (typeof ResizeObserver === "function") {
      ro = new ResizeObserver(schedule);
      ro.observe(card);
    }

    schedule();

    var controller = {
      recalculate: schedule,
      destroy: function () {
        destroyed = true;
        if (rafId !== null) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
        if (ro) {
          ro.disconnect();
          ro = null;
        }
        _applyHidden(new Set());
        responsiveTableControllersByTable.delete(table);
        _activeResponsiveControllers.delete(controller);
      },
    };

    responsiveTableControllersByTable.set(table, controller);
    _activeResponsiveControllers.add(controller);
    return controller;
  }

  function enhanceResponsiveTableColumns(config) {
    config = config || {};
    var root = config.root || (global.document || null);
    var tableSelector = config.tableSelector || DEFAULT_TABLE_SELECTOR;
    var cardSelector = config.cardSelector || DEFAULT_CARD_SELECTOR;
    var mandatoryColumnKeys = Array.isArray(config.mandatoryColumnKeys)
      ? config.mandatoryColumnKeys
      : ["estado", "acoes", "actions", "status"];

    if (!root || typeof root.querySelectorAll !== "function") {
      return;
    }

    Array.from(root.querySelectorAll(cardSelector)).forEach(function (card) {
      Array.from(card.querySelectorAll(tableSelector)).forEach(function (table) {
        createResponsiveTableColumnsController({ table: table, card: card, mandatoryColumnKeys: mandatoryColumnKeys });
      });
    });

    if (!_responsiveWindowListenerAdded && global.window && typeof global.window.addEventListener === "function") {
      _responsiveWindowListenerAdded = true;
      var winRaf = null;
      global.window.addEventListener("resize", function () {
        if (winRaf !== null) {
          return;
        }
        winRaf = requestAnimationFrame(function () {
          winRaf = null;
          _activeResponsiveControllers.forEach(function (ctrl) {
            ctrl.recalculate();
          });
        });
      }, { passive: true });
    }
  }

  global.AppGenesisProcessShell = {
    ...(global.AppGenesisProcessShell || {}),
    createProcessHeaderController,
    createLoadMoreTableController,
    enhanceLoadMoreTables,
    createSearchableTableController,
    enhanceSearchableTableCards,
    createTableActionsMenuController,
    enhanceTableActionMenus,
    createConfirmDialogController,
    enhanceConfirmableActions,
    createToastController,
    showToast,
    enhanceFeedbackToasts,
    createResponsiveTableColumnsController,
    enhanceResponsiveTableColumns,
  };
})(typeof window !== "undefined" ? window : globalThis);
