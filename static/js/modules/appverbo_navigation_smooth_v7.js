// APPVERBO_NAVIGATION_SMOOTH_V7_START
//###################################################################################
// (1) FUNCOES BASE
//###################################################################################

(function () {
  "use strict";

  let clearActiveTimerV7 = null;
  let stableTimerV7 = null;

  const ADMIN_TAB_CLASSES_V7 = [
    "appverbo-admin-tab-entidade",
    "appverbo-admin-tab-utilizador",
    "appverbo-admin-tab-sessoes",
    "appverbo-admin-tab-menu",
    "appverbo-admin-tab-definicoes",
    "appverbo-admin-tab-contas"
  ];

  function getCurrentUrlV7() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function cleanValueV7(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeTargetSelectorV7(value) {
    const cleanValue = String(value || "").trim();
    if (!cleanValue) {
      return "";
    }
    return cleanValue.startsWith("#") ? cleanValue : `#${cleanValue}`;
  }

  function escapeSelectorValueV7(value) {
    const cleanValue = String(value || "");
    if (typeof window !== "undefined" && window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(cleanValue);
    }
    return cleanValue.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  }

  function normalizeLookupTextV7(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ");
  }

  function markReadyV7() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");
  }

  function setDisplayV7(element, value) {
    if (!element || !element.style) {
      return;
    }

    element.style.setProperty("display", value, "important");
  }

  function showElementV7(element) {
    if (!element || !element.style) {
      return;
    }

    element.removeAttribute("hidden");
    element.style.setProperty("display", "block", "important");
    element.style.setProperty("visibility", "visible", "important");
    element.style.setProperty("opacity", "1", "important");
  }

  function hideElementV7(element) {
    if (!element || !element.style) {
      return;
    }

    element.style.setProperty("display", "none", "important");
  }

  //###################################################################################
  // (2) DETETAR ESTADO
  //###################################################################################

  function urlIndicaAdminV7(url) {
    if (!url || url.pathname !== "/users/new") {
      return false;
    }
    const menu = cleanValueV7(url.searchParams.get("menu"));
    return menu === "administrativo" || menu === "sessoes";
  }

  function getActiveSidebarMenuKeyV7() {
    if (typeof document === "undefined") {
      return "";
    }
    const activeMenuButton = document.querySelector("button.menu-item.active[data-menu], .menu-item.active[data-menu]");
    if (!activeMenuButton) {
      return "";
    }
    return cleanValueV7(activeMenuButton.getAttribute("data-menu"));
  }

  function getAdminTabFromUrlV7(url) {
    if (!urlIndicaAdminV7(url)) {
      return "";
    }

    const dynamicProcessContext = resolveAdminDynamicProcessContextFromUrlV7(url);
    if (
      dynamicProcessContext.hasDynamicProcessContext &&
      (
        !dynamicProcessContext.targetSelector ||
        dynamicProcessContext.targetSelector === "#dynamic-process-card"
      )
    ) {
      return "definicoes";
    }

    const adminTab = cleanValueV7(url.searchParams.get("admin_tab"));
    const target = cleanValueV7(url.searchParams.get("target"));
    const hash = cleanValueV7((url.hash || "").replace(/^#/, ""));
    const settingsTab = cleanValueV7(url.searchParams.get("settings_tab")).replace(/_/g, "-");
    const sidebarSectionsTab = cleanValueV7(url.searchParams.get("sidebar_sections_tab")).replace(/_/g, "-");
    const sidebarSectionEditKey = cleanValueV7(url.searchParams.get("sidebar_section_edit_key"));

    if (adminTab === "entidade" || target.includes("entity") || target.includes("entidade")) {
      return "entidade";
    }

    if (adminTab === "utilizador" || target.includes("user") || target.includes("utilizador")) {
      return "utilizador";
    }

    if (
      adminTab === "sessoes" ||
      settingsTab === "sessoes" ||
      settingsTab === "sessoes-sidebar" ||
      sidebarSectionsTab === "sessoes" ||
      sidebarSectionsTab === "sessoes-sidebar" ||
      sidebarSectionEditKey !== "" ||
      target.includes("admin-sidebar-sections") ||
      target.includes("sidebar-sections") ||
      hash.includes("admin-sidebar-sections") ||
      hash.includes("sidebar-sections")
    ) {
      return "sessoes";
    }

    if (
      adminTab === "menu" ||
      target.includes("admin-menu-card") ||
      target.includes("settings-menu-edit-card") ||
      hash.includes("admin-menu-card") ||
      hash.includes("settings-menu-edit-card")
    ) {
      return "menu";
    }

    if (
      adminTab === "definicoes" ||
      target.includes("admin-definicoes-card") ||
      hash.includes("admin-definicoes-card")
    ) {
      return "definicoes";
    }

    if (
      adminTab === "contas" ||
      target.includes("admin-account-status") ||
      hash.includes("admin-account-status")
    ) {
      return "contas";
    }

    return "";
  }

  function urlIndicaAdminProcessOnlyV7(url) {
    if (!urlIndicaAdminV7(url)) {
      return false;
    }

    return getAdminTabFromUrlV7(url) === "";
  }

  function resolveAdminDynamicProcessContextFromUrlV7(url) {
    if (!urlIndicaAdminV7(url)) {
      return {
        targetSelector: "",
        dynamicSectionKey: "",
        hasDynamicProcessContext: false
      };
    }

    const targetSelector = normalizeTargetSelectorV7(url.searchParams.get("target"));
    const dynamicSectionKey = cleanValueV7(
      url.searchParams.get("dynamic_process_section") ||
      url.searchParams.get("section_key")
    );
    const hasExplicitNonDynamicTarget = Boolean(
      targetSelector && targetSelector !== "#dynamic-process-card"
    );
    const hasDynamicProcessContext = Boolean(
      dynamicSectionKey &&
      (
        targetSelector === "#dynamic-process-card" ||
        !hasExplicitNonDynamicTarget
      )
    );

    return {
      targetSelector,
      dynamicSectionKey: hasDynamicProcessContext ? dynamicSectionKey : "",
      hasDynamicProcessContext
    };
  }

  function getDynamicProcessSectionFromUrlV7(url) {
    return resolveAdminDynamicProcessContextFromUrlV7(url).dynamicSectionKey;
  }

  function clearAdminNavigationParamsV7(url, options = {}) {
    if (!url || !url.searchParams) {
      return;
    }

    const { includeDynamicProcess = false } = options;

    [
      "admin_tab",
      "target",
      "sidebar_sections_tab",
      "sidebar_section_edit_key",
      "entity_edit_id",
      "entity_view",
      "user_edit_id",
      "user_view",
      "definition_edit_id",
      "settings_edit_key",
      "settings_action",
      "settings_tab",
      "settings_success",
      "settings_error",
      "profile_success",
      "profile_error",
      "success",
      "error",
      "appverbo_after_save"
    ].forEach(function (paramName) {
      url.searchParams.delete(paramName);
    });

    if (includeDynamicProcess) {
      url.searchParams.delete("dynamic_process_section");
      url.searchParams.delete("section_key");
    }
  }

  //###################################################################################
  // (3) MENU SUPERIOR ESTAVEL
  //###################################################################################

  function manterMenuSubprocessosVisivelV7() {
    const menuTabsCard = document.getElementById("menu-tabs-card");

    if (!menuTabsCard) {
      return;
    }

    menuTabsCard.style.setProperty("display", "block", "important");
    menuTabsCard.style.setProperty("visibility", "visible", "important");
    menuTabsCard.style.setProperty("opacity", "1", "important");
    menuTabsCard.style.setProperty("transition", "none", "important");
  }

  function marcarMenuEstavelV7() {
    if (!document.body) {
      return;
    }

    document.body.classList.add("appverbo-admin-submenu-stable");
    document.body.classList.add("appverbo-admin-submenu-switching");
    manterMenuSubprocessosVisivelV7();

    if (stableTimerV7) {
      window.clearTimeout(stableTimerV7);
    }

    stableTimerV7 = window.setTimeout(function () {
      if (document.body) {
        document.body.classList.remove("appverbo-admin-submenu-switching");
      }

      manterMenuSubprocessosVisivelV7();
      stableTimerV7 = null;
    }, 220);
  }

  //###################################################################################
  // (4) ABAS ATIVAS
  //###################################################################################

  function getTabFromElementV7(element) {
    if (!element) {
      return "";
    }

    const rawAdminTab = cleanValueV7(
      element.getAttribute("data-admin-tab") ||
      element.getAttribute("data-tab") ||
      element.getAttribute("data-admin-target") ||
      element.getAttribute("data-appverbo-subprocess-tab") ||
      ""
    );

    if (rawAdminTab === "entidade") {
      return "entidade";
    }

    if (rawAdminTab === "utilizador") {
      return "utilizador";
    }

    if (rawAdminTab === "sessoes") {
      return "sessoes";
    }

    if (rawAdminTab === "menu") {
      return "menu";
    }

    if (rawAdminTab === "definicoes") {
      return "definicoes";
    }

    if (rawAdminTab === "contas") {
      return "contas";
    }

    const rawTarget = cleanValueV7(
      element.getAttribute("data-target") ||
      element.getAttribute("data-menu-target") ||
      element.getAttribute("aria-controls") ||
      ""
    ).replace(/^#/, "");

    if (rawTarget.includes("entity") || rawTarget.includes("entidade")) {
      return "entidade";
    }

    if (rawTarget.includes("user") || rawTarget.includes("utilizador")) {
      return "utilizador";
    }

    if (rawTarget.includes("sidebar-sections") || rawTarget.includes("sessoes")) {
      return "sessoes";
    }

    if (rawTarget.includes("admin-menu-card") || rawTarget.includes("settings-menu-edit-card")) {
      return "menu";
    }

    if (rawTarget.includes("admin-definicoes-card")) {
      return "definicoes";
    }

    if (rawTarget.includes("account")) {
      return "contas";
    }

    const rawHref = String(element.getAttribute("href") || "").trim();
    if (rawHref) {
      try {
        const hrefUrl = new URL(rawHref, window.location.origin);
        const hrefAdminTab = cleanValueV7(hrefUrl.searchParams.get("admin_tab"));
        const hrefTarget = cleanValueV7(hrefUrl.searchParams.get("target") || "").replace(/^#/, "");
        const hrefHash = cleanValueV7((hrefUrl.hash || "").replace(/^#/, ""));
        const hrefLookup = (hrefTarget + " " + hrefHash).trim();

        if (hrefAdminTab === "entidade" || hrefLookup.includes("entity") || hrefLookup.includes("entidade")) {
          return "entidade";
        }

        if (hrefAdminTab === "utilizador" || hrefLookup.includes("user") || hrefLookup.includes("utilizador")) {
          return "utilizador";
        }

        if (
          hrefAdminTab === "sessoes" ||
          hrefLookup.includes("admin-sidebar-sections") ||
          hrefLookup.includes("sidebar-sections")
        ) {
          return "sessoes";
        }

        if (
          hrefAdminTab === "menu" ||
          hrefLookup.includes("admin-menu-card") ||
          hrefLookup.includes("settings-menu-edit-card")
        ) {
          return "menu";
        }

        if (hrefAdminTab === "definicoes" || hrefLookup.includes("admin-definicoes-card")) {
          return "definicoes";
        }

        if (hrefAdminTab === "contas" || hrefLookup.includes("admin-account-status")) {
          return "contas";
        }
      } catch (error) {
        if (rawHref.indexOf("#") === 0) {
          const hrefHashOnly = cleanValueV7(rawHref.replace(/^#/, ""));

          if (hrefHashOnly.includes("entity") || hrefHashOnly.includes("entidade")) {
            return "entidade";
          }

          if (hrefHashOnly.includes("user") || hrefHashOnly.includes("utilizador")) {
            return "utilizador";
          }

          if (hrefHashOnly.includes("admin-sidebar-sections") || hrefHashOnly.includes("sidebar-sections")) {
            return "sessoes";
          }

          if (hrefHashOnly.includes("admin-menu-card") || hrefHashOnly.includes("settings-menu-edit-card")) {
            return "menu";
          }

          if (hrefHashOnly.includes("admin-definicoes-card")) {
            return "definicoes";
          }

          if (hrefHashOnly.includes("admin-account-status")) {
            return "contas";
          }
        }
      }
    }

    const lookup = normalizeLookupTextV7([
      element.textContent || "",
      element.id || "",
      element.className || "",
      element.getAttribute("title") || "",
      element.getAttribute("aria-label") || ""
    ].join(" "));

    if (lookup.includes("entidade")) {
      return "entidade";
    }

    if (lookup.includes("utilizador") || lookup.includes("usuario")) {
      return "utilizador";
    }

    if (lookup.includes("sessao") || lookup.includes("sessoes")) {
      return "sessoes";
    }

    if (
      lookup === "menu" ||
      lookup === "menus" ||
      lookup.includes(" menu ") ||
      lookup.includes(" menus ")
    ) {
      return "menu";
    }

    if (lookup.includes("definicoes") || lookup.includes("definições")) {
      return "definicoes";
    }

    if (lookup.includes("conta") || lookup.includes("configuracao")) {
      return "contas";
    }

    return "";
  }

  function limparAbaAtivaSubprocessoV7() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu) {
      return;
    }

    Array.from(submenu.querySelectorAll(".submenu-item, button, a, [data-admin-tab]")).forEach(function (element) {
      element.classList.remove("active");
      element.classList.remove("selected");
      element.classList.remove("is-active");
      element.setAttribute("aria-selected", "false");
      element.removeAttribute("data-active");
      element.removeAttribute("data-selected");
      element.removeAttribute("data-appverbo-force-active");
      element.removeAttribute("data-appverbo-menu-active");
      element.removeAttribute("data-appverbo-menu-inactive");
      element.setAttribute("data-appverbo-force-inactive", "true");
    });
  }

  function marcarElementoAbaAtivaV7(element) {
    if (!element) {
      return false;
    }

    element.classList.add("active");
    element.setAttribute("aria-selected", "true");
    element.setAttribute("data-appverbo-force-active", "true");
    element.removeAttribute("data-appverbo-force-inactive");
    element.removeAttribute("data-appverbo-menu-inactive");
    return true;
  }

  function marcarAbaAtivaV7(tab) {
    const submenu = document.getElementById("submenu-items");

    if (!submenu) {
      return;
    }

    limparAbaAtivaSubprocessoV7();

    Array.from(submenu.querySelectorAll(".submenu-item, button, a, [data-admin-tab]")).some(function (element) {
      const elementTab = getTabFromElementV7(element);

      if (elementTab !== tab) {
        return false;
      }

      return marcarElementoAbaAtivaV7(element);
    });
  }

  function marcarAbaDinamicaAtivaV7(sectionKey) {
    const submenu = document.getElementById("submenu-items");
    const cleanSectionKey = cleanValueV7(sectionKey);

    if (!submenu || !cleanSectionKey) {
      return false;
    }

    limparAbaAtivaSubprocessoV7();

    const dynamicLink = submenu.querySelector(
      `.submenu-item[data-dynamic-process-section="${escapeSelectorValueV7(cleanSectionKey)}"], ` +
      `.submenu-item[data-dynamic-process-section-key="${escapeSelectorValueV7(cleanSectionKey)}"]`
    );

    if (!dynamicLink) {
      return false;
    }

    return marcarElementoAbaAtivaV7(dynamicLink);
  }

  function marcarAbaAtivaPorContextoV7(tab, dynamicSectionKey) {
    if (marcarAbaDinamicaAtivaV7(dynamicSectionKey)) {
      return;
    }

    marcarAbaAtivaV7(tab);
  }

  function limparAbaAtivaComRepeticaoV7() {
    limparAbaAtivaSubprocessoV7();

    [0, 20, 80, 160, 320, 650].forEach(function (delay) {
      window.setTimeout(function () {
        if (document.body && document.body.classList.contains("appverbo-admin-process-only")) {
          limparAbaAtivaSubprocessoV7();
          manterMenuSubprocessosVisivelV7();
        }
      }, delay);
    });

    if (clearActiveTimerV7) {
      window.clearInterval(clearActiveTimerV7);
    }

    let count = 0;
    clearActiveTimerV7 = window.setInterval(function () {
      count += 1;

      if (!document.body || !document.body.classList.contains("appverbo-admin-process-only") || count > 20) {
        window.clearInterval(clearActiveTimerV7);
        clearActiveTimerV7 = null;
        return;
      }

      limparAbaAtivaSubprocessoV7();
      manterMenuSubprocessosVisivelV7();
    }, 100);
  }

  //###################################################################################
  // (5) URL CANONICA
  //###################################################################################

  function resolveMenuKeyForTabV7(tab) {
    const cleanTab = cleanValueV7(tab);
    if (cleanTab === "entidade" || cleanTab === "utilizador") {
      return "administrativo";
    }
    if (cleanTab === "sessoes" || cleanTab === "menu" || cleanTab === "definicoes") {
      return "sessoes";
    }
    return "administrativo";
  }

  function buildAdminSubprocessUrlV7(tab) {
    const currentUrl = getCurrentUrlV7();
    const url = currentUrl
      ? new URL(currentUrl.toString())
      : new URL("/users/new", window.location.origin);

    url.pathname = "/users/new";
    const menuKey = resolveMenuKeyForTabV7(tab);
    url.searchParams.set("menu", menuKey);
    clearAdminNavigationParamsV7(url, { includeDynamicProcess: true });

    if (tab === "entidade") {
      url.searchParams.set("admin_tab", "entidade");
      url.searchParams.set("target", "create-entity-card");
      url.hash = "create-entity-card";
      return url.pathname + url.search + url.hash;
    }

    if (tab === "utilizador") {
      url.searchParams.set("admin_tab", "utilizador");
      url.searchParams.set("target", "create-user-card");
      url.hash = "create-user-card";
      return url.pathname + url.search + url.hash;
    }

    if (tab === "sessoes") {
      url.searchParams.set("admin_tab", "sessoes");
      url.searchParams.set("sidebar_sections_tab", "sessoes");
      url.searchParams.set("target", "admin-sidebar-sections-card");
      url.hash = "admin-sidebar-sections-card";
      return url.pathname + url.search + url.hash;
    }

    if (tab === "menu") {
      url.searchParams.set("admin_tab", "menu");
      url.searchParams.set("target", "admin-menu-card");
      url.hash = "admin-menu-card";
      return url.pathname + url.search + url.hash;
    }

    if (tab === "definicoes") {
      url.searchParams.set("admin_tab", "definicoes");
      url.searchParams.set("target", "admin-definicoes-card");
      url.hash = "admin-definicoes-card";
      return url.pathname + url.search + url.hash;
    }

    if (tab === "contas") {
      url.searchParams.set("admin_tab", "contas");
      url.searchParams.set("target", "admin-account-status-card");
      url.hash = "admin-account-status-card";
      return url.pathname + url.search + url.hash;
    }

    return "/users/new?menu=" + resolveMenuKeyForTabV7(tab);
  }

  //###################################################################################
  // (6) MATCH DE CARDS POR SUBPROCESSO
  //###################################################################################

  function isMenuTabsCardV7(card) {
    return Boolean(card && card.id === "menu-tabs-card");
  }

  function isHomeCardV7(card) {
    return Boolean(card && card.id === "home-summary-card");
  }

  function buildAdminCardIdSetV7(values) {
    return new Set(
      (Array.isArray(values) ? values : [])
        .map((value) => cleanValueV7(value))
        .filter(Boolean)
    );
  }

  const ADMIN_TAB_CARD_ID_SETS_V7 = Object.freeze({
    entidade: buildAdminCardIdSetV7([
      "create-entity-card",
      "edit-entity-card",
      "recent-entities-card",
      "inactive-entities-card",
      "admin-subprocess-v2-entidade",
      "admin-subprocess-v2-entidade-edit",
      "admin-entidade-v2-integrated-root"
    ]),
    utilizador: buildAdminCardIdSetV7([
      "create-user-card",
      "edit-user-card",
      "admin-user-shadow-readonly-card",
      "admin-user-shadow-inactive-card",
      "admin-users-created-card",
      "inactive-users-card"
    ]),
    sessoes: buildAdminCardIdSetV7([
      "admin-sidebar-sections-card",
      "admin-sidebar-sections-form-card",
      "admin-sidebar-sections-card-create",
      "admin-sidebar-sections-card-inactive"
    ]),
    menu: buildAdminCardIdSetV7([
      "admin-menu-card-create",
      "admin-menu-card",
      "admin-menu-card-inactive",
      "settings-menu-edit-card"
    ]),
    definicoes: buildAdminCardIdSetV7([
      "admin-definicoes-card-create",
      "admin-definicoes-card",
      "admin-definicoes-card-edit",
      "admin-definicoes-card-inactive"
    ]),
    contas: buildAdminCardIdSetV7([
      "admin-account-create-card",
      "admin-account-status-card"
    ])
  });

  function resolveCardTabByIdV7(cleanId) {
    if (!cleanId) {
      return "";
    }

    if (ADMIN_TAB_CARD_ID_SETS_V7.entidade.has(cleanId)) {
      return "entidade";
    }
    if (ADMIN_TAB_CARD_ID_SETS_V7.utilizador.has(cleanId)) {
      return "utilizador";
    }
    if (ADMIN_TAB_CARD_ID_SETS_V7.sessoes.has(cleanId)) {
      return "sessoes";
    }
    if (ADMIN_TAB_CARD_ID_SETS_V7.menu.has(cleanId)) {
      return "menu";
    }
    if (ADMIN_TAB_CARD_ID_SETS_V7.definicoes.has(cleanId)) {
      return "definicoes";
    }
    if (ADMIN_TAB_CARD_ID_SETS_V7.contas.has(cleanId)) {
      return "contas";
    }

    if (cleanId.startsWith("admin-sidebar-sections")) {
      return "sessoes";
    }
    if (cleanId.startsWith("admin-definicoes-card")) {
      return "definicoes";
    }
    if (cleanId.startsWith("admin-menu-card")) {
      return "menu";
    }
    if (cleanId.includes("admin-account") || cleanId.includes("account-status")) {
      return "contas";
    }

    if (
      cleanId.includes("user") ||
      cleanId.includes("utilizador")
    ) {
      return "utilizador";
    }

    if (
      cleanId.includes("entity") ||
      cleanId.includes("entities") ||
      cleanId.includes("entidade")
    ) {
      return "entidade";
    }

    return "";
  }

  function resolveCardTabV7(card) {
    if (!card || isMenuTabsCardV7(card) || isHomeCardV7(card)) {
      return "";
    }

    const cachedTab = cleanValueV7(card.getAttribute("data-appverbo-admin-tab"));
    if (cachedTab) {
      return cachedTab;
    }

    const subprocess = cleanValueV7(card.getAttribute("data-admin-subprocess"));
    if (
      subprocess === "entidade" ||
      subprocess === "utilizador" ||
      subprocess === "sessoes" ||
      subprocess === "menu" ||
      subprocess === "definicoes" ||
      subprocess === "contas"
    ) {
      card.setAttribute("data-appverbo-admin-tab", subprocess);
      return subprocess;
    }

    const resolvedById = resolveCardTabByIdV7(cleanValueV7(card.id));
    if (resolvedById) {
      card.setAttribute("data-appverbo-admin-tab", resolvedById);
      return resolvedById;
    }

    const menuScope = cleanValueV7(card.getAttribute("data-menu-scope"));
    if (menuScope.includes("configuracao")) {
      card.setAttribute("data-appverbo-admin-tab", "contas");
      return "contas";
    }

    return "";
  }

  function isCardForTabV7(card, tab) {
    const cleanTab = cleanValueV7(tab);
    if (!cleanTab) {
      return false;
    }
    return resolveCardTabV7(card) === cleanTab;
  }

  function getAdminCardsV7() {
    const container =
      document.querySelector(".content .container") ||
      document.querySelector(".content") ||
      document.body;

    return Array.from(container.querySelectorAll(".card, .admin-subprocess-card-v1"));
  }

  function hasCustomSubprocessLinksV7() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu) {
      return false;
    }

    const submenuItems = Array.from(
      submenu.querySelectorAll(".submenu-item, button, a, [data-admin-tab]")
    );

    return submenuItems.some(function (item) {
      if (!item) {
        return false;
      }

      const profileSection = cleanValueV7(item.getAttribute("data-profile-section"));
      if (profileSection) {
        return true;
      }

      const dynamicSection = cleanValueV7(
        item.getAttribute("data-dynamic-process-section") ||
        item.getAttribute("data-dynamic-process-section-key")
      );
      if (dynamicSection) {
        return true;
      }

      const href = String(item.getAttribute("href") || "").trim();
      if (href.indexOf("#") === 0 && !getTabFromElementV7(item)) {
        return true;
      }

      return false;
    });
  }

  function shouldForceServerRenderForTabV7(tab) {
    const cleanTab = cleanValueV7(tab);

    if (!cleanTab) {
      return false;
    }

    if (cleanTab === "menu") {
      const hasCanonicalMenuCards = Boolean(
        document.getElementById("admin-menu-card") ||
        document.getElementById("admin-menu-card-create") ||
        document.getElementById("admin-menu-card-inactive") ||
        document.getElementById("settings-menu-edit-card")
      );

      return !hasCanonicalMenuCards;
    }

    if (cleanTab === "sessoes" || cleanTab === "definicoes") {
      const hasSubprocessBlocks = getAdminCardsV7().some(function (card) {
        return isCardForTabV7(card, cleanTab);
      });

      return !hasSubprocessBlocks;
    }

    // O subprocesso Utilizador possui blocos server-render (shadow tables).
    // Quando a pagina inicia noutra aba, esses blocos podem nao existir no DOM.
    // Neste caso, o clique deve recarregar em admin_tab=utilizador.
    if (cleanTab === "utilizador") {
      const hasUserShadowBlocks = Boolean(
        document.querySelector(
          "#admin-user-shadow-readonly-card, " +
          "#admin-users-created-card, " +
          "[data-admin-subprocess-shadow='utilizador']"
        )
      );

      return !hasUserShadowBlocks;
    }

    return false;
  }

  function shouldAlwaysNavigateForHashSubmenuTabV7(tab) {
    const cleanTab = cleanValueV7(tab);
    return cleanTab === "sessoes" || cleanTab === "menu" || cleanTab === "definicoes";
  }

  //###################################################################################
  // (7) RENDER DO SUBPROCESSO
  //###################################################################################

  function limparClassesTabBodyV7() {
    if (!document.body) {
      return;
    }

    ADMIN_TAB_CLASSES_V7.forEach(function (className) {
      document.body.classList.remove(className);
    });
  }

  function renderAdminProcessOnlyV7() {
    if (!document.body) {
      return;
    }

    document.body.classList.add("appverbo-admin-process-only");
    document.body.classList.add("appverbo-admin-submenu-stable");
    document.body.classList.remove("appverbo-admin-subprocess-context");
    document.body.classList.remove("appverbo-admin-sessoes");
    limparClassesTabBodyV7();

    getAdminCardsV7().forEach(function (card) {
      if (isMenuTabsCardV7(card)) {
        showElementV7(card);
      } else {
        hideElementV7(card);
      }
    });

    manterMenuSubprocessosVisivelV7();
    limparAbaAtivaComRepeticaoV7();
  }

  function exitAdminProcessOnlyModeV7() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    document.body.classList.add("appverbo-admin-subprocess-context");
    document.body.classList.add("appverbo-admin-submenu-stable");
    limparClassesTabBodyV7();
    manterMenuSubprocessosVisivelV7();
  }

  function renderAdminSubprocessV7(tab, options) {
    const config = options || {};
    const normalizedTab = tab;
    const dynamicSectionKey = cleanValueV7(config.dynamicSectionKey);

    if (!normalizedTab) {
      renderAdminProcessOnlyV7();
      return false;
    }

    if (!document.body) {
      return false;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    document.body.classList.add("appverbo-admin-subprocess-context");
    document.body.classList.add("appverbo-admin-submenu-stable");
    document.body.classList.toggle("appverbo-admin-sessoes", normalizedTab === "sessoes");

    limparClassesTabBodyV7();
    document.body.classList.add("appverbo-admin-tab-" + normalizedTab);

    const cards = getAdminCardsV7();
    let shownCount = 0;

    cards.forEach(function (card) {
      if (isMenuTabsCardV7(card)) {
        showElementV7(card);
        return;
      }

      if (isCardForTabV7(card, normalizedTab)) {
        showElementV7(card);
        shownCount += 1;
      } else {
        hideElementV7(card);
      }
    });

    marcarAbaAtivaPorContextoV7(normalizedTab, dynamicSectionKey);
    manterMenuSubprocessosVisivelV7();
    marcarMenuEstavelV7();

    if (config.updateUrl !== false && window.history && typeof window.history.pushState === "function") {
      const destination = buildAdminSubprocessUrlV7(normalizedTab);
      const currentPath = window.location.pathname + window.location.search + window.location.hash;

      if (currentPath !== destination) {
        window.history.pushState(window.history.state, document.title, destination);
      }
    }

    return shownCount > 0;
  }

  //###################################################################################
  // (8) INICIALIZAR PELO URL
  //###################################################################################

  function inicializarV7() {
    const url = getCurrentUrlV7();

    if (!urlIndicaAdminV7(url)) {
      markReadyV7();
      return;
    }

    const tab = getAdminTabFromUrlV7(url);
    const dynamicSectionKey = getDynamicProcessSectionFromUrlV7(url);

    if (tab) {
      renderAdminSubprocessV7(tab, {
        updateUrl: false,
        dynamicSectionKey
      });
    } else {
      if (hasCustomSubprocessLinksV7()) {
        exitAdminProcessOnlyModeV7();
        markReadyV7();
        return;
      }

      const menuKey = cleanValueV7(url.searchParams.get("menu")) || getActiveSidebarMenuKeyV7() || "administrativo";
      const defaultTab = menuKey === "sessoes" ? "sessoes" : "entidade";

      if (shouldForceServerRenderForTabV7(defaultTab)) {
        window.location.assign(buildAdminSubprocessUrlV7(defaultTab));
        return;
      }

      renderAdminSubprocessV7(defaultTab, { updateUrl: true });
    }

    markReadyV7();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.requestAnimationFrame(inicializarV7);
    }, { once: true });
  } else {
    window.requestAnimationFrame(inicializarV7);
  }

  window.addEventListener("load", inicializarV7, { once: true });
  window.addEventListener("pageshow", inicializarV7);

  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(inicializarV7);
  });

  //###################################################################################
  // (9) CLIQUES NOS SUBPROCESSOS
  //###################################################################################

  document.addEventListener("click", function (event) {
    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const clickedTopSubprocess = target.closest(
      "#submenu-items .submenu-item, #submenu-items button, #submenu-items a, button[data-admin-tab]"
    );

    if (clickedTopSubprocess) {
      const currentUrl = getCurrentUrlV7();
      const isAdminRoute = urlIndicaAdminV7(currentUrl);
      const activeMenuKey = getActiveSidebarMenuKeyV7();
      const isAdminSidebarMenuActive = activeMenuKey === "administrativo" || activeMenuKey === "sessoes";

      if (!isAdminRoute || !isAdminSidebarMenuActive) {
        return;
      }

      const submenuAnchor =
        clickedTopSubprocess.matches &&
        clickedTopSubprocess.matches("#submenu-items .submenu-item, #submenu-items a")
          ? clickedTopSubprocess
          : null;
      const submenuHref = String(submenuAnchor ? submenuAnchor.getAttribute("href") || "" : "").trim();
      const isHashOnlySubmenuLink = submenuHref.indexOf("#") === 0;
      const isAdminProcessOnlyMode =
        Boolean(document.body) &&
        document.body.classList.contains("appverbo-admin-process-only");

      const tab = getTabFromElementV7(clickedTopSubprocess);

      if (tab && submenuAnchor && isHashOnlySubmenuLink) {
        // No estado inicial (admin process-only), algumas abas dependem de server-render.
        // Para esses casos, navegamos para URL canônica imediatamente.
        if (
          isAdminProcessOnlyMode &&
          (shouldAlwaysNavigateForHashSubmenuTabV7(tab) || shouldForceServerRenderForTabV7(tab))
        ) {
          const destination = buildAdminSubprocessUrlV7(tab);
          const currentPath = window.location.pathname + window.location.search + window.location.hash;

          if (destination && currentPath !== destination) {
            event.preventDefault();
            event.stopPropagation();
            if (typeof event.stopImmediatePropagation === "function") {
              event.stopImmediatePropagation();
            }
            window.location.assign(destination);
            return;
          }
        }
      }

      if (tab) {
        event.preventDefault();
        event.stopPropagation();

        if (typeof event.stopImmediatePropagation === "function") {
          event.stopImmediatePropagation();
        }

        const destination = buildAdminSubprocessUrlV7(tab);
        const currentPath = window.location.pathname + window.location.search + window.location.hash;

        if (shouldForceServerRenderForTabV7(tab)) {
          if (destination && currentPath !== destination) {
            window.location.assign(destination);
            return;
          }
        }

        const rendered = renderAdminSubprocessV7(tab, { updateUrl: true });

        if (!rendered && destination) {
          if (currentPath !== destination) {
            window.location.assign(destination);
          } else {
            window.location.reload();
          }
          return;
        }
        return;
      }
    }

    const menuButton = target.closest("button[data-menu]");

    const activeMenuKeyClick = menuButton ? cleanValueV7(menuButton.getAttribute("data-menu")) : "";
    if (menuButton && (activeMenuKeyClick === "administrativo" || activeMenuKeyClick === "sessoes")) {
      window.setTimeout(function () {
        if (hasCustomSubprocessLinksV7()) {
          exitAdminProcessOnlyModeV7();
          markReadyV7();
          return;
        }

        const firstTab = activeMenuKeyClick === "sessoes" ? "sessoes" : "entidade";

        if (shouldForceServerRenderForTabV7(firstTab)) {
          window.location.assign(buildAdminSubprocessUrlV7(firstTab));
          return;
        }

        renderAdminSubprocessV7(firstTab, { updateUrl: true });
        markReadyV7();
      }, 0);

      window.setTimeout(function () {
        if (hasCustomSubprocessLinksV7()) {
          exitAdminProcessOnlyModeV7();
        }
      }, 80);
      return;
    }

    const editLink = target.closest(".admin-subprocess-action-link-v1");

    if (editLink) {
      marcarMenuEstavelV7();
      window.setTimeout(inicializarV7, 0);
    }
  }, true);
})();
// APPVERBO_NAVIGATION_SMOOTH_V7_END
