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
  // (2) CAMPO VALOR INICIAL PARA TIPO "COR"
  //###################################################################################

  function normalizeHexColorValueV1(value) {
    const rawValue = String(value || "").trim();

    if (!rawValue) {
      return "";
    }

    const compactValue = rawValue.replace(/\s+/g, "");

    if (/^#?[0-9a-fA-F]{3}$/.test(compactValue)) {
      const cleanValue = compactValue.replace("#", "").toUpperCase();
      return (
        "#" +
        cleanValue
          .split("")
          .map(function (character) {
            return character + character;
          })
          .join("")
      );
    }

    if (/^#?[0-9a-fA-F]{6}$/.test(compactValue)) {
      return "#" + compactValue.replace("#", "").toUpperCase();
    }

    return "";
  }

  function getDefinicoesFormsV1() {
    return Array.from(
      document.querySelectorAll(
        "[data-admin-subprocess='definicoes'].admin-subprocess-form-card-v1 form.admin-subprocess-form-v1"
      )
    );
  }

  function isDefinitionTypeColorV1(typeValue) {
    return normalizeTextV1(typeValue) === "cor";
  }

  function eyeDropperIconMarkupV1() {
    return [
      '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false">',
      '<path d="M14.7 3.3a1 1 0 0 1 1.4 0l4.6 4.6a1 1 0 0 1 0 1.4l-2 2-2-2-5.9 5.9a3 3 0 0 1-.7 3.3l-3.3 3.3a1 1 0 0 1-1.4-1.4l3.3-3.3a3 3 0 0 1 3.3-.7l5.9-5.9-2-2 2-2z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
      "</svg>",
    ].join("");
  }

  function getColorFieldElementsV1(formEl) {
    if (!formEl || !(formEl instanceof HTMLElement)) {
      return null;
    }

    const typeField = formEl.querySelector(
      "#admin_subprocess_parameter_type, [name='definition_type']"
    );
    const valueField = formEl.querySelector(
      "#admin_subprocess_initial_value, [name='definition_initial_value']"
    );

    if (!typeField || !valueField || valueField.tagName !== "INPUT") {
      return null;
    }

    const fieldContainer = valueField.closest(".field");
    if (!fieldContainer) {
      return null;
    }

    let inlineRow = fieldContainer.querySelector(
      "[data-definicoes-color-inline-row-v1='1']"
    );
    if (!inlineRow) {
      inlineRow = document.createElement("div");
      inlineRow.setAttribute("data-definicoes-color-inline-row-v1", "1");
      inlineRow.style.display = "flex";
      inlineRow.style.alignItems = "center";
      inlineRow.style.gap = "8px";
      inlineRow.style.width = "100%";
      inlineRow.style.boxSizing = "border-box";
      fieldContainer.insertBefore(inlineRow, valueField);
    }

    if (valueField.parentNode !== inlineRow) {
      inlineRow.appendChild(valueField);
    }

    let controlsContainer = fieldContainer.querySelector(
      "[data-definicoes-color-controls-v1='1']"
    );
    let colorInput = controlsContainer
      ? controlsContainer.querySelector("[data-definicoes-color-input-v1='1']")
      : null;
    let eyeDropperButton = controlsContainer
      ? controlsContainer.querySelector("[data-definicoes-eye-dropper-btn-v1='1']")
      : null;

    if (!controlsContainer || !colorInput || !eyeDropperButton) {
      controlsContainer = document.createElement("div");
      controlsContainer.setAttribute("data-definicoes-color-controls-v1", "1");
      controlsContainer.style.display = "none";
      controlsContainer.style.alignItems = "center";
      controlsContainer.style.justifyContent = "flex-end";
      controlsContainer.style.gap = "4px";
      controlsContainer.style.flex = "0 0 64px";
      controlsContainer.style.width = "64px";
      controlsContainer.style.maxWidth = "64px";

      colorInput = document.createElement("input");
      colorInput.type = "color";
      colorInput.value = "#000000";
      colorInput.setAttribute("data-definicoes-color-input-v1", "1");
      colorInput.setAttribute("aria-label", "Selecionar cor");
      colorInput.style.width = "30px";
      colorInput.style.minWidth = "30px";
      colorInput.style.maxWidth = "30px";
      colorInput.style.height = "30px";
      colorInput.style.padding = "0";
      colorInput.style.border = "1px solid #c8d3e8";
      colorInput.style.borderRadius = "6px";
      colorInput.style.background = "#ffffff";
      colorInput.style.cursor = "pointer";
      colorInput.style.boxSizing = "border-box";
      colorInput.style.setProperty("width", "30px", "important");
      colorInput.style.setProperty("min-width", "30px", "important");
      colorInput.style.setProperty("max-width", "30px", "important");
      colorInput.style.setProperty("height", "30px", "important");
      colorInput.style.setProperty("min-height", "30px", "important");
      colorInput.style.setProperty("max-height", "30px", "important");

      eyeDropperButton = document.createElement("button");
      eyeDropperButton.type = "button";
      eyeDropperButton.innerHTML = eyeDropperIconMarkupV1();
      eyeDropperButton.setAttribute("data-definicoes-eye-dropper-btn-v1", "1");
      eyeDropperButton.setAttribute("aria-label", "Conta-gotas");
      eyeDropperButton.title = "Conta-gotas";
      eyeDropperButton.style.width = "30px";
      eyeDropperButton.style.minWidth = "30px";
      eyeDropperButton.style.maxWidth = "30px";
      eyeDropperButton.style.height = "30px";
      eyeDropperButton.style.minHeight = "30px";
      eyeDropperButton.style.maxHeight = "30px";
      eyeDropperButton.style.display = "inline-flex";
      eyeDropperButton.style.alignItems = "center";
      eyeDropperButton.style.justifyContent = "center";
      eyeDropperButton.style.padding = "0";
      eyeDropperButton.style.border = "1px solid #c8d3e8";
      eyeDropperButton.style.borderRadius = "6px";
      eyeDropperButton.style.background = "#ffffff";
      eyeDropperButton.style.color = "#1f3f86";
      eyeDropperButton.style.cursor = "pointer";
      eyeDropperButton.style.boxSizing = "border-box";
      eyeDropperButton.style.setProperty("width", "30px", "important");
      eyeDropperButton.style.setProperty("min-width", "30px", "important");
      eyeDropperButton.style.setProperty("max-width", "30px", "important");
      eyeDropperButton.style.setProperty("height", "30px", "important");
      eyeDropperButton.style.setProperty("min-height", "30px", "important");
      eyeDropperButton.style.setProperty("max-height", "30px", "important");
      eyeDropperButton.style.setProperty("padding", "0", "important");
      eyeDropperButton.style.setProperty("line-height", "1", "important");

      controlsContainer.appendChild(colorInput);
      controlsContainer.appendChild(eyeDropperButton);
      inlineRow.appendChild(controlsContainer);
    } else if (controlsContainer.parentNode !== inlineRow) {
      inlineRow.appendChild(controlsContainer);
    }

    return {
      formEl: formEl,
      typeField: typeField,
      valueField: valueField,
      inlineRow: inlineRow,
      controlsContainer: controlsContainer,
      colorInput: colorInput,
      eyeDropperButton: eyeDropperButton,
    };
  }

  function syncColorInputFromValueFieldV1(colorElements) {
    const normalizedColorValue = normalizeHexColorValueV1(colorElements.valueField.value);

    if (normalizedColorValue) {
      colorElements.colorInput.value = normalizedColorValue;
      return;
    }

    if (!String(colorElements.valueField.value || "").trim()) {
      colorElements.colorInput.value = "#000000";
    }
  }

  function updateColorFieldVisibilityV1(colorElements) {
    const isColorType = isDefinitionTypeColorV1(colorElements.typeField.value);

    colorElements.valueField.style.flex = "1 1 auto";
    colorElements.valueField.style.minWidth = "0";
    colorElements.valueField.style.width = "100%";
    colorElements.valueField.style.boxSizing = "border-box";

    if (isColorType) {
      colorElements.valueField.style.flex = "1 1 calc(100% - 72px)";
      colorElements.controlsContainer.style.display = "flex";
      colorElements.valueField.placeholder = "Ex: #1A73E8";
      syncColorInputFromValueFieldV1(colorElements);
      return;
    }

    colorElements.controlsContainer.style.display = "none";
    colorElements.valueField.setCustomValidity("");
  }

  async function openEyeDropperAndApplyV1(colorElements) {
    if (typeof window.EyeDropper !== "function") {
      return;
    }

    const buttonEl = colorElements.eyeDropperButton;
    const previousOpacity = buttonEl.style.opacity;

    buttonEl.disabled = true;
    buttonEl.style.opacity = "0.6";

    try {
      const eyeDropper = new window.EyeDropper();
      const pickedColor = await eyeDropper.open();
      const normalizedColor = normalizeHexColorValueV1(
        pickedColor && pickedColor.sRGBHex
      );

      if (normalizedColor) {
        colorElements.valueField.value = normalizedColor;
        colorElements.valueField.dispatchEvent(new Event("input", { bubbles: true }));
        colorElements.valueField.dispatchEvent(new Event("change", { bubbles: true }));
      }
    } catch (_error) {
      // Ignora cancelamento do utilizador no conta-gotas.
    } finally {
      if (buttonEl.isConnected) {
        buttonEl.disabled = false;
        buttonEl.style.opacity = previousOpacity;
      }
    }
  }

  function validateColorFieldBeforeSubmitV1(colorElements) {
    if (!isDefinitionTypeColorV1(colorElements.typeField.value)) {
      colorElements.valueField.setCustomValidity("");
      return true;
    }

    const normalizedColorValue = normalizeHexColorValueV1(colorElements.valueField.value);

    if (!normalizedColorValue) {
      colorElements.valueField.setCustomValidity(
        "Para o tipo Cor, use hexadecimal: #RRGGBB."
      );
      colorElements.valueField.reportValidity();
      return false;
    }

    colorElements.valueField.value = normalizedColorValue;
    colorElements.valueField.setCustomValidity("");
    return true;
  }

  function bindColorFieldEventsV1(colorElements) {
    if (colorElements.valueField.dataset.definicoesColorValueBoundV1 !== "1") {
      colorElements.valueField.addEventListener("input", function () {
        colorElements.valueField.setCustomValidity("");
        syncColorInputFromValueFieldV1(colorElements);
      });

      colorElements.valueField.addEventListener("blur", function () {
        if (!isDefinitionTypeColorV1(colorElements.typeField.value)) {
          return;
        }

        const normalizedColorValue = normalizeHexColorValueV1(colorElements.valueField.value);
        if (normalizedColorValue) {
          colorElements.valueField.value = normalizedColorValue;
          syncColorInputFromValueFieldV1(colorElements);
        }
      });

      colorElements.valueField.dataset.definicoesColorValueBoundV1 = "1";
    }

    if (colorElements.typeField.dataset.definicoesColorTypeBoundV1 !== "1") {
      colorElements.typeField.addEventListener("change", function () {
        updateColorFieldVisibilityV1(colorElements);
      });
      colorElements.typeField.dataset.definicoesColorTypeBoundV1 = "1";
    }

    if (colorElements.colorInput.dataset.definicoesColorPickerBoundV1 !== "1") {
      colorElements.colorInput.addEventListener("input", function () {
        colorElements.valueField.value = String(colorElements.colorInput.value || "").toUpperCase();
        colorElements.valueField.setCustomValidity("");
      });
      colorElements.colorInput.dataset.definicoesColorPickerBoundV1 = "1";
    }

    if (colorElements.eyeDropperButton.dataset.definicoesEyeDropperBoundV1 !== "1") {
      colorElements.eyeDropperButton.addEventListener("click", function () {
        openEyeDropperAndApplyV1(colorElements);
      });
      colorElements.eyeDropperButton.dataset.definicoesEyeDropperBoundV1 = "1";
    }

    if (colorElements.formEl.dataset.definicoesColorSubmitBoundV1 !== "1") {
      colorElements.formEl.addEventListener("submit", function (event) {
        if (!validateColorFieldBeforeSubmitV1(colorElements)) {
          event.preventDefault();
        }
      });
      colorElements.formEl.dataset.definicoesColorSubmitBoundV1 = "1";
    }
  }

  function ensureDefinicoesColorFieldV1() {
    getDefinicoesFormsV1().forEach(function (formEl) {
      const colorElements = getColorFieldElementsV1(formEl);
      if (!colorElements) {
        return;
      }

      bindColorFieldEventsV1(colorElements);
      updateColorFieldVisibilityV1(colorElements);

      if (typeof window.EyeDropper !== "function") {
        colorElements.eyeDropperButton.style.display = "none";
      } else {
        colorElements.eyeDropperButton.style.display = "";
      }
    });
  }

  //###################################################################################
  // (3) PREENCHER CAMPOS PROCESSO E SUBPROCESSO
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
  // (4) INICIALIZACAO
  //###################################################################################

  function scheduleEnsureDefinicoesSelectsV1() {
    window.setTimeout(ensureDefinicoesSelectsV1, 0);
    window.setTimeout(ensureDefinicoesSelectsV1, 120);
    window.setTimeout(ensureDefinicoesSelectsV1, 320);
    window.setTimeout(ensureDefinicoesColorFieldV1, 0);
    window.setTimeout(ensureDefinicoesColorFieldV1, 120);
    window.setTimeout(ensureDefinicoesColorFieldV1, 320);
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
        ensureDefinicoesColorFieldV1();
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
