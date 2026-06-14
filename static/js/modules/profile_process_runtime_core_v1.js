// APPVERBO_PROFILE_PROCESS_RUNTIME_CORE_V1_MODULE_START
(function registerProfileProcessRuntimeCoreV1Module() {
  "use strict";

  window.APPVERBO_SETUP_PROFILE_PROCESS_RUNTIME_CORE_V1 = function setupProfileProcessRuntimeCoreV1(options) {
    const deps = options && typeof options === "object" ? options : {};

    if (!window.__APPVERBO_PROFILE_PROCESS_RUNTIME_CORE_V1_READY) {
function setupProfileProcessTabs() {
  const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  if (!personalCardEl) {
    return;
  }
  const profileCardTitleEl = personalCardEl.querySelector("[data-profile-card-title]");
  const profilePersonalSections = (
    Array.isArray(deps.profilePersonalSections) && deps.profilePersonalSections.length
  )
    ? deps.profilePersonalSections
    : (Array.isArray(bootstrap.profilePersonalSections) ? bootstrap.profilePersonalSections : []);
  const fallbackProfileCardTitle = String(
    (profileCardTitleEl && profileCardTitleEl.getAttribute("data-profile-card-title-default")) ||
    (profileCardTitleEl && profileCardTitleEl.textContent) ||
    "Dados pessoais"
  ).trim() || "Dados pessoais";
  const profileSectionLabelsByKey = new Map();

  //###################################################################################
  // (1) SINCRONIZAR TITULO DO CARD COM A ABA ATIVA
  //###################################################################################
  function normalizeProfileSectionKeyV1(value) {
    return String(value || "").trim().toLowerCase() || "geral";
  }

  function escapeProfileSectionSelectorValueV1(value) {
    const cleanValue = String(value || "");
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(cleanValue);
    }
    return cleanValue.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  }

  profilePersonalSections.forEach((section) => {
    const cleanSectionKey = normalizeProfileSectionKeyV1(section && section.key);
    const cleanSectionLabel = String(section && section.label || "").trim();
    if (!cleanSectionKey || !cleanSectionLabel || profileSectionLabelsByKey.has(cleanSectionKey)) {
      return;
    }
    profileSectionLabelsByKey.set(cleanSectionKey, cleanSectionLabel);
  });

  function resolveProfileCardTitleV1(sectionKey) {
    const cleanSectionKey = normalizeProfileSectionKeyV1(sectionKey);
    const mappedTitle = String(profileSectionLabelsByKey.get(cleanSectionKey) || "").trim();
    if (mappedTitle) {
      return mappedTitle;
    }
    if (itemsEl) {
      const sectionLinkEl = itemsEl.querySelector(
        `.submenu-item[data-profile-section="${escapeProfileSectionSelectorValueV1(cleanSectionKey)}"]`
      );
      const linkTitle = String((sectionLinkEl && sectionLinkEl.textContent) || "").trim();
      if (linkTitle) {
        return linkTitle;
      }
    }
    return fallbackProfileCardTitle;
  }

  function syncProfileCardTitleV1(sectionKey) {
    if (!profileCardTitleEl) {
      return;
    }
    profileCardTitleEl.textContent = resolveProfileCardTitleV1(sectionKey);
  }

  const sectionPanes = personalCardEl.querySelectorAll("[data-profile-section-pane]");
  if (!sectionPanes.length) {
    return;
  }

  function activateSection(sectionKey) {
    const normalizedSection = normalizeProfileSectionKeyV1(sectionKey);
    const availableSections = new Set(
      Array.from(sectionPanes)
        .map((paneEl) =>
          normalizeProfileSectionKeyV1(paneEl.getAttribute("data-profile-section-pane") || "geral")
        )
        .filter((section) => !hiddenMeuPerfilSectionKeys.has(section))
    );
    const effectiveSection = availableSections.has(normalizedSection)
      ? normalizedSection
      : (Array.from(availableSections)[0] || "geral");

    syncProfileCardTitleV1(effectiveSection);

    sectionPanes.forEach((paneEl) => {
      const paneSection = normalizeProfileSectionKeyV1(
        paneEl.getAttribute("data-profile-section-pane") || "geral"
      );
      const isFieldHiddenBySubsequentRules = paneEl.dataset.profileSubsequentHiddenV1 === "1";
      paneEl.style.display = (
        !hiddenMeuPerfilSectionKeys.has(paneSection) &&
        paneSection === effectiveSection &&
        !isFieldHiddenBySubsequentRules
      ) ? "" : "none";
    });
    const sectionInputEl = personalCardEl.querySelector("[data-meu-perfil-section-input]");
    if (sectionInputEl) {
      sectionInputEl.value = effectiveSection;
    }
    setupAllocationSectionMultiValue(personalCardEl, effectiveSection);
    meuPerfilSelectedProfileSection = effectiveSection;
  }

  window.activateProfilePersonalSection = activateSection;
  activateSection(meuPerfilSelectedProfileSection);
}

function collectCurrentMeuPerfilProcessValues() {
  const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  const valuesByField = {};
  if (!formEl) {
    return valuesByField;
  }

  const fixedFieldMap = {
    full_name: "nome",
    primary_phone: "telefone",
    login_email: "email",
    country: "pais",
    birth_date: "data_nascimento",
    whatsapp_notice_opt_in: "autorizacao_whatsapp"
  };
  const readonlyFieldMap = {
    edit_whatsapp_status: "whatsapp",
    edit_account_status: "conta",
    edit_member_status: "estado_membro",
    edit_is_collaborator: "colaborador",
    edit_entities_readonly: "entidades",
    edit_whatsapp_last_check: "ultima_verificacao_whatsapp",
    edit_whatsapp_last_error: "detalhe_verificacao"
  };
  const bootstrapReadonlyValues = {
    conta: String(bootstrap.currentUserAccountStatus || "").trim(),
    estado_membro: String(bootstrap.currentUserMemberStatus || "").trim(),
    entidades: String(bootstrap.currentUserEntities || "").trim()
  };

  formEl.querySelectorAll("[name]").forEach((controlEl) => {
    const rawName = String(controlEl.getAttribute("name") || "").trim();
    let fieldKey = "";
    if (rawName.startsWith("custom_field__")) {
      fieldKey = normalizeMenuKey(rawName.replace(/^custom_field__/, ""));
    } else {
      fieldKey = normalizeMenuKey(fixedFieldMap[rawName] || "");
    }
    if (!fieldKey) {
      return;
    }
    if (controlEl.type === "checkbox") {
      valuesByField[fieldKey] = controlEl.checked ? "1" : "0";
      return;
    }
    valuesByField[fieldKey] = String(controlEl.value || "").trim();
  });

  Object.keys(readonlyFieldMap).forEach((controlId) => {
    const controlEl = formEl.querySelector("#" + controlId);
    const fieldKey = normalizeMenuKey(readonlyFieldMap[controlId] || "");
    if (!controlEl || !fieldKey) {
      return;
    }
    valuesByField[fieldKey] = String(controlEl.value || "").trim();
  });

  Object.keys(bootstrapReadonlyValues).forEach((fieldKey) => {
    const cleanFieldKey = normalizeMenuKey(fieldKey);
    const fieldValue = String(bootstrapReadonlyValues[fieldKey] || "").trim();
    if (!cleanFieldKey || !fieldValue || Object.prototype.hasOwnProperty.call(valuesByField, cleanFieldKey)) {
      return;
    }
    valuesByField[cleanFieldKey] = fieldValue;
  });

  return valuesByField;
}

function getMeuPerfilProcessFieldKeyFromControl(controlEl) {
  if (!controlEl || typeof controlEl.getAttribute !== "function") {
    return "";
  }

  const rawName = String(controlEl.getAttribute("name") || "").trim();

  if (!rawName) {
    return "";
  }

  if (rawName.startsWith("custom_field__")) {
    return normalizeMenuKey(rawName.replace(/^custom_field__/, ""));
  }

  const fixedFieldMap = {
    full_name: "nome",
    primary_phone: "telefone",
    login_email: "email",
    country: "pais",
    birth_date: "data_nascimento",
    whatsapp_notice_opt_in: "autorizacao_whatsapp"
  };

  return normalizeMenuKey(fixedFieldMap[rawName] || "");
}

function applyMeuPerfilProcessSubsequentVisibility() {
  const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  if (!setting || !personalCardEl) {
    return;
  }

  hiddenMeuPerfilSectionKeys = getHiddenProcessTargets(
    setting.process_subsequent_fields,
    collectCurrentMeuPerfilProcessValues()
  );

  if (itemsEl) {
    const submenuLinks = itemsEl.querySelectorAll(".submenu-item[data-profile-section]");
    submenuLinks.forEach((linkEl) => {
      const sectionKey = normalizeMenuKey(linkEl.dataset.profileSection);
      linkEl.style.display = hiddenMeuPerfilSectionKeys.has(sectionKey) ? "none" : "";
    });
  }

  if (typeof window.activateProfilePersonalSection === "function") {
    window.activateProfilePersonalSection(meuPerfilSelectedProfileSection);
  }
  if (itemsEl) {
    const selectedLinkEl = itemsEl.querySelector(
      `.submenu-item[data-profile-section="${String(meuPerfilSelectedProfileSection || "").replace(/"/g, '\\"')}"]`
    );
    if (selectedLinkEl && selectedLinkEl.style.display !== "none") {
      setActiveSubmenu("#perfil-pessoal-card", selectedLinkEl);
      return;
    }
    const firstVisibleLinkEl = Array.from(itemsEl.querySelectorAll(".submenu-item[data-profile-section]")).find(
      (linkEl) => linkEl.style.display !== "none"
    );
    if (firstVisibleLinkEl) {
      meuPerfilSelectedProfileSection = String(firstVisibleLinkEl.dataset.profileSection || "");
      setActiveSubmenu("#perfil-pessoal-card", firstVisibleLinkEl);
    }
  }
  if (!window.__APPVERBO_QUANTITY_EDIT_PAIRS_V4_ACTIVE) {
    renderMeuPerfilQuantityGroups();
  }
}

function setupMeuPerfilQuantityRules() {
  if (window.__APPVERBO_QUANTITY_EDIT_PAIRS_V4_ACTIVE) {
    return;
  }

  const personalCardEl = document.getElementById("perfil-pessoal-card");
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
  if (!formEl || !setting) {
    return;
  }

  const normalizedRules = normalizeProcessQuantityRules(setting.process_quantity_fields);
  if (!normalizedRules.length) {
    syncMeuPerfilQuantityHiddenInputs({});
    return;
  }

  const quantityFieldKeys = new Set(
    normalizedRules
      .map((rule) => normalizeMenuKey(rule.quantityFieldKey))
      .filter(Boolean)
  );

  formEl.querySelectorAll("[name]").forEach((controlEl) => {
    const rawName = String(controlEl.getAttribute("name") || "").trim();
    let fieldKey = "";
    if (rawName.startsWith("custom_field__")) {
      fieldKey = normalizeMenuKey(rawName.replace(/^custom_field__/, ""));
    } else if (rawName === "full_name") {
      fieldKey = "nome";
    } else if (rawName === "primary_phone") {
      fieldKey = "telefone";
    } else if (rawName === "login_email") {
      fieldKey = "email";
    } else if (rawName === "country") {
      fieldKey = "pais";
    } else if (rawName === "birth_date") {
      fieldKey = "data_nascimento";
    }
    if (!quantityFieldKeys.has(fieldKey)) {
      return;
    }
    ["input", "change"].forEach((eventName) => {
      controlEl.addEventListener(eventName, () => {
        renderMeuPerfilQuantityGroups();
      });
    });
  });

  if (formEl.dataset.boundMeuPerfilQuantitySubmit !== "1") {
    formEl.dataset.boundMeuPerfilQuantitySubmit = "1";
    formEl.addEventListener("submit", () => {
      syncMeuPerfilQuantityHiddenInputs(collectCurrentMeuPerfilQuantityValues());
    });
  }

  renderMeuPerfilQuantityGroups();
}

function setupConditionalProcessVisibility() {
  let dynamicProcessConditionalRenderTimerId = 0;

  function getDynamicProcessFieldKeyFromControl(controlEl) {
    if (!controlEl || typeof controlEl.getAttribute !== "function") {
      return "";
    }

    const rawName = String(controlEl.getAttribute("name") || "").trim();

    if (!rawName.startsWith("process_field__")) {
      return "";
    }

    return normalizeMenuKey(rawName.replace(/^process_field__/, ""));
  }

  function isDynamicProcessFieldDrivingRerender(menuKey, fieldKey) {
    const cleanMenuKey = normalizeMenuKey(menuKey);
    const cleanFieldKey = normalizeMenuKey(fieldKey);

    if (!cleanMenuKey || !cleanFieldKey) {
      return false;
    }

    const setting = getSidebarMenuSetting(cleanMenuKey);

    if (!setting) {
      return false;
    }

    const drivesSubsequentRules = normalizeProcessSubsequentRules(
      setting.process_subsequent_fields
    ).some((rule) => normalizeMenuKey(rule.triggerField) === cleanFieldKey);

    if (drivesSubsequentRules) {
      return true;
    }

    const drivesQuantityRules = normalizeProcessQuantityRules(setting.process_quantity_fields)
      .some((rule) => normalizeMenuKey(rule.quantityFieldKey) === cleanFieldKey);

    if (drivesQuantityRules) {
      return true;
    }

    const processListSourcesByKey = new Map();
    (Array.isArray(setting.process_lists) ? setting.process_lists : []).forEach((processList) => {
      const listKey = normalizeMenuKey(processList && processList.key);
      if (!listKey) {
        return;
      }
      processListSourcesByKey.set(
        listKey,
        normalizeMenuKey(processList && (processList.source_key || processList.sourceKey))
      );
    });

    const hasMenusBySessionList = (Array.isArray(setting.process_field_options) ? setting.process_field_options : [])
      .some((option) => {
        const listKey = normalizeMenuKey(option && (option.list_key || option.listKey));
        return processListSourcesByKey.get(listKey) === "sidebar_menus_by_section";
      });

    if (!hasMenusBySessionList) {
      return false;
    }

    return (Array.isArray(setting.process_field_options) ? setting.process_field_options : [])
      .some((option) => {
        const optionKey = normalizeMenuKey(option && option.key);
        const listKey = normalizeMenuKey(option && (option.list_key || option.listKey));
        return (
          optionKey === cleanFieldKey &&
          processListSourcesByKey.get(listKey) === "sidebar_sections"
        );
      });
  }

  function isMeuPerfilFieldDrivingRerender(fieldKey, setting) {
    const cleanFieldKey = normalizeMenuKey(fieldKey);

    if (!cleanFieldKey || !setting) {
      return false;
    }

    const drivesSubsequentRules = normalizeProcessSubsequentRules(
      setting.process_subsequent_fields
    ).some((rule) => normalizeMenuKey(rule.triggerField) === cleanFieldKey);

    if (drivesSubsequentRules) {
      return true;
    }

    return normalizeProcessQuantityRules(setting.process_quantity_fields)
      .some((rule) => normalizeMenuKey(rule.quantityFieldKey) === cleanFieldKey);
  }

  function scheduleDynamicProcessConditionalRender(cleanMenuKey) {
    if (!cleanMenuKey) {
      return;
    }

    if (dynamicProcessConditionalRenderTimerId) {
      window.clearTimeout(dynamicProcessConditionalRenderTimerId);
      dynamicProcessConditionalRenderTimerId = 0;
    }

    dynamicProcessConditionalRenderTimerId = window.setTimeout(() => {
      dynamicProcessConditionalRenderTimerId = 0;
      renderDynamicProcessCard(
        cleanMenuKey,
        selectedDynamicSectionByMenu[cleanMenuKey] || (dynamicProcessSectionKeyInputEl ? dynamicProcessSectionKeyInputEl.value : ""),
        { preserveInteractionState: true }
      );
    }, 0);
  }

  const personalCardEl = document.getElementById("perfil-pessoal-card");
  const personalFormEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  if (personalFormEl && personalFormEl.dataset.boundSubsequentVisibility !== "1") {
    personalFormEl.dataset.boundSubsequentVisibility = "1";
    ["input", "change"].forEach((eventName) => {
      personalFormEl.addEventListener(eventName, (event) => {
        const targetEl = event && event.target ? event.target : null;

        if (isMeuPerfilQuantityV4GeneratedTarget(targetEl)) {
          return;
        }

        const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
        const changedFieldKey = getMeuPerfilProcessFieldKeyFromControl(targetEl);

        if (!isMeuPerfilFieldDrivingRerender(changedFieldKey, setting)) {
          return;
        }

        applyMeuPerfilProcessSubsequentVisibility();
      });
    });
  }

  if (dynamicProcessEditFormEl && dynamicProcessEditFormEl.dataset.boundSubsequentVisibility !== "1") {
    dynamicProcessEditFormEl.dataset.boundSubsequentVisibility = "1";
    ["input", "change"].forEach((eventName) => {
      dynamicProcessEditFormEl.addEventListener(eventName, (event) => {
        const cleanMenuKey = normalizeMenuKey(dynamicProcessMenuKeyInputEl ? dynamicProcessMenuKeyInputEl.value : "");
        if (!cleanMenuKey) {
          return;
        }
        const targetEl = event && event.target ? event.target : null;
        const changedFieldKey = getDynamicProcessFieldKeyFromControl(targetEl);
        if (!isDynamicProcessFieldDrivingRerender(cleanMenuKey, changedFieldKey)) {
          return;
        }
        scheduleDynamicProcessConditionalRender(cleanMenuKey);
      });
    });
  }

  if (dynamicProcessEditFormEl && dynamicProcessEditFormEl.dataset.boundQuantitySync !== "1") {
    dynamicProcessEditFormEl.dataset.boundQuantitySync = "1";
    dynamicProcessEditFormEl.addEventListener("submit", () => {
      const cleanMenuKey = normalizeMenuKey(dynamicProcessMenuKeyInputEl ? dynamicProcessMenuKeyInputEl.value : "");
      if (!cleanMenuKey) {
        return;
      }
      syncDynamicProcessQuantityHiddenInputs(
        cleanMenuKey,
        collectCurrentDynamicProcessQuantityValues(cleanMenuKey)
      );
    });
  }
}

      window.setupProfileProcessTabs = setupProfileProcessTabs;
      window.collectCurrentMeuPerfilProcessValues = collectCurrentMeuPerfilProcessValues;
      window.getMeuPerfilProcessFieldKeyFromControl = getMeuPerfilProcessFieldKeyFromControl;
      window.applyMeuPerfilProcessSubsequentVisibility = applyMeuPerfilProcessSubsequentVisibility;
      window.setupMeuPerfilQuantityRules = setupMeuPerfilQuantityRules;
      window.setupConditionalProcessVisibility = setupConditionalProcessVisibility;
      window.__APPVERBO_PROFILE_PROCESS_RUNTIME_CORE_V1_READY = true;
    }
  };
})();
// APPVERBO_PROFILE_PROCESS_RUNTIME_CORE_V1_MODULE_END
