//###################################################################################
// (1) PROCESS SUBMENU RUNTIME
//###################################################################################
(function initAppGenesisProcessSubmenuRuntimeV1(global) {
  const existingRuntime =
    global.AppGenesisProcessSubmenuRuntimeV1 &&
    typeof global.AppGenesisProcessSubmenuRuntimeV1 === "object"
      ? global.AppGenesisProcessSubmenuRuntimeV1
      : null;

  if (existingRuntime) {
    return;
  }

  const state = {
    itemsEl: null,
    topSubmenuController: null,
    menuConfig: {},
    selectedTargetByMenu: {},
    selectedDynamicSectionByMenu: {},
    normalizeMenuKey: function (value) {
      return String(value || "").trim().toLowerCase();
    },
    normalizeSubmenuTargetAlias: function (value) {
      return String(value || "").trim();
    },
    formatLabel: function (value) {
      return String(value || "").trim();
    },
    closeAllProfileEdits: function () {},
    applyContentForMenuTarget: function () {},
    renderDynamicProcessCard: function () {},
    getAdminSubprocessKeyByTarget: function () {
      return "";
    },
    debugTabsLog: function () {},
    logNavigationBootDebug: function () {},
    getActiveMenuKey: function () {
      return "";
    },
    setMeuPerfilSelectedProfileSection: function () {},
    activateProfilePersonalSection: function () {},
    applyMeuPerfilProcessSubsequentVisibility: function () {},
    syncActiveTabTitle: function () {},
    refreshProcessShellBreadcrumb: function () {},
    MEU_PERFIL_MENU_KEY: "meu_perfil",
    windowRef: global,
    documentRef: global.document || null
  };

  function configure(options) {
    const safeOptions = options && typeof options === "object" ? options : {};

    if ("itemsEl" in safeOptions) {
      state.itemsEl = safeOptions.itemsEl;
    }
    if ("topSubmenuController" in safeOptions) {
      state.topSubmenuController = safeOptions.topSubmenuController;
    }
    if (safeOptions.menuConfig && typeof safeOptions.menuConfig === "object") {
      state.menuConfig = safeOptions.menuConfig;
    }
    if (
      safeOptions.selectedTargetByMenu &&
      typeof safeOptions.selectedTargetByMenu === "object"
    ) {
      state.selectedTargetByMenu = safeOptions.selectedTargetByMenu;
    }
    if (
      safeOptions.selectedDynamicSectionByMenu &&
      typeof safeOptions.selectedDynamicSectionByMenu === "object"
    ) {
      state.selectedDynamicSectionByMenu = safeOptions.selectedDynamicSectionByMenu;
    }
    if (typeof safeOptions.normalizeMenuKey === "function") {
      state.normalizeMenuKey = safeOptions.normalizeMenuKey;
    }
    if (typeof safeOptions.normalizeSubmenuTargetAlias === "function") {
      state.normalizeSubmenuTargetAlias = safeOptions.normalizeSubmenuTargetAlias;
    }
    if (typeof safeOptions.formatLabel === "function") {
      state.formatLabel = safeOptions.formatLabel;
    }
    if (typeof safeOptions.closeAllProfileEdits === "function") {
      state.closeAllProfileEdits = safeOptions.closeAllProfileEdits;
    }
    if (typeof safeOptions.applyContentForMenuTarget === "function") {
      state.applyContentForMenuTarget = safeOptions.applyContentForMenuTarget;
    }
    if (typeof safeOptions.renderDynamicProcessCard === "function") {
      state.renderDynamicProcessCard = safeOptions.renderDynamicProcessCard;
    }
    if (typeof safeOptions.getAdminSubprocessKeyByTarget === "function") {
      state.getAdminSubprocessKeyByTarget = safeOptions.getAdminSubprocessKeyByTarget;
    }
    if (typeof safeOptions.debugTabsLog === "function") {
      state.debugTabsLog = safeOptions.debugTabsLog;
    }
    if (typeof safeOptions.logNavigationBootDebug === "function") {
      state.logNavigationBootDebug = safeOptions.logNavigationBootDebug;
    }
    if (typeof safeOptions.getActiveMenuKey === "function") {
      state.getActiveMenuKey = safeOptions.getActiveMenuKey;
    }
    if (typeof safeOptions.setMeuPerfilSelectedProfileSection === "function") {
      state.setMeuPerfilSelectedProfileSection = safeOptions.setMeuPerfilSelectedProfileSection;
    }
    if (typeof safeOptions.activateProfilePersonalSection === "function") {
      state.activateProfilePersonalSection = safeOptions.activateProfilePersonalSection;
    }
    if (typeof safeOptions.applyMeuPerfilProcessSubsequentVisibility === "function") {
      state.applyMeuPerfilProcessSubsequentVisibility = safeOptions.applyMeuPerfilProcessSubsequentVisibility;
    }
    if (typeof safeOptions.syncActiveTabTitle === "function") {
      state.syncActiveTabTitle = safeOptions.syncActiveTabTitle;
    }
    if (typeof safeOptions.refreshProcessShellBreadcrumb === "function") {
      state.refreshProcessShellBreadcrumb = safeOptions.refreshProcessShellBreadcrumb;
    }
    if (typeof safeOptions.MEU_PERFIL_MENU_KEY === "string" && safeOptions.MEU_PERFIL_MENU_KEY.trim()) {
      state.MEU_PERFIL_MENU_KEY = safeOptions.MEU_PERFIL_MENU_KEY.trim();
    }
    if (safeOptions.windowRef) {
      state.windowRef = safeOptions.windowRef;
    }
    if (safeOptions.documentRef) {
      state.documentRef = safeOptions.documentRef;
    }
  }

  function normalizeTopSubmenuSelectionData_v1(selectedReference) {
    if (!selectedReference) {
      return null;
    }

    if (selectedReference.nodeType === 1 && selectedReference.dataset) {
      const selectedDataset = {};

      if (selectedReference.dataset.profileSection) {
        selectedDataset.profileSection = String(selectedReference.dataset.profileSection || "");
      }

      if (selectedReference.dataset.dynamicProcessSection) {
        selectedDataset.dynamicProcessSectionKey = String(
          selectedReference.dataset.dynamicProcessSection || ""
        );
      }

      return selectedDataset;
    }

    if (typeof selectedReference !== "object" || Array.isArray(selectedReference)) {
      return null;
    }

    const selectedDataset = {};

    if (selectedReference.profileSection) {
      selectedDataset.profileSection = String(selectedReference.profileSection || "");
    }

    if (selectedReference.dynamicProcessSectionKey || selectedReference.dynamicProcessSection) {
      selectedDataset.dynamicProcessSectionKey = String(
        selectedReference.dynamicProcessSectionKey ||
        selectedReference.dynamicProcessSection ||
        ""
      );
    }

    return Object.keys(selectedDataset).length ? selectedDataset : null;
  }

  function clearSubmenuActiveLinks(links) {
    Array.from(links || []).forEach((link) => {
      link.classList.remove("active");
    });
  }

  function setActiveSubmenu(targetSelector, selectedLinkEl) {
    state.debugTabsLog("setActiveSubmenu", { targetSelector });
    if (!state.itemsEl) {
      return;
    }
    const normalizedTargetSelector = state.normalizeSubmenuTargetAlias(targetSelector);
    if (state.topSubmenuController) {
      state.topSubmenuController.setActive(
        normalizedTargetSelector,
        normalizeTopSubmenuSelectionData_v1(selectedLinkEl) || selectedLinkEl || null
      );
      return;
    }
    const links = state.itemsEl.querySelectorAll(".submenu-item");
    clearSubmenuActiveLinks(links);
    if (selectedLinkEl) {
      selectedLinkEl.classList.add("active");
      state.refreshProcessShellBreadcrumb({
        menuKey: state.getActiveMenuKey(),
        target: normalizedTargetSelector,
        source: "submenu"
      });
      return;
    }
    const firstMatch = Array.from(links).find(
      (link) => link.getAttribute("href") === normalizedTargetSelector
    );
    if (firstMatch) {
      firstMatch.classList.add("active");
    }
    state.refreshProcessShellBreadcrumb({
      menuKey: state.getActiveMenuKey(),
      target: normalizedTargetSelector,
      source: "submenu"
    });
  }

  function createTopSubmenuController(options) {
    const safeOptions = options && typeof options === "object" ? options : {};
    const container = safeOptions.container || null;
    const windowRef = safeOptions.windowRef || state.windowRef || global;
    const topSubmenuApi = windowRef.AppGenesisTopSubmenu || global.AppGenesisTopSubmenu;
    if (!container || !topSubmenuApi || typeof topSubmenuApi.createTopSubmenuController !== "function") {
      return null;
    }

    const formatLabel = typeof safeOptions.formatLabel === "function"
      ? safeOptions.formatLabel
      : state.formatLabel;
    const normalizeMenuKey = typeof safeOptions.normalizeMenuKey === "function"
      ? safeOptions.normalizeMenuKey
      : state.normalizeMenuKey;
    const getActiveMenuKey = typeof safeOptions.getActiveMenuKey === "function"
      ? safeOptions.getActiveMenuKey
      : state.getActiveMenuKey;
    const closeAllProfileEdits = typeof safeOptions.closeAllProfileEdits === "function"
      ? safeOptions.closeAllProfileEdits
      : state.closeAllProfileEdits;
    const setActiveSubmenuCallback = typeof safeOptions.setActiveSubmenu === "function"
      ? safeOptions.setActiveSubmenu
      : setActiveSubmenu;
    const applyContentForMenuTarget = typeof safeOptions.applyContentForMenuTarget === "function"
      ? safeOptions.applyContentForMenuTarget
      : state.applyContentForMenuTarget;
    const getAdminSubprocessKeyByTarget = typeof safeOptions.getAdminSubprocessKeyByTarget === "function"
      ? safeOptions.getAdminSubprocessKeyByTarget
      : state.getAdminSubprocessKeyByTarget;
    const renderDynamicProcessCard = typeof safeOptions.renderDynamicProcessCard === "function"
      ? safeOptions.renderDynamicProcessCard
      : state.renderDynamicProcessCard;
    const debugTabsLog = typeof safeOptions.debugTabsLog === "function"
      ? safeOptions.debugTabsLog
      : state.debugTabsLog;
    const logNavigationBootDebug = typeof safeOptions.logNavigationBootDebug === "function"
      ? safeOptions.logNavigationBootDebug
      : state.logNavigationBootDebug;
    const selectedTargetByMenu = (
      safeOptions.selectedTargetByMenu &&
      typeof safeOptions.selectedTargetByMenu === "object"
    )
      ? safeOptions.selectedTargetByMenu
      : state.selectedTargetByMenu;
    const selectedDynamicSectionByMenu = (
      safeOptions.selectedDynamicSectionByMenu &&
      typeof safeOptions.selectedDynamicSectionByMenu === "object"
    )
      ? safeOptions.selectedDynamicSectionByMenu
      : state.selectedDynamicSectionByMenu;
    const setMeuPerfilSelectedProfileSection =
      typeof safeOptions.setMeuPerfilSelectedProfileSection === "function"
        ? safeOptions.setMeuPerfilSelectedProfileSection
        : state.setMeuPerfilSelectedProfileSection;
    const activateProfilePersonalSection =
      typeof safeOptions.activateProfilePersonalSection === "function"
        ? safeOptions.activateProfilePersonalSection
        : state.activateProfilePersonalSection;
    const applyMeuPerfilProcessSubsequentVisibility =
      typeof safeOptions.applyMeuPerfilProcessSubsequentVisibility === "function"
        ? safeOptions.applyMeuPerfilProcessSubsequentVisibility
        : state.applyMeuPerfilProcessSubsequentVisibility;
    const syncActiveTabTitle = typeof safeOptions.syncActiveTabTitle === "function"
      ? safeOptions.syncActiveTabTitle
      : state.syncActiveTabTitle;
    const meuPerfilMenuKey = String(
      safeOptions.MEU_PERFIL_MENU_KEY || state.MEU_PERFIL_MENU_KEY || "meu_perfil"
    ).trim();
    const documentRef = safeOptions.documentRef || state.documentRef || global.document;

    return topSubmenuApi.createTopSubmenuController({
      container,
      formatLabel,
      enableTrackpadSwipe: true,
      onSelect: ({ item, linkEl }) => {
        const menuKey = normalizeMenuKey(getActiveMenuKey());
        if (!menuKey || !item) {
          return;
        }

        closeAllProfileEdits();
        selectedTargetByMenu[menuKey] = item.target;
        debugTabsLog("onSelect:before-apply", { menuKey, target: item.target });
        logNavigationBootDebug("submenu_tab_click:before", {
          menuKey,
          target: item.target,
          hrefBefore: windowRef.location.href
        });
        setActiveSubmenuCallback(item.target, linkEl);
        applyContentForMenuTarget(menuKey, item.target, "click:submenu-tab");

        if (
          menuKey === "administrativo" &&
          windowRef.history &&
          typeof windowRef.history.pushState === "function"
        ) {
          let adminTabParam = getAdminSubprocessKeyByTarget(item.target);
          if (!adminTabParam && item.target === "#dynamic-process-card" && item.dynamicProcessSectionKey) {
            adminTabParam = String(item.dynamicProcessSectionKey).trim().toLowerCase();
          }
          if (adminTabParam) {
            try {
              const nextUrl = new URL(windowRef.location.href);
              nextUrl.searchParams.set("menu", "administrativo");
              nextUrl.searchParams.set("admin_tab", adminTabParam);
              nextUrl.searchParams.delete("entity_edit_id");
              nextUrl.searchParams.delete("entity_view");
              nextUrl.searchParams.delete("user_edit_id");
              nextUrl.searchParams.delete("user_view");
              nextUrl.searchParams.delete("target");
              nextUrl.hash = "";
              const newPath = nextUrl.pathname + nextUrl.search;
              if (newPath !== windowRef.location.pathname + windowRef.location.search) {
                windowRef.history.pushState(
                  { menu: "administrativo", adminTab: adminTabParam, target: item.target },
                  documentRef ? documentRef.title : "",
                  newPath
                );
              }
            } catch (_) {}
          }
        }

        if (item.dynamicProcessSectionKey) {
          selectedDynamicSectionByMenu[menuKey] = String(item.dynamicProcessSectionKey);
          renderDynamicProcessCard(menuKey, item.dynamicProcessSectionKey);
        }

        if (
          menuKey === meuPerfilMenuKey &&
          typeof activateProfilePersonalSection === "function"
        ) {
          const sectionKey = String(item.profileSection || "");
          setMeuPerfilSelectedProfileSection(sectionKey);
          activateProfilePersonalSection(sectionKey);
          applyMeuPerfilProcessSubsequentVisibility();
          syncActiveTabTitle(
            "#submenu-items",
            "#perfil-pessoal-card .profile-card-header h2",
            ["Mais"]
          );
        }

        debugTabsLog("onSelect:after-apply", { menuKey, target: item.target });
        logNavigationBootDebug("submenu_tab_click:after", {
          menuKey,
          target: item.target,
          hrefAfter: windowRef.location.href
        });
      }
    });
  }

  function renderSubmenu(menuKey) {
    const config = state.menuConfig[menuKey];
    if (!config || !state.itemsEl) {
      return;
    }

    state.itemsEl.style.display = "flex";

    if (state.topSubmenuController) {
      state.topSubmenuController.render(Array.isArray(config.items) ? config.items : []);
      return;
    }

    state.itemsEl.innerHTML = "";

    config.items.forEach((item) => {
      const link = state.documentRef.createElement("a");
      link.className = "submenu-item";
      link.href = item.target;
      link.textContent = state.formatLabel(item.label);
      if (item.profileSection) {
        link.dataset.profileSection = String(item.profileSection);
      }
      if (item.dynamicProcessSectionKey) {
        link.dataset.dynamicProcessSection = String(item.dynamicProcessSectionKey);
      }
      link.addEventListener("click", (event) => {
        event.preventDefault();
        state.closeAllProfileEdits();
        state.selectedTargetByMenu[menuKey] = item.target;
        setActiveSubmenu(item.target, link);
        state.applyContentForMenuTarget(menuKey, item.target, "click:submenu-tab-fallback");
        if (item.dynamicProcessSectionKey) {
          state.selectedDynamicSectionByMenu[menuKey] = String(item.dynamicProcessSectionKey);
          state.renderDynamicProcessCard(menuKey, item.dynamicProcessSectionKey);
        }
        if (
          menuKey === state.MEU_PERFIL_MENU_KEY &&
          typeof state.activateProfilePersonalSection === "function"
        ) {
          const sectionKey = String(item.profileSection || "");
          state.setMeuPerfilSelectedProfileSection(sectionKey);
          state.activateProfilePersonalSection(sectionKey);
          state.applyMeuPerfilProcessSubsequentVisibility();
        }
      });
      state.itemsEl.appendChild(link);
    });
  }

  global.AppGenesisProcessSubmenuRuntimeV1 = Object.freeze({
    configure,
    createTopSubmenuController,
    clearSubmenuActiveLinks,
    setActiveSubmenu,
    renderSubmenu
  });
})(window);
