//###################################################################################
// APPVERBOBRAGA - CONFIGURABLE ITEMS MANAGER CORE V1
//###################################################################################

(function (window, document) {
  "use strict";

  //###################################################################################
  // (1) NAMESPACE
  //###################################################################################

  if (!window.AppVerboConfigurableItems) {
    window.AppVerboConfigurableItems = {};
  }

  const namespace = window.AppVerboConfigurableItems;

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

    return {
      key: String(column.key || "").trim(),
      label: String(column.label || column.key || "").trim(),
      className: String(column.className || "").trim(),
      render: typeof column.render === "function" ? column.render : null
    };
  }

  //###################################################################################
  // (3) NORMALIZAR CONFIGURACAO
  //###################################################################################

  function normalizeConfigurableItemsConfig_v1(rawConfig) {
    const config = rawConfig && typeof rawConfig === "object" ? rawConfig : {};
    const selectors = config.selectors && typeof config.selectors === "object" ? config.selectors : {};
    const pageSizeOptions = toArray_v1(config.pageSizeOptions).length
      ? toArray_v1(config.pageSizeOptions)
      : [5, 10, 25];

    return {
      root: config.root || null,
      rootSelector: String(config.rootSelector || "").trim(),
      itemName: String(config.itemName || "item").trim(),
      itemNamePlural: String(config.itemNamePlural || "itens").trim(),
      pageSizeDefault: clampNumber_v1(config.pageSizeDefault, 1, 100, 5),
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
        totalLabel: selectors.totalLabel || "[data-configurable-total-label]"
      },
      getItemId: typeof config.getItemId === "function" ? config.getItemId : defaultGetItemId_v1,
      readEditorItem: typeof config.readEditorItem === "function" ? config.readEditorItem : null,
      loadEditorItem: typeof config.loadEditorItem === "function" ? config.loadEditorItem : null,
      clearEditor: typeof config.clearEditor === "function" ? config.clearEditor : null,
      validateItem: typeof config.validateItem === "function" ? config.validateItem : null,
      syncHiddenInputs: typeof config.syncHiddenInputs === "function" ? config.syncHiddenInputs : null,
      onChange: typeof config.onChange === "function" ? config.onChange : null,
      onRender: typeof config.onRender === "function" ? config.onRender : null,
      initialItems: toArray_v1(config.initialItems),
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
      page: 1,
      pageSize: config.pageSizeDefault,
      editingId: "",
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
      totalLabel: resolveElement_v1(root, config.selectors.totalLabel)
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

    emitManagerEvent_v1(manager, "appverbo:configurable-items-change", {
      items: manager.getItems(),
      state: manager.state
    });
  }

  //###################################################################################
  // (7) TABELA
  //###################################################################################

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
      const th = createElement_v1("th", column.className, column.label || column.key);
      row.appendChild(th);
    });

    const actionsTh = createElement_v1("th", "configurable-items-actions-col-v1", "Ações");
    row.appendChild(actionsTh);

    thead.innerHTML = "";
    thead.appendChild(row);
    manager.elements.table.dataset.headerReadyV1 = "1";
  }

  function createActionButton_v1(action, label, itemId, disabled) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "configurable-items-action-btn-v1";
    button.dataset.configurableAction = action;
    button.dataset.configurableItemId = itemId;
    button.textContent = label;

    if (disabled) {
      button.disabled = true;
    }

    return button;
  }

  function renderTableBody_v1(manager) {
    const tableBody = manager.elements.tableBody;

    if (!tableBody) {
      return;
    }

    const items = manager.getItems();
    const totalItems = items.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / manager.state.pageSize));

    if (manager.state.page > totalPages) {
      manager.state.page = totalPages;
    }

    const startIndex = (manager.state.page - 1) * manager.state.pageSize;
    const visibleItems = items.slice(startIndex, startIndex + manager.state.pageSize);

    tableBody.innerHTML = "";

    visibleItems.forEach((item, visibleIndex) => {
      const absoluteIndex = startIndex + visibleIndex;
      const itemId = item.__managerId;
      const row = document.createElement("tr");
      row.dataset.configurableItemId = itemId;

      manager.config.columns.forEach((column) => {
        const td = document.createElement("td");
        if (column.className) {
          td.className = column.className;
        }

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

      const actionsTd = document.createElement("td");
      actionsTd.className = "configurable-items-actions-v1";

      if (manager.config.actions.edit) {
        actionsTd.appendChild(createActionButton_v1("edit", "Editar", itemId, false));
      }

      if (manager.config.actions.move) {
        actionsTd.appendChild(createActionButton_v1("up", "Subir", itemId, absoluteIndex === 0));
        actionsTd.appendChild(createActionButton_v1("down", "Descer", itemId, absoluteIndex === totalItems - 1));
      }

      if (manager.config.actions.remove) {
        actionsTd.appendChild(createActionButton_v1("remove", "Remover", itemId, false));
      }

      row.appendChild(actionsTd);
      tableBody.appendChild(row);
    });

    if (manager.elements.table) {
      manager.elements.table.style.display = totalItems ? "" : "none";
    }

    if (manager.elements.emptyState) {
      manager.elements.emptyState.style.display = totalItems ? "none" : "";
      manager.elements.emptyState.textContent = `Sem ${manager.config.itemNamePlural} criados.`;
    }

    if (manager.elements.totalLabel) {
      manager.elements.totalLabel.textContent = `${totalItems} ${totalItems === 1 ? manager.config.itemName : manager.config.itemNamePlural}`;
    }
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
      manager.state.page = 1;
      manager.render();
      notifyChange_v1(manager);
    });
  }

  function renderPagination_v1(manager) {
    const paginationEl = manager.elements.pagination;

    if (!paginationEl) {
      return;
    }

    const totalItems = manager.state.items.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / manager.state.pageSize));

    if (manager.state.page > totalPages) {
      manager.state.page = totalPages;
    }

    paginationEl.innerHTML = "";

    if (totalItems <= manager.state.pageSize) {
      paginationEl.style.display = "none";
      return;
    }

    paginationEl.style.display = "";

    const previousButton = createElement_v1("button", "configurable-items-page-btn-v1", "Anterior");
    previousButton.type = "button";
    previousButton.disabled = manager.state.page <= 1;
    previousButton.dataset.configurablePage = String(manager.state.page - 1);
    paginationEl.appendChild(previousButton);

    for (let pageNumber = 1; pageNumber <= totalPages; pageNumber += 1) {
      const pageButton = createElement_v1("button", "configurable-items-page-btn-v1", String(pageNumber));
      pageButton.type = "button";
      pageButton.dataset.configurablePage = String(pageNumber);

      if (pageNumber === manager.state.page) {
        pageButton.classList.add("active");
      }

      paginationEl.appendChild(pageButton);
    }

    const nextButton = createElement_v1("button", "configurable-items-page-btn-v1", "Próxima");
    nextButton.type = "button";
    nextButton.disabled = manager.state.page >= totalPages;
    nextButton.dataset.configurablePage = String(manager.state.page + 1);
    paginationEl.appendChild(nextButton);
  }

  //###################################################################################
  // (9) ACOES
  //###################################################################################

  function findItemIndexById_v1(manager, itemId) {
    return manager.state.items.findIndex((item) => String(item.__managerId) === String(itemId));
  }

  function editItem_v1(manager, itemId) {
    const itemIndex = findItemIndexById_v1(manager, itemId);

    if (itemIndex < 0) {
      return;
    }

    const item = manager.state.items[itemIndex];
    manager.state.editingId = item.__managerId;

    if (typeof manager.config.loadEditorItem === "function") {
      manager.config.loadEditorItem(item, {
        manager,
        root: manager.root,
        elements: manager.elements,
        index: itemIndex
      });
    }

    manager.root.classList.add("configurable-items-editing-v1");
    emitManagerEvent_v1(manager, "appverbo:configurable-items-edit", { item, index: itemIndex });
  }

  function removeItem_v1(manager, itemId) {
    const itemIndex = findItemIndexById_v1(manager, itemId);

    if (itemIndex < 0) {
      return;
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
      manager.state.page = Math.max(1, Math.ceil(manager.state.items.length / manager.state.pageSize));
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

    manager.elements.tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("[data-configurable-action]");

      if (!button) {
        return;
      }

      const action = String(button.dataset.configurableAction || "").trim();
      const itemId = String(button.dataset.configurableItemId || "").trim();

      if (!action || !itemId) {
        return;
      }

      if (action === "edit") {
        editItem_v1(manager, itemId);
        return;
      }

      if (action === "remove") {
        removeItem_v1(manager, itemId);
        return;
      }

      if (action === "up" || action === "down") {
        moveItem_v1(manager, itemId, action);
      }
    });
  }

  function bindPaginationActions_v1(manager) {
    if (!manager.elements.pagination || manager.elements.pagination.dataset.boundPaginationV1 === "1") {
      return;
    }

    manager.elements.pagination.dataset.boundPaginationV1 = "1";

    manager.elements.pagination.addEventListener("click", (event) => {
      const button = event.target.closest("[data-configurable-page]");

      if (!button || button.disabled) {
        return;
      }

      manager.state.page = clampNumber_v1(button.dataset.configurablePage, 1, 100000, 1);
      manager.render();
    });
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
            window.alert(validationResult.message);
          }
          return;
        }
      }

      addOrUpdateItem_v1(manager, item);
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

    if (typeof manager.config.onRender === "function") {
      manager.config.onRender({
        manager,
        root: manager.root,
        elements: manager.elements,
        items: manager.getItems(),
        state: manager.state
      });
    }
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
        this.state.page = 1;
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
        this.state.editingId = "";
        this.root.classList.remove("configurable-items-editing-v1");

        if (typeof this.config.clearEditor === "function") {
          this.config.clearEditor({
            manager: this,
            root: this.root,
            elements: this.elements
          });
        }
      },

      syncHiddenInputs() {
        syncHiddenInputs_v1(this);
      },

      render() {
        renderManager_v1(this);
      }
    };

    manager.elements = resolveManagerElements_v1(root, config);

    root.dataset.configurableManagerActive = "1";
    root.classList.add("configurable-items-manager-v1");

    bindTableActions_v1(manager);
    bindPaginationActions_v1(manager);
    bindEditorForm_v1(manager);
    bindParentFormSubmit_v1(manager);

    manager.render();
    notifyChange_v1(manager);

    manager.state.initialized = true;

    return manager;
  }

  namespace.createConfigurableItemsManager_v1 = createConfigurableItemsManager_v1;
  namespace.normalizeLookup_v1 = normalizeLookup_v1;
  namespace.toSafeString_v1 = toSafeString_v1;
})(window, document);
