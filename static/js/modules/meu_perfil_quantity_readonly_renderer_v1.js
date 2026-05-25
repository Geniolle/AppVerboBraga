// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_MODULE_START
(function registerMeuPerfilQuantityReadonlyRendererV1Module() {
  "use strict";

  window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1 = function setupMeuPerfilQuantityReadonlyRendererV1(options) {
    const deps = options && typeof options === "object" ? options : {};
// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1) VISUALIZACAO DOS CAMPOS QUANTIDADE
//###################################################################################

(function setupMeuPerfilQuantityReadonlyRendererV1() {
  "use strict";

  if (window.__APPVERBO_QUANTITY_READONLY_RENDERER_V2_ACTIVE) {
    return;
  }

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeTextQuantityReadonlyV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function getMeuPerfilSettingQuantityReadonlyV1() {
    if (typeof getSidebarMenuSetting === "function") {
      const foundSetting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
      if (foundSetting) {
        return foundSetting;
      }
    }

    return (Array.isArray(sidebarMenuSettings) ? sidebarMenuSettings : []).find((setting) => {
      return normalizeMenuKey(setting && setting.key) === MEU_PERFIL_MENU_KEY;
    }) || null;
  }

  function getReadonlyGridQuantityReadonlyV1() {
    return document.querySelector("#perfil-pessoal-card .profile-readonly .personal-grid");
  }

  function getQuantityReadonlyValuesV1(ruleKey) {
    const cleanRuleKey = normalizeMenuKey(ruleKey);
    const valuesByMenu = (
      menuProcessQuantityValuesMap &&
      typeof menuProcessQuantityValuesMap === "object" &&
      !Array.isArray(menuProcessQuantityValuesMap)
    )
      ? menuProcessQuantityValuesMap[MEU_PERFIL_MENU_KEY]
      : null;

    if (!valuesByMenu || typeof valuesByMenu !== "object" || Array.isArray(valuesByMenu)) {
      return [];
    }

    return normalizeProcessQuantityItems(valuesByMenu[cleanRuleKey]);
  }

  function buildFieldMetaMapQuantityReadonlyV1(setting) {
    const metaMap = new Map();

    (Array.isArray(setting && setting.process_field_options) ? setting.process_field_options : []).forEach((option) => {
      const fieldKey = normalizeMenuKey(option && option.key);

      if (!fieldKey) {
        return;
      }

      metaMap.set(fieldKey, {
        key: fieldKey,
        label: toSentenceCaseText(option.label || fieldKey),
        fieldType: normalizeProcessFieldType(option.field_type)
      });
    });

    return metaMap;
  }

  function formatReadonlyValueQuantityReadonlyV1(value, fieldType) {
    const cleanValue = safeTextQuantityReadonlyV1(value).trim();

    if (!cleanValue) {
      return "-";
    }

    if (fieldType === "flag") {
      return ["1", "true", "sim", "yes", "on"].includes(cleanValue.toLowerCase())
        ? "Sim"
        : "Não";
    }

    return cleanValue;
  }

  function applyCurrentProfileSectionToQuantityReadonlyV1(host) {
    if (!host) {
      return;
    }

    const sectionInput = document.querySelector("[data-meu-perfil-section-input]");
    const currentSection = normalizeMenuKey(sectionInput ? sectionInput.value : "");
    const hostSection = normalizeMenuKey(host.dataset.profileSectionPane);

    if (!currentSection || !hostSection) {
      return;
    }

    host.style.display = currentSection === hostSection ? "" : "none";
  }

  function findInsertionPointQuantityReadonlyV1(grid, rule) {
    if (!grid || !rule) {
      return null;
    }

    const quantityFieldKey = normalizeMenuKey(rule.quantityFieldKey);

    if (!quantityFieldKey) {
      return null;
    }

    return grid.querySelector("[data-profile-field-key='" + quantityFieldKey + "']");
  }

  //###################################################################################
  // (2) RENDERIZAR REGRA READONLY
  //###################################################################################

  function renderReadonlyRuleQuantityReadonlyV1(grid, setting, rule, fieldMetaMap) {
    const values = getQuantityReadonlyValuesV1(rule.key);

    if (!Array.isArray(values) || !values.length) {
      return;
    }

    const host = document.createElement("div");

    host.className = "personal-item profile-quantity-readonly-v1";
    host.style.gridColumn = "1 / -1";
    host.dataset.profileQuantityReadonlyRuleKey = rule.key;
    host.dataset.profileSectionPane = rule.headerKey || "";

    const mainLabel = document.createElement("span");
    mainLabel.className = "personal-label";
    mainLabel.textContent = rule.label || rule.itemLabel || "Itens";
    host.appendChild(mainLabel);

    const listWrapper = document.createElement("div");
    listWrapper.className = "profile-quantity-readonly-list-v1";

    values.forEach((itemValues, itemIndex) => {
      const itemBlock = document.createElement("div");
      itemBlock.className = "profile-quantity-readonly-item-v1";

      const itemTitle = document.createElement("strong");
      itemTitle.className = "personal-value profile-quantity-readonly-title-v1";
      itemTitle.textContent = (rule.itemLabel || "Item") + " " + (itemIndex + 1);
      itemBlock.appendChild(itemTitle);

      const fieldsList = document.createElement("div");
      fieldsList.className = "profile-quantity-readonly-fields-v1";

      rule.repeatedFieldKeys.forEach((fieldKey) => {
        const cleanFieldKey = normalizeMenuKey(fieldKey);
        const fieldMeta = fieldMetaMap.get(cleanFieldKey) || {
          label: cleanFieldKey,
          fieldType: "text"
        };

        const row = document.createElement("div");
        row.className = "profile-quantity-readonly-field-v1";

        const label = document.createElement("span");
        label.className = "personal-label";
        label.textContent = fieldMeta.label || cleanFieldKey;

        const value = document.createElement("strong");
        value.className = "personal-value";
        value.textContent = formatReadonlyValueQuantityReadonlyV1(
          itemValues ? itemValues[cleanFieldKey] : "",
          fieldMeta.fieldType
        );

        row.appendChild(label);
        row.appendChild(value);
        fieldsList.appendChild(row);
      });

      itemBlock.appendChild(fieldsList);
      listWrapper.appendChild(itemBlock);
    });

    host.appendChild(listWrapper);

    const insertionPoint = findInsertionPointQuantityReadonlyV1(grid, rule);

    if (insertionPoint && insertionPoint.parentElement === grid) {
      insertionPoint.insertAdjacentElement("afterend", host);
    } else {
      grid.appendChild(host);
    }

    applyCurrentProfileSectionToQuantityReadonlyV1(host);
  }

  //###################################################################################
  // (3) RENDERIZAR TODAS AS REGRAS
  //###################################################################################

  function renderMeuPerfilQuantityReadonlyV1() {
    const grid = getReadonlyGridQuantityReadonlyV1();
    const setting = getMeuPerfilSettingQuantityReadonlyV1();

    if (!grid || !setting) {
      return;
    }

    Array.from(grid.querySelectorAll("[data-profile-quantity-readonly-rule-key]")).forEach((element) => {
      element.remove();
    });

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    if (!rules.length) {
      return;
    }

    const fieldMetaMap = buildFieldMetaMapQuantityReadonlyV1(setting);

    rules.forEach((rule) => {
      renderReadonlyRuleQuantityReadonlyV1(grid, setting, rule, fieldMetaMap);
    });
  }

  //###################################################################################
  // (4) SINCRONIZAR COM AS ABAS DO MEU PERFIL
  //###################################################################################

  function refreshMeuPerfilQuantityReadonlyVisibilityV1() {
    document
      .querySelectorAll("[data-profile-quantity-readonly-rule-key]")
      .forEach(applyCurrentProfileSectionToQuantityReadonlyV1);
  }

  function shouldRunMeuPerfilQuantityReadonlyV1(event) {
    const currentMenuKey = typeof normalizeMenuKey === "function"
      ? normalizeMenuKey(activeMenuKey)
      : "";

    if (currentMenuKey === MEU_PERFIL_MENU_KEY) {
      return true;
    }

    const targetEl = event && event.target ? event.target : null;

    return Boolean(
      targetEl &&
      typeof targetEl.closest === "function" &&
      targetEl.closest("#perfil-pessoal-card")
    );
  }

  document.addEventListener("click", function (event) {
    if (!shouldRunMeuPerfilQuantityReadonlyV1(event)) {
      return;
    }

    window.setTimeout(refreshMeuPerfilQuantityReadonlyVisibilityV1, 0);
    window.setTimeout(refreshMeuPerfilQuantityReadonlyVisibilityV1, 80);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderMeuPerfilQuantityReadonlyV1);
  } else {
    renderMeuPerfilQuantityReadonlyV1();
  }

  window.setTimeout(renderMeuPerfilQuantityReadonlyV1, 150);
  window.setTimeout(renderMeuPerfilQuantityReadonlyV1, 600);
})();

// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_END
  };
})();
// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_MODULE_END
