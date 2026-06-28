//###################################################################################
// APPVERBO_STANDARD_LIST_PROCESS_V1_START
// Processo dinâmico listável com o mesmo padrão visual de Estruturas > Sessões.
//###################################################################################

(function initStandardListProcessV1() {
  "use strict";

  const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
  const settings = Array.isArray(bootstrap.sidebarMenuSettings) ? bootstrap.sidebarMenuSettings : [];
  const historyMap = bootstrap.menuProcessHistoryMap && typeof bootstrap.menuProcessHistoryMap === "object"
    ? bootstrap.menuProcessHistoryMap
    : {};
  const valuesMap = bootstrap.menuProcessValuesMap && typeof bootstrap.menuProcessValuesMap === "object"
    ? bootstrap.menuProcessValuesMap
    : {};

  const SYSTEM_OPTIONS = [
    ["all", "Default"],
    ["owner", "Owner"],
    ["legado", "Legado"]
  ];
  const STATUS_OPTIONS = [
    ["ativo", "Ativo"],
    ["inativo", "Inativo"]
  ];

  let activeStandardMenuKey = "";
  const selectedSectionByMenu = new Map();

  //###################################################################################
  // (1) NORMALIZAÇÃO E CONFIGURAÇÃO
  //###################################################################################

  function normalizeText(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[_-]+/g, " ")
      .replace(/\s+/g, " ");
  }

  function normalizeKey(value) {
    if (typeof window.normalizeMenuKey === "function") {
      return window.normalizeMenuKey(value);
    }

    return String(value || "").trim().toLowerCase();
  }

  function slug(value) {
    return normalizeText(value)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function toSentenceCase(value) {
    const cleanValue = String(value || "").trim();

    if (!cleanValue) {
      return "";
    }

    return cleanValue.charAt(0).toUpperCase() + cleanValue.slice(1);
  }

  function isTruthy(value) {
    if (value === true) {
      return true;
    }

    return ["1", "true", "sim", "yes", "on", "list"].includes(normalizeText(value));
  }

  function isStandardListProcess(setting) {
    if (!setting || typeof setting !== "object") {
      return false;
    }

    const explicitLayout = normalizeText(
      setting.process_layout ||
      setting.layout ||
      setting.processLayout ||
      setting.process_mode ||
      setting.processMode
    );

    if (["list", "lista", "standard list", "standard_list", "gestao", "gestão"].includes(explicitLayout)) {
      return true;
    }

    if (
      isTruthy(setting.is_list_process) ||
      isTruthy(setting.isListProcess) ||
      isTruthy(setting.standard_list_process) ||
      isTruthy(setting.standardListProcess)
    ) {
      return true;
    }

    const joined = [setting.key, setting.label, setting.title]
      .map(normalizeText)
      .filter(Boolean)
      .join(" ");

    return joined.includes("perfil") && joined.includes("autorizacao");
  }

  const standardSettings = settings.filter(isStandardListProcess);
  const standardSettingsByKey = new Map();

  standardSettings.forEach(function registerSetting(setting) {
    const menuKey = normalizeKey(setting.key);

    if (menuKey) {
      standardSettingsByKey.set(menuKey, setting);
    }
  });

  if (!standardSettingsByKey.size) {
    return;
  }

  function getStandardSetting(menuKey) {
    return standardSettingsByKey.get(normalizeKey(menuKey)) || null;
  }

  function buildListOptionsByKey(setting) {
    const result = new Map();
    const processLists = Array.isArray(setting.process_lists) ? setting.process_lists : [];

    processLists.forEach(function eachList(processList) {
      const listKey = normalizeKey(processList && processList.key);

      if (!listKey) {
        return;
      }

      result.set(
        listKey,
        Array.isArray(processList.items)
          ? processList.items.map(function itemToText(item) { return String(item || "").trim(); }).filter(Boolean)
          : []
      );
    });

    return result;
  }

  function buildFieldMetaByKey(setting) {
    const metaByKey = new Map();
    const listOptionsByKey = buildListOptionsByKey(setting);
    const options = Array.isArray(setting.process_field_options) ? setting.process_field_options : [];

    options.forEach(function eachOption(option) {
      const fieldKey = normalizeKey(option && option.key);

      if (!fieldKey) {
        return;
      }

      const fieldType = normalizeFieldType(option.field_type || option.fieldType);
      const listKey = normalizeKey(option.list_key || option.listKey);
      const isRequired = isTruthy(
        Object.prototype.hasOwnProperty.call(option, "is_required")
          ? option.is_required
          : option.required
      );

      metaByKey.set(fieldKey, {
        key: fieldKey,
        label: String(option.label || fieldKey).trim() || fieldKey,
        fieldType,
        isRequired: isRequired && fieldType !== "header",
        listKey,
        listOptions: listOptionsByKey.get(listKey) || [],
        size: Number.parseInt(String(option.size || "255"), 10) || 255
      });
    });

    return metaByKey;
  }

  function normalizeFieldType(value) {
    const fieldType = normalizeKey(value || "text");

    if (["text", "number", "email", "phone", "date", "flag", "list", "header"].includes(fieldType)) {
      return fieldType;
    }

    return "text";
  }

  function getFieldInputType(fieldType) {
    if (fieldType === "email") {
      return "email";
    }

    if (fieldType === "number") {
      return "number";
    }

    if (fieldType === "phone") {
      return "tel";
    }

    if (fieldType === "date") {
      return "date";
    }

    return "text";
  }

  function buildSections(setting) {
    const fieldMetaByKey = buildFieldMetaByKey(setting);
    const rows = Array.isArray(setting.process_visible_field_rows)
      ? setting.process_visible_field_rows
      : [];

    if (rows.length) {
      const sectionMap = new Map();
      const sectionOrder = [];
      let firstFieldKey = "";

      rows.forEach(function eachRow(row) {
        const fieldKey = normalizeKey(row && row.field_key);

        if (!fieldKey) {
          return;
        }

        const fieldMeta = fieldMetaByKey.get(fieldKey) || { key: fieldKey, label: fieldKey, fieldType: "text" };

        if (fieldMeta.fieldType === "header") {
          return;
        }

        if (!firstFieldKey) {
          firstFieldKey = fieldKey;
        }

        const headerKey = normalizeKey(row.header_key);
        const sectionKey = headerKey || "__geral__";

        if (!sectionMap.has(sectionKey)) {
          const headerMeta = fieldMetaByKey.get(sectionKey) || null;
          sectionMap.set(sectionKey, {
            key: sectionKey,
            label: headerKey ? String((headerMeta && headerMeta.label) || headerKey) : "Geral",
            fields: []
          });
          sectionOrder.push(sectionKey);
        }

        sectionMap.get(sectionKey).fields.push(fieldMeta);
      });

      const sections = sectionOrder
        .map(function byOrder(sectionKey) { return sectionMap.get(sectionKey); })
        .filter(function hasFields(section) { return section && section.fields.length; });

      if (sections.length === 1 && sections[0].key === "__geral__") {
        return sections[0].fields.map(function fieldAsSection(field) {
          return {
            key: "field:" + field.key,
            label: field.label,
            fields: [field]
          };
        });
      }

      return sections;
    }

    const visibleFields = Array.isArray(setting.process_visible_fields)
      ? setting.process_visible_fields.map(normalizeKey).filter(Boolean)
      : [];

    return visibleFields
      .map(function fieldKeyToSection(fieldKey) {
        const fieldMeta = fieldMetaByKey.get(fieldKey) || { key: fieldKey, label: fieldKey, fieldType: "text" };

        if (fieldMeta.fieldType === "header") {
          return null;
        }

        return {
          key: "field:" + fieldKey,
          label: fieldMeta.label,
          fields: [fieldMeta]
        };
      })
      .filter(Boolean);
  }

  function getSelectedSection(menuKey, setting) {
    const sections = buildSections(setting);

    if (!sections.length) {
      return null;
    }

    const requested = selectedSectionByMenu.get(menuKey) || String(bootstrap.initialDynamicProcessSection || "").trim();
    const selected = sections.find(function matchSection(section) {
      return String(section.key || "") === requested;
    });

    return selected || sections[0];
  }

  function pluralizeSingular(label) {
    const cleanLabel = normalizeText(label);

    if (cleanLabel === "perfil") {
      return "perfis";
    }

    if (cleanLabel.endsWith("l") && cleanLabel.length > 1) {
      return cleanLabel.slice(0, -1) + "is";
    }

    if (cleanLabel.endsWith("m")) {
      return cleanLabel.slice(0, -1) + "ns";
    }

    return cleanLabel ? cleanLabel + "s" : "registos";
  }

  function buildLabels(section) {
    const firstField = section && section.fields && section.fields[0]
      ? section.fields[0]
      : null;
    const singular = normalizeText(firstField && firstField.label) || "registo";
    const plural = pluralizeSingular(singular);

    return {
      singular,
      plural,
      create: "Criar " + singular,
      activeTitle: toSentenceCase(plural) + " ativos",
      inactiveTitle: toSentenceCase(plural) + " inativos",
      emptyActive: "Sem " + plural + " ativos.",
      emptyInactive: "Sem " + plural + " inativos."
    };
  }

  function getSystemLabel(value) {
    const cleanValue = normalizeKey(value || "all");

    if (cleanValue === "owner") {
      return "Owner";
    }

    if (cleanValue === "legado") {
      return "Legado";
    }

    return "Default";
  }

  function normalizeStatus(value) {
    const cleanValue = normalizeText(value || "ativo");

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValue)) {
      return "inativo";
    }

    return "ativo";
  }

  function getStatusLabel(value) {
    return normalizeStatus(value) === "inativo" ? "Inativo" : "Ativo";
  }

  //###################################################################################
  // (2) ESTRUTURA VISUAL STANDARD
  //###################################################################################

  function ensureRootStyles() {
    if (document.getElementById("standard-list-process-v1-style")) {
      return;
    }

    const styleEl = document.createElement("style");
    styleEl.id = "standard-list-process-v1-style";
    styleEl.textContent = `
      .standard-list-process-search-row-v1 {
        align-items: center;
        display: flex;
        justify-content: flex-end;
        margin: -8px 0 10px;
      }
      .standard-list-process-search-v1 {
        border: 1px solid #cdd7e6;
        border-radius: 999px;
        font-size: 13px;
        min-height: 32px;
        padding: 6px 12px;
        width: min(260px, 100%);
      }
      .standard-list-process-empty-row-v1 td {
        color: #5f6877;
        padding: 14px 12px;
      }
      .standard-list-process-action-v1 {
        align-items: center;
        background: transparent;
        border: 0;
        border-radius: 6px;
        color: #0a6ed1;
        cursor: pointer;
        display: inline-flex;
        font-size: 14px;
        font-weight: 800;
        justify-content: center;
        min-height: 28px;
        min-width: 28px;
        padding: 4px 6px;
      }
      .standard-list-process-action-v1:hover {
        background: #eef5ff;
      }
      .standard-list-process-pagination-v1 {
        align-items: center;
        display: grid;
        gap: 12px;
        grid-template-columns: 1fr auto 1fr;
        margin-top: 12px;
      }
      .standard-list-process-page-size-v1 {
        align-items: center;
        color: #5f6877;
        display: inline-flex;
        font-size: 13px;
        gap: 8px;
      }
      .standard-list-process-page-size-v1 select {
        border: 1px solid #d4ddeb;
        border-radius: 8px;
        min-height: 32px;
        padding: 4px 8px;
      }
      .standard-list-process-pages-v1 {
        color: #0a6ed1;
        font-size: 13px;
        font-weight: 800;
        justify-self: center;
      }
    `;
    document.head.appendChild(styleEl);
  }

  function getOrCreateSection(id, className, menuKey, afterEl) {
    let sectionEl = document.getElementById(id);

    if (!sectionEl) {
      sectionEl = document.createElement("section");
      sectionEl.id = id;
      if (afterEl && afterEl.parentNode) {
        afterEl.parentNode.insertBefore(sectionEl, afterEl.nextSibling);
      } else {
        document.querySelector(".container")?.appendChild(sectionEl);
      }
    }

    sectionEl.className = className;
    sectionEl.dataset.menuScope = menuKey;
    sectionEl.dataset.adminSubprocess = menuKey;
    sectionEl.dataset.standardListProcessV1 = "1";
    sectionEl.style.display = "none";
    return sectionEl;
  }

  function getProcessCardIds(menuKey) {
    const key = slug(menuKey);

    return {
      create: key + "-standard-create-card",
      active: key + "-standard-active-card",
      inactive: key + "-standard-inactive-card"
    };
  }

  function ensureCards(menuKey) {
    const ids = getProcessCardIds(menuKey);
    const anchor = document.getElementById("menu-tabs-card");
    const createCard = getOrCreateSection(
      ids.create,
      "card admin-subprocess-card-v1 admin-subprocess-form-card-v1 appverbo-process-action-card-v1 standard-list-process-create-card-v1",
      menuKey,
      anchor
    );
    const activeCard = getOrCreateSection(
      ids.active,
      "card admin-subprocess-card-v1 admin-subprocess-table-card-v1 standard-list-process-table-card-v1",
      menuKey,
      createCard
    );
    const inactiveCard = getOrCreateSection(
      ids.inactive,
      "card admin-subprocess-card-v1 admin-subprocess-table-card-v1 standard-list-process-table-card-v1",
      menuKey,
      activeCard
    );

    activeCard.dataset.adminSubprocessRole = "active-table";
    inactiveCard.dataset.adminSubprocessRole = "inactive-table";

    return { createCard, activeCard, inactiveCard, ids };
  }

  function buildFieldControl(field, value) {
    const fieldType = normalizeFieldType(field.fieldType);
    const inputName = "process_field__" + field.key;
    const fieldId = "standard_list_" + field.key + "_" + Math.random().toString(16).slice(2);
    const wrapEl = document.createElement("div");
    wrapEl.className = "field admin-subprocess-field-v1";

    const labelEl = document.createElement("label");
    labelEl.setAttribute("for", fieldId);
    labelEl.textContent = field.label + (field.isRequired ? " *" : "");
    wrapEl.appendChild(labelEl);

    let controlEl = null;

    if (fieldType === "list") {
      controlEl = document.createElement("select");
      const defaultOptionEl = document.createElement("option");
      defaultOptionEl.value = "";
      defaultOptionEl.textContent = "Selecione";
      controlEl.appendChild(defaultOptionEl);
      (field.listOptions || []).forEach(function eachOption(optionValue) {
        const optionEl = document.createElement("option");
        optionEl.value = String(optionValue || "");
        optionEl.textContent = String(optionValue || "");
        controlEl.appendChild(optionEl);
      });
    } else if (fieldType === "flag") {
      controlEl = document.createElement("select");
      [["1", "Sim"], ["0", "Não"]].forEach(function eachFlag(optionData) {
        const optionEl = document.createElement("option");
        optionEl.value = optionData[0];
        optionEl.textContent = optionData[1];
        controlEl.appendChild(optionEl);
      });
    } else {
      controlEl = document.createElement("input");
      controlEl.type = getFieldInputType(fieldType);
      if (["text", "number", "email", "phone"].includes(fieldType)) {
        controlEl.maxLength = Math.max(1, Math.min(Number.parseInt(String(field.size || "255"), 10) || 255, 255));
      }
    }

    controlEl.id = fieldId;
    controlEl.name = inputName;
    controlEl.required = Boolean(field.isRequired && fieldType !== "flag");
    controlEl.value = String(value || "");
    wrapEl.appendChild(controlEl);
    return wrapEl;
  }

  function buildSelectField(name, label, options, value) {
    const fieldId = "standard_list_" + name + "_" + Math.random().toString(16).slice(2);
    const wrapEl = document.createElement("div");
    wrapEl.className = "field admin-subprocess-field-v1";

    const labelEl = document.createElement("label");
    labelEl.setAttribute("for", fieldId);
    labelEl.textContent = label + " *";

    const selectEl = document.createElement("select");
    selectEl.id = fieldId;
    selectEl.name = name;
    selectEl.required = true;

    options.forEach(function eachOption(optionData) {
      const optionEl = document.createElement("option");
      optionEl.value = optionData[0];
      optionEl.textContent = optionData[1];
      if (String(optionData[0]) === String(value || optionData[0])) {
        optionEl.selected = true;
      }
      selectEl.appendChild(optionEl);
    });

    wrapEl.appendChild(labelEl);
    wrapEl.appendChild(selectEl);
    return wrapEl;
  }

  //###################################################################################
  // (3) DADOS E TABELAS
  //###################################################################################

  function getRecordsForSection(menuKey, sectionKey) {
    const records = Array.isArray(historyMap[menuKey]) ? historyMap[menuKey] : [];

    return records.filter(function matchSection(record) {
      const recordSectionKey = String(record && record.section_key || "").trim();
      return !sectionKey || !recordSectionKey || recordSectionKey === sectionKey;
    });
  }

  function getRecordMainValue(record, section) {
    const values = record && record.values && typeof record.values === "object" ? record.values : {};

    for (let index = 0; index < section.fields.length; index += 1) {
      const field = section.fields[index];
      const value = String(values[field.key] || "").trim();

      if (value) {
        return value;
      }
    }

    return "-";
  }

  function getRecordSystemValue(record) {
    const values = record && record.values && typeof record.values === "object" ? record.values : {};
    return String(values.__system || values.sistema || values.system || "all").trim() || "all";
  }

  function getRecordStatusValue(record) {
    const values = record && record.values && typeof record.values === "object" ? record.values : {};
    return normalizeStatus(values.__estado || values.status || "ativo");
  }

  function buildRows(menuKey, section) {
    return getRecordsForSection(menuKey, section.key).map(function mapRecord(record) {
      return {
        record,
        recordId: String(record.record_id || "").trim(),
        label: getRecordMainValue(record, section),
        system: getSystemLabel(getRecordSystemValue(record)),
        status: getRecordStatusValue(record),
        statusLabel: getStatusLabel(getRecordStatusValue(record)),
        values: record.values && typeof record.values === "object" ? record.values : {}
      };
    });
  }

  function createStatusBadge(status) {
    const spanEl = document.createElement("span");
    const cleanStatus = normalizeStatus(status);
    spanEl.className = "admin-subprocess-badge-v1 " + (cleanStatus === "ativo"
      ? "admin-subprocess-badge-active-v1"
      : "admin-subprocess-badge-inactive-v1");
    spanEl.textContent = getStatusLabel(cleanStatus);
    return spanEl;
  }

  function renderTable(cardEl, options) {
    const rows = options.rows || [];
    const labels = options.labels;
    const section = options.section;
    const isActive = options.status === "ativo";
    let currentSearch = "";
    let currentPageSize = 5;
    let currentPage = 1;

    cardEl.innerHTML = "";

    const titleEl = document.createElement("h2");
    titleEl.textContent = isActive ? labels.activeTitle : labels.inactiveTitle;
    cardEl.appendChild(titleEl);

    const searchRowEl = document.createElement("div");
    searchRowEl.className = "standard-list-process-search-row-v1";
    const searchInputEl = document.createElement("input");
    searchInputEl.type = "search";
    searchInputEl.className = "standard-list-process-search-v1";
    searchInputEl.placeholder = "Pesquisar...";
    searchRowEl.appendChild(searchInputEl);
    cardEl.appendChild(searchRowEl);

    const tableWrapEl = document.createElement("div");
    tableWrapEl.className = "admin-subprocess-table-wrap-v1";

    const tableEl = document.createElement("table");
    tableEl.className = "admin-subprocess-table-v1";

    const theadEl = document.createElement("thead");
    const mainHeader = section.fields[0] ? section.fields[0].label : labels.singular;
    theadEl.innerHTML = "<tr><th>" + escapeHtml(mainHeader).toUpperCase() + "</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbodyEl = document.createElement("tbody");
    tableEl.appendChild(theadEl);
    tableEl.appendChild(tbodyEl);
    tableWrapEl.appendChild(tableEl);
    cardEl.appendChild(tableWrapEl);

    const paginationEl = document.createElement("div");
    paginationEl.className = "standard-list-process-pagination-v1";
    paginationEl.innerHTML = `
      <label class="standard-list-process-page-size-v1">
        <select aria-label="Entradas por página">
          <option value="5">5</option>
          <option value="10">10</option>
          <option value="20">20</option>
        </select>
        entradas por página
      </label>
      <div class="standard-list-process-pages-v1"></div>
      <span></span>
    `;
    cardEl.appendChild(paginationEl);

    const pageSizeSelectEl = paginationEl.querySelector("select");
    const pageLabelEl = paginationEl.querySelector(".standard-list-process-pages-v1");

    function getVisibleRows() {
      const filteredRows = rows.filter(function filterByStatus(row) {
        if (normalizeStatus(row.status) !== options.status) {
          return false;
        }

        if (!currentSearch) {
          return true;
        }

        return normalizeText(row.label + " " + row.system + " " + row.statusLabel).includes(currentSearch);
      });

      return filteredRows;
    }

    function renderRows() {
      const visibleRows = getVisibleRows();
      const totalPages = Math.max(1, Math.ceil(visibleRows.length / currentPageSize));
      currentPage = Math.min(Math.max(currentPage, 1), totalPages);
      const startIndex = (currentPage - 1) * currentPageSize;
      const pageRows = visibleRows.slice(startIndex, startIndex + currentPageSize);
      tbodyEl.innerHTML = "";

      if (!pageRows.length) {
        const emptyRowEl = document.createElement("tr");
        emptyRowEl.className = "standard-list-process-empty-row-v1";
        const emptyCellEl = document.createElement("td");
        emptyCellEl.colSpan = 4;
        emptyCellEl.textContent = isActive ? labels.emptyActive : labels.emptyInactive;
        emptyRowEl.appendChild(emptyCellEl);
        tbodyEl.appendChild(emptyRowEl);
      } else {
        pageRows.forEach(function renderRow(row) {
          const trEl = document.createElement("tr");

          const nameCellEl = document.createElement("td");
          nameCellEl.textContent = row.label || "-";
          trEl.appendChild(nameCellEl);

          const systemCellEl = document.createElement("td");
          systemCellEl.textContent = row.system || "Default";
          trEl.appendChild(systemCellEl);

          const statusCellEl = document.createElement("td");
          statusCellEl.appendChild(createStatusBadge(row.status));
          trEl.appendChild(statusCellEl);

          const actionsCellEl = document.createElement("td");
          actionsCellEl.className = "admin-col-actions-v1";
          const actionsWrapEl = document.createElement("div");
          actionsWrapEl.className = "table-actions admin-subprocess-row-actions-v1";

          const viewBtnEl = document.createElement("button");
          viewBtnEl.type = "button";
          viewBtnEl.className = "standard-list-process-action-v1";
          viewBtnEl.title = "Visualizar detalhes";
          viewBtnEl.setAttribute("aria-label", "Visualizar detalhes");
          viewBtnEl.textContent = "👁";
          viewBtnEl.addEventListener("click", function showDetails() {
            alert(labels.singular + "\nNome: " + row.label + "\nSistema: " + row.system + "\nEstado: " + row.statusLabel);
          });

          const editBtnEl = document.createElement("button");
          editBtnEl.type = "button";
          editBtnEl.className = "standard-list-process-action-v1";
          editBtnEl.title = "Editar";
          editBtnEl.setAttribute("aria-label", "Editar");
          editBtnEl.textContent = "✎";
          editBtnEl.addEventListener("click", function editRecord() {
            renderCreateForm(options.menuKey, options.setting, section, labels, row.record);
          });

          actionsWrapEl.appendChild(viewBtnEl);
          actionsWrapEl.appendChild(editBtnEl);
          actionsCellEl.appendChild(actionsWrapEl);
          trEl.appendChild(actionsCellEl);
          tbodyEl.appendChild(trEl);
        });
      }

      pageLabelEl.textContent = "[ " + (visibleRows.length ? currentPage : 0) + " / " + (visibleRows.length ? totalPages : 0) + " ]";
    }

    searchInputEl.addEventListener("input", function onSearchInput() {
      currentSearch = normalizeText(searchInputEl.value);
      currentPage = 1;
      renderRows();
    });

    pageSizeSelectEl.addEventListener("change", function onPageSizeChange() {
      currentPageSize = Number.parseInt(String(pageSizeSelectEl.value || "5"), 10) || 5;
      currentPage = 1;
      renderRows();
    });

    renderRows();
  }

  //###################################################################################
  // (4) FORMULÁRIO DE CRIAÇÃO/EDIÇÃO
  //###################################################################################

  function renderCreateForm(menuKey, setting, section, labels, editRecord) {
    const cards = ensureCards(menuKey);
    const createCard = cards.createCard;
    const isEditing = Boolean(editRecord && editRecord.record_id);
    const values = isEditing && editRecord.values && typeof editRecord.values === "object"
      ? editRecord.values
      : {};

    createCard.innerHTML = "";

    const toolbarEl = document.createElement("div");
    toolbarEl.className = "appverbo-process-action-toolbar-v1";

    const detailsEl = document.createElement("details");
    detailsEl.className = "entity-create-collapse admin-subprocess-create-collapse-v1 appverbo-process-action-details-v1";
    detailsEl.open = isEditing;

    const summaryEl = document.createElement("summary");
    summaryEl.className = "appverbo-process-action-toggle-v1";
    summaryEl.innerHTML = "<span>" + escapeHtml(isEditing ? "Editar " + labels.singular : labels.create) + "</span>";

    const panelEl = document.createElement("div");
    panelEl.className = "entity-create-body appverbo-process-action-panel-v1";

    const formEl = document.createElement("form");
    formEl.method = "post";
    formEl.action = "/users/profile/process-data";
    formEl.className = "admin-subprocess-form-v1";

    const hiddenFields = {
      menu_key: menuKey,
      section_key: section.key,
      history_action: isEditing ? "update" : "create",
      history_record_id: isEditing ? String(editRecord.record_id || "") : ""
    };

    Object.keys(hiddenFields).forEach(function appendHidden(name) {
      const inputEl = document.createElement("input");
      inputEl.type = "hidden";
      inputEl.name = name;
      inputEl.value = hiddenFields[name];
      formEl.appendChild(inputEl);
    });

    const gridEl = document.createElement("div");
    gridEl.className = "admin-subprocess-grid-v1";

    section.fields.forEach(function appendField(field) {
      gridEl.appendChild(buildFieldControl(field, values[field.key] || ""));
    });

    gridEl.appendChild(buildSelectField("process_system", "Sistema", SYSTEM_OPTIONS, getRecordSystemValue(editRecord || {})));
    gridEl.appendChild(buildSelectField("process_state", "Estado", STATUS_OPTIONS, getRecordStatusValue(editRecord || {})));

    formEl.appendChild(gridEl);

    const actionRowEl = document.createElement("div");
    actionRowEl.className = "form-action-row admin-subprocess-actions-v1";

    const saveBtnEl = document.createElement("button");
    saveBtnEl.type = "submit";
    saveBtnEl.className = "action-btn";
    saveBtnEl.textContent = "Guardar";

    const cancelBtnEl = document.createElement("button");
    cancelBtnEl.type = "button";
    cancelBtnEl.className = "action-btn-cancel";
    cancelBtnEl.textContent = "Cancelar";
    cancelBtnEl.addEventListener("click", function cancelEdit() {
      renderStandardProcess(menuKey, section.key);
    });

    actionRowEl.appendChild(saveBtnEl);
    actionRowEl.appendChild(cancelBtnEl);
    formEl.appendChild(actionRowEl);

    panelEl.appendChild(formEl);
    detailsEl.appendChild(summaryEl);
    detailsEl.appendChild(panelEl);
    toolbarEl.appendChild(detailsEl);
    createCard.appendChild(toolbarEl);
    showOnlyStandardCards(menuKey);

    if (isEditing) {
      createCard.scrollIntoView({ block: "start", behavior: "smooth" });
    }
  }

  //###################################################################################
  // (5) NAVEGAÇÃO STANDARD
  //###################################################################################

  function renderSubmenu(menuKey, setting, selectedSectionKey) {
    const submenuEl = document.getElementById("submenu-items");
    const sections = buildSections(setting);

    if (!submenuEl) {
      return;
    }

    submenuEl.innerHTML = "";
    sections.forEach(function appendTab(section) {
      const tabEl = document.createElement("button");
      tabEl.type = "button";
      tabEl.className = "submenu-item" + (section.key === selectedSectionKey ? " active" : "");
      tabEl.textContent = section.label || "Geral";
      tabEl.dataset.standardListProcessSection = section.key;
      tabEl.addEventListener("click", function activateSection(event) {
        event.preventDefault();
        selectedSectionByMenu.set(menuKey, section.key);
        renderStandardProcess(menuKey, section.key, true);
      });
      submenuEl.appendChild(tabEl);
    });
  }

  function setSidebarActive(menuKey) {
    document.querySelectorAll(".menu-item").forEach(function eachButton(buttonEl) {
      const isActive = normalizeKey(buttonEl.dataset.menu) === menuKey;
      buttonEl.classList.toggle("active", isActive);
    });
  }

  function showOnlyStandardCards(menuKey) {
    document.querySelectorAll("[data-menu-scope], #dynamic-process-card").forEach(function hideScoped(cardEl) {
      if (cardEl.id === "menu-tabs-card") {
        return;
      }

      cardEl.style.display = "none";
    });

    document
      .querySelectorAll("[data-standard-list-process-v1='1'][data-admin-subprocess='" + menuKey + "']")
      .forEach(function showCard(cardEl) {
        cardEl.style.display = "";
      });
  }

  function updateBrowserUrl(menuKey, targetId, shouldPushUrl) {
    if (!shouldPushUrl || !window.history || typeof window.history.pushState !== "function") {
      return;
    }

    const target = "#" + targetId;
    const nextUrl = "/users/new?menu=" + encodeURIComponent(menuKey) + "&target=" + encodeURIComponent(target) + target;
    const currentUrl = window.location.pathname + window.location.search + window.location.hash;

    if (currentUrl !== nextUrl) {
      window.history.pushState({}, "", nextUrl);
    }
  }

  function renderStandardProcess(menuKey, requestedSectionKey, shouldPushUrl) {
    const setting = getStandardSetting(menuKey);

    if (!setting) {
      return false;
    }

    ensureRootStyles();
    activeStandardMenuKey = menuKey;
    const cards = ensureCards(menuKey);
    const selectedSection = requestedSectionKey
      ? buildSections(setting).find(function match(section) { return section.key === requestedSectionKey; })
      : getSelectedSection(menuKey, setting);
    const section = selectedSection || getSelectedSection(menuKey, setting);

    if (!section) {
      return false;
    }

    selectedSectionByMenu.set(menuKey, section.key);
    const labels = buildLabels(section);
    const rows = buildRows(menuKey, section);

    const titleEl = document.getElementById("process-shell-title");
    if (titleEl) {
      titleEl.textContent = String(setting.label || "Processo").trim() || "Processo";
    }

    renderSubmenu(menuKey, setting, section.key);
    renderCreateForm(menuKey, setting, section, labels, null);
    renderTable(cards.activeCard, { menuKey, setting, section, labels, rows, status: "ativo" });
    renderTable(cards.inactiveCard, { menuKey, setting, section, labels, rows, status: "inativo" });
    showOnlyStandardCards(menuKey);
    setSidebarActive(menuKey);
    updateBrowserUrl(menuKey, cards.ids.active, shouldPushUrl);
    return true;
  }

  function getCurrentMenuKey() {
    const url = new URL(window.location.href);
    return normalizeKey(url.searchParams.get("menu") || bootstrap.initialMenu || "");
  }

  function installSidebarInterception() {
    document.addEventListener("click", function onMenuClick(event) {
      const buttonEl = event.target.closest(".menu-item[data-menu]");

      if (!buttonEl) {
        return;
      }

      const menuKey = normalizeKey(buttonEl.dataset.menu);

      if (!getStandardSetting(menuKey)) {
        return;
      }

      event.preventDefault();
      event.stopImmediatePropagation();
      renderStandardProcess(menuKey, "", true);
    }, true);
  }

  function init() {
    installSidebarInterception();

    const menuKey = getCurrentMenuKey();

    if (getStandardSetting(menuKey)) {
      window.setTimeout(function renderAfterBaseMenu() {
        renderStandardProcess(menuKey, String(bootstrap.initialDynamicProcessSection || ""), false);
      }, 0);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
//###################################################################################
// APPVERBO_STANDARD_LIST_PROCESS_V1_END
//###################################################################################
