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
      bootstrapTextSizeKey: "adminTabsTextSizePx",
      bootstrapFontFamilyKey: "adminTabsFontFamily",
      bootstrapColorKey: "adminTabsColorHex",
      bootstrapTextColorKey: "adminTabsTextColorHex",
      cssVariableName: "--appverbo-admin-tab-width-v1"
    },
    {
      containerSelector: ".profile-process-tabs",
      itemSelector: ".profile-process-tab-btn",
      fixedWidthCh: 24,
      bootstrapWidthKey: "adminTabsWidthCh",
      bootstrapTextSizeKey: "adminTabsTextSizePx",
      bootstrapFontFamilyKey: "adminTabsFontFamily",
      bootstrapColorKey: "adminTabsColorHex",
      bootstrapTextColorKey: "adminTabsTextColorHex",
      cssVariableName: "--appverbo-process-tab-equal-width"
    },
    {
      containerSelector: ".process-edit-tabs",
      itemSelector: ".process-edit-tab-link",
      fixedWidthCh: 24,
      bootstrapWidthKey: "adminTabsWidthCh",
      bootstrapTextSizeKey: "adminTabsTextSizePx",
      bootstrapFontFamilyKey: "adminTabsFontFamily",
      bootstrapColorKey: "adminTabsColorHex",
      bootstrapTextColorKey: "adminTabsTextColorHex",
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

  function applyInlineTextSizeToTabsV1(tabs, textSizePx) {
    const hasValidSize = Number.isFinite(textSizePx) && textSizePx > 0;
    const normalizedSize = hasValidSize ? `${Math.ceil(textSizePx)}px` : "";

    tabs.forEach(function (tab) {
      if (normalizedSize) {
        tab.style.setProperty("font-size", normalizedSize, "important");
      } else {
        tab.style.removeProperty("font-size");
      }

      Array.from(tab.querySelectorAll("*")).forEach(function (childElement) {
        if (normalizedSize) {
          childElement.style.setProperty("font-size", normalizedSize, "important");
        } else {
          childElement.style.removeProperty("font-size");
        }
      });
    });
  }

  function normalizeHexColorV1(value) {
    const rawValue = String(value || "").trim().replace(/\s+/g, "");

    if (!rawValue) {
      return "";
    }

    const cleanValue = rawValue.charAt(0) === "#" ? rawValue.slice(1) : rawValue;

    if (/^[0-9a-fA-F]{3}$/.test(cleanValue)) {
      const expandedValue = cleanValue
        .split("")
        .map(function (character) {
          return character + character;
        })
        .join("");
      return `#${expandedValue.toUpperCase()}`;
    }

    if (/^[0-9a-fA-F]{6}$/.test(cleanValue)) {
      return `#${cleanValue.toUpperCase()}`;
    }

    return "";
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

  function resolveBootstrapColorHex_v1(group) {
    const bootstrapColorKey = String(group.bootstrapColorKey || "").trim();

    if (!bootstrapColorKey) {
      return "";
    }

    const bootstrap = window.__APPVERBO_BOOTSTRAP__;

    if (!bootstrap || typeof bootstrap !== "object") {
      return "";
    }

    return normalizeHexColorV1(bootstrap[bootstrapColorKey]);
  }

  function resolveBootstrapTextSizePxV1(group) {
    const bootstrapTextSizeKey = String(group.bootstrapTextSizeKey || "").trim();

    if (!bootstrapTextSizeKey) {
      return null;
    }

    const bootstrap = window.__APPVERBO_BOOTSTRAP__;

    if (!bootstrap || typeof bootstrap !== "object") {
      return null;
    }

    const rawTextSizeValue = bootstrap[bootstrapTextSizeKey];
    const parsedTextSizeValue = Number.parseInt(String(rawTextSizeValue || "").trim(), 10);

    if (!Number.isFinite(parsedTextSizeValue) || parsedTextSizeValue <= 0) {
      return null;
    }

    return Math.max(10, Math.min(40, parsedTextSizeValue));
  }

  function resolveBootstrapTextColorHex_v1(group) {
    const bootstrapTextColorKey = String(group.bootstrapTextColorKey || "").trim();

    if (!bootstrapTextColorKey) {
      return "";
    }

    const bootstrap = window.__APPVERBO_BOOTSTRAP__;

    if (!bootstrap || typeof bootstrap !== "object") {
      return "";
    }

    return normalizeHexColorV1(bootstrap[bootstrapTextColorKey]);
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

  function isActiveTabStateV1(tab) {
    if (!tab) {
      return false;
    }

    const isProcessEditTab = Boolean(tab.closest(".process-edit-tabs"));

    if (tab.classList && tab.classList.contains("active")) {
      return true;
    }

    const ariaSelected = String(tab.getAttribute("aria-selected") || "").trim().toLowerCase();
    if (ariaSelected === "true") {
      return true;
    }

    const dataActive = String(tab.getAttribute("data-active") || "").trim().toLowerCase();
    if (dataActive === "true") {
      return true;
    }

    if (isProcessEditTab) {
      return false;
    }

    const dataSelected = String(tab.getAttribute("data-selected") || "").trim().toLowerCase();
    if (dataSelected === "true") {
      return true;
    }

    const forcedActive = String(tab.getAttribute("data-appverbo-force-active") || "").trim().toLowerCase();
    if (forcedActive === "true") {
      return true;
    }

    const menuActive = String(tab.getAttribute("data-appverbo-menu-active") || "").trim().toLowerCase();
    if (menuActive === "true") {
      return true;
    }

    return false;
  }

  function resolveTabTextColorFromBackgroundV1(hexColor) {
    const normalizedHexColor = normalizeHexColorV1(hexColor);

    if (!normalizedHexColor) {
      return "#FFFFFF";
    }

    const red = Number.parseInt(normalizedHexColor.slice(1, 3), 16);
    const green = Number.parseInt(normalizedHexColor.slice(3, 5), 16);
    const blue = Number.parseInt(normalizedHexColor.slice(5, 7), 16);
    const luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255;

    return luminance >= 0.62 ? "#1F2F4A" : "#FFFFFF";
  }

  function clearInlineColorStylesV1(tab) {
    tab.style.removeProperty("background");
    tab.style.removeProperty("background-color");
    tab.style.removeProperty("border-color");
    tab.style.removeProperty("color");

    Array.from(tab.querySelectorAll("*")).forEach(function (childElement) {
      childElement.style.removeProperty("color");
    });
  }

  function applyInlineColorToTabsV1(tabs, activeColorHex, activeTextColorHex) {
    tabs.forEach(function (tab) {
      clearInlineColorStylesV1(tab);
    });

    const normalizedColorHex = normalizeHexColorV1(activeColorHex);

    if (!normalizedColorHex) {
      return;
    }

    const normalizedTextColorHex = normalizeHexColorV1(activeTextColorHex);
    const textColor = normalizedTextColorHex || resolveTabTextColorFromBackgroundV1(normalizedColorHex);

    tabs.forEach(function (tab) {
      if (!isActiveTabStateV1(tab)) {
        return;
      }

      tab.style.setProperty("background", normalizedColorHex, "important");
      tab.style.setProperty("background-color", normalizedColorHex, "important");
      tab.style.setProperty("border-color", normalizedColorHex, "important");
      tab.style.setProperty("color", textColor, "important");

      Array.from(tab.querySelectorAll("*")).forEach(function (childElement) {
        childElement.style.setProperty("color", textColor, "important");
      });
    });
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
    const bootstrapTextSizePx = resolveBootstrapTextSizePxV1(group);
    const bootstrapFontFamily = resolveBootstrapFontFamily_v1(group);
    const bootstrapColorHex = resolveBootstrapColorHex_v1(group);
    const bootstrapTextColorHex = resolveBootstrapTextColorHex_v1(group);
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
      applyInlineTextSizeToTabsV1(tabs, bootstrapTextSizePx);
      applyInlineColorToTabsV1(tabs, bootstrapColorHex, bootstrapTextColorHex);

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
      characterData: true,
      attributes: true,
      attributeFilter: [
        "class",
        "aria-selected",
        "data-active",
        "data-selected",
        "data-appverbo-force-active",
        "data-appverbo-menu-active"
      ]
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAdminTabsEqualWidth_v1);
  } else {
    initAdminTabsEqualWidth_v1();
  }
})();
