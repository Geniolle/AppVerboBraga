//###################################################################################
// APPVERBOBRAGA - PROCESS FIELDS CONFIG MANAGER V7
// Usa o core generico AppVerboConfigurableItems, igual ao processo Campos adicionais.
//###################################################################################

(function (window, document) {
  "use strict";

  //###################################################################################
  // (1) CONSTANTES
  //###################################################################################

  const FORM_SELECTOR = "form[data-process-fields-config-manager-v1='1']";
  const CORE_NAMESPACE = "AppVerboConfigurableItems";

  //###################################################################################
  // (2) HELPERS GERAIS
  //###################################################################################

  function textoSeguro_v7(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizarTexto_v7(value) {
    return textoSeguro_v7(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizarChave_v7(value) {
    return normalizarTexto_v7(value);
  }

  function limparLabelCabecalho_v7(value) {
    return textoSeguro_v7(value)
      .replace(/\s*-\s*Cabeçalho\s*$/i, "")
      .replace(/\s*-\s*Cabecalho\s*$/i, "")
      .trim();
  }

  function optionEhCabecalho_v7(option) {
    if (!option || !textoSeguro_v7(option.value).trim()) {
      return false;
    }

    const kind = normalizarTexto_v7(
      option.dataset.processConfigKind ||
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-process-config-kind") ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const texto = normalizarTexto_v7(option.textContent);
    const value = normalizarTexto_v7(option.value);

    return kind === "header" || texto.includes("cabecalho") || value.includes("cabecalho");
  }

  function criarOption_v7(value, label, selectedValue, kind) {
    const option = document.createElement("option");

    option.value = value || "";
    option.textContent = label || "";

    if (kind) {
      option.dataset.processConfigKind = kind;
    }

    if (label) {
      option.dataset.processConfigLabel = label;
    }

    if (textoSeguro_v7(value) === textoSeguro_v7(selectedValue)) {
      option.selected = true;
    }

    return option;
  }

  //###################################################################################
  // (3) ELEMENTOS
  //###################################################################################

  function obterElementos_v7(form) {
    return {
      legacyContainer: form.querySelector("[data-process-fields-config-legacy-container]"),
      hiddenContainer: form.querySelector("[data-process-fields-config-hidden-container]"),
      editorBlock: (
        form.querySelector("[data-process-fields-config-editor-block]") ||
        form.querySelector(".process-fields-config-editor-v1") ||
        form
      ),
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

  function elementosMinimosValidos_v7(elements) {
    return Boolean(
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
  // (4) OPÇÕES DISPONIVEIS
  //###################################################################################

  function lerOpcoesOriginais_v7(elements) {
    const seen = new Set();

    return Array.from(elements.editorKey.options)
      .map(function (option) {
        const key = textoSeguro_v7(option.value).trim().toLowerCase();

        if (!key || seen.has(key)) {
          return null;
        }

        seen.add(key);

        return {
          key,
          label: limparLabelCabecalho_v7(
            textoSeguro_v7(option.dataset.processConfigLabel || option.textContent)
          ),
          kind: optionEhCabecalho_v7(option) ? "header" : "field"
        };
      })
      .filter(Boolean);
  }

  function lerHeaderOptions_v7(elements, originalOptions) {
    const fromHeaderSelect = Array.from(elements.headerKey.options)
      .map(function (option) {
        const key = textoSeguro_v7(option.value).trim().toLowerCase();

        if (!key) {
          return null;
        }

        return {
          key,
          label: limparLabelCabecalho_v7(
            textoSeguro_v7(option.dataset.processConfigLabel || option.textContent)
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

  function localizarPorChave_v7(options, key) {
    const cleanKey = normalizarChave_v7(key);

    return options.find(function (item) {
      return normalizarChave_v7(item.key) === cleanKey;
    }) || null;
  }

  function labelCampo_v7(state, key) {
    const item = localizarPorChave_v7(state.fieldOptions, key);
    return item ? item.label : key;
  }

  function labelCabecalho_v7(state, key) {
    const item = localizarPorChave_v7(state.headerOptions, key);
    return item ? item.label : "";
  }

  //###################################################################################
  // (5) RECONSTRUIR SELECTS
  //###################################################################################

  function obterEditingItem_v7(state) {
    if (!state || !state.editingId) {
      return null;
    }

    return state.items.find(function (item) {
      return textoSeguro_v7(item.__managerId || item.managerId || item.id) === textoSeguro_v7(state.editingId);
    }) || null;
  }

  function reconstruirSelectCampo_v7(elements, state, selectedKey) {
    const editingItem = obterEditingItem_v7(state);
    const currentValue = normalizarChave_v7(
      selectedKey ||
      elements.editorKey.dataset.processFieldsConfigEditingKeyV7 ||
      elements.editorKey.value ||
      (editingItem ? editingItem.key : "")
    );

    const configuredKeys = new Set(
      state.items.map(function (item) {
        return normalizarChave_v7(item.key);
      })
    );

    elements.editorKey.innerHTML = "";
    elements.editorKey.appendChild(criarOption_v7("", "Selecione", "", ""));

    state.fieldOptions.forEach(function (item) {
      const itemKey = normalizarChave_v7(item.key);

      if (configuredKeys.has(itemKey) && itemKey !== currentValue) {
        return;
      }

      elements.editorKey.appendChild(
        criarOption_v7(item.key, item.label, currentValue, "field")
      );
    });

    elements.editorKey.value = currentValue;
  }

  function reconstruirSelectCabecalho_v7(elements, state, selectedKey) {
    const currentValue = normalizarChave_v7(selectedKey || elements.headerKey.value);

    elements.headerKey.innerHTML = "";
    elements.headerKey.appendChild(criarOption_v7("", "Sem cabeçalho", currentValue, ""));

    state.headerOptions.forEach(function (item) {
      elements.headerKey.appendChild(
        criarOption_v7(item.key, item.label, currentValue, "header")
      );
    });

    elements.headerKey.value = currentValue;
  }

  //###################################################################################
  // (6) LER CONFIGURACOES EXISTENTES
  //###################################################################################

  function valorLinhaLegacy_v7(row, selector) {
    const input = row.querySelector(selector);
    return input ? textoSeguro_v7(input.value).trim().toLowerCase() : "";
  }

  function lerItensLegacy_v7(elements, state) {
    if (!elements.legacyContainer) {
      return [];
    }

    const rows = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-config-field-row]")
    );

    const items = [];
    let currentHeaderKey = "";

    rows.forEach(function (row, index) {
      const key = valorLinhaLegacy_v7(row, "[data-process-config-key]");
      const kind = valorLinhaLegacy_v7(row, "[data-process-config-kind]");
      const explicitHeaderKey = valorLinhaLegacy_v7(row, "[data-process-config-header-key]");

      if (!key) {
        return;
      }

      if (kind === "header") {
        currentHeaderKey = key;
        return;
      }

      items.push({
        id: "legacy_" + index + "_" + key,
        key,
        label: labelCampo_v7(state, key),
        headerKey: explicitHeaderKey || currentHeaderKey,
        headerLabel: labelCabecalho_v7(state, explicitHeaderKey || currentHeaderKey)
      });
    });

    return items;
  }

  function lerItensHidden_v7(elements, state) {
    const fieldInputs = Array.from(
      elements.hiddenContainer.querySelectorAll("input[name='visible_fields']")
    );

    const headerInputs = Array.from(
      elements.hiddenContainer.querySelectorAll("input[name='visible_headers']")
    );

    return fieldInputs
      .map(function (input, index) {
        const key = textoSeguro_v7(input.value).trim().toLowerCase();

        if (!key) {
          return null;
        }

        const headerKey = textoSeguro_v7(headerInputs[index] ? headerInputs[index].value : "")
          .trim()
          .toLowerCase();

        return {
          id: "hidden_" + index + "_" + key,
          key,
          label: labelCampo_v7(state, key),
          headerKey,
          headerLabel: labelCabecalho_v7(state, headerKey)
        };
      })
      .filter(Boolean);
  }

  function juntarItensSemDuplicados_v7(first, second) {
    const merged = [];
    const seen = new Set();

    first.concat(second).forEach(function (item) {
      const key = normalizarChave_v7(item.key);

      if (!key || seen.has(key)) {
        return;
      }

      seen.add(key);
      merged.push(item);
    });

    return merged;
  }

  //###################################################################################
  // (7) EDITOR
  //###################################################################################

  function limparEditor_v7(context) {
    const root = context.root;
    const elements = root.__processFieldsConfigElementsV7;

    if (!elements) {
      return;
    }

    delete elements.editorKey.dataset.processFieldsConfigEditingKeyV7;
    elements.editorKey.value = "";
    elements.headerKey.value = "";

    reconstruirSelectCampo_v7(elements, context.state || context.manager.state, "");
    reconstruirSelectCabecalho_v7(elements, context.state || context.manager.state, "");
  }

  function carregarEditor_v7(item, context) {
    const root = context.root;
    const elements = root.__processFieldsConfigElementsV7;
    const state = context.state || context.manager.state;

    if (!elements) {
      return;
    }

    elements.editorKey.dataset.processFieldsConfigEditingKeyV7 = item.key || "";
    reconstruirSelectCampo_v7(elements, state, item.key || "");
    reconstruirSelectCabecalho_v7(elements, state, item.headerKey || "");

    elements.editorKey.value = item.key || "";
    elements.headerKey.value = item.headerKey || "";

    if (typeof elements.editorKey.focus === "function") {
      elements.editorKey.focus();
    }
  }

  function lerEditorItem_v7(context) {
    const root = context.root;
    const elements = root.__processFieldsConfigElementsV7;
    const state = context.state || context.manager.state;

    if (!elements) {
      return null;
    }

    const selectedOption = elements.editorKey.options[elements.editorKey.selectedIndex];

    if (!selectedOption || !selectedOption.value) {
      return null;
    }

    const key = textoSeguro_v7(selectedOption.value).trim().toLowerCase();
    const headerKey = textoSeguro_v7(elements.headerKey.value).trim().toLowerCase();

    return {
      id: state.editingId || "field_" + Date.now() + "_" + key,
      key,
      label: textoSeguro_v7(selectedOption.dataset.processConfigLabel || selectedOption.textContent),
      headerKey,
      headerLabel: labelCabecalho_v7(state, headerKey)
    };
  }

  function validarEditorItem_v7(item, context) {
    if (!item || !item.key) {
      return { valid: false, message: "Selecione um campo." };
    }

    const editingId = textoSeguro_v7(context.state.editingId);

    const duplicated = context.items.some(function (existingItem) {
      const sameKey = normalizarChave_v7(existingItem.key) === normalizarChave_v7(item.key);
      const sameId = textoSeguro_v7(existingItem.__managerId) === editingId;

      return sameKey && !sameId;
    });

    if (duplicated) {
      return { valid: false, message: "Este campo já está configurado." };
    }

    return { valid: true };
  }

  function existeDraft_v7(elements, manager) {
    return Boolean(manager.state.editingId || elements.editorKey.value);
  }

  //###################################################################################
  // (8) SINCRONIZAR INPUTS PARA BACKEND
  //###################################################################################

  function sincronizarHiddenInputs_v7(context) {
    const root = context.root;
    const elements = root.__processFieldsConfigElementsV7;

    if (!elements || !elements.hiddenContainer) {
      return;
    }

    elements.hiddenContainer.innerHTML = "";

    context.items.forEach(function (item) {
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

  //###################################################################################
  // (9) SUBMIT DA CONFIGURACAO
  //###################################################################################


  //###################################################################################
  // (8A) EVITAR ENVIO DE INPUTS LEGADOS/DUPLICADOS
  //###################################################################################

  function desativarInputsLegadosV8(form, elements) {
    const hiddenContainer = elements && elements.hiddenContainer ? elements.hiddenContainer : null;
    const legacyContainer = elements && elements.legacyContainer ? elements.legacyContainer : null;

    function devePreservarControle_v8(control) {
      return Boolean(hiddenContainer && hiddenContainer.contains(control));
    }

    function desativarControle_v8(control) {
      if (!control || devePreservarControle_v8(control)) {
        return;
      }

      control.disabled = true;
      control.dataset.processFieldsConfigDisabledByV8 = "1";
    }

    Array.from(
      form.querySelectorAll(
        "input[name='visible_fields'], input[name='visible_headers'], input[name='visible_fields[]'], input[name='visible_headers[]']"
      )
    ).forEach(desativarControle_v8);

    if (legacyContainer) {
      Array.from(
        legacyContainer.querySelectorAll("input, select, textarea")
      ).forEach(desativarControle_v8);
    }
  }

  function submitNativo_v7(form) {
    HTMLFormElement.prototype.submit.call(form);
  }

  function vincularBotoesFormulario_v7(form, elements, manager) {
    if (form.dataset.processFieldsConfigSubmitBoundV7 === "1") {
      return;
    }

    form.dataset.processFieldsConfigSubmitBoundV7 = "1";

    elements.submitButton.addEventListener("click", function (event) {
      event.preventDefault();

      if (existeDraft_v7(elements, manager)) {
        const item = lerEditorItem_v7({
          manager,
          root: form,
          elements: manager.elements,
          state: manager.state
        });

        const validationResult = validarEditorItem_v7(item, {
          manager,
          root: form,
          elements: manager.elements,
          state: manager.state,
          items: manager.getItems()
        });

        if (validationResult && validationResult.valid === false) {
          if (validationResult.message) {
            window.alert(validationResult.message);
          }

          return;
        }

        manager.addOrUpdate(item);
      }

      manager.syncHiddenInputs();
      desativarInputsLegadosV8(form, elements);
      submitNativo_v7(form);
    });

    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      manager.clearEditing();
    });

    if (form.dataset.processFieldsConfigSubmitNativeBoundV8 !== "1") {
      form.dataset.processFieldsConfigSubmitNativeBoundV8 = "1";

      form.addEventListener("submit", function () {
        manager.syncHiddenInputs();
        desativarInputsLegadosV8(form, elements);
      });
    }
  }

  //###################################################################################
  // (10) INICIALIZAR UM FORMULARIO
  //###################################################################################

  function iniciarGestorV7(form) {
    if (!form || form.dataset.processFieldsConfigManagerBoundV7 === "1") {
      return null;
    }

    const core = window[CORE_NAMESPACE];

    if (!core || typeof core.createConfigurableItemsManager_v1 !== "function") {
      return null;
    }

    const elements = obterElementos_v7(form);

    if (!elementosMinimosValidos_v7(elements)) {
      return null;
    }

    form.dataset.processFieldsConfigManagerBoundV7 = "1";
    form.__processFieldsConfigElementsV7 = elements;

    const originalOptions = lerOpcoesOriginais_v7(elements);

    const provisionalState = {
      fieldOptions: originalOptions.filter(function (item) { return item.kind !== "header"; }),
      headerOptions: lerHeaderOptions_v7(elements, originalOptions),
      items: [],
      page: 1,
      pageSize: Number.parseInt(elements.pageSize.value, 10) || 5,
      editingId: ""
    };

    const initialItems = juntarItensSemDuplicados_v7(
      lerItensHidden_v7(elements, provisionalState),
      lerItensLegacy_v7(elements, provisionalState)
    );

    const manager = core.createConfigurableItemsManager_v1({
      root: form,
      itemName: "campo",
      itemNamePlural: "campos",
      pageSizeDefault: Number.parseInt(elements.pageSize.value, 10) || 5,
      pageSizeOptions: [5, 10, 25],
      initialItems,
      selectors: {
        editorForm: "[data-process-fields-config-editor-block]",
        table: "[data-process-fields-config-table]",
        tableBody: "[data-process-fields-config-table-body]",
        emptyState: "[data-process-fields-config-empty]",
        pagination: "[data-process-fields-config-pagination]",
        pageSize: "[data-process-fields-config-page-size]",
        hiddenContainer: "[data-process-fields-config-hidden-container]",
        totalLabel: "[data-process-fields-config-total-label]"
      },
      columns: [
        {
          key: "label",
          label: "Nome do campo"
        },
        {
          key: "headerLabel",
          label: "Cabeçalho do campo",
          render: function (item) {
            return item.headerLabel || "Sem cabeçalho";
          }
        }
      ],
      getItemId: function (item, index) {
        return item.id || item.key || "field_" + (index + 1);
      },
      readEditorItem: lerEditorItem_v7,
      loadEditorItem: carregarEditor_v7,
      clearEditor: limparEditor_v7,
      validateItem: validarEditorItem_v7,
      syncHiddenInputs: sincronizarHiddenInputs_v7,
      onRender: function (context) {
        const state = context.state;
        state.fieldOptions = provisionalState.fieldOptions;
        state.headerOptions = provisionalState.headerOptions;

        reconstruirSelectCampo_v7(elements, state);
        reconstruirSelectCabecalho_v7(elements, state);
      }
    });

    if (!manager) {
      return null;
    }

    manager.state.fieldOptions = provisionalState.fieldOptions;
    manager.state.headerOptions = provisionalState.headerOptions;

    reconstruirSelectCampo_v7(elements, manager.state);
    reconstruirSelectCabecalho_v7(elements, manager.state);
    vincularBotoesFormulario_v7(form, elements, manager);
    manager.syncHiddenInputs();

    return manager;
  }

  function iniciarTodosV7() {
    Array.from(document.querySelectorAll(FORM_SELECTOR)).forEach(iniciarGestorV7);
  }

  //###################################################################################
  // (11) INICIALIZACAO
  //###################################################################################

  window.setupProcessFieldsConfigManagerV7 = iniciarTodosV7;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarTodosV7);
  } else {
    iniciarTodosV7();
  }
})(window, document);
