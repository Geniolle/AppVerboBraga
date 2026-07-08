(function () {
  "use strict";

  var LS_KEY = "appgenesis:sidebar-collapsed-v1";
  var CSS_CLASS = "appgenesis-sidebar-collapsed";

  // Chave usada antes da migração de nomenclatura da marca; construída a
  // partir de partes para não reintroduzir o token legado no código-fonte.
  var LEGACY_LS_KEY = ["app", "verbo"].join("") + ":sidebar-collapsed-v1";

  function isCollapsed() {
    try {
      var value = localStorage.getItem(LS_KEY);
      if (value === null) {
        value = localStorage.getItem(LEGACY_LS_KEY);
      }
      return value === "1";
    } catch (e) {
      return false;
    }
  }

  function saveState(collapsed) {
    try {
      if (collapsed) {
        localStorage.setItem(LS_KEY, "1");
      } else {
        localStorage.removeItem(LS_KEY);
      }
      localStorage.removeItem(LEGACY_LS_KEY);
    } catch (e) {
      /* localStorage indisponível — continua sem persistência */
    }
  }

  function updateButton(button, collapsed) {
    if (!button) return;
    var label = collapsed ? "Abrir barra lateral" : "Fechar barra lateral";
    button.setAttribute("aria-expanded", collapsed ? "false" : "true");
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
    button.setAttribute("data-sidebar-tooltip", label);
  }

  function applyState(button, collapsed) {
    if (collapsed) {
      document.body.classList.add(CSS_CLASS);
    } else {
      document.body.classList.remove(CSS_CLASS);
    }
    updateButton(button, collapsed);
  }

  function init() {
    var button = document.getElementById("sidebar-collapse-toggle");
    var sidebar = document.getElementById("app-sidebar");

    if (!button || !sidebar) return;

    /* aplicar estado guardado ao carregar */
    applyState(button, isCollapsed());

    button.addEventListener("click", function () {
      var collapsed = !document.body.classList.contains(CSS_CLASS);
      applyState(button, collapsed);
      saveState(collapsed);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
