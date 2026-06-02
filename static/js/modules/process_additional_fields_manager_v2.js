//###################################################################################
// (1) PROCESS ADDITIONAL FIELDS MANAGER V2 - LEGACY FALLBACK
//###################################################################################
(function registerProcessAdditionalFieldsManagerV2() {
  "use strict";

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
    const sizedTypes = new Set(["text", "textarea", "number", "email", "phone"]);

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
        setEditorFeedback("Ja existe um campo adicional com esse nome.");
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
          `<td>${row.isRequired ? "Sim" : "Nao"}</td>`,
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
    window.__appverboAddAdditionalFieldV2 = handleAddAdditionalFieldV2;
    window.__appverboClearAdditionalFieldV2 = handleClearAdditionalFieldV2;

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

  window.setupProcessAdditionalFieldsManagerV2 = setupProcessAdditionalFieldsManagerV2;
})();
