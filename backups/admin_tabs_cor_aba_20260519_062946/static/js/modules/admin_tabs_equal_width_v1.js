(function () {
  "use strict";

  if (window.__appverboAdminTabsEqualWidthManagerLoadedV1 === true) {
    return;
  }
  window.__appverboAdminTabsEqualWidthManagerLoadedV1 = true;

  //###################################################################################
  // (1) CONFIGURACAO DOS GRUPOS DE ABAS
  //###################################################################################

  const tabGroups_v1 = [
    {
      containerSelector: "#menu-tabs-card #submenu-items.menu-tabs",
      itemSelector: ".submenu-item",
      fixedWidthCh: 24,
      bootstrapWidthKey: "adminTabsWidthCh",
      bootstrapFontFamilyKey: "adminTabsFontFamily",
      cssVariableName: "--appverbo-admin-tab-width-v1"
    },
    {
      containerSelector: ".profile-process-tabs",
      itemSelector: ".profile-process-tab-btn",
      fixedWidthCh: 24,
      cssVariableName: "--appverbo-process-tab-equal-width"
    },
    {
      containerSelector: ".process-edit-tabs",
      itemSelector: ".process-edit-tab-link",
      fixedWidthCh: 24,
      useInlineWidth: true
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

    const computedStyle = window.getComputedStyle(element);

    if (computedStyle.display === "none" || computedStyle.visibility === "hidden") {
      return false;
    }

    const rect = element.getBoundingClientRect();

    return rect.width > 0 && rect.height > 0;
  }

  function clearTabWidth_v1(container, tabs, cssVariableName, useInlineWidth) {
    if (cssVariableName) {
      container.style.removeProperty(cssVariableName);
    }

    if (useInlineWidth) {
      tabs.forEach(function (tab) {
        tab.style.removeProperty("width");
        tab.style.removeProperty("min-width");
        tab.style.removeProperty("max-width");
      });
    }
  }

  function measureNaturalTabWidth_v1(tab) {
    const widthValue = tab.style.getPropertyValue("width");
    const widthPriority = tab.style.getPropertyPriority("width");
    const minWidthValue = tab.style.getPropertyValue("min-width");
    const minWidthPriority = tab.style.getPropertyPriority("min-width");
    const maxWidthValue = tab.style.getPropertyValue("max-width");
    const maxWidthPriority = tab.style.getPropertyPriority("max-width");

    tab.style.removeProperty("width");
    tab.style.removeProperty("min-width");
    tab.style.removeProperty("max-width");

    const measuredWidth = Math.ceil(Math.max(tab.scrollWidth || 0, tab.getBoundingClientRect().width || 0));

    if (widthValue) {
      tab.style.setProperty("width", widthValue, widthPriority || "");
    }

    if (minWidthValue) {
      tab.style.setProperty("min-width", minWidthValue, minWidthPriority || "");
    }

    if (maxWidthValue) {
      tab.style.setProperty("max-width", maxWidthValue, maxWidthPriority || "");
    }

    return measuredWidth;
  }

  function applyInlineWidthToTabs_v1(tabs, resolvedWidthPx) {
    tabs.forEach(function (tab) {
      tab.style.setProperty("width", `${resolvedWidthPx}px`, "important");
      tab.style.setProperty("min-width", `${resolvedWidthPx}px`, "important");
      tab.style.setProperty("max-width", `${resolvedWidthPx}px`, "important");
    });
  }

  function applyInlineWidthValueToTabs_v1(tabs, widthValue) {
    tabs.forEach(function (tab) {
      tab.style.setProperty("width", widthValue, "important");
      tab.style.setProperty("min-width", widthValue, "important");
      tab.style.setProperty("max-width", widthValue, "important");
    });
  }

  function applyInlineFontFamilyToTabs_v1(tabs, fontFamilyValue) {
    tabs.forEach(function (tab) {
      if (fontFamilyValue) {
        tab.style.setProperty("font-family", fontFamilyValue, "important");
      } else {
        tab.style.removeProperty("font-family");
      }
    });
  }

  function resolveBootstrapFixedWidthCh_v1(group) {
    const bootstrapWidthKey = String(group.bootstrapWidthKey || "").trim();

    if (!bootstrapWidthKey) {
      return null;
    }

    const bootstrap = window.__APPVERBO_BOOTSTRAP__;

    if (!bootstrap || typeof bootstrap !== "object") {
      return null;
    }

    const rawWidthValue = bootstrap[bootstrapWidthKey];
    const parsedWidthValue = Number.parseInt(String(rawWidthValue || "").trim(), 10);

    if (!Number.isFinite(parsedWidthValue) || parsedWidthValue <= 0) {
      return null;
    }

    return Math.max(8, Math.min(60, parsedWidthValue));
  }

  function resolveBootstrapFontFamily_v1(group) {
    const bootstrapFontFamilyKey = String(group.bootstrapFontFamilyKey || "").trim();

    if (!bootstrapFontFamilyKey) {
      return "";
    }

    const bootstrap = window.__APPVERBO_BOOTSTRAP__;

    if (!bootstrap || typeof bootstrap !== "object") {
      return "";
    }

    const rawFontFamilyValue = String(bootstrap[bootstrapFontFamilyKey] || "").trim();

    if (!rawFontFamilyValue) {
      return "";
    }

    if (rawFontFamilyValue.length > 120) {
      return "";
    }

    if (/[\r\n;{}]/.test(rawFontFamilyValue)) {
      return "";
    }

    return rawFontFamilyValue;
  }

  function equalizeTabGroup_v1(group) {
    const containerSelector = group.containerSelector;
    const itemSelector = group.itemSelector;
    const minWidthPx = Number.isFinite(group.minWidthPx) ? group.minWidthPx : 0;
    const extraWidthPx = Number.isFinite(group.extraWidthPx) ? group.extraWidthPx : 0;
    const defaultFixedWidthCh = Number.isFinite(group.fixedWidthCh) ? group.fixedWidthCh : 0;
    const bootstrapFixedWidthCh = resolveBootstrapFixedWidthCh_v1(group);
    const fixedWidthCh = Number.isFinite(bootstrapFixedWidthCh)
      ? bootstrapFixedWidthCh
      : defaultFixedWidthCh;
    const bootstrapFontFamily = resolveBootstrapFontFamily_v1(group);
    const cssVariableName = String(group.cssVariableName || "").trim();
    const useInlineWidth = group.useInlineWidth === true;
    const containers = Array.from(document.querySelectorAll(containerSelector));

    containers.forEach(function (container) {
      if (!isVisibleTab_v1(container)) {
        return;
      }

      const tabs = Array.from(container.querySelectorAll(itemSelector)).filter(isVisibleTab_v1);

      if (!tabs.length) {
        return;
      }

      applyInlineFontFamilyToTabs_v1(tabs, bootstrapFontFamily);

      if (tabs.length === 1) {
        clearTabWidth_v1(container, tabs, cssVariableName, useInlineWidth);
        return;
      }

      if (fixedWidthCh > 0) {
        const fixedWidthValue = `${Math.ceil(fixedWidthCh)}ch`;

        if (cssVariableName) {
          container.style.setProperty(cssVariableName, fixedWidthValue);
        }

        if (useInlineWidth) {
          applyInlineWidthValueToTabs_v1(tabs, fixedWidthValue);
        }

        return;
      }

      const maxWidth = Math.ceil(
        tabs.reduce(function (currentMax, tab) {
          return Math.max(currentMax, measureNaturalTabWidth_v1(tab));
        }, 0)
      );

      const resolvedWidthPx = Math.ceil(Math.max(minWidthPx, maxWidth) + extraWidthPx);

      if (resolvedWidthPx <= 0) {
        return;
      }

      if (cssVariableName) {
        container.style.setProperty(cssVariableName, `${resolvedWidthPx}px`);
      }

      if (useInlineWidth) {
        applyInlineWidthToTabs_v1(tabs, resolvedWidthPx);
      }
    });
  }

  //###################################################################################
  // (3) APLICAR REGRA GLOBAL DE LARGURA
  //###################################################################################

  function equalizeAllTabs_v1() {
    tabGroups_v1.forEach(function (group) {
      equalizeTabGroup_v1(group);
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
    window.addEventListener("appverbo:normalize-tabs-width-v1", scheduleEqualizeTabs_v1);

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
