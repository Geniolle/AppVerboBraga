//###################################################################################
// APPVERBOBRAGA - PROCESS LISTS MANAGER V1
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

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

  function normalizeSearchText_v1(value) {
    return toSafeString_v1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function escapeHtml_v1(value) {
    return toSafeString_v1(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function canUseSessionStorage_v1() {
    try {
      return Boolean(window && window.sessionStorage);
    } catch (error) {
      return false;
    }
  }

  function readStoredPaginationState_v1(storageKey, fallbackPageSize) {
    if (!storageKey || !canUseSessionStorage_v1()) {
      return null;
    }

    try {
      const rawValue = window.sessionStorage.getItem(storageKey);
      if (!rawValue) {
        return null;
      }

      const parsed = JSON.parse(rawValue);
      const page = Number.parseInt(parsed && parsed.page, 10);
      const pageSize = Number.parseInt(parsed && parsed.pageSize, 10);

      return {
        page: Number.isFinite(page) && page > 0 ? page : 1,
        pageSize: Number.isFinite(pageSize) && pageSize > 0 ? pageSize : fallbackPageSize
      };
    } catch (error) {
      return null;
    }
  }

  function saveStoredPaginationState_v1(storageKey, state) {
    if (!storageKey || !state || !canUseSessionStorage_v1()) {
      return;
    }

    try {
      window.sessionStorage.setItem(
        storageKey,
        JSON.stringify({
          page: Number.isFinite(state.page) && state.page > 0 ? state.page : 1,
          pageSize: Number.isFinite(state.pageSize) && state.pageSize > 0 ? state.pageSize : 5
        })
      );
    } catch (error) {
      // Ignore storage quota/private mode failures.
    }
  }

  function buildPaginationStorageKey_v1(form) {
    const menuKeyInput = form ? form.querySelector("input[name='menu_key']") : null;
    const menuKey = normalizeKey_v1(menuKeyInput ? menuKeyInput.value : "");
    return "appverbo:process-editor:lista:" + (menuKey || "default");
  }

  const PROCESS_LIST_SOURCE_MANUAL_V1 = "manual";
  const PROCESS_LIST_SOURCE_USERS_V1 = "users";
  const PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1 = "sidebar_sections";
  const PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1 = "sidebar_menus_by_section";
  const PROCESS_LIST_SOURCE_CURRENT_MENU_HEADERS_V1 = "current_menu_headers";
  const PROCESS_LIST_SOURCE_TABLE_PREFIX_V1 = "table:";
  const PROCESS_LIST_SOURCE_TABLE_KEY_ALIASES_V1 = Object.freeze(
    {
      user_profiles: "profiles"
    }
  );
  const PROCESS_LIST_SOURCE_OPTIONS_V1 = Object.freeze(
    {
      [PROCESS_LIST_SOURCE_MANUAL_V1]: "Manual",
      [PROCESS_LIST_SOURCE_USERS_V1]: "Utilizador (automatico)",
      [PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1]: "Sessoes (automatico)",
      [PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1]: "Subprocesso/Menu por sessao (automatico)",
      [PROCESS_LIST_SOURCE_CURRENT_MENU_HEADERS_V1]: "Abas/Cabecalhos do processo atual (automatico)"
    }
  );

  function normalizeTableKeyFromSource_v1(value) {
    const rawValue = toSafeString_v1(value).trim().toLowerCase();
    let cleanTableKey = "";

    if (!rawValue) {
      return "";
    }

    if (rawValue.indexOf(PROCESS_LIST_SOURCE_TABLE_PREFIX_V1) === 0) {
      const rest = rawValue.slice(PROCESS_LIST_SOURCE_TABLE_PREFIX_V1.length);
      cleanTableKey = normalizeKey_v1(rest.split(":")[0]);
    } else if (rawValue.indexOf("table_") === 0) {
      cleanTableKey = normalizeKey_v1(rawValue.slice(6));
    }

    if (!cleanTableKey) {
      return "";
    }

    return PROCESS_LIST_SOURCE_TABLE_KEY_ALIASES_V1[cleanTableKey] || cleanTableKey;
  }

  function normalizeColumnFromSource_v1(value) {
    const rawValue = toSafeString_v1(value).trim().toLowerCase();

    if (!rawValue || rawValue.indexOf(PROCESS_LIST_SOURCE_TABLE_PREFIX_V1) !== 0) {
      return "";
    }

    const rest = rawValue.slice(PROCESS_LIST_SOURCE_TABLE_PREFIX_V1.length);
    const colonIndex = rest.indexOf(":");

    if (colonIndex < 0) {
      return "";
    }

    return normalizeKey_v1(rest.slice(colonIndex + 1));
  }

  function buildTableSourceKey_v1(tableKey) {
    const cleanTableKey = normalizeKey_v1(tableKey);
    if (!cleanTableKey) {
      return "";
    }
    return PROCESS_LIST_SOURCE_TABLE_PREFIX_V1 + cleanTableKey;
  }

  function normalizeSourceKey_v1(value) {
    const rawValue = toSafeString_v1(value).trim().toLowerCase();
    const normalizedValue = normalizeKey_v1(rawValue);

    if (
      normalizedValue === "users" ||
      normalizedValue === "user" ||
      normalizedValue === "utilizador" ||
      normalizedValue === "utilizadores"
    ) {
      return PROCESS_LIST_SOURCE_USERS_V1;
    }

    if (
      normalizedValue === PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1 ||
      normalizedValue === "sessions" ||
      normalizedValue === "session" ||
      normalizedValue === "sessoes" ||
      normalizedValue === "sidebar_sections"
    ) {
      return PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1;
    }

    if (
      normalizedValue === PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1 ||
      normalizedValue === "menus_by_section" ||
      normalizedValue === "menu_by_section" ||
      normalizedValue === "menus_por_sessao" ||
      normalizedValue === "menu_por_sessao" ||
      normalizedValue === "subprocessos_por_sessao" ||
      normalizedValue === "submenu_por_sessao"
    ) {
      return PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1;
    }

    if (
      normalizedValue === PROCESS_LIST_SOURCE_CURRENT_MENU_HEADERS_V1 ||
      normalizedValue === "current_process_headers" ||
      normalizedValue === "process_headers_current_menu" ||
      normalizedValue === "cabecalhos_do_processo_atual" ||
      normalizedValue === "abas_do_processo_atual" ||
      normalizedValue === "abas_processo_atual"
    ) {
      return PROCESS_LIST_SOURCE_CURRENT_MENU_HEADERS_V1;
    }

    const tableKey = normalizeTableKeyFromSource_v1(rawValue);
    if (tableKey) {
      const columnKey = normalizeColumnFromSource_v1(rawValue);
      if (columnKey) {
        return PROCESS_LIST_SOURCE_TABLE_PREFIX_V1 + tableKey + ":" + columnKey;
      }
      return buildTableSourceKey_v1(tableKey);
    }

    return PROCESS_LIST_SOURCE_MANUAL_V1;
  }

  function formatTableLabel_v1(tableKey) {
    const cleanTableKey = normalizeTableKeyFromSource_v1(buildTableSourceKey_v1(tableKey)) || normalizeKey_v1(tableKey);

    if (cleanTableKey === "profiles") {
      return "Perfil";
    }

    return cleanTableKey
      .split("_")
      .filter(Boolean)
      .map(function (part) {
        return part.charAt(0).toUpperCase() + part.slice(1);
      })
      .join(" ");
  }

  function resolveSourceLabel_v1(sourceKey) {
    const cleanSourceKey = normalizeSourceKey_v1(sourceKey);
    const tableKey = normalizeTableKeyFromSource_v1(cleanSourceKey);
    if (tableKey) {
      const columnKey = normalizeColumnFromSource_v1(cleanSourceKey);
      const tableLabel = formatTableLabel_v1(tableKey) || tableKey;
      if (columnKey) {
        return "Tabela: " + tableLabel + " · " + columnKey + " (automático)";
      }
      return "Tabela: " + tableLabel + " (automático)";
    }
    return PROCESS_LIST_SOURCE_OPTIONS_V1[cleanSourceKey] || PROCESS_LIST_SOURCE_OPTIONS_V1[PROCESS_LIST_SOURCE_MANUAL_V1];
  }

  function isUsersSource_v1(sourceKey) {
    return normalizeSourceKey_v1(sourceKey) === PROCESS_LIST_SOURCE_USERS_V1;
  }

  function isTableSource_v1(sourceKey) {
    return Boolean(normalizeTableKeyFromSource_v1(normalizeSourceKey_v1(sourceKey)));
  }

  function isAutomaticSource_v1(sourceKey) {
    const cleanSourceKey = normalizeSourceKey_v1(sourceKey);
    return (
      cleanSourceKey === PROCESS_LIST_SOURCE_USERS_V1 ||
      cleanSourceKey === PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1 ||
      cleanSourceKey === PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1 ||
      cleanSourceKey === PROCESS_LIST_SOURCE_CURRENT_MENU_HEADERS_V1 ||
      isTableSource_v1(cleanSourceKey)
    );
  }

  function resolveSearchText_v1(item) {
    const sourceLabel = resolveSourceLabel_v1(item.sourceKey);
    const automaticSource = isAutomaticSource_v1(item.sourceKey);
    const contentLabel = automaticSource
      ? "Automatico fonte configurada"
      : (item.itemsCsv || "-");

    return [
      item.label,
      sourceLabel,
      contentLabel
    ].join(" ");
  }

  function resolveFilteredItems_v1(state) {
    const searchQuery = normalizeSearchText_v1(state.searchQuery);

    if (!searchQuery) {
      return state.items.slice();
    }

    return state.items.filter(function (item) {
      return normalizeSearchText_v1(resolveSearchText_v1(item)).includes(searchQuery);
    });
  }

  function createButton_v1(action, label, itemId, disabled) {
    const button = document.createElement("button");
    const icons = {
      edit: "&#9998;",
      up: "&#8593;",
      down: "&#8595;",
      remove: "&#128465;"
    };

    button.type = "button";
    button.className = "configurable-items-action-btn-v1";
    button.dataset.processListAction = action;
    button.dataset.processListItemId = itemId;
    button.title = label;
    button.setAttribute("aria-label", label);
    button.innerHTML = icons[action] || label;

    if (disabled) {
      button.disabled = true;
    }

    return button;
  }

  //###################################################################################
  // (2) LEITURA DO DOM
  //###################################################################################

  function getElements_v1(form) {
    return {
      legacyContainer: form.querySelector("[data-process-lists-legacy-container]"),
      hiddenContainer: form.querySelector("[data-process-lists-hidden-container]"),
      editorKey: form.querySelector("[data-process-list-editor-key]"),
      editorLabel: form.querySelector("[data-process-list-editor-label]"),
      editorItems: form.querySelector("[data-process-list-editor-items]"),
      editorSource: form.querySelector("[data-process-list-editor-source]"),
      editorTable: form.querySelector("[data-process-list-editor-table]"),
      editorColumn: form.querySelector("[data-process-list-editor-column]"),
      editorTableField: form.querySelector("[data-process-list-table-field]"),
      editorColumnField: form.querySelector("[data-process-list-column-field]"),
      submitButton: form.querySelector("[data-process-list-editor-submit]"),
      cancelButton: form.querySelector("[data-process-list-editor-cancel]"),
      table: form.querySelector("[data-process-lists-table]"),
      tableBody: form.querySelector("[data-process-lists-table-body]"),
      emptyState: form.querySelector("[data-process-lists-empty]"),
      totalLabel: form.querySelector("[data-process-lists-total-label]"),
      searchInput: form.querySelector("[data-process-lists-search]"),
      pageSize: form.querySelector("[data-process-lists-page-size]"),
      pagination: form.querySelector("[data-process-lists-pagination]")
    };
  }

  function readInput_v1(row, name) {
    const input = row.querySelector("[name='" + name + "']");
    return input ? toSafeString_v1(input.value).trim() : "";
  }

  function readInitialItems_v1(elements) {
    const rows = Array.from(elements.legacyContainer.querySelectorAll("[data-process-list-row]"));

    return rows
      .map(function (row, index) {
        const label = readInput_v1(row, "process_list_label");
        const key = readInput_v1(row, "process_list_key") || normalizeKey_v1(label) || "lista_" + (index + 1);
        const itemsCsv = readInput_v1(row, "process_list_items_csv");
        const sourceKey = normalizeSourceKey_v1(readInput_v1(row, "process_list_source"));

        return {
          managerId: "list_" + index + "_" + key,
          key: key,
          label: label,
          itemsCsv: itemsCsv,
          sourceKey: sourceKey
        };
      })
      .filter(function (item) {
        return item.label || item.itemsCsv;
      });
  }

  //###################################################################################
  // (3) SINCRONIZACAO COM BACKEND
  //###################################################################################

  function syncHiddenInputs_v1(state, elements) {
    elements.hiddenContainer.innerHTML = "";

    state.items.forEach(function (item) {
      const fields = [
        ["process_list_key", item.key],
        ["process_list_label", item.label],
        ["process_list_items_csv", item.itemsCsv],
        ["process_list_source", normalizeSourceKey_v1(item.sourceKey)]
      ];

      fields.forEach(function (field) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = field[0];
        input.value = field[1] || "";
        elements.hiddenContainer.appendChild(input);
      });
    });
  }

  //###################################################################################
  // (4) EDITOR SUPERIOR
  //###################################################################################

  function loadTableColumns_v1(tableKey, elements, selectedColumn) {
    if (!elements || !elements.editorColumn) {
      return;
    }

    const select = elements.editorColumn;
    select.innerHTML = "<option value=\"\">Carregando...</option>";

    fetch("/settings/menu/table-columns?table=" + encodeURIComponent(tableKey))
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        select.innerHTML = "<option value=\"\">Selecione o campo</option>";

        if (data.ok && Array.isArray(data.columns)) {
          data.columns.slice().sort(function (a, b) { return a.localeCompare(b); }).forEach(function (col) {
            const opt = document.createElement("option");
            opt.value = col;
            opt.textContent = col;

            if (col === selectedColumn) {
              opt.selected = true;
            }

            select.appendChild(opt);
          });
        }
      })
      .catch(function () {
        select.innerHTML = "<option value=\"\">Erro ao carregar campos</option>";
      });
  }

  function buildFullSourceKeyFromEditor_v1(elements) {
    const sourceValue = toSafeString_v1(
      elements.editorSource ? elements.editorSource.value : ""
    ).trim().toLowerCase();

    if (sourceValue === "table") {
      const tableValue = normalizeKey_v1(
        elements.editorTable ? elements.editorTable.value : ""
      );
      const columnValue = normalizeKey_v1(
        elements.editorColumn ? elements.editorColumn.value : ""
      );

      if (tableValue && columnValue) {
        return PROCESS_LIST_SOURCE_TABLE_PREFIX_V1 + tableValue + ":" + columnValue;
      }

      if (tableValue) {
        return PROCESS_LIST_SOURCE_TABLE_PREFIX_V1 + tableValue;
      }

      return PROCESS_LIST_SOURCE_MANUAL_V1;
    }

    return normalizeSourceKey_v1(sourceValue);
  }

  function syncEditorTableMode_v1(elements) {
    if (!elements) {
      return;
    }

    const sourceValue = toSafeString_v1(
      elements.editorSource ? elements.editorSource.value : ""
    ).trim().toLowerCase();
    const isTable = sourceValue === "table";

    if (elements.editorTableField) {
      elements.editorTableField.style.display = isTable ? "" : "none";
    }

    if (elements.editorColumnField) {
      elements.editorColumnField.style.display = isTable ? "" : "none";
    }
  }

  function syncEditorSourceMode_v1(elements) {
    if (!elements || !elements.editorItems) {
      return;
    }

    const rawSourceValue = toSafeString_v1(
      elements.editorSource ? elements.editorSource.value : ""
    ).trim().toLowerCase();
    const currentSourceKey = normalizeSourceKey_v1(buildFullSourceKeyFromEditor_v1(elements));
    const automaticSource = isAutomaticSource_v1(currentSourceKey) || rawSourceValue === "table";

    elements.editorItems.disabled = automaticSource;
    elements.editorItems.placeholder = automaticSource
      ? "Preenchimento automático com a fonte selecionada."
      : "Ex.: Ativo, Inativo, Pendente";

    if (automaticSource) {
      elements.editorItems.value = "";
    }

    syncEditorTableMode_v1(elements);
  }

  function clearEditor_v1(state, elements) {
    state.editingId = "";
    elements.editorKey.value = "";
    elements.editorLabel.value = "";
    elements.editorItems.value = "";

    if (elements.editorSource) {
      elements.editorSource.value = PROCESS_LIST_SOURCE_MANUAL_V1;
    }

    if (elements.editorTable) {
      elements.editorTable.value = "";
    }

    if (elements.editorColumn) {
      elements.editorColumn.innerHTML = "<option value=\"\">Selecione o campo</option>";
    }

    syncEditorSourceMode_v1(elements);
  }

  function ensureEditorSourceOption_v1(elements, sourceKey) {
    if (!elements || !elements.editorSource) {
      return;
    }

    const cleanSourceKey = normalizeSourceKey_v1(sourceKey);
    if (!cleanSourceKey) {
      return;
    }

    const hasOption = Array.from(elements.editorSource.options || []).some(function (optionEl) {
      return normalizeSourceKey_v1(optionEl.value) === cleanSourceKey;
    });

    if (hasOption) {
      return;
    }

    const optionEl = document.createElement("option");
    optionEl.value = cleanSourceKey;
    optionEl.textContent = resolveSourceLabel_v1(cleanSourceKey);
    elements.editorSource.appendChild(optionEl);
  }

  function loadEditor_v1(item, state, elements) {
    state.editingId = item.managerId;
    elements.editorKey.value = item.key || "";
    elements.editorLabel.value = item.label || "";
    elements.editorItems.value = item.itemsCsv || "";

    if (elements.editorSource) {
      const sourceKey = normalizeSourceKey_v1(item.sourceKey);
      const tableKey = normalizeTableKeyFromSource_v1(sourceKey);

      if (tableKey) {
        const columnKey = normalizeColumnFromSource_v1(sourceKey);
        elements.editorSource.value = "table";

        if (elements.editorTable) {
          elements.editorTable.value = tableKey;
        }

        if (tableKey) {
          loadTableColumns_v1(tableKey, elements, columnKey);
        }
      } else {
        ensureEditorSourceOption_v1(elements, sourceKey);
        elements.editorSource.value = sourceKey;
      }
    }

    syncEditorSourceMode_v1(elements);
    elements.editorLabel.focus();
  }

  function readEditorItem_v1(state, elements) {
    const label = toSafeString_v1(elements.editorLabel.value).trim();
    const sourceKey = normalizeSourceKey_v1(buildFullSourceKeyFromEditor_v1(elements));
    const itemsCsv = isAutomaticSource_v1(sourceKey)
      ? ""
      : toSafeString_v1(elements.editorItems.value).trim();
    const currentKey = toSafeString_v1(elements.editorKey.value).trim();
    const key = currentKey || normalizeKey_v1(label);

    return {
      managerId: state.editingId || "tmp_" + Date.now(),
      key: key,
      label: label,
      itemsCsv: itemsCsv,
      sourceKey: sourceKey
    };
  }

  function validateItem_v1(item, state) {
    if (!item.label) {
      window.alert("Informe o nome da lista.");
      return false;
    }

    const duplicate = state.items.some(function (existing) {
      return existing.managerId !== item.managerId
        && normalizeKey_v1(existing.label) === normalizeKey_v1(item.label);
    });

    if (duplicate) {
      window.alert("Ja existe uma lista com esse nome.");
      return false;
    }

    return true;
  }

  function addOrUpdateFromEditor_v1(state, elements) {
    const item = readEditorItem_v1(state, elements);

    if (!validateItem_v1(item, state)) {
      return false;
    }

    const currentIndex = state.items.findIndex(function (existing) {
      return existing.managerId === item.managerId;
    });

    if (currentIndex >= 0) {
      state.items[currentIndex] = item;
    } else {
      item.managerId = "tmp_" + Date.now() + "_" + normalizeKey_v1(item.label);
      state.items.push(item);
      state.page = Math.max(1, Math.ceil(state.items.length / state.pageSize));
    }

    clearEditor_v1(state, elements);
    return true;
  }

  function hasDraft_v1(elements, state) {
    return Boolean(
      state.editingId ||
      toSafeString_v1(elements.editorLabel.value).trim() ||
      toSafeString_v1(elements.editorItems.value).trim()
    );
  }

  //###################################################################################
  // (5) TABELA E PAGINACAO
  //###################################################################################

  function renderTable_v1(state, elements) {
    const totalAllItems = state.items.length;
    const filteredItems = resolveFilteredItems_v1(state);
    const totalItems = filteredItems.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / state.pageSize));

    if (state.page > totalPages) {
      state.page = totalPages;
    }

    const visibleCount = Math.min(totalItems, Math.max(1, state.page) * state.pageSize);
    const visibleItems = filteredItems.slice(0, visibleCount);

    elements.tableBody.innerHTML = "";

    visibleItems.forEach(function (item, visibleIndex) {
      const absoluteIndex = findItemIndex_v1(state, item.managerId);
      const row = document.createElement("tr");
      const sourceLabel = resolveSourceLabel_v1(item.sourceKey);
      const automaticSource = isAutomaticSource_v1(item.sourceKey);
      const contentLabel = automaticSource
        ? "Automático (fonte configurada)"
        : (item.itemsCsv || "-");

      row.dataset.processListItemId = item.managerId;
      row.innerHTML = [
        "<td>" + escapeHtml_v1(item.label) + "</td>",
        "<td>" + escapeHtml_v1(sourceLabel) + "</td>",
        "<td>" + escapeHtml_v1(contentLabel) + "</td>"
      ].join("");

      const actionsTd = document.createElement("td");
      const actionsWrap = document.createElement("div");

      actionsTd.className = "configurable-items-actions-cell-v1";
      actionsWrap.className = "configurable-items-actions-v1";

      actionsWrap.appendChild(createButton_v1("edit", "Editar", item.managerId, false));
      actionsWrap.appendChild(createButton_v1("up", "Subir", item.managerId, absoluteIndex === 0));
      actionsWrap.appendChild(createButton_v1("down", "Descer", item.managerId, absoluteIndex === totalAllItems - 1));
      actionsWrap.appendChild(createButton_v1("remove", "Remover", item.managerId, false));

      actionsTd.appendChild(actionsWrap);
      row.appendChild(actionsTd);
      elements.tableBody.appendChild(row);
    });

    elements.table.style.display = totalItems ? "" : "none";
    elements.emptyState.style.display = totalItems ? "none" : "";
    elements.emptyState.textContent = state.searchQuery && totalAllItems
      ? "Sem resultados para a procura."
      : "Sem listas criadas.";
    elements.totalLabel.textContent = totalAllItems + " " + (totalAllItems === 1 ? "lista" : "listas");

    renderPagination_v1(state, elements, totalPages, totalItems, visibleCount);
    saveStoredPaginationState_v1(state.storageKey, state);
  }

  function renderPagination_v1(state, elements, totalPages, totalItems, visibleCount) {
    elements.pagination.innerHTML = "";

    if (totalItems <= state.pageSize) {
      elements.pagination.style.display = "none";
      return;
    }

    elements.pagination.style.display = "";

    const configurableCore = window.AppVerboConfigurableItems || {};

    if (typeof configurableCore.renderFooterLoadMorePagination_v1 === "function") {
      configurableCore.renderFooterLoadMorePagination_v1({
        container: elements.pagination,
        currentPage: state.page,
        totalPages,
        totalItems,
        visibleCount,
        loadMoreLabel: "Mais",
        onPageChange: function (nextPage) {
          state.page = Math.max(1, Math.min(totalPages, nextPage));
          renderTable_v1(state, elements);
        }
      });
      return;
    }

    const previousButton = document.createElement("button");
    previousButton.type = "button";
    previousButton.className = "table-limiter-nav-btn";
    previousButton.innerHTML = "&#8249;";
    previousButton.disabled = state.page <= 1;
    previousButton.addEventListener("click", function () {
      if (state.page > 1) {
        state.page -= 1;
        renderTable_v1(state, elements);
      }
    });

    const pageLabel = document.createElement("span");
    pageLabel.className = "table-limiter-page";
    pageLabel.textContent = String(state.page);

    const nextButton = document.createElement("button");
    nextButton.type = "button";
    nextButton.className = "table-limiter-nav-btn";
    nextButton.innerHTML = "&#8250;";
    nextButton.disabled = state.page >= totalPages;
    nextButton.addEventListener("click", function () {
      if (state.page < totalPages) {
        state.page += 1;
        renderTable_v1(state, elements);
      }
    });

    elements.pagination.appendChild(previousButton);
    elements.pagination.appendChild(pageLabel);
    elements.pagination.appendChild(nextButton);
  }

  //###################################################################################
  // (6) ACOES
  //###################################################################################

  function findItemIndex_v1(state, itemId) {
    return state.items.findIndex(function (item) {
      return item.managerId === itemId;
    });
  }

  function moveItem_v1(state, fromIndex, toIndex) {
    if (fromIndex < 0 || toIndex < 0 || fromIndex >= state.items.length || toIndex >= state.items.length) {
      return;
    }

    const item = state.items.splice(fromIndex, 1)[0];
    state.items.splice(toIndex, 0, item);
  }

  function bindEvents_v1(form, state, elements) {
    elements.submitButton.addEventListener("click", function (event) {
      event.preventDefault();

      if (hasDraft_v1(elements, state)) {
        const ok = addOrUpdateFromEditor_v1(state, elements);

        if (!ok) {
          return;
        }
      }

      syncHiddenInputs_v1(state, elements);

      if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
        return;
      }

      form.submit();
    });

    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      clearEditor_v1(state, elements);
    });

    if (elements.editorSource) {
      elements.editorSource.addEventListener("change", function () {
        if (elements.editorTable) {
          elements.editorTable.value = "";
        }

        if (elements.editorColumn) {
          elements.editorColumn.innerHTML = "<option value=\"\">Selecione o campo</option>";
        }

        syncEditorSourceMode_v1(elements);
      });
    }

    if (elements.editorTable) {
      elements.editorTable.addEventListener("change", function () {
        const tableKey = normalizeKey_v1(elements.editorTable.value);

        if (elements.editorColumn) {
          elements.editorColumn.innerHTML = "<option value=\"\">Selecione o campo</option>";
        }

        if (tableKey) {
          loadTableColumns_v1(tableKey, elements, "");
        }

        syncEditorSourceMode_v1(elements);
      });
    }

    elements.pageSize.addEventListener("change", function () {
      state.pageSize = Number.parseInt(elements.pageSize.value, 10) || 5;
      state.page = 1;
      renderTable_v1(state, elements);
    });

    if (elements.searchInput) {
      elements.searchInput.addEventListener("input", function () {
        state.searchQuery = toSafeString_v1(elements.searchInput.value);
        state.page = 1;
        renderTable_v1(state, elements);
      });
    }

    elements.tableBody.addEventListener("click", function (event) {
      const button = event.target.closest("[data-process-list-action]");

      if (!button) {
        return;
      }

      const action = button.dataset.processListAction;
      const itemId = button.dataset.processListItemId;
      const index = findItemIndex_v1(state, itemId);

      if (index < 0) {
        return;
      }

      if (action === "edit") {
        loadEditor_v1(state.items[index], state, elements);
        return;
      }

      if (action === "up") {
        moveItem_v1(state, index, index - 1);
      }

      if (action === "down") {
        moveItem_v1(state, index, index + 1);
      }

      if (action === "remove") {
        state.items.splice(index, 1);
      }

      renderTable_v1(state, elements);
      syncHiddenInputs_v1(state, elements);

      if (action === "remove") {
        if (typeof form.requestSubmit === "function") {
          form.requestSubmit();
        } else {
          form.submit();
        }
        return;
      }
    });

    form.addEventListener("submit", function () {
      syncHiddenInputs_v1(state, elements);
    });
  }

  //###################################################################################
  // (7) INICIALIZACAO
  //###################################################################################

  function setupProcessListsManager_v1(form) {
    if (!form || form.dataset.processListsManagerBoundV1 === "1") {
      return;
    }

    const elements = getElements_v1(form);

    if (
      !elements.legacyContainer ||
      !elements.hiddenContainer ||
      !elements.editorKey ||
      !elements.editorLabel ||
      !elements.editorItems ||
      !elements.submitButton ||
      !elements.cancelButton ||
      !elements.table ||
      !elements.tableBody ||
      !elements.emptyState ||
      !elements.totalLabel ||
      !elements.pageSize ||
      !elements.pagination
    ) {
      return;
    }

    const state = {
      items: readInitialItems_v1(elements),
      page: 1,
      pageSize: Number.parseInt(elements.pageSize.value, 10) || 5,
      storageKey: buildPaginationStorageKey_v1(form),
      searchQuery: "",
      editingId: ""
    };

    const storedState = readStoredPaginationState_v1(state.storageKey, state.pageSize);
    if (storedState) {
      state.page = storedState.page;
      state.pageSize = storedState.pageSize;
    }

    if (elements.pageSize) {
      const hasOption = Array.from(elements.pageSize.options || []).some(function (optionEl) {
        return Number.parseInt(optionEl.value, 10) === state.pageSize;
      });
      if (hasOption) {
        elements.pageSize.value = String(state.pageSize);
      }
    }

    if (elements.editorSource && !elements.editorSource.value) {
      elements.editorSource.value = PROCESS_LIST_SOURCE_MANUAL_V1;
    }

    form.dataset.processListsManagerBoundV1 = "1";

    bindEvents_v1(form, state, elements);
    syncEditorSourceMode_v1(elements);
    syncHiddenInputs_v1(state, elements);
    renderTable_v1(state, elements);
  }

  function setupAllProcessListsManagers_v1() {
    document
      .querySelectorAll("form[data-process-lists-manager-v1='1']")
      .forEach(setupProcessListsManager_v1);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessListsManagers_v1);
  } else {
    setupAllProcessListsManagers_v1();
  }

  window.setTimeout(setupAllProcessListsManagers_v1, 150);
  window.setTimeout(setupAllProcessListsManagers_v1, 600);
})();
