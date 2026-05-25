// APPVERBO_PROFILE_PROCESS_RUNTIME_CORE_V1_MODULE_START
(function registerProfileProcessRuntimeCoreV1Module() {
  "use strict";

  window.APPVERBO_SETUP_PROFILE_PROCESS_RUNTIME_CORE_V1 = function setupProfileProcessRuntimeCoreV1(options) {
    const deps = options && typeof options === "object" ? options : {};

    if (!window.__APPVERBO_PROFILE_PROCESS_RUNTIME_CORE_V1_READY) {
function setupProfileProcessTabs() {
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  if (!personalCardEl) {
    return;
  }
  const sectionPanes = personalCardEl.querySelectorAll("[data-profile-section-pane]");
  if (!sectionPanes.length) {
    return;
  }

  function activateSection(sectionKey) {
    const normalizedSection = String(sectionKey || "").trim().toLowerCase() || "geral";
    const availableSections = new Set(
      Array.from(sectionPanes)
        .map((paneEl) =>
          String(paneEl.getAttribute("data-profile-section-pane") || "geral").trim().toLowerCase()
        )
        .filter((section) => !hiddenMeuPerfilSectionKeys.has(section))
    );
    const effectiveSection = availableSections.has(normalizedSection)
      ? normalizedSection
      : (Array.from(availableSections)[0] || "geral");

    sectionPanes.forEach((paneEl) => {
      const paneSection = String(
        paneEl.getAttribute("data-profile-section-pane") || "geral"
      ).trim().toLowerCase();
      paneEl.style.display = !hiddenMeuPerfilSectionKeys.has(paneSection) && paneSection === effectiveSection ? "" : "none";
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

    return normalizeProcessQuantityRules(setting.process_quantity_fields)
      .some((rule) => normalizeMenuKey(rule.quantityFieldKey) === cleanFieldKey);
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
