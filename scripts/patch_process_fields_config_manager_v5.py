from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v5.js"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not TEMPLATE_PATH.exists():
    fail(f"ficheiro nao encontrado: {TEMPLATE_PATH}")


####################################################################################
# (2) LER TEMPLATE
####################################################################################

template = TEMPLATE_PATH.read_text(encoding="utf-8")


####################################################################################
# (3) CRIAR JS V5 - GESTOR ESTAVEL
####################################################################################

js_content = r'''//###################################################################################
// APPVERBOBRAGA - PROCESS FIELDS CONFIG MANAGER V5
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNÇÕES BASE
  //###################################################################################

  function textoSeguro_v5(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizarTexto_v5(value) {
    return textoSeguro_v5(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizarChave_v5(value) {
    return normalizarTexto_v5(value);
  }

  function escaparHtml_v5(value) {
    return textoSeguro_v5(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function limparLabelCabecalho_v5(value) {
    return textoSeguro_v5(value)
      .replace(/\s*-\s*Cabeçalho\s*$/i, "")
      .replace(/\s*-\s*Cabecalho\s*$/i, "")
      .trim();
  }

  function criarOption_v5(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value || "";
    option.textContent = label || "";

    if (textoSeguro_v5(value) === textoSeguro_v5(selectedValue)) {
      option.selected = true;
    }

    return option;
  }

  function eCabecalho_v5(option) {
    if (!option || !textoSeguro_v5(option.value).trim()) {
      return false;
    }

    const tipo = normalizarTexto_v5(
      option.dataset.processConfigKind ||
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-process-config-kind") ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const texto = normalizarTexto_v5(option.textContent);
    const valor = normalizarTexto_v5(option.value);

    return tipo === "header" || texto.includes("cabecalho") || valor.includes("cabecalho");
  }

  function criarBotaoAcao_v5(action, label, itemId, disabled) {
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

  function obterElementos_v5(form) {
    return {
      legacyContainer: form.querySelector("[data-process-fields-config-legacy-container]"),
      hiddenContainer: form.querySelector("[data-process-fields-config-hidden-container]"),
      editorKey: form.querySelector("[data-process-fields-config-editor-key]"),
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

  function elementosValidos_v5(elements) {
    return Boolean(
      elements.legacyContainer &&
      elements.hiddenContainer &&
      elements.editorKey &&
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
  // (3) OPÇÕES DO SELECT ORIGINAL
  //###################################################################################

  function lerOpcoesOriginais_v5(elements) {
    const seen = new Set();

    return Array.from(elements.editorKey.options)
      .map(function (option) {
        const key = textoSeguro_v5(option.value).trim().toLowerCase();

        if (!key || seen.has(key)) {
          return null;
        }

        seen.add(key);

        return {
          key: key,
          label: limparLabelCabecalho_v5(
            textoSeguro_v5(option.dataset.processConfigLabel || option.textContent)
          ),
          kind: eCabecalho_v5(option) ? "header" : "field"
        };
      })
      .filter(Boolean);
  }

  function localizarPorChave_v5(options, key) {
    const cleanKey = normalizarChave_v5(key);

    return options.find(function (item) {
      return normalizarChave_v5(item.key) === cleanKey;
    }) || null;
  }

  function labelCampo_v5(state, key) {
    const item = localizarPorChave_v5(state.fieldOptions, key);
    return item ? item.label : key;
  }

  function labelCabecalho_v5(state, key) {
    const item = localizarPorChave_v5(state.headerOptions, key);
    return item ? item.label : "";
  }

  //###################################################################################
  // (4) RECONSTRUIR EDITOR SEM SUMIR BOTÕES
  //###################################################################################

  function garantirEstruturaEditor_v5(form, elements, state) {
    if (form.dataset.processFieldsEditorStructureV5 === "1") {
      return;
    }

    form.dataset.processFieldsEditorStructureV5 = "1";

    const editorField =
      elements.editorKey.closest(".field") ||
      elements.editorKey.closest(".form-field") ||
      elements.editorKey.parentElement;

    if (!editorField || !editorField.parentElement) {
      return;
    }

    const originalParent = editorField.parentElement;

    const oldRows = Array.from(
      form.querySelectorAll(
        ".process-fields-picker-row-v1, .process-fields-picker-row-v2, .process-fields-picker-row-v3, .process-fields-picker-row-v4, .process-fields-picker-row-v5, .process-fields-picker-row-v6, " +
        ".process-fields-config-editor-row-v2, .process-fields-config-editor-row-v3, .process-fields-config-editor-row-v4, .process-fields-config-editor-row-v5"
      )
    );

    oldRows.forEach(function (row) {
      if (row.contains(elements.editorKey)) {
        originalParent.insertBefore(editorField, row);
      }

      row.remove();
    });

    form.querySelectorAll(
      ".process-field-header-picker-v1, .process-field-header-picker-v2, .process-field-header-picker-v3, .process-field-header-picker-v4, .process-field-header-picker-v5, .process-field-header-picker-v6, " +
      ".process-fields-config-header-editor-v2, .process-fields-config-header-editor-v3, .process-fields-config-header-editor-v4, .process-fields-config-header-editor-v5"
    ).forEach(function (item) {
      item.remove();
    });

    const row = document.createElement("div");
    row.className = "process-fields-config-editor-row-v5";

    const headerWrapper = document.createElement("div");
    headerWrapper.className = "process-fields-config-header-editor-v5";

    const headerLabel = document.createElement("label");
    headerLabel.textContent = "CABEÇALHO DO CAMPO";

    const headerSelect = document.createElement("select");
    headerSelect.dataset.processFieldsConfigHeaderEditorV5 = "1";

    headerSelect.appendChild(criarOption_v5("", "Sem cabeçalho", ""));

    state.headerOptions.forEach(function (item) {
      const option = criarOption_v5(item.key, item.label, "");
      option.dataset.processConfigKind = "header";
      option.dataset.processConfigLabel = item.label;
      headerSelect.appendChild(option);
    });

    headerWrapper.appendChild(headerLabel);
    headerWrapper.appendChild(headerSelect);

    originalParent.insertBefore(row, editorField);
    row.appendChild(editorField);
    row.appendChild(headerWrapper);

    state.headerSelect = headerSelect;

    garantirLinhaBotoes_v5(form, elements, row);
  }

  function garantirLinhaBotoes_v5(form, elements, afterRow) {
    let actionRow =
      elements.submitButton.closest(".process-fields-config-actions-v5") ||
      elements.submitButton.closest(".form-action-row") ||
      elements.submitButton.closest(".profile-edit-actions") ||
      elements.submitButton.parentElement;

    if (!actionRow) {
      actionRow = document.createElement("div");
      actionRow.className = "process-fields-config-actions-v5";
      actionRow.appendChild(elements.submitButton);
      actionRow.appendChild(elements.cancelButton);
    }

    actionRow.classList.add("process-fields-config-actions-v5");

    if (afterRow && afterRow.parentElement && actionRow.parentElement !== afterRow.parentElement) {
      afterRow.parentElement.insertBefore(actionRow, afterRow.nextSibling);
    } else if (afterRow && afterRow.parentElement) {
      afterRow.parentElement.insertBefore(actionRow, afterRow.nextSibling);
    }

    elements.submitButton.style.display = "";
    elements.cancelButton.style.display = "";
    elements.submitButton.hidden = false;
    elements.cancelButton.hidden = false;
  }

  function renomearLabels_v5(form) {
    Array.from(form.querySelectorAll("label, th")).forEach(function (element) {
      const text = normalizarTexto_v5(element.textContent);

      if (text === "campo do processo") {
        element.textContent = "NOME DO CAMPO";
      }
    });
  }

  function reconstruirSelectCampos_v5(elements, state) {
    const configuredKeys = new Set(
      state.items.map(function (item) {
        return normalizarChave_v5(item.key);
      })
    );

    const currentValue = normalizarChave_v5(elements.editorKey.value);

    elements.editorKey.innerHTML = "";
    elements.editorKey.appendChild(criarOption_v5("", "Selecione", ""));

    state.fieldOptions.forEach(function (item) {
      const itemKey = normalizarChave_v5(item.key);

      if (configuredKeys.has(itemKey) && itemKey !== currentValue) {
        return;
      }

      const option = criarOption_v5(item.key, item.label, currentValue);
      option.dataset.processConfigKind = "field";
      option.dataset.processConfigLabel = item.label;
      elements.editorKey.appendChild(option);
    });
  }

  //###################################################################################
  // (5) LER CONFIGURAÇÃO ATUAL
  //###################################################################################

  function valorLinha_v5(row, selector) {
    const input = row.querySelector(selector);
    return input ? textoSeguro_v5(input.value).trim().toLowerCase() : "";
  }

  function lerItensLegacy_v5(elements, state) {
    const rows = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-config-field-row]")
    );

    const items = [];
    let currentHeaderKey = "";

    rows.forEach(function (row, index) {
      const key = valorLinha_v5(row, "[data-process-config-key]");
      const kind = valorLinha_v5(row, "[data-process-config-kind]");

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
        label: labelCampo_v5(state, key),
        headerKey: currentHeaderKey,
        headerLabel: labelCabecalho_v5(state, currentHeaderKey)
      });
    });

    return items;
  }

  function lerItensHidden_v5(elements, state) {
    const fieldInputs = Array.from(
      elements.hiddenContainer.querySelectorAll('input[name="visible_fields"]')
    );
    const headerInputs = Array.from(
      elements.hiddenContainer.querySelectorAll('input[name="visible_headers"]')
    );

    return fieldInputs
      .map(function (input, index) {
        const key = textoSeguro_v5(input.value).trim().toLowerCase();

        if (!key) {
          return null;
        }

        const headerKey = textoSeguro_v5(headerInputs[index] ? headerInputs[index].value : "")
          .trim()
          .toLowerCase();

        return {
          managerId: "hidden_" + index + "_" + key,
          key: key,
          label: labelCampo_v5(state, key),
          headerKey: headerKey,
          headerLabel: labelCabecalho_v5(state, headerKey)
        };
      })
      .filter(Boolean);
  }

  function juntarItens_v5(first, second) {
    const merged = [];
    const seen = new Set();

    first.concat(second).forEach(function (item) {
      const key = normalizarChave_v5(item.key);

      if (!key || seen.has(key)) {
        return;
      }

      seen.add(key);
      merged.push(item);
    });

    return merged;
  }

  //###################################################################################
  // (6) ADICIONAR / EDITAR
  //###################################################################################

  function limparEditor_v5(elements, state) {
    state.editingId = "";
    elements.editorKey.value = "";

    if (state.headerSelect) {
      state.headerSelect.value = "";
    }

    reconstruirSelectCampos_v5(elements, state);
  }

  function lerDraft_v5(elements, state) {
    const selectedOption = elements.editorKey.options[elements.editorKey.selectedIndex];

    if (!selectedOption || !selectedOption.value) {
      return null;
    }

    const key = textoSeguro_v5(selectedOption.value).trim().toLowerCase();
    const headerKey = textoSeguro_v5(state.headerSelect ? state.headerSelect.value : "")
      .trim()
      .toLowerCase();

    return {
      managerId: state.editingId || "item_" + Date.now() + "_" + key,
      key: key,
      label: textoSeguro_v5(selectedOption.dataset.processConfigLabel || selectedOption.textContent),
      headerKey: headerKey,
      headerLabel: labelCabecalho_v5(state, headerKey)
    };
  }

  function validarDraft_v5(state, item) {
    if (!item || !item.key) {
      window.alert("Selecione um campo.");
      return false;
    }

    const duplicate = state.items.some(function (existing) {
      return existing.managerId !== item.managerId &&
        normalizarChave_v5(existing.key) === normalizarChave_v5(item.key);
    });

    if (duplicate) {
      window.alert("Este campo já está configurado.");
      return false;
    }

    return true;
  }

  function adicionarOuAtualizar_v5(elements, state) {
    const item = lerDraft_v5(elements, state);

    if (!validarDraft_v5(state, item)) {
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

    limparEditor_v5(elements, state);
    return true;
  }

  function existeDraft_v5(elements, state) {
    return Boolean(state.editingId || elements.editorKey.value);
  }

  function carregarEditor_v5(elements, state, item) {
    state.editingId = item.managerId;
    reconstruirSelectCampos_v5(elements, state);

    elements.editorKey.value = item.key || "";

    if (state.headerSelect) {
      state.headerSelect.value = item.headerKey || "";
    }

    elements.editorKey.focus();
  }

  //###################################################################################
  // (7) HIDDEN INPUTS
  //###################################################################################

  function sincronizarHiddenInputs_v5(elements, state) {
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

  function submitNativo_v5(form) {
    HTMLFormElement.prototype.submit.call(form);
  }

  //###################################################################################
  // (8) TABELA
  //###################################################################################

  function reescreverCabecalhoTabela_v5(elements) {
    const headRow = elements.table.querySelector("thead tr");

    if (!headRow || headRow.dataset.processFieldsConfigHeaderV5 === "1") {
      return;
    }

    headRow.innerHTML = [
      "<th>NOME DO CAMPO</th>",
      "<th>CABEÇALHO DO CAMPO</th>",
      "<th>AÇÕES</th>"
    ].join("");

    headRow.dataset.processFieldsConfigHeaderV5 = "1";
  }

  function renderizarPaginacao_v5(elements, state, totalPages) {
    elements.pagination.innerHTML = "";

    const previousButton = document.createElement("button");
    previousButton.type = "button";
    previousButton.className = "table-limiter-nav-btn";
    previousButton.innerHTML = "&#8249;";
    previousButton.disabled = state.page <= 1;
    previousButton.addEventListener("click", function () {
      if (state.page > 1) {
        state.page -= 1;
        renderizarTabela_v5(elements, state);
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
        renderizarTabela_v5(elements, state);
      }
    });

    elements.pagination.appendChild(previousButton);
    elements.pagination.appendChild(pageLabel);
    elements.pagination.appendChild(nextButton);
  }

  function renderizarTabela_v5(elements, state) {
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
        "<td>" + escaparHtml_v5(item.label || item.key) + "</td>",
        "<td>" + escaparHtml_v5(item.headerLabel || "Sem cabeçalho") + "</td>"
      ].join("");

      const actionsTd = document.createElement("td");
      const actionsWrap = document.createElement("div");

      actionsTd.className = "configurable-items-actions-cell-v1";
      actionsWrap.className = "configurable-items-actions-v1";

      actionsWrap.appendChild(criarBotaoAcao_v5("edit", "Editar", item.managerId, false));
      actionsWrap.appendChild(criarBotaoAcao_v5("up", "Subir", item.managerId, absoluteIndex === 0));
      actionsWrap.appendChild(criarBotaoAcao_v5("down", "Descer", item.managerId, absoluteIndex === totalItems - 1));
      actionsWrap.appendChild(criarBotaoAcao_v5("remove", "Remover", item.managerId, false));

      actionsTd.appendChild(actionsWrap);
      row.appendChild(actionsTd);
      elements.tableBody.appendChild(row);
    });

    elements.table.style.display = totalItems ? "" : "none";
    elements.emptyState.style.display = totalItems ? "none" : "";
    elements.totalLabel.textContent = totalItems + " " + (totalItems === 1 ? "campo" : "campos");

    renderizarPaginacao_v5(elements, state, totalPages);
    sincronizarHiddenInputs_v5(elements, state);
    reconstruirSelectCampos_v5(elements, state);
  }

  //###################################################################################
  // (9) EVENTOS
  //###################################################################################

  function encontrarIndice_v5(state, itemId) {
    return state.items.findIndex(function (item) {
      return item.managerId === itemId;
    });
  }

  function moverItem_v5(state, fromIndex, toIndex) {
    if (fromIndex < 0 || toIndex < 0 || fromIndex >= state.items.length || toIndex >= state.items.length) {
      return;
    }

    const item = state.items.splice(fromIndex, 1)[0];
    state.items.splice(toIndex, 0, item);
  }

  function vincularEventos_v5(form, elements, state) {
    elements.submitButton.addEventListener("click", function (event) {
      event.preventDefault();

      if (existeDraft_v5(elements, state)) {
        const ok = adicionarOuAtualizar_v5(elements, state);

        if (!ok) {
          return;
        }
      }

      renderizarTabela_v5(elements, state);
      sincronizarHiddenInputs_v5(elements, state);
      submitNativo_v5(form);
    });

    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      limparEditor_v5(elements, state);
    });

    elements.pageSize.addEventListener("change", function () {
      state.pageSize = Number.parseInt(elements.pageSize.value, 10) || 5;
      state.page = 1;
      renderizarTabela_v5(elements, state);
    });

    elements.tableBody.addEventListener("click", function (event) {
      const button = event.target.closest("[data-process-fields-config-action]");

      if (!button) {
        return;
      }

      const action = button.dataset.processFieldsConfigAction;
      const itemId = button.dataset.processFieldsConfigItemId;
      const index = encontrarIndice_v5(state, itemId);

      if (index < 0) {
        return;
      }

      if (action === "edit") {
        carregarEditor_v5(elements, state, state.items[index]);
        return;
      }

      if (action === "up") {
        moverItem_v5(state, index, index - 1);
      }

      if (action === "down") {
        moverItem_v5(state, index, index + 1);
      }

      if (action === "remove") {
        state.items.splice(index, 1);
      }

      renderizarTabela_v5(elements, state);
    });

    form.addEventListener("submit", function () {
      sincronizarHiddenInputs_v5(elements, state);
    });
  }

  //###################################################################################
  // (10) ESTILO
  //###################################################################################

  function injetarEstilo_v5() {
    if (document.getElementById("process-fields-config-manager-v5-style")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "process-fields-config-manager-v5-style";
    style.textContent = `
      .process-fields-config-editor-row-v5 {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
        gap: 12px !important;
        align-items: end !important;
        width: 100% !important;
      }

      .process-fields-config-editor-row-v5 > * {
        min-width: 0 !important;
        width: 100% !important;
      }

      .process-fields-config-editor-row-v5 .field,
      .process-fields-config-header-editor-v5 {
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
        width: 100% !important;
        min-width: 0 !important;
        margin: 0 !important;
      }

      .process-fields-config-editor-row-v5 label,
      .process-fields-config-header-editor-v5 label {
        min-height: 14px !important;
        line-height: 14px !important;
        margin: 0 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
      }

      .process-fields-config-editor-row-v5 select,
      .process-fields-config-header-editor-v5 select {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        height: 38px !important;
        min-height: 38px !important;
        box-sizing: border-box !important;
      }

      .process-fields-config-actions-v5 {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 8px !important;
        margin-top: 12px !important;
        width: 100% !important;
      }

      .process-fields-config-actions-v5 button {
        display: inline-flex !important;
        visibility: visible !important;
      }

      @media (max-width: 900px) {
        .process-fields-config-editor-row-v5 {
          grid-template-columns: 1fr !important;
        }
      }
    `;

    document.head.appendChild(style);
  }

  //###################################################################################
  // (11) INICIALIZAR
  //###################################################################################

  function iniciarGestor_v5(form) {
    if (!form || form.dataset.processFieldsConfigManagerBoundV5 === "1") {
      return;
    }

    const elements = obterElementos_v5(form);

    if (!elementosValidos_v5(elements)) {
      return;
    }

    form.dataset.processFieldsConfigManagerBoundV5 = "1";

    const originalOptions = lerOpcoesOriginais_v5(elements);

    const state = {
      fieldOptions: originalOptions.filter(function (item) { return item.kind !== "header"; }),
      headerOptions: originalOptions.filter(function (item) { return item.kind === "header"; }),
      headerSelect: null,
      items: [],
      page: 1,
      pageSize: Number.parseInt(elements.pageSize.value, 10) || 5,
      editingId: ""
    };

    injetarEstilo_v5();
    renomearLabels_v5(form);
    garantirEstruturaEditor_v5(form, elements, state);

    state.items = juntarItens_v5(
      lerItensHidden_v5(elements, state),
      lerItensLegacy_v5(elements, state)
    );

    reconstruirSelectCampos_v5(elements, state);
    reescreverCabecalhoTabela_v5(elements);
    vincularEventos_v5(form, elements, state);
    renderizarTabela_v5(elements, state);
  }

  function iniciarTodos_v5() {
    document
      .querySelectorAll("form[data-process-fields-config-manager-v1='1']")
      .forEach(iniciarGestor_v5);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarTodos_v5);
  } else {
    iniciarTodos_v5();
  }

  window.setTimeout(iniciarTodos_v5, 300);
})();
'''

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: process_fields_config_manager_v5.js criado.")


####################################################################################
# (4) ATUALIZAR TEMPLATE
####################################################################################

template = template.replace("CAMPO DO PROCESSO", "NOME DO CAMPO")
template = template.replace("Campo do processo", "Nome do campo")
template = template.replace("campo do processo", "nome do campo")

template = re.sub(
    r'\s*<link rel="stylesheet" href="/static/css/modules/process_fields_header_alignment_v1\.css\?v=[^"]+">',
    "",
    template,
)

for version in ["v1", "v2", "v3", "v4", "v5", "v6"]:
    template = re.sub(
        rf'\s*<script src="/static/js/modules/process_fields_header_manager_{version}\.js\?v=[^"]+"></script>',
        "",
        template,
    )

for version in ["v1", "v2", "v3", "v4"]:
    template = re.sub(
        rf'/static/js/modules/process_fields_config_manager_{version}\.js\?v=[^"]+',
        '/static/js/modules/process_fields_config_manager_v5.js?v=20260430-fields-config-v5',
        template,
    )

if "process_fields_config_manager_v5.js" not in template:
    script_tag = '<script src="/static/js/modules/process_fields_config_manager_v5.js?v=20260430-fields-config-v5"></script>'
    scripts_block_pattern = re.compile(
        r"(?P<start>\{% block scripts %\}[\s\S]*?)(?P<end>\n\{% endblock %\})",
        re.S,
    )

    match = scripts_block_pattern.search(template)

    if match:
        template = (
            template[:match.end("start")]
            + "\n  "
            + script_tag
            + template[match.end("start"):]
        )
    else:
        template = template.rstrip() + "\n\n{% block scripts %}\n  " + script_tag + "\n{% endblock %}\n"

TEMPLATE_PATH.write_text(template, encoding="utf-8")

print("OK: new_user.html atualizado para carregar process_fields_config_manager_v5.js.")
print("OK: patch_process_fields_config_manager_v5 concluído.")
