//###################################################################################
// (1) SUBMENU OVERFLOW MENU V1
//###################################################################################
(function registerSubmenuOverflowMenuV1() {
  "use strict";

  if (window.__appverboSubmenuOverflowMenuLoadedV1 === true) {
    return;
  }
  window.__appverboSubmenuOverflowMenuLoadedV1 = true;
  window.__appverboSubmenuOverflowDebugV1 = true;

  function debugLogV1(message, payload) {
    if (window.__appverboSubmenuOverflowDebugV1 !== true) {
      return;
    }
    try {
      console.log("[APPVERBO_SUBMENU_OVERFLOW_V1]", message, payload || {});
    } catch (error) {
      // no-op
    }
  }

  const OVERFLOW_TARGETS_V1 = [
    {
      key: "submenu_tabs",
      itemsSelector: "#submenu-items",
      cardSelector: "#menu-tabs-card",
      stateKey: "__appverboSubmenuOverflowStateV1"
    },
    {
      key: "process_edit_tabs",
      itemsSelector: "#process-edit-tabs",
      cardSelector: "#settings-menu-edit-card",
      stateKey: "__appverboProcessEditOverflowStateV1"
    }
  ];

  function normalizeTextV1(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function isTabItemV1(element) {
    if (!element) {
      return false;
    }
    return element.matches(
      ".submenu-item, .process-edit-tab-link, a, button, [data-admin-tab], [data-process-edit-tab], [role='tab']"
    );
  }

  function resolveTabItemsV1(itemsEl) {
    return Array.from(itemsEl.children || []).filter(isTabItemV1);
  }

  function isHiddenByStyleV1(element) {
    if (!element) {
      return true;
    }
    const computed = window.getComputedStyle(element);
    if (computed.display === "none" || computed.visibility === "hidden") {
      return true;
    }
    const rect = element.getBoundingClientRect();
    return rect.width <= 0 || rect.height <= 0;
  }

  function isTabActiveV1(tabElement) {
    if (!tabElement) {
      return false;
    }
    if (tabElement.classList.contains("active")) {
      return true;
    }
    if (String(tabElement.getAttribute("aria-selected") || "").toLowerCase() === "true") {
      return true;
    }
    if (String(tabElement.getAttribute("data-appverbo-force-active") || "").toLowerCase() === "true") {
      return true;
    }
    if (String(tabElement.getAttribute("data-appverbo-menu-active") || "").toLowerCase() === "true") {
      return true;
    }
    return false;
  }

  function parsePxV1(value) {
    const parsed = Number.parseFloat(String(value || "").trim());
    if (!Number.isFinite(parsed)) {
      return 0;
    }
    return parsed;
  }

  function measureOuterWidthV1(element) {
    if (!element) {
      return 0;
    }
    const rect = element.getBoundingClientRect();
    const computed = window.getComputedStyle(element);
    return Math.ceil(
      rect.width +
      parsePxV1(computed.marginLeft) +
      parsePxV1(computed.marginRight)
    );
  }

  function closeOverflowPanelV1(state) {
    if (!state) {
      return;
    }
    if (state.panelOriginalParent && state.panel.parentElement !== state.panelOriginalParent) {
      if (state.panelOriginalNextSibling && state.panelOriginalNextSibling.parentElement === state.panelOriginalParent) {
        state.panelOriginalParent.insertBefore(state.panel, state.panelOriginalNextSibling);
      } else {
        state.panelOriginalParent.appendChild(state.panel);
      }
    }
    state.panel.hidden = true;
    state.trigger.setAttribute("aria-expanded", "false");
    state.host.removeAttribute("data-appverbo-overflow-open-v1");
    state.panel.style.removeProperty("position");
    state.panel.style.removeProperty("top");
    state.panel.style.removeProperty("left");
    state.panel.style.removeProperty("right");
    state.panel.style.removeProperty("z-index");
    state.panel.style.removeProperty("max-height");
    state.panel.style.removeProperty("overflow-y");
    state.panel.style.removeProperty("min-width");
  }

  function applyPopupPanelStylesV1(state) {
    if (!state || !state.panel || !state.list) {
      return;
    }
    state.panel.style.setProperty("background", "#ffffff", "important");
    state.panel.style.setProperty("border", "1px solid #9fb5d9", "important");
    state.panel.style.setProperty("border-radius", "8px", "important");
    state.panel.style.setProperty("box-shadow", "0 10px 24px rgba(15, 23, 42, 0.16)", "important");
    state.panel.style.setProperty("padding", "0", "important");
    state.panel.style.setProperty("overflow-x", "hidden", "important");
    state.list.style.setProperty("display", "flex", "important");
    state.list.style.setProperty("flex-direction", "column", "important");
    state.list.style.setProperty("gap", "0", "important");
    state.list.style.setProperty("background", "#ffffff", "important");
  }

  function positionFloatingPanelV1(state) {
    if (!state || state.panel.hidden) {
      return;
    }
    const triggerRect = state.trigger.getBoundingClientRect();
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
    const panelRect = state.panel.getBoundingClientRect();
    const rawPanelWidth = Math.max(220, Math.ceil(panelRect.width || 0));
    const panelWidth = Math.min(320, rawPanelWidth);
    const panelHeight = Math.max(40, Math.ceil(panelRect.height || 0));

    let left = Math.round(triggerRect.left);
    if (left < 8) {
      left = 8;
    }
    if ((left + panelWidth) > (viewportWidth - 8)) {
      left = Math.max(8, viewportWidth - panelWidth - 8);
    }

    let top = Math.round(triggerRect.bottom + 6);
    if ((top + panelHeight) > (viewportHeight - 8)) {
      top = Math.max(8, Math.round(triggerRect.top - panelHeight - 6));
    }

    state.panel.style.setProperty("position", "fixed", "important");
    state.panel.style.setProperty("left", `${left}px`, "important");
    state.panel.style.setProperty("top", `${top}px`, "important");
    state.panel.style.setProperty("right", "auto", "important");
    state.panel.style.setProperty("z-index", "2147483000", "important");
    state.panel.style.setProperty("min-width", "220px", "important");
    state.panel.style.setProperty("width", `${panelWidth}px`, "important");
    state.panel.style.setProperty("max-width", `${Math.min(320, viewportWidth - 16)}px`, "important");
    state.panel.style.setProperty("max-height", `${Math.max(160, viewportHeight - 24)}px`, "important");
    state.panel.style.setProperty("overflow-y", "auto", "important");
  }

  function openOverflowPanelV1(state) {
    if (!state) {
      return;
    }
    if (!state.panelOriginalParent) {
      state.panelOriginalParent = state.panel.parentElement || state.host;
      state.panelOriginalNextSibling = state.panel.nextSibling;
    }
    if (state.panel.parentElement !== document.body) {
      document.body.appendChild(state.panel);
    }
    applyPopupPanelStylesV1(state);
    state.panel.hidden = false;
    state.trigger.setAttribute("aria-expanded", "true");
    state.host.setAttribute("data-appverbo-overflow-open-v1", "true");
    positionFloatingPanelV1(state);
  }

  function toggleOverflowPanelV1(state) {
    if (!state) {
      return;
    }
    if (state.panel.hidden) {
      openOverflowPanelV1(state);
      return;
    }
    closeOverflowPanelV1(state);
  }

  function hideOverflowHostV1(state) {
    if (!state) {
      return;
    }
    state.host.style.display = "none";
    state.trigger.textContent = "Mais";
    state.list.innerHTML = "";
    state.host.removeAttribute("data-appverbo-overflow-open-v1");
    closeOverflowPanelV1(state);
  }

  function showOverflowHostV1(state) {
    if (!state) {
      return;
    }
    state.host.style.display = "inline-flex";
  }

  function clearTabOverflowStateV1(tabItems) {
    tabItems.forEach((tabElement) => {
      tabElement.removeAttribute("data-appverbo-overflow-hidden-v1");
      tabElement.removeAttribute("aria-hidden");
      tabElement.hidden = false;
      tabElement.style.removeProperty("display");
      tabElement.style.removeProperty("visibility");
      tabElement.style.removeProperty("pointer-events");
      tabElement.style.removeProperty("position");
    });
  }

  function measureHostWidthV1(state) {
    const previousDisplay = state.host.style.display;
    const previousVisibility = state.host.style.visibility;

    state.host.style.display = "inline-flex";
    state.host.style.visibility = "hidden";
    const measuredWidth = Math.max(44, Math.ceil(state.host.getBoundingClientRect().width));
    state.host.style.display = previousDisplay;
    state.host.style.visibility = previousVisibility;

    return measuredWidth;
  }

  function ensureOverflowStructureV1(itemsEl, targetConfig) {
    const cardSelector = targetConfig && targetConfig.cardSelector
      ? String(targetConfig.cardSelector)
      : "";
    if (!cardSelector) {
      return null;
    }
    const cardEl = itemsEl.closest(cardSelector);
    if (!cardEl) {
      return null;
    }

    let rowEl = cardEl.querySelector("[data-appverbo-submenu-overflow-row-v1='1']");
    if (!rowEl) {
      rowEl = document.createElement("div");
      rowEl.className = "appverbo-submenu-overflow-row-v1";
      rowEl.setAttribute("data-appverbo-submenu-overflow-row-v1", "1");
      itemsEl.parentElement.insertBefore(rowEl, itemsEl);
      rowEl.appendChild(itemsEl);
    } else if (!rowEl.contains(itemsEl)) {
      rowEl.insertBefore(itemsEl, rowEl.firstChild || null);
    }

    let hostEl = rowEl.querySelector("[data-appverbo-submenu-overflow-host-v1='1']");
    if (!hostEl) {
      hostEl = document.createElement("div");
      hostEl.className = "appverbo-submenu-overflow-host-v1";
      hostEl.setAttribute("data-appverbo-submenu-overflow-host-v1", "1");
      hostEl.style.display = "none";
      rowEl.appendChild(hostEl);
    }

    let triggerEl = hostEl.querySelector("[data-appverbo-submenu-overflow-trigger-v1='1']");
    if (!triggerEl) {
      triggerEl = document.createElement("button");
      triggerEl.type = "button";
      triggerEl.className = "appverbo-submenu-overflow-trigger-v1";
      triggerEl.textContent = "Mais";
      triggerEl.setAttribute("data-appverbo-submenu-overflow-trigger-v1", "1");
      triggerEl.setAttribute("aria-haspopup", "true");
      triggerEl.setAttribute("aria-expanded", "false");
      hostEl.appendChild(triggerEl);
    }

    let panelEl = hostEl.querySelector("[data-appverbo-submenu-overflow-panel-v1='1']");
    if (!panelEl) {
      panelEl = document.createElement("div");
      panelEl.className = "appverbo-submenu-overflow-panel-v1";
      panelEl.setAttribute("data-appverbo-submenu-overflow-panel-v1", "1");
      panelEl.hidden = true;
      hostEl.appendChild(panelEl);
    }

    let listEl = panelEl.querySelector("[data-appverbo-submenu-overflow-list-v1='1']");
    if (!listEl) {
      listEl = document.createElement("div");
      listEl.className = "appverbo-submenu-overflow-list-v1";
      listEl.setAttribute("data-appverbo-submenu-overflow-list-v1", "1");
      panelEl.appendChild(listEl);
    }

    cardEl.classList.add("appverbo-submenu-overflow-enabled-v1");
    cardEl.classList.add("appverbo-submenu-overflow-scope-v1");
    cardEl.style.setProperty("position", "relative");
    cardEl.style.setProperty("overflow", "visible");

    rowEl.style.setProperty("display", "flex");
    rowEl.style.setProperty("align-items", "flex-end");
    rowEl.style.setProperty("flex-wrap", "nowrap");
    rowEl.style.setProperty("min-width", "0");

    itemsEl.style.setProperty("display", "flex");
    itemsEl.style.setProperty("flex-wrap", "nowrap");
    itemsEl.style.setProperty("align-items", "flex-end");
    itemsEl.style.setProperty("min-width", "0");

    const state = {
      cardEl,
      rowEl,
      itemsEl,
      host: hostEl,
      trigger: triggerEl,
      panel: panelEl,
      list: listEl,
      tabMap: new Map(),
      syncRafId: 0,
      observersBound: false,
      resizeObserver: null,
      mutationObserver: null,
      panelOriginalParent: null,
      panelOriginalNextSibling: null
    };

    return state;
  }

  function renderOverflowItemsV1(state, hiddenTabItems) {
    state.tabMap.clear();
    state.list.innerHTML = "";

    if (!hiddenTabItems.length) {
      state.trigger.textContent = "Mais";
      debugLogV1("renderOverflowItemsV1.empty", {
        hiddenCount: 0
      });
      return;
    }

    state.trigger.textContent = "Mais";
    debugLogV1("renderOverflowItemsV1.items", {
      hiddenCount: hiddenTabItems.length,
      labels: hiddenTabItems.map((tabElement) => normalizeTextV1(tabElement.textContent))
    });

    hiddenTabItems.forEach((tabElement, index) => {
      const optionButton = document.createElement("button");
      optionButton.type = "button";
      optionButton.className = "appverbo-submenu-overflow-option-v1";
      optionButton.textContent = normalizeTextV1(tabElement.textContent) || `Opcao ${index + 1}`;
      optionButton.style.setProperty("display", "block", "important");
      optionButton.style.setProperty("width", "100%", "important");
      optionButton.style.setProperty("min-height", "34px", "important");
      optionButton.style.setProperty("padding", "8px 12px", "important");
      optionButton.style.setProperty("margin", "0", "important");
      optionButton.style.setProperty("border", "0", "important");
      optionButton.style.setProperty("border-bottom", "1px solid #d9e2f2", "important");
      optionButton.style.setProperty("border-radius", "0", "important");
      optionButton.style.setProperty("background", "#ffffff", "important");
      optionButton.style.setProperty("color", "#0f172a", "important");
      optionButton.style.setProperty("font-size", "14px", "important");
      optionButton.style.setProperty("font-weight", "500", "important");
      optionButton.style.setProperty("line-height", "1.3", "important");
      optionButton.style.setProperty("text-align", "left", "important");
      optionButton.style.setProperty("white-space", "nowrap", "important");
      optionButton.style.setProperty("text-overflow", "ellipsis", "important");
      optionButton.style.setProperty("overflow", "hidden", "important");
      optionButton.style.setProperty("cursor", "pointer", "important");
      optionButton.addEventListener("mouseenter", () => {
        optionButton.style.setProperty("background", "#eef4ff", "important");
        optionButton.style.setProperty("color", "#0b63d1", "important");
      });
      optionButton.addEventListener("mouseleave", () => {
        if (String(optionButton.getAttribute("data-appverbo-overflow-active-v1") || "").toLowerCase() === "true") {
          optionButton.style.setProperty("background", "#e9f1ff", "important");
          optionButton.style.setProperty("color", "#0b63d1", "important");
          optionButton.style.setProperty("font-weight", "700", "important");
          return;
        }
        optionButton.style.setProperty("background", "#ffffff", "important");
        optionButton.style.setProperty("color", "#0f172a", "important");
      });
      optionButton.setAttribute("data-appverbo-overflow-option-id-v1", String(index));
      if (isTabActiveV1(tabElement)) {
        optionButton.setAttribute("data-appverbo-overflow-active-v1", "true");
        optionButton.style.setProperty("background", "#e9f1ff", "important");
        optionButton.style.setProperty("color", "#0b63d1", "important");
        optionButton.style.setProperty("font-weight", "700", "important");
      }
      state.tabMap.set(String(index), tabElement);
      state.list.appendChild(optionButton);
    });

    const lastButton = state.list.lastElementChild;
    if (lastButton && lastButton.style) {
      lastButton.style.setProperty("border-bottom", "0", "important");
    }
  }

  function resolveVisibleFlagsV1(tabWidths, availableTabsWidth, activeIndex) {
    const visibleFlags = tabWidths.map(() => true);
    let occupiedWidth = tabWidths.reduce((sum, width) => sum + width, 0);

    if (occupiedWidth <= availableTabsWidth) {
      return visibleFlags;
    }

    for (let index = tabWidths.length - 1; index >= 0; index -= 1) {
      if (occupiedWidth <= availableTabsWidth) {
        break;
      }
      if (index === activeIndex) {
        continue;
      }
      if (!visibleFlags[index]) {
        continue;
      }
      visibleFlags[index] = false;
      occupiedWidth -= tabWidths[index];
    }

    if (occupiedWidth <= availableTabsWidth) {
      return visibleFlags;
    }

    for (let index = tabWidths.length - 1; index >= 0; index -= 1) {
      if (occupiedWidth <= availableTabsWidth) {
        break;
      }
      if (!visibleFlags[index]) {
        continue;
      }
      visibleFlags[index] = false;
      occupiedWidth -= tabWidths[index];
    }

    if (!visibleFlags.some(Boolean) && tabWidths.length) {
      visibleFlags[0] = true;
    }

    return visibleFlags;
  }

  function applyOverflowDistributionV1(state) {
    const itemsEl = state.itemsEl;
    const tabItems = resolveTabItemsV1(itemsEl);
    debugLogV1("applyOverflowDistributionV1.start", {
      tabCount: tabItems.length
    });

    state.cardEl.classList.add("appverbo-submenu-overflow-enabled-v1");
    state.cardEl.style.setProperty("position", "relative");
    state.cardEl.style.setProperty("overflow", "visible");
    state.rowEl.style.setProperty("display", "flex");
    state.rowEl.style.setProperty("align-items", "flex-end");
    state.rowEl.style.setProperty("flex-wrap", "nowrap");
    state.itemsEl.style.setProperty("display", "flex");
    state.itemsEl.style.setProperty("flex-wrap", "nowrap");
    state.itemsEl.style.setProperty("align-items", "flex-end");
    state.itemsEl.style.setProperty("overflow-x", "hidden");
    state.itemsEl.style.setProperty("overflow-y", "hidden");

    clearTabOverflowStateV1(tabItems);

    const firstVisibleTab = tabItems.find((tabElement) => !isHiddenByStyleV1(tabElement)) || tabItems[0] || null;
    if (firstVisibleTab) {
      const rowHeight = Math.max(28, Math.ceil(firstVisibleTab.getBoundingClientRect().height));
      state.itemsEl.style.setProperty("max-height", `${rowHeight}px`);
      state.rowEl.style.setProperty("max-height", `${rowHeight + 2}px`);
      state.rowEl.style.setProperty("overflow", "hidden");
    }

    if (!tabItems.length || isHiddenByStyleV1(state.rowEl) || isHiddenByStyleV1(itemsEl)) {
      debugLogV1("applyOverflowDistributionV1.skip_hidden", {
        rowHidden: isHiddenByStyleV1(state.rowEl),
        itemsHidden: isHiddenByStyleV1(itemsEl)
      });
      hideOverflowHostV1(state);
      return;
    }

    const totalTabsWidth = tabItems.reduce((sum, tabElement) => sum + measureOuterWidthV1(tabElement), 0);
    const rowWidth = Math.floor(state.rowEl.clientWidth || 0);

    if (rowWidth <= 0) {
      debugLogV1("applyOverflowDistributionV1.row_width_zero", {
        rowWidth
      });
      window.setTimeout(() => {
        scheduleOverflowSyncV1(state);
      }, 32);
      return;
    }

    if (totalTabsWidth <= rowWidth) {
      debugLogV1("applyOverflowDistributionV1.no_overflow", {
        totalTabsWidth,
        rowWidth
      });
      hideOverflowHostV1(state);
      return;
    }

    const hostWidth = measureHostWidthV1(state);
    const rowStyle = window.getComputedStyle(state.rowEl);
    const rowGapPx = parsePxV1(rowStyle.columnGap || rowStyle.gap);
    const availableTabsWidth = Math.max(0, rowWidth - hostWidth - rowGapPx);
    const tabWidths = tabItems.map((tabElement) => measureOuterWidthV1(tabElement));
    const activeIndex = tabItems.findIndex((tabElement) => isTabActiveV1(tabElement));
    const visibleFlags = resolveVisibleFlagsV1(tabWidths, availableTabsWidth, activeIndex);
    debugLogV1("applyOverflowDistributionV1.measure", {
      rowWidth,
      totalTabsWidth,
      hostWidth,
      rowGapPx,
      availableTabsWidth,
      tabWidths,
      activeIndex
    });

    const resolvedHiddenTabItems = [];
    tabItems.forEach((tabElement, index) => {
      if (visibleFlags[index]) {
        tabElement.removeAttribute("data-appverbo-overflow-hidden-v1");
        tabElement.removeAttribute("aria-hidden");
        tabElement.hidden = false;
        tabElement.style.removeProperty("display");
        tabElement.style.removeProperty("visibility");
        tabElement.style.removeProperty("pointer-events");
        tabElement.style.removeProperty("position");
        return;
      }
      tabElement.setAttribute("data-appverbo-overflow-hidden-v1", "true");
      tabElement.setAttribute("aria-hidden", "true");
      tabElement.hidden = true;
      tabElement.style.setProperty("display", "none", "important");
      tabElement.style.setProperty("visibility", "hidden", "important");
      tabElement.style.setProperty("pointer-events", "none", "important");
      tabElement.style.setProperty("position", "absolute", "important");
      resolvedHiddenTabItems.push(tabElement);
    });

    if (!resolvedHiddenTabItems.length) {
      const firstTop = tabItems.length ? tabItems[0].offsetTop : 0;
      const wrappedTabItems = tabItems.filter((tabElement) => tabElement.offsetTop > (firstTop + 1));
      if (wrappedTabItems.length) {
        debugLogV1("applyOverflowDistributionV1.fallback_wrapped", {
          wrappedCount: wrappedTabItems.length,
          labels: wrappedTabItems.map((tabElement) => normalizeTextV1(tabElement.textContent))
        });
        wrappedTabItems.forEach((tabElement) => {
          tabElement.setAttribute("data-appverbo-overflow-hidden-v1", "true");
          tabElement.setAttribute("aria-hidden", "true");
          tabElement.hidden = true;
          tabElement.style.setProperty("display", "none", "important");
          tabElement.style.setProperty("visibility", "hidden", "important");
          tabElement.style.setProperty("pointer-events", "none", "important");
          tabElement.style.setProperty("position", "absolute", "important");
        });
        showOverflowHostV1(state);
        renderOverflowItemsV1(state, wrappedTabItems);
        return;
      }
      debugLogV1("applyOverflowDistributionV1.no_hidden_after_fallback", {});
      hideOverflowHostV1(state);
      return;
    }

    debugLogV1("applyOverflowDistributionV1.hidden", {
      hiddenCount: resolvedHiddenTabItems.length,
      labels: resolvedHiddenTabItems.map((tabElement) => normalizeTextV1(tabElement.textContent))
    });
    showOverflowHostV1(state);
    renderOverflowItemsV1(state, resolvedHiddenTabItems);
  }

  function scheduleOverflowSyncV1(state) {
    if (!state || state.syncRafId) {
      return;
    }
    state.syncRafId = window.requestAnimationFrame(() => {
      state.syncRafId = 0;
      applyOverflowDistributionV1(state);
    });
  }

  function bindObserversV1(state) {
    if (!state || state.observersBound) {
      return;
    }
    state.observersBound = true;

    state.trigger.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();

      const tabItems = resolveTabItemsV1(state.itemsEl);
      const hiddenByFlag = tabItems.filter((tabElement) => {
        return String(tabElement.getAttribute("data-appverbo-overflow-hidden-v1") || "").toLowerCase() === "true";
      });
      debugLogV1("trigger.click.start", {
        tabCount: tabItems.length,
        hiddenByFlagCount: hiddenByFlag.length,
        listChildrenBefore: state.list.children.length
      });
      if (!hiddenByFlag.length) {
        const firstTop = tabItems.length ? tabItems[0].offsetTop : 0;
        const wrappedTabItems = tabItems.filter((tabElement) => tabElement.offsetTop > (firstTop + 1));
        if (wrappedTabItems.length) {
          debugLogV1("trigger.click.wrapped_detected", {
            wrappedCount: wrappedTabItems.length,
            labels: wrappedTabItems.map((tabElement) => normalizeTextV1(tabElement.textContent))
          });
          wrappedTabItems.forEach((tabElement) => {
            tabElement.setAttribute("data-appverbo-overflow-hidden-v1", "true");
            tabElement.setAttribute("aria-hidden", "true");
            tabElement.hidden = true;
            tabElement.style.setProperty("display", "none", "important");
            tabElement.style.setProperty("visibility", "hidden", "important");
            tabElement.style.setProperty("pointer-events", "none", "important");
            tabElement.style.setProperty("position", "absolute", "important");
          });
          renderOverflowItemsV1(state, wrappedTabItems);
          showOverflowHostV1(state);
        } else {
          const rowRect = state.rowEl.getBoundingClientRect();
          const hostRect = state.host.getBoundingClientRect();
          const visibleRightLimit = Math.floor(Math.min(rowRect.right, hostRect.left) - 2);
          const overflowedByRect = tabItems.filter((tabElement) => {
            const tabRect = tabElement.getBoundingClientRect();
            return Math.ceil(tabRect.right) > visibleRightLimit;
          });
          debugLogV1("trigger.click.rect_detected", {
            visibleRightLimit,
            overflowedCount: overflowedByRect.length,
            labels: overflowedByRect.map((tabElement) => normalizeTextV1(tabElement.textContent))
          });
          if (overflowedByRect.length) {
            overflowedByRect.forEach((tabElement) => {
              tabElement.setAttribute("data-appverbo-overflow-hidden-v1", "true");
              tabElement.setAttribute("aria-hidden", "true");
              tabElement.hidden = true;
              tabElement.style.setProperty("display", "none", "important");
              tabElement.style.setProperty("visibility", "hidden", "important");
              tabElement.style.setProperty("pointer-events", "none", "important");
              tabElement.style.setProperty("position", "absolute", "important");
            });
            renderOverflowItemsV1(state, overflowedByRect);
            showOverflowHostV1(state);
          } else {
            debugLogV1("trigger.click.no_overflow_detected", {});
            scheduleOverflowSyncV1(state);
          }
        }
      }

      if (!state.list.children.length) {
        const fallbackTabItems = tabItems.filter((tabElement) => !isTabActiveV1(tabElement));
        if (fallbackTabItems.length) {
          debugLogV1("trigger.click.fallback_non_active", {
            fallbackCount: fallbackTabItems.length,
            labels: fallbackTabItems.map((tabElement) => normalizeTextV1(tabElement.textContent))
          });
          renderOverflowItemsV1(state, fallbackTabItems);
          showOverflowHostV1(state);
        }
      }

      debugLogV1("trigger.click.before_toggle", {
        listChildrenAfter: state.list.children.length,
        panelHidden: state.panel.hidden
      });
      toggleOverflowPanelV1(state);
      debugLogV1("trigger.click.after_toggle", {
        panelHidden: state.panel.hidden,
        ariaExpanded: state.trigger.getAttribute("aria-expanded")
      });
    });

    state.list.addEventListener("click", (event) => {
      const optionButton = event.target.closest("[data-appverbo-overflow-option-id-v1]");
      if (!optionButton) {
        return;
      }
      const optionId = String(optionButton.getAttribute("data-appverbo-overflow-option-id-v1") || "");
      const targetTab = state.tabMap.get(optionId);
      if (targetTab && typeof targetTab.click === "function") {
        targetTab.click();
      }
      closeOverflowPanelV1(state);
    });

    document.addEventListener("click", (event) => {
      const insideHost = state.host.contains(event.target);
      const insidePanel = state.panel.contains(event.target);
      if (!insideHost && !insidePanel) {
        closeOverflowPanelV1(state);
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeOverflowPanelV1(state);
      }
    });

    if (typeof ResizeObserver === "function") {
      state.resizeObserver = new ResizeObserver(() => {
        scheduleOverflowSyncV1(state);
        positionFloatingPanelV1(state);
      });
      state.resizeObserver.observe(state.rowEl);
      state.resizeObserver.observe(state.itemsEl);
    } else {
      window.addEventListener("resize", () => {
        scheduleOverflowSyncV1(state);
        positionFloatingPanelV1(state);
      });
    }

    window.addEventListener("scroll", () => {
      positionFloatingPanelV1(state);
    }, true);

    state.mutationObserver = new MutationObserver(() => {
      scheduleOverflowSyncV1(state);
    });
    state.mutationObserver.observe(state.itemsEl, {
      childList: true,
      subtree: false,
      attributes: true,
      attributeFilter: ["class", "aria-selected", "data-appverbo-force-active", "data-appverbo-menu-active"]
    });

    window.addEventListener("appverbo:normalize-tabs-width-v1", () => {
      scheduleOverflowSyncV1(state);
    });
  }

  function setupOverflowForTargetV1(targetConfig) {
    if (!targetConfig || !targetConfig.itemsSelector || !targetConfig.stateKey) {
      return null;
    }

    const itemsEl = document.querySelector(String(targetConfig.itemsSelector));
    if (!itemsEl) {
      debugLogV1("setup.not_found", {
        target: targetConfig.key || "unknown",
        selector: targetConfig.itemsSelector
      });
      return null;
    }

    let state = itemsEl[targetConfig.stateKey];
    if (!state) {
      state = ensureOverflowStructureV1(itemsEl, targetConfig);
      if (!state) {
        return null;
      }
      itemsEl[targetConfig.stateKey] = state;
    }

    bindObserversV1(state);
    scheduleOverflowSyncV1(state);
    debugLogV1("setup.done", {
      target: targetConfig.key || "unknown",
      itemsFound: true,
      childCount: (itemsEl.children || []).length
    });
    return state;
  }

  function setupSubmenuOverflowMenuV1() {
    const states = [];
    OVERFLOW_TARGETS_V1.forEach((targetConfig) => {
      const state = setupOverflowForTargetV1(targetConfig);
      if (state) {
        states.push(state);
      }
    });
    return states;
  }

  window.APPVERBO_SETUP_SUBMENU_OVERFLOW_MENU_V1 = setupSubmenuOverflowMenuV1;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      setupSubmenuOverflowMenuV1();
    });
  } else {
    setupSubmenuOverflowMenuV1();
  }
})();
