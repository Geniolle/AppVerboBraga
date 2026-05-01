(function () {
  "use strict";

  //###################################################################################
  // (1) PROTECAO CONTRA DUPLICACAO
  //###################################################################################

  if (window.__processFieldsConfigSavePersistV1 === true) {
    return;
  }

  window.__processFieldsConfigSavePersistV1 = true;

  //###################################################################################
  // (2) FUNCOES AUXILIARES
  //###################################################################################

  function normalizarTexto_v1(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizarChave_v1(value) {
    return String(value || "").trim().toLowerCase();
  }

  function escaparCss_v1(value) {
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(value);
    }

    return String(value || "").replace(/"/g, '\\"');
  }

  function obterTextoContextoSelect_v1(select) {
    if (!select) {
      return "";
    }

    let labelText = "";

    const form = select.closest("form");
    const selectId = String(select.id || "").trim();

    if (form && selectId) {
      const label = form.querySelector('label[for="' + escaparCss_v1(selectId) + '"]');

      if (label) {
        labelText += " " + String(label.textContent || "");
      }
    }

    const wrapper =
      select.closest(".field") ||
      select.closest(".form-field") ||
      select.closest(".form-group") ||
      select.closest(".input-group") ||
      select.closest("td") ||
      select.parentElement;

    if (wrapper) {
      labelText += " " + String(wrapper.textContent || "");
    }

    return normalizarTexto_v1(labelText);
  }

  function formularioConfiguracaoCampos_v1(form) {
    if (!form) {
      return false;
    }

    const action = String(form.getAttribute("action") || "");
    const text = normalizarTexto_v1(form.textContent);

    return (
      action.includes("/settings/menu/process-fields") ||
      text.includes("configuracao dos campos") ||
      text.includes("configuração dos campos")
    );
  }

  function listarFormulariosConfiguracaoCampos_v1() {
    return Array.from(document.querySelectorAll("form")).filter(formularioConfiguracaoCampos_v1);
  }

  function isSelectCabecalho_v1(select) {
    if (!select) {
      return false;
    }

    const name = normalizarTexto_v1(select.name);
    const id = normalizarTexto_v1(select.id);
    const contextText = obterTextoContextoSelect_v1(select);

    return (
      select.dataset.mainHeaderSelectV4 === "1" ||
      select.dataset.mainHeaderSelectV5 === "1" ||
      select.dataset.mainHeaderSelectV6 === "1" ||
      name === "selected_visible_header" ||
      name.includes("header") ||
      id.includes("header") ||
      contextText.includes("cabecalho") ||
      contextText.includes("cabeçalho")
    );
  }

  function encontrarSelectCampo_v1(form) {
    if (!form) {
      return null;
    }

    const selects = Array.from(form.querySelectorAll("select"));

    const byDataset = selects.find(function (select) {
      return (
        select.dataset.processFieldsConfigEditorKeyV6 === "1" ||
        select.dataset.processFieldsConfigEditingKeyV7 ||
        select.dataset.processFieldsConfigEditingKey
      );
    });

    if (byDataset && !isSelectCabecalho_v1(byDataset)) {
      return byDataset;
    }

    const byLabel = selects.find(function (select) {
      if (isSelectCabecalho_v1(select)) {
        return false;
      }

      const contextText = obterTextoContextoSelect_v1(select);

      return (
        contextText.includes("nome do campo") ||
        contextText.includes("campo do processo") ||
        contextText.includes("campo")
      );
    });

    if (byLabel) {
      return byLabel;
    }

    return selects.find(function (select) {
      return !isSelectCabecalho_v1(select);
    }) || null;
  }

  function encontrarSelectCabecalho_v1(form) {
    if (!form) {
      return null;
    }

    return (
      form.querySelector("[data-main-header-select-v6='1']") ||
      form.querySelector("[data-main-header-select-v5='1']") ||
      form.querySelector("[data-main-header-select-v4='1']") ||
      form.querySelector("[name='selected_visible_header']") ||
      Array.from(form.querySelectorAll("select")).find(isSelectCabecalho_v1) ||
      null
    );
  }

  function obterLabelOptionSelecionada_v1(select, value) {
    if (!select) {
      return "";
    }

    const cleanValue = normalizarChave_v1(value);

    const option = Array.from(select.options).find(function (item) {
      return normalizarChave_v1(item.value) === cleanValue;
    });

    return option ? String(option.textContent || "").trim() : "";
  }

  //###################################################################################
  // (3) LOCALIZAR E ATUALIZAR LINHA/INPUTS OCULTOS
  //###################################################################################

  function obterEscopoLinha_v1(fieldInput) {
    if (!fieldInput) {
      return null;
    }

    return (
      fieldInput.closest("tr") ||
      fieldInput.closest("[data-process-fields-row]") ||
      fieldInput.closest("[data-process-field-row]") ||
      fieldInput.closest(".process-fields-config-row-v6") ||
      fieldInput.closest(".process-fields-config-row-v4") ||
      fieldInput.closest(".configured-field-row") ||
      fieldInput.closest(".settings-row") ||
      fieldInput.closest(".field-row") ||
      fieldInput.parentElement
    );
  }

  function obterHeaderInputDaLinha_v1(form, row, rowIndex) {
    if (row) {
      const insideRow = row.querySelector('input[name="visible_headers"]');

      if (insideRow) {
        return insideRow;
      }
    }

    const allHeaders = Array.from(form.querySelectorAll('input[name="visible_headers"]'));

    if (rowIndex >= 0 && rowIndex < allHeaders.length) {
      return allHeaders[rowIndex];
    }

    return null;
  }

  function criarInputOculto_v1(name, value) {
    const input = document.createElement("input");

    input.type = "hidden";
    input.name = name;
    input.value = value || "";

    return input;
  }

  function obterOuCriarContainerOculto_v1(form) {
    let container = form.querySelector("[data-process-fields-save-persist-hidden-v1='1']");

    if (container) {
      return container;
    }

    container = document.createElement("div");
    container.dataset.processFieldsSavePersistHiddenV1 = "1";
    container.style.display = "none";

    form.appendChild(container);

    return container;
  }

  function criarLinhaOcultaPersistencia_v1(form, fieldKey, headerKey) {
    const container = obterOuCriarContainerOculto_v1(form);

    const row = document.createElement("div");
    row.dataset.processFieldsGeneratedRowV1 = "1";

    row.appendChild(criarInputOculto_v1("visible_fields", fieldKey));
    row.appendChild(criarInputOculto_v1("visible_headers", headerKey));

    container.appendChild(row);

    return row.querySelector('input[name="visible_fields"]');
  }

  function atualizarDisplayCabecalhoLinha_v1(row, headerKey, headerLabel) {
    if (!row) {
      return;
    }

    const label = headerLabel || headerKey || "Sem cabeçalho";

    const headerSelect = row.querySelector("select");

    if (headerSelect && isSelectCabecalho_v1(headerSelect)) {
      headerSelect.value = headerKey;
      return;
    }

    if (row.cells && row.cells.length >= 2) {
      let display = row.cells[1].querySelector("[data-process-fields-header-display-persist-v1='1']");

      if (!display) {
        display = document.createElement("span");
        display.dataset.processFieldsHeaderDisplayPersistV1 = "1";

        Array.from(row.cells[1].childNodes).forEach(function (node) {
          if (node.nodeType === Node.TEXT_NODE) {
            node.nodeValue = "";
          }
        });

        row.cells[1].insertBefore(display, row.cells[1].firstChild);
      }

      display.textContent = label;
      return;
    }

    const existingDisplay = row.querySelector("[data-process-fields-header-display-persist-v1='1']");

    if (existingDisplay) {
      existingDisplay.textContent = label;
    }
  }

  function sincronizarEditorComInputsOcultos_v1(form) {
    if (!form || !formularioConfiguracaoCampos_v1(form)) {
      return false;
    }

    const fieldSelect = encontrarSelectCampo_v1(form);
    const headerSelect = encontrarSelectCabecalho_v1(form);

    if (!fieldSelect) {
      return false;
    }

    const originalFieldKey = normalizarChave_v1(
      fieldSelect.dataset.processFieldsConfigEditingKeyV7 ||
      fieldSelect.dataset.processFieldsConfigEditingKey ||
      fieldSelect.dataset.editingConfiguredFieldV1 ||
      ""
    );

    const selectedFieldKey = normalizarChave_v1(fieldSelect.value || originalFieldKey);
    const selectedHeaderKey = normalizarChave_v1(headerSelect ? headerSelect.value : "");

    if (!selectedFieldKey) {
      return false;
    }

    const fieldInputs = Array.from(form.querySelectorAll('input[name="visible_fields"]'));
    let targetInput = null;
    let targetIndex = -1;

    fieldInputs.forEach(function (input, index) {
      const inputValue = normalizarChave_v1(input.value);

      if (targetInput) {
        return;
      }

      if (originalFieldKey && inputValue === originalFieldKey) {
        targetInput = input;
        targetIndex = index;
        return;
      }

      if (inputValue === selectedFieldKey) {
        targetInput = input;
        targetIndex = index;
      }
    });

    if (!targetInput) {
      targetInput = criarLinhaOcultaPersistencia_v1(form, selectedFieldKey, selectedHeaderKey);
      targetIndex = Array.from(form.querySelectorAll('input[name="visible_fields"]')).indexOf(targetInput);
    }

    targetInput.value = selectedFieldKey;

    const row = obterEscopoLinha_v1(targetInput);
    let headerInput = obterHeaderInputDaLinha_v1(form, row, targetIndex);

    if (!headerInput) {
      headerInput = criarInputOculto_v1("visible_headers", selectedHeaderKey);

      if (row) {
        row.appendChild(headerInput);
      }
      else {
        obterOuCriarContainerOculto_v1(form).appendChild(headerInput);
      }
    }

    headerInput.value = selectedHeaderKey;

    const headerLabel = obterLabelOptionSelecionada_v1(headerSelect, selectedHeaderKey);

    atualizarDisplayCabecalhoLinha_v1(row, selectedHeaderKey, headerLabel);

    fieldSelect.dataset.processFieldsConfigEditingKeyV7 = selectedFieldKey;
    fieldSelect.dataset.processFieldsPersistLastSavedV1 = selectedFieldKey;

    if (headerSelect) {
      headerSelect.dataset.processFieldsPersistLastSavedV1 = selectedHeaderKey;
    }

    return true;
  }

  //###################################################################################
  // (4) DETETAR CLIQUE EM GUARDAR E SUBMIT
  //###################################################################################

  function isBotaoGuardarConfiguracaoCampos_v1(button) {
    if (!button) {
      return false;
    }

    const form = button.closest("form");

    if (!form || !formularioConfiguracaoCampos_v1(form)) {
      return false;
    }

    const text = normalizarTexto_v1(
      button.textContent ||
      button.getAttribute("aria-label") ||
      button.getAttribute("title") ||
      button.dataset.action ||
      ""
    );

    return (
      button.dataset.processFieldsConfigSubmit === "1" ||
      text.includes("guardar") ||
      text.includes("gravar") ||
      text.includes("salvar") ||
      text.includes("save")
    );
  }

  function vincularFormulario_v1(form) {
    if (!form || form.dataset.processFieldsSavePersistBoundV1 === "1") {
      return;
    }

    form.dataset.processFieldsSavePersistBoundV1 = "1";

    form.addEventListener("submit", function () {
      sincronizarEditorComInputsOcultos_v1(form);
    }, false);
  }

  function inicializar_v1() {
    listarFormulariosConfiguracaoCampos_v1().forEach(vincularFormulario_v1);
  }

  document.addEventListener("click", function (event) {
    const button = event.target ? event.target.closest("button, a, input[type='button'], input[type='submit']") : null;

    if (!isBotaoGuardarConfiguracaoCampos_v1(button)) {
      return;
    }

    const form = button.closest("form");

    sincronizarEditorComInputsOcultos_v1(form);
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v1);
  }
  else {
    inicializar_v1();
  }

  window.setTimeout(inicializar_v1, 250);
  window.setTimeout(inicializar_v1, 800);
  window.setTimeout(inicializar_v1, 1500);
})();