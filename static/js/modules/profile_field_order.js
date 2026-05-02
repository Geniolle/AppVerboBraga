//###################################################################################
// (1) ORDENACAO DOS CAMPOS DO MEU PERFIL
//###################################################################################

(function () {
  "use strict";

  const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
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
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getProfileForm() {
    return (
      document.querySelector('form[action="/users/profile/personal"]') ||
      document.querySelector("#perfil-pessoal-card form")
    );
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

  function getReadonlyFieldByKey(card, fieldKey) {
    const readonlyGrid = card.querySelector(".profile-readonly .personal-grid");
    if (!readonlyGrid) {
      return null;
    }

    const targetLabel = normalizeLookupText(getBuiltinFieldLabel(fieldKey));

    return Array.from(readonlyGrid.querySelectorAll(".personal-item")).find((item) => {
      const label = item.querySelector(".personal-label");
      return normalizeLookupText(label ? label.textContent : "") === targetLabel;
    }) || null;
  }

  function reorderContainerByFieldOrder(container, resolveElement, itemSelector) {
    if (!container || !profilePersonalVisibleFields.length) {
      return;
    }

    Array.from(container.querySelectorAll(itemSelector)).forEach((element) => {
      element.style.order = "";
    });

    profilePersonalVisibleFields.forEach((fieldKey, index) => {
      const element = resolveElement(fieldKey);
      if (element && element.parentNode === container) {
        element.style.order = String(index + 1);
      }
    });
  }

  //###################################################################################
  // (3) REORDENAR CAMPOS
  //###################################################################################

  function reorderProfileFields() {
    const form = getProfileForm();

    if (!form) {
      return;
    }

    const card = document.getElementById("perfil-pessoal-card");
    const formGrid =
      form.querySelector(".personal-grid") ||
      form.querySelector(".form-grid") ||
      form;

    reorderContainerByFieldOrder(
      formGrid,
      (fieldKey) => getFormFieldByKey(form, fieldKey),
      ".field"
    );

    const actionsRow = form.querySelector(".profile-edit-actions");
    if (actionsRow) {
      actionsRow.style.order = String(profilePersonalVisibleFields.length + 100);
    }

    if (card) {
      const readonlyGrid = card.querySelector(".profile-readonly .personal-grid");
      reorderContainerByFieldOrder(
        readonlyGrid,
        (fieldKey) => getReadonlyFieldByKey(card, fieldKey),
        ".personal-item"
      );
    }
  }

  //###################################################################################
  // (4) INICIALIZACAO
  //###################################################################################

  function init() {
    reorderProfileFields();

    window.setTimeout(reorderProfileFields, 100);
    window.setTimeout(reorderProfileFields, 400);
    window.setTimeout(reorderProfileFields, 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
