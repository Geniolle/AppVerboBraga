(function () {
  "use strict";

  //###################################################################################
  // (1) CONFIGURACAO DOS GRUPOS DE ABAS
  //###################################################################################

  const tabGroups_v1 = [
    {
      containerSelector: "#menu-tabs-card #submenu-items.menu-tabs",
      itemSelector: ".submenu-item"
    },
    {
      containerSelector: ".profile-process-tabs",
      itemSelector: ".profile-process-tab-btn"
    }
  ];

  let resizeTimer_v1 = null;
  let mutationTimer_v1 = null;

  //###################################################################################
  // (2) FUNCOES AUXILIARES
  //###################################################################################

  function isVisibleTab_v1(element) {
    if (!element) {
      return false;
    }

    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function clearTabWidth_v1(container, tabs) {
    container.style.removeProperty("--appverbo-process-tab-equal-width");

    tabs.forEach(function (tab) {
      tab.style.removeProperty("width");
      tab.style.removeProperty("min-width");
    });
  }

  function equalizeTabGroup_v1(containerSelector, itemSelector) {
    const containers = Array.from(document.querySelectorAll(containerSelector));

    containers.forEach(function (container) {
      const tabs = Array.from(container.querySelectorAll(itemSelector)).filter(isVisibleTab_v1);

      if (tabs.length <= 1) {
        clearTabWidth_v1(container, tabs);
        return;
      }

      clearTabWidth_v1(container, tabs);

      const maxWidth = Math.ceil(
        tabs.reduce(function (currentMax, tab) {
          return Math.max(currentMax, tab.getBoundingClientRect().width);
        }, 0)
      );

      if (maxWidth <= 0) {
        return;
      }

      container.style.setProperty("--appverbo-process-tab-equal-width", `${maxWidth}px`);
    });
  }

  //###################################################################################
  // (3) APLICAR REGRA GLOBAL DE LARGURA
  //###################################################################################

  function equalizeAllTabs_v1() {
    tabGroups_v1.forEach(function (group) {
      equalizeTabGroup_v1(group.containerSelector, group.itemSelector);
    });
  }

  function scheduleEqualizeTabs_v1() {
    window.clearTimeout(mutationTimer_v1);
    mutationTimer_v1 = window.setTimeout(equalizeAllTabs_v1, 60);
  }

  function handleResizeEqualTabs_v1() {
    window.clearTimeout(resizeTimer_v1);
    resizeTimer_v1 = window.setTimeout(equalizeAllTabs_v1, 120);
  }

  //###################################################################################
  // (4) INICIALIZACAO
  //###################################################################################

  function initAdminTabsEqualWidth_v1() {
    equalizeAllTabs_v1();

    window.setTimeout(equalizeAllTabs_v1, 100);
    window.setTimeout(equalizeAllTabs_v1, 300);
    window.setTimeout(equalizeAllTabs_v1, 800);

    window.addEventListener("resize", handleResizeEqualTabs_v1);

    const observer = new MutationObserver(scheduleEqualizeTabs_v1);
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAdminTabsEqualWidth_v1);
  } else {
    initAdminTabsEqualWidth_v1();
  }
})();