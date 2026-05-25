// APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1_MODULE_START
(function registerMeuPerfilSubsequentVisibilityV1Module() {
  "use strict";

  window.APPVERBO_SETUP_MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1 = function setupMeuPerfilSubsequentVisibilityV1(options) {
    const deps = options && typeof options === "object" ? options : {};

    const activeMenuKey = typeof deps.activeMenuKey === "undefined" ? "" : deps.activeMenuKey;
    const MEU_PERFIL_MENU_KEY = String(deps.MEU_PERFIL_MENU_KEY || "meu_perfil");
    const sidebarMenuSettings = Array.isArray(deps.sidebarMenuSettings)
      ? deps.sidebarMenuSettings
      : [];
    const profilePersonalSections = Array.isArray(deps.profilePersonalSections)
      ? deps.profilePersonalSections
      : [];
    const normalizeMenuKey = typeof deps.normalizeMenuKey === "function"
      ? deps.normalizeMenuKey
      : function normalizeMenuKeyFallbackMeuPerfilSubsequentV1(value) {
        return String(value === null || value === undefined ? "" : value).trim().toLowerCase();
      };
    const normalizeLookupText = typeof deps.normalizeLookupText === "function"
      ? deps.normalizeLookupText
      : function normalizeLookupTextFallbackMeuPerfilSubsequentV1(value) {
        return String(value === null || value === undefined ? "" : value)
          .trim()
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "");
      };
    const getSidebarMenuSetting = typeof deps.getSidebarMenuSetting === "function"
      ? deps.getSidebarMenuSetting
      : function getSidebarMenuSettingFallbackMeuPerfilSubsequentV1() { return null; };
    const normalizeProcessFieldType = typeof deps.normalizeProcessFieldType === "function"
      ? deps.normalizeProcessFieldType
      : function normalizeProcessFieldTypeFallbackMeuPerfilSubsequentV1(value) {
        return String(value === null || value === undefined ? "" : value).trim().toLowerCase();
      };
    const normalizeProcessSubsequentRules = typeof deps.normalizeProcessSubsequentRules === "function"
      ? deps.normalizeProcessSubsequentRules
      : function normalizeProcessSubsequentRulesFallbackMeuPerfilSubsequentV1(rules) {
        return Array.isArray(rules) ? rules : [];
      };
    const getHiddenProcessTargets = typeof deps.getHiddenProcessTargets === "function"
      ? deps.getHiddenProcessTargets
      : function getHiddenProcessTargetsFallbackMeuPerfilSubsequentV1() { return new Set(); };
    const isMeuPerfilQuantityV4GeneratedTarget = typeof deps.isMeuPerfilQuantityV4GeneratedTarget === "function"
      ? deps.isMeuPerfilQuantityV4GeneratedTarget
      : function isMeuPerfilQuantityV4GeneratedTargetFallbackMeuPerfilSubsequentV1() { return false; };
// APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1_START
//###################################################################################
// (MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1) APLICAR CAMPOS SUBSEQUENTES NO MEU PERFIL
//###################################################################################

(function setupMeuPerfilSubsequentVisibilityV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS BASE
  //###################################################################################

  function safeSubsequentTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeSubsequentKeyV1(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeSubsequentTextV1(value).trim().toLowerCase();
  }

  function normalizeSubsequentLookupV1(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeSubsequentTextV1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getMeuPerfilSettingSubsequentV1() {
    if (typeof getSidebarMenuSetting === "function") {
      const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);

      if (setting) {
        return setting;
      }
    }

    return (Array.isArray(sidebarMenuSettings) ? sidebarMenuSettings : []).find((setting) => {
      return normalizeSubsequentKeyV1(setting && setting.key) === MEU_PERFIL_MENU_KEY;
    }) || null;
  }

  function getCurrentProfileSectionSubsequentV1() {
    const selectors = [
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    for (const selector of selectors) {
      const input = document.querySelector(selector);
      const value = normalizeSubsequentKeyV1(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    const activeTab = document.querySelector(
      "#perfil-pessoal-card [data-profile-section-tab].active, " +
      "#perfil-pessoal-card [data-profile-section-button].active, " +
      "#perfil-pessoal-card .profile-section-tab.active, " +
      "#perfil-pessoal-card .active"
    );

    if (activeTab) {
      const dataSection = normalizeSubsequentKeyV1(
        activeTab.dataset.profileSection ||
        activeTab.dataset.profileSectionKey ||
        activeTab.dataset.profileSectionTab ||
        activeTab.dataset.sectionKey ||
        ""
      );

      if (dataSection) {
        return dataSection;
      }

      const activeLabel = normalizeSubsequentLookupV1(activeTab.textContent);
      const sections = Array.isArray(profilePersonalSections) ? profilePersonalSections : [];

      for (const section of sections) {
        if (normalizeSubsequentLookupV1(section && section.label) === activeLabel) {
          return normalizeSubsequentKeyV1(section && section.key);
        }
      }
    }

    return "";
  }

  //###################################################################################
  // (2) METADADOS DOS CAMPOS
  //###################################################################################

  function buildMeuPerfilFieldMetaMapSubsequentV1(setting) {
    const metaMap = new Map();

    (Array.isArray(setting && setting.process_field_options) ? setting.process_field_options : []).forEach((option) => {
      const key = normalizeSubsequentKeyV1(option && option.key);

      if (!key) {
        return;
      }

      metaMap.set(key, {
        key,
        label: safeSubsequentTextV1(option.label || key).trim(),
        lookupLabel: normalizeSubsequentLookupV1(option.label || key),
        fieldType: normalizeProcessFieldType(option.field_type)
      });
    });

    return metaMap;
  }

  function isHeaderTargetSubsequentV1(fieldKey, fieldMetaMap) {
    const cleanKey = normalizeSubsequentKeyV1(fieldKey);
    const meta = fieldMetaMap.get(cleanKey);

    return Boolean(meta && normalizeProcessFieldType(meta.fieldType) === "header");
  }

  //###################################################################################
  // (3) LEITURA DOS VALORES ATUAIS
  //###################################################################################

  function resolveProfileControlNameSubsequentV1(fieldKey) {
    const cleanKey = normalizeSubsequentKeyV1(fieldKey);

    if (!cleanKey) {
      return "";
    }

    if (cleanKey.startsWith("custom_")) {
      return "custom_field__" + cleanKey;
    }

    const builtinNames = {
      nome: "full_name",
      email: "login_email",
      telefone: "primary_phone",
      pais: "country",
      data_nascimento: "birth_date",
      estado_civil: "estado_civil",
      tem_filhos: "tem_filhos"
    };

    return builtinNames[cleanKey] || cleanKey;
  }

  function readControlValueSubsequentV1(control) {
    if (!control) {
      return "";
    }

    const tagName = safeSubsequentTextV1(control.tagName).toLowerCase();
    const type = safeSubsequentTextV1(control.type).toLowerCase();

    if (type === "checkbox") {
      return control.checked ? "Sim" : "Não";
    }

    if (tagName === "select") {
      const rawValue = safeSubsequentTextV1(control.value).trim();
      const optionText = control.options && control.selectedIndex >= 0
        ? safeSubsequentTextV1(control.options[control.selectedIndex].textContent).trim()
        : "";

      return optionText || rawValue;
    }

    return safeSubsequentTextV1(control.value).trim();
  }

  function findFieldWrapperSubsequentV1(fieldKey) {
    const cleanKey = normalizeSubsequentKeyV1(fieldKey);

    if (!cleanKey) {
      return null;
    }

    return document.querySelector(
      "#perfil-pessoal-card [data-profile-field-key='" + cleanKey + "']"
    );
  }

  function readReadonlyValueSubsequentV1(fieldKey) {
    const wrapper = findFieldWrapperSubsequentV1(fieldKey);

    if (!wrapper) {
      return "";
    }

    const valueElement = wrapper.querySelector(".personal-value, strong, output");

    if (valueElement) {
      return safeSubsequentTextV1(valueElement.textContent).trim();
    }

    const labelElement = wrapper.querySelector(".personal-label, label");
    const labelText = labelElement ? safeSubsequentTextV1(labelElement.textContent).trim() : "";
    const fullText = safeSubsequentTextV1(wrapper.textContent).trim();

    if (labelText && fullText.startsWith(labelText)) {
      return fullText.slice(labelText.length).trim();
    }

    return fullText;
  }

  function readProfileFieldValueSubsequentV1(fieldKey) {
    const cleanKey = normalizeSubsequentKeyV1(fieldKey);
    const controlName = resolveProfileControlNameSubsequentV1(cleanKey);

    const controls = [];

    if (controlName) {
      document.querySelectorAll(
        "#perfil-pessoal-card [name='" + controlName + "'], " +
        "[name='" + controlName + "']"
      ).forEach((control) => controls.push(control));
    }

    document.querySelectorAll(
      "#perfil-pessoal-card [data-profile-field-key='" + cleanKey + "'] input, " +
      "#perfil-pessoal-card [data-profile-field-key='" + cleanKey + "'] select, " +
      "#perfil-pessoal-card [data-profile-field-key='" + cleanKey + "'] textarea"
    ).forEach((control) => controls.push(control));

    for (const control of controls) {
      if (!control || control.disabled) {
        continue;
      }

      const value = readControlValueSubsequentV1(control);

      if (value) {
        return value;
      }
    }

    return readReadonlyValueSubsequentV1(cleanKey);
  }

  function buildValuesByFieldSubsequentV1(rules) {
    const valuesByField = {};

    normalizeProcessSubsequentRules(rules).forEach((rule) => {
      const triggerField = normalizeSubsequentKeyV1(rule.triggerField);

      if (!triggerField || Object.prototype.hasOwnProperty.call(valuesByField, triggerField)) {
        return;
      }

      valuesByField[triggerField] = readProfileFieldValueSubsequentV1(triggerField);
    });

    return valuesByField;
  }

  //###################################################################################
  // (4) ENCONTRAR E OCULTAR CAMPOS
  //###################################################################################

  function getWrappersByLabelSubsequentV1(fieldKey, fieldMetaMap) {
    const meta = fieldMetaMap.get(normalizeSubsequentKeyV1(fieldKey));
    const labelLookup = normalizeSubsequentLookupV1(meta && meta.label);

    if (!labelLookup) {
      return [];
    }

    const wrappers = [];

    document.querySelectorAll("#perfil-pessoal-card .field, #perfil-pessoal-card .personal-item").forEach((wrapper) => {
      const labelElement = wrapper.querySelector("label, .personal-label");

      if (!labelElement) {
        return;
      }

      const wrapperLabel = normalizeSubsequentLookupV1(labelElement.textContent);

      if (wrapperLabel === labelLookup) {
        wrappers.push(wrapper);
      }
    });

    return wrappers;
  }

  function getFieldWrappersSubsequentV1(fieldKey, fieldMetaMap) {
    const cleanKey = normalizeSubsequentKeyV1(fieldKey);
    const wrappers = [];

    document.querySelectorAll(
      "#perfil-pessoal-card [data-profile-field-key='" + cleanKey + "']"
    ).forEach((element) => {
      const wrapper = (
        element.classList && (element.classList.contains("field") || element.classList.contains("personal-item"))
      )
        ? element
        : (element.closest(".field, .personal-item") || element);

      if (wrapper && !wrappers.includes(wrapper)) {
        wrappers.push(wrapper);
      }
    });

    getWrappersByLabelSubsequentV1(cleanKey, fieldMetaMap).forEach((wrapper) => {
      if (wrapper && !wrappers.includes(wrapper)) {
        wrappers.push(wrapper);
      }
    });

    return wrappers;
  }

  function disableWrapperSubsequentV1(wrapper) {
    if (!wrapper) {
      return;
    }

    wrapper.dataset.profileSubsequentHiddenV1 = "1";
    wrapper.hidden = true;
    wrapper.style.display = "none";

    wrapper.querySelectorAll("input, select, textarea, button").forEach((control) => {
      if (!control.disabled) {
        control.dataset.profileSubsequentDisabledV1 = "1";
        control.disabled = true;
      }
    });
  }

  function enableWrapperSubsequentV1(wrapper) {
    if (!wrapper) {
      return;
    }

    delete wrapper.dataset.profileSubsequentHiddenV1;

    const currentSection = getCurrentProfileSectionSubsequentV1();
    const wrapperSection = normalizeSubsequentKeyV1(wrapper.dataset.profileSectionPane);

    if (wrapper.dataset.profileQuantityOriginDuplicateV1 === "1") {
      wrapper.hidden = true;
      wrapper.style.display = "none";
      return;
    }

    if (currentSection && wrapperSection && currentSection !== wrapperSection) {
      wrapper.hidden = true;
      wrapper.style.display = "none";
    } else {
      wrapper.hidden = false;
      wrapper.style.display = "";
    }

    wrapper.querySelectorAll("input, select, textarea, button").forEach((control) => {
      if (control.dataset.profileSubsequentDisabledV1 === "1") {
        control.disabled = false;
        delete control.dataset.profileSubsequentDisabledV1;
      }
    });
  }

  //###################################################################################
  // (5) OCULTAR/EXIBIR SECOES QUANDO O TARGET FOR CABECALHO
  //###################################################################################

  function getSectionTabsSubsequentV1(sectionKey, fieldMetaMap) {
    const cleanSectionKey = normalizeSubsequentKeyV1(sectionKey);
    const meta = fieldMetaMap.get(cleanSectionKey);
    const labelLookup = normalizeSubsequentLookupV1(meta && meta.label);
    const tabs = [];

    document.querySelectorAll(
      "#perfil-pessoal-card [data-profile-section-tab], " +
      "#perfil-pessoal-card [data-profile-section-button], " +
      "#perfil-pessoal-card .profile-section-tab, " +
      "#perfil-pessoal-card button, " +
      "#perfil-pessoal-card a"
    ).forEach((tab) => {
      const dataKey = normalizeSubsequentKeyV1(
        tab.dataset.profileSection ||
        tab.dataset.profileSectionKey ||
        tab.dataset.profileSectionTab ||
        tab.dataset.sectionKey ||
        ""
      );

      const textLookup = normalizeSubsequentLookupV1(tab.textContent);

      if ((dataKey && dataKey === cleanSectionKey) || (labelLookup && textLookup === labelLookup)) {
        tabs.push(tab);
      }
    });

    return tabs;
  }

  function setSectionVisibleSubsequentV1(sectionKey, visible, fieldMetaMap) {
    const cleanSectionKey = normalizeSubsequentKeyV1(sectionKey);

    if (!cleanSectionKey) {
      return;
    }

    getSectionTabsSubsequentV1(cleanSectionKey, fieldMetaMap).forEach((tab) => {
      tab.hidden = !visible;
      tab.style.display = visible ? "" : "none";
      tab.dataset.profileSubsequentSectionHiddenV1 = visible ? "" : "1";
    });

    document.querySelectorAll(
      "#perfil-pessoal-card [data-profile-section-pane='" + cleanSectionKey + "']"
    ).forEach((element) => {
      if (visible) {
        enableWrapperSubsequentV1(element);
      } else {
        disableWrapperSubsequentV1(element);
      }
    });
  }

  //###################################################################################
  // (6) APLICAR REGRAS
  //###################################################################################

  function applyMeuPerfilSubsequentVisibilityV1() {
    const setting = getMeuPerfilSettingSubsequentV1();

    if (!setting) {
      return;
    }

    const rawRules = setting.process_subsequent_rules || setting.process_subsequent_fields || setting.process_subsequent || [];

    const rules = normalizeProcessSubsequentRules(rawRules);

    if (!rules.length) {
      return;
    }

    const fieldMetaMap = buildMeuPerfilFieldMetaMapSubsequentV1(setting);
    const valuesByField = buildValuesByFieldSubsequentV1(rules);
    const hiddenTargets = getHiddenProcessTargets(rules, valuesByField);
    const targetFields = new Set();

    rules.forEach((rule) => {
      if (rule && rule.targetField) {
        targetFields.add(normalizeSubsequentKeyV1(rule.targetField));
      }
    });

    targetFields.forEach((targetField) => {
      const shouldHide = hiddenTargets.has(targetField);

      if (isHeaderTargetSubsequentV1(targetField, fieldMetaMap)) {
        setSectionVisibleSubsequentV1(targetField, !shouldHide, fieldMetaMap);
        return;
      }

      getFieldWrappersSubsequentV1(targetField, fieldMetaMap).forEach((wrapper) => {
        if (shouldHide) {
          disableWrapperSubsequentV1(wrapper);
        } else {
          enableWrapperSubsequentV1(wrapper);
        }
      });
    });
  }

  function scheduleMeuPerfilSubsequentVisibilityV1() {
    window.setTimeout(applyMeuPerfilSubsequentVisibilityV1, 0);
    window.setTimeout(applyMeuPerfilSubsequentVisibilityV1, 80);
    window.setTimeout(applyMeuPerfilSubsequentVisibilityV1, 250);
  }

  //###################################################################################
  // (7) EVENTOS
  //###################################################################################

  function shouldRunMeuPerfilSubsequentVisibilityV1(event) {
    const targetEl = event && event.target ? event.target : null;

    if (isMeuPerfilQuantityV4GeneratedTarget(targetEl)) {
      return false;
    }

    const currentMenuKey = typeof normalizeMenuKey === "function"
      ? normalizeMenuKey(activeMenuKey)
      : "";

    if (currentMenuKey === MEU_PERFIL_MENU_KEY) {
      return true;
    }

    return Boolean(
      targetEl &&
      typeof targetEl.closest === "function" &&
      targetEl.closest("#perfil-pessoal-card")
    );
  }

  document.addEventListener("input", function (event) {
    if (!shouldRunMeuPerfilSubsequentVisibilityV1(event)) {
      return;
    }
    scheduleMeuPerfilSubsequentVisibilityV1();
  }, true);
  document.addEventListener("change", function (event) {
    if (!shouldRunMeuPerfilSubsequentVisibilityV1(event)) {
      return;
    }
    scheduleMeuPerfilSubsequentVisibilityV1();
  }, true);
  document.addEventListener("click", function (event) {
    if (!shouldRunMeuPerfilSubsequentVisibilityV1(event)) {
      return;
    }
    scheduleMeuPerfilSubsequentVisibilityV1();
  }, true);
  document.addEventListener("appverbo:profile-section-restored", function (event) {
    if (!shouldRunMeuPerfilSubsequentVisibilityV1(event)) {
      return;
    }
    scheduleMeuPerfilSubsequentVisibilityV1();
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleMeuPerfilSubsequentVisibilityV1);
  } else {
    scheduleMeuPerfilSubsequentVisibilityV1();
  }

  window.setTimeout(scheduleMeuPerfilSubsequentVisibilityV1, 150);
  window.setTimeout(scheduleMeuPerfilSubsequentVisibilityV1, 600);
  window.setTimeout(scheduleMeuPerfilSubsequentVisibilityV1, 1200);
})();

// APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1_END
  };
})();
// APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1_MODULE_END
