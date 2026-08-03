//###################################################################################
// (1) PROCESS NAVIGATION STATE
//###################################################################################
(function initAppGenesisProcessNavigationStateV1(global) {
  const existingState =
    global.AppGenesisProcessNavigationStateV1 &&
    typeof global.AppGenesisProcessNavigationStateV1 === "object"
      ? global.AppGenesisProcessNavigationStateV1
      : null;

  if (existingState) {
    return;
  }

  const state = {
    normalizeMenuKey: function (value) {
      return String(value || "").trim().toLowerCase();
    },
    normalizeTarget: function (value) {
      const cleanValue = String(value || "").trim();
      if (!cleanValue) {
        return "";
      }
      return cleanValue.startsWith("#") ? cleanValue : "#" + cleanValue;
    },
    normalizeAuthorizationProfileTarget: function () {
      return "";
    },
    isNativeAdminTarget: function () {
      return false;
    },
    isNativeTargetForMenu: function () {
      return false;
    },
    selectedTargetByMenu: {},
    windowRef: global
  };

  function configure(options) {
    const safeOptions = options && typeof options === "object" ? options : {};

    if (typeof safeOptions.normalizeMenuKey === "function") {
      state.normalizeMenuKey = safeOptions.normalizeMenuKey;
    }
    if (typeof safeOptions.normalizeTarget === "function") {
      state.normalizeTarget = safeOptions.normalizeTarget;
    }
    if (typeof safeOptions.normalizeAuthorizationProfileTarget === "function") {
      state.normalizeAuthorizationProfileTarget = safeOptions.normalizeAuthorizationProfileTarget;
    }
    if (typeof safeOptions.isNativeAdminTarget === "function") {
      state.isNativeAdminTarget = safeOptions.isNativeAdminTarget;
    }
    if (typeof safeOptions.isNativeTargetForMenu === "function") {
      state.isNativeTargetForMenu = safeOptions.isNativeTargetForMenu;
    }
    if (
      safeOptions.selectedTargetByMenu &&
      typeof safeOptions.selectedTargetByMenu === "object"
    ) {
      state.selectedTargetByMenu = safeOptions.selectedTargetByMenu;
    }
    if (safeOptions.windowRef) {
      state.windowRef = safeOptions.windowRef;
    }
  }

  function resolveAdminSelectedTargetV1({
    initialAdminTab,
    startupHash: rawHash,
    initialMenuTarget: rawTarget,
    settingsEditKey: rawSettingsKey
  }) {
    let cleanHash = state.normalizeTarget(rawHash);
    if (cleanHash === "#edit-user-card") {
      cleanHash = "#create-user-card";
    } else if (cleanHash === "#edit-entity-card") {
      cleanHash = "#recent-entities-card";
    }
    const cleanTarget = state.normalizeTarget(rawTarget);
    const cleanTab = String(initialAdminTab || "").trim().toLowerCase();
    if (state.isNativeAdminTarget(cleanHash)) {
      return cleanHash;
    }
    if (state.isNativeAdminTarget(cleanTarget)) {
      return cleanTarget;
    }
    if (rawSettingsKey) {
      return "#settings-menu-edit-card";
    }
    if (cleanTab === "sessoes") {
      return "#admin-sidebar-sections-card";
    }
    if (cleanTab === "entidade") {
      return "#recent-entities-card";
    }
    if (cleanTab === "utilizador") {
      return "#create-user-card";
    }
    if (cleanTab === "contas") {
      return "#menu-subprocess-card-active";
    }
    return "#dynamic-process-card";
  }

  function getDefaultTargetForMenu(menuKey, config, options) {
    const safeOptions = options && typeof options === "object" ? options : {};
    const forceFirstItem = Boolean(safeOptions.forceFirstItem);

    if (!Array.isArray(config.items) || !config.items.length) {
      const savedTarget = state.selectedTargetByMenu[menuKey];
      if (state.isNativeTargetForMenu(menuKey, savedTarget)) {
        return savedTarget;
      }
      return "";
    }
    if (forceFirstItem) {
      return config.items[0].target;
    }
    const savedTarget = state.selectedTargetByMenu[menuKey];
    if (savedTarget) {
      if (state.isNativeTargetForMenu(menuKey, savedTarget)) {
        return savedTarget;
      }
      if (config.items.some((item) => item.target === savedTarget)) {
        return savedTarget;
      }
    }
    return config.items[0].target;
  }

  function hasExplicitAuthProfileContextV1() {
    try {
      const windowRef = state.windowRef || global;
      const params = new URLSearchParams(windowRef.location.search);
      const menuKey = state.normalizeMenuKey(params.get("menu") || "");
      const targetKey = String(params.get("target") || "").trim();
      const hashKey = windowRef.location.hash || "";
      const hasAuthorizationProfileTarget =
        Boolean(state.normalizeAuthorizationProfileTarget(targetKey)) ||
        Boolean(state.normalizeAuthorizationProfileTarget(hashKey));

      return (
        menuKey === "perfil_de_autorizacao" ||
        hasAuthorizationProfileTarget ||
        (params.get("appgenesis_after_save") === "1" && menuKey === "perfil_de_autorizacao")
      );
    } catch (err) {
      return false;
    }
  }

  function resolveStartupMenu(options) {
    const safeOptions = options && typeof options === "object" ? options : {};
    const menuConfig = (
      safeOptions.menuConfig &&
      typeof safeOptions.menuConfig === "object" &&
      !Array.isArray(safeOptions.menuConfig)
    )
      ? safeOptions.menuConfig
      : {};
    const initialMenu = state.normalizeMenuKey(safeOptions.initialMenu || "");
    const sidebarMenuKeys = safeOptions.sidebarMenuKeys instanceof Set
      ? safeOptions.sidebarMenuKeys
      : new Set(Array.isArray(safeOptions.sidebarMenuKeys) ? safeOptions.sidebarMenuKeys : []);

    let startupMenu = menuConfig[initialMenu] ? initialMenu : "home";

    if (startupMenu === "perfil_de_autorizacao" && !hasExplicitAuthProfileContextV1()) {
      startupMenu = "home";
    }

    if (!sidebarMenuKeys.has(startupMenu) && startupMenu !== "perfil") {
      if (sidebarMenuKeys.has("home")) {
        startupMenu = "home";
      } else {
        const fallbackMenu = Array.from(sidebarMenuKeys.values()).find(
          (key) => key !== "perfil_de_autorizacao"
        );
        startupMenu = fallbackMenu || "home";
      }
    }

    return startupMenu;
  }

  global.AppGenesisProcessNavigationStateV1 = Object.freeze({
    configure,
    resolveAdminSelectedTargetV1,
    getDefaultTargetForMenu,
    hasExplicitAuthProfileContextV1,
    resolveStartupMenu
  });
})(window);
