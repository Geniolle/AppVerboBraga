//###################################################################################
// APPGENESIS - PROCESS LISTS MANAGER V1
//###################################################################################

(function (window, document) {
  "use strict";

  const FORM_SELECTOR = "form[data-process-lists-manager-v1='1']";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function getCore_v1() {
    return window.AppGenesisConfigurableItems || {};
  }

  function toSafeString_v1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeKey_v1(value) {
    return toSafeString_v1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function readProcessListAllSessionsKey_v1() {
    const bootstrap = window.__APPGENESIS_BOOTSTRAP__ || {};
    return normalizeKey_v1(bootstrap.processListAllSessionsKey || "all_sessions") || "all_sessions";
  }

  function readProcessListAllSessionsLabel_v1() {
    const bootstrap = window.__APPGENESIS_BOOTSTRAP__ || {};
    return toSafeString_v1(bootstrap.processListAllSessionsLabel || "Todas as sessões").trim() || "Todas as sessões";
  }

  function isProcessListAllSessionsKey_v1(value) {
    return normalizeKey_v1(value) === readProcessListAllSessionsKey_v1();
  }

  function normalizeProcessListStatus_v1(rawStatus, rawIsActive) {
    const cleanStatus = normalizeKey_v1(rawStatus);
    const cleanIsActive = toSafeString_v1(rawIsActive).trim().toLowerCase();

    if (rawStatus === false || cleanStatus === "false" || cleanIsActive === "false" || cleanIsActive === "0") {
      return "inativo";
    }

    if (rawStatus === true || cleanStatus === "true" || cleanIsActive === "true" || cleanIsActive === "1") {
      return "ativo";
    }

    if (cleanStatus === "inactive" || cleanStatus === "inativo" || cleanStatus === "inativa") {
      return "inativo";
    }

    if (cleanStatus === "active" || cleanStatus === "ativo" || cleanStatus === "ativa") {
      return "ativo";
    }

    return "ativo";
  }

  function normalizeProcessListSourceSessionOptions_v1(sourceSessionOptions) {
    const normalized = [];
    const seenValues = new Set();
    const allSessionsKey = readProcessListAllSessionsKey_v1();
    const allSessionsLabel = readProcessListAllSessionsLabel_v1();

    normalized.push({
      value: allSessionsKey,
      label: allSessionsLabel
    });
    seenValues.add(allSessionsKey);

    (Array.isArray(sourceSessionOptions) ? sourceSessionOptions : []).forEach((rawOption) => {
      if (!rawOption || typeof rawOption !== "object") {
        return;
      }

      const value = toSafeString_v1(rawOption.value || rawOption.key || "").trim().toLowerCase();
      const label = toSafeString_v1(rawOption.label || rawOption.value || rawOption.key || "").trim();

      if (!value || !label || seenValues.has(value)) {
        return;
      }

      seenValues.add(value);
      normalized.push({
        value,
        label
      });
    });

    return normalized;
  }

  function filterProcessListSourceMenuOptions_v1(sourceMenuOptions, selectedSessionKey) {
    const normalizedSessionKey = normalizeKey_v1(selectedSessionKey);
    const normalizedAllSessionsKey = readProcessListAllSessionsKey_v1();
    const seenMenuKeys = new Set();

    if (!normalizedSessionKey) {
      return [];
    }

    return (Array.isArray(sourceMenuOptions) ? sourceMenuOptions : []).filter((rawOption) => {
      if (!rawOption || typeof rawOption !== "object") {
        return false;
      }

      const menuKey = toSafeString_v1(rawOption.value || rawOption.key || "").trim().toLowerCase();
      const menuLabel = toSafeString_v1(rawOption.label || rawOption.value || rawOption.key || "").trim();
      const sourceSessionKey = toSafeString_v1(rawOption.sourceSessionKey || "").trim().toLowerCase();

      if (!menuKey || !menuLabel || !sourceSessionKey) {
        return false;
      }
      if (seenMenuKeys.has(menuKey)) {
        return false;
      }
      if (normalizedSessionKey !== normalizedAllSessionsKey && sourceSessionKey !== normalizedSessionKey) {
        return false;
      }

      seenMenuKeys.add(menuKey);
      return true;
    });
  }

  function readProcessListSourceMenusFromBootstrap_v1() {
    const bootstrap = window.__APPGENESIS_BOOTSTRAP__ || {};
    const rawMenus = Array.isArray(bootstrap.processListSourceMenus)
      ? bootstrap.processListSourceMenus
      : [];
    const normalized = [];
    const seenMenuKeys = new Set();

    rawMenus.forEach((rawMenu) => {
      if (!rawMenu || typeof rawMenu !== "object") {
        return;
      }

      const value = toSafeString_v1(rawMenu.menu_key || rawMenu.value || rawMenu.key || "").trim().toLowerCase();
      const label = toSafeString_v1(rawMenu.menu_label || rawMenu.label || rawMenu.value || rawMenu.key || "").trim();
      const sourceSessionKey = toSafeString_v1(
        rawMenu.sidebar_section_key || rawMenu.source_session_key || rawMenu.sourceSessionKey || ""
      ).trim().toLowerCase();
      const sourceSessionLabel = toSafeString_v1(
        rawMenu.sidebar_section_label || rawMenu.source_session_label || rawMenu.sourceSessionLabel || ""
      ).trim();

      if (!value || !label || seenMenuKeys.has(value)) {
        return;
      }

      seenMenuKeys.add(value);
      normalized.push({
        value,
        label,
        sourceSessionKey,
        sourceSessionLabel
      });
    });

    return normalized;
  }

  function showValidationMessage_v1(message) {
    const core = getCore_v1();

    if (typeof core.showAlertDialog_v1 === "function") {
      core.showAlertDialog_v1({
        title: "Validacao",
        message
      });
      return;
    }

    if (
      window.AppGenesisDialogV1 &&
      typeof window.AppGenesisDialogV1.alert === "function"
    ) {
      window.AppGenesisDialogV1.alert({
        title: "Validacao",
        message
      });
      return;
    }

    if (window.console && typeof window.console.warn === "function") {
      window.console.warn("[ProcessListsManagerV1]", message);
    }
  }

  function submitNative_v1(form) {
    HTMLFormElement.prototype.submit.call(form);
  }

  function nowMs_v1() {
    if (window.performance && typeof window.performance.now === "function") {
      return window.performance.now();
    }

    return Date.now();
  }

  function isProcessListsPerfLogsEnabled_v1() {
    const bootstrap = window.__APPGENESIS_BOOTSTRAP__ || {};
    const rawFlag = bootstrap.processListsPerfLogs
      ?? bootstrap.perfLogsEnabled
      ?? window.APPGENESIS_PERF_LOGS
      ?? "";
    const cleanFlag = String(rawFlag).trim().toLowerCase();

    return cleanFlag === "1" || cleanFlag === "true" || cleanFlag === "yes";
  }

  function createProcessListsPerfState_v1() {
    return {
      enabled: isProcessListsPerfLogsEnabled_v1(),
      cycleStart: nowMs_v1(),
      readMs: 0,
      renderMs: 0,
      responsiveMs: 0,
      responsiveTables: 0,
      backendCount: 0,
      initialCount: 0,
      stateCount: 0,
      activeCount: 0,
      inactiveCount: 0,
      hasLoggedInitial: false
    };
  }

  function logProcessListsPerfSummary_v1(perfState) {
    if (!perfState || !perfState.enabled) {
      return;
    }

    const totalMs = Math.max(0, Math.round(nowMs_v1() - perfState.cycleStart));
    const readMs = Math.max(0, Math.round(perfState.readMs || 0));
    const renderMs = Math.max(0, Math.round(perfState.renderMs || 0));
    const responsiveMs = Math.max(0, Math.round(perfState.responsiveMs || 0));
    const backendCount = Math.max(0, Number.parseInt(perfState.backendCount, 10) || 0);
    const initialCount = Math.max(0, Number.parseInt(perfState.initialCount, 10) || 0);
    const stateCount = Math.max(0, Number.parseInt(perfState.stateCount, 10) || 0);
    const activeCount = Math.max(0, Number.parseInt(perfState.activeCount, 10) || 0);
    const inactiveCount = Math.max(0, Number.parseInt(perfState.inactiveCount, 10) || 0);
    const responsiveTables = Math.max(0, Number.parseInt(perfState.responsiveTables, 10) || 0);
    const summary = `[PERF][ProcessLists] total=${totalMs}ms read=${readMs}ms render=${renderMs}ms responsive=${responsiveMs}ms tables=${responsiveTables} active=${activeCount} inactive=${inactiveCount}`;
    const aggregatedSummary = `[PERF][ProcessLists] backend=${backendCount} initial=${initialCount} state=${stateCount} active=${activeCount} inactive=${inactiveCount} total=${totalMs}ms`;

    if (window.console && typeof window.console.info === "function") {
      window.console.info(summary);
      window.console.info(aggregatedSummary);
    }

    perfState.cycleStart = nowMs_v1();
    perfState.readMs = 0;
    perfState.renderMs = 0;
    perfState.responsiveMs = 0;
    perfState.responsiveTables = 0;
    perfState.hasLoggedInitial = true;
  }

  //###################################################################################
  // (2) ELEMENTOS E LEITURA INICIAL
  //###################################################################################

  function getElements_v1(form) {
    const root = form.querySelector("[data-process-list-reusable-manager]");

    if (!root) {
      return null;
    }

    return {
      root,
      menuKeyInput: form.querySelector("input[name='menu_key']"),
      legacyContainer: root.querySelector("[data-process-lists-legacy-container]"),
      hiddenContainer: root.querySelector("[data-process-lists-hidden-container]"),
      editorKey: root.querySelector("[data-process-list-editor-key]"),
      editorLabel: root.querySelector("[data-process-list-editor-label]"),
      editorItems: root.querySelector("[data-process-list-editor-items]"),
      editorItemsWrapper: root.querySelector("[data-process-list-editor-items-wrapper]"),
      editorFieldType: root.querySelector("[data-process-list-editor-field-type]"),
      editorSourceSession: root.querySelector("[data-process-list-editor-source-session]"),
      editorSourceSessionWrapper: root.querySelector("[data-process-list-editor-session-wrapper]"),
      editorSourceMenu: root.querySelector("[data-process-list-editor-source-menu]"),
      editorSourceMenuWrapper: root.querySelector("[data-process-list-editor-menu-wrapper]"),
      editorSourceSubprocess: root.querySelector("[data-process-list-editor-source-subprocess]"),
      editorSourceSubprocessWrapper: root.querySelector("[data-process-list-editor-subprocess-wrapper]"),
      editorStatus: root.querySelector("[data-process-list-editor-status]"),
      sourceSessionOptionsScript: root.querySelector("[data-process-list-source-sessions]"),
      sourceSubprocessMapScript: root.querySelector("[data-process-list-source-subprocess-map]"),
      submitButton: root.querySelector("[data-process-list-editor-submit]"),
      cancelButton: root.querySelector("[data-process-list-editor-cancel]"),
      table: root.querySelector("[data-process-lists-table]"),
      tableBody: root.querySelector("[data-process-lists-table-body]"),
      emptyState: root.querySelector("[data-process-lists-empty]"),
      inactiveTable: root.querySelector("[data-process-lists-inactive-table]"),
      inactiveTableBody: root.querySelector("[data-process-lists-inactive-table-body]"),
      inactiveEmptyState: root.querySelector("[data-process-lists-inactive-empty]"),
      inactiveTotalLabel: root.querySelector("[data-process-lists-inactive-total-label]"),
      inactivePageSize: root.querySelector("[data-process-lists-inactive-page-size]"),
      inactivePagination: root.querySelector("[data-process-lists-inactive-pagination]"),
      totalLabel: root.querySelector("[data-process-lists-total-label]"),
      pageSize: root.querySelector("[data-process-lists-page-size]"),
      pagination: root.querySelector("[data-process-lists-pagination]"),
      searchInput: root.querySelector("[data-configurable-search]")
    };
  }

  function getProcessListsDeleteEndpoint_v1(form) {
    if (!form) {
      return "/settings/menu/process-lists/delete";
    }

    const rawAction = toSafeString_v1(form.getAttribute("action") || "").trim();
    if (!rawAction) {
      return "/settings/menu/process-lists/delete";
    }

    return `${rawAction.replace(/\/?$/, "")}/delete`;
  }

  function hasRequiredElements_v1(elements) {
    return Boolean(
      elements &&
      elements.root &&
      elements.menuKeyInput &&
      elements.legacyContainer &&
      elements.hiddenContainer &&
      elements.editorKey &&
      elements.editorLabel &&
      elements.editorFieldType &&
      elements.editorSourceSession &&
      elements.editorSourceSessionWrapper &&
      elements.editorItems &&
      elements.editorItemsWrapper &&
      elements.editorSourceMenu &&
      elements.editorSourceMenuWrapper &&
      elements.editorSourceSubprocess &&
      elements.editorSourceSubprocessWrapper &&
      elements.editorStatus &&
      elements.submitButton &&
      elements.cancelButton &&
      elements.table &&
      elements.tableBody &&
      elements.emptyState &&
      elements.pageSize &&
      elements.pagination &&
      elements.inactivePageSize &&
      elements.inactivePagination
    );
  }

  function readInput_v1(row, name) {
    const input = row.querySelector(`[name='${name}']`);
    return input ? toSafeString_v1(input.value).trim() : "";
  }

  function readInitialItems_v1(elements, sourceMenuOptions) {
    const rows = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-list-row]")
    );

    return rows
      .map((row, index) => {
        const label = readInput_v1(row, "process_list_label");
        const key = readInput_v1(row, "process_list_key") || normalizeKey_v1(label) || `lista_${index + 1}`;
        const fieldType = (readInput_v1(row, "process_list_field_type") || "").trim().toLowerCase();
        const itemsCsv = readInput_v1(row, "process_list_items_csv");
        const sourceMenuKey = readInput_v1(row, "process_list_source_menu_key");
        const sourceSessionKey = readInput_v1(row, "process_list_source_session_key") ||
          getSourceSessionKeyFromMenuOptions_v1(sourceMenuOptions, sourceMenuKey);
        const sourceSubprocessKey = readInput_v1(row, "process_list_source_subprocess_key");
        const status = normalizeProcessListStatus_v1(
          readInput_v1(row, "process_list_status"),
          readInput_v1(row, "process_list_is_active")
        );

        return {
          managerId: `list_${index}_${key}`,
          key,
          label,
          field_type: fieldType || "manual",
          itemsCsv,
          sourceSessionKey,
          sourceMenuKey,
          sourceSubprocessKey,
          status
        };
      })
      .filter((item) => item.label || item.itemsCsv);
  }

  function getSourceSubprocessMap_v1(elements) {
    if (!elements || !elements.sourceSubprocessMapScript) {
      return {};
    }

    const rawText = toSafeString_v1(elements.sourceSubprocessMapScript.textContent).trim();

    if (!rawText) {
      return {};
    }

    try {
      const parsed = JSON.parse(rawText);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
    } catch (error) {
      if (window.console && typeof window.console.warn === "function") {
        window.console.warn("[ProcessListsManagerV1] mapa de subprocessos invalido", error);
      }
      return {};
    }
  }

  function readSourceSessionOptionsFromElement_v1(elements) {
    if (!elements) {
      return [];
    }

    const sourceElement = elements.sourceSessionOptionsScript || elements.editorSourceSession;
    if (!sourceElement) {
      return [];
    }

    const rawText = sourceElement.tagName === "SCRIPT"
      ? toSafeString_v1(sourceElement.textContent).trim()
      : "";

    if (rawText) {
      try {
        const parsed = JSON.parse(rawText);
        const rawItems = Array.isArray(parsed) ? parsed : [];
        const normalized = [];
        const seen = new Set();

        rawItems.forEach((rawItem) => {
          if (!rawItem || typeof rawItem !== "object") {
            return;
          }

          const value = toSafeString_v1(
            rawItem.key ||
            rawItem.section_key ||
            rawItem.sidebar_section_key ||
            rawItem.value ||
            rawItem.menu_section ||
            ""
          ).trim().toLowerCase();
          const label = toSafeString_v1(
            rawItem.label ||
            rawItem.name ||
            rawItem.section_label ||
            rawItem.value ||
            rawItem.key ||
            ""
          ).trim();
          const status = toSafeString_v1(
            rawItem.status !== undefined ? rawItem.status : rawItem.is_active
          ).trim().toLowerCase();
          const isInactive = status === "inativo" || status === "inactive" || status === "false" || status === "0";

          if (!value || !label || isInactive) {
            return;
          }

          if (seen.has(value)) {
            return;
          }

          seen.add(value);
          normalized.push({ value, label });
        });

        return normalized;
      } catch (error) {
        if (window.console && typeof window.console.warn === "function") {
          window.console.warn("[ProcessListsManagerV1] secções de sessão invalidas", error);
        }
      }
    }

    if (sourceElement.tagName !== "SELECT") {
      return [];
    }

    return Array.from(sourceElement.options)
      .map((option) => ({
        value: toSafeString_v1(option.value).trim(),
        label: toSafeString_v1(option.textContent).trim()
      }))
      .filter((option) => option.value && option.label);
  }

  function readSourceSessionOptions_v1(elements) {
    return readSourceSessionOptionsFromElement_v1(elements);
  }

  function readSourceMenuOptions_v1(elements) {
    const bootstrapSourceMenus = readProcessListSourceMenusFromBootstrap_v1();
    if (bootstrapSourceMenus.length) {
      return bootstrapSourceMenus;
    }

    if (!elements || !elements.editorSourceMenu) {
      return [];
    }

    return Array.from(elements.editorSourceMenu.options)
      .map((option) => ({
        value: toSafeString_v1(option.value).trim(),
        label: toSafeString_v1(option.textContent).trim(),
        sourceSessionKey: toSafeString_v1(
          option.dataset.processListSourceSessionKey || option.dataset.sourceSessionKey || ""
        ).trim().toLowerCase(),
        sourceSessionLabel: toSafeString_v1(
          option.dataset.processListSourceSessionLabel || option.dataset.sourceSessionLabel || ""
        ).trim()
      }))
      .filter((option) => option.value && option.label);
  }

  function refreshAutomaticSourceOptions_v1(context) {
    const elements = context && context.elements ? context.elements : null;

    if (!elements) {
      return {
        sourceSessionOptions: [],
        sourceMenuOptions: [],
        sourceSubprocessMap: {}
      };
    }

    const sourceSessionOptionsSnapshot = Array.isArray(
      context && context.manager && context.manager.sourceSessionOptionsSnapshot
    )
      ? context.manager.sourceSessionOptionsSnapshot
      : Array.isArray(context && context.sourceSessionOptionsSnapshot)
        ? context.sourceSessionOptionsSnapshot
      : normalizeProcessListSourceSessionOptions_v1(readSourceSessionOptions_v1(elements));
    const sourceMenuOptionsSnapshot = Array.isArray(
      context && context.manager && context.manager.sourceMenuOptionsSnapshot
    )
      ? context.manager.sourceMenuOptionsSnapshot
      : Array.isArray(context && context.sourceMenuOptionsSnapshot)
        ? context.sourceMenuOptionsSnapshot
      : readSourceMenuOptions_v1(elements);
    const sourceSessionOptions = normalizeProcessListSourceSessionOptions_v1(sourceSessionOptionsSnapshot);
    const sourceMenuOptions = Array.isArray(sourceMenuOptionsSnapshot) ? sourceMenuOptionsSnapshot : [];
    const sourceSubprocessMap = getSourceSubprocessMap_v1(elements);

    if (context) {
      context.sourceSessionOptions = sourceSessionOptions;
      context.sourceMenuOptions = sourceMenuOptions;
      context.sourceSubprocessMap = sourceSubprocessMap;
      if (!Array.isArray(context.sourceSessionOptionsSnapshot)) {
        context.sourceSessionOptionsSnapshot = sourceSessionOptions;
      }
      if (!Array.isArray(context.sourceMenuOptionsSnapshot)) {
        context.sourceMenuOptionsSnapshot = sourceMenuOptions;
      }
      if (context.manager) {
        context.manager.sourceSessionOptionsSnapshot = sourceSessionOptions;
        context.manager.sourceMenuOptionsSnapshot = sourceMenuOptions;
      }
    }

    return {
      sourceSessionOptions,
      sourceMenuOptions,
      sourceSubprocessMap
    };
  }

  function populateSelectOptions_v1(select, placeholderLabel, availableOptions, selectedValue, options) {
    if (!select) {
      return false;
    }

    const preserveUnavailableSelection = Boolean(options && options.preserveUnavailableSelection);
    const unavailableLabel = toSafeString_v1(options && options.unavailableLabel ? options.unavailableLabel : "Indisponível").trim() || "Indisponível";
    const optionValue = toSafeString_v1(selectedValue).trim();
    const normalizedSelectedValue = normalizeKey_v1(optionValue);
    const normalizedOptions = Array.isArray(availableOptions) ? availableOptions : [];

    select.innerHTML = "";

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = placeholderLabel;
    select.appendChild(placeholder);

    let hasSelectedOption = false;

    normalizedOptions.forEach((rawOption) => {
      if (!rawOption || typeof rawOption !== "object") {
        return;
      }

      const value = toSafeString_v1(rawOption.value || rawOption.key || "").trim();
      const label = toSafeString_v1(rawOption.label || rawOption.value || rawOption.key || "").trim();

      if (!value || !label) {
        return;
      }

      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      if (rawOption.sourceSessionKey) {
        option.dataset.processListSourceSessionKey = toSafeString_v1(rawOption.sourceSessionKey).trim().toLowerCase();
      }
      if (rawOption.sourceSessionLabel) {
        option.dataset.processListSourceSessionLabel = toSafeString_v1(rawOption.sourceSessionLabel).trim();
      }
      if (rawOption.disabled) {
        option.disabled = true;
      }
      if (normalizedSelectedValue && normalizeKey_v1(value) === normalizedSelectedValue) {
        option.selected = true;
        hasSelectedOption = true;
      }
      select.appendChild(option);
    });

    if (optionValue && !hasSelectedOption && preserveUnavailableSelection) {
      const unavailableOption = document.createElement("option");
      unavailableOption.value = optionValue;
      unavailableOption.textContent = unavailableLabel;
      unavailableOption.selected = true;
      select.appendChild(unavailableOption);
      hasSelectedOption = true;
    }

    if (!hasSelectedOption) {
      select.value = "";
    }

    return hasSelectedOption;
  }

  function getSourceSessionKeyFromMenuOptions_v1(sourceMenuOptions, menuKey) {
    const selectedMenuKey = normalizeKey_v1(menuKey);
    if (!selectedMenuKey) {
      return "";
    }

    const selectedMenuOption = Array.isArray(sourceMenuOptions)
      ? sourceMenuOptions.find((option) => normalizeKey_v1(option.value) === selectedMenuKey)
      : null;

    return toSafeString_v1(selectedMenuOption && selectedMenuOption.sourceSessionKey ? selectedMenuOption.sourceSessionKey : "").trim().toLowerCase();
  }

  function updateAutomaticSourceControls_v1(context, options) {
    const elements = context && context.elements ? context.elements : null;

    if (!elements || !elements.editorSourceSession || !elements.editorSourceMenu || !elements.editorSourceSubprocess) {
      return;
    }

    const refreshedOptions = refreshAutomaticSourceOptions_v1(context);
    const sourceSessionOptions = Array.isArray(refreshedOptions.sourceSessionOptions)
      ? refreshedOptions.sourceSessionOptions
      : [];
    const sourceMenuOptions = Array.isArray(refreshedOptions.sourceMenuOptions)
      ? refreshedOptions.sourceMenuOptions
      : [];
    const sourceSubprocessMap = refreshedOptions.sourceSubprocessMap || {};
    const isHydratingEditor = Boolean(context && context.isHydratingEditor);
    const keepVisible = Boolean(options && options.keepVisible);
    const preserveUnavailableSelection = Boolean(options && options.preserveUnavailableSelection) && !isHydratingEditor;
    const selectedSessionKey = toSafeString_v1(
      options && Object.prototype.hasOwnProperty.call(options, "selectedSessionKey")
        ? options.selectedSessionKey
        : elements.editorSourceSession.value
    ).trim().toLowerCase();
    const selectedMenuKey = toSafeString_v1(
      options && Object.prototype.hasOwnProperty.call(options, "selectedMenuKey")
        ? options.selectedMenuKey
        : elements.editorSourceMenu.value
    ).trim().toLowerCase();
    const selectedSubprocessKey = toSafeString_v1(
      options && Object.prototype.hasOwnProperty.call(options, "selectedSubprocessKey")
        ? options.selectedSubprocessKey
        : elements.editorSourceSubprocess.value
    ).trim().toLowerCase();
    const allSessionsKey = readProcessListAllSessionsKey_v1();

    const resolvedSessionKey = selectedSessionKey || getSourceSessionKeyFromMenuOptions_v1(sourceMenuOptions, selectedMenuKey);
    const normalizedResolvedSessionKey = normalizeKey_v1(resolvedSessionKey);

    populateSelectOptions_v1(
      elements.editorSourceSession,
      "Selecione a sessão",
      sourceSessionOptions,
      normalizedResolvedSessionKey,
      {
        preserveUnavailableSelection,
        unavailableLabel: "Sessão indisponível"
      }
    );

    const normalizedSessionKey = toSafeString_v1(elements.editorSourceSession.value).trim().toLowerCase();
    if (normalizedSessionKey === allSessionsKey) {
      elements.editorSourceMenu.value = "";
      elements.editorSourceMenu.innerHTML = "";
      elements.editorSourceSubprocess.value = "";
      elements.editorSourceSubprocess.innerHTML = "";
      elements.editorSourceSession.disabled = !keepVisible;
      elements.editorSourceMenu.disabled = true;
      elements.editorSourceSubprocess.disabled = true;
      elements.editorSourceMenuWrapper.hidden = true;
      elements.editorSourceSubprocessWrapper.hidden = true;
      elements.root.dataset.hasSourceSubprocess = "0";
      return;
    }

    const filteredMenuOptions = filterProcessListSourceMenuOptions_v1(
      sourceMenuOptions,
      normalizedSessionKey
    );

    populateSelectOptions_v1(
      elements.editorSourceMenu,
      "Selecione o menu",
      filteredMenuOptions,
      selectedMenuKey,
      {
        preserveUnavailableSelection: preserveUnavailableSelection && Boolean(normalizedSessionKey),
        unavailableLabel: "Menu indisponível"
      }
    );

    const normalizedMenuKey = toSafeString_v1(elements.editorSourceMenu.value).trim().toLowerCase();
    const sourceSubprocessOptions = normalizedMenuKey
      ? getSourceSubprocessOptions_v1(sourceSubprocessMap, normalizedMenuKey)
      : [];

    populateSourceSubprocessOptions_v1(
      { elements },
      {
        options: sourceSubprocessOptions,
        selectedValue: selectedSubprocessKey,
        preserveUnavailableSelection,
        keepVisible: keepVisible && Boolean(normalizedMenuKey)
      }
    );

    elements.editorSourceSession.disabled = !keepVisible;
    elements.editorSourceMenu.disabled = !keepVisible || !normalizedSessionKey;
    elements.editorSourceSubprocess.disabled = !keepVisible || !normalizedMenuKey;
    elements.editorSourceMenuWrapper.hidden = !keepVisible;
    elements.editorSourceSubprocessWrapper.hidden = !keepVisible || !normalizedMenuKey;

    if (!normalizedSessionKey && !preserveUnavailableSelection && !isHydratingEditor) {
      elements.editorSourceMenu.value = "";
      elements.editorSourceSubprocess.value = "";
    }

    if (!normalizedMenuKey && !preserveUnavailableSelection && !isHydratingEditor) {
      elements.editorSourceSubprocess.value = "";
    }
  }

  function normalizeSourceSubprocessOptions_v1(rawOptions) {
    if (!Array.isArray(rawOptions)) {
      return [];
    }

    const options = [];
    const seen = new Set();

    rawOptions.forEach((rawOption) => {
      if (!rawOption || typeof rawOption !== "object") {
        return;
      }

      const value = toSafeString_v1(rawOption.value || rawOption.key).trim();
      const label = toSafeString_v1(rawOption.label || rawOption.value || rawOption.key).trim();

      if (!value || !label) {
        return;
      }

      const lookup = value.toLowerCase();
      if (seen.has(lookup)) {
        return;
      }

      seen.add(lookup);
      options.push({ value, label });
    });

    return options;
  }

  function getSourceSubprocessOptions_v1(sourceSubprocessMap, menuKey) {
    const cleanMenuKey = normalizeKey_v1(menuKey);
    return normalizeSourceSubprocessOptions_v1(
      sourceSubprocessMap && cleanMenuKey ? sourceSubprocessMap[cleanMenuKey] : []
    );
  }

  //###################################################################################
  // (3) COLUNAS DA LISTAGEM DO PROCESSO
  //###################################################################################

  function getColumnElements_v2(form) {
    const root = form.querySelector("[data-process-list-columns-manager]");

    if (!root) {
      return null;
    }

    return {
      root,
      legacyContainer: root.querySelector("[data-process-list-columns-legacy-container]"),
      hiddenContainer: root.querySelector("[data-process-list-columns-hidden-container]"),
      editorKey: root.querySelector("[data-process-list-column-editor-key]"),
      editorField: root.querySelector("[data-process-list-column-editor-field]"),
      editorLabel: root.querySelector("[data-process-list-column-editor-label]"),
      editorSourceKind: root.querySelector("[data-process-list-column-editor-source-kind]"),
      editorAlwaysVisible: root.querySelector("[data-process-list-column-editor-always-visible]"),
      editorPriority: root.querySelector("[data-process-list-column-editor-priority]"),
      submitButton: root.querySelector("[data-process-list-column-editor-submit]"),
      cancelButton: root.querySelector("[data-process-list-column-editor-cancel]"),
      pageSize: root.querySelector("[data-process-list-columns-page-size]")
    };
  }

  function readInitialColumns_v2(elements) {
    return Array.from(elements.legacyContainer.querySelectorAll("[data-process-list-column-row]"))
      .map((row, index) => {
        const fieldKey = readInput_v1(row, "process_list_column_field_key");
        const key = readInput_v1(row, "process_list_column_key") || fieldKey;

        return {
          managerId: `column_${index}_${key}`,
          key,
          label: readInput_v1(row, "process_list_column_label"),
          fieldKey,
          sourceKind: readInput_v1(row, "process_list_column_source_kind") || "field",
          alwaysVisible: readInput_v1(row, "process_list_column_always_visible") === "1",
          responsivePriority: Number.parseInt(readInput_v1(row, "process_list_column_responsive_priority"), 10) || 0
        };
      })
      .filter((item) => item.fieldKey);
  }

  function clearColumnEditor_v2(context) {
    const elements = context && context.elements ? context.elements : context;

    if (!elements) {
      return;
    }

    elements.editorKey.value = "";
    elements.editorField.value = "";
    elements.editorLabel.value = "";
    elements.editorAlwaysVisible.checked = false;
    elements.editorPriority.value = "0";
  }

  function loadColumnEditorItem_v2(item, context) {
    const elements = context && context.elements ? context.elements : null;

    if (!item || !elements) {
      return;
    }

    elements.editorKey.value = item.key || "";
    elements.editorField.value = item.fieldKey || "";
    elements.editorLabel.value = item.label || "";
    elements.editorAlwaysVisible.checked = Boolean(item.alwaysVisible);
    elements.editorPriority.value = String(item.responsivePriority || 0);
    elements.editorField.focus();
  }

  function readColumnEditorItem_v2(context) {
    const elements = context.elements;
    const fieldKey = toSafeString_v1(elements.editorField.value).trim();
    const selectedOption = elements.editorField.options[elements.editorField.selectedIndex];
    const label = toSafeString_v1(elements.editorLabel.value).trim() ||
      toSafeString_v1(selectedOption ? selectedOption.textContent : "").trim();
    const currentKey = toSafeString_v1(elements.editorKey.value).trim();

    return {
      managerId: toSafeString_v1(context.state.editingId).trim() || `tmp_column_${Date.now()}`,
      key: currentKey || fieldKey,
      label,
      fieldKey,
      sourceKind: "field",
      alwaysVisible: Boolean(elements.editorAlwaysVisible.checked),
      responsivePriority: Number.parseInt(elements.editorPriority.value, 10) || 0
    };
  }

  function validateColumnItem_v2(item, context) {
    if (!item.fieldKey) {
      return { valid: false, message: "Selecione o campo da coluna." };
    }

    const editingId = toSafeString_v1(context.state.editingId).trim();
    const duplicate = context.items.some((existing) => {
      const existingId = toSafeString_v1(existing.__managerId || existing.managerId).trim();
      return existingId !== editingId && existing.fieldKey === item.fieldKey;
    });

    return duplicate
      ? { valid: false, message: "Este campo já está configurado como coluna." }
      : { valid: true };
  }

  function syncColumnHiddenInputs_v2(context) {
    const elements = context.elements;
    elements.hiddenContainer.innerHTML = "";

    context.items.forEach((item) => {
      [
        ["process_list_column_key", item.key],
        ["process_list_column_label", item.label],
        ["process_list_column_field_key", item.fieldKey],
        ["process_list_column_source_kind", item.sourceKind || "field"],
        ["process_list_column_always_visible", item.alwaysVisible ? "1" : "0"],
        ["process_list_column_responsive_priority", String(item.responsivePriority || 0)]
      ].forEach((field) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = field[0];
        input.value = field[1] || "";
        elements.hiddenContainer.appendChild(input);
      });
    });
  }

  //###################################################################################
  // (4) EDITOR E COMPATIBILIDADE DE SUBMIT
  //###################################################################################

  function clearEditor_v1(context) {
    const elements = context && context.elements ? context.elements : context;
    const manager = context && context.manager ? context.manager : null;
    const sourceSubprocessMap = context && context.sourceSubprocessMap ? context.sourceSubprocessMap : {};

    if (manager && manager.root) {
      manager.root.classList.remove("configurable-items-editing-v1");
    }

    if (!elements) {
      return;
    }

    elements.editorKey.value = "";
    elements.editorLabel.value = "";
    elements.editorItems.value = "";
    elements.editorSourceSession.value = "";
    elements.editorSourceMenu.value = "";
    elements.editorSourceSubprocess.value = "";
      if (elements.editorStatus) {
        elements.editorStatus.value = "ativo";
      }
    delete elements.editorItems.dataset.previousItems;
    if (elements.editorFieldType) {
      elements.editorFieldType.value = "manual";
    }
    applyEditorFieldTypeState_v3(
      { elements, manager, sourceSubprocessMap },
      { resetTemporaryState: true, clearSourceSelection: true }
    );
  }

  function loadEditorItem_v1(item, context) {
    const elements = context && context.elements ? context.elements : null;
    const manager = context && context.manager ? context.manager : null;
    const sourceSubprocessMap = context && context.sourceSubprocessMap ? context.sourceSubprocessMap : {};
    const sourceMenuOptions = context && Array.isArray(context.sourceMenuOptions) ? context.sourceMenuOptions : [];

    if (!item || !elements) {
      return;
    }

    if (manager && manager.root) {
      manager.root.classList.add("configurable-items-editing-v1");
    }

    if (context) {
      context.isHydratingEditor = true;
      refreshAutomaticSourceOptions_v1(context);
    }

    try {
      elements.editorKey.value = item.key || "";
      elements.editorLabel.value = item.label || "";
      elements.editorItems.value = item.itemsCsv || "";
      if (elements.editorStatus) {
        elements.editorStatus.value = normalizeProcessListStatus_v1(item.status, item.is_active);
      }
      delete elements.editorItems.dataset.previousItems;
      if (elements.editorFieldType) {
        elements.editorFieldType.value = item.field_type || "manual";
      }
      const inferredSessionKey = toSafeString_v1(
        item.sourceSessionKey ||
        item.sourceSidebarSectionKey ||
        getSourceSessionKeyFromMenuOptions_v1(sourceMenuOptions, item.sourceMenuKey)
      ).trim().toLowerCase();
      const isAllSessionsSelection = isProcessListAllSessionsKey_v1(inferredSessionKey);
      elements.editorSourceSession.value = inferredSessionKey;
      elements.editorSourceMenu.value = isAllSessionsSelection ? "" : (item.sourceMenuKey || "");
      elements.editorSourceSubprocess.value = isAllSessionsSelection ? "" : (item.sourceSubprocessKey || "");
      applyEditorFieldTypeState_v3(
        {
          elements,
          manager,
          sourceSubprocessMap,
          sourceSessionOptions: context && context.sourceSessionOptions ? context.sourceSessionOptions : [],
          sourceMenuOptions: context && context.sourceMenuOptions ? context.sourceMenuOptions : [],
          isHydratingEditor: true
        },
        {
          selectedSessionKey: inferredSessionKey,
          selectedMenuKey: isAllSessionsSelection ? "" : (item.sourceMenuKey || ""),
          selectedSubprocessKey: isAllSessionsSelection ? "" : (item.sourceSubprocessKey || ""),
          preserveUnavailableSelection: false
        }
      );
      elements.editorLabel.focus();
    } finally {
      if (context) {
        context.isHydratingEditor = false;
      }
    }
  }

  function readEditorItem_v1(context) {
    const state = context && context.state ? context.state : {};
    const elements = context && context.elements ? context.elements : {};
    const label = toSafeString_v1(elements.editorLabel ? elements.editorLabel.value : "").trim();
    const itemsCsv = toSafeString_v1(elements.editorItems ? elements.editorItems.value : "").trim();
    const fieldType = toSafeString_v1(elements.editorFieldType ? elements.editorFieldType.value : "").trim().toLowerCase();
    const sourceSessionKey = toSafeString_v1(elements.editorSourceSession ? elements.editorSourceSession.value : "").trim().toLowerCase();
    const sourceMenuKey = toSafeString_v1(elements.editorSourceMenu ? elements.editorSourceMenu.value : "").trim().toLowerCase();
    const sourceSubprocessKey = toSafeString_v1(elements.editorSourceSubprocess ? elements.editorSourceSubprocess.value : "").trim().toLowerCase();
    const isAllSessionsSelection = isProcessListAllSessionsKey_v1(sourceSessionKey);
    const resolvedSourceSessionKey = isAllSessionsSelection ? sourceSessionKey : sourceSessionKey || getSourceSessionKeyFromMenuOptions_v1(
      context && Array.isArray(context.sourceMenuOptions) ? context.sourceMenuOptions : [],
      sourceMenuKey
    );
    const status = toSafeString_v1(elements.editorStatus ? elements.editorStatus.value : "").trim().toLowerCase();
    const currentKey = toSafeString_v1(elements.editorKey ? elements.editorKey.value : "").trim();
    const editingId = toSafeString_v1(state.editingId).trim();
    const key = currentKey || normalizeKey_v1(label);

    return {
      managerId: editingId || `tmp_${Date.now()}`,
      key,
      label,
      field_type: (fieldType === "automatic" ? "automatic" : "manual"),
      itemsCsv: fieldType === "automatic" ? "" : itemsCsv,
      sourceSessionKey: fieldType === "automatic" ? resolvedSourceSessionKey : "",
      sourceMenuKey: fieldType === "automatic" && !isAllSessionsSelection ? sourceMenuKey : "",
      sourceSubprocessKey: fieldType === "automatic" && !isAllSessionsSelection ? sourceSubprocessKey : "",
      status: normalizeProcessListStatus_v1(status)
    };
  }

  function validateItem_v1(item, context) {
    const items = context && Array.isArray(context.items) ? context.items : [];
    const editingId = context && context.state ? toSafeString_v1(context.state.editingId).trim() : "";

    if (!item.label) {
      return {
        valid: false,
        message: "Informe o nome da lista."
      };
    }

    const normalizedLabel = normalizeKey_v1(item.label);
    const duplicate = items.some((existing) => {
      const existingId = toSafeString_v1(existing.__managerId || existing.managerId).trim();
      return existingId !== editingId && normalizeKey_v1(existing.label) === normalizedLabel;
    });

    if (duplicate) {
      return {
        valid: false,
        message: "Ja existe uma lista com esse nome."
      };
    }

    if (item.field_type === "manual" && !item.itemsCsv) {
      return { valid: false, message: "Informe o conteúdo da lista." };
    }

    const currentItem = items.find((existing) => {
      const existingId = toSafeString_v1(existing.__managerId || existing.managerId).trim();
      return existingId === editingId;
    }) || null;
    const isLegacyAutomaticWithoutSource = Boolean(
      currentItem &&
      String(currentItem.field_type || "").trim().toLowerCase() === "automatic" &&
      !toSafeString_v1(currentItem.sourceSessionKey || currentItem.sourceSidebarSectionKey).trim() &&
      !toSafeString_v1(currentItem.sourceMenuKey).trim() &&
      !toSafeString_v1(currentItem.sourceSubprocessKey).trim()
    );

    if (item.field_type === "automatic" && !item.sourceSessionKey && !isLegacyAutomaticWithoutSource) {
      return {
        valid: false,
        message: "Selecione a sessão."
      };
    }

    if (item.field_type === "automatic" && !isProcessListAllSessionsKey_v1(item.sourceSessionKey) && !item.sourceMenuKey && !isLegacyAutomaticWithoutSource) {
      return {
        valid: false,
        message: "Selecione o menu de origem da lista automática."
      };
    }

    return { valid: true };
  }

  function hasDraft_v1(elements, manager) {
    return Boolean(
      (manager && manager.state && manager.state.editingId) ||
      toSafeString_v1(elements.editorLabel.value).trim() ||
      toSafeString_v1(elements.editorItems.value).trim() ||
      toSafeString_v1(elements.editorSourceSession.value).trim() ||
      toSafeString_v1(elements.editorSourceMenu.value).trim() ||
      toSafeString_v1(elements.editorSourceSubprocess.value).trim()
    );
  }

  function syncHiddenInputs_v1(context) {
    const elements = context && context.elements ? context.elements : null;
    const items = context && Array.isArray(context.items) ? context.items : [];
    const form = elements && elements.submitButton && elements.submitButton.form
      ? elements.submitButton.form
      : elements && elements.cancelButton && elements.cancelButton.form
        ? elements.cancelButton.form
        : null;
    const configuredInput = form
      ? form.querySelector("[name='process_lists_configured']")
      : null;

    if (!elements || !elements.hiddenContainer) {
      return;
    }

    if (configuredInput) {
      configuredInput.value = "1";
    }

    elements.hiddenContainer.innerHTML = "";

    items.forEach((item) => {
      [
        ["process_list_key", item.key],
        ["process_list_label", item.label],
        ["process_list_field_type", item.field_type || "manual"],
        ["process_list_items_csv", item.field_type === "automatic" ? "" : item.itemsCsv],
        ["process_list_source_session_key", item.field_type === "automatic" ? (item.sourceSessionKey || item.sourceSidebarSectionKey || "") : ""],
        ["process_list_source_menu_key", item.field_type === "automatic" ? item.sourceMenuKey : ""],
        ["process_list_source_subprocess_key", item.field_type === "automatic" ? item.sourceSubprocessKey : ""],
        ["process_list_status", normalizeProcessListStatus_v1(item.status, item.is_active)]
      ].forEach((field) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = field[0];
        input.value = field[1] || "";
        elements.hiddenContainer.appendChild(input);
      });
    });
  }

  //###################################################################################
  // (4.5) FIELD TYPE UI BEHAVIOR
  //###################################################################################

  function populateSourceSubprocessOptions_v1(context, options) {
    const elements = context && context.elements ? context.elements : null;

    if (!elements || !elements.editorSourceSubprocess) {
      return;
    }

    const availableOptions = Array.isArray(options && options.options) ? options.options : [];
    const selectedValue = toSafeString_v1(options && options.selectedValue ? options.selectedValue : "").trim();
    const preserveUnavailableSelection = Boolean(options && options.preserveUnavailableSelection);
    const keepVisible = Boolean(options && options.keepVisible);
    const forceVisible = Boolean(options && options.forceVisible);

    elements.editorSourceSubprocess.innerHTML = "";

    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "Todos os subprocessos";
    elements.editorSourceSubprocess.appendChild(defaultOption);

    let hasSelectedOption = false;

    availableOptions.forEach((option) => {
      const optionEl = document.createElement("option");
      optionEl.value = option.value;
      optionEl.textContent = option.label;
      if (option.value === selectedValue) {
        optionEl.selected = true;
        hasSelectedOption = true;
      }
      elements.editorSourceSubprocess.appendChild(optionEl);
    });

    if (selectedValue && !hasSelectedOption && preserveUnavailableSelection) {
      const unavailableOption = document.createElement("option");
      unavailableOption.value = selectedValue;
      unavailableOption.textContent = "Subprocesso indisponível";
      unavailableOption.selected = true;
      elements.editorSourceSubprocess.appendChild(unavailableOption);
      hasSelectedOption = true;
    }

    if (!hasSelectedOption) {
      elements.editorSourceSubprocess.value = "";
    }

    elements.editorSourceSubprocess.disabled = !(keepVisible || forceVisible);
  }

  function applyEditorFieldTypeState_v3(context, options) {
    const elements = context && context.elements ? context.elements : context;

    if (!elements || !elements.editorFieldType || !elements.editorItems ||
        !elements.editorItemsWrapper || !elements.editorSourceSession ||
        !elements.editorSourceSessionWrapper || !elements.editorSourceMenu ||
        !elements.editorSourceMenuWrapper || !elements.editorSourceSubprocess ||
        !elements.editorSourceSubprocessWrapper || !elements.root) {
      return;
    }

    const val = String(elements.editorFieldType.value || "").trim().toLowerCase();
    const resetTemporaryState = Boolean(options && options.resetTemporaryState);
    const clearSourceSelection = Boolean(options && options.clearSourceSelection);
    const preserveUnavailableSelection = Boolean(options && options.preserveUnavailableSelection);

    if (val === "automatic") {
      if (elements.editorItems.dataset.previousItems === undefined) {
        elements.editorItems.dataset.previousItems = elements.editorItems.value || "";
      }
      elements.editorItems.value = "";
      elements.editorItems.disabled = true;
      elements.editorItemsWrapper.hidden = true;
      elements.editorSourceSessionWrapper.hidden = false;
      elements.editorSourceMenuWrapper.hidden = true;
      elements.editorSourceSubprocessWrapper.hidden = true;
      elements.root.dataset.hasSourceSubprocess = "0";
      updateAutomaticSourceControls_v1(
        context,
        {
          selectedSessionKey: clearSourceSelection ? "" : options && Object.prototype.hasOwnProperty.call(options, "selectedSessionKey")
            ? options.selectedSessionKey
            : elements.editorSourceSession.value,
          selectedMenuKey: clearSourceSelection ? "" : options && Object.prototype.hasOwnProperty.call(options, "selectedMenuKey")
            ? options.selectedMenuKey
            : elements.editorSourceMenu.value,
          selectedSubprocessKey: clearSourceSelection ? "" : options && Object.prototype.hasOwnProperty.call(options, "selectedSubprocessKey")
            ? options.selectedSubprocessKey
            : elements.editorSourceSubprocess.value,
          preserveUnavailableSelection,
          keepVisible: true
        }
      );
      elements.root.dataset.hasSourceSubprocess = toSafeString_v1(elements.editorSourceMenu.value).trim() ? "1" : "0";
    } else {
      elements.editorItemsWrapper.hidden = false;
      elements.editorItems.disabled = false;
      elements.editorSourceSession.value = "";
      elements.editorSourceSession.disabled = true;
      elements.editorSourceSessionWrapper.hidden = true;
      elements.editorSourceMenu.value = "";
      elements.editorSourceMenu.disabled = true;
      elements.editorSourceMenuWrapper.hidden = true;
      elements.editorSourceSubprocess.value = "";
      elements.editorSourceSubprocess.disabled = true;
      elements.editorSourceSubprocessWrapper.hidden = true;
      elements.root.dataset.hasSourceSubprocess = "0";
      if (!resetTemporaryState && elements.editorItems.dataset.previousItems !== undefined) {
        if (!elements.editorItems.value) {
          elements.editorItems.value = elements.editorItems.dataset.previousItems || "";
        }
      }
      if (clearSourceSelection) {
        elements.editorSourceSession.value = "";
        elements.editorSourceMenu.value = "";
        elements.editorSourceSubprocess.value = "";
      }
      delete elements.editorItems.dataset.previousItems;
    }
  }

  function bindCancel_v1(form, elements, manager) {
    if (!form || !elements.cancelButton || form.dataset.processListsCancelBoundV1 === "1") {
      return;
    }

    form.dataset.processListsCancelBoundV1 = "1";
    elements.cancelButton.dataset.appgenesisCancel = "1";
    elements.cancelButton.dataset.appgenesisCancelLocal = "1";
    elements.cancelButton.__appgenesisLocalDraftCheckV1 = function () {
      return hasDraft_v1(elements, manager);
    };

    form.addEventListener("appgenesis:cancelled", (event) => {
      const detail = event && event.detail ? event.detail : {};

      if (detail.trigger !== elements.cancelButton) {
        return;
      }

      manager.clearEditing();
    });
  }

  function bindSubmit_v1(form, elements, manager) {
    if (!form || !elements.submitButton || form.dataset.processListsSubmitBoundV1 === "1") {
      return;
    }

    form.dataset.processListsSubmitBoundV1 = "1";

    elements.submitButton.addEventListener("click", (event) => {
      event.preventDefault();

      if (hasDraft_v1(elements, manager)) {
        const item = readEditorItem_v1({
          manager,
          elements: manager.elements,
          state: manager.state
        });
        const validationResult = validateItem_v1(item, {
          manager,
          elements: manager.elements,
          state: manager.state,
          items: manager.getItems()
        });

        if (validationResult && validationResult.valid === false) {
          if (validationResult.message) {
            showValidationMessage_v1(validationResult.message);
          }
          return;
        }

        manager.addOrUpdate(item);
      }

      manager.syncHiddenInputs();
      if (form.processListColumnsManagerV2) {
        form.processListColumnsManagerV2.syncHiddenInputs();
      }
      submitNative_v1(form);
    });

    if (form.dataset.processListsSubmitNativeBoundV1 === "1") {
      return;
    }

    form.dataset.processListsSubmitNativeBoundV1 = "1";
    form.addEventListener("submit", () => {
      manager.syncHiddenInputs();
      if (form.processListColumnsManagerV2) {
        form.processListColumnsManagerV2.syncHiddenInputs();
      }
    });
  }

  function setupProcessListColumnsManager_v2(form) {
    const core = getCore_v1();
    const elements = getColumnElements_v2(form);

    if (!elements || !elements.legacyContainer || !elements.hiddenContainer ||
        !elements.editorField || !elements.editorLabel || !elements.submitButton ||
        !elements.cancelButton || !elements.pageSize) {
      return null;
    }

    const manager = core.createConfigurableItemsManager_v1({
      root: elements.root,
      itemName: "coluna",
      itemNamePlural: "colunas",
      pageSizeDefault: Number.parseInt(elements.pageSize.value, 10) || core.DEFAULT_CONFIGURABLE_PAGE_SIZE_V1,
      pageSizeOptions: core.DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1,
      initialItems: readInitialColumns_v2(elements),
      selectors: {
        editorForm: "[data-process-list-column-editor-block]",
        table: "[data-process-list-columns-table]",
        tableBody: "[data-process-list-columns-table-body]",
        emptyState: "[data-process-list-columns-empty]",
        pagination: "[data-process-list-columns-pagination]",
        pageSize: "[data-process-list-columns-page-size]",
        hiddenContainer: "[data-process-list-columns-hidden-container]",
        totalLabel: "[data-process-list-columns-total-label]"
      },
      columns: [
        { key: "fieldKey", label: "Campo da coluna", render: (item) => {
          const option = Array.from(elements.editorField.options).find((entry) => entry.value === item.fieldKey);
          return option ? option.textContent : item.fieldKey;
        } },
        { key: "label", label: "Nome da coluna" },
        { key: "alwaysVisible", label: "Sempre visível", render: (item) => item.alwaysVisible ? "Sim" : "Não" },
        { key: "responsivePriority", label: "Prioridade" }
      ],
      getItemId: (item, index) => item.managerId || item.__managerId || item.key || `column_${index + 1}`,
      readEditorItem: readColumnEditorItem_v2,
      loadEditorItem: loadColumnEditorItem_v2,
      clearEditor: clearColumnEditor_v2,
      validateItem: validateColumnItem_v2,
      syncHiddenInputs: syncColumnHiddenInputs_v2
    });

    if (!manager) {
      return null;
    }

    Object.assign(manager.elements, elements);
    manager.render = () => renderPartitionedLists_v1(manager, elements);
    elements.cancelButton.dataset.appgenesisCancel = "1";
    elements.cancelButton.dataset.appgenesisCancelLocal = "1";
    form.addEventListener("appgenesis:cancelled", (event) => {
      if (event.detail && event.detail.trigger === elements.cancelButton) {
        manager.clearEditing();
      }
    });
    elements.submitButton.addEventListener("click", (event) => {
      event.preventDefault();
      const hasDraft = Boolean(manager.state.editingId || elements.editorField.value || elements.editorLabel.value.trim());

      if (hasDraft) {
        const item = readColumnEditorItem_v2({ elements, state: manager.state });
        const validation = validateColumnItem_v2(item, { items: manager.getItems(), state: manager.state });

        if (!validation.valid) {
          showValidationMessage_v1(validation.message);
          return;
        }
        manager.addOrUpdate(item);
      }

      manager.syncHiddenInputs();
      if (form.processListsManagerV1) {
        form.processListsManagerV1.syncHiddenInputs();
      }
      submitNative_v1(form);
    });
    manager.syncHiddenInputs();
    form.processListColumnsManagerV2 = manager;
    return manager;
  }

  function renderPartitionedLists_v1(manager, elements) {
    const core = getCore_v1();

    if (!core || typeof core.renderConfigurableItemsPartitionedViews_v1 !== "function") {
      return;
    }

    core.renderConfigurableItemsPartitionedViews_v1(manager, [
      {
        key: "active",
        elements: {
          table: elements.table,
          tableBody: elements.tableBody,
          emptyState: elements.emptyState,
          pagination: elements.pagination,
          pageSize: elements.pageSize,
          totalLabel: elements.totalLabel
        },
        pageSizeDefault: manager.config.pageSizeDefault,
        itemName: "lista",
        itemNamePlural: "listas ativas",
        emptyText: "Sem listas ativas.",
        filter: (item) => normalizeProcessListStatus_v1(item.status, item.is_active) !== "inativo"
      },
      {
        key: "inactive",
        elements: {
          table: elements.inactiveTable,
          tableBody: elements.inactiveTableBody,
          emptyState: elements.inactiveEmptyState,
          pagination: elements.inactivePagination,
          pageSize: elements.inactivePageSize,
          totalLabel: elements.inactiveTotalLabel
        },
        pageSizeDefault: manager.config.pageSizeDefault,
        itemName: "lista",
        itemNamePlural: "listas inativas",
        emptyText: "Sem listas inativas.",
        filter: (item) => normalizeProcessListStatus_v1(item.status, item.is_active) === "inativo"
      }
    ]);
  }

  //###################################################################################
  // (5) INICIALIZACAO
  //###################################################################################

  function setupProcessListsManager_v1(form) {
    if (!form || form.dataset.processListsManagerBoundV1 === "1") {
      return null;
    }

    const core = getCore_v1();

    if (!core || typeof core.createConfigurableItemsManager_v1 !== "function") {
      return null;
    }

    const elements = getElements_v1(form);

    if (!hasRequiredElements_v1(elements)) {
      return null;
    }

    form.dataset.processListsManagerBoundV1 = "1";
    const menuKey = toSafeString_v1(elements.menuKeyInput.value).trim().toLowerCase();
    const deleteEndpoint = getProcessListsDeleteEndpoint_v1(form);
    const sourceSubprocessMap = getSourceSubprocessMap_v1(elements);
    const sourceSessionOptions = readSourceSessionOptions_v1(elements);
    const sourceMenuOptions = readSourceMenuOptions_v1(elements);
    elements.root.dataset.hasSourceSubprocess = "0";
    const perfState = createProcessListsPerfState_v1();
    const readStartMs = perfState.cycleStart;

    let manager = null;
    const initialItems = readInitialItems_v1(elements, sourceMenuOptions);
    perfState.readMs = nowMs_v1() - readStartMs;
    perfState.backendCount = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-list-row]")
    ).length;
    perfState.initialCount = initialItems.length;
    manager = core.createConfigurableItemsManager_v1({
      root: elements.root,
      itemName: "lista",
      itemNamePlural: "listas",
      createTitle: "Criar lista",
      editTitle: "Editar lista",
      pageSizeDefault: Number.parseInt(elements.pageSize.value, 10) || core.DEFAULT_CONFIGURABLE_PAGE_SIZE_V1,
      pageSizeOptions: core.DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1,
      skipInitialRender: true,
      initialItems,
      menuKey,
      selectors: {
        editorForm: "[data-process-list-reusable-editor-block]",
        table: "[data-process-lists-table]",
        tableBody: "[data-process-lists-table-body]",
        emptyState: "[data-process-lists-empty]",
        pagination: "[data-process-lists-pagination]",
        pageSize: "[data-process-lists-page-size]",
        hiddenContainer: "[data-process-lists-hidden-container]",
        totalLabel: "[data-process-lists-total-label]",
        searchInput: "[data-configurable-search]"
      },
      columns: [
        {
          key: "label",
          label: "Nome da lista",
          alwaysVisible: true,
          responsivePriority: 100
        },
        {
          key: "field_type",
          label: "Tipo de campo",
          responsivePriority: 50,
          render: (item) => {
            const ft = String(item.field_type || "").trim().toLowerCase();
            return ft === "automatic" ? "Automático" : "Manual";
          }
        },
        {
          key: "itemsCsv",
          label: "Conteúdo da lista",
          responsivePriority: 10,
          render: (item) => item.itemsCsv || "-"
        },
        {
          key: "sourceMenuKey",
          label: "Menu",
          responsivePriority: 40,
          render: (item) => {
            if (String(item.field_type || "manual").toLowerCase() !== "automatic") {
              return "-";
            }
            if (!String(item.sourceMenuKey || "").trim()) {
              return "-";
            }
            const option = Array.from(elements.editorSourceMenu.options).find(
              (entry) => entry.value === item.sourceMenuKey
            );
            return option ? option.textContent : "Menu indisponível";
          }
        },
        {
          key: "sourceSubprocessKey",
          label: "Subprocesso",
          responsivePriority: 30,
          render: (item) => {
            if (String(item.field_type || "manual").toLowerCase() !== "automatic") {
              return "-";
            }
            if (!String(item.sourceMenuKey || "").trim()) {
              return "-";
            }
            if (!String(item.sourceSubprocessKey || "").trim()) {
              return "Todos os subprocessos";
            }
            const sourceOptions = getSourceSubprocessOptions_v1(
              sourceSubprocessMap,
              item.sourceMenuKey
            );
            const sourceOption = sourceOptions.find(
              (entry) => entry.value === item.sourceSubprocessKey
            );
            return sourceOption ? sourceOption.label : "Subprocesso indisponível";
          }
        },
        {
          key: "entidade",
          label: "Entidade",
          responsivePriority: 20,
          render: () => elements.root.dataset.entityNumber || "-"
        },
        {
          key: "status",
          label: "Estado",
          alwaysVisible: true,
          responsivePriority: 90,
          render: (item) => {
            const isInactive = String(item.status || "ativo").trim().toLowerCase() === "inativo";
            const badgeClass = isInactive ? "entity-status-inactive" : "entity-status-active";
            const badgeLabel = isInactive ? "Inativo" : "Ativo";
            const badge = document.createElement("span");
            badge.className = `entity-status ${badgeClass}`;
            badge.textContent = badgeLabel;
            return badge;
          }
        }
      ],
      getItemId: (item, index) => item.managerId || item.__managerId || item.key || `list_${index + 1}`,
      readEditorItem: (context) => readEditorItem_v1({
        ...context,
        sourceSubprocessMap,
        sourceSessionOptions,
        sourceMenuOptions
      }),
      loadEditorItem: (item, context) => loadEditorItem_v1(item, {
        ...context,
        sourceSubprocessMap,
        sourceSessionOptions,
        sourceMenuOptions
      }),
      clearEditor: (context) => clearEditor_v1({
        ...context,
        sourceSubprocessMap,
        sourceSessionOptions,
        sourceMenuOptions
      }),
      validateItem: validateItem_v1,
      syncHiddenInputs: syncHiddenInputs_v1,
      canRemoveItem: (item) => normalizeProcessListStatus_v1(item && item.status, item && item.is_active) === "inativo",
      deleteItem: async ({ item }) => {
        const cleanListKey = toSafeString_v1(item && item.key ? item.key : "").trim();

        if (!menuKey) {
          return {
            success: false,
            message: "Menu inválido."
          };
        }

        if (!cleanListKey) {
          return {
            success: false,
            message: "Lista inválida."
          };
        }

        try {
          const response = await fetch(deleteEndpoint, {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              menu_key: menuKey,
              list_key: cleanListKey
            })
          });

          let payload = null;
          const responseText = await response.text();

          if (responseText) {
            try {
              payload = JSON.parse(responseText);
            } catch (parseError) {
              payload = null;
            }
          }

          if (!response.ok) {
            return {
              success: false,
              message: payload && payload.message ? payload.message : "Não foi possível eliminar a lista."
            };
          }

          if (!payload || payload.success !== true) {
            return {
              success: false,
              message: payload && payload.message ? payload.message : "Não foi possível eliminar a lista."
            };
          }

          return {
            success: true,
            message: payload.message || "Lista eliminada com sucesso.",
            listKey: payload.list_key || cleanListKey
          };
        } catch (error) {
          return {
            success: false,
            message: error && error.message ? error.message : "Falha de rede ao eliminar a lista."
          };
        }
      },
      onRender: null
    });

    if (!manager) {
      form.dataset.processListsManagerBoundV1 = "";
      return null;
    }

    Object.assign(manager.elements, elements);
    manager._perfMetricsV1 = perfState;
    manager.render = () => {
      if (perfState.enabled) {
        perfState.responsiveMs = 0;
        perfState.responsiveTables = 0;
        perfState.renderMs = 0;
      }

      const renderStartMs = nowMs_v1();
      renderPartitionedLists_v1(manager, elements);
      perfState.renderMs = nowMs_v1() - renderStartMs;
      perfState.activeCount = manager.getItems().filter((item) => normalizeProcessListStatus_v1(item.status, item.is_active) !== "inativo").length;
      perfState.inactiveCount = manager.getItems().filter((item) => normalizeProcessListStatus_v1(item.status, item.is_active) === "inativo").length;
      perfState.stateCount = manager.getItems().length;
      logProcessListsPerfSummary_v1(perfState);
    };
    manager.render();

    const managerContext = {
      elements,
      manager,
      sourceSubprocessMap,
      sourceSessionOptions,
      sourceMenuOptions,
      sourceSessionOptionsSnapshot: normalizeProcessListSourceSessionOptions_v1(sourceSessionOptions),
      sourceMenuOptionsSnapshot: Array.isArray(sourceMenuOptions) ? sourceMenuOptions : [],
      isHydratingEditor: false
    };

    manager.sourceSessionOptionsSnapshot = managerContext.sourceSessionOptionsSnapshot;
    manager.sourceMenuOptionsSnapshot = managerContext.sourceMenuOptionsSnapshot;

    refreshAutomaticSourceOptions_v1(managerContext);

    elements.editorFieldType.addEventListener("change", () => {
      if (managerContext.isHydratingEditor) {
        return;
      }
      applyEditorFieldTypeState_v3(
        managerContext,
        {
          clearSourceSelection: true,
          selectedSessionKey: elements.editorSourceSession.value,
          selectedMenuKey: elements.editorSourceMenu.value,
          selectedSubprocessKey: elements.editorSourceSubprocess.value
        }
      );
    });
    elements.editorSourceSession.addEventListener("change", () => {
      if (managerContext.isHydratingEditor) {
        return;
      }
      refreshAutomaticSourceOptions_v1(managerContext);
      updateAutomaticSourceControls_v1(managerContext, {
        selectedSessionKey: elements.editorSourceSession.value,
        selectedMenuKey: elements.editorSourceMenu.value,
        selectedSubprocessKey: elements.editorSourceSubprocess.value,
        preserveUnavailableSelection: false,
        keepVisible: true
      });
    });
    elements.editorSourceMenu.addEventListener("change", () => {
      if (managerContext.isHydratingEditor) {
        return;
      }
      refreshAutomaticSourceOptions_v1(managerContext);
      updateAutomaticSourceControls_v1(managerContext, {
        selectedSessionKey: elements.editorSourceSession.value,
        selectedMenuKey: elements.editorSourceMenu.value,
        selectedSubprocessKey: elements.editorSourceSubprocess.value,
        preserveUnavailableSelection: true,
        keepVisible: true
      });
    });
    applyEditorFieldTypeState_v3(
      managerContext,
      {
        resetTemporaryState: true,
        clearSourceSelection: true,
        selectedSessionKey: elements.editorSourceSession.value,
        selectedMenuKey: elements.editorSourceMenu.value,
        selectedSubprocessKey: elements.editorSourceSubprocess.value
      }
    );

    bindCancel_v1(form, elements, manager);
    form.processListsManagerV1 = manager;
    setupProcessListColumnsManager_v2(form);
    bindSubmit_v1(form, elements, manager);
    manager.render();
    manager.syncHiddenInputs();

    return manager;
  }

  function setupAllProcessListsManagers_v1() {
    Array.from(document.querySelectorAll(FORM_SELECTOR)).forEach(setupProcessListsManager_v1);
  }

  //###################################################################################
  // (6) BOOT
  //###################################################################################

  window.setupProcessListsManagerV1 = setupAllProcessListsManagers_v1;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessListsManagers_v1);
  } else {
    setupAllProcessListsManagers_v1();
  }
})(window, document);
