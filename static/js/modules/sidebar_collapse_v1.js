(function () {
  "use strict";

  var LS_KEY = "appverbo:sidebar-collapsed-v1";
  var CSS_CLASS = "appverbo-sidebar-collapsed";

  function isCollapsed() {
    try {
      return localStorage.getItem(LS_KEY) === "1";
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
    } catch (e) {
      /* localStorage indisponível — continua sem persistência */
    }
  }

  function updateButton(button, collapsed) {
    if (!button) return;
    if (collapsed) {
      button.setAttribute("aria-expanded", "false");
      button.setAttribute("aria-label", "Expandir menu lateral");
      button.setAttribute("title", "Expandir menu lateral");
    } else {
      button.setAttribute("aria-expanded", "true");
      button.setAttribute("aria-label", "Ocultar menu lateral");
      button.setAttribute("title", "Ocultar menu lateral");
    }
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
