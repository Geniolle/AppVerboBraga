// APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_MODULE_START
(function registerKeepCurrentProcessAfterProfileSaveV1Module() {
  "use strict";

  window.APPVERBO_SETUP_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1 = function setupKeepCurrentProcessAfterProfileSaveV1(options) {
    const deps = options && typeof options === "object" ? options : {};
// APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START
//###################################################################################
// (KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1) MANTER PROCESSO/ABA APOS GRAVAR
//###################################################################################

(function setupKeepCurrentProcessAfterProfileSaveV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeKeepProcessTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeKeepProcessKeyV1(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeKeepProcessTextV1(value).trim().toLowerCase();
  }

  function normalizeKeepProcessLookupV1(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeKeepProcessTextV1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getProfilePersonalFormKeepProcessV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function ensureHiddenInputKeepProcessV1(form, name) {
    let input = form.querySelector("input[name='" + name + "']");

    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }

    return input;
  }

  function getSectionFromKnownInputKeepProcessV1() {
    const selectors = [
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    for (const selector of selectors) {
      const input = document.querySelector(selector);
      const value = normalizeKeepProcessKeyV1(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getSectionFromActiveTabKeepProcessV1() {
    const sections = Array.isArray(profilePersonalSections) ? profilePersonalSections : [];

    const activeSelectors = [
      "[data-profile-section-tab].active",
      "[data-profile-section-tab][aria-selected='true']",
      "[data-profile-section-button].active",
      "[data-profile-section-button][aria-selected='true']",
      ".profile-section-tab.active",
      ".profile-section-tab[aria-selected='true']",
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

      const datasetSection = normalizeKeepProcessKeyV1(datasetValue);

      if (datasetSection) {
        return datasetSection;
      }

      const activeLabel = normalizeKeepProcessLookupV1(activeElement.textContent);

      if (!activeLabel) {
        continue;
      }

      for (const section of sections) {
        const sectionLabel = normalizeKeepProcessLookupV1(section && section.label);

        if (sectionLabel && sectionLabel === activeLabel) {
          return normalizeKeepProcessKeyV1(section && section.key);
        }
      }
    }

    return "";
  }

  function getSectionFromVisiblePaneKeepProcessV1(form) {
    const panes = Array.from(
      form.querySelectorAll("[data-profile-section-pane]")
    );

    for (const pane of panes) {
      const style = window.getComputedStyle ? window.getComputedStyle(pane) : null;

      if (
        pane.hidden ||
        pane.style.display === "none" ||
        (style && style.display === "none")
      ) {
        continue;
      }

      const sectionKey = normalizeKeepProcessKeyV1(pane.dataset.profileSectionPane);

      if (sectionKey) {
        return sectionKey;
      }
    }

    return "";
  }

  function getCurrentProfileSectionKeepProcessV1(form) {
    return (
      getSectionFromKnownInputKeepProcessV1() ||
      getSectionFromActiveTabKeepProcessV1() ||
      getSectionFromVisiblePaneKeepProcessV1(form) ||
      (
        Array.isArray(profilePersonalSections) && profilePersonalSections.length
          ? normalizeKeepProcessKeyV1(profilePersonalSections[0].key)
          : ""
      )
    );
  }

  //###################################################################################
  // (2) SINCRONIZAR CONTEXTO ANTES DE GRAVAR
  //###################################################################################

  function syncProfileSaveContextKeepProcessV1(form) {
    if (!form) {
      return;
    }

    const action = safeKeepProcessTextV1(form.getAttribute("action") || form.action);

    if (!action.includes("/users/profile/personal")) {
      return;
    }

    const currentSection = getCurrentProfileSectionKeepProcessV1(form);

    ensureHiddenInputKeepProcessV1(form, "menu").value = MEU_PERFIL_MENU_KEY;
    ensureHiddenInputKeepProcessV1(form, "target").value = "#perfil-pessoal-card";

    if (currentSection) {
      ensureHiddenInputKeepProcessV1(form, "profile_section").value = currentSection;
    }

    ensureHiddenInputKeepProcessV1(form, "appverbo_after_save").value = "1";
  }

  function bindProfileSaveContextKeepProcessV1() {
    const form = getProfilePersonalFormKeepProcessV1();

    if (!form || form.dataset.keepCurrentProcessAfterProfileSaveV1 === "1") {
      return;
    }

    form.dataset.keepCurrentProcessAfterProfileSaveV1 = "1";

    form.addEventListener("submit", function () {
      syncProfileSaveContextKeepProcessV1(form);
    }, true);

    form.addEventListener("click", function (event) {
      const submitControl = event.target && event.target.closest
        ? event.target.closest("button[type='submit'], input[type='submit'], button:not([type])")
        : null;

      if (!submitControl) {
        return;
      }

      syncProfileSaveContextKeepProcessV1(form);
    }, true);
  }

  //###################################################################################
  // (3) COBRIR SUBMIT NATIVO/PROGRAMATICO
  //###################################################################################

  if (
    window.HTMLFormElement &&
    window.HTMLFormElement.prototype &&
    !window.HTMLFormElement.prototype.__appverboKeepProcessSubmitPatchedV1
  ) {
    const nativeSubmit = window.HTMLFormElement.prototype.submit;

    window.HTMLFormElement.prototype.submit = function patchedSubmitKeepProcessV1() {
      syncProfileSaveContextKeepProcessV1(this);
      return nativeSubmit.call(this);
    };

    window.HTMLFormElement.prototype.__appverboKeepProcessSubmitPatchedV1 = true;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindProfileSaveContextKeepProcessV1);
  } else {
    bindProfileSaveContextKeepProcessV1();
  }

  window.setTimeout(bindProfileSaveContextKeepProcessV1, 150);
  window.setTimeout(bindProfileSaveContextKeepProcessV1, 600);
})();

// APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_END
  };
})();
// APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_MODULE_END
