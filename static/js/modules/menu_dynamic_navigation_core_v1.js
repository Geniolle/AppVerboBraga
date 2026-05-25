// APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_MODULE_START
(function registerMenuDynamicNavigationCoreV1Module() {
  "use strict";

  window.APPVERBO_SETUP_MENU_DYNAMIC_NAVIGATION_CORE_V1 = function setupMenuDynamicNavigationCoreV1(options) {
    const deps = options && typeof options === "object" ? options : {};

    if (!window.__APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_READY) {
function mergeDynamicProcessMenus() {
  sidebarMenuSettings.forEach((setting) => {
    const menuKey = normalizeMenuKey(setting.key);
    if (!menuKey || menuKey === "perfil") {
      return;
    }
    if (menuKey === MEU_PERFIL_MENU_KEY) {
      return;
    }
    if (visibleSidebarMenuKeys.size && !visibleSidebarMenuKeys.has(menuKey)) {
      return;
    }

    const cleanMenuLabel = toSentenceCaseText(setting.label) || "Processo";
    const existingConfig = menuConfig[menuKey];

    const menuValuesByField = (
      menuProcessValuesMap &&
      typeof menuProcessValuesMap[menuKey] === "object" &&
      menuProcessValuesMap[menuKey] !== null
    )
      ? menuProcessValuesMap[menuKey]
      : {};
    let sections = buildProcessSections(setting, menuValuesByField);
    if (!sections.length) {
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
      menuKey === normalizeMenuKey(initialMenu) &&
      initialDynamicProcessSection &&
      sections.some((section) => String(section.key || "") === String(initialDynamicProcessSection))
    ) {
      selectedDynamicSectionByMenu[menuKey] = String(initialDynamicProcessSection);
    } else {
      selectedDynamicSectionByMenu[menuKey] = sections[0].key;
    }

    const dynamicItems = sections.map((section) => ({
      label: toSentenceCaseText(section.label || "Campos"),
      target: "#dynamic-process-card",
      dynamicProcessSectionKey: String(section.key || "__empty__")
    }));
    if (existingConfig) {
      if (menuKey === "administrativo") {
        const baseItems = [
          { label: "Entidade", target: "#create-entity-card" },
          { label: "Utilizador", target: "#create-user-card" },
          { label: "Sessões", target: "#admin-sidebar-sections-card" },
          { label: "Menu", target: "#admin-menu-card" },
          { label: "Definições", target: "#admin-definicoes-card" }
        ];
        const mergedItems = dynamicItems.filter((item) => {
          const sectionKey = String(item.dynamicProcessSectionKey || "").trim().toLowerCase();
          if (!sectionKey) {
            return false;
          }
          if (sectionKey === "__geral__" || sectionKey.startsWith("field:")) {
            return false;
          }
          return !["entidade", "utilizador", "sessoes", "menu", "definicoes"].includes(sectionKey);
        });
        const seenTargets = new Set(baseItems.map((item) => buildMenuItemUniqueKey_v1(item)));
        const dynamicExtraItems = mergedItems.filter((item) => {
          const targetKey = buildMenuItemUniqueKey_v1(item);
          if (!targetKey || seenTargets.has(targetKey)) {
            return false;
          }
          seenTargets.add(targetKey);
          return true;
        });
        const resolvedItems = [...baseItems, ...dynamicExtraItems];
        menuConfig[menuKey] = {
          ...existingConfig,
          items: resolvedItems
        };
        return;
      }
      menuConfig[menuKey] = {
        ...existingConfig,
        items: dynamicItems
      };
      return;
    }
    menuConfig[menuKey] = {
      title: cleanMenuLabel,
      description: "Campos configurados para este processo.",
      singleView: true,
      toggleOnMenuClick: true,
      items: dynamicItems,
      details: [
        { label: "Modulo", value: cleanMenuLabel },
        { label: "Status", value: "Ativo" }
      ]
    };
  });
}

function applyContentForMenu(menuKey) {
  function showScopedCard(card) {
    if (!card || !card.style) {
      return;
    }

    card.style.removeProperty("display");
  }

  function hideScopedCard(card) {
    if (!card || !card.style) {
      return;
    }

    card.style.setProperty("display", "none", "important");
  }

  scopedCards.forEach((card) => {
    const rawScope = card.getAttribute("data-menu-scope") || "";
    const scopes = rawScope.split(",").map((value) => normalizeMenuKey(value)).filter(Boolean);

    if (scopes.includes(menuKey)) {
      showScopedCard(card);
      return;
    }

    hideScopedCard(card);
  });
  if (dynamicProcessCardEl) {
    dynamicProcessCardEl.style.display = "none";
  }
  if (dynamicProcessCreateCardEl) {
    dynamicProcessCreateCardEl.style.display = "none";
    dynamicProcessCreateCardEl.classList.remove("is-editing");
  }
  if (dynamicProcessHistoryActiveCardEl) {
    dynamicProcessHistoryActiveCardEl.style.display = "none";
  }
  if (dynamicProcessHistoryInactiveCardEl) {
    dynamicProcessHistoryInactiveCardEl.style.display = "none";
  }
}

function applyContentForMenuTarget(menuKey, targetSelector) {
  function showScopedCard(cardElement) {
    if (!cardElement || !cardElement.style) {
      return;
    }

    cardElement.style.removeProperty("display");
  }

  function hideScopedCard(cardElement) {
    if (!cardElement || !cardElement.style) {
      return;
    }

    cardElement.style.setProperty("display", "none", "important");
  }

  let resolvedTargetSelector = String(targetSelector || "");

  if (menuKey === "administrativo") {
    if (
      resolvedTargetSelector === "#admin-menu-form" ||
      resolvedTargetSelector === "#admin-menu-create-card"
    ) {
      resolvedTargetSelector = "#admin-menu-card";
    }
  }

  scopedCards.forEach((card) => {
    const rawScope = card.getAttribute("data-menu-scope") || "";
    const scopes = rawScope.split(",").map((value) => normalizeMenuKey(value)).filter(Boolean);
    if (!scopes.includes(menuKey)) {
      hideScopedCard(card);
      return;
    }
    const isEntityGroupedBlock =
      menuKey === "administrativo" &&
      (
        targetSelector === "#create-entity-card" ||
        targetSelector === "#admin-subprocess-v2-entidade"
      ) &&
      (
        card.id === "create-entity-card" ||
        card.id === "edit-entity-card" ||
        card.id === "recent-entities-card" ||
        card.id === "inactive-entities-card" ||
        card.id === "admin-entidade-v2-integrated-root"
      );
    const isUserGroupedBlock =
      menuKey === "administrativo" &&
      targetSelector === "#create-user-card" &&
      (
        card.id === "create-user-card" ||
        card.id === "edit-user-card" ||
        card.id === "admin-user-shadow-readonly-card" ||
        card.id === "admin-user-shadow-inactive-card" ||
        card.id === "admin-users-created-card" ||
        card.id === "inactive-users-card"
      );
    const isMenuGroupedBlock =
      menuKey === "administrativo" &&
      (
        (
          (
            resolvedTargetSelector === "#admin-menu-card" ||
            resolvedTargetSelector === "#admin-menu-card-inactive" ||
            resolvedTargetSelector === "#admin-menu-card-create" ||
            resolvedTargetSelector === "#settings-menu-edit-card"
          ) &&
          (
            card.id === "admin-menu-card-create" ||
            card.id === "admin-menu-card" ||
            card.id === "admin-menu-card-inactive"
          )
        )
      );
    const isDefinicoesGroupedBlock =
      menuKey === "administrativo" &&
      (
        resolvedTargetSelector === "#admin-definicoes-card" ||
        resolvedTargetSelector === "#admin-definicoes-card-create" ||
        resolvedTargetSelector === "#admin-definicoes-card-inactive" ||
        resolvedTargetSelector === "#admin-definicoes-card-edit"
      ) &&
      (
        card.id === "admin-definicoes-card" ||
        card.id === "admin-definicoes-card-create" ||
        card.id === "admin-definicoes-card-inactive" ||
        card.id === "admin-definicoes-card-edit"
      );
    if (
      resolvedTargetSelector === ("#" + card.id) ||
      isEntityGroupedBlock ||
      isUserGroupedBlock ||
      isMenuGroupedBlock ||
      isDefinicoesGroupedBlock
    ) {
      showScopedCard(card);
      return;
    }

    hideScopedCard(card);
  });
  if (dynamicProcessCardEl) {
    dynamicProcessCardEl.style.display = resolvedTargetSelector === "#dynamic-process-card" ? "" : "none";
  }
  if (dynamicProcessCreateCardEl) {
    dynamicProcessCreateCardEl.style.display = resolvedTargetSelector === "#dynamic-process-card" ? "" : "none";
    if (resolvedTargetSelector !== "#dynamic-process-card") {
      dynamicProcessCreateCardEl.classList.remove("is-editing");
    }
  }
  if (resolvedTargetSelector !== "#dynamic-process-card") {
    if (dynamicProcessHistoryActiveCardEl) {
      dynamicProcessHistoryActiveCardEl.style.display = "none";
    }
    if (dynamicProcessHistoryInactiveCardEl) {
      dynamicProcessHistoryInactiveCardEl.style.display = "none";
    }
  }
}

function clearSubmenuActiveLinks(links) {
  links.forEach((link) => {
    link.classList.remove("active");
  });
}

function setActiveSubmenu(targetSelector, selectedLinkEl = null) {
  if (!itemsEl) {
    return;
  }
  const links = itemsEl.querySelectorAll(".submenu-item");
  clearSubmenuActiveLinks(links);
  if (selectedLinkEl) {
    selectedLinkEl.classList.add("active");
    return;
  }
  const firstMatch = Array.from(links).find(
    (link) => link.getAttribute("href") === targetSelector
  );
  if (firstMatch) {
    firstMatch.classList.add("active");
  }
}

      window.mergeDynamicProcessMenus = mergeDynamicProcessMenus;
      window.applyContentForMenu = applyContentForMenu;
      window.applyContentForMenuTarget = applyContentForMenuTarget;
      window.clearSubmenuActiveLinks = clearSubmenuActiveLinks;
      window.setActiveSubmenu = setActiveSubmenu;
      window.__APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_READY = true;
    }

    if (!window.__APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_MERGED) {
      window.__APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_MERGED = true;
      mergeDynamicProcessMenus();
    }
  };
})();
// APPVERBO_MENU_DYNAMIC_NAVIGATION_CORE_V1_MODULE_END
