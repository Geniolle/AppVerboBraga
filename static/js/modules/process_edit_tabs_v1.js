//###################################################################################
// (1) PROCESS EDIT TABS V1
//###################################################################################
(function registerProcessEditTabsV1() {
  "use strict";

  function setupProcessEditTabsV1(context = {}) {
    const tabLinks = document.querySelectorAll("[data-process-edit-tab]");
    const panes = document.querySelectorAll("[data-process-edit-pane]");
    if (!tabLinks.length || !panes.length) {
      return;
    }

    function activateProcessTab(tabKey) {
      const hasTargetTab = Array.from(tabLinks).some(
        (tabLink) => (tabLink.getAttribute("data-process-edit-tab") || "") === tabKey
      );
      const resolvedTabKey = hasTargetTab ? tabKey : "geral";
      tabLinks.forEach((tabLink) => {
        const isActive = tabLink.getAttribute("data-process-edit-tab") === resolvedTabKey;
        tabLink.style.removeProperty("background");
        tabLink.style.removeProperty("background-color");
        tabLink.style.removeProperty("border-color");
        tabLink.style.removeProperty("color");
        tabLink.classList.toggle("active", isActive);
        tabLink.classList.toggle("is-active", isActive);
        tabLink.setAttribute("aria-selected", isActive ? "true" : "false");
        if (isActive) {
          tabLink.setAttribute("data-active", "true");
          tabLink.setAttribute("data-selected", "true");
          tabLink.removeAttribute("data-appverbo-force-active");
          tabLink.removeAttribute("data-appverbo-force-inactive");
          tabLink.removeAttribute("data-appverbo-menu-active");
        } else {
          tabLink.removeAttribute("data-active");
          tabLink.removeAttribute("data-selected");
          tabLink.removeAttribute("data-appverbo-force-active");
          tabLink.removeAttribute("data-appverbo-force-inactive");
          tabLink.removeAttribute("data-appverbo-menu-active");
        }
      });
      panes.forEach((pane) => {
        const isActive = pane.getAttribute("data-process-edit-pane") === resolvedTabKey;
        pane.classList.toggle("active", isActive);
      });
      window.dispatchEvent(new CustomEvent("appverbo:normalize-tabs-width-v1"));
    }

    tabLinks.forEach((tabLink) => {
      tabLink.addEventListener("click", (event) => {
        event.preventDefault();
        const tabKey = tabLink.getAttribute("data-process-edit-tab") || "geral";
        activateProcessTab(tabKey);
      });
    });

    if (context.settingsAction === "edit") {
      const cleanSettingsTab = String(context.settingsTab || "").trim();
      if (cleanSettingsTab) {
        activateProcessTab(cleanSettingsTab);
      } else {
        activateProcessTab("campos-config");
      }
    } else {
      activateProcessTab("geral");
    }
  }

  window.APPVERBO_SETUP_PROCESS_EDIT_TABS_V1 = setupProcessEditTabsV1;
})();
