//###################################################################################
// APPVERBOBRAGA - ADMIN DEFINICOES MANAGER V1
//###################################################################################

(function setupAdminDefinicoesManagerV1() {
  "use strict";

  if (window.__appverboAdminDefinicoesManagerLoadedV1 === true) {
    return;
  }
  window.__appverboAdminDefinicoesManagerLoadedV1 = true;

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function normalizeTextV1(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function isActiveRowV1(row) {
    if (!row || typeof row !== "object") {
      return false;
    }

    if (row.is_deleted === true) {
      return false;
    }

    const status = normalizeTextV1(row.status || row.section_status);
    const isActiveFlag = row.is_active === true;

    return isActiveFlag || status === "active" || status === "ativo";
  }

  function getSidebarMenuRowsV1() {
    const pageData = window.__NEW_USER_PAGE__DATA__ || {};
    return Array.isArray(pageData.sidebarMenuSettings) ? pageData.sidebarMenuSettings : [];
  }

  function uniqueOptionsFromRowsV1(rows, valueKeys, labelKeys) {
    const options = [];
    const seen = new Set();

    rows.forEach(function (row) {
      if (!isActiveRowV1(row)) {
        return;
      }

      let value = "";
      let label = "";

      valueKeys.forEach(function (key) {
        if (value) {
          return;
        }
        value = String(row[key] || "").trim();
      });

      labelKeys.forEach(function (key) {
        if (label) {
          return;
        }
        label = String(row[key] || "").trim();
      });

      const resolvedValue = value || label;
      const resolvedLabel = label || value;
      const normalized = normalizeTextV1(resolvedValue);

      if (!resolvedValue || !resolvedLabel || !normalized || seen.has(normalized)) {
        return;
      }

      seen.add(normalized);
      options.push([resolvedValue, resolvedLabel]);
    });

    return options;
  }

  function getProcessOptionsFromSessionsV1() {
    const rows = getSidebarMenuRowsV1();
    const options = uniqueOptionsFromRowsV1(
      rows,
      ["menu_section_label", "menu_section"],
      ["menu_section_label", "menu_section"]
    );

    if (options.length > 0) {
      return options;
    }

    const menuRows = Array.from(
      document.querySelectorAll(
        "[data-admin-subprocess='menu'][data-admin-subprocess-status='active'] tbody tr"
      )
    );
    const domOptions = [];
    const seen = new Set();

    menuRows.forEach(function (rowEl) {
      const cells = rowEl.querySelectorAll("td");
      const label = String(cells[1] ? cells[1].textContent : "").trim();
      const value = label;

      if (!label || !value || seen.has(value)) {
        return;
      }

      seen.add(value);
      domOptions.push([value, label]);
    });

    return domOptions;
  }

  function getSubprocessOptionsFromMenuV1() {
    const rows = getSidebarMenuRowsV1();
    const options = uniqueOptionsFromRowsV1(
      rows,
      ["key", "menu_key", "label", "name"],
      ["label", "name", "key", "menu_key"]
    );

    if (options.length > 0) {
      return options;
    }

    const menuRows = Array.from(
      document.querySelectorAll(
        "[data-admin-subprocess='menu'][data-admin-subprocess-status='active'] tbody tr"
      )
    );
    const domOptions = [];
    const seen = new Set();

    menuRows.forEach(function (rowEl) {
      const cells = rowEl.querySelectorAll("td");
      const label = String(cells[0] ? cells[0].textContent : "").trim();
      const value = label;

      if (!label || !value || seen.has(value)) {
        return;
      }

      seen.add(value);
      domOptions.push([value, label]);
    });

    return domOptions;
  }

  function buildSelectOptionV1(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = String(value || "");
    option.textContent = String(label || value || "");
    option.selected = String(value || "") === String(selectedValue || "");
    return option;
  }

  function hasServerRenderedOptionsV1(selectEl) {
    return Array.from(selectEl.options || []).some(function (optionEl) {
      const label = String(optionEl.textContent || "").trim().toLowerCase();
      const value = String(optionEl.value || "").trim();
      return label && label !== "selecione" && value;
    });
  }

  //###################################################################################
  // (2) PREENCHER CAMPOS PROCESSO E SUBPROCESSO
  //###################################################################################

  function ensureSelectFieldV1(fieldSelector, inputName, options) {
    const formCard = document.querySelector(
      "[data-admin-subprocess='definicoes'].admin-subprocess-form-card-v1"
    );

    if (!formCard) {
      return;
    }

    const currentField = formCard.querySelector(fieldSelector);
    if (!currentField) {
      return;
    }

    const currentFieldIsSelect = currentField.tagName === "SELECT";
    const currentValue = String(currentField.value || "").trim();

    if (currentFieldIsSelect && options.length === 0 && hasServerRenderedOptionsV1(currentField)) {
      return;
    }

    let targetSelect = null;
    if (currentFieldIsSelect) {
      targetSelect = currentField;
    } else {
      targetSelect = document.createElement("select");
      targetSelect.id = currentField.id || "";
      targetSelect.name = currentField.getAttribute("name") || inputName;
      targetSelect.className = currentField.className || "";
      targetSelect.required = currentField.required;
      currentField.parentNode.replaceChild(targetSelect, currentField);
    }

    while (targetSelect.firstChild) {
      targetSelect.removeChild(targetSelect.firstChild);
    }

    targetSelect.appendChild(buildSelectOptionV1("", "Selecione", currentValue));

    options.forEach(function (entry) {
      targetSelect.appendChild(buildSelectOptionV1(entry[0], entry[1], currentValue));
    });

    if (currentValue && !options.some(function (entry) { return String(entry[0]) === currentValue; })) {
      targetSelect.appendChild(buildSelectOptionV1(currentValue, currentValue, currentValue));
    }
  }

  function ensureDefinicoesSelectsV1() {
    ensureSelectFieldV1(
      "#admin_subprocess_process_name, [name='definition_process']",
      "definition_process",
      getProcessOptionsFromSessionsV1()
    );

    ensureSelectFieldV1(
      "#admin_subprocess_subprocess_name, [name='definition_subprocess']",
      "definition_subprocess",
      getSubprocessOptionsFromMenuV1()
    );
  }

  //###################################################################################
  // (3) INICIALIZACAO
  //###################################################################################

  function scheduleEnsureDefinicoesSelectsV1() {
    window.setTimeout(ensureDefinicoesSelectsV1, 0);
    window.setTimeout(ensureDefinicoesSelectsV1, 120);
    window.setTimeout(ensureDefinicoesSelectsV1, 320);
  }

  let observerTimerV1 = null;

  function startObserverV1() {
    if (!document.body || window.__appverboAdminDefinicoesManagerObserverV1 === true) {
      return;
    }

    const observer = new MutationObserver(function () {
      window.clearTimeout(observerTimerV1);
      observerTimerV1 = window.setTimeout(function () {
        ensureDefinicoesSelectsV1();
      }, 80);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    window.__appverboAdminDefinicoesManagerObserverV1 = true;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      scheduleEnsureDefinicoesSelectsV1();
      startObserverV1();
    });
  } else {
    scheduleEnsureDefinicoesSelectsV1();
    startObserverV1();
  }

  window.addEventListener("load", scheduleEnsureDefinicoesSelectsV1);
  window.addEventListener("appverbo:normalize-tabs-width-v1", scheduleEnsureDefinicoesSelectsV1);
})();
