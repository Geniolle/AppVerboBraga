//###################################################################################
// (1) ORDENACAO DOS CAMPOS DO MEU PERFIL
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) FUNCOES AUXILIARES
  //###################################################################################

  function getProfileForm() {
    return (
      document.querySelector('form[action="/users/profile/personal"]') ||
      document.querySelector("#perfil-pessoal-card form")
    );
  }

  function getFieldByInput(form, selectors) {
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

    return null;
  }

  function addClassIfExists(element, className) {
    if (element) {
      element.classList.add(className);
    }
  }

  //###################################################################################
  // (3) REORDENAR CAMPOS
  //###################################################################################

  function reorderProfileFields() {
    const form = getProfileForm();

    if (!form) {
      return;
    }

    const grid =
      form.querySelector(".personal-grid") ||
      form.querySelector(".form-grid") ||
      form;

    const nameField = getFieldByInput(form, [
      "#edit_full_name",
      '[name="full_name"]'
    ]);

    const phoneField = getFieldByInput(form, [
      "#edit_primary_phone",
      '[name="primary_phone"]'
    ]);

    const emailField = getFieldByInput(form, [
      "#edit_login_email",
      '[name="login_email"]',
      '[name="email"]'
    ]);

    const countryField = getFieldByInput(form, [
      "#edit_country",
      '[name="country"]'
    ]);

    addClassIfExists(nameField, "profile-field-name");
    addClassIfExists(phoneField, "profile-field-phone");
    addClassIfExists(emailField, "profile-field-email");
    addClassIfExists(countryField, "profile-field-country");

    if (nameField && nameField.parentNode === grid) {
      grid.insertBefore(nameField, grid.firstElementChild);
    }

    if (phoneField && nameField && phoneField.parentNode === grid) {
      nameField.insertAdjacentElement("afterend", phoneField);
    }

    if (emailField && phoneField && emailField.parentNode === grid) {
      phoneField.insertAdjacentElement("afterend", emailField);
    }

    if (countryField && emailField && countryField.parentNode === grid) {
      emailField.insertAdjacentElement("afterend", countryField);
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
