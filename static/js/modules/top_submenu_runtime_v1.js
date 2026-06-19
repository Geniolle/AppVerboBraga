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
  // (2) CRIAR CONTROLLER REUTILIZAVEL
  //###################################################################################

  function createTopSubmenuController(config) {
    const safeConfig = config && typeof config === "object" ? config : {};
    const container = safeConfig.container || null;
    const formatLabel = typeof safeConfig.formatLabel === "function"
      ? safeConfig.formatLabel
      : (value) => String(value || "");
    const onSelect = typeof safeConfig.onSelect === "function" ? safeConfig.onSelect : null;

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
  // (3) EXPOR API GLOBAL SEGURA
  //###################################################################################

  global.AppVerboTopSubmenu = {
    ...(global.AppVerboTopSubmenu || {}),
    createTopSubmenuController
  };
})(window);
