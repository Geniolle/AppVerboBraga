(function initAppVerboSidebarCollapseV1() {
  const STORAGE_KEY = "appverbo:sidebar-collapsed-v1";
  const COLLAPSED_CLASS = "appverbo-sidebar-collapsed";

  function readStoredState() {
    try {
      return window.localStorage.getItem(STORAGE_KEY) === "1";
    } catch (error) {
      return false;
    }
  }

  function writeStoredState(isCollapsed) {
    try {
      window.localStorage.setItem(STORAGE_KEY, isCollapsed ? "1" : "0");
    } catch (error) {
      // localStorage pode estar indisponivel em modo privado ou politicas restritivas.
    }
  }

  function applySidebarState(button, isCollapsed) {
    document.body.classList.toggle(COLLAPSED_CLASS, isCollapsed);

    if (!button) {
      return;
    }

    button.setAttribute("aria-expanded", String(!isCollapsed));
    button.setAttribute("aria-label", isCollapsed ? "Expandir menu lateral" : "Ocultar menu lateral");
    button.setAttribute("title", isCollapsed ? "Expandir menu lateral" : "Ocultar menu lateral");
  }

  function init() {
    const button = document.getElementById("sidebar-collapse-toggle");
    const sidebar = document.getElementById("app-sidebar");

    if (!button || !sidebar) {
      return;
    }

    applySidebarState(button, readStoredState());

    button.addEventListener("click", function handleSidebarCollapseClick() {
      const nextCollapsedState = !document.body.classList.contains(COLLAPSED_CLASS);
      applySidebarState(button, nextCollapsedState);
      writeStoredState(nextCollapsedState);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
