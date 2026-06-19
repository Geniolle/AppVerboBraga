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
    return Boolean(
      url &&
      url.pathname === "/users/new" &&
      cleanValueV7(url.searchParams.get("menu")) === "administrativo"
    );
  }

  function getAdminTabFromUrlV7(url) {
    if (!urlIndicaAdminV7(url)) {
      return "";
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

    if (rawTarget.includes("account")) {
      return "contas";
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

    submenu
      .querySelectorAll(".active, [aria-selected='true'], [data-active='true'], [data-selected='true']")
      .forEach(function (element) {
        element.classList.remove("active");
        element.classList.remove("selected");
        element.classList.remove("is-active");
        element.setAttribute("aria-selected", "false");
        element.removeAttribute("data-active");
        element.removeAttribute("data-selected");
      });
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

      element.classList.add("active");
      element.setAttribute("aria-selected", "true");
      return true;
    });
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

  function buildAdminSubprocessUrlV7(tab) {
    const url = new URL("/users/new", window.location.origin);

    url.searchParams.set("menu", "administrativo");

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

    if (tab === "contas") {
      url.searchParams.set("admin_tab", "contas");
      url.searchParams.set("target", "admin-account-status-card");
      url.hash = "admin-account-status-card";
      return url.pathname + url.search + url.hash;
    }

    return "/users/new?menu=administrativo";
  }

  //###################################################################################
  // (6) MATCH DE CARDS POR SUBPROCESSO
  //###################################################################################

  function getCardTextV7(card) {
    return normalizeLookupTextV7(card ? card.textContent || "" : "");
  }

  function isMenuTabsCardV7(card) {
    return Boolean(card && card.id === "menu-tabs-card");
  }

  function isHomeCardV7(card) {
    return Boolean(card && card.id === "home-summary-card");
  }

  function isCardForTabV7(card, tab) {
    if (!card || isMenuTabsCardV7(card) || isHomeCardV7(card)) {
      return false;
    }

    const id = cleanValueV7(card.id);
    const subprocess = cleanValueV7(card.getAttribute("data-admin-subprocess"));
    const text = getCardTextV7(card);

    if (tab === "entidade") {
      return (
        id === "create-entity-card" ||
        id === "edit-entity-card" ||
        id === "recent-entities-card" ||
        id === "inactive-entities-card" ||
        id.includes("entity") ||
        id.includes("entities") ||
        id.includes("entidade") ||
        text.includes("criar entidade") ||
        text.includes("entidades ativas") ||
        text.includes("entidades criadas") ||
        text.includes("entidades inativas") ||
        text.includes("dados gerais")
      );
    }

    if (tab === "utilizador") {
      return (
        id.includes("user") ||
        id.includes("utilizador") ||
        text.includes("criar utilizador") ||
        text.includes("utilizadores criados") ||
        text.includes("utilizadores ativos") ||
        text.includes("utilizadores inativos")
      );
    }

    if (tab === "sessoes") {
      return (
        subprocess === "sessoes" ||
        id.includes("admin-sidebar-sections") ||
        id.includes("sidebar-sections") ||
        text.includes("criar sessao") ||
        text.includes("sessoes ativas") ||
        text.includes("sessoes inativas") ||
        text.includes("criar sessão") ||
        text.includes("sessões ativas") ||
        text.includes("sessões inativas")
      );
    }

    if (tab === "menu") {
      return (
        subprocess === "menu" ||
        id === "admin-menu-card-create" ||
        id === "admin-menu-card" ||
        id === "admin-menu-card-inactive" ||
        id === "settings-menu-edit-card" ||
        text.includes("criar menu") ||
        text.includes("menus ativos") ||
        text.includes("menus inativos") ||
        text.includes("editar menu")
      );
    }

    if (tab === "contas") {
      return (
        id.includes("admin-account-status") ||
        id.includes("account-status") ||
        text.includes("conta") ||
        text.includes("permissao") ||
        text.includes("permissão") ||
        text.includes("configuracao") ||
        text.includes("configuração")
      );
    }

    return false;
  }

  function getAdminCardsV7() {
    const container =
      document.querySelector(".content .container") ||
      document.querySelector(".content") ||
      document.body;

    return Array.from(container.querySelectorAll(".card, .admin-subprocess-card-v1"));
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

  function renderAdminSubprocessV7(tab, options) {
    const config = options || {};
    const normalizedTab = tab;

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

    marcarAbaAtivaV7(normalizedTab);
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

    if (tab) {
      renderAdminSubprocessV7(tab, { updateUrl: false });
    } else {
      renderAdminProcessOnlyV7();

      if (window.history && typeof window.history.replaceState === "function") {
        window.history.replaceState(window.history.state, document.title, "/users/new?menu=administrativo");
      }
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
      const tab = getTabFromElementV7(clickedTopSubprocess);

      if (tab) {
        event.preventDefault();
        event.stopPropagation();

        if (typeof event.stopImmediatePropagation === "function") {
          event.stopImmediatePropagation();
        }

        renderAdminSubprocessV7(tab, { updateUrl: true });
        return;
      }
    }

    const menuButton = target.closest("button[data-menu]");

    if (menuButton && cleanValueV7(menuButton.getAttribute("data-menu")) === "administrativo") {
      window.setTimeout(function () {
        if (window.history && typeof window.history.replaceState === "function") {
          window.history.replaceState(window.history.state, document.title, "/users/new?menu=administrativo");
        }

        renderAdminProcessOnlyV7();
        markReadyV7();
      }, 0);

      window.setTimeout(renderAdminProcessOnlyV7, 80);
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
