// APPVERBO_MENU_NAVIGATION_BRIDGE_V1_MODULE_START
(function registerMenuNavigationBridgeV1Module() {
  "use strict";

  window.APPVERBO_CREATE_MENU_NAVIGATION_BRIDGE_API_V1 = function createMenuNavigationBridgeApiV1() {
    let facadeCache = null;

    //###################################################################################
    // (1) FACADE RESOLUTION
    //###################################################################################
    function getMenuNavigationFacade(context = {}) {
      if (facadeCache) {
        return facadeCache;
      }
      if (typeof window.APPVERBO_CREATE_MENU_NAVIGATION_FACADE_V1 !== "function") {
        return null;
      }
      facadeCache = window.APPVERBO_CREATE_MENU_NAVIGATION_FACADE_V1({
        menuConfig: context.menuConfig,
        itemsEl: context.itemsEl,
        menuTabsCardEl: context.menuTabsCardEl,
        menuButtons: context.menuButtons,
        MEU_PERFIL_MENU_KEY: context.MEU_PERFIL_MENU_KEY,
        toSentenceCaseText: context.toSentenceCaseText,
        normalizeMenuKey: context.normalizeMenuKey,
        closeAllProfileEdits: context.closeAllProfileEdits,
        setActiveSubmenu: context.setActiveSubmenu,
        applyContentForMenuTarget: context.applyContentForMenuTarget,
        applyContentForMenu: context.applyContentForMenu,
        renderDynamicProcessCard: context.renderDynamicProcessCard,
        updateSubmenuProcessTitle: context.updateSubmenuProcessTitle,
        applyMeuPerfilProcessSubsequentVisibility: context.applyMeuPerfilProcessSubsequentVisibility,
        selectedTargetByMenu: context.selectedTargetByMenu,
        selectedDynamicSectionByMenu: context.selectedDynamicSectionByMenu,
        setActiveMenuKey: context.setActiveMenuKey,
        getMeuPerfilSelectedProfileSection: context.getMeuPerfilSelectedProfileSection,
        setMeuPerfilSelectedProfileSection: context.setMeuPerfilSelectedProfileSection
      });
      return facadeCache;
    }

    //###################################################################################
    // (2) NAVIGATION BRIDGES
    //###################################################################################
    function getMenuNavigationController(context = {}) {
      const facade = getMenuNavigationFacade(context);
      if (!facade || typeof facade.getController !== "function") {
        return null;
      }
      return facade.getController();
    }

    function renderSubmenu(menuKey, context = {}) {
      const facade = getMenuNavigationFacade(context);
      if (!facade || typeof facade.renderSubmenu !== "function") {
        return;
      }
      facade.renderSubmenu(menuKey);
    }

    function getDefaultTargetForMenu(menuKey, config, options = {}, context = {}) {
      const facade = getMenuNavigationFacade(context);
      if (!facade || typeof facade.getDefaultTargetForMenu !== "function") {
        return "";
      }
      return facade.getDefaultTargetForMenu(menuKey, config, options);
    }

    function activateMenu(menuKey, options = {}, context = {}) {
      const facade = getMenuNavigationFacade(context);
      if (!facade || typeof facade.activateMenu !== "function") {
        return;
      }
      facade.activateMenu(menuKey, options);
    }

    function activateMenuTarget(menuKey, targetSelector, options = {}, context = {}) {
      const facade = getMenuNavigationFacade(context);
      if (!facade || typeof facade.activateMenuTarget !== "function") {
        return;
      }
      facade.activateMenuTarget(menuKey, targetSelector, options);
    }

    function handleHashNavigation(rawHash, context = {}) {
      const facade = getMenuNavigationFacade(context);
      if (!facade || typeof facade.handleHashNavigation !== "function") {
        return;
      }
      facade.handleHashNavigation(rawHash);
    }

    return {
      getMenuNavigationFacade,
      getMenuNavigationController,
      renderSubmenu,
      getDefaultTargetForMenu,
      activateMenu,
      activateMenuTarget,
      handleHashNavigation
    };
  };
})();
// APPVERBO_MENU_NAVIGATION_BRIDGE_V1_MODULE_END
