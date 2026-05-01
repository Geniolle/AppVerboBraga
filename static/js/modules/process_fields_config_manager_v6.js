//###################################################################################
// APPVERBOBRAGA - PROCESS FIELDS CONFIG MANAGER V6
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNÇÕES BASE
  //###################################################################################

  function textoSeguro_v6(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizarTexto_v6(value) {
    return textoSeguro_v6(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizarChave_v6(value) {
    return normalizarTexto_v6(value);
  }

  function escaparHtml_v6(value) {
    return textoSeguro_v6(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function limparLabelCabecalho_v6(value) {
    return textoSeguro_v6(value)
      .replace(/\s*-\s*Cabeçalho\s*$/i, "")
      .replace(/\s*-\s*Cabecalho\s*$/i, "")
      .trim();
  }

  function eCabecalho_v6(option) {
    if (!option || !textoSeguro_v6(option.value).trim()) {
      return false;
    }

    const kind = normalizarTexto_v6(
      option.dataset.processConfigKind ||
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-process-config-kind") ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const texto = normalizarTexto_v6(option.textContent);
    const value = normalizarTexto_v6(option.value);

    return kind === "header" || texto.includes("cabecalho") || value.includes("cabecalho");
  }

  function criarOption_v6(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value || "";
    option.textContent = label || "";

    if (textoSeguro_v6(value) === textoSeguro_v6(selectedValue)) {
      option.selected = true;
    }

    return option;
  }

  function criarBotaoAcao_v6(action, label, itemId, disabled) {
    const button = document.createElement("button");
    const icons = {
      edit: "&#9998;",
      up: "&#8593;",
      down: "&#8595;",
      remove: "&#128465;"
    };

    button.type = "button";
    button.className = "configurable-items-action-btn-v1";
    button.dataset.processFieldsConfigAction = action;
    button.dataset.processFieldsConfigItemId = itemId;
    button.title = label;
    button.setAttribute("aria-label", label);
    button.innerHTML = icons[action] || label;

    if (disabled) {
      button.disabled = true;
    }

    return button;
  }

  //###################################################################################
  // (2) ELEMENTOS
  //###################################################################################

  function obterElementos_v6(form) {
    return {
      legacyContainer: form.querySelector("[data-process-fields-config-legacy-container]"),
      hiddenContainer: form.querySelector("[data-process-fields-config-hidden-container]"),
      editorKey: form.querySelector("[data-process-fields-config-editor-key]"),
      headerKey: form.querySelector("[data-process-fields-config-header-editor-key]"),
      submitButton: form.querySelector("[data-process-fields-config-submit]"),
      cancelButton: form.querySelector("[data-process-fields-config-cancel]"),
      table: form.querySelector("[data-process-fields-config-table]"),
      tableBody: form.querySelector("[data-process-fields-config-table-body]"),
      emptyState: form.querySelector("[data-process-fields-config-empty]"),
      totalLabel: form.querySelector("[data-process-fields-config-total-label]"),
      pageSize: form.querySelector("[data-process-fields-config-page-size]"),
      pagination: form.querySelector("[data-process-fields-config-pagination]")
    };
  }

  function elementosValidos_v6(elements) {
    return Boolean(
      elements.legacyContainer &&
      elements.hiddenContainer &&
      elements.editorKey &&
      elements.headerKey &&
      elements.submitButton &&
      elements.cancelButton &&
      elements.table &&
      elements.tableBody &&
      elements.emptyState &&
      elements.totalLabel &&
      elements.pageSize &&
      elements.pagination
    );
  }


  //###################################################################################
  // (2A) LIMPAR CABEÇALHOS DUPLICADOS DE PATCHES ANTIGOS
  //###################################################################################

  function removerCabecalhosDuplicados_v6(form, elements) {
    const officialHeader = elements.headerKey;

    if (!officialHeader) {
      return;
    }

    const officialWrapper =
      officialHeader.closest(".process-fields-config-header-field-v6") ||
      officialHeader.closest(".field") ||
      officialHeader.parentElement;

    const duplicateSelectors = [
      "[data-process-fields-config-header-editor-v2]",
      "[data-process-fields-config-header-editor-v3]",
      "[data-process-fields-config-header-editor-v4]",
      "[data-process-fields-config-header-editor-v5]",
      "[data-process-field-header-picker]",
      "[data-configured-field-header-picker]",
      "[data-main-header-picker-v2]",
      "[data-main-header-picker-v3]",
      "[data-main-header-select-v4]",
      "[data-main-header-select-v5]",
      "[data-main-header-select-v6]",
      ".process-fields-config-header-editor-v2",
      ".process-fields-config-header-editor-v3",
      ".process-fields-config-header-editor-v4",
      ".process-fields-config-header-editor-v5",
      ".process-field-header-picker-v1",
      ".process-field-header-picker-v2",
      ".process-field-header-picker-v3",
      ".process-field-header-picker-v4",
      ".process-field-header-picker-v5",
      ".process-field-header-picker-v6"
    ];

    duplicateSelectors.forEach(function (selector) {
      form.querySelectorAll(selector).forEach(function (element) {
        const wrapper =
          element.closest(".process-fields-config-header-editor-v2") ||
          element.closest(".process-fields-config-header-editor-v3") ||
          element.closest(".process-fields-config-header-editor-v4") ||
          element.closest(".process-fields-config-header-editor-v5") ||
          element.closest(".process-field-header-picker-v1") ||
          element.closest(".process-field-header-picker-v2") ||
          element.closest(".process-field-header-picker-v3") ||
          element.closest(".process-field-header-picker-v4") ||
          element.closest(".process-field-header-picker-v5") ||
          element.closest(".process-field-header-picker-v6") ||
          element.closest(".field") ||
          element;

        if (wrapper && wrapper !== officialWrapper && !wrapper.contains(officialHeader)) {
          wrapper.remove();
        }
      });
    });

    const headerSelects = Array.from(
      form.querySelectorAll("select")
    ).filter(function (select) {
      if (select === officialHeader) {
        return false;
      }

      const label =
        select.closest(".field")?.querySelector("label") ||
        select.parentElement?.querySelector("label");

      return label && normalizarTexto_v6(label.textContent) === "cabecalho do campo";
    });

    headerSelects.forEach(function (select) {
      const wrapper =
        select.closest(".field") ||
        select.parentElement;

      if (wrapper && wrapper !== officialWrapper && !wrapper.contains(officialHeader)) {
        wrapper.remove();
      }
    });
  }

  //###################################################################################
  // (3) OPÇÕES
  //###################################################################################

  function lerOpcoesOriginais_v6(elements) {
    const seen = new Set();

    return Array.from(elements.editorKey.options)
      .map(function (option) {
        const key = textoSeguro_v6(option.value).trim().toLowerCase();

        if (!key || seen.has(key)) {
          return null;
        }

        seen.add(key);

        return {
          key: key,
          label: limparLabelCabecalho_v6(
            textoSeguro_v6(option.dataset.processConfigLabel || option.textContent)
          ),
          kind: eCabecalho_v6(option) ? "header" : "field"
        };
      })
      .filter(Boolean);
  }

  function lerHeaderOptions_v6(elements, originalOptions) {
    const fromHeaderSelect = Array.from(elements.headerKey.options)
      .map(function (option) {
        const key = textoSeguro_v6(option.value).trim().toLowerCase();

        if (!key) {
          return null;
        }

        return {
          key: key,
          label: limparLabelCabecalho_v6(
            textoSeguro_v6(option.dataset.processConfigLabel || option.textContent)
          ),
          kind: "header"
        };
      })
      .filter(Boolean);

    if (fromHeaderSelect.length) {
      return fromHeaderSelect;
    }

    return originalOptions.filter(function (item) {
      return item.kind === "header";
    });
  }

  function localizarPorChave_v6(options, key) {
    const cleanKey = normalizarChave_v6(key);

    return options.find(function (item) {
      return normalizarChave_v6(item.key) === cleanKey;
    }) || null;
  }

  function labelCampo_v6(state, key) {
    const item = localizarPorChave_v6(state.fieldOptions, key);
    return item ? item.label : key;
  }

  function labelCabecalho_v6(state, key) {
    const item = localizarPorChave_v6(state.headerOptions, key);
    return item ? item.label : "";
  }

  function reconstruirSelectCampo_v6(elements, state) {
    const configuredKeys = new Set(
      state.items.map(function (item) {
        return normalizarChave_v6(item.key);
      })
    );

    const currentValue = normalizarChave_v6(elements.editorKey.value);

    elements.editorKey.innerHTML = "";
    elements.editorKey.appendChild(criarOption_v6("", "Selecione", ""));

    state.fieldOptions.forEach(function (item) {
      const itemKey = normalizarChave_v6(item.key);

      if (configuredKeys.has(itemKey) && itemKey !== currentValue) {
        return;
      }

      const option = criarOption_v6(item.key, item.label, currentValue);
      option.dataset.processConfigKind = "field";
      option.dataset.processConfigLabel = item.label;
      elements.editorKey.appendChild(option);
    });
  }

  function reconstruirSelectCabecalho_v6(elements, state) {
    const currentValue = normalizarChave_v6(elements.headerKey.value);

    elements.headerKey.innerHTML = "";
    elements.headerKey.appendChild(criarOption_v6("", "Sem cabeçalho", currentValue));

    state.headerOptions.forEach(function (item) {
      const option = criarOption_v6(item.key, item.label, currentValue);
      option.dataset.processConfigKind = "header";
      option.dataset.processConfigLabel = item.label;
      elements.headerKey.appendChild(option);
    });
  }

  //###################################################################################
  // (4) LER ITENS EXISTENTES
  //###################################################################################

  function valorLinha_v6(row, selector) {
    const input = row.querySelector(selector);
    return input ? textoSeguro_v6(input.value).trim().toLowerCase() : "";
  }

  function lerItensLegacy_v6(elements, state) {
    const rows = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-config-field-row]")
    );

    const items = [];
    let currentHeaderKey = "";

    rows.forEach(function (row, index) {
      const key = valorLinha_v6(row, "[data-process-config-key]");
      const kind = valorLinha_v6(row, "[data-process-config-kind]");

      if (!key) {
        return;
      }

      if (kind === "header") {
        currentHeaderKey = key;
        return;
      }

      items.push({
        managerId: "legacy_" + index + "_" + key,
        key: key,
        label: labelCampo_v6(state, key),
        headerKey: currentHeaderKey,
        headerLabel: labelCabecalho_v6(state, currentHeaderKey)
      });
    });

    return items;
  }

  function lerItensHidden_v6(elements, state) {
    const fieldInputs = Array.from(
      elements.hiddenContainer.querySelectorAll('input[name="visible_fields"]')
    );
    const headerInputs = Array.from(
      elements.hiddenContainer.querySelectorAll('input[name="visible_headers"]')
    );

    return fieldInputs
      .map(function (input, index) {
        const key = textoSeguro_v6(input.value).trim().toLowerCase();

        if (!key) {
          return null;
        }

        const headerKey = textoSeguro_v6(headerInputs[index] ? headerInputs[index].value : "")
          .trim()
          .toLowerCase();

        return {
          managerId: "hidden_" + index + "_" + key,
          key: key,
          label: labelCampo_v6(state, key),
          headerKey: headerKey,
          headerLabel: labelCabecalho_v6(state, headerKey)
        };
      })
      .filter(Boolean);
  }

  function juntarItens_v6(first, second) {
    const merged = [];
    const seen = new Set();

    first.concat(second).forEach(function (item) {
      const key = normalizarChave_v6(item.key);

      if (!key || seen.has(key)) {
        return;
      }

      seen.add(key);
      merged.push(item);
    });

    return merged;
  }

  //###################################################################################
  // (5) EDITOR
  //###################################################################################

  function limparEditor_v6(elements, state) {
    state.editingId = "";
    elements.editorKey.value = "";
    elements.headerKey.value = "";
    reconstruirSelectCampo_v6(elements, state);
  }

  function lerDraft_v6(elements, state) {
    const selectedOption = elements.editorKey.options[elements.editorKey.selectedIndex];

    if (!selectedOption || !selectedOption.value) {
      return null;
    }

    const key = textoSeguro_v6(selectedOption.value).trim().toLowerCase();
    const headerKey = textoSeguro_v6(elements.headerKey.value).trim().toLowerCase();

    return {
      managerId: state.editingId || "item_" + Date.now() + "_" + key,
      key: key,
      label: textoSeguro_v6(selectedOption.dataset.processConfigLabel || selectedOption.textContent),
      headerKey: headerKey,
      headerLabel: labelCabecalho_v6(state, headerKey)
    };
  }

  function validarDraft_v6(state, item) {
    if (!item || !item.key) {
      window.alert("Selecione um campo.");
      return false;
    }

    const duplicate = state.items.some(function (existing) {
      return existing.managerId !== item.managerId &&
        normalizarChave_v6(existing.key) === normalizarChave_v6(item.key);
    });

    if (duplicate) {
      window.alert("Este campo já está configurado.");
      return false;
    }

    return true;
  }

  function adicionarOuAtualizar_v6(elements, state) {
    const item = lerDraft_v6(elements, state);

    if (!validarDraft_v6(state, item)) {
      return false;
    }

    const index = state.items.findIndex(function (existing) {
      return existing.managerId === item.managerId;
    });

    if (index >= 0) {
      state.items[index] = item;
    } else {
      state.items.push(item);
      state.page = Math.max(1, Math.ceil(state.items.length / state.pageSize));
    }

    limparEditor_v6(elements, state);
    return true;
  }

  function existeDraft_v6(elements, state) {
    return Boolean(state.editingId || elements.editorKey.value);
  }

  function carregarEditor_v6(elements, state, item) {
    state.editingId = item.managerId;
    reconstruirSelectCampo_v6(elements, state);

    elements.editorKey.value = item.key || "";
    elements.headerKey.value = item.headerKey || "";
    elements.editorKey.focus();
  }

  //###################################################################################
  // (6) HIDDEN INPUTS
  //###################################################################################

  function sincronizarHiddenInputs_v6(elements, state) {
    elements.hiddenContainer.innerHTML = "";

    state.items.forEach(function (item) {
      const fieldInput = document.createElement("input");
      fieldInput.type = "hidden";
      fieldInput.name = "visible_fields";
      fieldInput.value = item.key || "";
      elements.hiddenContainer.appendChild(fieldInput);

      const headerInput = document.createElement("input");
      headerInput.type = "hidden";
      headerInput.name = "visible_headers";
      headerInput.value = item.headerKey || "";
      elements.hiddenContainer.appendChild(headerInput);
    });
  }

  function submitNativo_v6(form) {
    HTMLFormElement.prototype.submit.call(form);
  }

  //###################################################################################
  // (7) TABELA
  //###################################################################################

  function reescreverCabecalhoTabela_v6(elements) {
    const headRow = elements.table.querySelector("thead tr");

    if (!headRow || headRow.dataset.processFieldsConfigHeaderV6 === "1") {
      return;
    }

    headRow.innerHTML = [
      "<th>NOME DO CAMPO</th>",
      "<th>CABEÇALHO DO CAMPO</th>",
      "<th>AÇÕES</th>"
    ].join("");

    headRow.dataset.processFieldsConfigHeaderV6 = "1";
  }

  function renderizarPaginacao_v6(elements, state, totalPages) {
    elements.pagination.innerHTML = "";

    const previousButton = document.createElement("button");
    previousButton.type = "button";
    previousButton.className = "table-limiter-nav-btn";
    previousButton.innerHTML = "&#8249;";
    previousButton.disabled = state.page <= 1;
    previousButton.addEventListener("click", function () {
      if (state.page > 1) {
        state.page -= 1;
        renderizarTabela_v6(elements, state);
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
        renderizarTabela_v6(elements, state);
      }
    });

    elements.pagination.appendChild(previousButton);
    elements.pagination.appendChild(pageLabel);
    elements.pagination.appendChild(nextButton);
  }

  function renderizarTabela_v6(elements, state) {
    const totalItems = state.items.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / state.pageSize));

    if (state.page > totalPages) {
      state.page = totalPages;
    }

    const start = (state.page - 1) * state.pageSize;
    const visibleItems = state.items.slice(start, start + state.pageSize);

    elements.tableBody.innerHTML = "";

    visibleItems.forEach(function (item, visibleIndex) {
      const absoluteIndex = start + visibleIndex;
      const row = document.createElement("tr");

      row.dataset.processFieldsConfigItemId = item.managerId;
      row.innerHTML = [
        "<td>" + escaparHtml_v6(item.label || item.key) + "</td>",
        "<td>" + escaparHtml_v6(item.headerLabel || "Sem cabeçalho") + "</td>"
      ].join("");

      const actionsTd = document.createElement("td");
      const actionsWrap = document.createElement("div");

      actionsTd.className = "configurable-items-actions-cell-v1";
      actionsWrap.className = "configurable-items-actions-v1";

      actionsWrap.appendChild(criarBotaoAcao_v6("edit", "Editar", item.managerId, false));
      actionsWrap.appendChild(criarBotaoAcao_v6("up", "Subir", item.managerId, absoluteIndex === 0));
      actionsWrap.appendChild(criarBotaoAcao_v6("down", "Descer", item.managerId, absoluteIndex === totalItems - 1));
      actionsWrap.appendChild(criarBotaoAcao_v6("remove", "Remover", item.managerId, false));

      actionsTd.appendChild(actionsWrap);
      row.appendChild(actionsTd);
      elements.tableBody.appendChild(row);
    });

    elements.table.style.display = totalItems ? "" : "none";
    elements.emptyState.style.display = totalItems ? "none" : "";
    elements.totalLabel.textContent = totalItems + " " + (totalItems === 1 ? "campo" : "campos");

    renderizarPaginacao_v6(elements, state, totalPages);
    sincronizarHiddenInputs_v6(elements, state);
    reconstruirSelectCampo_v6(elements, state);
  }

  //###################################################################################
  // (8) EVENTOS
  //###################################################################################

  function encontrarIndice_v6(state, itemId) {
    return state.items.findIndex(function (item) {
      return item.managerId === itemId;
    });
  }

  function moverItem_v6(state, fromIndex, toIndex) {
    if (fromIndex < 0 || toIndex < 0 || fromIndex >= state.items.length || toIndex >= state.items.length) {
      return;
    }

    const item = state.items.splice(fromIndex, 1)[0];
    state.items.splice(toIndex, 0, item);
  }

  function vincularEventos_v6(form, elements, state) {
    elements.submitButton.addEventListener("click", function (event) {
      event.preventDefault();

      if (existeDraft_v6(elements, state)) {
        const ok = adicionarOuAtualizar_v6(elements, state);

        if (!ok) {
          return;
        }
      }

      renderizarTabela_v6(elements, state);
      sincronizarHiddenInputs_v6(elements, state);
      submitNativo_v6(form);
    });

    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      limparEditor_v6(elements, state);
    });

    elements.pageSize.addEventListener("change", function () {
      state.pageSize = Number.parseInt(elements.pageSize.value, 10) || 5;
      state.page = 1;
      renderizarTabela_v6(elements, state);
    });

    elements.tableBody.addEventListener("click", function (event) {
      const button = event.target.closest("[data-process-fields-config-action]");

      if (!button) {
        return;
      }

      const action = button.dataset.processFieldsConfigAction;
      const itemId = button.dataset.processFieldsConfigItemId;
      const index = encontrarIndice_v6(state, itemId);

      if (index < 0) {
        return;
      }

      if (action === "edit") {
        carregarEditor_v6(elements, state, state.items[index]);
        return;
      }

      if (action === "up") {
        moverItem_v6(state, index, index - 1);
      }

      if (action === "down") {
        moverItem_v6(state, index, index + 1);
      }

      if (action === "remove") {
        state.items.splice(index, 1);
      }

      renderizarTabela_v6(elements, state);
    });

    form.addEventListener("submit", function () {
      sincronizarHiddenInputs_v6(elements, state);
    });
  }

  //###################################################################################
  // (9) INICIALIZAR
  //###################################################################################

  function iniciarGestor_v6(form) {
    if (!form || form.dataset.processFieldsConfigManagerBoundV6 === "1") {
      return;
    }

    const elements = obterElementos_v6(form);

    if (!elementosValidos_v6(elements)) {
      return;
    }

    form.dataset.processFieldsConfigManagerBoundV6 = "1";

    removerCabecalhosDuplicados_v6(form, elements);

    const originalOptions = lerOpcoesOriginais_v6(elements);
    const state = {
      fieldOptions: originalOptions.filter(function (item) { return item.kind !== "header"; }),
      headerOptions: lerHeaderOptions_v6(elements, originalOptions),
      items: [],
      page: 1,
      pageSize: Number.parseInt(elements.pageSize.value, 10) || 5,
      editingId: ""
    };

    state.items = juntarItens_v6(
      lerItensHidden_v6(elements, state),
      lerItensLegacy_v6(elements, state)
    );

    reconstruirSelectCabecalho_v6(elements, state);
    reconstruirSelectCampo_v6(elements, state);
    reescreverCabecalhoTabela_v6(elements);
    vincularEventos_v6(form, elements, state);
    renderizarTabela_v6(elements, state);
  }

  function iniciarTodos_v6() {
    document
      .querySelectorAll("form[data-process-fields-config-manager-v1='1']")
      .forEach(iniciarGestor_v6);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarTodos_v6);
  } else {
    iniciarTodos_v6();
  }
})();
