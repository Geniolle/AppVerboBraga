// APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_MODULE_START
(function registerInitialProfileSectionFromUrlV1Module() {
  "use strict";

  window.APPVERBO_SETUP_INITIAL_PROFILE_SECTION_FROM_URL_V1 = function setupInitialProfileSectionFromUrlV1(options) {
    const deps = options && typeof options === "object" ? options : {};

    const normalizeMenuKey = typeof deps.normalizeMenuKey === "function"
      ? deps.normalizeMenuKey
      : function normalizeMenuKeyFallbackInitialProfileV1(value) {
        return String(value === null || value === undefined ? "" : value).trim().toLowerCase();
      };
    const normalizeLookupText = typeof deps.normalizeLookupText === "function"
      ? deps.normalizeLookupText
      : function normalizeLookupTextFallbackInitialProfileV1(value) {
        return String(value === null || value === undefined ? "" : value)
          .trim()
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "");
      };
    const profilePersonalSections = Array.isArray(deps.profilePersonalSections)
      ? deps.profilePersonalSections
      : [];
// APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_START
//###################################################################################
// (INITIAL_PROFILE_SECTION_FROM_URL_V1) ATIVAR ABA DO MEU PERFIL APOS POS-SAVE
//###################################################################################

(function setupInitialProfileSectionFromUrlV1() {
  "use strict";

  function safeInitialProfileSectionTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeInitialProfileSectionKeyV1(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeInitialProfileSectionTextV1(value).trim().toLowerCase();
  }

  function normalizeInitialProfileSectionLookupV1(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeInitialProfileSectionTextV1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function readProfileSectionFromUrlV1() {
    try {
      const params = new URLSearchParams(window.location.search);
      return normalizeInitialProfileSectionKeyV1(params.get("profile_section"));
    } catch (error) {
      return "";
    }
  }

  function setProfileSectionInputsV1(sectionKey) {
    if (!sectionKey) {
      return;
    }

    const selectors = [
      "#perfil-pessoal-card input[name='profile_section']",
      "#perfil-pessoal-card [data-meu-perfil-section-input]",
      "#perfil-pessoal-card [data-profile-section-input]",
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    let changed = false;

    selectors.forEach((selector) => {
      document.querySelectorAll(selector).forEach((input) => {
        if (!input) {
          return;
        }

        input.value = sectionKey;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
        changed = true;
      });
    });

    const form = document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');

    if (form && !form.querySelector("input[name='profile_section']")) {
      const hidden = document.createElement("input");
      hidden.type = "hidden";
      hidden.name = "profile_section";
      hidden.value = sectionKey;
      form.appendChild(hidden);
      changed = true;
    }

    return changed;
  }

  function findProfileSectionTabByKeyOrLabelV1(sectionKey) {
    if (!sectionKey) {
      return null;
    }

    const sections = (typeof profilePersonalSections !== "undefined" && Array.isArray(profilePersonalSections))
      ? profilePersonalSections
      : [];

    const sectionMeta = sections.find((section) => {
      return normalizeInitialProfileSectionKeyV1(section && section.key) === sectionKey;
    }) || null;

    const sectionLabel = normalizeInitialProfileSectionLookupV1(sectionMeta && sectionMeta.label);

    const candidates = Array.from(
      document.querySelectorAll(
        "#perfil-pessoal-card [data-profile-section-tab], " +
        "#perfil-pessoal-card [data-profile-section-button], " +
        "#perfil-pessoal-card .profile-section-tab, " +
        "#perfil-pessoal-card button, " +
        "#perfil-pessoal-card a"
      )
    );

    return candidates.find((candidate) => {
      const dataKey = normalizeInitialProfileSectionKeyV1(
        candidate.dataset.profileSection ||
        candidate.dataset.profileSectionKey ||
        candidate.dataset.profileSectionTab ||
        candidate.dataset.sectionKey ||
        ""
      );

      if (dataKey && dataKey === sectionKey) {
        return true;
      }

      const textKey = normalizeInitialProfileSectionLookupV1(candidate.textContent);

      return Boolean(sectionLabel && textKey && textKey === sectionLabel);
    }) || null;
  }

  function activateProfileSectionFromUrlV1() {
    const sectionKey = readProfileSectionFromUrlV1();

    if (!sectionKey) {
      return;
    }

    setProfileSectionInputsV1(sectionKey);

    const tab = findProfileSectionTabByKeyOrLabelV1(sectionKey);

    if (tab && typeof tab.click === "function") {
      tab.click();
    }

    setProfileSectionInputsV1(sectionKey);

    document.dispatchEvent(
      new CustomEvent("appverbo:profile-section-restored", {
        detail: {
          sectionKey
        }
      })
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", activateProfileSectionFromUrlV1);
  } else {
    activateProfileSectionFromUrlV1();
  }

  window.setTimeout(activateProfileSectionFromUrlV1, 100);
  window.setTimeout(activateProfileSectionFromUrlV1, 350);
  window.setTimeout(activateProfileSectionFromUrlV1, 900);
})();

// APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_END
  };
})();
// APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_MODULE_END
