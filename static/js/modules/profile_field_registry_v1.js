//###################################################################################
// (1) REGISTRY CANONICO DOS CAMPOS DO MEU PERFIL
//###################################################################################

(function () {
  "use strict";

  const bootstrap = window.__APPGENESIS_BOOTSTRAP__ || {};

  const profilePersonalFieldLabels = (
    bootstrap.profilePersonalFieldLabels &&
    typeof bootstrap.profilePersonalFieldLabels === "object" &&
    !Array.isArray(bootstrap.profilePersonalFieldLabels)
  )
    ? bootstrap.profilePersonalFieldLabels
    : {};

  const builtinControlNames = {
    nome: "full_name",
    telefone: "primary_phone",
    email: "login_email",
    pais: "country",
    data_nascimento: "birth_date",
    autorizacao_whatsapp: "whatsapp_notice_opt_in"
  };

  const builtinFieldKeysByControlName = {
    full_name: "nome",
    primary_phone: "telefone",
    login_email: "email",
    email: "email",
    country: "pais",
    birth_date: "data_nascimento",
    whatsapp_notice_opt_in: "autorizacao_whatsapp"
  };

  const profileSectionSelectors = [
    "input[name='profile_section']",
    "[data-meu-perfil-section-input]",
    "[data-profile-section-input]"
  ];

  function toSafeString(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeLookupText(value) {
    return toSafeString(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function normalizeFieldKey(value) {
    const clean = toSafeString(value)
      .trim()
      .toLowerCase()
      .replace(/\s+/g, "_")
      .replace(/-+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");

    return clean;
  }

  function resolveControlName(fieldKey) {
    const cleanKey = normalizeFieldKey(fieldKey);

    if (!cleanKey) {
      return "";
    }

    if (cleanKey.startsWith("custom_")) {
      return "custom_field__" + cleanKey;
    }

    return builtinControlNames[cleanKey] || cleanKey;
  }

  function resolveFieldKeyFromControlName(controlName) {
    const cleanName = normalizeFieldKey(controlName);

    if (!cleanName) {
      return "";
    }

    if (cleanName.startsWith("custom_field__")) {
      return normalizeFieldKey(cleanName.replace(/^custom_field__/, ""));
    }

    return builtinFieldKeysByControlName[cleanName] || cleanName;
  }

  function getProfileForm(root) {
    const scope = root && typeof root.querySelector === "function" ? root : document;

    return (
      scope.querySelector('form[action="/users/profile/personal"]') ||
      scope.querySelector("#perfil-pessoal-card form") ||
      null
    );
  }

  function findProfileControl(form, fieldKey) {
    if (!form || typeof form.querySelector !== "function") {
      return null;
    }

    const cleanFieldKey = normalizeFieldKey(fieldKey);

    if (!cleanFieldKey) {
      return null;
    }

    const controlName = resolveControlName(cleanFieldKey);

    const selectorCandidates = [];
    if (controlName) {
      selectorCandidates.push(`[name="${controlName}"]`);
    }
    selectorCandidates.push(`[data-profile-field-key="${cleanFieldKey}"]`);

    if (cleanFieldKey.startsWith("custom_")) {
      selectorCandidates.push(`[name="custom_field__${cleanFieldKey}"]`);
    }

    for (const selector of selectorCandidates) {
      const node = form.querySelector(selector);

      if (!node) {
        continue;
      }

      if (node.matches && node.matches("input, select, textarea")) {
        return node;
      }

      const nestedControl = node.querySelector
        ? node.querySelector("input, select, textarea")
        : null;

      return nestedControl || node;
    }

    return null;
  }

  function readControlValue(control, fieldType) {
    if (!control) {
      return "";
    }

    const type = normalizeFieldKey(fieldType || control.type || "");

    if (type === "checkbox") {
      return control.checked ? "1" : "0";
    }

    if (control.tagName && control.tagName.toLowerCase() === "select") {
      return toSafeString(control.value).trim();
    }

    return toSafeString(control.value).trim();
  }

  function collectProfileValues(form) {
    if (!form || typeof form.querySelectorAll !== "function") {
      return {};
    }

    const valuesByField = {};

    form.querySelectorAll("[name]").forEach((control) => {
      const fieldKey = resolveFieldKeyFromControlName(control.getAttribute("name"));

      if (!fieldKey) {
        return;
      }

      valuesByField[fieldKey] = readControlValue(control, control.type);
    });

    return valuesByField;
  }

  function getCurrentProfileSection(root) {
    const scope = root && typeof root.querySelector === "function" ? root : document;

    for (const selector of profileSectionSelectors) {
      const input = scope.querySelector(selector);
      const value = normalizeFieldKey(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    const activeSelectors = [
      "#perfil-pessoal-card [data-profile-section-tab].active",
      "#perfil-pessoal-card [data-profile-section-tab][aria-selected='true']",
      "#perfil-pessoal-card [data-profile-section-button].active",
      "#perfil-pessoal-card [data-profile-section-button][aria-selected='true']",
      "#perfil-pessoal-card .profile-section-tab.active",
      "#perfil-pessoal-card .profile-section-tab[aria-selected='true']",
      "#perfil-pessoal-card .active"
    ];

    for (const selector of activeSelectors) {
      const activeElement = scope.querySelector(selector);

      if (!activeElement) {
        continue;
      }

      const dataSection = normalizeFieldKey(
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      if (dataSection) {
        return dataSection;
      }

      const activeLabel = normalizeLookupText(activeElement.textContent);
      const sections = Array.isArray(bootstrap.profilePersonalSections)
        ? bootstrap.profilePersonalSections
        : [];

      for (const section of sections) {
        if (normalizeLookupText(section && section.label) === activeLabel) {
          return normalizeFieldKey(section && section.key);
        }
      }
    }

    const firstSection = Array.isArray(bootstrap.profilePersonalSections) && bootstrap.profilePersonalSections.length
      ? normalizeFieldKey(bootstrap.profilePersonalSections[0].key)
      : "";

    return firstSection;
  }

  window.AppGenesisProfileFieldRegistryV1 = {
    normalizeFieldKey,
    resolveControlName,
    resolveFieldKeyFromControlName,
    findProfileControl,
    readControlValue,
    collectProfileValues,
    getProfileForm,
    getCurrentProfileSection,
    normalizeLookupText
  };
})();
