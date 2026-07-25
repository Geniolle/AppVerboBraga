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
  const profilePersonalFieldSectionMap = (
    bootstrap.profilePersonalFieldSectionMap &&
    typeof bootstrap.profilePersonalFieldSectionMap === "object" &&
    !Array.isArray(bootstrap.profilePersonalFieldSectionMap)
  )
    ? bootstrap.profilePersonalFieldSectionMap
    : {};
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
    const sections = Array.isArray(bootstrap.profilePersonalSections)
      ? bootstrap.profilePersonalSections
      : [];
    const sectionOrder = sections
      .map((section) => normalizeLookupText(section && section.key))
      .filter(Boolean);
    const visibleFields = profilePersonalVisibleFields.slice();
    const sectionMap = profilePersonalFieldSectionMap;
    const orderedKeys = [];
    const seenKeys = new Set();
    const builtinFieldOrder = [
      "nome",
      "email",
      "telefone",
      "pais",
      "data_nascimento",
      "whatsapp",
      "autorizacao_whatsapp",
      "conta",
      "estado_membro",
      "colaborador",
      "entidades",
      "ultima_verificacao_whatsapp",
      "detalhe_verificacao"
    ];
    const quantitySourceKeys = new Set();

    function appendKey(fieldKey) {
      const cleanKey = normalizeLookupText(fieldKey);
      if (!cleanKey || seenKeys.has(cleanKey)) {
        return;
      }
      orderedKeys.push(cleanKey);
      seenKeys.add(cleanKey);
    }

    if (sectionMap && typeof sectionMap === "object") {
      const personalCardEl = getProfilePersonalCard();
      const quantitySourceNodes = personalCardEl
        ? personalCardEl.querySelectorAll(
          "[data-meu-perfil-quantity-generated='1'][data-meu-perfil-quantity-source-key]"
        )
        : [];
      Array.from(quantitySourceNodes).forEach((node) => {
        const sourceKey = normalizeLookupText(node.dataset.meuPerfilQuantitySourceKey || "");
        if (sourceKey) {
          quantitySourceKeys.add(sourceKey);
        }
      });
    }

    builtinFieldOrder.forEach((fieldKey) => {
      if (visibleFields.includes(fieldKey)) {
        appendKey(fieldKey);
      }
    });

    if (sectionOrder.length) {
      sectionOrder.forEach((sectionKey) => {
        const sectionFields = visibleFields.filter((fieldKey) => {
          return (
            String(fieldKey || "").trim().toLowerCase().startsWith("custom_") &&
            normalizeLookupText(sectionMap[fieldKey] || "") === sectionKey
          );
        });

        sectionFields
          .filter((fieldKey) => quantitySourceKeys.has(fieldKey))
          .forEach(appendKey);

        sectionFields
          .filter((fieldKey) => !quantitySourceKeys.has(fieldKey))
          .forEach(appendKey);
      });
    }

    visibleFields.forEach((fieldKey) => {
      if (String(fieldKey || "").trim().toLowerCase().startsWith("custom_")) {
        appendKey(fieldKey);
      }
    });

    return orderedKeys.length ? orderedKeys : visibleFields;
  }

  function reorderContainerByFieldOrder(container, resolveElement, itemSelector, orderedFieldKeys) {
    const fieldKeys = Array.isArray(orderedFieldKeys) && orderedFieldKeys.length
      ? orderedFieldKeys
      : profilePersonalVisibleFields;

    if (!container || !fieldKeys.length) {
      return;
    }

    const directChildren = Array.from(container.children || []);
    const directChildSet = new Set(directChildren);
    const generatedBlocks = directChildren.filter((element) => {
      return Boolean(
        element &&
        element.dataset &&
        element.dataset.meuPerfilQuantityGenerated === "1" &&
        element.dataset.meuPerfilQuantitySourceKey
      );
    });
    const generatedBlocksBySource = new Map();

    generatedBlocks.forEach((blockEl) => {
      const sourceKey = normalizeLookupText(blockEl.dataset.meuPerfilQuantitySourceKey || "");
      if (!sourceKey) {
        return;
      }
      if (!generatedBlocksBySource.has(sourceKey)) {
        generatedBlocksBySource.set(sourceKey, []);
      }
      generatedBlocksBySource.get(sourceKey).push(blockEl);
    });

    const orderedNodes = [];
    const appendedNodes = new Set();

    const appendNode_v1 = (node) => {
      if (!node || appendedNodes.has(node)) {
        return;
      }
      orderedNodes.push(node);
      appendedNodes.add(node);
    };

    fieldKeys.forEach((fieldKey) => {
      const element = resolveElement(fieldKey);
      if (element && element.parentNode === container && directChildSet.has(element)) {
        appendNode_v1(element);
      }

      const sourceKey = normalizeLookupText(fieldKey);
      const relatedBlocks = generatedBlocksBySource.get(sourceKey) || [];
      relatedBlocks.forEach((blockEl) => {
        if (blockEl.parentNode === container && directChildSet.has(blockEl)) {
          appendNode_v1(blockEl);
        }
      });
    });

    directChildren.forEach((child) => {
      if (!appendedNodes.has(child)) {
        appendNode_v1(child);
      }
    });

    if (orderedNodes.length) {
      const fragment = document.createDocumentFragment();
      orderedNodes.forEach((node) => {
        fragment.appendChild(node);
      });
      container.appendChild(fragment);
    }
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
