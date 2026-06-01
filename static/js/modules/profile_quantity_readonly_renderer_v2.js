// APPVERBO_PROFILE_QUANTITY_READONLY_RENDERER_V2_START
(function () {
  "use strict";

  if (typeof window !== "undefined") {
    window.__APPVERBO_QUANTITY_READONLY_RENDERER_V2_ACTIVE = true;
  }

  //###################################################################################
  // (1) BOOTSTRAP E CONSTANTES
  //###################################################################################

  const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
  const MEU_PERFIL_KEY_V2 = "meu_perfil";
  const LEGACY_DOCUMENTOS_KEY_V2 = "documentos";

  const sidebarMenuSettings = Array.isArray(bootstrap.sidebarMenuSettings)
    ? bootstrap.sidebarMenuSettings
    : [];

  const menuProcessQuantityValuesMap = (
    bootstrap.menuProcessQuantityValuesMap &&
    typeof bootstrap.menuProcessQuantityValuesMap === "object" &&
    !Array.isArray(bootstrap.menuProcessQuantityValuesMap)
  )
    ? bootstrap.menuProcessQuantityValuesMap
    : {};

  //###################################################################################
  // (2) NORMALIZACAO
  //###################################################################################

  function normalizeKeyQuantityReadonly_v2(value) {
    const cleanValue = String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");

    if (cleanValue === LEGACY_DOCUMENTOS_KEY_V2) {
      return MEU_PERFIL_KEY_V2;
    }

    return cleanValue;
  }

  function normalizeTextQuantityReadonly_v2(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, " ");
  }

  function toSentenceCaseQuantityReadonly_v2(value) {
    const cleanText = String(value || "").trim().replace(/\s+/g, " ");

    if (!cleanText) {
      return "";
    }

    const loweredText = cleanText.toLocaleLowerCase("pt-PT");

    return loweredText.charAt(0).toLocaleUpperCase("pt-PT") + loweredText.slice(1);
  }

  function normalizeFieldTypeQuantityReadonly_v2(value) {
    const cleanType = String(value || "text").trim().toLowerCase();
    const allowedTypes = new Set(["text", "number", "email", "phone", "date", "flag", "list"]);

    return allowedTypes.has(cleanType) ? cleanType : "text";
  }

  //###################################################################################
  // (3) DADOS DO PROCESSO MEU PERFIL
  //###################################################################################

  function getMeuPerfilSettingQuantityReadonly_v2() {
    return sidebarMenuSettings.find(function (setting) {
      return normalizeKeyQuantityReadonly_v2(setting && setting.key) === MEU_PERFIL_KEY_V2;
    }) || null;
  }

  function getFieldMetaMapQuantityReadonly_v2(setting) {
    const metaMap = new Map();

    const options = Array.isArray(setting && setting.process_field_options)
      ? setting.process_field_options
      : [];

    options.forEach(function (option) {
      const fieldKey = normalizeKeyQuantityReadonly_v2(option && option.key);

      if (!fieldKey) {
        return;
      }

      metaMap.set(fieldKey, {
        key: fieldKey,
        label: toSentenceCaseQuantityReadonly_v2(option.label || fieldKey),
        fieldType: normalizeFieldTypeQuantityReadonly_v2(option.field_type)
      });
    });

    return metaMap;
  }

  function normalizeQuantityRulesQuantityReadonly_v2(rawRules) {
    if (!Array.isArray(rawRules)) {
      return [];
    }

    return rawRules
      .map(function (rawRule, index) {
        if (!rawRule || typeof rawRule !== "object") {
          return null;
        }

        const key = normalizeKeyQuantityReadonly_v2(
          rawRule.key ||
          rawRule.rule_key ||
          rawRule.ruleKey ||
          "qty_regra_" + String(index + 1)
        );

        const quantityFieldKey = normalizeKeyQuantityReadonly_v2(
          rawRule.quantity_field_key ||
          rawRule.quantityFieldKey
        );

        const repeatedFieldKeysRaw = Array.isArray(rawRule.repeated_field_keys || rawRule.repeatedFieldKeys)
          ? (rawRule.repeated_field_keys || rawRule.repeatedFieldKeys)
          : [];

        const repeatedFieldKeys = [];
        const seen = new Set();

        repeatedFieldKeysRaw.forEach(function (rawFieldKey) {
          const fieldKey = normalizeKeyQuantityReadonly_v2(rawFieldKey);

          if (!fieldKey || seen.has(fieldKey)) {
            return;
          }

          seen.add(fieldKey);
          repeatedFieldKeys.push(fieldKey);
        });

        if (!key || !quantityFieldKey || !repeatedFieldKeys.length) {
          return null;
        }

        return {
          key: key,
          label: toSentenceCaseQuantityReadonly_v2(rawRule.label || rawRule.rule_label || rawRule.name || "Quantidade"),
          quantityFieldKey: quantityFieldKey,
          repeatedFieldKeys: repeatedFieldKeys,
          headerKey: normalizeKeyQuantityReadonly_v2(rawRule.header_key || rawRule.headerKey),
          itemLabel: toSentenceCaseQuantityReadonly_v2(rawRule.item_label || rawRule.itemLabel || "Item") || "Item"
        };
      })
      .filter(Boolean);
  }

  function normalizeQuantityItemsQuantityReadonly_v2(rawItems) {
    if (!Array.isArray(rawItems)) {
      return [];
    }

    return rawItems
      .map(function (rawItem) {
        if (!rawItem || typeof rawItem !== "object") {
          return null;
        }

        const normalizedItem = {};

        Object.keys(rawItem).forEach(function (rawKey) {
          const fieldKey = normalizeKeyQuantityReadonly_v2(rawKey);

          if (!fieldKey) {
            return;
          }

          normalizedItem[fieldKey] = String(rawItem[rawKey] || "").trim();
        });

        return normalizedItem;
      })
      .filter(Boolean);
  }

  function getQuantityValuesQuantityReadonly_v2(ruleKey) {
    const valuesByMenu = menuProcessQuantityValuesMap[MEU_PERFIL_KEY_V2];

    if (!valuesByMenu || typeof valuesByMenu !== "object" || Array.isArray(valuesByMenu)) {
      return [];
    }

    return normalizeQuantityItemsQuantityReadonly_v2(valuesByMenu[normalizeKeyQuantityReadonly_v2(ruleKey)]);
  }

  //###################################################################################
  // (4) LOCALIZAR DOM
  //###################################################################################

  function getPerfilCardQuantityReadonly_v2() {
    return document.querySelector("#perfil-pessoal-card");
  }

  function getReadonlyGridQuantityReadonly_v2() {
    const card = getPerfilCardQuantityReadonly_v2();

    if (!card) {
      return null;
    }

    return card.querySelector(".profile-readonly .personal-grid");
  }

  function getCurrentProfileSectionQuantityReadonly_v2() {
    const sectionInput = document.querySelector("[data-meu-perfil-section-input]");
    const inputValue = normalizeKeyQuantityReadonly_v2(sectionInput ? sectionInput.value : "");

    if (inputValue) {
      return inputValue;
    }

    const activeTabSelectors = [
      "#submenu-items .submenu-item.active[data-profile-section]",
      "#submenu-items .submenu-item[data-profile-section][aria-selected='true']",
      "#submenu-items .submenu-item[data-profile-section][data-active='true']",
      ".submenu-item.active[data-profile-section]",
      ".submenu-item[data-profile-section][aria-selected='true']",
      "[data-profile-section-tab].active[data-profile-section]",
      "[data-profile-section-button].active[data-profile-section]",
      ".profile-section-tab.active[data-profile-section]"
    ];

    for (const selector of activeTabSelectors) {
      const activeElement = document.querySelector(selector);

      if (!activeElement) {
        continue;
      }

      const sectionFromDataset = normalizeKeyQuantityReadonly_v2(
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      if (sectionFromDataset) {
        return sectionFromDataset;
      }
    }

    try {
      const currentUrl = new URL(window.location.href);
      const sectionFromQuery = normalizeKeyQuantityReadonly_v2(currentUrl.searchParams.get("profile_section") || "");

      if (sectionFromQuery) {
        return sectionFromQuery;
      }
    }
    catch (error) {
      // Ignora erro de parse da URL.
    }

    return "";
  }

  //###################################################################################
  // (5) FORMATACAO DOS VALORES
  //###################################################################################

  function formatValueQuantityReadonly_v2(value, fieldType) {
    const cleanValue = String(value || "").trim();

    if (!cleanValue) {
      return "-";
    }

    if (fieldType === "flag") {
      return ["1", "true", "sim", "yes", "on"].includes(cleanValue.toLowerCase()) ? "Sim" : "Não";
    }

    if (fieldType === "date" && /^\d{4}-\d{2}-\d{2}$/.test(cleanValue)) {
      const parts = cleanValue.split("-");
      return parts[2] + "/" + parts[1] + "/" + parts[0];
    }

    return cleanValue;
  }

  function findQuantityFieldElementQuantityReadonly_v2(grid, rule, fieldMetaMap) {
    if (!grid || !rule) {
      return null;
    }

    const byKey = grid.querySelector('[data-profile-field-key="' + rule.quantityFieldKey + '"]');

    if (byKey) {
      return byKey.closest(".personal-item") || byKey;
    }

    const quantityMeta = fieldMetaMap.get(rule.quantityFieldKey);
    const expectedLabel = normalizeTextQuantityReadonly_v2(quantityMeta ? quantityMeta.label : rule.quantityFieldKey);

    return Array.from(grid.querySelectorAll(".personal-item")).find(function (item) {
      const label = item.querySelector(".personal-label");
      const labelText = normalizeTextQuantityReadonly_v2(label ? label.textContent : "");

      return labelText === expectedLabel;
    }) || null;
  }

  //###################################################################################
  // (6) REMOVER RENDER ANTIGO
  //###################################################################################

  function cleanupLegacyQuantityReadonly_v2(grid) {
    if (!grid) {
      return;
    }

    Array.from(grid.querySelectorAll([
      "[data-appverbo-quantity-readonly-generated-v1='1']",
      "[data-profile-quantity-readonly-rule-key]",
      ".profile-quantity-readonly-v1",
      ".appverbo-quantity-readonly-header-v1",
      ".appverbo-quantity-readonly-item-v1",
      ".appverbo-quantity-readonly-source-hidden-v1"
    ].join(","))).forEach(function (element) {
      element.remove();
    });

    Array.from(grid.querySelectorAll(".personal-item")).forEach(function (item) {
      const text = normalizeTextQuantityReadonly_v2(item.innerText || item.textContent || "");

      if (
        text.includes("quantidade de filhos") &&
        (
          text.includes("numero de filhos 1") ||
          text.includes("número de filhos 1") ||
          text.includes("nome do agregado") ||
          text.includes("data de nascimento do agregado")
        )
      ) {
        item.remove();
      }
    });
  }

  function cleanupCurrentQuantityReadonly_v2(grid) {
    if (!grid) {
      return;
    }

    Array.from(grid.querySelectorAll("[data-appverbo-quantity-readonly-v2='1']")).forEach(function (element) {
      element.remove();
    });
  }

  function restoreHiddenSourceFieldsQuantityReadonly_v2(grid) {
    if (!grid) {
      return;
    }

    Array.from(grid.querySelectorAll("[data-appverbo-quantity-source-hidden-v2='1']")).forEach(function (item) {
      item.style.display = "";
      item.removeAttribute("data-appverbo-quantity-source-hidden-v2");
    });
  }

  function hideSourceRepeatedFieldsQuantityReadonly_v2(grid, rule) {
    if (!grid || !rule || !Array.isArray(rule.repeatedFieldKeys) || !rule.repeatedFieldKeys.length) {
      return;
    }

    const ruleSectionKey = normalizeKeyQuantityReadonly_v2(rule.headerKey || "");
    const repeatedFieldKeySet = new Set(
      rule.repeatedFieldKeys
        .map(function (fieldKey) {
          return normalizeKeyQuantityReadonly_v2(fieldKey);
        })
        .filter(Boolean)
    );

    Array.from(grid.querySelectorAll(".personal-item")).forEach(function (item) {
      if (item.getAttribute("data-appverbo-quantity-readonly-v2") === "1") {
        return;
      }

      const fieldKey = normalizeKeyQuantityReadonly_v2(
        item.getAttribute("data-profile-field-key") || item.dataset.profileFieldKey || ""
      );

      if (!fieldKey || !repeatedFieldKeySet.has(fieldKey)) {
        return;
      }

      if (ruleSectionKey) {
        const itemSectionKey = normalizeKeyQuantityReadonly_v2(
          item.getAttribute("data-profile-section-pane") || item.dataset.profileSectionPane || ""
        );

        if (itemSectionKey && itemSectionKey !== ruleSectionKey) {
          return;
        }
      }

      item.style.display = "none";
      item.setAttribute("data-appverbo-quantity-source-hidden-v2", "1");
    });
  }

  function resolveItemOrderQuantityReadonly_v2(item) {
    if (!item) {
      return 0;
    }

    const styleOrder = Number.parseInt(String(item.style.order || "").trim(), 10);

    if (Number.isFinite(styleOrder)) {
      return styleOrder;
    }

    const dataOrder = Number.parseInt(
      String(item.getAttribute("data-appverbo-profile-order-v4") || "").trim(),
      10
    );

    if (Number.isFinite(dataOrder)) {
      return dataOrder;
    }

    return 0;
  }

  //###################################################################################
  // (7) CRIAR ELEMENTOS NO PADRAO CAMPO A CAMPO
  //###################################################################################

  function createHeaderQuantityReadonly_v2(rule, itemIndex, orderValue) {
    const header = document.createElement("div");

    header.className = "appverbo-quantity-readonly-header-v2";
    header.setAttribute("data-appverbo-quantity-readonly-v2", "1");
    header.setAttribute("data-profile-section-pane", rule.headerKey || "");
    header.style.gridColumn = "1 / -1";
    header.style.order = String(orderValue);
    header.textContent = rule.itemLabel + " " + String(itemIndex + 1);

    return header;
  }

  function createFieldQuantityReadonly_v2(rule, fieldKey, value, fieldMeta, orderValue) {
    const item = document.createElement("div");

    item.className = "personal-item appverbo-quantity-readonly-field-v2";
    item.setAttribute("data-appverbo-quantity-readonly-v2", "1");
    item.setAttribute("data-profile-section-pane", rule.headerKey || "");
    item.setAttribute("data-profile-field-key", fieldKey);
    item.style.order = String(orderValue);

    const label = document.createElement("span");
    label.className = "personal-label";
    label.textContent = fieldMeta.label || fieldKey;

    const strong = document.createElement("strong");
    strong.className = "personal-value";
    strong.textContent = formatValueQuantityReadonly_v2(value, fieldMeta.fieldType || "text");

    item.appendChild(label);
    item.appendChild(strong);

    return item;
  }

  function insertAfterQuantityReadonly_v2(referenceElement, newElement, grid) {
    if (referenceElement && referenceElement.parentElement === grid) {
      referenceElement.insertAdjacentElement("afterend", newElement);
      return newElement;
    }

    grid.appendChild(newElement);
    return newElement;
  }

  //###################################################################################
  // (8) VISIBILIDADE POR ABA
  //###################################################################################

  function applySectionVisibilityQuantityReadonly_v2() {
    const currentSection = getCurrentProfileSectionQuantityReadonly_v2();

    document.querySelectorAll("[data-appverbo-quantity-readonly-v2='1']").forEach(function (element) {
      const elementSection = normalizeKeyQuantityReadonly_v2(element.getAttribute("data-profile-section-pane") || "");

      if (!currentSection || !elementSection) {
        element.style.display = "";
        return;
      }

      element.style.display = currentSection === elementSection ? "" : "none";
    });
  }

  //###################################################################################
  // (9) RENDERIZAR
  //###################################################################################

  function renderQuantityReadonly_v2() {
    const grid = getReadonlyGridQuantityReadonly_v2();
    const setting = getMeuPerfilSettingQuantityReadonly_v2();

    if (!grid || !setting) {
      return;
    }

    cleanupLegacyQuantityReadonly_v2(grid);
    cleanupCurrentQuantityReadonly_v2(grid);
    restoreHiddenSourceFieldsQuantityReadonly_v2(grid);

    const rules = normalizeQuantityRulesQuantityReadonly_v2(setting.process_quantity_fields);
    const fieldMetaMap = getFieldMetaMapQuantityReadonly_v2(setting);

    rules.forEach(function (rule) {
      const values = getQuantityValuesQuantityReadonly_v2(rule.key);

      if (!values.length) {
        return;
      }

      let insertionPoint = findQuantityFieldElementQuantityReadonly_v2(grid, rule, fieldMetaMap);
      const insertionBaseOrder = resolveItemOrderQuantityReadonly_v2(insertionPoint);
      let nextOrder = insertionBaseOrder + 1;

      values.forEach(function (itemValues, itemIndex) {
        const header = createHeaderQuantityReadonly_v2(rule, itemIndex, nextOrder);
        insertionPoint = insertAfterQuantityReadonly_v2(insertionPoint, header, grid);
        nextOrder += 1;

        rule.repeatedFieldKeys.forEach(function (fieldKey) {
          const fieldMeta = fieldMetaMap.get(fieldKey) || {
            key: fieldKey,
            label: toSentenceCaseQuantityReadonly_v2(fieldKey),
            fieldType: "text"
          };

          const fieldElement = createFieldQuantityReadonly_v2(
            rule,
            fieldKey,
            itemValues ? itemValues[fieldKey] : "",
            fieldMeta,
            nextOrder
          );

          insertionPoint = insertAfterQuantityReadonly_v2(insertionPoint, fieldElement, grid);
          nextOrder += 1;
        });
      });

      hideSourceRepeatedFieldsQuantityReadonly_v2(grid, rule);
    });

    applySectionVisibilityQuantityReadonly_v2();
  }

  //###################################################################################
  // (10) ESTILO
  //###################################################################################

  function installStyleQuantityReadonly_v2() {
    if (document.getElementById("appverbo-profile-quantity-readonly-style-v2")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "appverbo-profile-quantity-readonly-style-v2";
    style.textContent = [
      ".appverbo-quantity-readonly-header-v2 { margin: 14px 0 2px; font-size: 14px; font-weight: 800; color: #0f172a; }",
      ".appverbo-quantity-readonly-field-v2 { min-height: 48px; }"
    ].join("\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (11) INICIAR
  //###################################################################################

  function startQuantityReadonly_v2() {
    installStyleQuantityReadonly_v2();

    renderQuantityReadonly_v2();

    window.setTimeout(renderQuantityReadonly_v2, 100);
    window.setTimeout(renderQuantityReadonly_v2, 400);
    window.setTimeout(renderQuantityReadonly_v2, 900);
    window.setTimeout(renderQuantityReadonly_v2, 1600);
  }

  function shouldReactToSectionChangeQuantityReadonly_v2(event) {
    const target = event && event.target ? event.target : null;

    if (!target || typeof target.closest !== "function") {
      return false;
    }

    if (
      target.closest("#submenu-items .submenu-item[data-profile-section]") ||
      target.closest(".submenu-item[data-profile-section]") ||
      target.closest("[data-profile-section-tab]") ||
      target.closest("[data-profile-section-button]") ||
      target.closest(".profile-section-tab")
    ) {
      return true;
    }

    if (target.matches("input[name='profile_section'], [data-meu-perfil-section-input], [data-profile-section-input]")) {
      return true;
    }

    if (
      target.closest("[data-edit-cancel]") ||
      target.closest(".profile-cancel-btn") ||
      target.closest(".action-btn-cancel")
    ) {
      return true;
    }

    return false;
  }

  document.addEventListener("click", function (event) {
    if (!shouldReactToSectionChangeQuantityReadonly_v2(event)) {
      return;
    }

    window.setTimeout(applySectionVisibilityQuantityReadonly_v2, 0);
    window.setTimeout(renderQuantityReadonly_v2, 80);
    window.setTimeout(renderQuantityReadonly_v2, 220);
  }, true);

  document.addEventListener("change", function (event) {
    if (!shouldReactToSectionChangeQuantityReadonly_v2(event)) {
      return;
    }

    window.setTimeout(applySectionVisibilityQuantityReadonly_v2, 0);
    window.setTimeout(renderQuantityReadonly_v2, 0);
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startQuantityReadonly_v2);
  }
  else {
    startQuantityReadonly_v2();
  }

  window.addEventListener("pageshow", startQuantityReadonly_v2);
})();
// APPVERBO_PROFILE_QUANTITY_READONLY_RENDERER_V2_END
