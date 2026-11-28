// new_user/09_process_settings_builders.js: Configuracao de processos: construtores de campos e abas de edicao.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

function setupProcessFieldsBuilder() {
  if (!processFieldsBuilderEl) {
    return;
  }
  const optionsRaw = processFieldsBuilderEl.getAttribute("data-field-options") || "[]";
  const headerOptionsRaw = processFieldsBuilderEl.getAttribute("data-header-options") || "[]";
  let fieldOptions = [];
  let headerOptions = [];
  try {
    fieldOptions = JSON.parse(optionsRaw);
  } catch (error) {
    fieldOptions = [];
  }
  try {
    headerOptions = JSON.parse(headerOptionsRaw);
  } catch (error) {
    headerOptions = [];
  }
  if (!Array.isArray(fieldOptions) || !fieldOptions.length) {
    return;
  }
  if (!Array.isArray(headerOptions)) {
    headerOptions = [];
  }

  const containerEl = document.getElementById("process-visible-fields-container");
  const addButtonEl = document.getElementById("process-field-add-btn");
  const formEl = processFieldsBuilderEl.closest("form");
  if (!containerEl || !addButtonEl || !formEl) {
    return;
  }

  function renderFieldOptions(selectedKey) {
    return fieldOptions
      .map((option) => {
        const optionKey = String(option.key || "");
        const optionLabel = String(option.label || optionKey);
        const isSelected = optionKey === String(selectedKey || "");
        return `<option value="${optionKey}"${isSelected ? " selected" : ""}>${optionLabel}</option>`;
      })
      .join("");
  }

  function renderHeaderOptions(selectedKey) {
    const cleanSelectedKey = String(selectedKey || "").trim();
    const optionsHtml = headerOptions
      .map((option) => {
        const optionKey = String(option.key || "");
        const optionLabel = String(option.label || optionKey);
        const isSelected = optionKey === cleanSelectedKey;
        return `<option value="${optionKey}"${isSelected ? " selected" : ""}>${optionLabel}</option>`;
      })
      .join("");
    return `<option value="">Sem cabeçalho</option>${optionsHtml}`;
  }

  function updateRemoveButtonsState() {
    const removeButtons = containerEl.querySelectorAll(".process-field-remove-btn");
    const isSingleRow = removeButtons.length <= 1;
    removeButtons.forEach((button) => {
      button.disabled = isSingleRow;
      button.classList.toggle("table-icon-btn-disabled", isSingleRow);
      button.setAttribute(
        "title",
        isSingleRow ? "É necessário manter pelo menos um campo" : "Remover campo"
      );
      button.setAttribute(
        "aria-label",
        isSingleRow ? "É necessário manter pelo menos um campo" : "Remover campo"
      );
    });
  }

  function bindRemoveButton(buttonEl) {
    buttonEl.addEventListener("click", () => {
      const rows = containerEl.querySelectorAll(".process-field-row");
      if (rows.length <= 1) {
        updateRemoveButtonsState();
        return;
      }
      const rowEl = buttonEl.closest(".process-field-row");
      if (rowEl) {
        rowEl.remove();
      }
      updateRemoveButtonsState();
    });
  }

  function createFieldRow(selectedKey, selectedHeaderKey) {
    const rowEl = document.createElement("div");
    rowEl.className = "process-field-row";
    rowEl.innerHTML = `
      <div class="field">
        <label>Campo</label>
        <select name="visible_fields" class="process-field-select">
          ${renderFieldOptions(selectedKey || fieldOptions[0].key)}
        </select>
      </div>
      <div class="field">
        <label>Cabeçalho</label>
        <select name="visible_headers" class="process-field-header-select">
          ${renderHeaderOptions(selectedHeaderKey || "")}
        </select>
      </div>
      <button
        type="button"
        class="table-icon-btn table-icon-btn-danger process-field-remove-btn"
        title="Remover campo"
        aria-label="Remover campo"
      >
        &#10005;
      </button>
    `;
    const removeButtonEl = rowEl.querySelector(".process-field-remove-btn");
    if (removeButtonEl) {
      bindRemoveButton(removeButtonEl);
    }
    return rowEl;
  }

  containerEl.querySelectorAll(".process-field-remove-btn").forEach((buttonEl) => {
    bindRemoveButton(buttonEl);
  });

  addButtonEl.addEventListener("click", () => {
    containerEl.appendChild(createFieldRow(fieldOptions[0].key, ""));
    updateRemoveButtonsState();
  });

  formEl.addEventListener("submit", () => {
    const seenFieldKeys = new Set();
    const selects = containerEl.querySelectorAll("select[name='visible_fields']");
    selects.forEach((selectEl) => {
      const cleanValue = String(selectEl.value || "").trim();
      if (!cleanValue || seenFieldKeys.has(cleanValue)) {
        selectEl.removeAttribute("name");
        const rowEl = selectEl.closest(".process-field-row");
        if (rowEl) {
          const headerSelectEl = rowEl.querySelector("select[name='visible_headers']");
          if (headerSelectEl) {
            headerSelectEl.removeAttribute("name");
          }
        }
        return;
      }
      seenFieldKeys.add(cleanValue);
    });
  });

  if (!containerEl.querySelector(".process-field-row")) {
    containerEl.appendChild(createFieldRow(fieldOptions[0].key, ""));
  }
  if (fieldOptions.length <= 1) {
    addButtonEl.disabled = true;
    addButtonEl.classList.add("table-icon-btn-disabled");
    addButtonEl.setAttribute("title", "Não há mais campos para adicionar");
    addButtonEl.setAttribute("aria-label", "Não há mais campos para adicionar");
  }
  updateRemoveButtonsState();
}

function setupProcessAdditionalFieldsBuilder() {
  const builderEl = document.getElementById("process-additional-fields-builder");
  if (!builderEl) {
    return;
  }

  const fieldTypesRaw = builderEl.getAttribute("data-field-types") || "[]";
  let fieldTypes = [];
  try {
    fieldTypes = JSON.parse(fieldTypesRaw);
  } catch (error) {
    fieldTypes = [];
  }
  if (!Array.isArray(fieldTypes) || !fieldTypes.length) {
    fieldTypes = [
      { key: "text", label: "Texto" },
      { key: "number", label: "Número" },
      { key: "email", label: "Email" },
      { key: "phone", label: "Telefone" },
      { key: "date", label: "Data" },
      { key: "flag", label: "Flag" }
    ];
  }

  const containerEl = document.getElementById("process-additional-fields-container");
  const addButtonEl = document.getElementById("process-additional-field-add-btn");
  const formEl = builderEl.closest("form");
  const moveFormEl = document.getElementById("process-additional-field-move-form");
  const limiterEl = document.getElementById("process-additional-fields-limiter");
  const pageSizeEl = document.getElementById("process-additional-fields-page-size");
  const prevEl = document.getElementById("process-additional-fields-prev");
  const nextEl = document.getElementById("process-additional-fields-next");
  const pageEl = document.getElementById("process-additional-fields-page");
  if (!containerEl || !addButtonEl || !formEl) {
    return;
  }

  const sizedTypes = new Set(["text", "number", "email", "phone"]);
  let additionalFieldsPageSize = Number.parseInt(pageSizeEl ? pageSizeEl.value : "5", 10) || 5;
  let additionalFieldsCurrentPage = 1;

  function renderTypeOptions(selectedType) {
    return fieldTypes
      .map((item) => {
        const optionKey = String(item.key || "");
        const optionLabel = String(item.label || optionKey);
        const isSelected = optionKey === String(selectedType || "text");
        return `<option value="${optionKey}"${isSelected ? " selected" : ""}>${optionLabel}</option>`;
      })
      .join("");
  }

  function syncRowState(rowEl) {
    const typeSelectEl = rowEl.querySelector("select[name='additional_field_type']");
    const requiredSelectEl = rowEl.querySelector("select[name='additional_field_required']");
    const sizeInputEl = rowEl.querySelector("input[name='additional_field_size']");
    if (!typeSelectEl || !sizeInputEl) {
      return;
    }
    const cleanType = String(typeSelectEl.value || "text").trim().toLowerCase();
    if (cleanType === "header" && requiredSelectEl) {
      requiredSelectEl.value = "0";
    }
    rowEl.classList.toggle("process-additional-field-row-header", cleanType === "header");
    const isSizeEnabled = sizedTypes.has(cleanType);
    if (isSizeEnabled) {
      sizeInputEl.readOnly = false;
      sizeInputEl.classList.remove("process-additional-size-readonly");
      if (!String(sizeInputEl.value || "").trim()) {
        sizeInputEl.value = "30";
      }
    } else {
      sizeInputEl.value = "";
      sizeInputEl.readOnly = true;
      sizeInputEl.classList.add("process-additional-size-readonly");
    }
  }

  function renderAdditionalFieldsPagination() {
    if (!limiterEl || !pageSizeEl || !prevEl || !nextEl || !pageEl) {
      return;
    }

    const rowEls = Array.from(containerEl.querySelectorAll(".process-additional-field-row"));
    if (!rowEls.length) {
      limiterEl.style.display = "none";
      return;
    }

    const totalPages = Math.max(1, Math.ceil(rowEls.length / additionalFieldsPageSize));
    if (additionalFieldsCurrentPage > totalPages) {
      additionalFieldsCurrentPage = totalPages;
    }

    const start = (additionalFieldsCurrentPage - 1) * additionalFieldsPageSize;
    const end = start + additionalFieldsPageSize;

    rowEls.forEach((rowEl, index) => {
      rowEl.style.display = index >= start && index < end ? "" : "none";
    });

    pageEl.textContent = String(additionalFieldsCurrentPage);
    prevEl.disabled = additionalFieldsCurrentPage <= 1;
    nextEl.disabled = additionalFieldsCurrentPage >= totalPages;
    limiterEl.style.display = rowEls.length > additionalFieldsPageSize ? "flex" : "none";
  }

  function bindRemoveButton(buttonEl) {
    buttonEl.addEventListener("click", () => {
      const rowEl = buttonEl.closest(".process-additional-field-row");
      if (rowEl) {
        rowEl.remove();
        renderAdditionalFieldsPagination();
      }
    });
  }

  function submitMoveRequest(buttonEl) {
    if (!moveFormEl || !buttonEl) {
      return;
    }

    const menuKey = String(buttonEl.getAttribute("data-menu-key") || "").trim();
    const fieldKey = String(buttonEl.getAttribute("data-field-key") || "").trim();
    const direction = String(buttonEl.getAttribute("data-move-direction") || "").trim().toLowerCase();
    const redirectMenu = String(buttonEl.getAttribute("data-redirect-menu") || "").trim();
    const redirectTarget = String(buttonEl.getAttribute("data-redirect-target") || "#settings-menu-edit-card").trim();

    if (!menuKey || !fieldKey || (direction !== "up" && direction !== "down")) {
      return;
    }

    const menuKeyEl = moveFormEl.querySelector('input[name="menu_key"]');
    const fieldKeyEl = moveFormEl.querySelector('input[name="field_key"]');
    const directionEl = moveFormEl.querySelector('input[name="direction"]');
    const redirectMenuEl = moveFormEl.querySelector('input[name="redirect_menu"]');
    const redirectTargetEl = moveFormEl.querySelector('input[name="redirect_target"]');

    if (!menuKeyEl || !fieldKeyEl || !directionEl || !redirectMenuEl || !redirectTargetEl) {
      return;
    }

    menuKeyEl.value = menuKey;
    fieldKeyEl.value = fieldKey;
    directionEl.value = direction;
    redirectMenuEl.value = redirectMenu;
    redirectTargetEl.value = redirectTarget;

    moveFormEl.submit();
  }

  function bindRow(rowEl) {
    const removeButtonEl = rowEl.querySelector(".process-additional-field-remove-btn");
    if (removeButtonEl) {
      bindRemoveButton(removeButtonEl);
    }
    rowEl.querySelectorAll(".process-additional-field-move-btn").forEach((buttonEl) => {
      if (buttonEl.dataset.moveBound === "1") {
        return;
      }
      buttonEl.dataset.moveBound = "1";
      buttonEl.addEventListener("click", () => {
        submitMoveRequest(buttonEl);
      });
    });
    const typeSelectEl = rowEl.querySelector("select[name='additional_field_type']");
    if (typeSelectEl) {
      typeSelectEl.addEventListener("change", () => {
        syncRowState(rowEl);
      });
    }
    syncRowState(rowEl);
  }

  function createAdditionalFieldRow(initialValue, initialType, initialRequired, initialSize) {
    const rowEl = document.createElement("div");
    rowEl.className = "process-field-row process-additional-field-row";
    rowEl.innerHTML = `
      <input type="hidden" name="additional_field_key" value="">
      <div class="field">
        <label>Nome do campo adicional</label>
        <input
          type="text"
          name="additional_field_label"
          maxlength="80"
          placeholder="Ex.: Data de batismo"
          value="${String(initialValue || "").replace(/"/g, "&quot;")}"
        >
      </div>
      <div class="field">
        <label>Tipo do campo</label>
        <select name="additional_field_type" class="process-additional-field-type-select">
          ${renderTypeOptions(initialType || "text")}
        </select>
      </div>
      <div class="field">
        <label>Obrigatório</label>
        <select name="additional_field_required" class="process-additional-field-required-select">
          <option value="0"${String(initialRequired || "0") === "0" ? " selected" : ""}>Não</option>
          <option value="1"${String(initialRequired || "0") === "1" ? " selected" : ""}>Sim</option>
        </select>
      </div>
      <div class="field">
        <label>Tamanho</label>
        <input
          type="number"
          name="additional_field_size"
          class="process-additional-field-size-input"
          min="1"
          max="255"
          placeholder=""
          value="${String(initialSize || "")}"
        >
      </div>
      <button
        type="button"
        class="table-icon-btn table-icon-btn-danger process-additional-field-remove-btn"
        title="Remover campo adicional"
        aria-label="Remover campo adicional"
      >
        &#10005;
      </button>
    `;
    bindRow(rowEl);
    return rowEl;
  }

  containerEl.querySelectorAll(".process-additional-field-row").forEach((rowEl) => {
    bindRow(rowEl);
  });

  addButtonEl.addEventListener("click", () => {
    const rowEl = createAdditionalFieldRow("", "text", "0", "30");
    containerEl.appendChild(rowEl);
    const totalRows = containerEl.querySelectorAll(".process-additional-field-row").length;
    additionalFieldsCurrentPage = Math.max(1, Math.ceil(totalRows / additionalFieldsPageSize));
    renderAdditionalFieldsPagination();
    const inputEl = rowEl.querySelector("input[name='additional_field_label']");
    if (inputEl) {
      inputEl.focus();
    }
  });

  if (pageSizeEl && prevEl && nextEl && pageEl) {
    pageSizeEl.addEventListener("change", () => {
      additionalFieldsPageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
      additionalFieldsCurrentPage = 1;
      renderAdditionalFieldsPagination();
    });

    prevEl.addEventListener("click", () => {
      if (additionalFieldsCurrentPage <= 1) {
        return;
      }
      additionalFieldsCurrentPage -= 1;
      renderAdditionalFieldsPagination();
    });

    nextEl.addEventListener("click", () => {
      const rowCount = containerEl.querySelectorAll(".process-additional-field-row").length;
      const totalPages = Math.max(1, Math.ceil(rowCount / additionalFieldsPageSize));
      if (additionalFieldsCurrentPage >= totalPages) {
        return;
      }
      additionalFieldsCurrentPage += 1;
      renderAdditionalFieldsPagination();
    });
  }

  formEl.addEventListener("submit", () => {
    const rowEls = containerEl.querySelectorAll(".process-additional-field-row");
    rowEls.forEach((rowEl) => {
      const keyEl = rowEl.querySelector("input[name='additional_field_key']");
      const labelEl = rowEl.querySelector("input[name='additional_field_label']");
      const typeEl = rowEl.querySelector("select[name='additional_field_type']");
      const requiredEl = rowEl.querySelector("select[name='additional_field_required']");
      const sizeEl = rowEl.querySelector("input[name='additional_field_size']");
      if (!labelEl || !typeEl || !requiredEl || !sizeEl) {
        return;
      }
      const cleanLabel = String(labelEl.value || "").trim();
      labelEl.value = cleanLabel;
      const cleanType = String(typeEl.value || "text").trim().toLowerCase();
      if (cleanType === "header") {
        requiredEl.value = "0";
      }
      const isSizeEnabled = sizedTypes.has(cleanType);
      if (!isSizeEnabled) {
        sizeEl.value = "";
      }

      if (!cleanLabel) {
        if (keyEl) {
          keyEl.removeAttribute("name");
        }
        labelEl.removeAttribute("name");
        typeEl.removeAttribute("name");
        requiredEl.removeAttribute("name");
        sizeEl.removeAttribute("name");
      }
    });
  });

  renderAdditionalFieldsPagination();
}

function setupProcessAdditionalFieldsManagerV2() {
  const builderEl = document.getElementById("process-additional-fields-builder");
  const formEl = builderEl ? builderEl.closest("form[data-additional-fields-manager-v2='1']") : null;
  if (!builderEl || !formEl) {
    return;
  }
  if (builderEl.dataset.additionalFieldsManagerV2Bound === "1") {
    return;
  }

  const containerEl = document.getElementById("process-additional-fields-container");
  const editorKeyEl = document.getElementById("process-additional-field-editor-key");
  const editorLabelEl = document.getElementById("process-additional-field-editor-label");
  const editorTypeEl = document.getElementById("process-additional-field-editor-type");
  const editorRequiredEl = document.getElementById("process-additional-field-editor-required");
  const editorSizeFieldEl = document.getElementById("process-additional-field-editor-size-field");
  const editorSizeEl = document.getElementById("process-additional-field-editor-size");
  const editorListFieldEl = document.getElementById("process-additional-field-editor-list-field");
  const editorListKeyEl = document.getElementById("process-additional-field-editor-list-key");
  const feedbackEl = document.getElementById("process-additional-field-editor-feedback");
  const addButtonEl = document.getElementById("process-additional-field-add-btn");
  const clearButtonEl = document.getElementById("process-additional-field-clear-btn");
  const tableBodyEl = document.getElementById("process-additional-fields-created-body");
  const emptyEl = document.getElementById("process-additional-fields-empty");
  const limiterEl = document.getElementById("process-additional-fields-limiter");
  const pageSizeEl = document.getElementById("process-additional-fields-page-size");
  const prevEl = document.getElementById("process-additional-fields-prev");
  const nextEl = document.getElementById("process-additional-fields-next");
  const pageEl = document.getElementById("process-additional-fields-page");
  const fieldTypesRaw = builderEl.getAttribute("data-field-types") || "[]";
  const processListsRaw = builderEl.getAttribute("data-process-lists") || "[]";

  if (
    !containerEl ||
    !editorKeyEl ||
    !editorLabelEl ||
    !editorTypeEl ||
    !editorRequiredEl ||
    !editorSizeFieldEl ||
    !editorSizeEl ||
    !editorListFieldEl ||
    !editorListKeyEl ||
    !feedbackEl ||
    !addButtonEl ||
    !clearButtonEl ||
    !tableBodyEl ||
    !emptyEl ||
    !limiterEl ||
    !pageSizeEl ||
    !prevEl ||
    !nextEl ||
    !pageEl
  ) {
    return;
  }

  let fieldTypes = [];
  let processLists = [];
  let tempIndex = 1;
  let currentPage = 1;
  let pageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
  const sizedTypes = new Set(["text", "number", "email", "phone"]);

  try {
    fieldTypes = JSON.parse(fieldTypesRaw);
  } catch (_error) {
    fieldTypes = [];
  }
  try {
    processLists = JSON.parse(processListsRaw);
  } catch (_error) {
    processLists = [];
  }

  const typeLabelByKey = new Map(
    (Array.isArray(fieldTypes) ? fieldTypes : []).map((item) => [
      String(item.key || "").trim().toLowerCase(),
      String(item.label || item.key || "").trim()
    ])
  );
  typeLabelByKey.set("list", "Lista");

  function normalizeKey(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function getListLabel(listKey) {
    const cleanListKey = normalizeKey(listKey);
    const matched = (Array.isArray(processLists) ? processLists : []).find((item) => {
      return normalizeKey(item.key) === cleanListKey;
    });
    return matched ? String(matched.label || matched.key || "-") : "-";
  }

  function syncEditorState() {
    const cleanType = String(editorTypeEl.value || "text").trim().toLowerCase();
    const isHeader = cleanType === "header";
    const isList = cleanType === "list";
    const sizeEnabled = sizedTypes.has(cleanType);

    editorRequiredEl.disabled = isHeader;
    if (isHeader) {
      editorRequiredEl.value = "0";
    }

    editorSizeFieldEl.style.display = sizeEnabled ? "" : "none";
    editorSizeEl.readOnly = !sizeEnabled;
    editorSizeEl.classList.toggle("process-additional-size-readonly", !sizeEnabled);
    if (!sizeEnabled) {
      editorSizeEl.value = "";
    } else if (!String(editorSizeEl.value || "").trim()) {
      editorSizeEl.value = "30";
    }

    editorListFieldEl.style.display = isList ? "" : "none";
    editorListKeyEl.disabled = !isList;
    if (!isList) {
      editorListKeyEl.value = "";
    }
  }

  function setEditorFeedback(message, type = "error") {
    feedbackEl.textContent = String(message || "").trim();
    feedbackEl.style.display = feedbackEl.textContent ? "" : "none";
    feedbackEl.classList.toggle("error", type === "error");
    feedbackEl.classList.toggle("ok", type === "ok");
  }

  function clearEditor() {
    editorKeyEl.value = "";
    editorLabelEl.value = "";
    editorTypeEl.value = "text";
    editorRequiredEl.value = "0";
    editorSizeEl.value = "30";
    editorListKeyEl.value = "";
    addButtonEl.textContent = "Guardar";
    setEditorFeedback("");
    syncEditorState();
  }

  function readStoreRow(rowEl) {
    const keyEl = rowEl.querySelector("input[name='additional_field_key']");
    const labelEl = rowEl.querySelector("input[name='additional_field_label']");
    const typeEl = rowEl.querySelector("select[name='additional_field_type'], input[name='additional_field_type']");
    const requiredEl = rowEl.querySelector("select[name='additional_field_required'], input[name='additional_field_required']");
    const sizeEl = rowEl.querySelector("input[name='additional_field_size']");
    const listKeyEl = rowEl.querySelector("select[name='additional_field_list_key'], input[name='additional_field_list_key']");
    if (!labelEl || !typeEl || !requiredEl || !sizeEl) {
      return null;
    }

    return {
      key: String(keyEl ? keyEl.value : rowEl.getAttribute("data-field-key") || "").trim(),
      label: String(labelEl.value || "").trim(),
      fieldType: String(typeEl.value || "text").trim().toLowerCase(),
      isRequired: String(requiredEl.value || "0").trim() === "1",
      size: String(sizeEl.value || "").trim(),
      listKey: String(listKeyEl ? listKeyEl.value : "").trim()
    };
  }

  function readStoreRows() {
    return Array.from(containerEl.children)
      .map((rowEl) => readStoreRow(rowEl))
      .filter((row) => row && row.label);
  }

  function createHiddenInput(name, value) {
    const inputEl = document.createElement("input");
    inputEl.type = "hidden";
    inputEl.name = name;
    inputEl.value = String(value || "");
    return inputEl;
  }

  function buildStoreRow(fieldData) {
    const rowEl = document.createElement("div");
    rowEl.className = "process-additional-field-store-row";
    rowEl.setAttribute("data-field-key", fieldData.key);
    rowEl.appendChild(createHiddenInput("additional_field_key", fieldData.key));
    rowEl.appendChild(createHiddenInput("additional_field_label", fieldData.label));
    rowEl.appendChild(createHiddenInput("additional_field_type", fieldData.fieldType));
    rowEl.appendChild(createHiddenInput("additional_field_required", fieldData.isRequired ? "1" : "0"));
    rowEl.appendChild(createHiddenInput("additional_field_size", fieldData.size || ""));
    rowEl.appendChild(createHiddenInput("additional_field_list_key", fieldData.listKey || ""));
    return rowEl;
  }

  function removeStoreRow(fieldKey) {
    const rowEl = Array.from(containerEl.children).find((item) => {
      return String(item.getAttribute("data-field-key") || "").trim() === String(fieldKey || "").trim();
    });
    if (rowEl) {
      rowEl.remove();
    }
  }

  function upsertStoreRow(fieldData) {
    const existingRowEl = Array.from(containerEl.children).find((item) => {
      return String(item.getAttribute("data-field-key") || "").trim() === String(fieldData.key || "").trim();
    });
    const nextSiblingEl = existingRowEl ? existingRowEl.nextSibling : null;

    removeStoreRow(fieldData.key);

    const newRowEl = buildStoreRow(fieldData);
    if (nextSiblingEl) {
      containerEl.insertBefore(newRowEl, nextSiblingEl);
    } else {
      containerEl.appendChild(newRowEl);
    }
  }

  function buildPayloadFromEditor() {
    const cleanLabel = String(editorLabelEl.value || "").trim();
    if (!cleanLabel) {
      setEditorFeedback("Informe o nome do campo adicional.");
      editorLabelEl.focus();
      return null;
    }

    const cleanType = String(editorTypeEl.value || "text").trim().toLowerCase();
    const cleanKey = String(editorKeyEl.value || "").trim() || `tmp_${normalizeKey(cleanLabel) || "campo"}_${tempIndex++}`;
    const duplicateLabel = readStoreRows().some((row) => {
      return row.key !== cleanKey && String(row.label || "").trim().toLowerCase() === cleanLabel.toLowerCase();
    });
    if (duplicateLabel) {
      setEditorFeedback("Já existe um campo adicional com esse nome.");
      editorLabelEl.focus();
      return null;
    }

    return {
      key: cleanKey,
      label: cleanLabel,
      fieldType: cleanType,
      isRequired: cleanType === "header" ? false : String(editorRequiredEl.value || "0") === "1",
      size: sizedTypes.has(cleanType) ? String(editorSizeEl.value || "").trim() || "30" : "",
      listKey: cleanType === "list" ? String(editorListKeyEl.value || "").trim() : ""
    };
  }

  function fillEditor(fieldData) {
    editorKeyEl.value = fieldData.key;
    editorLabelEl.value = fieldData.label;
    editorTypeEl.value = fieldData.fieldType || "text";
    editorRequiredEl.value = fieldData.isRequired ? "1" : "0";
    editorSizeEl.value = fieldData.size || "30";
    editorListKeyEl.value = fieldData.listKey || "";
    addButtonEl.textContent = "Atualizar campo";
    syncEditorState();
    editorLabelEl.focus();
  }

  function moveStoreRow(fieldKey, direction) {
    const rowEls = Array.from(containerEl.children);
    const currentIndex = rowEls.findIndex((rowEl) => {
      return String(rowEl.getAttribute("data-field-key") || "").trim() === String(fieldKey || "").trim();
    });
    const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
    if (currentIndex < 0 || targetIndex < 0 || targetIndex >= rowEls.length) {
      return;
    }
    const currentRowEl = rowEls[currentIndex];
    const targetRowEl = rowEls[targetIndex];
    if (direction === "up") {
      containerEl.insertBefore(currentRowEl, targetRowEl);
    } else {
      containerEl.insertBefore(targetRowEl, currentRowEl);
    }
  }

  function renderPagination() {
    const rowEls = Array.from(tableBodyEl.querySelectorAll("tr"));
    if (!rowEls.length) {
      limiterEl.style.display = "none";
      return;
    }

    const totalPages = Math.max(1, Math.ceil(rowEls.length / pageSize));
    if (currentPage > totalPages) {
      currentPage = totalPages;
    }

    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;

    rowEls.forEach((rowEl, index) => {
      rowEl.style.display = index >= start && index < end ? "" : "none";
    });

    pageEl.textContent = String(currentPage);
    prevEl.disabled = currentPage <= 1;
    nextEl.disabled = currentPage >= totalPages;
    limiterEl.style.display = rowEls.length > pageSize ? "flex" : "none";
  }

  function renderTable() {
    const rows = readStoreRows();
    tableBodyEl.innerHTML = "";

    if (!rows.length) {
      emptyEl.style.display = "";
      limiterEl.style.display = "none";
      return;
    }

    emptyEl.style.display = "none";
    rows.forEach((row) => {
      const trEl = document.createElement("tr");
      trEl.setAttribute("data-field-key", row.key);
      trEl.innerHTML = [
        `<td>${escapeHtml(row.label)}</td>`,
        `<td>${escapeHtml(typeLabelByKey.get(row.fieldType) || row.fieldType || "-")}</td>`,
        `<td>${row.isRequired ? "Sim" : "Não"}</td>`,
        `<td>${escapeHtml(row.size || "-")}</td>`,
        `<td>${escapeHtml(row.fieldType === "list" ? getListLabel(row.listKey) : "-")}</td>`,
        '<td><div class="table-actions">',
        '<button type="button" class="table-icon-btn" data-additional-field-action="edit" title="Modificar campo" aria-label="Modificar campo">&#9998;</button>',
        '<button type="button" class="table-icon-btn" data-additional-field-action="up" title="Mover para cima" aria-label="Mover para cima">&#8593;</button>',
        '<button type="button" class="table-icon-btn" data-additional-field-action="down" title="Mover para baixo" aria-label="Mover para baixo">&#8595;</button>',
        '<button type="button" class="table-icon-btn table-icon-btn-danger" data-additional-field-action="delete" title="Remover campo" aria-label="Remover campo">&#128465;</button>',
        "</div></td>"
      ].join("");
      tableBodyEl.appendChild(trEl);
    });

    renderPagination();
  }

  function handleAddAdditionalFieldV2() {
    const payload = buildPayloadFromEditor();
    if (!payload) {
      return;
    }
    upsertStoreRow(payload);
    clearEditor();
    setEditorFeedback("Campo adicional preparado para guardar.", "ok");
    currentPage = Math.max(1, Math.ceil(readStoreRows().length / pageSize));
    renderTable();
  }

  function handleClearAdditionalFieldV2() {
    clearEditor();
  }

  addButtonEl.addEventListener("click", handleAddAdditionalFieldV2);
  clearButtonEl.addEventListener("click", handleClearAdditionalFieldV2);
  window.__appgenesisAddAdditionalFieldV2 = handleAddAdditionalFieldV2;
  window.__appgenesisClearAdditionalFieldV2 = handleClearAdditionalFieldV2;

  editorTypeEl.addEventListener("change", () => {
    syncEditorState();
  });

  pageSizeEl.addEventListener("change", () => {
    pageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
    currentPage = 1;
    renderPagination();
  });

  prevEl.addEventListener("click", () => {
    if (currentPage <= 1) {
      return;
    }
    currentPage -= 1;
    renderPagination();
  });

  nextEl.addEventListener("click", () => {
    const totalPages = Math.max(1, Math.ceil(tableBodyEl.querySelectorAll("tr").length / pageSize));
    if (currentPage >= totalPages) {
      return;
    }
    currentPage += 1;
    renderPagination();
  });

  tableBodyEl.addEventListener("click", (event) => {
    const actionBtn = event.target.closest("[data-additional-field-action]");
    if (!actionBtn) {
      return;
    }

    const action = String(actionBtn.getAttribute("data-additional-field-action") || "").trim();
    const rowEl = actionBtn.closest("tr[data-field-key]");
    const fieldKey = String(rowEl ? rowEl.getAttribute("data-field-key") || "" : "").trim();
    const fieldData = readStoreRows().find((row) => row.key === fieldKey);
    if (!action || !fieldKey || !fieldData) {
      return;
    }

    if (action === "edit") {
      fillEditor(fieldData);
      return;
    }
    if (action === "delete") {
      removeStoreRow(fieldKey);
      if (String(editorKeyEl.value || "").trim() === fieldKey) {
        clearEditor();
      }
      renderTable();
      return;
    }
    if (action === "up" || action === "down") {
      moveStoreRow(fieldKey, action);
      renderTable();
    }
  });

  formEl.addEventListener("submit", () => {
    if (String(editorLabelEl.value || "").trim()) {
      const payload = buildPayloadFromEditor();
      if (payload) {
        upsertStoreRow(payload);
      }
    }
  });

  clearEditor();
  renderTable();
  builderEl.dataset.additionalFieldsManagerV2Bound = "1";
}

function normalizeProcessEditTabKey_v1(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/_/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

// A URL nao e atualizada quando o utilizador clica numa aba interna (ver abaixo), por isso
// window.location fica parado na aba de entrada (ex.: "geral"). O mecanismo global de
// post-save-context (linha ~8194) captura essa URL parada no momento do submit e usa-a para
// reconstruir o destino apos o redirect do servidor, sobrepondo-se ao settings_tab correto
// que o backend ja devolve. Sincronizar aqui evita que essa aba fique presa em "geral".
function syncProcessEditTabToUrl_v1(tabKey) {
  if (settingsAction !== "edit" || !settingsEditKey) {
    return;
  }
  try {
    const url = new URL(window.location.href);
    if (normalizeProcessEditTabKey_v1(url.searchParams.get("settings_tab")) === tabKey) {
      return;
    }
    url.searchParams.set("settings_tab", tabKey);
    const newHref = url.pathname + url.search + url.hash;
    logAppGenesisProcessEditorDebugV1("syncProcessEditTabToUrl_v1:history.replaceState", {
      previousHref: window.location.href,
      newHref,
      tabKey,
      caller: "syncProcessEditTabToUrl_v1"
    });
    window.history.replaceState(window.history.state, document.title, newHref);
  } catch (error) {
    // Ignorar falha ao sincronizar o URL da aba ativa; a navegacao normal continua a funcionar.
  }
}

function setupProcessEditTabs() {
  const tabLinks = document.querySelectorAll("[data-process-edit-tab]");
  const panes = document.querySelectorAll("[data-process-edit-pane]");
  if (!tabLinks.length || !panes.length) {
    return;
  }

  function activateProcessTab(tabKey) {
    const normalizedTabKey = normalizeProcessEditTabKey_v1(tabKey);
    const hasTargetTab = Array.from(tabLinks).some(
      (tabLink) => (tabLink.getAttribute("data-process-edit-tab") || "") === normalizedTabKey
    );
    const resolvedTabKey = hasTargetTab ? normalizedTabKey : "geral";
    tabLinks.forEach((tabLink) => {
      const isActive = tabLink.getAttribute("data-process-edit-tab") === resolvedTabKey;
      tabLink.classList.toggle("active", isActive);
      tabLink.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    panes.forEach((pane) => {
      const isActive = pane.getAttribute("data-process-edit-pane") === resolvedTabKey;
      pane.classList.toggle("active", isActive);
    });
    logAppGenesisProcessEditorDebugV1("setupProcessEditTabs:activateProcessTab", {
      requestedTabKey: tabKey,
      resolvedTabKey,
      href: window.location.href
    });
    return resolvedTabKey;
  }

  tabLinks.forEach((tabLink) => {
    tabLink.addEventListener("click", (event) => {
      event.preventDefault();
      const tabKey = tabLink.getAttribute("data-process-edit-tab") || "geral";
      const resolvedTabKey = activateProcessTab(tabKey);
      syncProcessEditTabToUrl_v1(resolvedTabKey);
    });
  });

  if (settingsAction === "edit") {
    const urlSettingsTab = normalizeProcessEditTabKey_v1(
      new URLSearchParams(window.location.search).get("settings_tab")
    );
    const cleanSettingsTab = String(settingsTab || "").trim() || urlSettingsTab;
    if (cleanSettingsTab) {
      activateProcessTab(cleanSettingsTab);
    } else {
      activateProcessTab("campos-config");
    }
  } else {
    activateProcessTab("geral");
  }
}
