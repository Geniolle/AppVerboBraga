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

  // APPVERBO_PROCESS_FIELDS_V6_ACTION_BUTTONS_V2_START

  function criarBotaoFormulario_v6(kind, label) {
    const button = document.createElement("button");

    button.type = "button";
    button.textContent = label;

    if (kind === "submit") {
      button.dataset.processFieldsConfigSubmit = "1";
      button.className = "action-btn process-fields-config-submit-v6";
    }

    if (kind === "cancel") {
      button.dataset.processFieldsConfigCancel = "1";
      button.className = "action-btn-cancel process-fields-config-cancel-v6";
    }

    button.hidden = false;
    button.removeAttribute("hidden");
    button.style.display = "inline-flex";
    button.style.visibility = "visible";
    button.style.opacity = "1";
    button.style.alignItems = "center";
    button.style.justifyContent = "center";
    button.style.minWidth = "110px";
    button.style.height = "38px";
    button.style.borderRadius = "8px";
    button.style.fontWeight = "700";
    button.style.cursor = "pointer";

    return button;
  }

  function mostrarElementoFormulario_v6(element) {
    if (!element) {
      return;
    }

    element.hidden = false;
    element.removeAttribute("hidden");
    element.style.display = "";
    element.style.visibility = "visible";
    element.style.opacity = "1";
  }

  function localizarLinhaEditorFormulario_v6(form, elements) {
    const editorWrapper =
      elements.editorKey.closest(".field") ||
      elements.editorKey.closest(".form-field") ||
      elements.editorKey.parentElement;

    const headerWrapper =
      elements.headerKey.closest(".field") ||
      elements.headerKey.closest(".form-field") ||
      elements.headerKey.parentElement;

    if (editorWrapper && headerWrapper && editorWrapper.parentElement === headerWrapper.parentElement) {
      return editorWrapper.parentElement;
    }

    return (
      form.querySelector(".process-fields-config-editor-row-v6") ||
      form.querySelector(".process-fields-config-editor-row-v4") ||
      headerWrapper ||
      editorWrapper ||
      form
    );
  }

  function garantirBotoesFormulario_v6(form, elements) {
    if (!form || !elements || !elements.editorKey || !elements.headerKey) {
      return;
    }

    let actionRow = form.querySelector("[data-process-fields-config-action-row-v6='1']");

    if (!actionRow) {
      actionRow = document.createElement("div");
      actionRow.dataset.processFieldsConfigActionRowV6 = "1";
      actionRow.className = "form-action-row process-fields-config-action-row-v6";
    }

    actionRow.hidden = false;
    actionRow.removeAttribute("hidden");
    actionRow.style.display = "flex";
    actionRow.style.gap = "10px";
    actionRow.style.alignItems = "center";
    actionRow.style.justifyContent = "flex-start";
    actionRow.style.marginTop = "12px";
    actionRow.style.width = "100%";
    actionRow.style.visibility = "visible";
    actionRow.style.opacity = "1";

    if (!elements.submitButton) {
      elements.submitButton = criarBotaoFormulario_v6("submit", "Guardar");
    }

    if (!elements.cancelButton) {
      elements.cancelButton = criarBotaoFormulario_v6("cancel", "Cancelar");
    }

    mostrarElementoFormulario_v6(elements.submitButton);
    mostrarElementoFormulario_v6(elements.cancelButton);

    if (!actionRow.contains(elements.submitButton)) {
      actionRow.appendChild(elements.submitButton);
    }

    if (!actionRow.contains(elements.cancelButton)) {
      actionRow.appendChild(elements.cancelButton);
    }

    const editorRow = localizarLinhaEditorFormulario_v6(form, elements);

    if (editorRow && editorRow.parentElement && editorRow !== actionRow) {
      editorRow.insertAdjacentElement("afterend", actionRow);
      return;
    }

    form.insertBefore(actionRow, form.firstChild);
  }

  // APPVERBO_PROCESS_FIELDS_V6_ACTION_BUTTONS_V2_END


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

  function reconstruirSelectCampo_v7(elements, state) {
    // APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_SELECT_EDIT_START
    const configuredKeys = new Set(
      state.items.map(function (item) {
        return normalizarChave_v6(item.key);
      })
    );

    const currentValue = normalizarChave_v6(
      elements.editorKey.value ||
      elements.editorKey.dataset.processFieldsConfigEditingKeyV7 ||
      ""
    );

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
    // APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_SELECT_EDIT_END
  }

  function reconstruirSelectCampo_v6(elements, state) {
    return reconstruirSelectCampo_v7(elements, state);
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

  function limparEditor_v7(elements, state) {
    // APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_EDITOR_CLEAR_START
    state.editingId = "";
    elements.editorKey.value = "";
    delete elements.editorKey.dataset.processFieldsConfigEditingKeyV7;
    elements.headerKey.value = "";
    reconstruirSelectCampo_v6(elements, state);
    // APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_EDITOR_CLEAR_END
  }

  function limparEditor_v6(elements, state) {
    return limparEditor_v7(elements, state);
  }

  function carregarEditor_v7(elements, state, item) {
    // APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_EDITOR_LOAD_START
    state.editingId = item.managerId;
    elements.editorKey.dataset.processFieldsConfigEditingKeyV7 = item.key || "";
    elements.editorKey.value = item.key || "";
    reconstruirSelectCampo_v6(elements, state);
    elements.editorKey.value = item.key || "";
    elements.headerKey.value = item.headerKey || "";

    if (typeof elements.editorKey.focus === "function") {
      elements.editorKey.focus();
    }
    // APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_EDITOR_LOAD_END
  }

  function carregarEditor_v6(elements, state, item) {
    return carregarEditor_v7(elements, state, item);
  }


  // APPVERBO_PROCESS_FIELDS_HEADER_RESOLVE_V3_START

  function resolverHeaderKeyAtual_v9(elements) {
    if (!elements) {
      return "";
    }

    const candidates = [];

    if (elements.headerKey) {
      candidates.push(elements.headerKey);
    }

    const form = elements.editorKey ? elements.editorKey.closest("form") : null;

    if (form) {
      form.querySelectorAll("select").forEach(function (select) {
        const name = normalizarChave_v6(select.name || "");
        const id = normalizarChave_v6(select.id || "");
        const dataMarker = String(select.getAttribute("data-process-fields-config-header-editor-key") || "");
        const wrapperText = normalizarChave_v6(
          select.closest(".field, .form-field, label, div")
            ? select.closest(".field, .form-field, label, div").textContent
            : ""
        );

        if (
          dataMarker ||
          name.includes("header") ||
          id.includes("header") ||
          wrapperText.includes("cabecalho") ||
          wrapperText.includes("cabeçalho")
        ) {
          candidates.push(select);
        }
      });
    }

    for (const candidate of candidates) {
      const value = normalizarChave_v6(candidate.value || "");

      if (value) {
        if (elements.headerKey && elements.headerKey !== candidate) {
          elements.headerKey.value = value;
        }

        return value;
      }
    }

    return "";
  }

  // APPVERBO_PROCESS_FIELDS_HEADER_RESOLVE_V3_END

  // APPVERBO_PROCESS_FIELDS_HEADER_SAVE_FIX_V1_START

  function obterHeaderLabelSelecionado_v8(elements, headerKey) {
    if (!elements || !elements.headerKey || !headerKey) {
      return "";
    }

    const option = Array.from(elements.headerKey.options || []).find(function (item) {
      return normalizarChave_v6(item.value) === normalizarChave_v6(headerKey);
    });

    return option ? String(option.textContent || "").trim() : "";
  }

  function lerDraft_v8(elements, state) {
    const selectedOption = elements.editorKey.options[elements.editorKey.selectedIndex];

    const fieldKey = normalizarChave_v6(elements.editorKey.value);
    const headerKey = resolverHeaderKeyAtual_v9(elements);

    const fieldLabel = String(
      selectedOption
        ? (
          selectedOption.dataset.processConfigLabel ||
          selectedOption.textContent ||
          fieldKey
        )
        : fieldKey
    ).trim();

    const headerLabel = obterHeaderLabelSelecionado_v8(elements, headerKey);

    return {
      managerId: state.editingId || fieldKey,
      key: fieldKey,
      label: fieldLabel || fieldKey,
      headerKey: headerKey,
      headerLabel: headerLabel
    };
  }

  function lerDraft_v6(elements, state) {
    return lerDraft_v8(elements, state);
  }

  // APPVERBO_PROCESS_FIELDS_HEADER_SAVE_FIX_V1_END



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


  //###################################################################################
  // (6) HIDDEN INPUTS
  //###################################################################################

  // APPVERBO_PROCESS_FIELDS_HIDDEN_HEADERS_FIX_V1_START

  function criarHiddenProcessField_v8(container, name, value) {
    const input = document.createElement("input");

    input.type = "hidden";
    input.name = name;
    input.value = value || "";
    input.dataset.processFieldsGeneratedHiddenV8 = "1";

    container.appendChild(input);
  }

  function obterHiddenContainerProcessFields_v8(elements, state) {
    const form = elements && elements.editorKey ? elements.editorKey.closest("form") : null;

    let container =
      elements.hiddenContainer ||
      elements.hiddenInputsContainer ||
      elements.hiddenFieldsContainer ||
      null;

    if (!container && form) {
      container = form.querySelector("[data-process-fields-hidden-container-v8='1']");
    }

    if (!container && form) {
      container = document.createElement("div");
      container.dataset.processFieldsHiddenContainerV8 = "1";
      container.hidden = true;
      form.appendChild(container);
    }

    return container;
  }

  function reconstruirHiddenInputs_v8(elements, state) {
    const form = elements && elements.editorKey ? elements.editorKey.closest("form") : null;
    const container = obterHiddenContainerProcessFields_v8(elements, state);

    if (!container) {
      return;
    }

    if (form) {
      form.querySelectorAll("input[type='hidden'][name='visible_fields'], input[type='hidden'][name='visible_headers'], input[type='hidden'][name='visible_rows_json']").forEach(function (input) {
        input.remove();
      });
    }

    container.innerHTML = "";

    // APPVERBO_PROCESS_FIELDS_ROWS_JSON_V3_START
    const visibleRowsJson_v9 = [];

    (state.items || []).forEach(function (item) {
      const fieldKey = normalizarChave_v6(item.key);
      const headerKey = normalizarChave_v6(item.headerKey || item.header_key || item.header || "");

      if (!fieldKey) {
        return;
      }

      visibleRowsJson_v9.push({
        field_key: fieldKey,
        header_key: headerKey
      });

      criarHiddenProcessField_v8(container, "visible_fields", fieldKey);
      criarHiddenProcessField_v8(container, "visible_headers", headerKey);
    });

    criarHiddenProcessField_v8(
      container,
      "visible_rows_json",
      JSON.stringify(visibleRowsJson_v9)
    );
    // APPVERBO_PROCESS_FIELDS_ROWS_JSON_V3_END
  }

  function reconstruirHiddenInputs_v6(elements, state) {
    return reconstruirHiddenInputs_v8(elements, state);
  }

  // APPVERBO_PROCESS_FIELDS_HIDDEN_HEADERS_FIX_V1_END




  // APPVERBO_PROCESS_FIELDS_SYNC_ALIAS_V2_START

  function sincronizarHiddenInputs_v6(elements, state) {
    return reconstruirHiddenInputs_v8(elements, state);
  }

  // APPVERBO_PROCESS_FIELDS_SYNC_ALIAS_V2_END


  // APPVERBO_PROCESS_FIELDS_HEADER_PERSIST_V4_START

  function resolverHeaderKeyAtual_v10(elements) {
    if (!elements) {
      return "";
    }

    const candidates = [];

    if (elements.headerKey) {
      candidates.push(elements.headerKey);
    }

    const form = elements.editorKey ? elements.editorKey.closest("form") : null;

    if (form) {
      form.querySelectorAll("select").forEach(function (select) {
        const name = normalizarChave_v6(select.name || "");
        const id = normalizarChave_v6(select.id || "");
        const marker = String(select.getAttribute("data-process-fields-config-header-editor-key") || "");
        const wrapperText = normalizarChave_v6(
          select.closest(".field, .form-field, label, div")
            ? select.closest(".field, .form-field, label, div").textContent
            : ""
        );

        if (
          marker ||
          name.includes("header") ||
          id.includes("header") ||
          wrapperText.includes("cabecalho") ||
          wrapperText.includes("cabeçalho")
        ) {
          candidates.push(select);
        }
      });
    }

    for (const candidate of candidates) {
      const value = normalizarChave_v6(candidate.value || "");

      if (!value) {
        continue;
      }

      if (elements.headerKey && elements.headerKey !== candidate) {
        elements.headerKey.value = value;
      }

      return value;
    }

    return "";
  }

  function resolverHeaderLabelAtual_v10(elements, headerKey) {
    if (!elements || !headerKey) {
      return "";
    }

    const form = elements.editorKey ? elements.editorKey.closest("form") : null;
    const candidates = [];

    if (elements.headerKey) {
      candidates.push(elements.headerKey);
    }

    if (form) {
      form.querySelectorAll("select").forEach(function (select) {
        candidates.push(select);
      });
    }

    for (const select of candidates) {
      const option = Array.from(select.options || []).find(function (item) {
        return normalizarChave_v6(item.value || "") === normalizarChave_v6(headerKey);
      });

      if (option) {
        return String(option.textContent || "").trim();
      }
    }

    return labelCabecalho_v6 ? labelCabecalho_v6({}, headerKey) : "";
  }

  function lerDraft_v10(elements, state) {
    const fieldKey = normalizarChave_v6(elements.editorKey ? elements.editorKey.value : "");
    const headerKey = resolverHeaderKeyAtual_v10(elements);

    const selectedOption = elements.editorKey
      ? elements.editorKey.options[elements.editorKey.selectedIndex]
      : null;

    const fieldLabel = String(
      selectedOption
        ? (
          selectedOption.dataset.processConfigLabel ||
          selectedOption.textContent ||
          fieldKey
        )
        : fieldKey
    ).trim();

    const headerLabel = resolverHeaderLabelAtual_v10(elements, headerKey);

    return {
      managerId: state.editingId || fieldKey,
      key: fieldKey,
      label: fieldLabel || fieldKey,
      headerKey: headerKey,
      headerLabel: headerLabel || "Sem cabeçalho"
    };
  }

  function lerDraft_v6(elements, state) {
    return lerDraft_v10(elements, state);
  }

  function criarHiddenProcessField_v10(container, name, value) {
    const input = document.createElement("input");

    input.type = "hidden";
    input.name = name;
    input.value = value || "";
    input.dataset.processFieldsHeaderPersistV4 = "1";

    container.appendChild(input);
  }

  function obterHiddenContainerProcessFields_v10(elements) {
    const form = elements && elements.editorKey ? elements.editorKey.closest("form") : null;

    let container =
      elements.hiddenContainer ||
      elements.hiddenInputsContainer ||
      elements.hiddenFieldsContainer ||
      null;

    if (!container && form) {
      container = form.querySelector("[data-process-fields-config-hidden-container]");
    }

    if (!container && form) {
      container = form.querySelector("[data-process-fields-hidden-container-v10='1']");
    }

    if (!container && form) {
      container = document.createElement("div");
      container.hidden = true;
      container.dataset.processFieldsHiddenContainerV10 = "1";
      form.appendChild(container);
    }

    return container;
  }

  function sincronizarHiddenInputs_v10(elements, state) {
    const form = elements && elements.editorKey ? elements.editorKey.closest("form") : null;
    const container = obterHiddenContainerProcessFields_v10(elements);

    if (!container) {
      return;
    }

    if (form) {
      form
        .querySelectorAll("input[type='hidden'][name='visible_fields'], input[type='hidden'][name='visible_headers'], input[type='hidden'][name='visible_rows_json']")
        .forEach(function (input) {
          input.remove();
        });
    }

    container.innerHTML = "";

    const visibleRows = [];

    (state.items || []).forEach(function (item) {
      const fieldKey = normalizarChave_v6(item.key);
      const headerKey = normalizarChave_v6(item.headerKey || item.header_key || item.header || "");

      if (!fieldKey) {
        return;
      }

      visibleRows.push({
        field_key: fieldKey,
        header_key: headerKey
      });

      criarHiddenProcessField_v10(container, "visible_fields", fieldKey);
      criarHiddenProcessField_v10(container, "visible_headers", headerKey);
    });

    criarHiddenProcessField_v10(
      container,
      "visible_rows_json",
      JSON.stringify(visibleRows)
    );
  }

  function sincronizarHiddenInputs_v6(elements, state) {
    return sincronizarHiddenInputs_v10(elements, state);
  }

  function reconstruirHiddenInputs_v6(elements, state) {
    return sincronizarHiddenInputs_v10(elements, state);
  }

  // APPVERBO_PROCESS_FIELDS_HEADER_PERSIST_V4_END

  // APPVERBO_PROCESS_FIELDS_NATIVE_SUBMIT_V12_START

  function garantirAcaoFormularioProcessFields_v12(form) {
    if (!form) {
      return;
    }

    const actionText = String(form.getAttribute("action") || "");

    if (!actionText || !actionText.includes("/settings/menu/process-fields")) {
      form.setAttribute("action", "/settings/menu/process-fields");
    }

    const methodText = String(form.getAttribute("method") || "");

    if (!methodText || methodText.toUpperCase() !== "POST") {
      form.setAttribute("method", "post");
    }
  }

  function submitNativo_v6(form) {
    if (!form) {
      return;
    }

    if (form.dataset.processFieldsNativeSubmitV12 === "1") {
      return;
    }

    form.dataset.processFieldsNativeSubmitV12 = "1";

    garantirAcaoFormularioProcessFields_v12(form);

    HTMLFormElement.prototype.submit.call(form);
  }

  // APPVERBO_PROCESS_FIELDS_NATIVE_SUBMIT_V12_END



  // APPVERBO_PROCESS_FIELDS_NO_NATIVE_DOUBLE_POST_V12_START

  function formularioConfiguracaoCampos_v12(form) {
    if (!form || typeof form.querySelector !== "function") {
      return false;
    }

    const actionText = String(form.getAttribute("action") || form.action || "");

    return (
      actionText.includes("/settings/menu/process-fields") ||
      Boolean(form.querySelector("[data-process-fields-config-hidden-container]")) ||
      Boolean(form.querySelector("[data-process-fields-config-table]")) ||
      Boolean(form.querySelector("[data-process-fields-config-submit]"))
    );
  }

  function botaoConfiguracaoCampos_v12(event) {
    if (!event || !event.target || typeof event.target.closest !== "function") {
      return null;
    }

    return event.target.closest("button, input[type='submit'], input[type='button']");
  }

  document.addEventListener(
    "click",
    function (event) {
      const button = botaoConfiguracaoCampos_v12(event);

      if (!button) {
        return;
      }

      const form = button.closest("form");

      if (!formularioConfiguracaoCampos_v12(form)) {
        return;
      }

      if (button.dataset.processFieldsAllowNativeV12 === "1") {
        return;
      }

      event.preventDefault();
    },
    true
  );

  document.addEventListener(
    "submit",
    function (event) {
      const form = event.target;

      if (!formularioConfiguracaoCampos_v12(form)) {
        return;
      }

      event.preventDefault();
      event.stopImmediatePropagation();

      if (form.dataset.processFieldsConfirmSaveActiveV11 === "1") {
        return;
      }

      if (typeof submitNativo_v6 === "function") {
        submitNativo_v6(form);
      }
    },
    true
  );

  // APPVERBO_PROCESS_FIELDS_NO_NATIVE_DOUBLE_POST_V12_END


  // APPVERBO_PROCESS_FIELDS_KEY_BASED_HEADER_SAVE_V14_START

  function obterItemExistentePorCampo_v14(state, fieldKey) {
    const cleanFieldKey = normalizarChave_v6(fieldKey);

    if (!cleanFieldKey || !state || !Array.isArray(state.items)) {
      return null;
    }

    return state.items.find(function (item) {
      return normalizarChave_v6(item.key) === cleanFieldKey;
    }) || null;
  }

  function obterHeaderKeyEditor_v14(elements) {
    if (!elements || !elements.headerKey) {
      return "";
    }

    return normalizarChave_v6(elements.headerKey.value || "");
  }

  function obterLabelCampoEditor_v14(elements, fieldKey) {
    if (!elements || !elements.editorKey) {
      return fieldKey || "";
    }

    const selectedOption = elements.editorKey.options[elements.editorKey.selectedIndex];

    if (selectedOption) {
      return String(
        selectedOption.dataset.processConfigLabel ||
        selectedOption.textContent ||
        fieldKey ||
        ""
      ).trim();
    }

    return fieldKey || "";
  }

  function obterLabelCabecalhoEditor_v14(elements, state, headerKey) {
    const cleanHeaderKey = normalizarChave_v6(headerKey);

    if (!cleanHeaderKey) {
      return "Sem cabeçalho";
    }

    if (state && Array.isArray(state.headerOptions)) {
      const stateOption = state.headerOptions.find(function (item) {
        return normalizarChave_v6(item.key) === cleanHeaderKey;
      });

      if (stateOption && stateOption.label) {
        return String(stateOption.label || "").trim();
      }
    }

    if (elements && elements.headerKey) {
      const option = Array.from(elements.headerKey.options || []).find(function (item) {
        return normalizarChave_v6(item.value) === cleanHeaderKey;
      });

      if (option) {
        return String(option.textContent || "").trim();
      }
    }

    return cleanHeaderKey;
  }

  function lerDraft_v14(elements, state) {
    const fieldKey = normalizarChave_v6(elements && elements.editorKey ? elements.editorKey.value : "");
    const headerKey = obterHeaderKeyEditor_v14(elements);
    const existingItem = obterItemExistentePorCampo_v14(state, fieldKey);

    if (!fieldKey) {
      return null;
    }

    return {
      managerId: existingItem && existingItem.managerId ? existingItem.managerId : fieldKey,
      key: fieldKey,
      label: obterLabelCampoEditor_v14(elements, fieldKey) || fieldKey,
      headerKey: headerKey,
      headerLabel: obterLabelCabecalhoEditor_v14(elements, state, headerKey)
    };
  }

  function lerDraft_v6(elements, state) {
    return lerDraft_v14(elements, state);
  }

  function normalizarItensPorCampo_v14(state) {
    if (!state || !Array.isArray(state.items)) {
      return [];
    }

    const normalizedItems = [];
    const indexByFieldKey = new Map();

    state.items.forEach(function (item) {
      const fieldKey = normalizarChave_v6(item && item.key ? item.key : "");

      if (!fieldKey) {
        return;
      }

      const headerKey = normalizarChave_v6(
        item.headerKey ||
        item.header_key ||
        item.header ||
        ""
      );

      const normalizedItem = {
        managerId: item.managerId || fieldKey,
        key: fieldKey,
        label: item.label || fieldKey,
        headerKey: headerKey,
        headerLabel: headerKey
          ? (item.headerLabel || item.header_label || headerKey)
          : "Sem cabeçalho"
      };

      if (indexByFieldKey.has(fieldKey)) {
        const existingIndex = indexByFieldKey.get(fieldKey);
        const existingItem = normalizedItems[existingIndex];

        if (headerKey || !existingItem.headerKey) {
          normalizedItems[existingIndex] = normalizedItem;
        }

        return;
      }

      indexByFieldKey.set(fieldKey, normalizedItems.length);
      normalizedItems.push(normalizedItem);
    });

    state.items = normalizedItems;

    return normalizedItems;
  }

  function criarHiddenProcessField_v14(container, name, value) {
    const input = document.createElement("input");

    input.type = "hidden";
    input.name = name;
    input.value = value || "";
    input.dataset.processFieldsKeyBasedHeaderSaveV14 = "1";

    container.appendChild(input);
  }

  function obterHiddenContainerProcessFields_v14(elements) {
    const form = elements && elements.editorKey ? elements.editorKey.closest("form") : null;

    let container =
      elements.hiddenContainer ||
      elements.hiddenInputsContainer ||
      elements.hiddenFieldsContainer ||
      null;

    if (!container && form) {
      container = form.querySelector("[data-process-fields-config-hidden-container]");
    }

    if (!container && form) {
      container = form.querySelector("[data-process-fields-hidden-container-v14='1']");
    }

    if (!container && form) {
      container = document.createElement("div");
      container.hidden = true;
      container.dataset.processFieldsHiddenContainerV14 = "1";
      form.appendChild(container);
    }

    return container;
  }

  function sincronizarHiddenInputs_v14(elements, state) {
    const form = elements && elements.editorKey ? elements.editorKey.closest("form") : null;
    const container = obterHiddenContainerProcessFields_v14(elements);

    if (!container) {
      return;
    }

    if (form) {
      form
        .querySelectorAll("input[type='hidden'][name='visible_fields'], input[type='hidden'][name='visible_headers'], input[type='hidden'][name='visible_rows_json']")
        .forEach(function (input) {
          input.remove();
        });
    }

    container.innerHTML = "";

    const visibleRows = [];
    const normalizedItems = normalizarItensPorCampo_v14(state);

    normalizedItems.forEach(function (item) {
      const fieldKey = normalizarChave_v6(item.key);
      const headerKey = normalizarChave_v6(item.headerKey || "");

      if (!fieldKey) {
        return;
      }

      visibleRows.push({
        field_key: fieldKey,
        header_key: headerKey
      });

      criarHiddenProcessField_v14(container, "visible_fields", fieldKey);
      criarHiddenProcessField_v14(container, "visible_headers", headerKey);
    });

    criarHiddenProcessField_v14(
      container,
      "visible_rows_json",
      JSON.stringify(visibleRows)
    );
  }

  function sincronizarHiddenInputs_v6(elements, state) {
    return sincronizarHiddenInputs_v14(elements, state);
  }

  function reconstruirHiddenInputs_v6(elements, state) {
    return sincronizarHiddenInputs_v14(elements, state);
  }

  // APPVERBO_PROCESS_FIELDS_KEY_BASED_HEADER_SAVE_V14_END

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

    garantirBotoesFormulario_v6(form, elements);

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
