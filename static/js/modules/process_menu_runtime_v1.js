//###################################################################################
// (1) PROCESS MENU RUNTIME
//###################################################################################
(function initAppGenesisProcessMenuRuntimeV1(global) {
  const existingRuntime =
    global.AppGenesisProcessMenuRuntimeV1 &&
    typeof global.AppGenesisProcessMenuRuntimeV1 === "object"
      ? global.AppGenesisProcessMenuRuntimeV1
      : null;

  if (existingRuntime) {
    return;
  }

  const state = {
    menuConfig: {},
    menuButtons: [],
    selectedTargetByMenu: {},
    selectedDynamicSectionByMenu: {},
    normalizeMenuKey: function (value) {
      return String(value || "").trim().toLowerCase();
    },
    renderSubmenu: function () {},
    getDefaultTargetForMenu: function () {
      return "";
    },
    setActiveSubmenu: function () {},
    applyContentForMenuTarget: function () {},
    renderDynamicProcessCard: function () {},
    closeAllProfileEdits: function () {},
    syncActiveTabTitle: function () {},
    applyMeuPerfilProcessSubsequentVisibility: function () {},
    applyContentForMenu: function () {},
    getAdminSubprocessKeyByTarget: function () {
      return "";
    },
    getSidebarAdminSubprocessMenuKeyByTarget: function () {
      return "";
    },
    normalizeAuthorizationProfileTarget: function () {
      return "";
    },
    debugTabsLog: function () {},
    logNavigationBootDebug: function () {},
    processShellHeaderController: null,
    refreshProcessShellBreadcrumb: function () {},
    getMeuPerfilSelectedProfileSection: function () {
      return "";
    },
    setMeuPerfilSelectedProfileSection: function () {},
    activateProfilePersonalSection: function () {},
    setActiveMenuKey: function () {},
    getActiveMenuKey: function () {
      return "";
    },
    getMeuPerfilPersonalCardTarget: function () {
      return "#perfil-pessoal-card";
    },
    MEU_PERFIL_MENU_KEY: "meu_perfil",
    ESTRUTURAS_MENU_KEY_V1: "sessoes",
    windowRef: global
  };

  function configure(options) {
    const safeOptions = options && typeof options === "object" ? options : {};

    if (safeOptions.menuConfig && typeof safeOptions.menuConfig === "object") {
      state.menuConfig = safeOptions.menuConfig;
    }
    if (safeOptions.menuButtons) {
      state.menuButtons = safeOptions.menuButtons;
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
    if (typeof safeOptions.renderSubmenu === "function") {
      state.renderSubmenu = safeOptions.renderSubmenu;
    }
    if (typeof safeOptions.getDefaultTargetForMenu === "function") {
      state.getDefaultTargetForMenu = safeOptions.getDefaultTargetForMenu;
    }
    if (typeof safeOptions.setActiveSubmenu === "function") {
      state.setActiveSubmenu = safeOptions.setActiveSubmenu;
    }
    if (typeof safeOptions.applyContentForMenuTarget === "function") {
      state.applyContentForMenuTarget = safeOptions.applyContentForMenuTarget;
    }
    if (typeof safeOptions.renderDynamicProcessCard === "function") {
      state.renderDynamicProcessCard = safeOptions.renderDynamicProcessCard;
    }
    if (typeof safeOptions.closeAllProfileEdits === "function") {
      state.closeAllProfileEdits = safeOptions.closeAllProfileEdits;
    }
    if (typeof safeOptions.syncActiveTabTitle === "function") {
      state.syncActiveTabTitle = safeOptions.syncActiveTabTitle;
    }
    if (typeof safeOptions.applyMeuPerfilProcessSubsequentVisibility === "function") {
      state.applyMeuPerfilProcessSubsequentVisibility = safeOptions.applyMeuPerfilProcessSubsequentVisibility;
    }
    if (typeof safeOptions.applyContentForMenu === "function") {
      state.applyContentForMenu = safeOptions.applyContentForMenu;
    }
    if (typeof safeOptions.getAdminSubprocessKeyByTarget === "function") {
      state.getAdminSubprocessKeyByTarget = safeOptions.getAdminSubprocessKeyByTarget;
    }
    if (typeof safeOptions.getSidebarAdminSubprocessMenuKeyByTarget === "function") {
      state.getSidebarAdminSubprocessMenuKeyByTarget = safeOptions.getSidebarAdminSubprocessMenuKeyByTarget;
    }
    if (typeof safeOptions.normalizeAuthorizationProfileTarget === "function") {
      state.normalizeAuthorizationProfileTarget = safeOptions.normalizeAuthorizationProfileTarget;
    }
    if (typeof safeOptions.debugTabsLog === "function") {
      state.debugTabsLog = safeOptions.debugTabsLog;
    }
    if (typeof safeOptions.logNavigationBootDebug === "function") {
      state.logNavigationBootDebug = safeOptions.logNavigationBootDebug;
    }
    if ("processShellHeaderController" in safeOptions) {
      state.processShellHeaderController = safeOptions.processShellHeaderController;
    }
    if (typeof safeOptions.refreshProcessShellBreadcrumb === "function") {
      state.refreshProcessShellBreadcrumb = safeOptions.refreshProcessShellBreadcrumb;
    }
    if (typeof safeOptions.getMeuPerfilSelectedProfileSection === "function") {
      state.getMeuPerfilSelectedProfileSection = safeOptions.getMeuPerfilSelectedProfileSection;
    }
    if (typeof safeOptions.setMeuPerfilSelectedProfileSection === "function") {
      state.setMeuPerfilSelectedProfileSection = safeOptions.setMeuPerfilSelectedProfileSection;
    }
    if (typeof safeOptions.activateProfilePersonalSection === "function") {
      state.activateProfilePersonalSection = safeOptions.activateProfilePersonalSection;
    }
    if (typeof safeOptions.setActiveMenuKey === "function") {
      state.setActiveMenuKey = safeOptions.setActiveMenuKey;
    }
    if (typeof safeOptions.getActiveMenuKey === "function") {
      state.getActiveMenuKey = safeOptions.getActiveMenuKey;
    }
    if (typeof safeOptions.getMeuPerfilPersonalCardTarget === "function") {
      state.getMeuPerfilPersonalCardTarget = safeOptions.getMeuPerfilPersonalCardTarget;
    }
    if (typeof safeOptions.MEU_PERFIL_MENU_KEY === "string" && safeOptions.MEU_PERFIL_MENU_KEY.trim()) {
      state.MEU_PERFIL_MENU_KEY = safeOptions.MEU_PERFIL_MENU_KEY.trim();
    }
    if (
      typeof safeOptions.ESTRUTURAS_MENU_KEY_V1 === "string" &&
      safeOptions.ESTRUTURAS_MENU_KEY_V1.trim()
    ) {
      state.ESTRUTURAS_MENU_KEY_V1 = safeOptions.ESTRUTURAS_MENU_KEY_V1.trim();
    }
    if (safeOptions.windowRef) {
      state.windowRef = safeOptions.windowRef;
    }
  }

  function activateMenu(menuKey, options) {
    const safeOptions = options && typeof options === "object" ? options : {};
    state.debugTabsLog("activateMenu:start", { menuKey, options: safeOptions });
    const config = state.menuConfig[menuKey];
    if (!config) {
      return;
    }
    const resetDynamicToFirst = Boolean(safeOptions.resetDynamicToFirst);
    const source = String(safeOptions.source || "unspecified");
    const targetButton = Array.from(state.menuButtons || []).find(
      (btn) => state.normalizeMenuKey(btn.dataset.menu) === menuKey
    );
    const menuItems = Array.isArray(config.items) ? config.items : [];
    if (resetDynamicToFirst) {
      const firstDynamicItem = menuItems.find((item) => item.dynamicProcessSectionKey);
      if (firstDynamicItem) {
        state.selectedDynamicSectionByMenu[menuKey] = String(
          firstDynamicItem.dynamicProcessSectionKey || ""
        );
      }
    }

    state.closeAllProfileEdits();
    state.setActiveMenuKey(menuKey);
    if (state.processShellHeaderController) {
      state.processShellHeaderController.setActions([]);
      state.processShellHeaderController.setTitle(config.title || "Processo", menuKey);
    }
    Array.from(state.menuButtons || []).forEach((item) => item.classList.remove("active"));
    if (targetButton) {
      targetButton.classList.add("active");
    }
    state.renderSubmenu(menuKey);

    const defaultTarget = state.getDefaultTargetForMenu(
      menuKey,
      config,
      { forceFirstItem: resetDynamicToFirst }
    );
    if (defaultTarget) {
      const savedDynamicSectionKey = String(state.selectedDynamicSectionByMenu[menuKey] || "");
      let selectedDynamicItem = null;
      if (defaultTarget === "#dynamic-process-card") {
        selectedDynamicItem = menuItems.find(
          (item) => String(item.dynamicProcessSectionKey || "") === savedDynamicSectionKey
        );
        if (!selectedDynamicItem) {
          selectedDynamicItem = menuItems.find((item) => item.target === "#dynamic-process-card") || null;
        }
      }

      state.selectedTargetByMenu[menuKey] = defaultTarget;
      if (selectedDynamicItem) {
        const selectedSectionKey = String(selectedDynamicItem.dynamicProcessSectionKey || "");
        state.setActiveSubmenu(defaultTarget, {
          dynamicProcessSectionKey: selectedSectionKey
        });
        state.selectedDynamicSectionByMenu[menuKey] = selectedSectionKey;
        state.renderDynamicProcessCard(menuKey, selectedSectionKey);
      } else {
        state.setActiveSubmenu(defaultTarget);
      }
      state.debugTabsLog("activateMenu:before-apply", { menuKey, defaultTarget });
      state.applyContentForMenuTarget(menuKey, defaultTarget, source);
      state.refreshProcessShellBreadcrumb({ menuKey, target: defaultTarget, source });
      if (menuKey === state.MEU_PERFIL_MENU_KEY) {
        let selectedSectionItem = menuItems.find(
          (item) => String(item.profileSection || "") === state.getMeuPerfilSelectedProfileSection()
        );
        if (!selectedSectionItem) {
          selectedSectionItem = menuItems.find((item) => item.target === defaultTarget) || menuItems[0];
        }
        if (selectedSectionItem) {
          const selectedSectionKey = String(selectedSectionItem.profileSection || "");
          state.setMeuPerfilSelectedProfileSection(selectedSectionKey);
          state.activateProfilePersonalSection(selectedSectionKey);
          state.applyMeuPerfilProcessSubsequentVisibility();
          state.setActiveSubmenu(defaultTarget, {
            profileSection: selectedSectionKey
          });
          state.syncActiveTabTitle(
            "#submenu-items",
            `${state.getMeuPerfilPersonalCardTarget()} .profile-card-header h2`,
            ["Mais"]
          );
        }
      }
      return;
    }
    state.applyContentForMenu(menuKey);
    state.setActiveSubmenu("");
    state.refreshProcessShellBreadcrumb({ menuKey, target: "", source });
  }

  function activateMenuTarget(menuKey, targetSelector, source) {
    const cleanSource = String(source || "unspecified");
    const config = state.menuConfig[menuKey];
    if (!config) {
      return;
    }
    activateMenu(menuKey, { resetDynamicToFirst: false, source: cleanSource });
    if (!targetSelector) {
      return;
    }
    state.selectedTargetByMenu[menuKey] = targetSelector;
    state.setActiveSubmenu(targetSelector);
    state.applyContentForMenuTarget(menuKey, targetSelector, cleanSource);
    state.refreshProcessShellBreadcrumb({ menuKey, target: targetSelector, source: cleanSource });
    if (targetSelector === "#dynamic-process-card") {
      state.renderDynamicProcessCard(menuKey, state.selectedDynamicSectionByMenu[menuKey] || "");
    }
    const targetCard = state.windowRef.document.querySelector(targetSelector);
    if (targetCard) {
      targetCard.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function handleHashNavigation(rawHash) {
    const cleanHash = String(rawHash || "").trim();
    if (!cleanHash) {
      return;
    }
    let normalizedHash = cleanHash;
    if (normalizedHash === "#edit-user-card") {
      normalizedHash = "#create-user-card";
    } else if (normalizedHash === "#edit-entity-card") {
      normalizedHash = "#recent-entities-card";
    } else if (normalizedHash === "#configuracao-account-status-card") {
      normalizedHash = "#admin-account-status-card";
    }

    if (state.normalizeAuthorizationProfileTarget(normalizedHash)) {
      activateMenuTarget("perfil_de_autorizacao", normalizedHash);
      return;
    }

    const hashTargetMenuMap = {
      "#create-user-card": "administrativo",
      "#admin-users-created-card": "administrativo",
      "#inactive-users-card": "administrativo",
      "#create-entity-card": "administrativo",
      "#recent-entities-card": "administrativo",
      "#inactive-entities-card": "administrativo",
      "#admin-account-status-card": state.ESTRUTURAS_MENU_KEY_V1,
      "#admin-sidebar-sections-card": state.ESTRUTURAS_MENU_KEY_V1,
      "#admin-sidebar-sections-form-card": state.ESTRUTURAS_MENU_KEY_V1,
      "#admin-account-create-card": state.ESTRUTURAS_MENU_KEY_V1,
      "#settings-menu-edit-card": state.ESTRUTURAS_MENU_KEY_V1
    };
    const targetMenu = hashTargetMenuMap[normalizedHash];
    if (targetMenu) {
      activateMenuTarget(targetMenu, normalizedHash);
      return;
    }
    const sidebarAdminTargetMenu = state.getSidebarAdminSubprocessMenuKeyByTarget(normalizedHash);
    if (sidebarAdminTargetMenu) {
      activateMenuTarget(sidebarAdminTargetMenu, normalizedHash);
    }
  }

  function bindMenuButtonListeners() {
    Array.from(state.menuButtons || []).forEach((btn) => {
      if (btn.getAttribute("data-appgenesis-menu-runtime-bound") === "1") {
        return;
      }
      btn.setAttribute("data-appgenesis-menu-runtime-bound", "1");
      btn.addEventListener("click", () => {
        const clickedMenuKey = state.normalizeMenuKey(btn.dataset.menu);
        state.logNavigationBootDebug("sidebar_click:before", {
          clickedMenuKey,
          hrefBefore: state.windowRef.location.href,
          activeMenuKeyBefore: state.getActiveMenuKey()
        });
        activateMenu(clickedMenuKey, {
          resetDynamicToFirst: true,
          source: "click:sidebar"
        });
        state.logNavigationBootDebug("sidebar_click:after", {
          clickedMenuKey,
          hrefAfter: state.windowRef.location.href,
          activeMenuKeyAfter: state.getActiveMenuKey()
        });
      });
    });
  }

  function bindHashChangeListener() {
    const windowRef = state.windowRef || global;
    if (windowRef.__appGenesisMenuRuntimeHashBoundV1) {
      return;
    }
    windowRef.__appGenesisMenuRuntimeHashBoundV1 = true;
    windowRef.addEventListener("hashchange", () => {
      handleHashNavigation(windowRef.location.hash || "");
    });
  }

  global.AppGenesisProcessMenuRuntimeV1 = Object.freeze({
    configure,
    activateMenu,
    activateMenuTarget,
    handleHashNavigation,
    bindMenuButtonListeners,
    bindHashChangeListener
  });
})(window);
