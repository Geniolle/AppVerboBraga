//###################################################################################
// (1) MENU NAVIGATION FACADE V1
//###################################################################################
(function registerMenuNavigationFacadeV1() {
  "use strict";

  function createMenuNavigationFacadeV1(context = {}) {
    let controller = null;

    function getController() {
      if (controller) {
        return controller;
      }
      if (typeof window.APPVERBO_CREATE_MENU_NAVIGATION_CONTROLLER_V1 !== "function") {
        return null;
      }
      controller = window.APPVERBO_CREATE_MENU_NAVIGATION_CONTROLLER_V1({
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
        applyMeuPerfilProcessSubsequentVisibility: context.applyMeuPerfilProcessSubsequentVisibility,
        selectedTargetByMenu: context.selectedTargetByMenu,
        selectedDynamicSectionByMenu: context.selectedDynamicSectionByMenu,
        setActiveMenuKey: context.setActiveMenuKey,
        getMeuPerfilSelectedProfileSection: context.getMeuPerfilSelectedProfileSection,
        setMeuPerfilSelectedProfileSection: context.setMeuPerfilSelectedProfileSection
      });
      return controller;
    }

    function renderSubmenu(menuKey) {
      const resolvedController = getController();
      if (!resolvedController) {
        return;
      }
      resolvedController.renderSubmenu(menuKey);
    }

    function getDefaultTargetForMenu(menuKey, config, options = {}) {
      const resolvedController = getController();
      if (!resolvedController) {
        return "";
      }
      return resolvedController.getDefaultTargetForMenu(menuKey, config, options);
    }

    function activateMenu(menuKey, options = {}) {
      const resolvedController = getController();
      if (!resolvedController) {
        return;
      }
      resolvedController.activateMenu(menuKey, options);
    }

    function activateMenuTarget(menuKey, targetSelector) {
      const resolvedController = getController();
      if (!resolvedController) {
        return;
      }
      resolvedController.activateMenuTarget(menuKey, targetSelector);
    }

    function handleHashNavigation(rawHash) {
      const resolvedController = getController();
      if (!resolvedController) {
        return;
      }
      resolvedController.handleHashNavigation(rawHash);
    }

    return {
      getController,
      renderSubmenu,
      getDefaultTargetForMenu,
      activateMenu,
      activateMenuTarget,
      handleHashNavigation
    };
  }

  window.APPVERBO_CREATE_MENU_NAVIGATION_FACADE_V1 = createMenuNavigationFacadeV1;
})();
