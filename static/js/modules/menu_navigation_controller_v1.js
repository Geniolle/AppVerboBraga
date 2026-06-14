//###################################################################################
// (1) MENU NAVIGATION CONTROLLER V1
//###################################################################################
(function registerMenuNavigationControllerV1() {
  "use strict";

  function createMenuNavigationControllerV1(context = {}) {
    const processSubprocessStandardsApiV1 = (
      typeof window !== "undefined" &&
      typeof window.APPVERBO_CREATE_PROCESS_SUBPROCESS_STANDARDS_API_V1 === "function"
    )
      ? window.APPVERBO_CREATE_PROCESS_SUBPROCESS_STANDARDS_API_V1()
      : null;
    const standardSubprocessTargetMapCacheV1 = new Map();

    function getStandardSubprocessTargetMap(menuKey) {
      const cleanMenuKey = context.normalizeMenuKey(menuKey);
      if (!cleanMenuKey) {
        return new Map();
      }
      if (standardSubprocessTargetMapCacheV1.has(cleanMenuKey)) {
        return standardSubprocessTargetMapCacheV1.get(cleanMenuKey);
      }
      const map = (
        processSubprocessStandardsApiV1 &&
        typeof processSubprocessStandardsApiV1.getStandardSubprocessTargetMapV1 === "function"
      )
        ? processSubprocessStandardsApiV1.getStandardSubprocessTargetMapV1(cleanMenuKey, {
            normalizeMenuKey: context.normalizeMenuKey
          })
        : new Map();
      standardSubprocessTargetMapCacheV1.set(cleanMenuKey, map);
      return map;
    }

    function resolveStandardSubprocessItem(menuKey, item) {
      if (item && item.route) {
        return item;
      }
      const cleanTarget = String(item && item.target || "").trim();
      if (!cleanTarget) {
        return null;
      }
      const map = getStandardSubprocessTargetMap(menuKey);
      return map.get(cleanTarget) || null;
    }

    function navigateToStandardSubprocessRoute(menuKey, item) {
      if (
        !processSubprocessStandardsApiV1 ||
        typeof processSubprocessStandardsApiV1.resolveSubprocessNavigationUrlV1 !== "function"
      ) {
        return false;
      }
      const standardItem = resolveStandardSubprocessItem(menuKey, item);
      if (!standardItem || !standardItem.route) {
        return false;
      }

      const nextUrl = processSubprocessStandardsApiV1.resolveSubprocessNavigationUrlV1(menuKey, standardItem, {
        baseHref: window.location.href,
        pathname: "/users/new",
        normalizeMenuKey: context.normalizeMenuKey
      });
      if (!nextUrl) {
        return false;
      }

      window.location.assign(nextUrl);
      return true;
    }

    function resolveProcessTitle(menuKey, config) {
      if (typeof context.resolveMenuProcessTitleLabel === "function") {
        const resolvedLabel = context.resolveMenuProcessTitleLabel(
          menuKey,
          String((config && config.title) || "")
        );
        if (String(resolvedLabel || "").trim()) {
          return String(resolvedLabel).trim();
        }
      }

      const configTitle = String((config && config.title) || "").trim();
      if (configTitle) {
        return context.toSentenceCaseText(configTitle);
      }

      return context.toSentenceCaseText(String(menuKey || ""));
    }

    function updateSubmenuProcessTitle(menuKey, config) {
      if (typeof context.updateSubmenuProcessTitle !== "function") {
        return;
      }
      context.updateSubmenuProcessTitle(menuKey, resolveProcessTitle(menuKey, config));
    }

    function escapeSelectorValueV1(value) {
      const cleanValue = String(value || "");
      if (typeof window !== "undefined" && window.CSS && typeof window.CSS.escape === "function") {
        return window.CSS.escape(cleanValue);
      }
      return cleanValue.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
    }

    function resolveDynamicSectionLinkElementV1(sectionKey) {
      if (!context.itemsEl) {
        return null;
      }
      const cleanSectionKey = String(sectionKey || "").trim();
      if (!cleanSectionKey) {
        return null;
      }
      return context.itemsEl.querySelector(
        `.submenu-item[data-dynamic-process-section="${escapeSelectorValueV1(cleanSectionKey)}"]`
      );
    }

    function renderSubmenu(menuKey) {
      const config = context.menuConfig[menuKey];
      updateSubmenuProcessTitle(menuKey, config);
      if (!config || !context.itemsEl) {
        return;
      }

      const menuItems = Array.isArray(config.items) ? config.items : [];
      const shouldHideSingleDynamicSubmenu = (
        menuItems.length === 1 &&
        String(menuItems[0] && menuItems[0].target || "") === "#dynamic-process-card" &&
        Boolean(menuItems[0] && menuItems[0].dynamicProcessSectionKey)
      );

      if (typeof document !== "undefined" && document.body) {
        document.body.classList.toggle("appverbo-hide-submenu-tabs-v1", shouldHideSingleDynamicSubmenu);
      }
      if (context.menuTabsCardEl) {
        context.menuTabsCardEl.style.display = shouldHideSingleDynamicSubmenu ? "none" : "";
      }

      context.itemsEl.innerHTML = "";
      context.itemsEl.style.display = shouldHideSingleDynamicSubmenu ? "none" : "flex";

      menuItems.forEach((item) => {
        const link = document.createElement("a");
        const standardItem = resolveStandardSubprocessItem(menuKey, item);
        const routeConfig = (
          standardItem &&
          standardItem.route &&
          typeof standardItem.route === "object"
        )
          ? standardItem.route
          : null;
        link.className = "submenu-item";
        link.href = item.target;
        link.textContent = context.toSentenceCaseText(item.label);
        if (standardItem && standardItem.key) {
          link.dataset.tab = String(standardItem.key);
          link.dataset.adminTab = String(standardItem.key);
          link.dataset.appverboSubprocessTab = String(standardItem.key);
        }
        if (routeConfig && routeConfig.adminTab) {
          link.dataset.adminTab = String(routeConfig.adminTab);
        }
        if (item.profileSection) {
          link.dataset.profileSection = String(item.profileSection);
        }
        if (item.dynamicProcessSectionKey) {
          link.dataset.dynamicProcessSection = String(item.dynamicProcessSectionKey);
        }
        link.addEventListener("click", (event) => {
          event.preventDefault();

          if (navigateToStandardSubprocessRoute(menuKey, item)) {
            return;
          }

          context.closeAllProfileEdits();
          context.selectedTargetByMenu[menuKey] = item.target;
          context.setActiveSubmenu(item.target, link);
          context.applyContentForMenuTarget(menuKey, item.target);
          if (item.dynamicProcessSectionKey) {
            context.selectedDynamicSectionByMenu[menuKey] = String(item.dynamicProcessSectionKey);
            context.renderDynamicProcessCard(menuKey, item.dynamicProcessSectionKey);
          }
          if (
            menuKey === context.MEU_PERFIL_MENU_KEY &&
            typeof window.activateProfilePersonalSection === "function"
          ) {
            const sectionKey = String(item.profileSection || "");
            context.setMeuPerfilSelectedProfileSection(sectionKey);
            window.activateProfilePersonalSection(sectionKey);
            context.applyMeuPerfilProcessSubsequentVisibility();
          }
        });
        context.itemsEl.appendChild(link);
      });

      if (typeof window.setTimeout === "function") {
        window.setTimeout(() => {
          const event = new CustomEvent("appverbo:normalize-tabs-width-v1");
          window.dispatchEvent(event);
        }, 0);
      }
    }

    function getDefaultTargetForMenu(menuKey, config, options = {}) {
      const { forceFirstItem = false } = options;
      if (!Array.isArray(config.items) || !config.items.length) {
        const savedTarget = context.selectedTargetByMenu[menuKey];
        if (savedTarget === "#settings-menu-edit-card") {
          const settingsCardEl = document.querySelector(savedTarget);
          if (settingsCardEl) {
            return savedTarget;
          }
        }
        return "";
      }
      if (forceFirstItem) {
        return config.items[0].target;
      }
      const savedTarget = context.selectedTargetByMenu[menuKey];
      if (savedTarget) {
        if (config.items.some((item) => item.target === savedTarget)) {
          return savedTarget;
        }
        if (savedTarget === "#settings-menu-edit-card") {
          const settingsCardEl = document.querySelector(savedTarget);
          if (settingsCardEl) {
            return savedTarget;
          }
        }
      }
      return config.items[0].target;
    }

    function activateMenu(menuKey, options = {}) {
      const config = context.menuConfig[menuKey];
      if (!config) {
        return;
      }
      const { resetDynamicToFirst = false } = options;
      const forceFirstItem = Boolean(resetDynamicToFirst);
      const targetButton = Array.from(context.menuButtons).find((btn) => context.normalizeMenuKey(btn.dataset.menu) === menuKey);
      const menuItems = Array.isArray(config.items) ? config.items : [];
      if (resetDynamicToFirst) {
        const firstDynamicItem = menuItems.find((item) => item.dynamicProcessSectionKey);
        if (firstDynamicItem) {
          context.selectedDynamicSectionByMenu[menuKey] = String(
            firstDynamicItem.dynamicProcessSectionKey || ""
          );
        }
      }

      context.closeAllProfileEdits();
      context.setActiveMenuKey(menuKey);
      context.menuButtons.forEach((item) => item.classList.remove("active"));
      if (targetButton) {
        targetButton.classList.add("active");
      }
      renderSubmenu(menuKey);

      const defaultTarget = getDefaultTargetForMenu(
        menuKey,
        config,
        { forceFirstItem }
      );
      if (defaultTarget) {
        const savedDynamicSectionKey = String(context.selectedDynamicSectionByMenu[menuKey] || "");
        let selectedDynamicItem = null;
        if (defaultTarget === "#dynamic-process-card") {
          selectedDynamicItem = menuItems.find(
            (item) => String(item.dynamicProcessSectionKey || "") === savedDynamicSectionKey
          );
          if (!selectedDynamicItem) {
            selectedDynamicItem = menuItems.find((item) => item.target === "#dynamic-process-card") || null;
          }
        }

        context.selectedTargetByMenu[menuKey] = defaultTarget;
        if (selectedDynamicItem && context.itemsEl) {
          const selectedSectionKey = String(selectedDynamicItem.dynamicProcessSectionKey || "");
          const selectedLinkEl = resolveDynamicSectionLinkElementV1(selectedSectionKey);
          if (selectedLinkEl) {
            context.setActiveSubmenu(defaultTarget, selectedLinkEl);
          } else {
            context.setActiveSubmenu(defaultTarget);
          }
          context.selectedDynamicSectionByMenu[menuKey] = selectedSectionKey;
          context.renderDynamicProcessCard(menuKey, selectedSectionKey);
        } else {
          context.setActiveSubmenu(defaultTarget);
        }
        context.applyContentForMenuTarget(menuKey, defaultTarget);
        if (defaultTarget === "#dynamic-process-card") {
          const dynamicCard =
            typeof document !== "undefined"
              ? document.getElementById("dynamic-process-card")
              : null;
          if (dynamicCard) {
            dynamicCard.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        }
        if (
          menuKey === context.MEU_PERFIL_MENU_KEY &&
          typeof window.activateProfilePersonalSection === "function"
        ) {
          let selectedSectionItem = null;
          if (forceFirstItem) {
            selectedSectionItem = menuItems.find(
              (item) => String(item.target || "") === String(defaultTarget || "")
            ) || menuItems[0];
          } else {
            selectedSectionItem = menuItems.find(
              (item) => String(item.profileSection || "") === context.getMeuPerfilSelectedProfileSection()
            );
          }
          if (!selectedSectionItem) {
            selectedSectionItem = menuItems.find((item) => item.target === defaultTarget) || menuItems[0];
          }
          if (selectedSectionItem) {
            const selectedSectionKey = String(selectedSectionItem.profileSection || "");
            context.setMeuPerfilSelectedProfileSection(selectedSectionKey);
            window.activateProfilePersonalSection(selectedSectionKey);
            context.applyMeuPerfilProcessSubsequentVisibility();
            const selectedLinkEl = context.itemsEl
              ? context.itemsEl.querySelector(
                `.submenu-item[data-profile-section="${selectedSectionKey.replace(/"/g, '\\"')}"]`
              )
              : null;
            if (selectedLinkEl) {
              context.setActiveSubmenu(defaultTarget, selectedLinkEl);
            }
          }
        }
        return;
      }
      context.applyContentForMenu(menuKey);
      context.setActiveSubmenu("");
    }

    function activateMenuTarget(menuKey, targetSelector, options = {}) {
      const config = context.menuConfig[menuKey];
      if (!config) {
        return;
      }
      activateMenu(menuKey, { resetDynamicToFirst: false });
      if (!targetSelector) {
        return;
      }
      context.selectedTargetByMenu[menuKey] = targetSelector;
      if (targetSelector === "#dynamic-process-card") {
        const selectedLinkEl = resolveDynamicSectionLinkElementV1(
          context.selectedDynamicSectionByMenu[menuKey] || ""
        );
        if (selectedLinkEl) {
          context.setActiveSubmenu(targetSelector, selectedLinkEl, menuKey);
        } else {
          context.setActiveSubmenu(targetSelector, null, menuKey);
        }
      } else {
        context.setActiveSubmenu(targetSelector, null, menuKey);
      }
      context.applyContentForMenuTarget(menuKey, targetSelector);
      if (targetSelector === "#dynamic-process-card") {
        context.renderDynamicProcessCard(menuKey, context.selectedDynamicSectionByMenu[menuKey] || "");
      }
      if (!options.preventScroll) {
        const targetCard = document.querySelector(targetSelector);
        if (targetCard) {
          targetCard.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    }

    function handleHashNavigation(rawHash) {
      const cleanHash = String(rawHash || "").trim();
      if (!cleanHash) {
        return;
      }
      if (
        !processSubprocessStandardsApiV1 ||
        typeof processSubprocessStandardsApiV1.resolveStandardMenuByHashTargetV1 !== "function"
      ) {
        return;
      }

      let normalizedHash = cleanHash;
      const resolvedHashTarget = processSubprocessStandardsApiV1.resolveStandardMenuByHashTargetV1(cleanHash, {
        normalizeMenuKey: context.normalizeMenuKey
      });
      normalizedHash = String(resolvedHashTarget && resolvedHashTarget.targetSelector || "").trim() || cleanHash;
      const targetMenu = String(resolvedHashTarget && resolvedHashTarget.menuKey || "").trim();

      if (targetMenu) {
        const hasDifferentScrollTarget = (cleanHash !== normalizedHash);
        activateMenuTarget(targetMenu, normalizedHash, { preventScroll: hasDifferentScrollTarget });
        if (hasDifferentScrollTarget) {
          try {
            const scrollTarget = document.querySelector(cleanHash);
            if (scrollTarget) {
              scrollTarget.scrollIntoView({ behavior: "smooth", block: "start" });
            }
          } catch (_error) {
          }
        }
      }
    }

    return {
      renderSubmenu,
      getDefaultTargetForMenu,
      activateMenu,
      activateMenuTarget,
      handleHashNavigation
    };
  }

  window.APPVERBO_CREATE_MENU_NAVIGATION_CONTROLLER_V1 = createMenuNavigationControllerV1;
})();
