//###################################################################################
// (1) PROCESS/SUBPROCESS STANDARDS V1
//###################################################################################
(function registerProcessSubprocessStandardsV1() {
  "use strict";

  const DEFAULT_TAB_THEME_V1 = Object.freeze({
    activeColor: "#0b63d1",
    inactiveColor: "#1f2937",
    indicatorColor: "#0b63d1",
    borderColor: "#d6dfed"
  });

  const ADMINISTRATIVO_SUBPROCESS_TABS_V1 = Object.freeze([
    {
      key: "entidade",
      label: "Entidade",
      target: "#create-entity-card",
      route: {
        adminTab: "entidade",
        target: "create-entity-card",
        hash: "create-entity-card"
      }
    },
    {
      key: "utilizador",
      label: "Utilizador",
      target: "#create-user-card",
      route: {
        adminTab: "utilizador",
        target: "create-user-card",
        hash: "create-user-card"
      }
    },
    {
      key: "definicoes",
      label: "Definições",
      target: "#admin-definicoes-card",
      route: {
        adminTab: "definicoes",
        target: "admin-definicoes-card",
        hash: "admin-definicoes-card"
      }
    }
  ]);

  const SESSOES_SUBPROCESS_TABS_V1 = Object.freeze([
    {
      key: "sessoes",
      label: "Sessões",
      target: "#admin-sidebar-sections-card",
      route: {
        adminTab: "sessoes",
        target: "admin-sidebar-sections-card",
        hash: "admin-sidebar-sections-card",
        extraQuery: {
          sidebar_sections_tab: "sessoes"
        }
      }
    },
    {
      key: "menu",
      label: "Menu",
      target: "#admin-menu-card",
      route: {
        adminTab: "menu",
        target: "admin-menu-card",
        hash: "admin-menu-card"
      }
    },
    {
      key: "perfil",
      label: "Perfil",
      target: "#admin-perfil-card",
      route: {
        adminTab: "perfil",
        target: "admin-perfil-card",
        hash: "admin-perfil-card"
      }
    }
  ]);


  const SUBPROCESS_TAB_LIBRARY_V1 = Object.freeze({
    administrativo: ADMINISTRATIVO_SUBPROCESS_TABS_V1,
    sessoes: SESSOES_SUBPROCESS_TABS_V1
  });

  const MENU_TARGET_ALIAS_LIBRARY_V1 = Object.freeze({
    administrativo: Object.freeze({
      "#admin-definicoes-card-edit": "#admin-definicoes-card"
    }),
    sessoes: Object.freeze({
      "#admin-menu-form": "#admin-menu-card",
      "#admin-menu-create-card": "#admin-menu-card",
      "#admin-sidebar-sections-form-card": "#admin-sidebar-sections-card"
    })
  });

  const MENU_SCOPED_CARD_GROUP_LIBRARY_V1 = Object.freeze({
    sessoes: Object.freeze([
      Object.freeze({
        key: "sessoes",
        targets: Object.freeze([
          "#admin-sidebar-sections-card",
          "#admin-sidebar-sections-card-create",
          "#admin-sidebar-sections-card-inactive",
          "#admin-sidebar-sections-form-card"
        ]),
        cardIds: Object.freeze([
          "admin-sidebar-sections-card-create",
          "admin-sidebar-sections-card",
          "admin-sidebar-sections-card-inactive",
          "admin-sidebar-sections-form-card"
        ])
      }),
      Object.freeze({
        key: "menu",
        targets: Object.freeze([
          "#admin-menu-card",
          "#admin-menu-card-inactive",
          "#admin-menu-card-create",
          "#settings-menu-edit-card"
        ]),
        cardIds: Object.freeze([
          "admin-menu-card-create",
          "admin-menu-card",
          "admin-menu-card-inactive",
          "settings-menu-edit-card"
        ])
      })
    ]),
    administrativo: Object.freeze([
      Object.freeze({
        key: "entidade",
        targets: Object.freeze(["#create-entity-card", "#admin-subprocess-v2-entidade"]),
        cardIds: Object.freeze([
          "create-entity-card",
          "edit-entity-card",
          "recent-entities-card",
          "inactive-entities-card",
          "admin-entidade-v2-integrated-root"
        ])
      }),
      Object.freeze({
        key: "utilizador",
        targets: Object.freeze(["#create-user-card"]),
        cardIds: Object.freeze([
          "create-user-card",
          "edit-user-card",
          "admin-user-shadow-readonly-card",
          "admin-user-shadow-inactive-card",
          "admin-users-created-card",
          "inactive-users-card"
        ])
      }),
      Object.freeze({
        key: "definicoes",
        targets: Object.freeze([
          "#admin-definicoes-card",
          "#admin-definicoes-card-create",
          "#admin-definicoes-card-inactive",
          "#admin-definicoes-card-edit"
        ]),
        cardIds: Object.freeze([
          "admin-definicoes-card",
          "admin-definicoes-card-create",
          "admin-definicoes-card-inactive",
          "admin-definicoes-card-edit"
        ])
      })
    ])
  });

  const HASH_TARGET_ALIAS_LIBRARY_V1 = Object.freeze({
    "#edit-user-card": "#create-user-card",
    "#admin-user-shadow-readonly-card": "#create-user-card",
    "#admin-user-shadow-inactive-card": "#create-user-card",
    "#admin-users-created-card": "#create-user-card",
    "#inactive-users-card": "#create-user-card",
    "#edit-entity-card": "#create-entity-card",
    "#configuracao-account-status-card": "#admin-menu-card",
    "#admin-definicoes-card-create": "#admin-definicoes-card",
    "#admin-definicoes-card-inactive": "#admin-definicoes-card"
  });

  const HASH_TARGET_MENU_LIBRARY_V1 = Object.freeze({
    "#create-user-card": "administrativo",
    "#create-entity-card": "administrativo",
    "#admin-subprocess-v2-entidade": "administrativo",
    "#admin-definicoes-card": "administrativo",
    "#admin-definicoes-card-create": "administrativo",
    "#admin-definicoes-card-inactive": "administrativo",
    "#admin-definicoes-card-edit": "administrativo",
    "#admin-menu-card-create": "sessoes",
    "#admin-menu-card": "sessoes",
    "#admin-menu-card-inactive": "sessoes",
    "#admin-sidebar-sections-card": "sessoes",
    "#admin-sidebar-sections-form-card": "sessoes",
    "#settings-menu-edit-card": "sessoes"
  });

  //###################################################################################
  // (2) HELPERS
  //###################################################################################
  function defaultNormalizeMenuKeyV1(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeHashValueV1(rawHash) {
    const cleanHash = String(rawHash || "").trim();
    if (!cleanHash) {
      return "";
    }
    return cleanHash.charAt(0) === "#" ? cleanHash.slice(1) : cleanHash;
  }

  function normalizeTargetSelectorV1(rawSelector) {
    const cleanSelector = String(rawSelector || "").trim();
    if (!cleanSelector) {
      return "";
    }
    return cleanSelector.charAt(0) === "#" ? cleanSelector : `#${cleanSelector}`;
  }

  function normalizeCardIdV1(rawCardId) {
    return String(rawCardId || "").trim().replace(/^#/, "");
  }

  function cloneTabDefinitionV1(tabDefinition) {
    return {
      ...tabDefinition,
      route: tabDefinition && tabDefinition.route
        ? { ...tabDefinition.route }
        : null
    };
  }

  function cloneScopedCardGroupV1(group) {
    return {
      key: String(group && group.key || "").trim(),
      targets: Array.isArray(group && group.targets)
        ? group.targets.map((target) => String(target || "").trim())
        : [],
      cardIds: Array.isArray(group && group.cardIds)
        ? group.cardIds.map((cardId) => normalizeCardIdV1(cardId))
        : []
    };
  }

  //###################################################################################
  // (3) SUBPROCESS TABS STANDARD
  //###################################################################################
  function getStandardSubprocessTabsV1(menuKey, options = {}) {
    const normalizeMenuKey = (
      typeof options.normalizeMenuKey === "function"
        ? options.normalizeMenuKey
        : defaultNormalizeMenuKeyV1
    );
    const cleanMenuKey = normalizeMenuKey(menuKey);
    const tabDefinitions = SUBPROCESS_TAB_LIBRARY_V1[cleanMenuKey] || [];
    return tabDefinitions.map(cloneTabDefinitionV1);
  }

  function getStandardSubprocessKeysV1(menuKey, options = {}) {
    return getStandardSubprocessTabsV1(menuKey, options)
      .map((tabDefinition) => normalizeHashValueV1(tabDefinition && tabDefinition.key))
      .filter(Boolean);
  }

  function getStandardSubprocessTargetMapV1(menuKey, options = {}) {
    const map = new Map();
    getStandardSubprocessTabsV1(menuKey, options).forEach((tabDefinition) => {
      const target = String(tabDefinition && tabDefinition.target || "").trim();
      if (target) {
        map.set(target, cloneTabDefinitionV1(tabDefinition));
      }
    });
    return map;
  }

  function resolveSubprocessNavigationUrlV1(menuKey, item, options = {}) {
    const routeConfig = item && item.route && typeof item.route === "object"
      ? item.route
      : null;
    if (!routeConfig) {
      return "";
    }

    let url = null;
    try {
      const baseHref = String(options.baseHref || window.location.href || "/users/new");
      url = new URL(baseHref, window.location.origin);
    } catch (_error) {
      url = new URL("/users/new", window.location.origin);
    }

    const pathname = String(options.pathname || "/users/new").trim() || "/users/new";
    url.pathname = pathname;
    url.search = "";
    url.hash = "";

    const normalizeMenuKey = (
      typeof options.normalizeMenuKey === "function"
        ? options.normalizeMenuKey
        : defaultNormalizeMenuKeyV1
    );
    const cleanMenuKey = normalizeMenuKey(menuKey);
    url.searchParams.set("menu", cleanMenuKey);

    const adminTab = String(routeConfig.adminTab || "").trim();
    if (adminTab) {
      url.searchParams.set("admin_tab", adminTab);
    }

    const target = String(routeConfig.target || "").trim();
    if (target) {
      url.searchParams.set("target", target);
    }

    const extraQuery = routeConfig.extraQuery && typeof routeConfig.extraQuery === "object"
      ? routeConfig.extraQuery
      : {};
    Object.keys(extraQuery).forEach((queryKey) => {
      const queryValue = String(extraQuery[queryKey] || "").trim();
      if (!queryValue) {
        return;
      }
      url.searchParams.set(queryKey, queryValue);
    });

    const hashValue = normalizeHashValueV1(routeConfig.hash || target || item && item.target || "");
    if (hashValue) {
      url.hash = `#${hashValue}`;
    }

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (4) SCOPED CARD VISIBILITY STANDARD
  //###################################################################################
  function getStandardScopedCardGroupsV1(menuKey, options = {}) {
    const normalizeMenuKey = (
      typeof options.normalizeMenuKey === "function"
        ? options.normalizeMenuKey
        : defaultNormalizeMenuKeyV1
    );
    const cleanMenuKey = normalizeMenuKey(menuKey);
    const groups = MENU_SCOPED_CARD_GROUP_LIBRARY_V1[cleanMenuKey] || [];
    return groups.map(cloneScopedCardGroupV1);
  }

  function resolveStandardScopedTargetV1(menuKey, targetSelector, options = {}) {
    const normalizeMenuKey = (
      typeof options.normalizeMenuKey === "function"
        ? options.normalizeMenuKey
        : defaultNormalizeMenuKeyV1
    );
    const cleanMenuKey = normalizeMenuKey(menuKey);
    const normalizedTarget = normalizeTargetSelectorV1(targetSelector);
    if (!normalizedTarget) {
      return "";
    }

    const aliasMap = MENU_TARGET_ALIAS_LIBRARY_V1[cleanMenuKey] || {};
    const aliasedTarget = normalizeTargetSelectorV1(aliasMap[normalizedTarget] || normalizedTarget);
    return aliasedTarget;
  }

  function isScopedCardMatchV1(menuKey, targetSelector, cardId, options = {}) {
    const normalizedCardId = normalizeCardIdV1(cardId);
    if (!normalizedCardId) {
      return false;
    }

    const resolvedTargetSelector = resolveStandardScopedTargetV1(menuKey, targetSelector, options);
    if (!resolvedTargetSelector) {
      return false;
    }

    if (resolvedTargetSelector === `#${normalizedCardId}`) {
      return true;
    }

    // If the card is an edit card, only match it if the target itself is an edit card
    if (typeof document !== "undefined") {
      const cardEl = document.getElementById(normalizedCardId);
      if (cardEl && cardEl.getAttribute("data-admin-card-role") === "edit") {
        const targetEl = document.querySelector(resolvedTargetSelector);
        const targetRole = targetEl ? targetEl.getAttribute("data-admin-card-role") : null;
        if (targetRole !== "edit") {
          return false;
        }
      }
    }

    // Dynamic matching by data-admin-card-group attribute
    if (typeof document !== "undefined") {
      const cardEl = document.getElementById(normalizedCardId);
      if (cardEl) {
        const cardGroup = cardEl.getAttribute("data-admin-card-group");
        if (cardGroup) {
          const targetEl = document.querySelector(resolvedTargetSelector);
          if (targetEl) {
            const targetGroup = targetEl.getAttribute("data-admin-card-group");
            if (targetGroup && cardGroup === targetGroup) {
              return true;
            }
          }
        }
      }
    }

    const groups = getStandardScopedCardGroupsV1(menuKey, options);
    return groups.some((group) => (
      group.targets.includes(resolvedTargetSelector) &&
      group.cardIds.includes(normalizedCardId)
    ));
  }

  //###################################################################################
  // (5) HASH NAVIGATION STANDARD
  //###################################################################################
  function resolveStandardHashTargetV1(rawHash) {
    const normalizedHash = normalizeTargetSelectorV1(rawHash);
    if (!normalizedHash) {
      return "";
    }

    // Try dynamic DOM-based resolution first
    if (typeof document !== "undefined") {
      const element = document.getElementById(normalizedHash.replace("#", ""));
      if (element) {
        const tabKey = element.getAttribute("data-admin-subprocess");
        if (tabKey) {
          for (const menuKey in SUBPROCESS_TAB_LIBRARY_V1) {
            const tabs = SUBPROCESS_TAB_LIBRARY_V1[menuKey];
            const tabDef = tabs.find((t) => t.key === tabKey);
            if (tabDef && tabDef.target) {
              return normalizeTargetSelectorV1(tabDef.target);
            }
          }
        }
      }
    }

    const aliasedHash = HASH_TARGET_ALIAS_LIBRARY_V1[normalizedHash];
    return normalizeTargetSelectorV1(aliasedHash || normalizedHash);
  }

  function resolveStandardMenuByHashTargetV1(rawHash, options = {}) {
    const normalizeMenuKey = (
      typeof options.normalizeMenuKey === "function"
        ? options.normalizeMenuKey
        : defaultNormalizeMenuKeyV1
    );
    const normalizedTarget = resolveStandardHashTargetV1(rawHash);
    if (!normalizedTarget) {
      return {
        menuKey: "",
        targetSelector: ""
      };
    }

    // Try dynamic DOM-based menuKey resolution first
    if (typeof document !== "undefined") {
      const originalHash = normalizeTargetSelectorV1(rawHash);
      const element = document.getElementById(originalHash.replace("#", ""));
      if (element) {
        const tabKey = element.getAttribute("data-admin-subprocess");
        if (tabKey) {
          for (const menuKey in SUBPROCESS_TAB_LIBRARY_V1) {
            const tabs = SUBPROCESS_TAB_LIBRARY_V1[menuKey];
            if (tabs.some((t) => t.key === tabKey)) {
              return {
                menuKey: normalizeMenuKey(menuKey),
                targetSelector: normalizedTarget
              };
            }
          }
        }
      }
    }

    const menuKey = normalizeMenuKey(HASH_TARGET_MENU_LIBRARY_V1[normalizedTarget] || "");
    return {
      menuKey,
      targetSelector: normalizedTarget
    };
  }

  //###################################################################################
  // (6) TAB THEME STANDARD
  //###################################################################################
  function ensureDefaultSubprocessTabThemeV1() {
    if (typeof document === "undefined" || !document.documentElement) {
      return;
    }

    const root = document.documentElement;
    if (!root.style.getPropertyValue("--appverbo-subprocess-tab-active-color")) {
      root.style.setProperty("--appverbo-subprocess-tab-active-color", DEFAULT_TAB_THEME_V1.activeColor);
    }
    if (!root.style.getPropertyValue("--appverbo-subprocess-tab-inactive-color")) {
      root.style.setProperty("--appverbo-subprocess-tab-inactive-color", DEFAULT_TAB_THEME_V1.inactiveColor);
    }
    if (!root.style.getPropertyValue("--appverbo-subprocess-tab-indicator-color")) {
      root.style.setProperty("--appverbo-subprocess-tab-indicator-color", DEFAULT_TAB_THEME_V1.indicatorColor);
    }
    if (!root.style.getPropertyValue("--appverbo-subprocess-tab-border-color")) {
      root.style.setProperty("--appverbo-subprocess-tab-border-color", DEFAULT_TAB_THEME_V1.borderColor);
    }
  }

  function applySubprocessTabThemeV1(theme = {}) {
    if (typeof document === "undefined" || !document.documentElement) {
      return;
    }
    const root = document.documentElement;
    const activeColor = String(theme.activeColor || DEFAULT_TAB_THEME_V1.activeColor).trim();
    const inactiveColor = String(theme.inactiveColor || DEFAULT_TAB_THEME_V1.inactiveColor).trim();
    const indicatorColor = String(theme.indicatorColor || DEFAULT_TAB_THEME_V1.indicatorColor).trim();
    const borderColor = String(theme.borderColor || DEFAULT_TAB_THEME_V1.borderColor).trim();

    root.style.setProperty("--appverbo-subprocess-tab-active-color", activeColor);
    root.style.setProperty("--appverbo-subprocess-tab-inactive-color", inactiveColor);
    root.style.setProperty("--appverbo-subprocess-tab-indicator-color", indicatorColor);
    root.style.setProperty("--appverbo-subprocess-tab-border-color", borderColor);
  }

  window.APPVERBO_CREATE_PROCESS_SUBPROCESS_STANDARDS_API_V1 = function createProcessSubprocessStandardsApiV1() {
    return {
      DEFAULT_TAB_THEME_V1: { ...DEFAULT_TAB_THEME_V1 },
      getStandardSubprocessTabsV1,
      getStandardSubprocessKeysV1,
      getStandardSubprocessTargetMapV1,
      getStandardScopedCardGroupsV1,
      resolveStandardScopedTargetV1,
      isScopedCardMatchV1,
      resolveStandardHashTargetV1,
      resolveStandardMenuByHashTargetV1,
      resolveSubprocessNavigationUrlV1,
      ensureDefaultSubprocessTabThemeV1,
      applySubprocessTabThemeV1
    };
  };
})();
