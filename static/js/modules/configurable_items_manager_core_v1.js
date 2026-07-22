//###################################################################################
// APPGENESIS - CONFIGURABLE ITEMS MANAGER CORE V1
//###################################################################################

(function (window, document) {
  "use strict";

  //###################################################################################
  // (1) NAMESPACE
  //###################################################################################

  if (!window.AppGenesisConfigurableItems) {
    window.AppGenesisConfigurableItems = {};
  }

  const namespace = window.AppGenesisConfigurableItems;

  const DEFAULT_CONFIGURABLE_PAGE_SIZE_V1 = 5;
  const DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1 = [5, 10, 20];

  //###################################################################################
  // (2) HELPERS GERAIS
  //###################################################################################

  function toArray_v1(value) {
    return Array.isArray(value) ? value.slice() : [];
  }

  function toSafeString_v1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeLookup_v1(value) {
    return toSafeString_v1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function showAlertDialog_v1(options) {
    const safeOptions = options && typeof options === "object" ? options : {};
    const title = toSafeString_v1(safeOptions.title).trim() || "Validacao";
    const message = toSafeString_v1(safeOptions.message).trim();

    if (!message) {
      return null;
    }

    if (
      window.AppGenesisDialogV1 &&
      typeof window.AppGenesisDialogV1.alert === "function"
    ) {
      return window.AppGenesisDialogV1.alert({
        title,
        message
      });
    }

    if (window.console && typeof window.console.warn === "function") {
      window.console.warn("[AppGenesisConfigurableItems]", message);
    }
    return null;
  }

  function resolveElement_v1(root, selector) {
    if (!selector) {
      return null;
    }

    if (selector instanceof Element) {
      return selector;
    }

    if (root && typeof root.querySelector === "function") {
      return root.querySelector(selector);
    }

    return document.querySelector(selector);
  }

  function createElement_v1(tagName, className, textContent) {
    const element = document.createElement(tagName);

    if (className) {
      element.className = className;
    }

    if (textContent !== undefined && textContent !== null) {
      element.textContent = String(textContent);
    }

    return element;
  }

  function clampNumber_v1(value, minValue, maxValue, fallbackValue) {
    const parsedValue = Number.parseInt(String(value || "").trim(), 10);

    if (!Number.isFinite(parsedValue)) {
      return fallbackValue;
    }

    return Math.min(maxValue, Math.max(minValue, parsedValue));
  }

  function defaultGetItemId_v1(item, index) {
    if (item && item.id !== undefined && item.id !== null && String(item.id).trim()) {
      return String(item.id).trim();
    }

    if (item && item.key !== undefined && item.key !== null && String(item.key).trim()) {
      return String(item.key).trim();
    }

    return `item_${index + 1}`;
  }

  function defaultRenderCell_v1(item, column) {
    const key = String(column && column.key ? column.key : "").trim();

    if (!key || !item) {
      return "";
    }

    return toSafeString_v1(item[key]);
  }

  function normalizeColumn_v1(rawColumn) {
    const column = rawColumn && typeof rawColumn === "object" ? rawColumn : {};
    const responsivePriority = Number(column.responsivePriority);

    return {
      key: String(column.key || "").trim(),
      label: String(column.label || column.key || "").trim(),
      className: String(column.className || "").trim(),
      render: typeof column.render === "function" ? column.render : null,
      alwaysVisible: Boolean(column.alwaysVisible),
      responsivePriority: Number.isFinite(responsivePriority) ? responsivePriority : null,
      responsiveKey: String(column.responsiveKey || column.key || "").trim(),
      mobileLabel: String(column.mobileLabel || "").trim(),
      responsiveMinWidth: Number.isFinite(Number(column.responsiveMinWidth))
        ? Number(column.responsiveMinWidth)
        : null
    };
  }

  function hasResponsiveColumns_v1(columns) {
    return toArray_v1(columns).some((column) => {
      const normalized = normalizeColumn_v1(column);
      return normalized.alwaysVisible || Number.isFinite(normalized.responsivePriority);
    });
  }

  function applyResponsiveCellMeta_v1(cell, column, index, isActions) {
    if (!cell) {
      return;
    }

    cell.dataset.configurableColumnIndex = String(index);

    if (column && column.key) {
      cell.dataset.configurableColumnKey = String(column.key);
      cell.dataset.responsiveKey = String(column.key);
    }

    if (column && column.responsiveKey) {
      cell.dataset.configurableResponsiveKey = column.responsiveKey;
      cell.dataset.responsiveKey = column.responsiveKey;
    }

    if (column && column.mobileLabel) {
      cell.dataset.configurableMobileLabel = column.mobileLabel;
    }

    if (column && Number.isFinite(column.responsivePriority)) {
      cell.dataset.configurableResponsivePriority = String(column.responsivePriority);
      cell.dataset.responsivePriority = String(column.responsivePriority);
    }

    if (column && column.alwaysVisible) {
      cell.dataset.configurableAlwaysVisible = "1";
      cell.dataset.alwaysVisible = "1";
    }

    if (isActions) {
      cell.dataset.configurableColumnKey = "actions";
      cell.dataset.configurableAlwaysVisible = "1";
      cell.dataset.responsiveKey = "actions";
      cell.dataset.alwaysVisible = "1";
    }
  }

  function createConfigurableTableCell_v1(tagName, column, index, isActions) {
    const cell = document.createElement(tagName);
    if (column && column.className) {
      cell.className = column.className;
    }
    applyResponsiveCellMeta_v1(cell, column, index, isActions);
    return cell;
  }

  function createConfigurableRow_v1(manager, item, absoluteIndex, fullItemIndex, totalAllItems) {
    const row = document.createElement("tr");
    const itemId = item.__managerId;

    row.dataset.configurableItemId = itemId;

    manager.config.columns.forEach((column, columnIndex) => {
      const td = createConfigurableTableCell_v1("td", column, columnIndex, false);
      const value = column.render
        ? column.render(item, absoluteIndex, manager)
        : defaultRenderCell_v1(item, column, absoluteIndex, manager);

      if (value instanceof Node) {
        td.appendChild(value);
      } else {
        td.textContent = toSafeString_v1(value);
      }

      row.appendChild(td);
    });

    const actionsTd = createConfigurableTableCell_v1(
      "td",
      {
        className: "configurable-items-actions-cell-v1 admin-col-actions-v1"
      },
      manager.config.columns.length,
      true
    );
    actionsTd.appendChild(createRawActionsContainer_v1(manager, item, itemId, fullItemIndex, totalAllItems));
    row.appendChild(actionsTd);

    return row;
  }

  function getResponsiveManagedTableElements_v1(table) {
    const tableWrap = table ? table.closest(".configurable-items-table-wrap-v1") : null;
    return {
      table,
      tableWrap,
      thead: table ? table.querySelector("thead") : null,
      tbody: table ? table.querySelector("tbody") : null
    };
  }

  function applyResponsiveColumnsToTable_v1(manager, table) {
    if (!manager || !table || !table.isConnected) {
      return;
    }

    const tableInfo = getResponsiveManagedTableElements_v1(table);
    const tableWrap = tableInfo.tableWrap;

    if (!tableWrap) {
      return;
    }

    const responsiveColumns = manager.config.columns
      .map((column, index) => ({ column, index }))
      .filter(({ column }) => column && (column.alwaysVisible || Number.isFinite(column.responsivePriority)))
      .sort((left, right) => {
        const leftPriority = Number.isFinite(left.column.responsivePriority) ? left.column.responsivePriority : Number.MAX_SAFE_INTEGER;
        const rightPriority = Number.isFinite(right.column.responsivePriority) ? right.column.responsivePriority : Number.MAX_SAFE_INTEGER;
        if (leftPriority !== rightPriority) {
          return leftPriority - rightPriority;
        }
        return left.index - right.index;
      });

    if (!responsiveColumns.length) {
      tableWrap.classList.remove("configurable-items-responsive-wrap-v1");
      table.classList.remove("configurable-items-responsive-table-v1");
      tableWrap.classList.remove("configurable-items-responsive-compact-v1");
      tableWrap.classList.remove("configurable-items-responsive-ultra-v1");
      table.removeAttribute("data-configurable-responsive-table");
      return;
    }

    tableWrap.classList.add("configurable-items-responsive-wrap-v1");
    table.classList.add("configurable-items-responsive-table-v1");
    tableWrap.classList.remove("configurable-items-responsive-compact-v1");
    tableWrap.classList.remove("configurable-items-responsive-ultra-v1");
    table.setAttribute("data-configurable-responsive-table", "1");

    const allHeaderCells = Array.from(table.querySelectorAll("thead th"));
    const allRows = Array.from(table.querySelectorAll("tbody tr"));
    const availableWidth = tableWrap.clientWidth || tableWrap.getBoundingClientRect().width || 0;
    const perfState = manager && manager._perfMetricsV1 && manager._perfMetricsV1.enabled
      ? manager._perfMetricsV1
      : null;
    const perfStartMs = perfState && window.performance && typeof window.performance.now === "function"
      ? window.performance.now()
      : 0;

    if (!availableWidth) {
      return;
    }

    const resetVisibility = () => {
      allHeaderCells.forEach((cell) => {
        cell.classList.remove("configurable-items-responsive-hidden-v1");
        cell.hidden = false;
        cell.removeAttribute("aria-hidden");
      });

      allRows.forEach((row) => {
        Array.from(row.children).forEach((cell) => {
          cell.classList.remove("configurable-items-responsive-hidden-v1");
          cell.hidden = false;
          cell.removeAttribute("aria-hidden");
        });
      });
    };

    const hideColumn = (columnIndex) => {
      const headerCell = allHeaderCells[columnIndex];
      if (headerCell) {
        headerCell.classList.add("configurable-items-responsive-hidden-v1");
        headerCell.hidden = true;
        headerCell.setAttribute("aria-hidden", "true");
      }

      allRows.forEach((row) => {
        const cell = row.children[columnIndex];
        if (cell) {
          cell.classList.add("configurable-items-responsive-hidden-v1");
          cell.hidden = true;
          cell.setAttribute("aria-hidden", "true");
        }
      });
    };

    resetVisibility();

    if (table.scrollWidth <= availableWidth) {
      if (perfState && perfStartMs) {
        perfState.responsiveMs = (perfState.responsiveMs || 0) + (window.performance.now() - perfStartMs);
        perfState.responsiveTables = (perfState.responsiveTables || 0) + 1;
      }
      return;
    }

    for (const entry of responsiveColumns) {
      if (entry.column.alwaysVisible) {
        continue;
      }

      hideColumn(entry.index);

      if (table.scrollWidth <= availableWidth) {
        break;
      }
    }

    if (table.scrollWidth > availableWidth) {
      tableWrap.classList.add("configurable-items-responsive-compact-v1");
      void tableWrap.offsetWidth;
    }

    if (table.scrollWidth > availableWidth) {
      tableWrap.classList.add("configurable-items-responsive-ultra-v1");
      void tableWrap.offsetWidth;
    }

    if (perfState && perfStartMs) {
      perfState.responsiveMs = (perfState.responsiveMs || 0) + (window.performance.now() - perfStartMs);
      perfState.responsiveTables = (perfState.responsiveTables || 0) + 1;
    }
  }

  function refreshTableActionMenus_v1(manager) {
    if (!manager || !manager.root) {
      return;
    }

    const shell = window.AppGenesisProcessShell || {};
    if (typeof shell.enhanceTableActionMenus !== "function") {
      return;
    }

    shell.enhanceTableActionMenus({
      root: manager.root,
      actionsSelector: ".table-actions"
    });
  }

  function scheduleResponsiveTableRender_v1(manager) {
    if (!manager || manager._responsiveRafId) {
      return;
    }

    manager._responsiveRafId = window.requestAnimationFrame(() => {
      manager._responsiveRafId = 0;
      if (typeof manager.render === "function") {
        manager.render();
      }
    });
  }

  function ensureResponsiveColumnsObserver_v1(manager) {
    if (!manager || manager._responsiveResizeBound || !hasResponsiveColumns_v1(manager.config.columns)) {
      return;
    }

    manager._responsiveResizeBound = true;
    window.addEventListener("resize", () => {
      scheduleResponsiveTableRender_v1(manager);
    });
  }

  //###################################################################################
  // (3) NORMALIZAR CONFIGURACAO
  //###################################################################################

  function normalizeConfigurableItemsConfig_v1(rawConfig) {
    const config = rawConfig && typeof rawConfig === "object" ? rawConfig : {};
    const selectors = config.selectors && typeof config.selectors === "object" ? config.selectors : {};
    const pageSizeOptions = toArray_v1(config.pageSizeOptions).length
      ? toArray_v1(config.pageSizeOptions)
      : DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1;

    return {
      root: config.root || null,
      rootSelector: String(config.rootSelector || "").trim(),
      itemName: String(config.itemName || "item").trim(),
      itemNamePlural: String(config.itemNamePlural || "itens").trim(),
      createTitle: String(config.createTitle || "").trim(),
      editTitle: String(config.editTitle || "").trim(),
      pageSizeDefault: clampNumber_v1(config.pageSizeDefault, 1, 100, DEFAULT_CONFIGURABLE_PAGE_SIZE_V1),
      pageSizeOptions,
      columns: toArray_v1(config.columns).map(normalizeColumn_v1).filter((column) => column.key || column.label),
      selectors: {
        editorForm: selectors.editorForm || "[data-configurable-editor-form]",
        table: selectors.table || "[data-configurable-table]",
        tableBody: selectors.tableBody || "[data-configurable-table-body]",
        emptyState: selectors.emptyState || "[data-configurable-empty]",
        pagination: selectors.pagination || "[data-configurable-pagination]",
        pageSize: selectors.pageSize || "[data-configurable-page-size]",
        hiddenContainer: selectors.hiddenContainer || "[data-configurable-hidden-container]",
        totalLabel: selectors.totalLabel || "[data-configurable-total-label]",
        searchInput: selectors.searchInput || "[data-configurable-search]",
        formCard: selectors.formCard || "[data-configurable-form-card]",
        formTitle: selectors.formTitle || "[data-configurable-form-title]"
      },
      getItemId: typeof config.getItemId === "function" ? config.getItemId : defaultGetItemId_v1,
      readEditorItem: typeof config.readEditorItem === "function" ? config.readEditorItem : null,
      loadEditorItem: typeof config.loadEditorItem === "function" ? config.loadEditorItem : null,
      clearEditor: typeof config.clearEditor === "function" ? config.clearEditor : null,
      validateItem: typeof config.validateItem === "function" ? config.validateItem : null,
      syncHiddenInputs: typeof config.syncHiddenInputs === "function" ? config.syncHiddenInputs : null,
      deleteItem: typeof config.deleteItem === "function" ? config.deleteItem : null,
      canRemoveItem: typeof config.canRemoveItem === "function" ? config.canRemoveItem : null,
      onChange: typeof config.onChange === "function" ? config.onChange : null,
      onRender: typeof config.onRender === "function" ? config.onRender : null,
      initialItems: toArray_v1(config.initialItems),
      skipInitialRender: Boolean(config.skipInitialRender),
      preventEditorSubmit: config.preventEditorSubmit !== false,
      actions: {
        edit: config.actions && config.actions.edit === false ? false : true,
        remove: config.actions && config.actions.remove === false ? false : true,
        move: config.actions && config.actions.move === false ? false : true
      }
    };
  }

  //###################################################################################
  // (4) CRIAR ESTADO
  //###################################################################################

  function normalizeItems_v1(items, config) {
    return toArray_v1(items).map((rawItem, index) => {
      const item = rawItem && typeof rawItem === "object" ? { ...rawItem } : {};
      const itemId = config.getItemId(item, index);

      return {
        ...item,
        __managerId: String(itemId || `item_${index + 1}`),
        __managerOrder: Number.isFinite(Number(item.__managerOrder)) ? Number(item.__managerOrder) : index + 1
      };
    });
  }

  function createInitialState_v1(config) {
    return {
      items: normalizeItems_v1(config.initialItems, config),
      visibleCount: config.pageSizeDefault,
      pageSize: config.pageSizeDefault,
      editingId: "",
      searchQuery: "",
      initialized: false
    };
  }

  //###################################################################################
  // (5) ELEMENTOS DO MANAGER
  //###################################################################################

  function resolveManagerRoot_v1(config) {
    if (config.root instanceof Element) {
      return config.root;
    }

    if (config.rootSelector) {
      return document.querySelector(config.rootSelector);
    }

    return null;
  }

  function resolveManagerElements_v1(root, config) {
    return {
      editorForm: resolveElement_v1(root, config.selectors.editorForm),
      table: resolveElement_v1(root, config.selectors.table),
      tableBody: resolveElement_v1(root, config.selectors.tableBody),
      emptyState: resolveElement_v1(root, config.selectors.emptyState),
      pagination: resolveElement_v1(root, config.selectors.pagination),
      pageSize: resolveElement_v1(root, config.selectors.pageSize),
      hiddenContainer: resolveElement_v1(root, config.selectors.hiddenContainer),
      totalLabel: resolveElement_v1(root, config.selectors.totalLabel),
      searchEl: resolveElement_v1(root, config.selectors.searchInput),
      formCard: resolveElement_v1(root, config.selectors.formCard),
      formTitle: resolveElement_v1(root, config.selectors.formTitle)
    };
  }

  //###################################################################################
  // (6) SINCRONIZACAO
  //###################################################################################

  function emitManagerEvent_v1(manager, eventName, detail) {
    if (!manager || !manager.root) {
      return;
    }

    manager.root.dispatchEvent(
      new CustomEvent(eventName, {
        bubbles: true,
        detail: detail || {}
      })
    );
  }

  function syncHiddenInputs_v1(manager) {
    if (!manager || typeof manager.config.syncHiddenInputs !== "function") {
      return;
    }

    manager.config.syncHiddenInputs({
      manager,
      root: manager.root,
      elements: manager.elements,
      items: manager.getItems(),
      state: manager.state
    });
  }

  function notifyChange_v1(manager) {
    syncHiddenInputs_v1(manager);

    if (typeof manager.config.onChange === "function") {
      manager.config.onChange({
        manager,
        root: manager.root,
        elements: manager.elements,
        items: manager.getItems(),
        state: manager.state
      });
    }

    emitManagerEvent_v1(manager, "appgenesis:configurable-items-change", {
      items: manager.getItems(),
      state: manager.state
    });
  }

  //###################################################################################
  // (7) TABELA
  //###################################################################################

  function getVisibleItems_v1(manager) {
    const query = normalizeLookup_v1(toSafeString_v1(manager.state.searchQuery || ""));

    if (!query) {
      return manager.state.items.slice();
    }

    return manager.state.items.filter((item) => {
      return manager.config.columns.some((column) => {
        const cellValue = column.render
          ? toSafeString_v1(column.render(item, 0, manager))
          : toSafeString_v1(item[column.key] == null ? "" : item[column.key]);
        return normalizeLookup_v1(cellValue).indexOf(query) !== -1;
      });
    });
  }

  const _configurableManagerRegistry = new Map();
  const _configurableManagerByRoot = new WeakMap();
  let _configurableManagerNextId = 1;

  function ensureConfigurableManagerCreateTriggerDelegation() {
    if (ensureConfigurableManagerCreateTriggerDelegation._ready) return;
    ensureConfigurableManagerCreateTriggerDelegation._ready = true;

    document.addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-configurable-create-trigger]");
      if (!trigger) return;

      const targetSelector = String(trigger.dataset.configurableManagerTarget || "").trim();
      if (!targetSelector) return;

      const targetRoot = document.querySelector(targetSelector);
      if (!targetRoot) return;

      const manager = _configurableManagerByRoot.get(targetRoot);
      if (!manager) return;

      event.preventDefault();
      openCreateItem_v1(manager);
    });
  }

  function showConfigurableActionError_v1(message) {
    const shell = window.AppGenesisProcessShell || {};
    const safeMessage = String(message || "").trim() || "Não foi possível concluir a ação.";

    if (shell && typeof shell.showToast === "function") {
      shell.showToast({
        type: "error",
        title: "Erro",
        message: safeMessage
      });
      return;
    }

    if (window.console && typeof window.console.error === "function") {
      window.console.error(safeMessage);
    }
  }

  function handleConfigurableAction_v1(manager, action, itemId, triggerEl) {
    if (action === "edit") {
      editItem_v1(manager, itemId);
      return;
    }

    if (action === "up" || action === "down") {
      moveItem_v1(manager, itemId, action);
      return;
    }

    if (action === "remove") {
      const itemName = manager.config.itemName || "item";
      const shell = window.AppGenesisProcessShell;

      if (shell && typeof shell.createConfirmDialogController === "function") {
        shell.createConfirmDialogController({
          title: "Eliminar",
          message: `Tem a certeza que pretende eliminar este ${itemName}?`,
          confirmLabel: "Eliminar",
          cancelLabel: "Cancelar",
          danger: true
        }).then((confirmed) => {
          if (confirmed) {
            void removeItem_v1(manager, itemId, triggerEl);
          }
        });
      } else {
        if (window.confirm(`Tem a certeza que pretende eliminar este ${itemName}?`)) {
          void removeItem_v1(manager, itemId, triggerEl);
        }
      }
    }
  }

  async function removeItem_v1(manager, itemId, triggerEl) {
    const itemIndex = findItemIndexById_v1(manager, itemId);

    if (itemIndex < 0) {
      return false;
    }

    const item = manager.state.items[itemIndex];
    const deleteHandler = typeof manager.config.deleteItem === "function"
      ? manager.config.deleteItem
      : null;
    const shell = window.AppGenesisProcessShell || {};
    const previousDisabledState = triggerEl ? triggerEl.disabled : false;

    if (triggerEl) {
      triggerEl.disabled = true;
      triggerEl.setAttribute("aria-busy", "true");
    }

    try {
      if (deleteHandler) {
        const deleteResult = await deleteHandler({
          manager,
          item,
          itemId,
          trigger: triggerEl
        });

        if (!deleteResult || deleteResult.success !== true) {
          showConfigurableActionError_v1(
            deleteResult && deleteResult.message ? deleteResult.message : "Não foi possível eliminar o registo."
          );
          return false;
        }
      }

      manager.state.items.splice(itemIndex, 1);
      manager.state.editingId = "";

      if (typeof manager.config.clearEditor === "function") {
        manager.config.clearEditor({
          manager,
          root: manager.root,
          elements: manager.elements
        });
      }

      manager.render();
      notifyChange_v1(manager);

      if (deleteHandler && shell && typeof shell.showToast === "function") {
        shell.showToast({
          type: "success",
          message: "Registo eliminado com sucesso."
        });
      }
      return true;
    } catch (error) {
      showConfigurableActionError_v1(error && error.message ? error.message : "Não foi possível eliminar o registo.");
      return false;
    } finally {
      if (triggerEl) {
        triggerEl.disabled = previousDisabledState;
        triggerEl.removeAttribute("aria-busy");
      }
    }
  }

  function ensureConfigurableManagerActionDelegation() {
    if (ensureConfigurableManagerActionDelegation._ready) return;
    ensureConfigurableManagerActionDelegation._ready = true;

    document.addEventListener("click", (event) => {
      const button = event.target.closest("[data-configurable-action][data-configurable-manager-id]");
      if (!button) return;
      const manager = _configurableManagerRegistry.get(button.dataset.configurableManagerId);
      if (!manager) return;
      const action = String(button.dataset.configurableAction || "").trim();
      const itemId = String(button.dataset.configurableItemId || "").trim();
      if (!action || !itemId) return;
      handleConfigurableAction_v1(manager, action, itemId, button);
    });
  }

  function createRawActionsContainer_v1(manager, item, itemId, fullItemIndex, totalAllItems) {
    if (!manager._configurableManagerId) {
      manager._configurableManagerId = String(_configurableManagerNextId++);
      _configurableManagerRegistry.set(manager._configurableManagerId, manager);
    }

    const container = document.createElement("div");
    container.className = "table-actions";
    const managerId = manager._configurableManagerId;

    function getRowActionIconSvg_v1(actionType) {
      const shell = window.AppGenesisProcessShell || {};

      if (typeof shell.getRowActionIconSvgV1 === "function") {
        return shell.getRowActionIconSvgV1(actionType);
      }

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

    const createActionButton = (actionType, label) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "table-icon-btn";
      button.title = label;
      button.setAttribute("aria-label", label);
      button.innerHTML = getRowActionIconSvg_v1(actionType);
      button.dataset.configurableAction = actionType === "reactivate"
        ? "reactivate"
        : actionType === "move_up"
          ? "up"
          : actionType === "move_down"
            ? "down"
            : actionType === "delete"
              ? "remove"
              : "edit";
      button.dataset.configurableItemId = itemId;
      button.dataset.configurableManagerId = managerId;
      if (actionType === "delete") {
        button.classList.add("table-icon-btn-danger");
      }
      return button;
    };

    // Ordem padrao global dos menus de Acoes: Subir/Descer sempre primeiro (topo do menu),
    // depois Editar, e Eliminar por ultimo (acao destrutiva). Ver templates/macros/admin_subprocess.html
    // (render_admin_subprocess_row_actions), que ja segue a mesma ordem para as tabelas Jinja.
    if (manager.config.actions.move) {
      if (fullItemIndex > 0) {
        container.appendChild(createActionButton("move_up", "Subir"));
      }

      if (fullItemIndex < totalAllItems - 1) {
        container.appendChild(createActionButton("move_down", "Descer"));
      }
    }

    if (manager.config.actions.edit) {
      container.appendChild(createActionButton("edit", "Editar"));
    }

    const canRemoveItem = typeof manager.config.canRemoveItem === "function"
      ? manager.config.canRemoveItem(item, fullItemIndex, totalAllItems, manager) !== false
      : true;

    if (manager.config.actions.remove && canRemoveItem) {
      container.appendChild(createActionButton("delete", "Eliminar"));
    }

    return container;
  }

  function renderTableHeader_v1(manager) {
    if (!manager.elements.table || manager.elements.table.dataset.headerReadyV1 === "1") {
      return;
    }

    let thead = manager.elements.table.querySelector("thead");

    if (!thead) {
      thead = document.createElement("thead");
      manager.elements.table.insertBefore(thead, manager.elements.table.firstChild);
    }

    const row = document.createElement("tr");

    manager.config.columns.forEach((column) => {
      const th = createConfigurableTableCell_v1("th", column, row.children.length, false);
      th.textContent = column.label || column.key;
      row.appendChild(th);
    });

    const actionsTh = createConfigurableTableCell_v1(
      "th",
      {
        className: "configurable-items-actions-col-v1 admin-col-actions-v1"
      },
      manager.config.columns.length,
      true
    );
    actionsTh.textContent = "Ações";
    row.appendChild(actionsTh);

    thead.innerHTML = "";
    thead.appendChild(row);
    manager.elements.table.dataset.headerReadyV1 = "1";
  }

  function renderTableBody_v1(manager) {
    const tableBody = manager.elements.tableBody;

    if (!tableBody) {
      return;
    }

    const filteredItems = getVisibleItems_v1(manager);
    const totalAllItems = manager.state.items.length;
    const totalItems = filteredItems.length;
    const visibleItems = filteredItems.slice(0, manager.state.visibleCount);

    tableBody.innerHTML = "";

    visibleItems.forEach((item, visibleIndex) => {
      const absoluteIndex = visibleIndex;
      const itemId = item.__managerId;
      const fullItemIndex = manager.state.items.findIndex((it) => it.__managerId === itemId);
      const row = createConfigurableRow_v1(manager, item, absoluteIndex, fullItemIndex, totalAllItems);
      tableBody.appendChild(row);
    });

    const _shell = window.AppGenesisProcessShell;
    if (_shell && typeof _shell.enhanceTableActionMenus === "function") {
      _shell.enhanceTableActionMenus({ root: manager.root });
    }

    if (manager.elements.table) {
      manager.elements.table.style.display = totalItems ? "" : "none";
    }

    if (manager.elements.emptyState) {
      manager.elements.emptyState.style.display = totalItems ? "none" : "";
      manager.elements.emptyState.textContent = `Sem ${manager.config.itemNamePlural} criados.`;
    }

    if (manager.elements.totalLabel) {
      const pluralName = totalAllItems === 1 ? manager.config.itemName : manager.config.itemNamePlural;
      const hasSearch = manager.state.searchQuery && manager.state.searchQuery.trim();
      if (hasSearch && totalItems !== totalAllItems) {
        manager.elements.totalLabel.textContent = `${totalItems} de ${totalAllItems} ${pluralName}`;
      } else {
        manager.elements.totalLabel.textContent = `${totalAllItems} ${pluralName}`;
      }
    }

    applyResponsiveColumnsToTable_v1(manager, manager.elements.table);
    refreshTableActionMenus_v1(manager);
  }

  //###################################################################################
  // (8) PAGINACAO
  //###################################################################################

  function renderPageSize_v1(manager) {
    const pageSizeEl = manager.elements.pageSize;

    if (!pageSizeEl || pageSizeEl.dataset.boundV1 === "1") {
      return;
    }

    if (pageSizeEl.tagName === "SELECT") {
      pageSizeEl.innerHTML = "";

      manager.config.pageSizeOptions.forEach((rawOption) => {
        const optionValue = clampNumber_v1(rawOption, 1, 100, manager.config.pageSizeDefault);
        const option = document.createElement("option");
        option.value = String(optionValue);
        option.textContent = String(optionValue);

        if (optionValue === manager.state.pageSize) {
          option.selected = true;
        }

        pageSizeEl.appendChild(option);
      });
    }

    pageSizeEl.dataset.boundV1 = "1";

    pageSizeEl.addEventListener("change", () => {
      manager.state.pageSize = clampNumber_v1(pageSizeEl.value, 1, 100, manager.config.pageSizeDefault);
      manager.state.visibleCount = manager.state.pageSize;
      manager.render();
      notifyChange_v1(manager);
    });
  }

  function renderPagination_v1(manager) {
    const paginationEl = manager.elements.pagination;

    if (!paginationEl) {
      return;
    }

    const footerEl = paginationEl.parentElement;

    let lessEl = footerEl
      ? footerEl.querySelector(".configurable-items-less-v1")
      : null;

    if (!lessEl && footerEl) {
      lessEl = document.createElement("div");
      lessEl.className = "appgenesis-load-more-less-v1 configurable-items-less-v1";
      footerEl.appendChild(lessEl);
    }

    const filteredItems = getVisibleItems_v1(manager);
    const totalItems = filteredItems.length;
    const currentCount = Math.min(manager.state.visibleCount, totalItems);
    const showMais = currentCount < totalItems;
    const showMenos = manager.state.visibleCount > manager.state.pageSize;
    const showCounter = totalItems > 0;

    paginationEl.innerHTML = "";
    if (lessEl) {
      lessEl.innerHTML = "";
    }

    if (!showCounter) {
      paginationEl.style.display = "none";
      if (lessEl) {
        lessEl.style.display = "none";
      }
      // O CSS partilhado com o Process Shell aplica display:flex !important em
      // .appgenesis-load-more-status-v1; so o atributo [hidden] no rodape (que tem
      // uma regra !important dedicada) consegue realmente escondê-lo.
      if (footerEl) {
        footerEl.hidden = true;
      }
      return;
    }

    if (footerEl) {
      footerEl.hidden = false;
    }
    paginationEl.style.display = "";
    if (lessEl) {
      lessEl.style.display = "";
    }

    if (showMais) {
      const moreBtn = createElement_v1("button", "appgenesis-load-more-btn-v1", "Mais");
      moreBtn.type = "button";
      moreBtn.addEventListener("click", () => {
        manager.state.visibleCount += manager.state.pageSize;
        manager.render();
      });
      paginationEl.appendChild(moreBtn);
    }

    const counter = createElement_v1("span", "appgenesis-load-more-counter-v1", `[ ${currentCount} / ${totalItems} ]`);
    paginationEl.appendChild(counter);

    if (showMenos && lessEl) {
      const lessBtn = createElement_v1("button", "appgenesis-load-more-btn-v1", "Menos");
      lessBtn.type = "button";
      lessBtn.addEventListener("click", () => {
        manager.state.visibleCount = manager.state.pageSize;
        manager.render();
      });
      lessEl.appendChild(lessBtn);
    }
  }

  //###################################################################################
  // (9) ACOES
  //###################################################################################

  function findItemIndexById_v1(manager, itemId) {
    return manager.state.items.findIndex((item) => String(item.__managerId) === String(itemId));
  }

  function focusFirstEditableField_v1(container) {
    if (!container) {
      return;
    }

    const field = container.querySelector(
      "input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])"
    );

    if (field && typeof field.focus === "function") {
      field.focus();
    }
  }

  function openFormCard_v1(manager, title) {
    const formCard = manager.elements.formCard;

    if (formCard) {
      formCard.hidden = false;

      if (typeof formCard.scrollIntoView === "function") {
        formCard.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }

    if (manager.elements.formTitle && title) {
      manager.elements.formTitle.textContent = title;
    }
  }

  function closeFormCard_v1(manager) {
    if (manager.elements.formCard) {
      manager.elements.formCard.hidden = true;
    }
  }

  function openCreateItem_v1(manager) {
    manager.state.editingId = "";
    manager.root.classList.remove("configurable-items-editing-v1");

    if (typeof manager.config.clearEditor === "function") {
      manager.config.clearEditor({
        manager,
        root: manager.root,
        elements: manager.elements
      });
    }

    openFormCard_v1(manager, manager.config.createTitle);

    if (manager.elements.formCard) {
      focusFirstEditableField_v1(manager.elements.editorForm);
    }

    emitManagerEvent_v1(manager, "appgenesis:configurable-items-create-open", {});
  }

  function closeEditorItem_v1(manager) {
    manager.state.editingId = "";
    manager.root.classList.remove("configurable-items-editing-v1");

    if (typeof manager.config.clearEditor === "function") {
      manager.config.clearEditor({
        manager,
        root: manager.root,
        elements: manager.elements
      });
    }

    closeFormCard_v1(manager);
  }

  function editItem_v1(manager, itemId) {
    const itemIndex = findItemIndexById_v1(manager, itemId);

    if (itemIndex < 0) {
      return;
    }

    const item = manager.state.items[itemIndex];
    manager.state.editingId = item.__managerId;

    if (typeof window.logAppGenesisProcessEditorDebugV1 === "function") {
      window.logAppGenesisProcessEditorDebugV1("configurableItemsManager:editItem", {
        itemId,
        itemLabel: item && item.label,
        itemKey: item && item.key,
        managerRootId: manager.root && manager.root.id,
        activeTabPane: (function () {
          const activePane = document.querySelector(".process-edit-pane.active");
          return activePane ? activePane.getAttribute("data-process-edit-pane") : null;
        })()
      });
    }

    if (typeof manager.config.loadEditorItem === "function") {
      manager.config.loadEditorItem(item, {
        manager,
        root: manager.root,
        elements: manager.elements,
        index: itemIndex
      });
    }

    manager.root.classList.add("configurable-items-editing-v1");
    openFormCard_v1(manager, manager.config.editTitle);

    if (manager.elements.formCard) {
      focusFirstEditableField_v1(manager.elements.editorForm);
    }

    emitManagerEvent_v1(manager, "appgenesis:configurable-items-edit", { item, index: itemIndex });
  }

  function moveItem_v1(manager, itemId, direction) {
    const itemIndex = findItemIndexById_v1(manager, itemId);

    if (itemIndex < 0) {
      return;
    }

    const targetIndex = direction === "up" ? itemIndex - 1 : itemIndex + 1;

    if (targetIndex < 0 || targetIndex >= manager.state.items.length) {
      return;
    }

    const item = manager.state.items[itemIndex];
    manager.state.items.splice(itemIndex, 1);
    manager.state.items.splice(targetIndex, 0, item);

    manager.state.items.forEach((row, index) => {
      row.__managerOrder = index + 1;
    });

    manager.render();
    notifyChange_v1(manager);
  }

  function addOrUpdateItem_v1(manager, rawItem) {
    const normalizedItems = normalizeItems_v1([rawItem], manager.config);
    const item = normalizedItems[0];

    if (!item) {
      return;
    }

    const editingId = manager.state.editingId;

    if (editingId) {
      const itemIndex = findItemIndexById_v1(manager, editingId);

      if (itemIndex >= 0) {
        item.__managerId = editingId;
        item.__managerOrder = manager.state.items[itemIndex].__managerOrder;
        manager.state.items[itemIndex] = item;
      } else {
        manager.state.items.push(item);
      }
    } else {
      item.__managerOrder = manager.state.items.length + 1;
      manager.state.items.push(item);
      manager.state.visibleCount = manager.state.items.length;
    }

    manager.state.editingId = "";
    manager.root.classList.remove("configurable-items-editing-v1");

    if (typeof manager.config.clearEditor === "function") {
      manager.config.clearEditor({
        manager,
        root: manager.root,
        elements: manager.elements
      });
    }

    manager.render();
    notifyChange_v1(manager);
  }

  //###################################################################################
  // (10) BINDINGS
  //###################################################################################

  function bindTableActions_v1(manager) {
    if (!manager.elements.tableBody || manager.elements.tableBody.dataset.boundActionsV1 === "1") {
      return;
    }
    manager.elements.tableBody.dataset.boundActionsV1 = "1";
  }

  function bindPaginationActions_v1(manager) {
    // Load-more buttons have direct event listeners from renderPagination_v1
  }

  function bindEditorForm_v1(manager) {
    if (!manager.elements.editorForm || manager.elements.editorForm.dataset.boundEditorV1 === "1") {
      return;
    }

    manager.elements.editorForm.dataset.boundEditorV1 = "1";

    manager.elements.editorForm.addEventListener("submit", (event) => {
      if (manager.config.preventEditorSubmit) {
        event.preventDefault();
      }

      if (typeof manager.config.readEditorItem !== "function") {
        return;
      }

      const item = manager.config.readEditorItem({
        manager,
        root: manager.root,
        elements: manager.elements,
        state: manager.state
      });

      if (!item) {
        return;
      }

      if (typeof manager.config.validateItem === "function") {
        const validationResult = manager.config.validateItem(item, {
          manager,
          root: manager.root,
          elements: manager.elements,
          state: manager.state,
          items: manager.getItems()
        });

        if (validationResult === false) {
          return;
        }

        if (validationResult && validationResult.valid === false) {
          if (validationResult.message) {
            showAlertDialog_v1({
              title: "Validacao",
              message: validationResult.message
            });
          }
          return;
        }
      }

      addOrUpdateItem_v1(manager, item);
    });
  }

  function bindSearchInput_v1(manager) {
    const searchEl = manager.elements.searchEl;

    if (!searchEl || searchEl.dataset.boundSearchV1 === "1") {
      return;
    }

    searchEl.dataset.boundSearchV1 = "1";

    searchEl.addEventListener("input", () => {
      manager.state.searchQuery = searchEl.value || "";
      manager.state.visibleCount = manager.state.pageSize;
      manager.render();
    });
  }

  function bindParentFormSubmit_v1(manager) {
    const parentForm = manager.root.closest("form");

    if (!parentForm || parentForm.dataset.configurableSubmitBoundV1 === "1") {
      return;
    }

    parentForm.dataset.configurableSubmitBoundV1 = "1";

    parentForm.addEventListener("submit", () => {
      syncHiddenInputs_v1(manager);
    });
  }

  //###################################################################################
  // (11) RENDER PRINCIPAL
  //###################################################################################

  function renderManager_v1(manager) {
    renderTableHeader_v1(manager);
    renderPageSize_v1(manager);
    renderTableBody_v1(manager);
    renderPagination_v1(manager);
    ensureResponsiveColumnsObserver_v1(manager);

    if (typeof manager.config.onRender === "function") {
      manager.config.onRender({
        manager,
        root: manager.root,
        elements: manager.elements,
        items: manager.getItems(),
        state: manager.state
      });
    }

    refreshTableActionMenus_v1(manager);
  }

  function normalizePartitionView_v1(rawView, index) {
    const view = rawView && typeof rawView === "object" ? rawView : {};

    return {
      key: String(view.key || `partition_${index + 1}`).trim(),
      filter: typeof view.filter === "function" ? view.filter : null,
      elements: view.elements && typeof view.elements === "object" ? view.elements : {},
      emptyText: String(view.emptyText || "").trim(),
      totalLabel: String(view.totalLabel || "").trim(),
      pageSizeDefault: Number.isFinite(Number(view.pageSizeDefault))
        ? clampNumber_v1(view.pageSizeDefault, 1, 100, DEFAULT_CONFIGURABLE_PAGE_SIZE_V1)
        : DEFAULT_CONFIGURABLE_PAGE_SIZE_V1,
      itemName: String(view.itemName || "").trim(),
      itemNamePlural: String(view.itemNamePlural || "").trim()
    };
  }

  function ensurePartitionState_v1(manager, view) {
    if (!manager.state.partitionViews || typeof manager.state.partitionViews !== "object") {
      manager.state.partitionViews = {};
    }

    if (!manager.state.partitionViews[view.key]) {
      manager.state.partitionViews[view.key] = {
        pageSize: view.pageSizeDefault,
        visibleCount: view.pageSizeDefault
      };
    }

    const viewState = manager.state.partitionViews[view.key];
    viewState.pageSize = clampNumber_v1(viewState.pageSize, 1, 100, view.pageSizeDefault);
    viewState.visibleCount = clampNumber_v1(
      viewState.visibleCount,
      1,
      100,
      viewState.pageSize
    );

    return viewState;
  }

  function bindPartitionPageSize_v1(manager, view, viewState) {
    const pageSizeEl = view.elements.pageSize;

    if (!pageSizeEl || pageSizeEl.dataset.boundPartitionV1 === "1") {
      return;
    }

    if (pageSizeEl.tagName === "SELECT") {
      pageSizeEl.innerHTML = "";

      manager.config.pageSizeOptions.forEach((rawOption) => {
        const optionValue = clampNumber_v1(rawOption, 1, 100, view.pageSizeDefault);
        const option = document.createElement("option");
        option.value = String(optionValue);
        option.textContent = String(optionValue);
        if (optionValue === viewState.pageSize) {
          option.selected = true;
        }
        pageSizeEl.appendChild(option);
      });
    }

    pageSizeEl.dataset.boundPartitionV1 = "1";
    pageSizeEl.addEventListener("change", () => {
      viewState.pageSize = clampNumber_v1(pageSizeEl.value, 1, 100, view.pageSizeDefault);
      viewState.visibleCount = viewState.pageSize;
      manager.render();
    });
  }

  function renderPartitionPagination_v1(manager, view, viewState, totalItems) {
    const paginationEl = view.elements.pagination;

    if (!paginationEl) {
      return;
    }

    const footerEl = paginationEl.parentElement;
    let lessEl = footerEl ? footerEl.querySelector(".configurable-items-less-v1") : null;

    if (!lessEl && footerEl) {
      lessEl = document.createElement("div");
      lessEl.className = "appgenesis-load-more-less-v1 configurable-items-less-v1";
      footerEl.appendChild(lessEl);
    }

    const currentCount = Math.min(viewState.visibleCount, totalItems);
    const showMais = currentCount < totalItems;
    const showMenos = viewState.visibleCount > viewState.pageSize;

    paginationEl.innerHTML = "";
    if (lessEl) {
      lessEl.innerHTML = "";
    }

    if (!totalItems) {
      paginationEl.style.display = "none";
      if (lessEl) {
        lessEl.style.display = "none";
      }
      if (footerEl) {
        footerEl.hidden = true;
      }
      return;
    }

    if (footerEl) {
      footerEl.hidden = false;
    }
    paginationEl.style.display = "";
    if (lessEl) {
      lessEl.style.display = "";
    }

    if (showMais) {
      const moreBtn = createElement_v1("button", "appgenesis-load-more-btn-v1", "Mais");
      moreBtn.type = "button";
      moreBtn.addEventListener("click", () => {
        viewState.visibleCount += viewState.pageSize;
        manager.render();
      });
      paginationEl.appendChild(moreBtn);
    }

    paginationEl.appendChild(
      createElement_v1("span", "appgenesis-load-more-counter-v1", `[ ${currentCount} / ${totalItems} ]`)
    );

    if (showMenos && lessEl) {
      const lessBtn = createElement_v1("button", "appgenesis-load-more-btn-v1", "Menos");
      lessBtn.type = "button";
      lessBtn.addEventListener("click", () => {
        viewState.visibleCount = Math.max(viewState.pageSize, viewState.visibleCount - viewState.pageSize);
        manager.render();
      });
      lessEl.appendChild(lessBtn);
    }
  }

  function renderPartitionedView_v1(manager, view, searchFilteredItems) {
    const elements = view.elements;

    if (!elements || !elements.tableBody || !elements.table) {
      return;
    }

    const viewState = ensurePartitionState_v1(manager, view);
    const viewItems = searchFilteredItems.filter((item) => {
      return view.filter ? view.filter(item, manager) : true;
    });
    const totalAllItems = manager.state.items.length;
    const totalItems = viewItems.length;

    bindPartitionPageSize_v1(manager, view, viewState);

    if (viewState.visibleCount < viewState.pageSize) {
      viewState.visibleCount = viewState.pageSize;
    }

    if (totalItems === 0) {
      viewState.visibleCount = viewState.pageSize;
    } else if (viewState.visibleCount > totalItems) {
      viewState.visibleCount = totalItems;
    }

    const visibleItems = viewItems.slice(0, viewState.visibleCount);
    elements.tableBody.innerHTML = "";

    visibleItems.forEach((item, visibleIndex) => {
      const itemId = item.__managerId;
      const fullItemIndex = manager.state.items.findIndex((candidate) => candidate.__managerId === itemId);
      elements.tableBody.appendChild(
        createConfigurableRow_v1(manager, item, visibleIndex, fullItemIndex, totalAllItems)
      );
    });

    if (elements.table) {
      elements.table.style.display = totalItems ? "" : "none";
    }

    if (elements.emptyState) {
      elements.emptyState.style.display = totalItems ? "none" : "";
      if (view.emptyText) {
        elements.emptyState.textContent = view.emptyText;
      }
    }

    if (elements.totalLabel) {
      const pluralName = totalItems === 1
        ? (view.itemName || manager.config.itemName)
        : (view.itemNamePlural || manager.config.itemNamePlural);
      const hasSearch = manager.state.searchQuery && manager.state.searchQuery.trim();
      if (hasSearch && totalItems !== searchFilteredItems.length) {
        elements.totalLabel.textContent = `${totalItems} de ${searchFilteredItems.length} ${pluralName}`;
      } else {
        elements.totalLabel.textContent = `${totalItems} ${pluralName}`;
      }
      elements.totalLabel.classList.remove("configurable-items-hidden-v1");
    }

    renderPartitionPagination_v1(manager, view, viewState, totalItems);
    applyResponsiveColumnsToTable_v1(manager, elements.table);
  }

  function renderConfigurableItemsPartitionedViews_v1(manager, rawViews) {
    if (!manager || !Array.isArray(rawViews) || !rawViews.length) {
      return;
    }

    const searchFilteredItems = getVisibleItems_v1(manager);
    const views = rawViews.map(normalizePartitionView_v1);

    views.forEach((view) => renderPartitionedView_v1(manager, view, searchFilteredItems));

    ensureResponsiveColumnsObserver_v1(manager);

    if (typeof manager.config.onRender === "function") {
      manager.config.onRender({
        manager,
        root: manager.root,
        elements: manager.elements,
        items: manager.getItems(),
        state: manager.state
      });
    }

    refreshTableActionMenus_v1(manager);
  }

  //###################################################################################
  // (12) API PUBLICA
  //###################################################################################

  function createConfigurableItemsManager_v1(rawConfig) {
    const config = normalizeConfigurableItemsConfig_v1(rawConfig);
    const root = resolveManagerRoot_v1(config);

    if (!root) {
      return null;
    }

    const manager = {
      root,
      config,
      state: createInitialState_v1(config),
      elements: null,

      getItems() {
        return this.state.items.map((item) => ({ ...item }));
      },

      setItems(items) {
        this.state.items = normalizeItems_v1(items, this.config);
        this.state.visibleCount = this.state.pageSize;
        this.render();
        notifyChange_v1(this);
      },

      addOrUpdate(item) {
        addOrUpdateItem_v1(this, item);
      },

      remove(itemId) {
        removeItem_v1(this, itemId);
      },

      move(itemId, direction) {
        moveItem_v1(this, itemId, direction);
      },

      clearEditing() {
        closeEditorItem_v1(this);
      },

      syncHiddenInputs() {
        syncHiddenInputs_v1(this);
      },

      render() {
        renderManager_v1(this);
      },

      openCreate() {
        openCreateItem_v1(this);
      },

      openEdit(itemId) {
        editItem_v1(this, itemId);
      },

      closeEditor() {
        closeEditorItem_v1(this);
      },

      isEditing() {
        return Boolean(this.state.editingId);
      }
    };

    manager.elements = resolveManagerElements_v1(root, config);

    root.dataset.configurableManagerActive = "1";
    root.classList.add("configurable-items-manager-v1");
    _configurableManagerByRoot.set(root, manager);

    bindTableActions_v1(manager);
    bindPaginationActions_v1(manager);
    bindEditorForm_v1(manager);
    bindSearchInput_v1(manager);
    bindParentFormSubmit_v1(manager);

    ensureConfigurableManagerActionDelegation();
    ensureConfigurableManagerCreateTriggerDelegation();

    if (!config.skipInitialRender) {
      manager.render();
      notifyChange_v1(manager);
    }

    manager.state.initialized = true;

    return manager;
  }

  namespace.createConfigurableItemsManager_v1 = createConfigurableItemsManager_v1;
  namespace.renderConfigurableItemsPartitionedViews_v1 = renderConfigurableItemsPartitionedViews_v1;
  namespace.normalizeLookup_v1 = normalizeLookup_v1;
  namespace.showAlertDialog_v1 = showAlertDialog_v1;
  namespace.toSafeString_v1 = toSafeString_v1;
  namespace.DEFAULT_CONFIGURABLE_PAGE_SIZE_V1 = DEFAULT_CONFIGURABLE_PAGE_SIZE_V1;
  namespace.DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1 = DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1;
})(window, document);
