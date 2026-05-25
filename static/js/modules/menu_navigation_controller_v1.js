//###################################################################################
// (1) MENU NAVIGATION CONTROLLER V1
//###################################################################################
(function registerMenuNavigationControllerV1() {
  "use strict";

  function createMenuNavigationControllerV1(context = {}) {
    function renderSubmenu(menuKey) {
      const config = context.menuConfig[menuKey];
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
        link.className = "submenu-item";
        link.href = item.target;
        link.textContent = context.toSentenceCaseText(item.label);
        if (item.profileSection) {
          link.dataset.profileSection = String(item.profileSection);
        }
        if (item.dynamicProcessSectionKey) {
          link.dataset.dynamicProcessSection = String(item.dynamicProcessSectionKey);
        }
        link.addEventListener("click", (event) => {
          event.preventDefault();

          if (menuKey === "administrativo" && item.target === "#admin-sidebar-sections-card") {
            const nextUrl = new URL("/users/new", window.location.origin);
            nextUrl.searchParams.set("menu", "administrativo");
            nextUrl.searchParams.set("admin_tab", "sessoes");
            nextUrl.searchParams.set("sidebar_sections_tab", "sessoes");
            nextUrl.searchParams.set("target", "admin-sidebar-sections-card");
            nextUrl.hash = "#admin-sidebar-sections-card";
            window.location.assign(nextUrl.pathname + nextUrl.search + nextUrl.hash);
            return;
          }
          if (menuKey === "administrativo" && item.target === "#admin-definicoes-card") {
            const nextUrl = new URL("/users/new", window.location.origin);
            nextUrl.searchParams.set("menu", "administrativo");
            nextUrl.searchParams.set("admin_tab", "definicoes");
            nextUrl.searchParams.set("target", "admin-definicoes-card");
            nextUrl.hash = "#admin-definicoes-card";
            window.location.assign(nextUrl.pathname + nextUrl.search + nextUrl.hash);
            return;
          }
          if (menuKey === "administrativo" && item.target === "#admin-menu-card") {
            const nextUrl = new URL("/users/new", window.location.origin);
            nextUrl.searchParams.set("menu", "administrativo");
            nextUrl.searchParams.set("admin_tab", "menu");
            nextUrl.searchParams.set("target", "admin-menu-card");
            nextUrl.hash = "#admin-menu-card";
            window.location.assign(nextUrl.pathname + nextUrl.search + nextUrl.hash);
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
        { forceFirstItem: resetDynamicToFirst }
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
          const selectedLinkEl = context.itemsEl.querySelector(
            `.submenu-item[data-dynamic-process-section="${selectedSectionKey.replace(/"/g, '\\"')}"]`
          );
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
        if (
          menuKey === context.MEU_PERFIL_MENU_KEY &&
          typeof window.activateProfilePersonalSection === "function"
        ) {
          let selectedSectionItem = menuItems.find(
            (item) => String(item.profileSection || "") === context.getMeuPerfilSelectedProfileSection()
          );
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

    function activateMenuTarget(menuKey, targetSelector) {
      const config = context.menuConfig[menuKey];
      if (!config) {
        return;
      }
      activateMenu(menuKey, { resetDynamicToFirst: false });
      if (!targetSelector) {
        return;
      }
      context.selectedTargetByMenu[menuKey] = targetSelector;
      context.setActiveSubmenu(targetSelector);
      context.applyContentForMenuTarget(menuKey, targetSelector);
      if (targetSelector === "#dynamic-process-card") {
        context.renderDynamicProcessCard(menuKey, context.selectedDynamicSectionByMenu[menuKey] || "");
      }
      const targetCard = document.querySelector(targetSelector);
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
      } else if (
        normalizedHash === "#admin-user-shadow-readonly-card" ||
        normalizedHash === "#admin-user-shadow-inactive-card" ||
        normalizedHash === "#admin-users-created-card" ||
        normalizedHash === "#inactive-users-card"
      ) {
        normalizedHash = "#create-user-card";
      } else if (normalizedHash === "#edit-entity-card") {
        normalizedHash = "#create-entity-card";
      } else if (normalizedHash === "#configuracao-account-status-card") {
        normalizedHash = "#admin-menu-card";
      } else if (
        normalizedHash === "#admin-definicoes-card-create" ||
        normalizedHash === "#admin-definicoes-card-inactive" ||
        normalizedHash === "#admin-definicoes-card-edit"
      ) {
        normalizedHash = "#admin-definicoes-card";
      }

      const hashTargetMenuMap = {
        "#create-user-card": "administrativo",
        "#create-entity-card": "administrativo",
        "#admin-subprocess-v2-entidade": "administrativo",
        "#admin-menu-card-create": "administrativo",
        "#admin-menu-card": "administrativo",
        "#admin-menu-card-inactive": "administrativo",
        "#admin-definicoes-card": "administrativo",
        "#admin-definicoes-card-create": "administrativo",
        "#admin-definicoes-card-inactive": "administrativo",
        "#admin-definicoes-card-edit": "administrativo",
        "#admin-sidebar-sections-card": "administrativo",
        "#settings-menu-edit-card": "administrativo"
      };
      const targetMenu = hashTargetMenuMap[normalizedHash];
      if (targetMenu) {
        activateMenuTarget(targetMenu, normalizedHash);
        if (cleanHash !== normalizedHash) {
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
