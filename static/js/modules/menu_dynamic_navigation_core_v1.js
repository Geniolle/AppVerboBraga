// APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_MODULE_START
(function registerMenuDynamicNavigationCoreV1Module() {
  "use strict";

  const ADMINISTRATIVO_TRAILING_STANDARD_KEYS_V1 = Object.freeze([
    "sessoes",
    "menu",
    "definicoes"
  ]);

  //###################################################################################
  // (1) HELPERS
  //###################################################################################
  function defaultNormalizeMenuKeyV1(value) {
    return String(value || "").trim().toLowerCase();
  }

  function defaultToSentenceCaseTextV1(value) {
    const cleanValue = String(value || "").trim();
    if (!cleanValue) {
      return "";
    }
    return cleanValue.charAt(0).toUpperCase() + cleanValue.slice(1);
  }

  function createMenuItemUniqueKeyFallbackV1(item) {
    const target = String(item && item.target ? item.target : "").trim();
    const sectionKey = String(item && item.dynamicProcessSectionKey ? item.dynamicProcessSectionKey : "").trim();
    const profileSection = String(item && item.profileSection ? item.profileSection : "").trim();
    const label = String(item && item.label ? item.label : "").trim();
    return `${target}::${sectionKey}::${profileSection}::${label}`;
  }

  function resolveElementByIdV1(options, id) {
    const key = String(id || "").trim();
    const contextualElement = options && options[key];
    if (contextualElement) {
      return contextualElement;
    }
    if (typeof document === "undefined" || !key) {
      return null;
    }
    return document.getElementById(key);
  }

  function resolveScopedCardsV1(options) {
    if (options && options.scopedCards && typeof options.scopedCards.forEach === "function") {
      return options.scopedCards;
    }
    if (typeof document === "undefined") {
      return [];
    }
    return document.querySelectorAll("[data-menu-scope]");
  }

  function showElementV1(element) {
    if (!element || !element.style) {
      return;
    }
    element.style.removeProperty("display");
  }

  function hideElementV1(element) {
    if (!element || !element.style) {
      return;
    }
    element.style.setProperty("display", "none", "important");
  }

  //###################################################################################
  // (2) SETUP
  //###################################################################################
  window.APPVERBO_SETUP_MENU_DYNAMIC_NAVIGATION_CORE_V1 = function setupMenuDynamicNavigationCoreV1(options) {
    const deps = options && typeof options === "object" ? options : {};
    const normalizeMenuKey = (
      typeof deps.normalizeMenuKey === "function"
        ? deps.normalizeMenuKey
        : defaultNormalizeMenuKeyV1
    );
    const toSentenceCaseText = (
      typeof deps.toSentenceCaseText === "function"
        ? deps.toSentenceCaseText
        : defaultToSentenceCaseTextV1
    );
    const buildProcessSections = (
      typeof deps.buildProcessSections === "function"
        ? deps.buildProcessSections
        : () => []
    );
    const buildMenuItemUniqueKeyV1 = (
      typeof deps.buildMenuItemUniqueKeyV1 === "function"
        ? deps.buildMenuItemUniqueKeyV1
        : createMenuItemUniqueKeyFallbackV1
    );
    const processSubprocessStandardsApiV1 = (
      typeof window !== "undefined" &&
      typeof window.APPVERBO_CREATE_PROCESS_SUBPROCESS_STANDARDS_API_V1 === "function"
    )
      ? window.APPVERBO_CREATE_PROCESS_SUBPROCESS_STANDARDS_API_V1()
      : null;
    const sidebarMenuSettings = Array.isArray(deps.sidebarMenuSettings) ? deps.sidebarMenuSettings : [];
    const visibleSidebarMenuKeys = (
      deps.visibleSidebarMenuKeys instanceof Set
        ? deps.visibleSidebarMenuKeys
        : new Set(
          (Array.isArray(deps.visibleSidebarMenuKeys) ? deps.visibleSidebarMenuKeys : [])
            .map((menuKey) => normalizeMenuKey(menuKey))
            .filter(Boolean)
        )
    );
    const menuConfig = (
      deps.menuConfig &&
      typeof deps.menuConfig === "object" &&
      !Array.isArray(deps.menuConfig)
    )
      ? deps.menuConfig
      : {};
    const menuProcessValuesMap = (
      deps.menuProcessValuesMap &&
      typeof deps.menuProcessValuesMap === "object" &&
      !Array.isArray(deps.menuProcessValuesMap)
    )
      ? deps.menuProcessValuesMap
      : {};
    const isEmpresaMenuKeyV1 = (menuKey) => normalizeMenuKey(menuKey) === "empresa";
    const dynamicProcessDataByMenu = (
      deps.dynamicProcessDataByMenu &&
      typeof deps.dynamicProcessDataByMenu === "object" &&
      !Array.isArray(deps.dynamicProcessDataByMenu)
    )
      ? deps.dynamicProcessDataByMenu
      : {};
    const selectedDynamicSectionByMenu = (
      deps.selectedDynamicSectionByMenu &&
      typeof deps.selectedDynamicSectionByMenu === "object" &&
      !Array.isArray(deps.selectedDynamicSectionByMenu)
    )
      ? deps.selectedDynamicSectionByMenu
      : {};
    const meuPerfilMenuKey = normalizeMenuKey(deps.MEU_PERFIL_MENU_KEY || "meu_perfil");
    const initialMenu = normalizeMenuKey(deps.initialMenu || "");
    const initialDynamicProcessSection = String(deps.initialDynamicProcessSection || "").trim();

    //###################################################################################
    // (2.1) RESOLVER PADROES DE TARGET E VISIBILIDADE
    //###################################################################################
    function resolveScopedTargetSelectorV1(menuKey, targetSelector) {
      if (
        processSubprocessStandardsApiV1 &&
        typeof processSubprocessStandardsApiV1.resolveStandardScopedTargetV1 === "function"
      ) {
        return processSubprocessStandardsApiV1.resolveStandardScopedTargetV1(menuKey, targetSelector, {
          normalizeMenuKey
        });
      }

      return String(targetSelector || "").trim();
    }

    function isScopedCardMatchV1(menuKey, targetSelector, cardId) {
      if (
        processSubprocessStandardsApiV1 &&
        typeof processSubprocessStandardsApiV1.isScopedCardMatchV1 === "function"
      ) {
        return processSubprocessStandardsApiV1.isScopedCardMatchV1(menuKey, targetSelector, cardId, {
          normalizeMenuKey
        });
      }

      const resolvedTargetSelector = resolveScopedTargetSelectorV1(menuKey, targetSelector);
      const cleanCardId = String(cardId || "").trim();
      if (!resolvedTargetSelector || !cleanCardId) {
        return false;
      }
      return resolvedTargetSelector === `#${cleanCardId}`;
    }

    //###################################################################################
    // (3) MERGE DOS MENUS DINAMICOS
    //###################################################################################
    function mergeDynamicProcessMenus() {
      sidebarMenuSettings.forEach((setting) => {
        const menuKey = normalizeMenuKey(setting && setting.key);
        if (!menuKey || menuKey === "perfil" || menuKey === meuPerfilMenuKey) {
          return;
        }
        if (visibleSidebarMenuKeys.size && !visibleSidebarMenuKeys.has(menuKey)) {
          return;
        }

        const cleanMenuLabel = toSentenceCaseText(setting && setting.label) || "Processo";
        const existingConfig = menuConfig[menuKey];
        const menuValuesByField = (
          menuProcessValuesMap &&
          typeof menuProcessValuesMap[menuKey] === "object" &&
          menuProcessValuesMap[menuKey] !== null
        )
          ? menuProcessValuesMap[menuKey]
          : {};
        const sections = buildProcessSections(setting, menuValuesByField);

        const isStandardProcess = menuKey === "administrativo" || menuKey === "sessoes";

        if (!sections.length && !isStandardProcess) {
          delete dynamicProcessDataByMenu[menuKey];
          delete selectedDynamicSectionByMenu[menuKey];
          if (existingConfig) {
            menuConfig[menuKey] = {
              ...existingConfig,
              items: []
            };
          } else {
            menuConfig[menuKey] = {
              title: cleanMenuLabel,
              description: "Campos configurados para este processo.",
              singleView: true,
              toggleOnMenuClick: true,
              items: [],
              details: [
                { label: "Modulo", value: cleanMenuLabel },
                { label: "Status", value: "Ativo" }
              ]
            };
          }
          return;
        }

        dynamicProcessDataByMenu[menuKey] = {
          menuLabel: cleanMenuLabel,
          sections
        };
        if (
          menuKey === initialMenu &&
          initialDynamicProcessSection &&
          sections.some((section) => String(section && section.key || "") === initialDynamicProcessSection)
        ) {
          selectedDynamicSectionByMenu[menuKey] = initialDynamicProcessSection;
        } else {
          selectedDynamicSectionByMenu[menuKey] = String(sections[0] && sections[0].key || "");
        }

        const dynamicItems = sections.map((section) => ({
          label: toSentenceCaseText(section && section.label || "Campos"),
          target: "#dynamic-process-card",
          dynamicProcessSectionKey: String(section && section.key || "__empty__")
        }));

        let finalItems = dynamicItems;
        if (menuKey === "administrativo" || menuKey === "sessoes") {
          const baseItems = (
            processSubprocessStandardsApiV1 &&
            typeof processSubprocessStandardsApiV1.getStandardSubprocessTabsV1 === "function"
          )
            ? processSubprocessStandardsApiV1.getStandardSubprocessTabsV1(menuKey, { normalizeMenuKey })
            : [
                { key: "entidade", label: "Entidade", target: "#create-entity-card" },
                { key: "utilizador", label: "Utilizador", target: "#create-user-card" },
                { label: "Sessões", target: "#admin-sidebar-sections-card" },
                { key: "menu", label: "Menu", target: "#admin-menu-card" },
                { label: "Definições", target: "#admin-definicoes-card" }
              ];
          const baseSectionKeys = (
            processSubprocessStandardsApiV1 &&
            typeof processSubprocessStandardsApiV1.getStandardSubprocessKeysV1 === "function"
          )
            ? new Set(processSubprocessStandardsApiV1.getStandardSubprocessKeysV1(menuKey, { normalizeMenuKey }))
            : new Set(["entidade", "utilizador", "sessoes", "menu", "definicoes"]);
          const normalizedBaseItems = baseItems.map((item) => {
            const cleanTarget = String(item && item.target || "").trim();
            let fallbackKey = "";

            if (cleanTarget === "#create-entity-card") {
              fallbackKey = "entidade";
            } else if (cleanTarget === "#create-user-card") {
              fallbackKey = "utilizador";
            } else if (cleanTarget === "#admin-sidebar-sections-card") {
              fallbackKey = "sessoes";
            } else if (cleanTarget === "#admin-menu-card") {
              fallbackKey = "menu";
            } else if (cleanTarget === "#admin-definicoes-card") {
              fallbackKey = "definicoes";
            }

            return {
              ...item,
              key: normalizeMenuKey(item && item.key || fallbackKey)
            };
          });
          const mergedItems = dynamicItems.filter((item) => {
            const sectionKey = String(item && item.dynamicProcessSectionKey || "").trim().toLowerCase();
            if (!sectionKey) {
              return false;
            }
            if (sectionKey === "__geral__" || sectionKey.startsWith("field:")) {
              return false;
            }
            return !baseSectionKeys.has(sectionKey);
          });
          const seenTargets = new Set(normalizedBaseItems.map((item) => buildMenuItemUniqueKeyV1(item)));
          const dynamicExtraItems = mergedItems.filter((item) => {
            const targetKey = buildMenuItemUniqueKeyV1(item);
            if (!targetKey || seenTargets.has(targetKey)) {
              return false;
            }
            seenTargets.add(targetKey);
            return true;
          });
          const trailingStandardKeysV1 = new Set(ADMINISTRATIVO_TRAILING_STANDARD_KEYS_V1);
          const leadingBaseItems = normalizedBaseItems.filter((item) => {
            const itemKey = normalizeMenuKey(item && item.key);
            return !trailingStandardKeysV1.has(itemKey);
          });
          const trailingBaseItems = normalizedBaseItems.filter((item) => {
            const itemKey = normalizeMenuKey(item && item.key);
            return trailingStandardKeysV1.has(itemKey);
          });
          
          finalItems = [...leadingBaseItems, ...dynamicExtraItems, ...trailingBaseItems];
        }

        if (existingConfig) {
          menuConfig[menuKey] = {
            ...existingConfig,
            items: finalItems
          };
          return;
        }

        menuConfig[menuKey] = {
          title: cleanMenuLabel,
          description: "Campos configurados para este processo.",
          singleView: true,
          toggleOnMenuClick: true,
          items: finalItems,
          details: [
            { label: "Modulo", value: cleanMenuLabel },
            { label: "Status", value: "Ativo" }
          ]
        };
      });
    }

    //###################################################################################
    // (4) CONTROLO DE VISIBILIDADE POR MENU/ALVO
    //###################################################################################
    function applyContentForMenu(menuKey) {
      const cards = resolveScopedCardsV1(deps);
      cards.forEach((card) => {
        const rawScope = card.getAttribute("data-menu-scope") || "";
        const scopes = rawScope.split(",").map((value) => normalizeMenuKey(value)).filter(Boolean);
        if (scopes.includes(menuKey)) {
          showElementV1(card);
          return;
        }
        hideElementV1(card);
      });

      hideElementV1(resolveElementByIdV1(deps, "dynamic-process-card"));
      const createCardEl = resolveElementByIdV1(deps, "dynamic-process-create-card");
      hideElementV1(createCardEl);
      if (createCardEl) {
        createCardEl.classList.remove("is-editing");
      }
      hideElementV1(resolveElementByIdV1(deps, "dynamic-process-history-active-card"));
      hideElementV1(resolveElementByIdV1(deps, "dynamic-process-history-inactive-card"));
    }

    function applyContentForMenuTarget(menuKey, targetSelector) {
      const resolvedTargetSelector = resolveScopedTargetSelectorV1(menuKey, targetSelector);

      const cards = resolveScopedCardsV1(deps);
      cards.forEach((card) => {
        const rawScope = card.getAttribute("data-menu-scope") || "";
        const scopes = rawScope.split(",").map((value) => normalizeMenuKey(value)).filter(Boolean);
        if (!scopes.includes(menuKey)) {
          hideElementV1(card);
          return;
        }

        if (isScopedCardMatchV1(menuKey, resolvedTargetSelector, card.id)) {
          showElementV1(card);
          return;
        }

        hideElementV1(card);
      });

      const dynamicCardEl = resolveElementByIdV1(deps, "dynamic-process-card");
      const createCardEl = resolveElementByIdV1(deps, "dynamic-process-create-card");
      const historyActiveCardEl = resolveElementByIdV1(deps, "dynamic-process-history-active-card");
      const historyInactiveCardEl = resolveElementByIdV1(deps, "dynamic-process-history-inactive-card");
      const shouldShowDynamicCardTarget = resolvedTargetSelector === "#dynamic-process-card";
      const shouldHideCreateCardForEmpresa = isEmpresaMenuKeyV1(menuKey);
      const shouldShowDynamicCard = (
        shouldShowDynamicCardTarget
      );
      const shouldShowCreateCard = (
        shouldShowDynamicCardTarget &&
        !shouldHideCreateCardForEmpresa
      );

      if (dynamicCardEl && dynamicCardEl.style) {
        dynamicCardEl.style.display = shouldShowDynamicCard ? "" : "none";
      }
      if (createCardEl && createCardEl.style) {
        createCardEl.style.display = shouldShowCreateCard ? "" : "none";
        if (!shouldShowCreateCard) {
          createCardEl.classList.remove("is-editing");
        }
      }
      if (!shouldShowDynamicCard) {
        hideElementV1(historyActiveCardEl);
        hideElementV1(historyInactiveCardEl);
      }
    }

    //###################################################################################
    // (5) SUBMENU
    //###################################################################################
    function clearSubmenuLinkStateV1(link) {
      if (!link) {
        return;
      }

      link.classList.remove("active");
      link.classList.remove("selected");
      link.classList.remove("is-active");
      link.setAttribute("aria-selected", "false");
      link.removeAttribute("data-active");
      link.removeAttribute("data-selected");
      link.removeAttribute("data-appverbo-force-active");
      link.removeAttribute("data-appverbo-menu-active");
      link.removeAttribute("data-appverbo-menu-inactive");
      link.setAttribute("data-appverbo-force-inactive", "true");
    }

    function markSubmenuLinkActiveStateV1(link) {
      if (!link) {
        return;
      }

      link.classList.add("active");
      link.classList.add("selected");
      link.classList.add("is-active");
      link.setAttribute("aria-selected", "true");
      link.setAttribute("data-active", "true");
      link.setAttribute("data-selected", "true");
      link.setAttribute("data-appverbo-force-active", "true");
      link.removeAttribute("data-appverbo-force-inactive");
      link.removeAttribute("data-appverbo-menu-inactive");
    }

    function clearSubmenuActiveLinks(links) {
      Array.from(links || []).forEach((link) => {
        clearSubmenuLinkStateV1(link);
      });
    }

    function setActiveSubmenu(targetSelector, selectedLinkEl = null, menuKey = null) {
      const itemsEl = resolveElementByIdV1(deps, "submenu-items");
      if (!itemsEl) {
        return;
      }
      const links = itemsEl.querySelectorAll(".submenu-item");
      clearSubmenuActiveLinks(links);
      if (selectedLinkEl) {
        markSubmenuLinkActiveStateV1(selectedLinkEl);
        return;
      }
      const activeKey = normalizeMenuKey(menuKey || deps.initialMenu || "");
      const resolvedTargetSelector = resolveScopedTargetSelectorV1(activeKey, targetSelector);
      const firstMatch = Array.from(links).find(
        (link) => {
          const href = link.getAttribute("href");
          return href === targetSelector || href === resolvedTargetSelector;
        }
      );
      if (firstMatch) {
        markSubmenuLinkActiveStateV1(firstMatch);
      }
    }

    window.mergeDynamicProcessMenus = mergeDynamicProcessMenus;
    window.applyContentForMenu = applyContentForMenu;
    window.applyContentForMenuTarget = applyContentForMenuTarget;
    window.clearSubmenuActiveLinks = clearSubmenuActiveLinks;
    window.setActiveSubmenu = setActiveSubmenu;
    window.__APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_READY = true;

    if (deps.forceMerge || !window.__APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_MERGED) {
      window.__APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_MERGED = true;
      mergeDynamicProcessMenus();
    }
  };
})();
// APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_MODULE_END
