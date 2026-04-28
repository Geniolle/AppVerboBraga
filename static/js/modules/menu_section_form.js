//###################################################################################
// (1) CAMPO SESSAO DO MENU NA CRIACAO DE PASTA
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) FUNCOES AUXILIARES
  //###################################################################################

  function normalizeText(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function findFieldByLabel(form, text) {
    const expected = normalizeText(text);
    const fields = Array.from(form.querySelectorAll(".field"));

    return fields.find(function (field) {
      return normalizeText(field.textContent).includes(expected);
    });
  }

  //###################################################################################
  // (3) INSERIR CAMPO SESSAO DO MENU
  //###################################################################################

  function ensureMenuSectionField() {
    const form = document.querySelector('form[action="/settings/menu/create"]');

    if (!form) {
      return;
    }

    if (form.querySelector('[name="menu_section"]')) {
      return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "field";
    wrapper.innerHTML = [
      '<label for="create_menu_section">SESS&Atilde;O DO MENU *</label>',
      '<select id="create_menu_section" name="menu_section" required>',
      '  <option value="sistema">Sistema</option>',
      '  <option value="geral">Geral</option>',
      '  <option value="dados_gerais">Dados gerais</option>',
      '  <option value="igreja" selected>Igreja</option>',
      '  <option value="tesouraria">Tesouraria</option>',
      '</select>'
    ].join("");

    const visibilityField = findFieldByLabel(form, "Exibir no sistema");
    const nameField = findFieldByLabel(form, "Nome da pasta");

    if (visibilityField && visibilityField.parentNode) {
      visibilityField.parentNode.insertBefore(wrapper, visibilityField);
      return;
    }

    if (nameField && nameField.parentNode) {
      nameField.insertAdjacentElement("afterend", wrapper);
      return;
    }

    form.insertBefore(wrapper, form.firstChild);
  }

  //###################################################################################
  // (4) INICIALIZACAO
  //###################################################################################

  function init() {
    ensureMenuSectionField();
    window.setTimeout(ensureMenuSectionField, 100);
    window.setTimeout(ensureMenuSectionField, 500);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
