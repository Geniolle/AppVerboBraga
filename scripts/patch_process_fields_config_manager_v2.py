from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
NEW_JS_PATH = ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v2.js"


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
# (3) CRIAR JS V2 DO GESTOR OFICIAL DE CONFIGURACAO DOS CAMPOS
####################################################################################

js_content = r'''//###################################################################################
// APPVERBOBRAGA - PROCESS FIELDS CONFIG MANAGER V2
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function toSafeString_v2(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function escapeHtml_v2(value) {
    return toSafeString_v2(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function normalizeText_v2(value) {
    return toSafeString_v2(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizeKey_v2(value) {
    return normalizeText_v2(value);
  }

  function isHeaderOption_v2(option) {
    if (!option || !toSafeString_v2(option.value).trim()) {
      return false;
    }

    const dataKind = normalizeText_v2(
      option.dataset.processConfigKind ||
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-process-config-kind") ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const optionText = normalizeText_v2(option.textContent);
    const optionValue = normalizeText_v2(option.value);

    return (
      dataKind === "header" ||
      optionText.includes("cabecalho") ||
      optionValue.includes("cabecalho")
    );
  }

  function cleanHeaderLabel_v2(label) {
    return toSafeString_v2(label)
      .replace(/\s*-\s*Cabeçalho\s*$/i, "")
      .replace(/\s*-\s*Cabecalho\s*$/i, "")
      .trim();
  }

  function createOption_v2(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value || "";
    option.textContent = label || "";

    if (toSafeString_v2(value) === toSafeString_v2(selectedValue)) {
      option.selected = true;
    }

    return option;
  }

  function createButton_v2(action, label, itemId, disabled) {
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
  // (2) LEITURA DO DOM
  //###################################################################################

  function getElements_v2(form) {
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

  function readHiddenValue_v2(row, selector) {
    const input = row.querySelector(selector);
    return input ? toSafeString_v2(input.value).trim() : "";
  }

  function getOriginalOptions_v2(elements) {
    return Array.from(elements.editorKey.options).map(function (option) {
      return {
        key: toSafeString_v2(option.value).trim(),
        label: cleanHeaderLabel_v2(
          toSafeString_v2(option.dataset.processConfigLabel || option.textContent).trim()
        ),
        kind: isHeaderOption_v2(option) ? "header" : "field"
      };
    }).filter(function (item) {
      return item.key;
    });
  }

  function getHeaderOptions_v2(originalOptions) {
    const seen = new Set();

    return originalOptions.filter(function (item) {
      if (item.kind !== "header" || seen.has(item.key)) {
        return false;
      }

      seen.add(item.key);
      return true;
    });
  }

  function getFieldOptions_v2(originalOptions) {
    const seen = new Set();

    return originalOptions.filter(function (item) {
      if (item.kind === "header" || seen.has(item.key)) {
        return false;
      }

      seen.add(item.key);
      return true;
    });
  }

  function getHeaderLabel_v2(headerOptions, headerKey) {
    const cleanHeaderKey = normalizeKey_v2(headerKey);
    const option = headerOptions.find(function (item) {
      return normalizeKey_v2(item.key) === cleanHeaderKey;
    });

    return option ? option.label : "";
  }

  function readInitialItems_v2(elements, headerOptions) {
    const rows = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-config-field-row]")
    );

    const items = [];
    let currentHeaderKey = "";
    let currentHeaderLabel = "";

    rows.forEach(function (row, index) {
      const key = readHiddenValue_v2(row, "[data-process-config-key]");
      const label = readHiddenValue_v2(row, "[data-process-config-label]") || key;
      const kind = readHiddenValue_v2(row, "[data-process-config-kind]") === "header" ? "header" : "field";

      if (!key) {
        return;
      }

      if (kind === "header") {
        currentHeaderKey = key;
        currentHeaderLabel = cleanHeaderLabel_v2(label);
        return;
      }

      items.push({
        managerId: "config_" + index + "_" + key,
        key: key,
        label: label,
        kind: "field",
        headerKey: currentHeaderKey,
        headerLabel: currentHeaderLabel || getHeaderLabel_v2(headerOptions, currentHeaderKey)
      });
    });

    return items;
  }

  //###################################################################################
  // (3) EDITOR - NOME DO CAMPO E CABECALHO DO CAMPO
  //###################################################################################

  function rebuildEditorFieldOptions_v2(elements, fieldOptions) {
    const currentValue = elements.editorKey.value;

    elements.editorKey.innerHTML = "";
    elements.editorKey.appendChild(createOption_v2("", "Selecione", ""));

    fieldOptions.forEach(function (item) {
      const option = createOption_v2(item.key, item.label, currentValue);
      option.dataset.processConfigKind = "field";
      option.dataset.processConfigLabel = item.label;
      elements.editorKey.appendChild(option);
    });
  }

  function buildHeaderSelect_v2(headerOptions) {
    const select = document.createElement("select");
    select.dataset.processFieldsConfigHeaderEditorV2 = "1";
    select.appendChild(createOption_v2("", "Sem cabeçalho", ""));

    headerOptions.forEach(function (item) {
      select.appendChild(createOption_v2(item.key, item.label, ""));
    });

    return select;
  }

  function ensureEditorHeaderSelect_v2(form, elements, headerOptions) {
    const existing = form.querySelector("[data-process-fields-config-header-editor-v2='1']");

    if (existing) {
      return existing;
    }

    const editorWrapper =
      elements.editorKey.closest(".field") ||
      elements.editorKey.closest(".form-field") ||
      elements.editorKey.parentElement;

    const row = document.createElement("div");
    row.className = "process-fields-config-editor-row-v2";

    const headerWrapper = document.createElement("div");
    headerWrapper.className = "process-fields-config-header-editor-v2";

    const label = document.createElement("label");
    label.textContent = "CABEÇALHO DO CAMPO";

    const select = buildHeaderSelect_v2(headerOptions);

    headerWrapper.appendChild(label);
    headerWrapper.appendChild(select);

    if (editorWrapper && editorWrapper.parentElement) {
      editorWrapper.parentElement.insertBefore(row, editorWrapper);
      row.appendChild(editorWrapper);
      row.appendChild(headerWrapper);
    }

    return select;
  }

  function renameEditorLabel_v2(form) {
    Array.from(form.querySelectorAll("label, th")).forEach(function (element) {
      const text = normalizeText_v2(element.textContent);

      if (text === "campo do processo") {
        element.textContent = "NOME DO CAMPO";
      }
    });
  }

  function clearEditor_v2(state, elements) {
    state.editingId = "";
    elements.editorKey.value = "";

    if (state.headerSelect) {
      state.headerSelect.value = "";
    }
  }

  function readOptionItem_v2(elements, state) {
    const option = elements.editorKey.options[elements.editorKey.selectedIndex];

    if (!option || !option.value) {
      return null;
    }

    const headerKey = toSafeString_v2(state.headerSelect ? state.headerSelect.value : "").trim();
    const headerLabel = getHeaderLabel_v2(state.headerOptions, headerKey);

    return {
      managerId: "tmp_" + Date.now() + "_" + option.value,
      key: toSafeString_v2(option.value).trim(),
      label: toSafeString_v2(option.dataset.processConfigLabel || option.textContent).trim(),
      kind: "field",
      headerKey: headerKey,
      headerLabel: headerLabel
    };
  }

  function loadEditor_v2(item, state, elements) {
    state.editingId = item.managerId;
    elements.editorKey.value = item.key || "";

    if (state.headerSelect) {
      state.headerSelect.value = item.headerKey || "";
    }

    elements.editorKey.focus();
  }

  function hasDraft_v2(elements, state) {
    return Boolean(state.editingId || elements.editorKey.value);
  }

  //###################################################################################
  // (4) VALIDACAO E SINCRONIZACAO COM BACKEND
  //###################################################################################

  function validateItem_v2(item, state) {
    if (!item || !item.key) {
      window.alert("Selecione um campo.");
      return false;
    }

    const duplicate = state.items.some(function (existing) {
      return existing.managerId !== item.managerId
        && normalizeKey_v2(existing.key) === normalizeKey_v2(item.key);
    });

    if (duplicate) {
      window.alert("Este campo já está configurado.");
      return false;
    }

    return true;
  }

  function syncHiddenInputs_v2(state, elements) {
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

  function addOrUpdateFromEditor_v2(state, elements) {
    const item = readOptionItem_v2(elements, state);

    if (!item) {
      return false;
    }

    if (state.editingId) {
      item.managerId = state.editingId;
    }

    if (!validateItem_v2(item, state)) {
      return false;
    }

    const index = state.items.findIndex(function (existing) {
      return existing.managerId === item.managerId;
    });

    if (index >= 0) {
      state.items[index] = item;
    } else {
      item.managerId = "tmp_" + Date.now() + "_" + item.key;
      state.items.push(item);
      state.page = Math.max(1, Math.ceil(state.items.length / state.pageSize));
    }

    clearEditor_v2(state, elements);
    return true;
  }

  //###################################################################################
  // (5) TABELA E PAGINACAO
  //###################################################################################

  function rewriteTableHead_v2(elements) {
    const headRow = elements.table.querySelector("thead tr");

    if (!headRow || headRow.dataset.processFieldsConfigHeaderV2 === "1") {
      return;
    }

    headRow.innerHTML = [
      "<th>NOME DO CAMPO</th>",
      "<th>CABEÇALHO DO CAMPO</th>",
      "<th>AÇÕES</th>"
    ].join("");

    headRow.dataset.processFieldsConfigHeaderV2 = "1";
  }

  function renderTable_v2(state, elements) {
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
        "<td>" + escapeHtml_v2(item.label || item.key) + "</td>",
        "<td>" + escapeHtml_v2(item.headerLabel || "Sem cabeçalho") + "</td>"
      ].join("");

      const actionsTd = document.createElement("td");
      const actionsWrap = document.createElement("div");

      actionsTd.className = "configurable-items-actions-cell-v1";
      actionsWrap.className = "configurable-items-actions-v1";

      actionsWrap.appendChild(createButton_v2("edit", "Editar", item.managerId, false));
      actionsWrap.appendChild(createButton_v2("up", "Subir", item.managerId, absoluteIndex === 0));
      actionsWrap.appendChild(createButton_v2("down", "Descer", item.managerId, absoluteIndex === totalItems - 1));
      actionsWrap.appendChild(createButton_v2("remove", "Remover", item.managerId, false));

      actionsTd.appendChild(actionsWrap);
      row.appendChild(actionsTd);
      elements.tableBody.appendChild(row);
    });

    elements.table.style.display = totalItems ? "" : "none";
    elements.emptyState.style.display = totalItems ? "none" : "";
    elements.totalLabel.textContent = totalItems + " " + (totalItems === 1 ? "campo" : "campos");

    renderPagination_v2(state, elements, totalPages);
  }

  function renderPagination_v2(state, elements, totalPages) {
    elements.pagination.innerHTML = "";

    const previousButton = document.createElement("button");
    previousButton.type = "button";
    previousButton.className = "table-limiter-nav-btn";
    previousButton.innerHTML = "&#8249;";
    previousButton.disabled = state.page <= 1;
    previousButton.addEventListener("click", function () {
      if (state.page > 1) {
        state.page -= 1;
        renderTable_v2(state, elements);
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
        renderTable_v2(state, elements);
      }
    });

    elements.pagination.appendChild(previousButton);
    elements.pagination.appendChild(pageLabel);
    elements.pagination.appendChild(nextButton);
  }

  //###################################################################################
  // (6) ACOES
  //###################################################################################

  function findItemIndex_v2(state, itemId) {
    return state.items.findIndex(function (item) {
      return item.managerId === itemId;
    });
  }

  function moveItem_v2(state, fromIndex, toIndex) {
    if (fromIndex < 0 || toIndex < 0 || fromIndex >= state.items.length || toIndex >= state.items.length) {
      return;
    }

    const item = state.items.splice(fromIndex, 1)[0];
    state.items.splice(toIndex, 0, item);
  }

  function bindEvents_v2(form, state, elements) {
    elements.submitButton.addEventListener("click", function (event) {
      event.preventDefault();

      if (hasDraft_v2(elements, state)) {
        const ok = addOrUpdateFromEditor_v2(state, elements);

        if (!ok) {
          return;
        }
      }

      syncHiddenInputs_v2(state, elements);

      if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
        return;
      }

      form.submit();
    });

    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      clearEditor_v2(state, elements);
    });

    elements.pageSize.addEventListener("change", function () {
      state.pageSize = Number.parseInt(elements.pageSize.value, 10) || 5;
      state.page = 1;
      renderTable_v2(state, elements);
    });

    elements.tableBody.addEventListener("click", function (event) {
      const button = event.target.closest("[data-process-fields-config-action]");

      if (!button) {
        return;
      }

      const action = button.dataset.processFieldsConfigAction;
      const itemId = button.dataset.processFieldsConfigItemId;
      const index = findItemIndex_v2(state, itemId);

      if (index < 0) {
        return;
      }

      if (action === "edit") {
        loadEditor_v2(state.items[index], state, elements);
        return;
      }

      if (action === "up") {
        moveItem_v2(state, index, index - 1);
      }

      if (action === "down") {
        moveItem_v2(state, index, index + 1);
      }

      if (action === "remove") {
        state.items.splice(index, 1);
      }

      renderTable_v2(state, elements);
      syncHiddenInputs_v2(state, elements);
    });

    form.addEventListener("submit", function () {
      syncHiddenInputs_v2(state, elements);
    });
  }

  //###################################################################################
  // (7) ESTILO
  //###################################################################################

  function injectStyle_v2() {
    if (document.getElementById("process-fields-config-manager-v2-style")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "process-fields-config-manager-v2-style";
    style.textContent = `
      .process-fields-config-editor-row-v2 {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
        gap: 12px;
        align-items: end;
        width: 100%;
      }

      .process-fields-config-editor-row-v2 > * {
        min-width: 0;
        width: 100%;
      }

      .process-fields-config-editor-row-v2 .field,
      .process-fields-config-header-editor-v2 {
        display: flex;
        flex-direction: column;
        gap: 6px;
        width: 100%;
        min-width: 0;
        margin: 0;
      }

      .process-fields-config-editor-row-v2 label,
      .process-fields-config-header-editor-v2 label {
        min-height: 14px;
        line-height: 14px;
        margin: 0;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
      }

      .process-fields-config-editor-row-v2 select,
      .process-fields-config-header-editor-v2 select {
        width: 100%;
        min-width: 0;
        max-width: 100%;
        height: 38px;
        min-height: 38px;
        box-sizing: border-box;
      }

      @media (max-width: 900px) {
        .process-fields-config-editor-row-v2 {
          grid-template-columns: 1fr;
        }
      }
    `;

    document.head.appendChild(style);
  }

  //###################################################################################
  // (8) INICIALIZACAO
  //###################################################################################

  function setupProcessFieldsConfigManager_v2(form) {
    if (!form || form.dataset.processFieldsConfigManagerBoundV2 === "1") {
      return;
    }

    const elements = getElements_v2(form);

    if (
      !elements.legacyContainer ||
      !elements.hiddenContainer ||
      !elements.editorKey ||
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

    injectStyle_v2();
    renameEditorLabel_v2(form);

    const originalOptions = getOriginalOptions_v2(elements);
    const headerOptions = getHeaderOptions_v2(originalOptions);
    const fieldOptions = getFieldOptions_v2(originalOptions);

    rebuildEditorFieldOptions_v2(elements, fieldOptions);

    const headerSelect = ensureEditorHeaderSelect_v2(form, elements, headerOptions);

    const state = {
      items: readInitialItems_v2(elements, headerOptions),
      headerOptions: headerOptions,
      headerSelect: headerSelect,
      page: 1,
      pageSize: Number.parseInt(elements.pageSize.value, 10) || 5,
      editingId: ""
    };

    form.dataset.processFieldsConfigManagerBoundV2 = "1";

    rewriteTableHead_v2(elements);
    bindEvents_v2(form, state, elements);
    syncHiddenInputs_v2(state, elements);
    renderTable_v2(state, elements);
  }

  function setupAllProcessFieldsConfigManagers_v2() {
    document
      .querySelectorAll("form[data-process-fields-config-manager-v1='1']")
      .forEach(setupProcessFieldsConfigManager_v2);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessFieldsConfigManagers_v2);
  } else {
    setupAllProcessFieldsConfigManagers_v2();
  }

  window.setTimeout(setupAllProcessFieldsConfigManagers_v2, 150);
  window.setTimeout(setupAllProcessFieldsConfigManagers_v2, 600);
})();
'''

NEW_JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: process_fields_config_manager_v2.js criado.")


####################################################################################
# (4) ATUALIZAR TEMPLATE
####################################################################################

template = template.replace("CAMPO DO PROCESSO", "NOME DO CAMPO")
template = template.replace("Campo do processo", "Nome do campo")
template = template.replace("campo do processo", "nome do campo")

# Remove gestores auxiliares antigos que estavam a competir com o gestor oficial.
for version in ["v1", "v2", "v3", "v4", "v5", "v6"]:
    template = re.sub(
        rf'\s*<script src="/static/js/modules/process_fields_header_manager_{version}\.js\?v=[^"]+"></script>',
        "",
        template,
    )

# Substitui o gestor oficial antigo pelo V2.
template = re.sub(
    r'/static/js/modules/process_fields_config_manager_v1\.js\?v=[^"]+',
    '/static/js/modules/process_fields_config_manager_v2.js?v=20260430-fields-config-v2',
    template,
)

if "process_fields_config_manager_v2.js" not in template:
    script_tag = '<script src="/static/js/modules/process_fields_config_manager_v2.js?v=20260430-fields-config-v2"></script>'
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

print("OK: new_user.html atualizado para carregar process_fields_config_manager_v2.js.")
print("OK: patch_process_fields_config_manager_v2 concluído.")
