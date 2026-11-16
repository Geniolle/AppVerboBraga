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
  const DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1 = [5, 10, 20, 50];

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
      getItemLabel: typeof config.getItemLabel === "function" ? config.getItemLabel : null,
      readEditorItem: typeof config.readEditorItem === "function" ? config.readEditorItem : null,
      loadEditorItem: typeof config.loadEditorItem === "function" ? config.loadEditorItem : null,
      clearEditor: typeof config.clearEditor === "function" ? config.clearEditor : null,
      validateItem: typeof config.validateItem === "function" ? config.validateItem : null,
      syncHiddenInputs: typeof config.syncHiddenInputs === "function" ? config.syncHiddenInputs : null,
      onChange: typeof config.onChange === "function" ? config.onChange : null,
      onRender: typeof config.onRender === "function" ? config.onRender : null,
      initialItems: toArray_v1(config.initialItems),
      preventEditorSubmit: config.preventEditorSubmit !== false,
      persistOnChange: config.persistOnChange === true,
      inlineEditor: config.inlineEditor === true,
      actions: {
        edit: config.actions && config.actions.edit === false ? false : true,
        remove: config.actions && config.actions.remove === false ? false : true,
        move: config.actions && config.actions.move === false ? false : true,
        copy: config.actions && config.actions.copy === true
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

  function handleConfigurableAction_v1(manager, action, itemId) {
    if (action === "edit") {
      editItem_v1(manager, itemId);
      return;
    }

    if (action === "copy") {
      copyItem_v1(manager, itemId);
      return;
    }

    if (action === "up" || action === "down") {
      openMovePicker_v1(manager, itemId, action);
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
          if (confirmed) removeItem_v1(manager, itemId);
        });
      } else {
        if (window.confirm(`Tem a certeza que pretende eliminar este ${itemName}?`)) {
          removeItem_v1(manager, itemId);
        }
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
      handleConfigurableAction_v1(manager, action, itemId);
    });
  }

  function createRawActionsContainer_v1(manager, itemId, fullItemIndex, totalAllItems) {
    if (!manager._configurableManagerId) {
      manager._configurableManagerId = String(_configurableManagerNextId++);
      _configurableManagerRegistry.set(manager._configurableManagerId, manager);
    }

    const container = document.createElement("div");
    container.className = "table-actions";
    const managerId = manager._configurableManagerId;

    // Ordem padrao global dos menus de Acoes: Subir/Descer sempre primeiro (topo do menu),
    // depois Editar, e Eliminar por ultimo (acao destrutiva). Ver templates/macros/admin_subprocess.html
    // (render_admin_subprocess_row_actions), que ja segue a mesma ordem para as tabelas Jinja.
    if (manager.config.actions.move) {
      if (fullItemIndex > 0) {
        const upBtn = document.createElement("button");
        upBtn.type = "button";
        upBtn.title = "Subir";
        upBtn.setAttribute("aria-label", "Subir");
        upBtn.dataset.configurableAction = "up";
        upBtn.dataset.configurableItemId = itemId;
        upBtn.dataset.configurableManagerId = managerId;
        upBtn.textContent = "Subir";
        container.appendChild(upBtn);
      }

      if (fullItemIndex < totalAllItems - 1) {
        const downBtn = document.createElement("button");
        downBtn.type = "button";
        downBtn.title = "Descer";
        downBtn.setAttribute("aria-label", "Descer");
        downBtn.dataset.configurableAction = "down";
        downBtn.dataset.configurableItemId = itemId;
        downBtn.dataset.configurableManagerId = managerId;
        downBtn.textContent = "Descer";
        container.appendChild(downBtn);
      }
    }

    if (manager.config.actions.edit) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.title = "Editar";
      btn.setAttribute("aria-label", "Editar");
      btn.dataset.configurableAction = "edit";
      btn.dataset.configurableItemId = itemId;
      btn.dataset.configurableManagerId = managerId;
      btn.textContent = "Editar";
      container.appendChild(btn);
    }

    if (manager.config.actions.copy) {
      const copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.title = "Copiar";
      copyBtn.setAttribute("aria-label", "Copiar");
      copyBtn.dataset.configurableAction = "copy";
      copyBtn.dataset.configurableItemId = itemId;
      copyBtn.dataset.configurableManagerId = managerId;
      copyBtn.textContent = "Copiar";
      container.appendChild(copyBtn);
    }

    if (manager.config.actions.remove) {
      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.title = "Eliminar";
      delBtn.setAttribute("aria-label", "Eliminar");
      delBtn.dataset.configurableAction = "remove";
      delBtn.dataset.configurableItemId = itemId;
      delBtn.dataset.configurableManagerId = managerId;
      delBtn.textContent = "Eliminar";
      container.appendChild(delBtn);
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
      const th = createElement_v1("th", column.className, column.label || column.key);
      row.appendChild(th);
    });

    const actionsTh = createElement_v1("th", "configurable-items-actions-col-v1 admin-col-actions-v1", "Ações");
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

    // Antes de recriar as linhas, devolve o formulario inline ao seu sitio (nao o perde com a tabela).
    restoreInlineFormV1(manager);

    const filteredItems = getVisibleItems_v1(manager);
    const totalAllItems = manager.state.items.length;
    const totalItems = filteredItems.length;
    const visibleItems = filteredItems.slice(0, manager.state.visibleCount);

    tableBody.innerHTML = "";

    visibleItems.forEach((item, visibleIndex) => {
      const absoluteIndex = visibleIndex;
      const itemId = item.__managerId;
      const fullItemIndex = manager.state.items.findIndex((it) => it.__managerId === itemId);
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

      if (manager.config.inlineEditor) {
        row.style.cursor = "pointer";
        row.addEventListener("click", (event) => {
          if (event.target.closest("button, a, input, select, textarea, label")) return;
          editItem_v1(manager, itemId);
        });
      }

      const actionsTd = document.createElement("td");
      actionsTd.className = "configurable-items-actions-cell-v1 admin-col-actions-v1";
      actionsTd.appendChild(createRawActionsContainer_v1(manager, itemId, fullItemIndex, totalAllItems));
      row.appendChild(actionsTd);
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

  // Edicao inline (config.inlineEditor): o formulario abre logo abaixo da linha do item.
  function saveFormOriginV1(manager, formCard) {
    if (!manager._formOriginV1) {
      manager._formOriginV1 = { parent: formCard.parentNode, next: formCard.nextSibling };
    }
  }

  function restoreInlineFormV1(manager) {
    const formCard = manager.elements && manager.elements.formCard;
    const origin = manager._formOriginV1;

    if (formCard && origin && origin.parent) {
      const anchor = origin.next && origin.next.parentNode === origin.parent ? origin.next : null;
      origin.parent.insertBefore(formCard, anchor);
    }

    if (manager._inlineRowV1 && manager._inlineRowV1.parentNode) {
      manager._inlineRowV1.parentNode.removeChild(manager._inlineRowV1);
    }
    manager._inlineRowV1 = null;
  }

  function mountInlineFormV1(manager, itemId, formCard) {
    restoreInlineFormV1(manager);
    saveFormOriginV1(manager, formCard);

    const body = manager.elements.tableBody;
    if (!body) return;

    const rowEl = Array.prototype.find.call(body.querySelectorAll("tr"), (row) => {
      return String(row.dataset.configurableItemId) === String(itemId);
    });
    if (!rowEl) return;

    const inlineRow = document.createElement("tr");
    inlineRow.className = "configurable-items-inline-editor-row-v1";
    const cell = document.createElement("td");
    cell.colSpan = rowEl.children.length;
    cell.appendChild(formCard);
    inlineRow.appendChild(cell);
    rowEl.parentNode.insertBefore(inlineRow, rowEl.nextSibling);
    manager._inlineRowV1 = inlineRow;
  }

  function openFormCard_v1(manager, title) {
    const formCard = manager.elements.formCard;

    if (formCard) {
      if (manager.config.inlineEditor && manager.state.editingId) {
        mountInlineFormV1(manager, manager.state.editingId, formCard);
      } else {
        restoreInlineFormV1(manager);
      }

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
    restoreInlineFormV1(manager);

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

  // Copiar: abre o formulario de criacao ja preenchido com os dados da regra (sem chave, para criar nova).
  function copyItem_v1(manager, itemId) {
    const itemIndex = findItemIndexById_v1(manager, itemId);

    if (itemIndex < 0) {
      return;
    }

    const copied = { ...manager.state.items[itemIndex], key: "" };
    manager.state.editingId = "";
    manager.root.classList.remove("configurable-items-editing-v1");
    openCreateItem_v1(manager);

    if (typeof manager.config.loadEditorItem === "function") {
      manager.config.loadEditorItem(copied, {
        manager,
        root: manager.root,
        elements: manager.elements,
        index: itemIndex
      });
    }
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

    persistManagerChange_v1(manager);
  }

  // persistOnChange: eliminar/mover grava logo (sincroniza campos ocultos e submete o formulario).
  function persistManagerChange_v1(manager) {
    if (!manager.config.persistOnChange) return;
    manager.syncHiddenInputs();
    const formEl = manager.root.tagName === "FORM" ? manager.root : manager.root.closest("form");
    if (formEl) {
      HTMLFormElement.prototype.submit.call(formEl);
    }
  }

  // Subir/Descer: escolhe o item de referencia (acima/abaixo do qual o item editado fica).
  function getItemPickerLabel_v1(manager, item) {
    if (typeof manager.config.getItemLabel === "function") {
      const custom = toSafeString_v1(manager.config.getItemLabel(item)).trim();
      if (custom) return custom;
    }
    const firstColumn = (manager.config.columns || [])[0];
    if (firstColumn && typeof firstColumn.render === "function") {
      const rendered = toSafeString_v1(firstColumn.render(item, 0, manager)).trim();
      if (rendered && rendered !== "-") return rendered;
    }
    return toSafeString_v1(item.label || item.key || item.__managerId).trim();
  }

  function openMovePicker_v1(manager, itemId, direction) {
    const itemIndex = findItemIndexById_v1(manager, itemId);
    if (itemIndex < 0) return;

    const current = manager.state.items[itemIndex];
    const others = manager.state.items.filter((row) => String(row.__managerId) !== String(itemId));
    if (!others.length) return;

    const isUp = direction === "up";
    const itemName = getItemPickerLabel_v1(manager, current);
    const dialog = document.createElement("dialog");
    dialog.className = "appgenesis-move-picker-v1";
    dialog.style.cssText = "padding:20px;border:1px solid #d6dbe6;border-radius:10px;min-width:320px;max-width:90vw;";

    const title = document.createElement("h3");
    title.textContent = (isUp ? "Subir: " : "Descer: ") + itemName;
    title.style.margin = "0 0 12px";

    const label = document.createElement("label");
    label.textContent = isUp ? "Ficar acima de:" : "Ficar abaixo de:";
    label.style.display = "block";
    label.style.marginBottom = "6px";

    const select = document.createElement("select");
    select.style.width = "100%";
    others.forEach((row) => {
      const option = document.createElement("option");
      option.value = String(row.__managerId);
      option.textContent = getItemPickerLabel_v1(manager, row);
      select.appendChild(option);
    });

    const actions = document.createElement("div");
    actions.style.cssText = "display:flex;gap:8px;justify-content:flex-end;margin-top:16px;";

    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "action-btn-cancel";
    cancelBtn.textContent = "Cancelar";
    cancelBtn.addEventListener("click", () => dialog.close());

    const confirmBtn = document.createElement("button");
    confirmBtn.type = "button";
    confirmBtn.className = "action-btn";
    confirmBtn.textContent = "Confirmar";
    confirmBtn.addEventListener("click", () => {
      moveItemRelative_v1(manager, itemId, select.value, isUp ? "before" : "after");
      dialog.close();
    });

    actions.appendChild(cancelBtn);
    actions.appendChild(confirmBtn);
    dialog.appendChild(title);
    dialog.appendChild(label);
    dialog.appendChild(select);
    dialog.appendChild(actions);
    dialog.addEventListener("close", () => dialog.remove());

    document.body.appendChild(dialog);
    dialog.showModal();
  }

  function moveItemRelative_v1(manager, itemId, targetId, position) {
    const itemIndex = findItemIndexById_v1(manager, itemId);
    if (itemIndex < 0 || String(itemId) === String(targetId)) return;

    const item = manager.state.items[itemIndex];
    manager.state.items.splice(itemIndex, 1);

    const targetIndex = findItemIndexById_v1(manager, targetId);
    if (targetIndex < 0) {
      manager.state.items.splice(itemIndex, 0, item);
      return;
    }

    manager.state.items.splice(position === "after" ? targetIndex + 1 : targetIndex, 0, item);
    manager.state.items.forEach((row, index) => {
      row.__managerOrder = index + 1;
    });

    manager.render();
    notifyChange_v1(manager);
    persistManagerChange_v1(manager);
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
    persistManagerChange_v1(manager);
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

    manager.render();
    notifyChange_v1(manager);

    manager.state.initialized = true;

    return manager;
  }

  namespace.createConfigurableItemsManager_v1 = createConfigurableItemsManager_v1;
  namespace.normalizeLookup_v1 = normalizeLookup_v1;
  namespace.showAlertDialog_v1 = showAlertDialog_v1;
  namespace.toSafeString_v1 = toSafeString_v1;
  namespace.DEFAULT_CONFIGURABLE_PAGE_SIZE_V1 = DEFAULT_CONFIGURABLE_PAGE_SIZE_V1;
  namespace.DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1 = DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1;
})(window, document);
