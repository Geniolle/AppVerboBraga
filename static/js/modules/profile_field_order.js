//###################################################################################
// (1) ORDENACAO DOS CAMPOS DO MEU PERFIL
//###################################################################################

(function () {
  "use strict";

  const bootstrap = window.__APPGENESIS_BOOTSTRAP__ || {};
  const profileFieldRegistryV1 =
    window.AppGenesisProfileFieldRegistryV1 &&
    typeof window.AppGenesisProfileFieldRegistryV1 === "object"
      ? window.AppGenesisProfileFieldRegistryV1
      : null;
  const meuPerfilRuntimeV1 =
    window.AppGenesisMeuPerfilV1 &&
    typeof window.AppGenesisMeuPerfilV1 === "object"
      ? window.AppGenesisMeuPerfilV1
      : null;
  const MEU_PERFIL_PERSONAL_CARD_TARGET = meuPerfilRuntimeV1 &&
    typeof meuPerfilRuntimeV1.resolvePersonalCardTarget === "function"
      ? meuPerfilRuntimeV1.resolvePersonalCardTarget()
      : "#perfil-pessoal-card";
  const profilePersonalVisibleFields = Array.isArray(bootstrap.profilePersonalVisibleFields)
    ? bootstrap.profilePersonalVisibleFields
      .map((fieldKey) => String(fieldKey || "").trim().toLowerCase())
      .filter(Boolean)
    : [];
  const profilePersonalFieldLabels = (
    bootstrap.profilePersonalFieldLabels &&
    typeof bootstrap.profilePersonalFieldLabels === "object" &&
    !Array.isArray(bootstrap.profilePersonalFieldLabels)
  )
    ? bootstrap.profilePersonalFieldLabels
    : {};

  //###################################################################################
  // (2) FUNCOES AUXILIARES
  //###################################################################################

  function normalizeLookupText(value) {
    if (profileFieldRegistryV1 && typeof profileFieldRegistryV1.normalizeLookupText === "function") {
      return profileFieldRegistryV1.normalizeLookupText(value);
    }

    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getProfileForm() {
    if (profileFieldRegistryV1 && typeof profileFieldRegistryV1.getProfileForm === "function") {
      return profileFieldRegistryV1.getProfileForm(document);
    }

    return (
      document.querySelector('form[action="/users/profile/personal"]') ||
      document.querySelector(`${MEU_PERFIL_PERSONAL_CARD_TARGET} form`)
    );
  }

  function getProfilePersonalCard() {
    return document.querySelector(MEU_PERFIL_PERSONAL_CARD_TARGET);
  }

  function getBuiltinFieldLabel(fieldKey) {
    const labelMap = {
      nome: "Nome",
      email: "Email",
      telefone: "Telefone",
      pais: "País",
      data_nascimento: "Data de nascimento",
      whatsapp: "WhatsApp",
      autorizacao_whatsapp: "Autorização para avisos por WhatsApp",
      conta: "Conta",
      estado_membro: "Estado de membro",
      colaborador: "Colaborador",
      entidades: "Entidades",
      ultima_verificacao_whatsapp: "Última verificação WhatsApp",
      detalhe_verificacao: "Detalhe da verificação"
    };

    return String(profilePersonalFieldLabels[fieldKey] || labelMap[fieldKey] || fieldKey || "").trim();
  }

  function getFormFieldByKey(form, fieldKey) {
    if (profileFieldRegistryV1 && typeof profileFieldRegistryV1.findProfileControl === "function") {
      const control = profileFieldRegistryV1.findProfileControl(form, fieldKey);

      if (control) {
        return control.closest ? (control.closest(".field") || control) : control;
      }
    }

    const keyedField = form.querySelector(`[data-profile-field-key="${fieldKey}"]`);
    if (keyedField) {
      return keyedField.closest(".field") || keyedField;
    }

    const selectorMap = {
      nome: ['#edit_full_name', '[name="full_name"]'],
      telefone: ['#edit_primary_phone', '[name="primary_phone"]'],
      email: ['#edit_login_email', '[name="login_email"]', '[name="email"]'],
      pais: ['#edit_country', '[name="country"]'],
      data_nascimento: ['#edit_birth_date', '[name="birth_date"]'],
      autorizacao_whatsapp: ['[name="whatsapp_notice_opt_in"]']
    };

    const selectors = selectorMap[fieldKey] || [];
    for (const selector of selectors) {
      const input = form.querySelector(selector);
      if (!input) {
        continue;
      }
      const field = input.closest(".field");
      if (field) {
        return field;
      }
    }

    if (fieldKey.startsWith("custom_")) {
      const customInput = form.querySelector(`[name="custom_field__${fieldKey}"]`);
      if (customInput) {
        return customInput.closest(".field");
      }
    }

    return null;
  }

  function collectGridFieldKeys(container) {
    if (!container || typeof container.querySelectorAll !== "function") {
      return [];
    }

    const orderedKeys = [];
    Array.from(container.querySelectorAll("[data-profile-field-key]")).forEach((element) => {
      const fieldKey = normalizeLookupText(element.getAttribute("data-profile-field-key") || "");
      if (!fieldKey || orderedKeys.includes(fieldKey)) {
        return;
      }
      orderedKeys.push(fieldKey);
    });

    return orderedKeys;
  }

  function buildCanonicalProfileFieldOrder() {
    const personalCardEl = getProfilePersonalCard();
    const readonlyGridEl = personalCardEl
      ? personalCardEl.querySelector(".profile-readonly .personal-grid")
      : null;
    const readonlyKeys = collectGridFieldKeys(readonlyGridEl);

    if (readonlyKeys.length) {
      return readonlyKeys;
    }

    return profilePersonalVisibleFields.slice();
  }

  function reorderContainerByFieldOrder(container, resolveElement, itemSelector, orderedFieldKeys) {
    const fieldKeys = Array.isArray(orderedFieldKeys) && orderedFieldKeys.length
      ? orderedFieldKeys
      : profilePersonalVisibleFields;

    if (!container || !fieldKeys.length) {
      return;
    }

    Array.from(container.querySelectorAll(itemSelector)).forEach((element) => {
      element.style.order = "";
    });

    fieldKeys.forEach((fieldKey, index) => {
      const element = resolveElement(fieldKey);
      if (element && element.parentNode === container) {
        element.style.order = String((index + 1) * 10);
      }
    });

    const generatedBlocks = Array.from(
      container.querySelectorAll('[data-meu-perfil-quantity-generated="1"][data-meu-perfil-quantity-source-key]')
    );
    const generatedCountBySource = new Map();

    generatedBlocks.forEach((blockEl) => {
      const sourceKey = String(blockEl.getAttribute("data-meu-perfil-quantity-source-key") || "")
        .trim()
        .toLowerCase();
      if (!sourceKey) {
        return;
      }
      const sourceIndex = fieldKeys.indexOf(sourceKey);
      const baseOrder = sourceIndex >= 0 ? ((sourceIndex + 1) * 10) : ((fieldKeys.length + 1) * 10);
      const sourceCount = generatedCountBySource.get(sourceKey) || 0;
      generatedCountBySource.set(sourceKey, sourceCount + 1);
      blockEl.style.order = String(baseOrder + sourceCount + 1);
    });
  }

  //###################################################################################
  // (3) REORDENAR CAMPOS
  //###################################################################################

  function reorderProfileFields() {
    const personalCardEl = getProfilePersonalCard();
    const form = getProfileForm();

    if (!personalCardEl || !form) {
      return;
    }

    const readonlyGrid = personalCardEl.querySelector(".profile-readonly .personal-grid");
    const formGrid =
      form.querySelector(".personal-grid") ||
      form.querySelector(".form-grid") ||
      form;
    const orderedFieldKeys = buildCanonicalProfileFieldOrder();

    reorderContainerByFieldOrder(
      readonlyGrid,
      (fieldKey) => personalCardEl.querySelector(`[data-profile-field-key="${fieldKey}"]`),
      ".personal-item",
      orderedFieldKeys
    );

    reorderContainerByFieldOrder(
      formGrid,
      (fieldKey) => getFormFieldByKey(form, fieldKey),
      ".field",
      orderedFieldKeys
    );

    const actionsRow = form.querySelector(".profile-edit-actions");
    if (actionsRow) {
      actionsRow.style.order = String((orderedFieldKeys.length + 1) * 10);
    }
  }

  //###################################################################################
  // (4) INICIALIZACAO
  //###################################################################################

  function init() {
    reorderProfileFields();
    window.addEventListener("appgenesis:meu-perfil:layout-updated", reorderProfileFields);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.reorderMeuPerfilProfileFields = reorderProfileFields;
})();
