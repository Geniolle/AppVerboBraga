(function initAppVerboTopSubmenuRuntimeV1(global) {
  "use strict";

  if (!global) {
    return;
  }

  if (
    global.AppVerboTopSubmenu &&
    typeof global.AppVerboTopSubmenu.createTopSubmenuController === "function"
  ) {
    return;
  }

  //###################################################################################
  // (1) NORMALIZAR DADOS DO SUBMENU
  //###################################################################################

  function normalizeDatasetObject_v1(rawDataset) {
    if (!rawDataset || typeof rawDataset !== "object" || Array.isArray(rawDataset)) {
      return {};
    }

    const normalizedDataset = {};

    Object.keys(rawDataset)
      .sort()
      .forEach((rawKey) => {
        const cleanKey = String(rawKey || "").trim();
        const cleanValue = String(rawDataset[rawKey] ?? "").trim();

        if (!cleanKey || !cleanValue || cleanKey === "submenuIndex") {
          return;
        }

        if (cleanKey === "dynamicProcessSection") {
          normalizedDataset.dynamicProcessSectionKey = cleanValue;
          return;
        }

        normalizedDataset[cleanKey] = cleanValue;
      });

    return normalizedDataset;
  }

  function buildSelectionDataset_v1(item) {
    const selectionDataset = normalizeDatasetObject_v1(item && item.dataset);

    if (item && item.profileSection) {
      selectionDataset.profileSection = String(item.profileSection || "").trim();
    }

    if (item && item.dynamicProcessSectionKey) {
      selectionDataset.dynamicProcessSectionKey = String(item.dynamicProcessSectionKey || "").trim();
    }

    return normalizeDatasetObject_v1(selectionDataset);
  }

  function buildRenderSignature_v1(items) {
    const safeItems = Array.isArray(items) ? items : [];

    return JSON.stringify(
      safeItems.map((item) => ({
        label: String(item && item.label || "").trim(),
        target: String(item && item.target || "").trim(),
        profileSection: String(item && item.profileSection || "").trim(),
        dynamicProcessSectionKey: String(item && item.dynamicProcessSectionKey || "").trim(),
        dataset: buildSelectionDataset_v1(item)
      }))
    );
  }

  function buildLookupKey_v1(targetSelector, rawSelectedDataset) {
    const cleanTargetSelector = String(targetSelector || "").trim();
    const normalizedDataset = normalizeDatasetObject_v1(rawSelectedDataset);
    const keyParts = [`target:${cleanTargetSelector}`];

    Object.keys(normalizedDataset)
      .sort()
      .forEach((datasetKey) => {
        keyParts.push(`${datasetKey}:${normalizedDataset[datasetKey]}`);
      });

    return keyParts.join("|");
  }

  function buildLinkSelectionDataset_v1(linkEl) {
    if (!linkEl || !linkEl.dataset) {
      return {};
    }

    const selectionDataset = normalizeDatasetObject_v1(linkEl.dataset);

    if (linkEl.dataset.profileSection) {
      selectionDataset.profileSection = String(linkEl.dataset.profileSection || "").trim();
    }

    if (linkEl.dataset.dynamicProcessSection) {
      selectionDataset.dynamicProcessSectionKey = String(linkEl.dataset.dynamicProcessSection || "").trim();
    }

    return normalizeDatasetObject_v1(selectionDataset);
  }


  //###################################################################################
  // (2) HELPER — NAVEGAÇÃO POR TRACKPAD
  //###################################################################################

  function setupTrackpadTabNavigationV1(container, options, getState, triggerSelect) {
    var swipeThresholdPx = Number.isFinite(Number(options.swipeThresholdPx))
      ? Number(options.swipeThresholdPx)
      : 48;
    var swipeCooldownMs = Number.isFinite(Number(options.swipeCooldownMs))
      ? Number(options.swipeCooldownMs)
      : 500;
    var invertSwipe = options.invertSwipe === true;
    var lastNavigationAt = 0;

    var doc = container.ownerDocument || document;

    function isBlockedByOverlay() {
      if (doc.querySelector(".appverbo-confirm-overlay-v1")) {
        return true;
      }
      if (doc.querySelector(".appverbo-row-actions-popup-floating-v1")) {
        return true;
      }
      return false;
    }

    function isInteractiveEl(el) {
      if (!el) {
        return false;
      }
      var tag = (el.tagName || "").toLowerCase();
      if (tag === "input" || tag === "select" || tag === "textarea") {
        return true;
      }
      if (el.isContentEditable) {
        return true;
      }
      return false;
    }

    function handleWheel(event) {
      // Only pixel-mode — trackpad on macOS always uses pixel mode
      if (event.deltaMode !== 0) {
        return;
      }

      var dx = event.deltaX;
      var horizontal = Math.abs(dx);
      var vertical = Math.abs(event.deltaY);

      // Too small — could be accidental drift
      if (horizontal < swipeThresholdPx) {
        return;
      }

      // Vertical-dominant — let the page scroll normally
      if (vertical > horizontal * 0.65) {
        return;
      }

      // Gesture is clearly horizontal.
      // Call preventDefault() NOW — before any guard — to block browser back/forward navigation.
      event.preventDefault();

      // Guard: interactive element under cursor or focused
      if (isInteractiveEl(event.target)) {
        return;
      }
      if (isInteractiveEl(doc.activeElement)) {
        return;
      }

      // Guard: blocking overlay (confirm dialog or actions popup)
      if (isBlockedByOverlay()) {
        return;
      }

      // Guard: cooldown — one navigation per gesture
      var now = Date.now();
      if (now - lastNavigationAt < swipeCooldownMs) {
        return;
      }

      var currentState = getState();
      var items = currentState.items || [];
      var activeLinkEl = currentState.activeLinkEl;

      if (!items.length || !activeLinkEl) {
        return;
      }

      var activeIndex = parseInt(String(activeLinkEl.dataset.submenuIndex || "-1"), 10);
      if (!Number.isFinite(activeIndex) || activeIndex < 0) {
        return;
      }

      // dx > 0: fingers moved left → go to next tab (right direction in bar)
      // dx < 0: fingers moved right → go to previous tab (left direction in bar)
      var rawDirection = dx > 0 ? 1 : -1;
      var direction = invertSwipe ? -rawDirection : rawDirection;
      var nextIndex = activeIndex + direction;

      if (nextIndex < 0 || nextIndex >= items.length) {
        return;
      }

      lastNavigationAt = now;
      triggerSelect(nextIndex, event);
    }

    // Listen on document with capture:true so the event is intercepted before
    // the browser can act on it (history navigation) and before any inner handler
    doc.addEventListener("wheel", handleWheel, { passive: false, capture: true });

    return function destroySwipe() {
      doc.removeEventListener("wheel", handleWheel, { capture: true });
    };
  }

  //###################################################################################
  // (3) CRIAR CONTROLLER REUTILIZAVEL
  //###################################################################################

  function createTopSubmenuController(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const container = safeConfig.container || null;
    const formatLabel = typeof safeConfig.formatLabel === "function"
      ? safeConfig.formatLabel
      : (value) => String(value || "");
    const onSelect = typeof safeConfig.onSelect === "function" ? safeConfig.onSelect : null;
    const enableTrackpadSwipe = safeConfig.enableTrackpadSwipe !== false;
    const swipeThresholdPx = Number.isFinite(Number(safeConfig.swipeThresholdPx))
      ? Number(safeConfig.swipeThresholdPx)
      : 48;
    const swipeCooldownMs = Number.isFinite(Number(safeConfig.swipeCooldownMs))
      ? Number(safeConfig.swipeCooldownMs)
      : 500;
    const invertTrackpadSwipe = safeConfig.invertTrackpadSwipe === true;

    if (!container || typeof container.addEventListener !== "function") {
      return {
        render() {},
        setActive() {},
        clear() {},
        destroy() {}
      };
    }

    const state = {
      signature: "",
      items: [],
      activeLinkEl: null,
      linksByTarget: new Map(),
      linksByProfileSection: new Map(),
      linksByDynamicProcessSection: new Map(),
      linksByLookupKey: new Map(),
      isDestroyed: false
    };

    function clearLookupMaps() {
      state.linksByTarget.clear();
      state.linksByProfileSection.clear();
      state.linksByDynamicProcessSection.clear();
      state.linksByLookupKey.clear();
    }

    function setLinkAsActive(nextLinkEl) {
      if (state.activeLinkEl && state.activeLinkEl !== nextLinkEl) {
        state.activeLinkEl.classList.remove("active");
      }

      state.activeLinkEl = nextLinkEl || null;

      if (state.activeLinkEl) {
        state.activeLinkEl.classList.add("active");
      }
    }

    function rememberLink(item, linkEl, selectionDataset) {
      const cleanTargetSelector = String(item && item.target || "").trim();

      if (!state.linksByTarget.has(cleanTargetSelector)) {
        state.linksByTarget.set(cleanTargetSelector, []);
      }
      state.linksByTarget.get(cleanTargetSelector).push(linkEl);

      if (selectionDataset.profileSection) {
        state.linksByProfileSection.set(String(selectionDataset.profileSection || "").trim(), linkEl);
      }

      if (selectionDataset.dynamicProcessSectionKey) {
        state.linksByDynamicProcessSection.set(
          String(selectionDataset.dynamicProcessSectionKey || "").trim(),
          linkEl
        );
      }

      state.linksByLookupKey.set(
        buildLookupKey_v1(cleanTargetSelector, selectionDataset),
        linkEl
      );
    }

    function setDatasetAttributes(linkEl, selectionDataset) {
      Object.keys(selectionDataset).forEach((datasetKey) => {
        const cleanValue = String(selectionDataset[datasetKey] || "").trim();

        if (!cleanValue) {
          return;
        }

        if (datasetKey === "dynamicProcessSectionKey") {
          linkEl.dataset.dynamicProcessSection = cleanValue;
          return;
        }

        linkEl.dataset[datasetKey] = cleanValue;
      });
    }

    function findLinkByTargetAndDataset(targetSelector, selectedReference) {
      if (selectedReference && selectedReference.nodeType === 1) {
        return selectedReference;
      }

      const normalizedSelectionDataset = normalizeDatasetObject_v1(selectedReference);

      if (normalizedSelectionDataset.profileSection) {
        return state.linksByProfileSection.get(
          String(normalizedSelectionDataset.profileSection || "").trim()
        ) || null;
      }

      if (normalizedSelectionDataset.dynamicProcessSectionKey) {
        return state.linksByDynamicProcessSection.get(
          String(normalizedSelectionDataset.dynamicProcessSectionKey || "").trim()
        ) || null;
      }

      const exactLookupMatch = state.linksByLookupKey.get(
        buildLookupKey_v1(targetSelector, normalizedSelectionDataset)
      );
      if (exactLookupMatch) {
        return exactLookupMatch;
      }

      const targetLinks = state.linksByTarget.get(String(targetSelector || "").trim()) || [];
      return targetLinks[0] || null;
    }

    function handleContainerClick(event) {
      if (state.isDestroyed) {
        return;
      }

      const linkEl = event.target.closest(".submenu-item");
      if (!linkEl || !container.contains(linkEl)) {
        return;
      }

      event.preventDefault();

      const itemIndex = Number.parseInt(String(linkEl.dataset.submenuIndex || "").trim(), 10);
      const item = Number.isFinite(itemIndex) ? state.items[itemIndex] : null;

      if (!item) {
        return;
      }

      setLinkAsActive(linkEl);

      if (onSelect) {
        onSelect({
          event,
          item,
          linkEl,
          selectedDataset: buildLinkSelectionDataset_v1(linkEl)
        });
      }
    }

    container.addEventListener("click", handleContainerClick);

    function activateIndexForSwipeV1(nextIndex) {
      const links = Array.from(container.querySelectorAll(".submenu-item"));
      if (!links.length || nextIndex < 0 || nextIndex >= links.length) {
        return false;
      }
      const nextLink = links[nextIndex];
      if (!nextLink) {
        return false;
      }

      // Visual update immediately so there is no stale active state
      setLinkAsActive(nextLink);

      // Dispatch a synthetic click so handleContainerClick runs the exact same
      // path as a real user click, including event.preventDefault() on the <a>
      // and the full onSelect callback with a real event object.
      nextLink.dispatchEvent(
        new MouseEvent("click", { bubbles: true, cancelable: true, view: global })
      );

      // Reinforce after onSelect in case render() re-ran and cleared activeLinkEl
      if (typeof global.requestAnimationFrame === "function") {
        global.requestAnimationFrame(function () {
          if (!state.isDestroyed && container.contains(nextLink)) {
            setLinkAsActive(nextLink);
          }
        });
      }

      return true;
    }

    var destroySwipe = null;
    if (enableTrackpadSwipe) {
      destroySwipe = setupTrackpadTabNavigationV1(
        container,
        { swipeThresholdPx: swipeThresholdPx, swipeCooldownMs: swipeCooldownMs, invertSwipe: invertTrackpadSwipe },
        function getState() { return state; },
        function triggerSelect(nextIndex) {
          activateIndexForSwipeV1(nextIndex);
        }
      );
    }

    function render(items, options) {
      if (state.isDestroyed) {
        return;
      }

      const safeItems = Array.isArray(items) ? items.filter(Boolean) : [];
      const safeOptions = options && typeof options === "object" ? options : {};
      const nextSignature = buildRenderSignature_v1(safeItems);

      container.style.display = "flex";

      if (!safeOptions.force && nextSignature === state.signature) {
        if (safeOptions.activeTarget || safeOptions.activeDataset) {
          setActive(safeOptions.activeTarget || "", safeOptions.activeDataset || null);
        }
        return;
      }

      state.signature = nextSignature;
      state.items = safeItems;
      state.activeLinkEl = null;
      clearLookupMaps();

      const fragment = document.createDocumentFragment();

      safeItems.forEach((item, index) => {
        const linkEl = document.createElement("a");
        const selectionDataset = buildSelectionDataset_v1(item);

        linkEl.className = "submenu-item";
        linkEl.href = String(item.target || "").trim();
        linkEl.textContent = formatLabel(item.label);
        linkEl.dataset.submenuIndex = String(index);

        setDatasetAttributes(linkEl, selectionDataset);
        rememberLink(item, linkEl, selectionDataset);
        fragment.appendChild(linkEl);
      });

      if (typeof container.replaceChildren === "function") {
        container.replaceChildren(fragment);
      } else {
        container.innerHTML = "";
        container.appendChild(fragment);
      }

      if (safeOptions.activeTarget || safeOptions.activeDataset) {
        setActive(safeOptions.activeTarget || "", safeOptions.activeDataset || null);
      }
    }

    function setActive(targetSelector, selectedReference) {
      if (state.isDestroyed) {
        return;
      }

      const nextLinkEl = findLinkByTargetAndDataset(targetSelector, selectedReference);
      setLinkAsActive(nextLinkEl);
    }

    function clear() {
      if (state.isDestroyed) {
        return;
      }

      state.signature = "";
      state.items = [];
      setLinkAsActive(null);
      clearLookupMaps();
      container.innerHTML = "";
    }

    function destroy() {
      if (state.isDestroyed) {
        return;
      }

      container.removeEventListener("click", handleContainerClick);
      if (destroySwipe) {
        destroySwipe();
        destroySwipe = null;
      }
      clear();
      state.isDestroyed = true;
    }

    return {
      render,
      setActive,
      clear,
      destroy
    };
  }


  //###################################################################################
  // (4) EXPOR API GLOBAL SEGURA
  //###################################################################################

  global.AppVerboTopSubmenu = {
    ...(global.AppVerboTopSubmenu || {}),
    createTopSubmenuController
  };
})(window);
