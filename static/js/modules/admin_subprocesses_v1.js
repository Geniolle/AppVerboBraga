// APPGENESIS_ADMIN_SUBPROCESSES_V1_START
(function () {
  "use strict";

  const ADMIN_SUBPROCESS_SORT_INDICATOR_V1 = "⇅";
  const ADMIN_SUBPROCESS_SORTABLE_TABLE_SELECTOR_V1 = [
    "[data-admin-sortable-table='1']",
    "[data-appgenesis-sortable-table='1']",
    "table.admin-subprocess-table-v1"
  ].join(", ");
  const ADMIN_SUBPROCESS_SORT_BUTTON_SELECTOR_V1 = [
    "[data-admin-sort-button]",
    "[data-appgenesis-sort-button]"
  ].join(", ");
  const adminSubprocessSortableControllersV1 = new WeakMap();
  const adminSubprocessTextCollatorV1 = (
    typeof Intl !== "undefined" &&
    typeof Intl.Collator === "function"
  )
    ? new Intl.Collator("pt-PT", { numeric: true, sensitivity: "base" })
    : null;

  //###################################################################################
  // (1) UTILITARIOS DE ORDENACAO
  //###################################################################################

  function normalizeAdminSubprocessSortDirectionV1(direction) {
    const normalizedDirection = String(direction || "").trim().toLowerCase();
    return normalizedDirection === "desc" ? "desc" : normalizedDirection === "asc" ? "asc" : "";
  }

  function normalizeAdminSubprocessSortTypeV1(sortType) {
    return String(sortType || "").trim().toLowerCase() === "number" ? "number" : "text";
  }

  function normalizeAdminSubprocessSortTextV1(value) {
    return String(value == null ? "" : value).trim();
  }

  function readAdminSubprocessSortAttributeV1(element, attributeNames) {
    if (!element || !Array.isArray(attributeNames)) {
      return "";
    }

    for (let index = 0; index < attributeNames.length; index += 1) {
      const attributeName = attributeNames[index];

      if (!attributeName || !element.hasAttribute(attributeName)) {
        continue;
      }

      return element.getAttribute(attributeName) || "";
    }

    return "";
  }

  function parseAdminSubprocessNumericValueV1(value) {
    const normalizedValue = normalizeAdminSubprocessSortTextV1(value)
      .replace(/\s+/g, "")
      .replace(/\.(?=\d{3}(?:\D|$))/g, "")
      .replace(",", ".");

    if (!normalizedValue) {
      return null;
    }

    const parsedValue = Number.parseFloat(normalizedValue);
    return Number.isFinite(parsedValue) ? parsedValue : null;
  }

  function compareAdminSubprocessTextValuesV1(leftValue, rightValue) {
    if (adminSubprocessTextCollatorV1) {
      return adminSubprocessTextCollatorV1.compare(leftValue, rightValue);
    }

    return leftValue.localeCompare(rightValue, undefined, {
      numeric: true,
      sensitivity: "base"
    });
  }

  function buildAdminSubprocessComparableValueV1(rawValue, sortType) {
    const normalizedText = normalizeAdminSubprocessSortTextV1(rawValue);

    if (!normalizedText) {
      return {
        rank: 2,
        textValue: "",
        numberValue: null
      };
    }

    if (sortType === "number") {
      const parsedNumber = parseAdminSubprocessNumericValueV1(normalizedText);

      if (parsedNumber !== null) {
        return {
          rank: 0,
          textValue: normalizedText.toLocaleLowerCase(),
          numberValue: parsedNumber
        };
      }

      return {
        rank: 1,
        textValue: normalizedText.toLocaleLowerCase(),
        numberValue: null
      };
    }

    return {
      rank: 0,
      textValue: normalizedText.toLocaleLowerCase(),
      numberValue: null
    };
  }

  function compareAdminSubprocessRowValuesV1(leftRow, rightRow, sortType, direction) {
    if (leftRow.comparable.rank !== rightRow.comparable.rank) {
      return leftRow.comparable.rank - rightRow.comparable.rank;
    }

    let comparisonResult = 0;

    if (
      sortType === "number" &&
      typeof leftRow.comparable.numberValue === "number" &&
      typeof rightRow.comparable.numberValue === "number"
    ) {
      comparisonResult = leftRow.comparable.numberValue - rightRow.comparable.numberValue;
    }
    else {
      comparisonResult = compareAdminSubprocessTextValuesV1(
        leftRow.comparable.textValue,
        rightRow.comparable.textValue
      );
    }

    if (comparisonResult === 0) {
      return leftRow.originalIndex - rightRow.originalIndex;
    }

    return direction === "desc" ? comparisonResult * -1 : comparisonResult;
  }

  function collectAdminSubprocessTableRowsV1(tbodyEl) {
    return Array.from(tbodyEl.children).filter((rowEl) => {
      return (
        rowEl &&
        rowEl.tagName === "TR" &&
        !rowEl.classList.contains("appgenesis-table-empty-search-row-v1")
      );
    });
  }

  function resolveAdminSubprocessSortHeaderStateV1(buttonEl) {
    const headerCellEl = buttonEl ? buttonEl.closest("th") : null;
    const sortKey = normalizeAdminSubprocessSortTextV1(
      readAdminSubprocessSortAttributeV1(buttonEl, [
        "data-admin-sort-key",
        "data-appgenesis-sort-key"
      ]) || readAdminSubprocessSortAttributeV1(headerCellEl, [
        "data-admin-column-key",
        "data-appgenesis-column-key"
      ])
    );

    return {
      buttonEl,
      headerCellEl,
      indicatorEl: buttonEl ? buttonEl.querySelector(".admin-subprocess-sort-indicator-v1") : null,
      sortKey,
      sortType: normalizeAdminSubprocessSortTypeV1(
        readAdminSubprocessSortAttributeV1(buttonEl, [
          "data-admin-sort-type",
          "data-appgenesis-sort-type"
        ]) || readAdminSubprocessSortAttributeV1(headerCellEl, [
          "data-admin-sort-type",
          "data-appgenesis-sort-type"
        ])
      ),
      defaultSortDirection: normalizeAdminSubprocessSortDirectionV1(
        readAdminSubprocessSortAttributeV1(buttonEl, [
          "data-admin-default-sort",
          "data-appgenesis-default-sort"
        ]) || readAdminSubprocessSortAttributeV1(headerCellEl, [
          "data-admin-default-sort",
          "data-appgenesis-default-sort"
        ])
      ),
      columnIndex: headerCellEl ? headerCellEl.cellIndex : -1
    };
  }

  function ensureAdminSubprocessOriginalOrderV1(tableEl) {
    const tbodyEl = tableEl.tBodies && tableEl.tBodies[0] ? tableEl.tBodies[0] : null;

    if (!tbodyEl) {
      return;
    }

    let nextOriginalIndex = 0;
    collectAdminSubprocessTableRowsV1(tbodyEl).forEach((rowEl) => {
      const existingIndex = Number.parseInt(
        rowEl.getAttribute("data-admin-sort-original-index") || "",
        10
      );

      if (Number.isFinite(existingIndex)) {
        nextOriginalIndex = Math.max(nextOriginalIndex, existingIndex + 1);
        return;
      }

      rowEl.setAttribute("data-admin-sort-original-index", String(nextOriginalIndex));
      nextOriginalIndex += 1;
    });
  }

  function refreshAdminSubprocessTableStateV1(tableEl) {
    if (
      !window.AppGenesisProcessShell ||
      typeof window.AppGenesisProcessShell.enhanceLoadMoreTables !== "function"
    ) {
      return;
    }

    const rootEl = tableEl.closest(".card") || tableEl.parentElement || document;
    window.AppGenesisProcessShell.enhanceLoadMoreTables({
      root: rootEl,
      rowsSelector: "tbody tr"
    });
  }

  //###################################################################################
  // (2) VISUALIZAR DETALHES GENERICO
  //###################################################################################

  function instalarVisualizarAdminSubprocessV1() {
    if (window.__appgenesisAdminSubprocessViewV1 === true) {
      return;
    }

    window.__appgenesisAdminSubprocessViewV1 = true;

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
  // (2B) BOTAO "NOVA SESSAO" NO CABECALHO DO CARTAO "SESSOES ATIVAS"
  // Nao duplica logica de criacao: apenas localiza o <summary> original (ja
  // renderizado pelo macro admin_subprocess.html dentro do <details>
  // admin-subprocess-create-collapse-v1) e sintetiza um clique nele, que e' o
  // MESMO gatilho nativo que a faixa antiga usava. Delegado em document (nao
  // vinculado por elemento) porque os cartoes de Sessoes sao substituidos via
  // replaceWith() apos cada guardar por AJAX (ver bloco 4B abaixo).
  //###################################################################################

  function instalarInlineCreateToggleAdminSubprocessV1() {
    if (window.__appgenesisAdminSubprocessInlineCreateToggleV1 === true) {
      return;
    }

    window.__appgenesisAdminSubprocessInlineCreateToggleV1 = true;

    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-inline-create]");

      if (!button) {
        return;
      }

      const subprocessKey = button.getAttribute("data-admin-subprocess-inline-create") || "";
      const summaryEl = document.querySelector(
        '[data-admin-subprocess="' + subprocessKey + '"][data-admin-subprocess-role="form"] .admin-subprocess-create-collapse-v1 > summary'
      );

      if (summaryEl) {
        summaryEl.click();
      }
    });
  }

  //###################################################################################
  // (3) CONTROLLER DE TABELA ORDENAVEL
  //###################################################################################

  function createAdminSubprocessSortableTableControllerV1(tableEl) {
    if (!tableEl) {
      return null;
    }

    if (adminSubprocessSortableControllersV1.has(tableEl)) {
      return adminSubprocessSortableControllersV1.get(tableEl);
    }

    const tbodyEl = tableEl.tBodies && tableEl.tBodies[0] ? tableEl.tBodies[0] : null;
    const headerButtons = Array.from(tableEl.querySelectorAll(ADMIN_SUBPROCESS_SORT_BUTTON_SELECTOR_V1));

    if (!tbodyEl || !headerButtons.length) {
      return null;
    }

    const headerButtonStates = headerButtons.map((buttonEl) => {
      return resolveAdminSubprocessSortHeaderStateV1(buttonEl);
    }).filter((headerState) => {
      return Boolean(headerState.sortKey) && headerState.columnIndex >= 0;
    });

    if (!headerButtonStates.length) {
      return null;
    }

    const headerButtonStateByElement = new WeakMap();
    const rowSortStateByRow = new WeakMap();

    headerButtonStates.forEach((headerState) => {
      headerButtonStateByElement.set(headerState.buttonEl, headerState);
    });

    let activeSortKey = "";
    let activeSortDirection = "";
    let initialized = false;

    function ensureAdminSubprocessRowSortStateV1(rowEl) {
      let rowState = rowSortStateByRow.get(rowEl);

      if (rowState) {
        return rowState;
      }

      rowState = {
        comparableBySortKey: new Map()
      };
      rowSortStateByRow.set(rowEl, rowState);
      return rowState;
    }

    function readAdminSubprocessCellSortValueByIndexV1(rowEl, columnIndex) {
      const cellEl = rowEl.cells && rowEl.cells.length > columnIndex
        ? rowEl.cells[columnIndex]
        : null;

      if (!cellEl) {
        return "";
      }

      if (cellEl.hasAttribute("data-sort-value")) {
        return cellEl.getAttribute("data-sort-value") || "";
      }

      if (cellEl.hasAttribute("data-admin-sort-value")) {
        return cellEl.getAttribute("data-admin-sort-value") || "";
      }

      return cellEl.textContent || "";
    }

    function resolveAdminSubprocessComparableValueV1(rowEl, headerState) {
      const rowState = ensureAdminSubprocessRowSortStateV1(rowEl);
      const cacheKey = headerState.sortKey + "::" + headerState.sortType;

      if (rowState.comparableBySortKey.has(cacheKey)) {
        return rowState.comparableBySortKey.get(cacheKey);
      }

      const comparableValue = buildAdminSubprocessComparableValueV1(
        readAdminSubprocessCellSortValueByIndexV1(rowEl, headerState.columnIndex),
        headerState.sortType
      );

      rowState.comparableBySortKey.set(cacheKey, comparableValue);
      return comparableValue;
    }

    function updateSortUi() {
      headerButtonStates.forEach((headerState) => {
        const buttonDirection = headerState.sortKey === activeSortKey ? activeSortDirection : "";

        headerState.buttonEl.setAttribute("data-admin-sort-direction", buttonDirection);
        headerState.buttonEl.setAttribute("aria-pressed", buttonDirection ? "true" : "false");

        if (headerState.indicatorEl) {
          headerState.indicatorEl.textContent = ADMIN_SUBPROCESS_SORT_INDICATOR_V1;
        }

        if (headerState.headerCellEl) {
          const ariaSortValue = buttonDirection === "asc"
            ? "ascending"
            : buttonDirection === "desc"
              ? "descending"
              : "none";
          headerState.headerCellEl.setAttribute("aria-sort", ariaSortValue);
        }
      });
    }

    function resolveNextSortDirection(headerState) {
      if (!headerState || !headerState.sortKey) {
        return "asc";
      }

      if (headerState.sortKey === activeSortKey) {
        return activeSortDirection === "asc" ? "desc" : "asc";
      }

      return headerState.defaultSortDirection || "asc";
    }

    function applySort(headerState, direction) {
      if (!headerState || !headerState.sortKey) {
        return;
      }

      const sortKey = headerState.sortKey;
      const sortType = headerState.sortType;
      const sortDirection = normalizeAdminSubprocessSortDirectionV1(direction) || "asc";

      ensureAdminSubprocessOriginalOrderV1(tableEl);

      const sortableRows = collectAdminSubprocessTableRowsV1(tbodyEl).map((rowEl) => {
        const rowState = ensureAdminSubprocessRowSortStateV1(rowEl);
        const originalIndex = Number.parseInt(
          rowEl.getAttribute("data-admin-sort-original-index") || "",
          10
        );

        rowState.originalIndex = Number.isFinite(originalIndex) ? originalIndex : 0;

        return {
          rowEl,
          comparable: resolveAdminSubprocessComparableValueV1(rowEl, headerState),
          originalIndex: rowState.originalIndex
        };
      });

      sortableRows.sort((leftRow, rightRow) => {
        return compareAdminSubprocessRowValuesV1(leftRow, rightRow, sortType, sortDirection);
      });

      const rowsFragment = tbodyEl.ownerDocument.createDocumentFragment();
      sortableRows.forEach((rowState) => {
        rowsFragment.appendChild(rowState.rowEl);
      });
      tbodyEl.appendChild(rowsFragment);

      activeSortKey = sortKey;
      activeSortDirection = sortDirection;
      updateSortUi();
      refreshAdminSubprocessTableStateV1(tableEl);

      tableEl.dispatchEvent(new CustomEvent("appgenesis:table-sorted", {
        bubbles: true,
        detail: {
          sortKey,
          sortType,
          direction: sortDirection
        }
      }));
    }

    function handleHeaderClick(event) {
      const buttonEl = event.target.closest(ADMIN_SUBPROCESS_SORT_BUTTON_SELECTOR_V1);
      const headerState = buttonEl
        ? headerButtonStateByElement.get(buttonEl) || null
        : null;

      if (!buttonEl || !headerState || !tableEl.contains(buttonEl)) {
        return;
      }

      event.preventDefault();
      applySort(headerState, resolveNextSortDirection(headerState));
    }

    function init() {
      if (initialized || tableEl.dataset.adminSubprocessSortableReady === "1") {
        initialized = true;
        return;
      }

      ensureAdminSubprocessOriginalOrderV1(tableEl);
      tableEl.addEventListener("click", handleHeaderClick);
      tableEl.dataset.adminSubprocessSortableReady = "1";
      initialized = true;

      const defaultHeaderState = headerButtonStates.find((headerState) => {
        return Boolean(headerState.defaultSortDirection);
      });

      if (defaultHeaderState) {
        applySort(
          defaultHeaderState,
          defaultHeaderState.defaultSortDirection || "asc"
        );
      }
      else {
        updateSortUi();
      }
    }

    function destroy() {
      if (!initialized) {
        return;
      }

      tableEl.removeEventListener("click", handleHeaderClick);
      tableEl.dataset.adminSubprocessSortableReady = "0";
      adminSubprocessSortableControllersV1.delete(tableEl);
      initialized = false;
    }

    const controller = {
      init,
      destroy
    };

    adminSubprocessSortableControllersV1.set(tableEl, controller);
    return controller;
  }

  function instalarOrdenacaoAdminSubprocessV1(rootNode) {
    const safeRootNode = rootNode && typeof rootNode.querySelectorAll === "function"
      ? rootNode
      : document;
    const sortableTables = [];
    const seenTables = new Set();

    if (
      typeof safeRootNode.matches === "function" &&
      safeRootNode.matches(ADMIN_SUBPROCESS_SORTABLE_TABLE_SELECTOR_V1)
    ) {
      sortableTables.push(safeRootNode);
      seenTables.add(safeRootNode);
    }

    Array.from(
      safeRootNode.querySelectorAll(ADMIN_SUBPROCESS_SORTABLE_TABLE_SELECTOR_V1)
    ).forEach((tableEl) => {
      if (seenTables.has(tableEl)) {
        return;
      }

      sortableTables.push(tableEl);
      seenTables.add(tableEl);
    });

    sortableTables.forEach((tableEl) => {
      const controller = createAdminSubprocessSortableTableControllerV1(tableEl);

      if (controller) {
        controller.init();
      }
    });
  }

  //###################################################################################
  // (4) COLUNAS RESPONSIVAS PARA TABELAS ADMIN
  //###################################################################################

  function recalcAdminResponsiveTableV1(tableEl) {
    const wrap = tableEl.closest(".admin-subprocess-table-wrap-v1");
    if (!wrap || wrap.offsetParent === null) {
      return;
    }

    // Reset compact states before measuring
    wrap.classList.remove("admin-table-compact-v1", "admin-table-ultra-compact-v1");

    const allHeaderEls = Array.from(tableEl.querySelectorAll("thead th"));

    const optionalKeys = allHeaderEls
      .filter(function (th) {
        return (
          th.hasAttribute("data-admin-responsive-priority") &&
          !th.hasAttribute("data-admin-always-visible")
        );
      })
      .map(function (th) {
        return th.getAttribute("data-admin-column-key") || "";
      })
      .filter(Boolean);

    optionalKeys.sort(function (keyA, keyB) {
      const thA = tableEl.querySelector(
        "thead th[data-admin-column-key=\"" + keyA + "\"]"
      );
      const thB = tableEl.querySelector(
        "thead th[data-admin-column-key=\"" + keyB + "\"]"
      );
      const pA = thA ? parseInt(thA.getAttribute("data-admin-responsive-priority"), 10) || 0 : 0;
      const pB = thB ? parseInt(thB.getAttribute("data-admin-responsive-priority"), 10) || 0 : 0;
      if (pB !== pA) {
        return pB - pA;
      }
      return allHeaderEls.indexOf(thB) - allHeaderEls.indexOf(thA);
    });

    // Show all optional columns before re-evaluating
    optionalKeys.forEach(function (key) {
      tableEl
        .querySelectorAll("[data-admin-column-key=\"" + key + "\"]")
        .forEach(function (el) {
          el.classList.remove("admin-col-hidden-v1");
        });
    });

    // Hide optional columns by priority until table fits or all are hidden
    for (let i = 0; i < optionalKeys.length; i++) {
      if (tableEl.scrollWidth <= wrap.clientWidth + 2) {
        break;
      }
      tableEl
        .querySelectorAll("[data-admin-column-key=\"" + optionalKeys[i] + "\"]")
        .forEach(function (el) {
          if (!el.hasAttribute("data-admin-always-visible")) {
            el.classList.add("admin-col-hidden-v1");
          }
        });
    }

    // If still overflowing after hiding all optional columns, apply compact mode
    if (tableEl.scrollWidth > wrap.clientWidth + 2) {
      wrap.classList.add("admin-table-compact-v1");
      void wrap.offsetWidth; // force reflow so CSS changes take effect before re-measuring
    }

    // If compact mode is still insufficient, apply ultra-compact
    if (tableEl.scrollWidth > wrap.clientWidth + 2) {
      wrap.classList.add("admin-table-ultra-compact-v1");
    }
  }

  function initAdminResponsiveColumnsV1() {
    const tables = Array.from(
      document.querySelectorAll("table[data-admin-responsive-table=\"1\"]")
    );
    if (!tables.length) {
      return;
    }

    let rafHandle = null;
    function scheduleRecalc() {
      if (rafHandle !== null) {
        return;
      }
      rafHandle = requestAnimationFrame(function () {
        rafHandle = null;
        tables.forEach(recalcAdminResponsiveTableV1);
      });
    }

    scheduleRecalc();
    window.addEventListener("resize", scheduleRecalc);

    // Re-run when a table's card becomes visible after tab switching
    const seenCards = new Set();
    const cardObserver = new MutationObserver(function () {
      scheduleRecalc();
    });
    tables.forEach(function (table) {
      const card = table.closest("[data-menu-scope]");
      if (card && !seenCards.has(card)) {
        seenCards.add(card);
        cardObserver.observe(card, {
          attributes: true,
          attributeFilter: ["style"]
        });
      }
    });
  }

  //###################################################################################
  // (4B) AJAX SAVE — SESSOES
  //###################################################################################

  function _isDebugReturnAfterSaveEnabledAjaxV1() {
    try {
      return localStorage.getItem("appgenesisDebugReturnAfterSave") === "1";
    } catch (e) {
      return false;
    }
  }

  function _logReturnAfterSaveAjaxV1(event, data) {
    if (!_isDebugReturnAfterSaveEnabledAjaxV1()) {
      return;
    }

    console.log("[RETURN_AFTER_SAVE]", event, data || {});
  }

  function _isSessoesSaveFormAjaxV1(form) {
    return (form.getAttribute("action") || "").includes("/settings/menu/sidebar-section-save");
  }

  function _normalizeSessoesAjaxMessageV1(message, fallback) {
    var cleanMessage = String(message || "").trim();
    return cleanMessage || String(fallback || "").trim();
  }

  function _clearSessoesSaveAjaxFeedbackV1(root) {
    if (!root || !root.querySelectorAll) {
      return;
    }

    Array.from(root.querySelectorAll(".sessoes-ajax-feedback-v1")).forEach(function (element) {
      element.remove();
    });
  }

  function _insertSessoesSaveAjaxFeedbackV1(container, className, message) {
    if (!container) {
      return null;
    }

    var feedback = document.createElement("div");
    feedback.className = className + " sessoes-ajax-feedback-v1";
    feedback.setAttribute("role", "alert");
    feedback.textContent = message;

    var anchor = container.querySelector(".admin-subprocess-actions-v1");
    if (anchor && anchor.parentNode === container) {
      container.insertBefore(feedback, anchor);
    } else {
      container.appendChild(feedback);
    }

    return feedback;
  }

  function _showSessoesSaveAjaxErrorV1(form, message) {
    var safeMessage = _normalizeSessoesAjaxMessageV1(message, "Não foi possível gravar a sessão.");
    _clearSessoesSaveAjaxFeedbackV1(form);
    _insertSessoesSaveAjaxFeedbackV1(form, "alert error", safeMessage);
  }

  function _showSessoesSaveAjaxSuccessV1(message) {
    var safeMessage = _normalizeSessoesAjaxMessageV1(message, "Sessão atualizada com sucesso.");

    if (
      window.AppGenesisProcessShell &&
      typeof window.AppGenesisProcessShell.showToast === "function"
    ) {
      window.AppGenesisProcessShell.showToast({
        type: "success",
        message: safeMessage
      });
      return;
    }

    var createCard = document.getElementById("admin-sidebar-sections-card");
    if (!createCard) {
      return;
    }

    _clearSessoesSaveAjaxFeedbackV1(createCard);
    _insertSessoesSaveAjaxFeedbackV1(createCard, "alert ok", safeMessage);
  }

  function _setSessoesSaveButtonStateV1(button, isPending, originalText) {
    if (!button) {
      return;
    }

    button.disabled = Boolean(isPending);
    button.textContent = isPending ? "A gravar..." : originalText;
  }

  function _buildCleanSessoesUrlV1(rawUrl) {
    var url;

    try {
      url = new URL(rawUrl || window.location.href, window.location.origin);
    } catch (error) {
      url = new URL(window.location.href);
    }

    [
      "sidebar_section_edit_key",
      "dynamic_process_section",
      "appgenesis_after_save",
      "success",
      "error",
      "sidebar_section_return_url"
    ].forEach(function (paramName) {
      url.searchParams.delete(paramName);
    });

    url.searchParams.set("menu", "sessoes");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.hash = "admin-sidebar-sections-card";

    return url.pathname + url.search + url.hash;
  }

  function _replaceHistoryUrlV1(nextUrl) {
    if (!nextUrl || !window.history || typeof window.history.replaceState !== "function") {
      return;
    }

    window.history.replaceState(window.history.state, document.title, nextUrl);
  }

  function _syncSidebarGlobalRefreshBaselineAfterLocalAjaxSaveV1() {
    var refreshApi = window.AppGenesisSidebarGlobalRefreshV1;

    if (
      !refreshApi ||
      typeof refreshApi.refreshBaseline !== "function"
    ) {
      return Promise.resolve();
    }

    if (typeof refreshApi.pauseOnce === "function") {
      refreshApi.pauseOnce();
    }

    return Promise.resolve(refreshApi.refreshBaseline("local_ajax_save"))
      .catch(function (error) {
        _logReturnAfterSaveAjaxV1("sidebar_refresh:sync_error", {
          error: String(error)
        });
      });
  }

  function _importRequiredCardV1(sourceDocument, cardId) {
    var sourceCard = sourceDocument ? sourceDocument.getElementById(cardId) : null;

    if (!sourceCard) {
      throw new Error("Card ausente no HTML atualizado: " + cardId);
    }

    return document.importNode(sourceCard, true);
  }

  function _ensureVisibleCardV1(card) {
    if (!card) {
      return card;
    }

    card.hidden = false;
    card.style.display = "";
    return card;
  }

  function _replaceSessoesCreateCardV1(nextCreateCard) {
    var currentCreateCard = document.getElementById("admin-sidebar-sections-card");
    var currentEditCard = document.getElementById("admin-sidebar-sections-form-card");
    var activeCard = document.getElementById("admin-sidebar-sections-card-active");
    var visibleCreateCard = _ensureVisibleCardV1(nextCreateCard);

    if (currentCreateCard && currentCreateCard.parentNode) {
      currentCreateCard.replaceWith(visibleCreateCard);
      return visibleCreateCard;
    }

    if (currentEditCard && currentEditCard.parentNode) {
      currentEditCard.replaceWith(visibleCreateCard);
      return visibleCreateCard;
    }

    if (activeCard && activeCard.parentNode) {
      activeCard.parentNode.insertBefore(visibleCreateCard, activeCard);
      return visibleCreateCard;
    }

    throw new Error("Não foi possível localizar a área principal de Sessões para substituir o card.");
  }

  function _replaceSessoesListCardV1(cardId, nextCard) {
    var currentCard = document.getElementById(cardId);

    if (!currentCard || !currentCard.parentNode) {
      throw new Error("Card atual não encontrado: " + cardId);
    }

    currentCard.replaceWith(nextCard);
    return nextCard;
  }

  function _enhanceSessoesCardsV1(cards) {
    var uniqueRoots = [];
    var seenRoots = new Set();

    cards.forEach(function (card) {
      if (!card || seenRoots.has(card)) {
        return;
      }

      seenRoots.add(card);
      uniqueRoots.push(card);
      instalarOrdenacaoAdminSubprocessV1(card);
    });

    if (window.AppGenesisProcessShell) {
      uniqueRoots.forEach(function (root) {
        if (typeof window.AppGenesisProcessShell.enhanceSearchableTableCards === "function") {
          window.AppGenesisProcessShell.enhanceSearchableTableCards({ root: root });
        }

        if (typeof window.AppGenesisProcessShell.enhanceLoadMoreTables === "function") {
          window.AppGenesisProcessShell.enhanceLoadMoreTables({ root: root });
        }

        if (typeof window.AppGenesisProcessShell.enhanceTableActionMenus === "function") {
          window.AppGenesisProcessShell.enhanceTableActionMenus({ root: root });
        }

        if (typeof window.AppGenesisProcessShell.enhanceResponsiveTableColumns === "function") {
          window.AppGenesisProcessShell.enhanceResponsiveTableColumns({ root: root });
        }
      });

      if (typeof window.AppGenesisProcessShell.enhanceConfirmableActions === "function") {
        window.AppGenesisProcessShell.enhanceConfirmableActions({ root: document });
      }
    }

    if (typeof window.AppGenesisAplicarVisibilidadeCardsSessoesV25 === "function") {
      window.AppGenesisAplicarVisibilidadeCardsSessoesV25();
    }

    if (typeof window.AppGenesisAplicarVisibilidadeSessoesSemPiscarV26 === "function") {
      window.AppGenesisAplicarVisibilidadeSessoesSemPiscarV26(document);
    }
  }

  function _refreshSessoesCardsWithoutReloadV1(cleanUrl) {
    return fetch(cleanUrl, {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Accept": "text/html"
      }
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }

        return response.text();
      })
      .then(function (html) {
        var parser = new DOMParser();
        var sourceDocument = parser.parseFromString(html, "text/html");

        var createCard = _importRequiredCardV1(sourceDocument, "admin-sidebar-sections-card");
        var activeCard = _importRequiredCardV1(sourceDocument, "admin-sidebar-sections-card-active");
        var inactiveCard = _importRequiredCardV1(sourceDocument, "admin-sidebar-sections-card-inactive");

        var mountedCreateCard = _replaceSessoesCreateCardV1(createCard);
        var mountedActiveCard = _replaceSessoesListCardV1("admin-sidebar-sections-card-active", activeCard);
        var mountedInactiveCard = _replaceSessoesListCardV1("admin-sidebar-sections-card-inactive", inactiveCard);

        _enhanceSessoesCardsV1([
          mountedCreateCard,
          mountedActiveCard,
          mountedInactiveCard
        ]);

        return {
          createCard: mountedCreateCard,
          activeCard: mountedActiveCard,
          inactiveCard: mountedInactiveCard
        };
      });
  }

  function _submitSessoesSaveFallbackV1(form) {
    if (
      typeof HTMLFormElement !== "undefined" &&
      HTMLFormElement.prototype &&
      typeof HTMLFormElement.prototype.submit === "function"
    ) {
      HTMLFormElement.prototype.submit.call(form);
      return;
    }

    form.submit();
  }

  function _markSessoesFallbackSubmitErrorV1(error) {
    var safeError = error instanceof Error ? error : new Error(String(error || "fallback_submit"));
    safeError._appgenesisShouldFallbackSubmit = true;
    return safeError;
  }

  function instalarSessoesSaveAjaxV1() {
    if (window.__appgenesisSessoesSaveAjaxV1 === true) {
      return;
    }

    window.__appgenesisSessoesSaveAjaxV1 = true;

    document.addEventListener("submit", function (event) {
      var form = event.target;
      if (!form || !_isSessoesSaveFormAjaxV1(form)) {
        return;
      }

      if (
        typeof window.fetch !== "function" ||
        typeof window.FormData !== "function" ||
        typeof window.DOMParser !== "function"
      ) {
        return;
      }

      if (form.dataset.sessoesAjaxSubmittingV1 === "1") {
        event.preventDefault();
        return;
      }

      event.preventDefault();
      form.dataset.sessoesAjaxSubmittingV1 = "1";
      _clearSessoesSaveAjaxFeedbackV1(form);

      var submitBtn = event.submitter || form.querySelector("[type='submit']");
      var originalBtnText = submitBtn ? (submitBtn.textContent || "").trim() : "";
      _setSessoesSaveButtonStateV1(submitBtn, true, originalBtnText);

      _logReturnAfterSaveAjaxV1("ajax:start", {
        form_action: form.getAttribute("action") || ""
      });

      fetch(form.action, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "Accept": "application/json"
        },
        body: new FormData(form)
      })
        .catch(function (error) {
          throw _markSessoesFallbackSubmitErrorV1(error);
        })
        .then(function (response) {
          return response.text().then(function (body) {
            var data = {};

            try {
              data = body ? JSON.parse(body) : {};
            } catch (error) {
              throw _markSessoesFallbackSubmitErrorV1(error);
            }

            return { status: response.status, ok: response.ok, data: data || {} };
          });
        })
        .then(function (result) {
          var data = result.data || {};
          var cleanRedirectUrl = _buildCleanSessoesUrlV1(data.redirect_url || window.location.href);

          _logReturnAfterSaveAjaxV1("ajax:response", {
            ok: data.ok,
            http_ok: result.ok,
            status: result.status,
            redirect_url: data.redirect_url || "",
            clean_redirect_url: cleanRedirectUrl
          });

          if (!data.ok) {
            throw new Error(_normalizeSessoesAjaxMessageV1(
              data.message || data.error,
              "Não foi possível gravar a sessão."
            ));
          }

          return _refreshSessoesCardsWithoutReloadV1(cleanRedirectUrl)
            .then(function () {
              _replaceHistoryUrlV1(cleanRedirectUrl);
              return _syncSidebarGlobalRefreshBaselineAfterLocalAjaxSaveV1();
            })
            .then(function () {
              _showSessoesSaveAjaxSuccessV1(data.message);
            });
        })
        .then(function () {
          delete form.dataset.sessoesAjaxSubmittingV1;
        })
        .catch(function (error) {
          var message = _normalizeSessoesAjaxMessageV1(
            error && error.message,
            "Não foi possível gravar a sessão."
          );

          _logReturnAfterSaveAjaxV1("ajax:error", {
            error: String(message || error)
          });

          delete form.dataset.sessoesAjaxSubmittingV1;
          _setSessoesSaveButtonStateV1(submitBtn, false, originalBtnText);

          if (error && error._appgenesisShouldFallbackSubmit === true) {
            _submitSessoesSaveFallbackV1(form);
            return;
          }

          _showSessoesSaveAjaxErrorV1(form, message);
        });
    }, false);
  }

  //###################################################################################
  // (5) INICIAR
  //###################################################################################

  function instalarAdminSubprocessesV1() {
    instalarVisualizarAdminSubprocessV1();
    instalarInlineCreateToggleAdminSubprocessV1();
    instalarOrdenacaoAdminSubprocessV1(document);
    initAdminResponsiveColumnsV1();
    instalarSessoesSaveAjaxV1();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarAdminSubprocessesV1);
  }
  else {
    instalarAdminSubprocessesV1();
  }
})();
// APPGENESIS_ADMIN_SUBPROCESSES_V1_END
