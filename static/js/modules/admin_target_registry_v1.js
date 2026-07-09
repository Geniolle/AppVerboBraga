//###################################################################################
// (1) ADMIN TARGET REGISTRY
//###################################################################################
(function initAppGenesisAdminTargetRegistryV1(global) {
  const existingRegistry =
    global.AppGenesisAdminTargetRegistryV1 &&
    typeof global.AppGenesisAdminTargetRegistryV1 === "object"
      ? global.AppGenesisAdminTargetRegistryV1
      : null;

  if (existingRegistry) {
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
    getSidebarAdminSubprocessSetting: function () {
      return null;
    },
    getSidebarAdminMenuKeyByTarget: function () {
      return "";
    },
    ESTRUTURAS_MENU_KEY_V1: "sessoes",
    EMPRESA_MENU_KEY_V1: "empresa"
  };

  const NATIVE_ADMIN_TARGETS_V1 = new Set([
    "#create-entity-card",
    "#edit-entity-card",
    "#recent-entities-card",
    "#inactive-entities-card",
    "#create-user-card",
    "#edit-user-card",
    "#admin-users-created-card",
    "#inactive-users-card",
    "#admin-account-create-card",
    "#admin-account-status-card",
    "#admin-sidebar-sections-card",
    "#admin-sidebar-sections-form-card",
    "#settings-card",
    "#settings-menu-edit-card"
  ]);

  const ESTRUTURAS_NATIVE_TARGETS_V1 = new Set([
    "#admin-account-create-card",
    "#admin-account-status-card",
    "#menu-subprocess-card",
    "#menu-subprocess-card-active",
    "#menu-subprocess-card-inactive",
    "#admin-sidebar-sections-card",
    "#admin-sidebar-sections-card-active",
    "#admin-sidebar-sections-card-inactive",
    "#admin-sidebar-sections-form-card",
    "#settings-card",
    "#settings-menu-edit-card"
  ]);

  const EMPRESA_NATIVE_TARGETS_V1 = new Set(["#empresa-card"]);

  const AUTHORIZATION_PROFILE_TARGET_ALIAS_MAP_V1 = Object.freeze({
    "#auth-profile": "#auth-profile-card",
    "#auth-profile-card": "#auth-profile-card",
    "#auth-profile-active-card": "#auth-profile-card",
    "#auth-profile-inactive-card": "#auth-profile-card",
    "#auth-profile-form-card": "#auth-profile-card",
    "#auth-objeto": "#auth-objeto-card",
    "#auth-objeto-card": "#auth-objeto-card",
    "#auth-objeto-active-card": "#auth-objeto-card",
    "#auth-objeto-inactive-card": "#auth-objeto-card",
    "#auth-objeto-form-card": "#auth-objeto-card"
  });

  const AUTH_PROFILE_NATIVE_TARGETS_V1 = new Set(
    Object.keys(AUTHORIZATION_PROFILE_TARGET_ALIAS_MAP_V1)
  );

  function configure(options) {
    const safeOptions = options && typeof options === "object" ? options : {};

    if (typeof safeOptions.normalizeMenuKey === "function") {
      state.normalizeMenuKey = safeOptions.normalizeMenuKey;
    }
    if (typeof safeOptions.normalizeTarget === "function") {
      state.normalizeTarget = safeOptions.normalizeTarget;
    }
    if (typeof safeOptions.getSidebarAdminSubprocessSetting === "function") {
      state.getSidebarAdminSubprocessSetting = safeOptions.getSidebarAdminSubprocessSetting;
    }
    if (typeof safeOptions.getSidebarAdminMenuKeyByTarget === "function") {
      state.getSidebarAdminMenuKeyByTarget = safeOptions.getSidebarAdminMenuKeyByTarget;
    }
    if (typeof safeOptions.ESTRUTURAS_MENU_KEY_V1 === "string" && safeOptions.ESTRUTURAS_MENU_KEY_V1.trim()) {
      state.ESTRUTURAS_MENU_KEY_V1 = safeOptions.ESTRUTURAS_MENU_KEY_V1.trim();
    }
    if (typeof safeOptions.EMPRESA_MENU_KEY_V1 === "string" && safeOptions.EMPRESA_MENU_KEY_V1.trim()) {
      state.EMPRESA_MENU_KEY_V1 = safeOptions.EMPRESA_MENU_KEY_V1.trim();
    }
  }

  function normalizeBaseTarget(value) {
    let cleanTarget = state.normalizeTarget(value);

    if (!cleanTarget) {
      return "";
    }

    if (cleanTarget.endsWith("-active")) {
      cleanTarget = cleanTarget.substring(0, cleanTarget.length - 7);
    } else if (cleanTarget.endsWith("-inactive")) {
      cleanTarget = cleanTarget.substring(0, cleanTarget.length - 9);
    } else if (cleanTarget.endsWith("-form-card")) {
      cleanTarget = cleanTarget.substring(0, cleanTarget.length - 10) + "-card";
    }

    const normalizedAuthorizationProfileTarget = normalizeAuthorizationProfileTarget(cleanTarget);
    return normalizedAuthorizationProfileTarget || cleanTarget;
  }

  function normalizeAuthorizationProfileTarget(value) {
    return AUTHORIZATION_PROFILE_TARGET_ALIAS_MAP_V1[state.normalizeTarget(value)] || "";
  }

  function authorizationProfileTargetsMatch(leftTarget, rightTarget) {
    const normalizedLeftTarget = normalizeAuthorizationProfileTarget(leftTarget);
    const normalizedRightTarget = normalizeAuthorizationProfileTarget(rightTarget);
    if (normalizedLeftTarget || normalizedRightTarget) {
      return normalizedLeftTarget === normalizedRightTarget;
    }
    return state.normalizeTarget(leftTarget) === state.normalizeTarget(rightTarget);
  }

  function isNativeAdminTarget(value) {
    return NATIVE_ADMIN_TARGETS_V1.has(state.normalizeTarget(value));
  }

  function isNativeTargetForMenu(menuKey, value) {
    const cleanMenuKey = state.normalizeMenuKey(menuKey);
    const cleanTarget = normalizeBaseTarget(value);
    const originalTarget = state.normalizeTarget(value);

    if (!cleanTarget) {
      return false;
    }

    if (cleanMenuKey === "administrativo") {
      return NATIVE_ADMIN_TARGETS_V1.has(cleanTarget) || NATIVE_ADMIN_TARGETS_V1.has(originalTarget);
    }

    if (cleanMenuKey === state.ESTRUTURAS_MENU_KEY_V1) {
      return ESTRUTURAS_NATIVE_TARGETS_V1.has(cleanTarget) || ESTRUTURAS_NATIVE_TARGETS_V1.has(originalTarget);
    }

    if (cleanMenuKey === state.EMPRESA_MENU_KEY_V1) {
      return EMPRESA_NATIVE_TARGETS_V1.has(cleanTarget) || EMPRESA_NATIVE_TARGETS_V1.has(originalTarget);
    }

    if (cleanMenuKey === "perfil_de_autorizacao") {
      return AUTH_PROFILE_NATIVE_TARGETS_V1.has(cleanTarget) || AUTH_PROFILE_NATIVE_TARGETS_V1.has(originalTarget);
    }

    const sidebarAdminSubprocessSetting = state.getSidebarAdminSubprocessSetting(cleanMenuKey);
    if (sidebarAdminSubprocessSetting) {
      return (
        cleanTarget === sidebarAdminSubprocessSetting.defaultTarget ||
        cleanTarget === sidebarAdminSubprocessSetting.editTarget ||
        originalTarget === sidebarAdminSubprocessSetting.defaultTarget ||
        originalTarget === sidebarAdminSubprocessSetting.editTarget
      );
    }

    return false;
  }

  function getAdminSubprocessKeyByTarget(target) {
    const cleanTarget = state.normalizeTarget(target);
    const sidebarAdminMenuKey = state.getSidebarAdminMenuKeyByTarget(cleanTarget);
    if (sidebarAdminMenuKey) {
      const sidebarAdminSubprocessSetting = state.getSidebarAdminSubprocessSetting(sidebarAdminMenuKey);
      return sidebarAdminSubprocessSetting ? sidebarAdminSubprocessSetting.subprocessKey : "";
    }

    const targetMap = {
      "#create-entity-card": "entidade",
      "#edit-entity-card": "entidade",
      "#recent-entities-card": "entidade",
      "#inactive-entities-card": "entidade",
      "#create-user-card": "utilizador",
      "#edit-user-card": "utilizador",
      "#admin-users-created-card": "utilizador",
      "#inactive-users-card": "utilizador",
      "#admin-sidebar-sections-card": "sessoes",
      "#admin-sidebar-sections-form-card": "sessoes",
      "#admin-sidebar-sections-card-active": "sessoes",
      "#admin-sidebar-sections-card-inactive": "sessoes",
      "#settings-card": "menu",
      "#settings-menu-edit-card": "menu",
      "#admin-account-status-card": "menu",
      "#admin-account-create-card": "menu",
      "#menu-subprocess-card": "menu",
      "#menu-subprocess-card-active": "menu",
      "#menu-subprocess-card-inactive": "menu",
      "#auth-profile-card": "perfil_de_autorizacao",
      "#auth-profile-form-card": "perfil_de_autorizacao",
      "#auth-profile-active-card": "perfil_de_autorizacao",
      "#auth-profile-inactive-card": "perfil_de_autorizacao",
      "#auth-objeto-card": "objeto_de_autorizacao",
      "#auth-objeto-form-card": "objeto_de_autorizacao",
      "#auth-objeto-active-card": "objeto_de_autorizacao",
      "#auth-objeto-inactive-card": "objeto_de_autorizacao"
    };
    return targetMap[cleanTarget] || "";
  }

  function normalizeSubmenuTargetAlias(targetSelector) {
    const cleanTarget = String(targetSelector || "").trim();
    const normalizedAuthorizationProfileTarget = normalizeAuthorizationProfileTarget(cleanTarget);
    if (normalizedAuthorizationProfileTarget) {
      return normalizedAuthorizationProfileTarget;
    }

    const sidebarAdminMenuKey = state.getSidebarAdminMenuKeyByTarget(cleanTarget);
    if (sidebarAdminMenuKey) {
      const sidebarAdminSubprocessSetting = state.getSidebarAdminSubprocessSetting(sidebarAdminMenuKey);
      if (
        sidebarAdminSubprocessSetting &&
        cleanTarget === sidebarAdminSubprocessSetting.editTarget
      ) {
        return sidebarAdminSubprocessSetting.defaultTarget;
      }
    }

    const targetAliasMap = {
      "#edit-user-card": "#create-user-card",
      "#admin-users-created-card": "#create-user-card",
      "#inactive-users-card": "#create-user-card",
      "#create-entity-card": "#recent-entities-card",
      "#edit-entity-card": "#recent-entities-card",
      "#inactive-entities-card": "#recent-entities-card",
      "#admin-account-create-card": "#menu-subprocess-card-active",
      "#settings-menu-edit-card": "#menu-subprocess-card-active",
      "#admin-sidebar-sections-form-card": "#admin-sidebar-sections-card"
    };
    return targetAliasMap[cleanTarget] || cleanTarget;
  }

  global.AppGenesisAdminTargetRegistryV1 = Object.freeze({
    configure,
    NATIVE_ADMIN_TARGETS_V1,
    ESTRUTURAS_NATIVE_TARGETS_V1,
    EMPRESA_NATIVE_TARGETS_V1,
    AUTHORIZATION_PROFILE_TARGET_ALIAS_MAP_V1,
    AUTH_PROFILE_NATIVE_TARGETS_V1,
    normalizeBaseTarget,
    normalizeAuthorizationProfileTarget,
    authorizationProfileTargetsMatch,
    isNativeAdminTarget,
    isNativeTargetForMenu,
    getAdminSubprocessKeyByTarget,
    normalizeSubmenuTargetAlias
  });
})(window);
