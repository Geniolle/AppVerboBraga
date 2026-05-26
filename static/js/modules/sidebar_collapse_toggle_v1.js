//###################################################################################
// (1) SIDEBAR COLLAPSE TOGGLE - ESTADO GLOBAL
//###################################################################################
(function () {
  "use strict";

  const STORAGE_KEY_V1 = "appverbo:sidebar-collapsed-v1";
  const COLLAPSED_CLASS_V1 = "appverbo-sidebar-collapsed";

  function readCollapsedPreferenceV1() {
    try {
      return window.localStorage.getItem(STORAGE_KEY_V1) === "1";
    } catch (error) {
      return false;
    }
  }

  function persistCollapsedPreferenceV1(isCollapsed) {
    try {
      window.localStorage.setItem(STORAGE_KEY_V1, isCollapsed ? "1" : "0");
    } catch (error) {
      // Sem persistencia: segue com estado em memoria.
    }
  }

  function applyCollapsedStateV1(buttonEl, isCollapsed) {
    if (!document.body) {
      return;
    }

    document.body.classList.toggle(COLLAPSED_CLASS_V1, !!isCollapsed);

    if (!buttonEl) {
      return;
    }

    buttonEl.setAttribute(
      "aria-label",
      isCollapsed ? "Abrir menu lateral" : "Fechar menu lateral"
    );
    buttonEl.setAttribute("title", isCollapsed ? "Abrir menu lateral" : "Fechar menu lateral");
    buttonEl.setAttribute("aria-expanded", isCollapsed ? "false" : "true");
  }

  function setupSidebarCollapseToggleV1() {
    const buttonEl = document.getElementById("appverbo-sidebar-toggle");
    if (!buttonEl) {
      return;
    }

    let isCollapsed = readCollapsedPreferenceV1();
    applyCollapsedStateV1(buttonEl, isCollapsed);

    buttonEl.addEventListener("click", function () {
      isCollapsed = !isCollapsed;
      applyCollapsedStateV1(buttonEl, isCollapsed);
      persistCollapsedPreferenceV1(isCollapsed);
    });
  }

  document.addEventListener("DOMContentLoaded", setupSidebarCollapseToggleV1, { once: true });
})();

