//###################################################################################
// (1) PROCESS CARDS VISIBILITY
//###################################################################################
(function initAppGenesisProcessCardsVisibilityV1(global) {
  const existingRuntime =
    global.AppGenesisProcessCardsVisibilityV1 &&
    typeof global.AppGenesisProcessCardsVisibilityV1 === "object"
      ? global.AppGenesisProcessCardsVisibilityV1
      : null;

  if (existingRuntime) {
    return;
  }

  const state = {
    normalizeMenuKey: function (value) {
      return String(value || "").trim().toLowerCase();
    },
    getSidebarAdminSubprocessSetting: function () {
      return null;
    },
    getAdminSubprocessKeyByTarget: function () {
      return "";
    },
    ESTRUTURAS_MENU_KEY_V1: "sessoes",
    scopedCards: [],
    dynamicProcessCardEl: null,
    dynamicProcessActionCardEl: null,
    dynamicProcessActiveCardEl: null,
    dynamicProcessInactiveCardEl: null,
    debugTabsLog: function () {},
    logNavigationBootDebug: function () {},
    documentRef: global.document || null,
    windowRef: global
  };

  function configure(options) {
    const safeOptions = options && typeof options === "object" ? options : {};

    if (typeof safeOptions.normalizeMenuKey === "function") {
      state.normalizeMenuKey = safeOptions.normalizeMenuKey;
    }
    if (typeof safeOptions.getSidebarAdminSubprocessSetting === "function") {
      state.getSidebarAdminSubprocessSetting = safeOptions.getSidebarAdminSubprocessSetting;
    }
    if (typeof safeOptions.getAdminSubprocessKeyByTarget === "function") {
      state.getAdminSubprocessKeyByTarget = safeOptions.getAdminSubprocessKeyByTarget;
    }
    if (
      typeof safeOptions.ESTRUTURAS_MENU_KEY_V1 === "string" &&
      safeOptions.ESTRUTURAS_MENU_KEY_V1.trim()
    ) {
      state.ESTRUTURAS_MENU_KEY_V1 = safeOptions.ESTRUTURAS_MENU_KEY_V1.trim();
    }
    if (safeOptions.scopedCards) {
      state.scopedCards = safeOptions.scopedCards;
    }
    if ("dynamicProcessCardEl" in safeOptions) {
      state.dynamicProcessCardEl = safeOptions.dynamicProcessCardEl;
    }
    if ("dynamicProcessActionCardEl" in safeOptions) {
      state.dynamicProcessActionCardEl = safeOptions.dynamicProcessActionCardEl;
    }
    if ("dynamicProcessActiveCardEl" in safeOptions) {
      state.dynamicProcessActiveCardEl = safeOptions.dynamicProcessActiveCardEl;
    }
    if ("dynamicProcessInactiveCardEl" in safeOptions) {
      state.dynamicProcessInactiveCardEl = safeOptions.dynamicProcessInactiveCardEl;
    }
    if (typeof safeOptions.debugTabsLog === "function") {
      state.debugTabsLog = safeOptions.debugTabsLog;
    }
    if (typeof safeOptions.logNavigationBootDebug === "function") {
      state.logNavigationBootDebug = safeOptions.logNavigationBootDebug;
    }
    if (safeOptions.documentRef) {
      state.documentRef = safeOptions.documentRef;
    }
    if (safeOptions.windowRef) {
      state.windowRef = safeOptions.windowRef;
    }
  }

  function setDynamicProcessCardsVisibility(isVisible) {
    const displayValue = isVisible ? "" : "none";

    if (state.dynamicProcessCardEl) {
      state.dynamicProcessCardEl.style.display = displayValue;
    }
    if (state.dynamicProcessActionCardEl) {
      state.dynamicProcessActionCardEl.style.display = displayValue;
    }
    if (state.dynamicProcessActiveCardEl) {
      state.dynamicProcessActiveCardEl.style.display = displayValue;
    }
    if (state.dynamicProcessInactiveCardEl) {
      state.dynamicProcessInactiveCardEl.style.display = displayValue;
    }
  }

  function applyContentForMenu(menuKey) {
    Array.from(state.scopedCards || []).forEach((card) => {
      const rawScope = card.getAttribute("data-menu-scope") || "";
      const scopes = rawScope.split(",").map((value) => state.normalizeMenuKey(value)).filter(Boolean);
      card.style.display = scopes.includes(menuKey) ? "" : "none";
    });
    setDynamicProcessCardsVisibility(false);
  }

  function cardBelongsToEntityGroup(menuKey, targetSelector, card) {
    return (
      menuKey === "administrativo" &&
      targetSelector === "#create-entity-card" &&
      (
        card.id === "create-entity-card" ||
        card.id === "edit-entity-card" ||
        card.id === "recent-entities-card" ||
        card.id === "inactive-entities-card"
      )
    );
  }

  function cardBelongsToUserGroup(menuKey, targetSelector, card) {
    return (
      menuKey === "administrativo" &&
      targetSelector === "#create-user-card" &&
      (
        card.id === "create-user-card" ||
        card.id === "edit-user-card" ||
        card.id === "admin-users-created-card" ||
        card.id === "inactive-users-card"
      )
    );
  }

  function cardBelongsToSettingsGroup(supportsStructuredAdminGroups, targetSelector, card) {
    return (
      supportsStructuredAdminGroups &&
      (
        targetSelector === "#admin-account-create-card" ||
        targetSelector === "#admin-account-status-card" ||
        targetSelector === "#settings-menu-edit-card"
      ) &&
      (
        card.id === "admin-account-create-card" ||
        card.id === "settings-menu-edit-card" ||
        card.id === "admin-account-status-card"
      )
    );
  }

  function applyContentForMenuTarget(menuKey, targetSelector, source) {
    const cleanSource = String(source || "unspecified");
    const shouldShowGlobalLoaderV1 =
      cleanSource === "click:sidebar" || cleanSource === "click:submenu-tab";
    const windowRef = state.windowRef || global;

    if (
      shouldShowGlobalLoaderV1 &&
      typeof windowRef.showGlobalLoadingOverlayV1 === "function"
    ) {
      windowRef.showGlobalLoadingOverlayV1("navigation:" + cleanSource);
    }

    state.debugTabsLog("applyContent:start", {
      menuKey,
      targetSelector,
      visibleCards: Array.from(state.scopedCards || [])
        .filter((card) => card.style.display !== "none")
        .map((card) => card.id || card.className)
    });

    const sidebarAdminSubprocessSetting = state.getSidebarAdminSubprocessSetting(menuKey);
    const supportsStructuredAdminGroups = (
      menuKey === "administrativo" ||
      menuKey === state.ESTRUTURAS_MENU_KEY_V1 ||
      menuKey === "perfil_de_autorizacao" ||
      Boolean(sidebarAdminSubprocessSetting)
    );
    const adminSubprocessKey = supportsStructuredAdminGroups
      ? state.getAdminSubprocessKeyByTarget(targetSelector)
      : "";

    state.logNavigationBootDebug("activateSubprocessCardsV1:resolve", {
      source: cleanSource,
      menuKey,
      targetSelector,
      adminSubprocessKey,
      supportsStructuredAdminGroups,
      menuSubprocessCardActiveExists: !!(
        state.documentRef && state.documentRef.getElementById("menu-subprocess-card-active")
      ),
      menuSubprocessCardInactiveExists: !!(
        state.documentRef && state.documentRef.getElementById("menu-subprocess-card-inactive")
      )
    });

    const shownCardIds = [];
    const hiddenCardIds = [];

    Array.from(state.scopedCards || []).forEach((card) => {
      const rawScope = card.getAttribute("data-menu-scope") || "";
      const scopes = rawScope.split(",").map((value) => state.normalizeMenuKey(value)).filter(Boolean);
      if (!scopes.includes(menuKey)) {
        card.style.display = "none";
        return;
      }

      const allowAdminSubprocessGroupForTarget = targetSelector !== "#settings-menu-edit-card";
      const isAdminSubprocessGroupedBlock =
        allowAdminSubprocessGroupForTarget &&
        Boolean(adminSubprocessKey) &&
        card.getAttribute("data-admin-subprocess") === adminSubprocessKey;
      const shouldShowCard =
        targetSelector === ("#" + card.id) ||
        isAdminSubprocessGroupedBlock ||
        cardBelongsToEntityGroup(menuKey, targetSelector, card) ||
        cardBelongsToUserGroup(menuKey, targetSelector, card) ||
        cardBelongsToSettingsGroup(supportsStructuredAdminGroups, targetSelector, card);

      card.style.display = shouldShowCard ? "" : "none";
      if (card.id) {
        (shouldShowCard ? shownCardIds : hiddenCardIds).push(card.id);
      }
    });

    setDynamicProcessCardsVisibility(targetSelector === "#dynamic-process-card");

    state.debugTabsLog("applyContent:end", {
      menuKey,
      targetSelector,
      visibleCards: Array.from(state.scopedCards || [])
        .filter((card) => card.style.display !== "none")
        .map((card) => card.id || card.className)
    });

    state.logNavigationBootDebug("activateSubprocessCardsV1:applied", {
      source: cleanSource,
      menuKey,
      targetSelector,
      adminSubprocessKey,
      shownCardIds,
      hiddenCardIds: hiddenCardIds.filter(
        (id) => id.indexOf("menu-subprocess") !== -1 || id.indexOf("admin-sidebar-sections") !== -1
      ),
      menuSubprocessCardActiveShown: shownCardIds.includes("menu-subprocess-card-active"),
      menuSubprocessCardInactiveShown: shownCardIds.includes("menu-subprocess-card-inactive")
    });

    if (
      shouldShowGlobalLoaderV1 &&
      typeof windowRef.hideGlobalLoadingOverlayV1 === "function"
    ) {
      windowRef.setTimeout(
        () => windowRef.hideGlobalLoadingOverlayV1("navigation:" + cleanSource),
        800
      );
    }
  }

  global.AppGenesisProcessCardsVisibilityV1 = Object.freeze({
    configure,
    applyContentForMenu,
    applyContentForMenuTarget,
    setDynamicProcessCardsVisibility
  });
})(window);
