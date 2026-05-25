// APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_MODULE_START
(function registerMeuPerfilQuantityOriginDedupV1Module() {
  "use strict";

  window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1 = function setupMeuPerfilQuantityOriginDedupV1(options) {
    const deps = options && typeof options === "object" ? options : {};
// APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1) EVITAR DUPLICACAO DO CAMPO ORIGEM
//###################################################################################

(function setupMeuPerfilQuantityOriginDedupV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeQuantityOriginDedupTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function getMeuPerfilQuantityOriginSettingV1() {
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

  function getMeuPerfilQuantityOriginFormV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function resolveQuantityOriginControlNameV1(fieldKey) {
    const cleanFieldKey = normalizeMenuKey(fieldKey);

    if (!cleanFieldKey) {
      return "";
    }

    if (cleanFieldKey.startsWith("custom_")) {
      return "custom_field__" + cleanFieldKey;
    }

    const builtinNames = {
      nome: "full_name",
      telefone: "primary_phone",
      email: "login_email",
      pais: "country",
      data_nascimento: "birth_date",
      autorizacao_whatsapp: "whatsapp_notice_opt_in"
    };

    return builtinNames[cleanFieldKey] || cleanFieldKey;
  }

  function getQuantityOriginCurrentSectionV1() {
    const sectionInput = document.querySelector("[data-meu-perfil-section-input]");
    return normalizeMenuKey(sectionInput ? sectionInput.value : "");
  }

  function getQuantityOriginWrapperV1(control) {
    if (!control) {
      return null;
    }

    return control.closest(".field")
      || control.closest("[data-profile-field-key]")
      || control.parentElement;
  }

  function getControlsByNameV1(form, controlName) {
    if (!form || !controlName) {
      return [];
    }

    return Array.from(form.elements || []).filter((control) => {
      return safeQuantityOriginDedupTextV1(control.name) === controlName;
    });
  }

  function disableDuplicateWrapperV1(wrapper, fieldKey) {
    if (!wrapper) {
      return;
    }

    wrapper.dataset.profileQuantityOriginDuplicateV1 = "1";
    wrapper.dataset.profileFieldKey = normalizeMenuKey(fieldKey);
    wrapper.hidden = true;
    wrapper.style.display = "none";

    Array.from(wrapper.querySelectorAll("input, select, textarea, button")).forEach((control) => {
      control.disabled = true;
      control.dataset.profileQuantityOriginDuplicateDisabledV1 = "1";
    });
  }

  function enableKeptWrapperV1(wrapper, rule) {
    if (!wrapper || !rule) {
      return;
    }

    wrapper.dataset.profileQuantityOriginKeepV1 = "1";
    wrapper.dataset.profileFieldKey = normalizeMenuKey(rule.quantityFieldKey);

    if (rule.headerKey) {
      wrapper.dataset.profileSectionPane = rule.headerKey;
    }

    wrapper.hidden = false;

    Array.from(wrapper.querySelectorAll("input, select, textarea, button")).forEach((control) => {
      if (control.dataset.profileQuantityOriginDuplicateDisabledV1 === "1") {
        return;
      }

      control.disabled = false;
    });
  }

  function applyQuantityOriginVisibilityV1(wrapper, rule) {
    if (!wrapper || !rule) {
      return;
    }

    const currentSection = getQuantityOriginCurrentSectionV1();
    const targetSection = normalizeMenuKey(rule.headerKey || wrapper.dataset.profileSectionPane || "");

    if (!currentSection || !targetSection) {
      wrapper.style.display = "";
      return;
    }

    wrapper.style.display = currentSection === targetSection ? "" : "none";
  }

  //###################################################################################
  // (2) DEDUP POR REGRA
  //###################################################################################

  function dedupQuantityOriginRuleV1(form, rule) {
    const quantityFieldKey = normalizeMenuKey(rule && rule.quantityFieldKey);
    const controlName = resolveQuantityOriginControlNameV1(quantityFieldKey);

    if (!quantityFieldKey || !controlName) {
      return;
    }

    const controls = getControlsByNameV1(form, controlName);

    if (!controls.length) {
      return;
    }

    const wrappers = [];
    const seenWrappers = new Set();

    controls.forEach((control) => {
      const wrapper = getQuantityOriginWrapperV1(control);

      if (!wrapper || seenWrappers.has(wrapper)) {
        return;
      }

      seenWrappers.add(wrapper);
      wrappers.push(wrapper);
    });

    if (!wrappers.length) {
      return;
    }

    const targetSection = normalizeMenuKey(rule.headerKey);

    let keepWrapper = null;

    if (targetSection) {
      keepWrapper = wrappers.find((wrapper) => {
        return normalizeMenuKey(wrapper.dataset.profileSectionPane) === targetSection;
      }) || null;
    }

    if (!keepWrapper) {
      keepWrapper = wrappers[0];
    }

    enableKeptWrapperV1(keepWrapper, rule);

    wrappers.forEach((wrapper) => {
      if (wrapper === keepWrapper) {
        return;
      }

      disableDuplicateWrapperV1(wrapper, quantityFieldKey);
    });

    applyQuantityOriginVisibilityV1(keepWrapper, rule);
  }

  //###################################################################################
  // (3) DEDUP GLOBAL
  //###################################################################################

  function dedupMeuPerfilQuantityOriginsV1() {
    const form = getMeuPerfilQuantityOriginFormV1();
    const setting = getMeuPerfilQuantityOriginSettingV1();

    if (!form || !setting) {
      return;
    }

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    if (!rules.length) {
      return;
    }

    rules.forEach((rule) => {
      dedupQuantityOriginRuleV1(form, rule);
    });
  }

  function scheduleDedupMeuPerfilQuantityOriginsV1() {
    window.setTimeout(dedupMeuPerfilQuantityOriginsV1, 0);
    window.setTimeout(dedupMeuPerfilQuantityOriginsV1, 80);
    window.setTimeout(dedupMeuPerfilQuantityOriginsV1, 250);
  }

  function shouldRunMeuPerfilQuantityOriginDedupV1(event) {
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

  document.addEventListener("click", function (event) {
    if (!shouldRunMeuPerfilQuantityOriginDedupV1(event)) {
      return;
    }
    scheduleDedupMeuPerfilQuantityOriginsV1();
  }, true);
  document.addEventListener("input", function (event) {
    if (!shouldRunMeuPerfilQuantityOriginDedupV1(event)) {
      return;
    }
    scheduleDedupMeuPerfilQuantityOriginsV1();
  }, true);
  document.addEventListener("change", function (event) {
    if (!shouldRunMeuPerfilQuantityOriginDedupV1(event)) {
      return;
    }
    scheduleDedupMeuPerfilQuantityOriginsV1();
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleDedupMeuPerfilQuantityOriginsV1);
  } else {
    scheduleDedupMeuPerfilQuantityOriginsV1();
  }

  window.setTimeout(scheduleDedupMeuPerfilQuantityOriginsV1, 150);
  window.setTimeout(scheduleDedupMeuPerfilQuantityOriginsV1, 600);
})();

// APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_END
  };
})();
// APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_MODULE_END
