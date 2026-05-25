// APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_MODULE_START
(function registerMeuPerfilEditSectionFilterV1Module() {
  "use strict";

  window.APPVERBO_SETUP_MEU_PERFIL_EDIT_SECTION_FILTER_V1 = function setupMeuPerfilEditSectionFilterV1(options) {
    const deps = options && typeof options === "object" ? options : {};
// APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_START
//###################################################################################
// (MEU_PERFIL_EDIT_SECTION_FILTER_V1) FILTRAR CAMPOS DO EDITAR POR ABA/CABECALHO
//###################################################################################

(function setupMeuPerfilEditSectionFilterV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeEditSectionTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeEditSectionKeyV1(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeEditSectionTextV1(value).trim().toLowerCase();
  }

  function normalizeEditSectionLookupV1(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeEditSectionTextV1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getMeuPerfilEditFormV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function sectionKeyFromLabelV1(label) {
    const cleanLabel = normalizeEditSectionLookupV1(label);

    if (!cleanLabel) {
      return "";
    }

    const sections = Array.isArray(profilePersonalSections) ? profilePersonalSections : [];

    for (const section of sections) {
      const sectionLabel = normalizeEditSectionLookupV1(section && section.label);

      if (sectionLabel && sectionLabel === cleanLabel) {
        return normalizeEditSectionKeyV1(section && section.key);
      }
    }

    return "";
  }

  function getCurrentProfileSectionFromInputV1() {
    const selectors = [
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    for (const selector of selectors) {
      const input = document.querySelector(selector);
      const value = normalizeEditSectionKeyV1(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getCurrentProfileSectionFromActiveTabV1() {
    const activeSelectors = [
      "[data-profile-section-tab].active",
      "[data-profile-section-tab][aria-selected='true']",
      "[data-profile-section-button].active",
      "[data-profile-section-button][aria-selected='true']",
      ".profile-section-tab.active",
      ".profile-section-tab[aria-selected='true']",
      "#perfil-pessoal-card .tab.active",
      "#perfil-pessoal-card .active"
    ];

    for (const selector of activeSelectors) {
      const activeElement = document.querySelector(selector);

      if (!activeElement) {
        continue;
      }

      const datasetValue = (
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      const datasetSection = normalizeEditSectionKeyV1(datasetValue);

      if (datasetSection) {
        return datasetSection;
      }

      const textSection = sectionKeyFromLabelV1(activeElement.textContent);

      if (textSection) {
        return textSection;
      }
    }

    return "";
  }

  function getCurrentProfileSectionV1() {
    return (
      getCurrentProfileSectionFromInputV1() ||
      getCurrentProfileSectionFromActiveTabV1() ||
      (
        Array.isArray(profilePersonalSections) &&
        profilePersonalSections.length
          ? normalizeEditSectionKeyV1(profilePersonalSections[0].key)
          : ""
      )
    );
  }

  function getElementSectionPaneV1(element) {
    if (!element) {
      return "";
    }

    return normalizeEditSectionKeyV1(
      element.dataset.profileSectionPane ||
      element.dataset.profileSection ||
      element.dataset.sectionKey ||
      ""
    );
  }

  function getVisibilityWrapperV1(element) {
    if (!element) {
      return null;
    }

    if (
      element.classList &&
      (
        element.classList.contains("field") ||
        element.classList.contains("profile-quantity-rule-v1") ||
        element.classList.contains("profile-quantity-readonly-v1")
      )
    ) {
      return element;
    }

    return (
      element.closest(".field") ||
      element.closest("[data-profile-quantity-rule-key]") ||
      element.closest("[data-profile-quantity-readonly-rule-key]") ||
      element
    );
  }

  function isDuplicateOriginWrapperV1(wrapper) {
    if (!wrapper || !wrapper.dataset) {
      return false;
    }

    return wrapper.dataset.profileQuantityOriginDuplicateV1 === "1";
  }

  function syncWrapperRequiredStateV1(wrapper, shouldEnableRequired) {
    if (!wrapper) {
      return;
    }

    wrapper.querySelectorAll("input, select, textarea").forEach((control) => {
      if (!control || String(control.type || "").toLowerCase() === "hidden") {
        return;
      }

      if (shouldEnableRequired) {
        if (control.dataset.profileSectionRequiredTemporarilyRemovedV1 === "1") {
          control.required = true;
          delete control.dataset.profileSectionRequiredTemporarilyRemovedV1;
        }
        return;
      }

      if (control.required) {
        control.required = false;
        control.dataset.profileSectionRequiredTemporarilyRemovedV1 = "1";
      }
    });
  }

  function setWrapperVisibleBySectionV1(wrapper, currentSection, expectedSection) {
    if (!wrapper || !currentSection || !expectedSection) {
      return;
    }

    if (isDuplicateOriginWrapperV1(wrapper)) {
      wrapper.hidden = true;
      wrapper.style.display = "none";
      syncWrapperRequiredStateV1(wrapper, false);
      return;
    }

    if (currentSection === expectedSection) {
      wrapper.hidden = false;
      wrapper.style.display = "";
      syncWrapperRequiredStateV1(wrapper, true);
      return;
    }

    wrapper.hidden = true;
    wrapper.style.display = "none";
    syncWrapperRequiredStateV1(wrapper, false);
  }

  function applyQuantityHostsSectionV1(form) {
    if (!form || typeof getSidebarMenuSetting !== "function" || typeof normalizeProcessQuantityRules !== "function") {
      return;
    }

    const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);

    if (!setting) {
      return;
    }

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    rules.forEach((rule) => {
      const ruleKey = normalizeEditSectionKeyV1(rule.key);
      const headerKey = normalizeEditSectionKeyV1(rule.headerKey);

      if (!ruleKey || !headerKey) {
        return;
      }

      const hosts = form.querySelectorAll(
        "[data-profile-quantity-rule-key='" + ruleKey + "'], " +
        "[data-profile-quantity-readonly-rule-key='" + ruleKey + "']"
      );

      hosts.forEach((host) => {
        host.dataset.profileSectionPane = headerKey;
      });
    });
  }

  //###################################################################################
  // (2) APLICAR FILTRO NO FORMULARIO EDITAR
  //###################################################################################

  function applyMeuPerfilEditSectionFilterV1() {
    const form = getMeuPerfilEditFormV1();

    if (!form) {
      return;
    }

    const currentSection = getCurrentProfileSectionV1();

    if (!currentSection) {
      return;
    }

    applyQuantityHostsSectionV1(form);

    const wrappers = new Set();

    Array.from(
      form.querySelectorAll("[data-profile-section-pane], [data-profile-section], [data-section-key]")
    ).forEach((element) => {
      const wrapper = getVisibilityWrapperV1(element);

      if (!wrapper || !form.contains(wrapper)) {
        return;
      }

      wrappers.add(wrapper);
    });

    Array.from(
      form.querySelectorAll("[data-profile-quantity-rule-key]")
    ).forEach((element) => {
      const wrapper = getVisibilityWrapperV1(element);

      if (!wrapper || !form.contains(wrapper)) {
        return;
      }

      wrappers.add(wrapper);
    });

    wrappers.forEach((wrapper) => {
      const wrapperSection = getElementSectionPaneV1(wrapper);

      if (!wrapperSection) {
        return;
      }

      setWrapperVisibleBySectionV1(wrapper, currentSection, wrapperSection);
    });
  }

  function scheduleMeuPerfilEditSectionFilterV1() {
    window.setTimeout(applyMeuPerfilEditSectionFilterV1, 0);
    window.setTimeout(applyMeuPerfilEditSectionFilterV1, 80);
    window.setTimeout(applyMeuPerfilEditSectionFilterV1, 250);
  }

  //###################################################################################
  // (3) EVENTOS
  //###################################################################################

  function shouldRunMeuPerfilEditSectionFilterV1(event) {
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
    if (!shouldRunMeuPerfilEditSectionFilterV1(event)) {
      return;
    }
    scheduleMeuPerfilEditSectionFilterV1();
  }, true);
  document.addEventListener("input", function (event) {
    if (!shouldRunMeuPerfilEditSectionFilterV1(event)) {
      return;
    }
    scheduleMeuPerfilEditSectionFilterV1();
  }, true);
  document.addEventListener("change", function (event) {
    if (!shouldRunMeuPerfilEditSectionFilterV1(event)) {
      return;
    }
    scheduleMeuPerfilEditSectionFilterV1();
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleMeuPerfilEditSectionFilterV1);
  } else {
    scheduleMeuPerfilEditSectionFilterV1();
  }

  window.setTimeout(scheduleMeuPerfilEditSectionFilterV1, 150);
  window.setTimeout(scheduleMeuPerfilEditSectionFilterV1, 600);
  window.setTimeout(scheduleMeuPerfilEditSectionFilterV1, 1200);
})();

// APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_END
  };
})();
// APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_MODULE_END
