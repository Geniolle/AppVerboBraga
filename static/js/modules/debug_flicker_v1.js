(function initAppVerboFlickerDebugV1() {
  "use strict";

  //###################################################################################
  // (1) GUARDAS E ESTADO
  //###################################################################################

  if (window.__appverboFlickerDebugV1 === true) {
    return;
  }

  let currentUrl = null;

  try {
    currentUrl = new URL(window.location.href);
  } catch (_error) {
    return;
  }

  if (String(currentUrl.searchParams.get("debug_flicker") || "").trim() !== "1") {
    return;
  }

  window.__appverboFlickerDebugV1 = true;

  const DEBUG_PREFIX_V1 = "[APPVERBO FLICKER DEBUG]";
  const debugStartedAtV1 = (
    typeof window.performance !== "undefined" &&
    typeof window.performance.now === "function"
  )
    ? window.performance.now()
    : Date.now();
  let mutationObserverV1 = null;
  let observerStopTimerV1 = 0;

  //###################################################################################
  // (2) UTILITARIOS
  //###################################################################################

  function getElapsedMsV1() {
    const now = (
      typeof window.performance !== "undefined" &&
      typeof window.performance.now === "function"
    )
      ? window.performance.now()
      : Date.now();
    return Math.round(now - debugStartedAtV1);
  }

  function normalizeTextV1(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function safeGetComputedStyleV1(element) {
    if (!element || typeof window.getComputedStyle !== "function") {
      return null;
    }

    try {
      return window.getComputedStyle(element);
    } catch (_error) {
      return null;
    }
  }

  function safeGetRectV1(element) {
    if (!element || typeof element.getBoundingClientRect !== "function") {
      return { width: 0, height: 0 };
    }

    try {
      return element.getBoundingClientRect();
    } catch (_error) {
      return { width: 0, height: 0 };
    }
  }

  function logGroupV1(title, payload) {
    console.groupCollapsed(
      DEBUG_PREFIX_V1 + " " + title + " (" + String(getElapsedMsV1()) + "ms)"
    );

    if (Array.isArray(payload)) {
      if (payload.length) {
        console.table(payload);
      } else {
        console.log("empty");
      }
    } else if (payload && typeof payload === "object") {
      console.table([payload]);
    } else if (typeof payload !== "undefined") {
      console.log(payload);
    }

    console.groupEnd();
  }

  function collectUniqueElementsV1() {
    const selectors = [
      "#menu-tabs-card",
      "#dynamic-process-card",
      "[data-standard-list-process-v1]",
      ".admin-subprocess-card-v1",
      "[data-menu-scope]"
    ];
    const uniqueElements = new Set();

    selectors.forEach(function (selector) {
      document.querySelectorAll(selector).forEach(function (element) {
        uniqueElements.add(element);
      });
    });

    return Array.from(uniqueElements);
  }

  function buildCardStateRowV1(element) {
    const computedStyle = safeGetComputedStyleV1(element);
    const rect = safeGetRectV1(element);
    const inlineDisplay = element && element.style ? element.style.display || "" : "";
    const computedDisplay = computedStyle ? computedStyle.display : "";
    const computedVisibility = computedStyle ? computedStyle.visibility : "";
    const computedOpacity = computedStyle ? computedStyle.opacity : "";
    const offsetParentExists = Boolean(element && element.offsetParent);
    const isHiddenAttr = element ? element.hasAttribute("hidden") : false;
    const isVisible = Boolean(
      element &&
      !isHiddenAttr &&
      computedDisplay !== "none" &&
      computedVisibility !== "hidden" &&
      computedOpacity !== "0" &&
      rect.width > 0 &&
      rect.height > 0 &&
      offsetParentExists
    );

    return {
      id: element && element.id ? element.id : "",
      className: normalizeTextV1(element && element.className ? element.className : ""),
      menuScope: element ? normalizeTextV1(element.getAttribute("data-menu-scope")) : "",
      inlineDisplay: inlineDisplay,
      computedDisplay: computedDisplay,
      visibility: computedVisibility,
      opacity: computedOpacity,
      hiddenAttr: isHiddenAttr,
      offsetParent: offsetParentExists,
      width: Math.round(rect.width || 0),
      height: Math.round(rect.height || 0),
      visible: isVisible
    };
  }

  function buildSidebarMenuStateV1() {
    const activeButton = document.querySelector(".menu-item.active");

    return {
      activeExists: Boolean(activeButton),
      dataMenu: activeButton ? normalizeTextV1(activeButton.getAttribute("data-menu")) : "",
      text: activeButton ? normalizeTextV1(activeButton.textContent) : ""
    };
  }

  function buildTopTabsStateV1() {
    const container = document.getElementById("submenu-items");

    if (!container) {
      return [];
    }

    return Array.from(container.querySelectorAll("a, button, .submenu-item")).map(function (element, index) {
      return {
        index: index,
        text: normalizeTextV1(element.textContent),
        className: normalizeTextV1(element.className || ""),
        active: element.classList.contains("active"),
        ariaSelected: String(element.getAttribute("aria-selected") || "")
      };
    });
  }

  function buildUrlStateV1() {
    let url = null;

    try {
      url = new URL(window.location.href);
    } catch (_error) {
      return {
        pathname: "",
        search: "",
        hash: "",
        menu: "",
        admin_tab: "",
        target: "",
        dynamic_process_section: "",
        settings_edit_key: "",
        sidebar_section_edit_key: ""
      };
    }

    return {
      pathname: url.pathname,
      search: url.search,
      hash: url.hash,
      menu: String(url.searchParams.get("menu") || ""),
      admin_tab: String(url.searchParams.get("admin_tab") || ""),
      target: String(url.searchParams.get("target") || ""),
      dynamic_process_section: String(url.searchParams.get("dynamic_process_section") || ""),
      settings_edit_key: String(url.searchParams.get("settings_edit_key") || ""),
      sidebar_section_edit_key: String(url.searchParams.get("sidebar_section_edit_key") || "")
    };
  }

  //###################################################################################
  // (3) SNAPSHOTS
  //###################################################################################

  function captureSnapshotV1(phaseLabel) {
    logGroupV1(phaseLabel + " - url state", buildUrlStateV1());
    logGroupV1(
      phaseLabel + " - cards state",
      collectUniqueElementsV1().map(buildCardStateRowV1)
    );
    logGroupV1(phaseLabel + " - sidebar state", buildSidebarMenuStateV1());
    logGroupV1(phaseLabel + " - top tabs state", buildTopTabsStateV1());
  }

  //###################################################################################
  // (4) OBSERVER
  //###################################################################################

  function disconnectObserverV1() {
    if (mutationObserverV1) {
      mutationObserverV1.disconnect();
      mutationObserverV1 = null;
    }
  }

  function startObserverV1() {
    disconnectObserverV1();

    const cards = collectUniqueElementsV1();

    if (!cards.length || typeof MutationObserver !== "function") {
      return;
    }

    mutationObserverV1 = new MutationObserver(function (mutations) {
      const rows = mutations.map(function (mutation) {
        const target = mutation.target;
        const computedStyle = safeGetComputedStyleV1(target);
        const cardState = buildCardStateRowV1(target);
        return {
          id: target && target.id ? target.id : "",
          className: normalizeTextV1(target && target.className ? target.className : ""),
          attributeName: String(mutation.attributeName || ""),
          oldValue: normalizeTextV1(mutation.oldValue || ""),
          newValue: normalizeTextV1(
            target && mutation.attributeName
              ? target.getAttribute(mutation.attributeName)
              : ""
          ),
          hiddenAttr: Boolean(target && target.hasAttribute("hidden")),
          inlineDisplay: target && target.style ? target.style.display || "" : "",
          computedDisplay: computedStyle ? computedStyle.display : "",
          visible: cardState.visible
        };
      });

      logGroupV1("mutation observer - cards", rows);
    });

    cards.forEach(function (card) {
      mutationObserverV1.observe(card, {
        attributes: true,
        attributeOldValue: true,
        attributeFilter: ["style", "class", "hidden"]
      });
    });

    if (observerStopTimerV1) {
      window.clearTimeout(observerStopTimerV1);
    }

    observerStopTimerV1 = window.setTimeout(function () {
      observerStopTimerV1 = 0;
      captureSnapshotV1("observer stop 2000ms");
      disconnectObserverV1();
    }, 2000);
  }

  //###################################################################################
  // (5) CICLO DE VIDA
  //###################################################################################

  captureSnapshotV1("script loaded");
  startObserverV1();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      captureSnapshotV1("DOMContentLoaded");
      startObserverV1();
    });
  } else {
    captureSnapshotV1("DOMContentLoaded");
    startObserverV1();
  }

  window.addEventListener("load", function () {
    captureSnapshotV1("window load");
    startObserverV1();
  });

  window.setTimeout(function () {
    captureSnapshotV1("setTimeout 0ms");
    startObserverV1();
  }, 0);

  window.setTimeout(function () {
    captureSnapshotV1("setTimeout 100ms");
    startObserverV1();
  }, 100);

  window.setTimeout(function () {
    captureSnapshotV1("setTimeout 300ms");
    startObserverV1();
  }, 300);

  window.setTimeout(function () {
    captureSnapshotV1("setTimeout 1000ms");
    startObserverV1();
  }, 1000);
}());
