// APPVERBO_NAVIGATION_SMOOTH_V6_START
//###################################################################################
// (1) FUNCOES BASE
//###################################################################################

(function () {
  "use strict";

  let observerV6 = null;
  let clearActiveTimerV6 = null;
  let stableTimerV6 = null;

  function getCurrentUrlV6() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function cleanValueV6(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeLookupTextV6(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ");
  }

  function markReadyV6() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");
  }

  //###################################################################################
  // (2) DETETAR ESTADO ADMINISTRATIVO
  //###################################################################################

  function urlIndicaAdminV6(url) {
    return Boolean(
      url &&
      url.pathname === "/users/new" &&
      cleanValueV6(url.searchParams.get("menu")) === "administrativo"
    );
  }

  function urlIndicaAdminProcessOnlyV6(url) {
    if (!urlIndicaAdminV6(url)) {
      return false;
    }

    const adminTab = cleanValueV6(url.searchParams.get("admin_tab"));
    const target = cleanValueV6(url.searchParams.get("target"));
    const settingsEditKey = cleanValueV6(url.searchParams.get("settings_edit_key"));
    const sidebarSectionEditKey = cleanValueV6(url.searchParams.get("sidebar_section_edit_key"));
    const settingsTab = cleanValueV6(url.searchParams.get("settings_tab"));
    const sidebarSectionsTab = cleanValueV6(url.searchParams.get("sidebar_sections_tab"));
    const hash = cleanValueV6((url.hash || "").replace(/^#/, ""));

    return (
      !adminTab &&
      !target &&
      !settingsEditKey &&
      !sidebarSectionEditKey &&
      !settingsTab &&
      !sidebarSectionsTab &&
      !hash
    );
  }

  function urlIndicaSubprocessoSessoesV6(url) {
    if (!urlIndicaAdminV6(url)) {
      return false;
    }

    const adminTab = cleanValueV6(url.searchParams.get("admin_tab"));
    const target = cleanValueV6(url.searchParams.get("target"));
    const hash = cleanValueV6((url.hash || "").replace(/^#/, ""));
    const settingsTab = cleanValueV6(url.searchParams.get("settings_tab")).replace(/_/g, "-");
    const sidebarSectionsTab = cleanValueV6(url.searchParams.get("sidebar_sections_tab")).replace(/_/g, "-");
    const sidebarSectionEditKey = cleanValueV6(url.searchParams.get("sidebar_section_edit_key"));

    return (
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
    );
  }

  function urlIndicaAdminSubprocessContextV6(url) {
    if (!urlIndicaAdminV6(url)) {
      return false;
    }

    return !urlIndicaAdminProcessOnlyV6(url);
  }

  //###################################################################################
  // (3) MANTER BLOCO DE SUBPROCESSOS VISIVEL
  //###################################################################################

  function manterMenuSubprocessosVisivelV6() {
    const menuTabsCard = document.getElementById("menu-tabs-card");

    if (!menuTabsCard) {
      return;
    }

    menuTabsCard.style.setProperty("display", "block", "important");
    menuTabsCard.style.setProperty("visibility", "visible", "important");
    menuTabsCard.style.setProperty("opacity", "1", "important");
    menuTabsCard.style.setProperty("transition", "none", "important");
  }

  function marcarMenuEstavelV6() {
    if (!document.body) {
      return;
    }

    document.body.classList.add("appverbo-admin-submenu-stable");
    document.body.classList.add("appverbo-admin-submenu-switching");
    manterMenuSubprocessosVisivelV6();

    if (stableTimerV6) {
      window.clearTimeout(stableTimerV6);
    }

    stableTimerV6 = window.setTimeout(function () {
      if (document.body) {
        document.body.classList.remove("appverbo-admin-submenu-switching");
      }
      manterMenuSubprocessosVisivelV6();
      stableTimerV6 = null;
    }, 220);
  }

  //###################################################################################
  // (4) LIMPAR ABA ATIVA NO MODO SOMENTE PROCESSO
  //###################################################################################

  function limparAbaAtivaSubprocessoV6() {
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

  function iniciarObservadorProcessOnlyV6() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu || observerV6) {
      return;
    }

    observerV6 = new MutationObserver(function () {
      if (!document.body) {
        return;
      }

      manterMenuSubprocessosVisivelV6();

      if (!document.body.classList.contains("appverbo-admin-process-only")) {
        return;
      }

      limparAbaAtivaSubprocessoV6();
    });

    observerV6.observe(submenu, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["class", "aria-selected", "data-active", "data-selected", "style"]
    });
  }

  function pararObservadorProcessOnlyV6() {
    if (!observerV6) {
      return;
    }

    observerV6.disconnect();
    observerV6 = null;
  }

  function limparAbaAtivaComRepeticaoV6() {
    limparAbaAtivaSubprocessoV6();

    [0, 20, 80, 160, 320, 650].forEach(function (delay) {
      window.setTimeout(function () {
        if (document.body && document.body.classList.contains("appverbo-admin-process-only")) {
          limparAbaAtivaSubprocessoV6();
          manterMenuSubprocessosVisivelV6();
        }
      }, delay);
    });

    if (clearActiveTimerV6) {
      window.clearInterval(clearActiveTimerV6);
    }

    let count = 0;
    clearActiveTimerV6 = window.setInterval(function () {
      count += 1;

      if (!document.body || !document.body.classList.contains("appverbo-admin-process-only") || count > 20) {
        window.clearInterval(clearActiveTimerV6);
        clearActiveTimerV6 = null;
        return;
      }

      limparAbaAtivaSubprocessoV6();
      manterMenuSubprocessosVisivelV6();
    }, 100);
  }

  //###################################################################################
  // (5) RESOLVER DESTINO CANONICO DOS SUBPROCESSOS
  //###################################################################################

  function buildAdminSubprocessUrlV6(config) {
    const url = new URL("/users/new", window.location.origin);

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", config.adminTab);

    if (config.sidebarSectionsTab) {
      url.searchParams.set("sidebar_sections_tab", config.sidebarSectionsTab);
    }

    if (config.settingsTab) {
      url.searchParams.set("settings_tab", config.settingsTab);
    }

    if (config.target) {
      url.searchParams.set("target", config.target);
      url.hash = config.target;
    }

    return url.pathname + url.search + url.hash;
  }

  function resolverHrefExistenteV6(element) {
    const link = element && element.closest ? element.closest("a[href]") : null;

    if (!link) {
      return "";
    }

    const rawHref = String(link.getAttribute("href") || "").trim();

    if (!rawHref || rawHref === "#" || rawHref.startsWith("javascript:")) {
      return "";
    }

    let url = null;

    try {
      url = new URL(rawHref, window.location.origin);
    } catch (error) {
      return "";
    }

    if (url.pathname !== "/users/new") {
      return "";
    }

    if (!url.searchParams.get("menu")) {
      url.searchParams.set("menu", "administrativo");
    }

    return url.pathname + url.search + url.hash;
  }

  function resolverSubprocessoPeloElementoV6(element) {
    if (!element) {
      return null;
    }

    const existingHref = resolverHrefExistenteV6(element);

    if (existingHref) {
      return existingHref;
    }

    const rawAdminTab = cleanValueV6(
      element.getAttribute("data-admin-tab") ||
      element.getAttribute("data-tab") ||
      element.getAttribute("data-admin-target") ||
      ""
    );

    const rawTarget = cleanValueV6(
      element.getAttribute("data-target") ||
      element.getAttribute("data-menu-target") ||
      element.getAttribute("aria-controls") ||
      ""
    ).replace(/^#/, "");

    if (rawAdminTab === "entidade" || rawTarget === "create-entity-card") {
      return buildAdminSubprocessUrlV6({
        adminTab: "entidade",
        target: "create-entity-card"
      });
    }

    if (rawAdminTab === "utilizador" || rawTarget === "create-user-card") {
      return buildAdminSubprocessUrlV6({
        adminTab: "utilizador",
        target: "create-user-card"
      });
    }

    if (rawAdminTab === "sessoes" || rawTarget === "admin-sidebar-sections-card") {
      return buildAdminSubprocessUrlV6({
        adminTab: "sessoes",
        sidebarSectionsTab: "sessoes",
        target: "admin-sidebar-sections-card"
      });
    }

    if (rawAdminTab === "contas" || rawAdminTab === "menu" || rawTarget === "admin-account-status-card") {
      return buildAdminSubprocessUrlV6({
        adminTab: "contas",
        target: "admin-account-status-card"
      });
    }

    const lookup = normalizeLookupTextV6([
      element.textContent || "",
      element.id || "",
      element.className || "",
      element.getAttribute("title") || "",
      element.getAttribute("aria-label") || ""
    ].join(" "));

    if (lookup.includes("entidade")) {
      return buildAdminSubprocessUrlV6({
        adminTab: "entidade",
        target: "create-entity-card"
      });
    }

    if (lookup.includes("utilizador") || lookup.includes("usuario")) {
      return buildAdminSubprocessUrlV6({
        adminTab: "utilizador",
        target: "create-user-card"
      });
    }

    if (lookup.includes("sessao") || lookup.includes("sessoes")) {
      return buildAdminSubprocessUrlV6({
        adminTab: "sessoes",
        sidebarSectionsTab: "sessoes",
        target: "admin-sidebar-sections-card"
      });
    }

    if (lookup.includes("menu") || lookup.includes("conta") || lookup.includes("configuracao")) {
      return buildAdminSubprocessUrlV6({
        adminTab: "contas",
        target: "admin-account-status-card"
      });
    }

    return null;
  }

  //###################################################################################
  // (6) CLIQUE LIVRE SEM RECRIAR O MENU
  //###################################################################################

  function prepararCliqueSubprocessoV6(element) {
    const destination = resolverSubprocessoPeloElementoV6(element);

    if (!destination) {
      return false;
    }

    if (document.body) {
      document.body.classList.remove("appverbo-admin-process-only");
      document.body.classList.add("appverbo-admin-subprocess-context");
      document.body.classList.add("appverbo-admin-submenu-stable");
      document.body.classList.add("appverbo-admin-submenu-switching");
    }

    pararObservadorProcessOnlyV6();
    manterMenuSubprocessosVisivelV6();

    if (window.history && typeof window.history.pushState === "function") {
      const currentPath = window.location.pathname + window.location.search + window.location.hash;

      if (currentPath !== destination) {
        window.history.pushState(window.history.state, document.title, destination);
      }
    }

    marcarMenuEstavelV6();
    return true;
  }

  //###################################################################################
  // (7) NORMALIZAR URLS ESPECIAIS
  //###################################################################################

  function normalizarUrlSessoesV6() {
    const url = getCurrentUrlV6();

    if (!urlIndicaSubprocessoSessoesV6(url)) {
      return;
    }

    let changed = false;

    if (cleanValueV6(url.searchParams.get("admin_tab")) !== "sessoes") {
      url.searchParams.set("admin_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV6(url.searchParams.get("sidebar_sections_tab"))) {
      url.searchParams.set("sidebar_sections_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV6(url.searchParams.get("target"))) {
      url.searchParams.set("target", "admin-sidebar-sections-card");
      changed = true;
    }

    if (!url.hash) {
      url.hash = "admin-sidebar-sections-card";
      changed = true;
    }

    if (changed && window.history && typeof window.history.replaceState === "function") {
      window.history.replaceState(
        window.history.state,
        document.title,
        url.pathname + url.search + url.hash
      );
    }
  }

  function normalizarUrlAdminProcessOnlyV6() {
    const url = getCurrentUrlV6();

    if (!urlIndicaAdminProcessOnlyV6(url)) {
      return;
    }

    const nextUrl = "/users/new?menu=administrativo";

    if (
      window.location.pathname + window.location.search + window.location.hash !== nextUrl &&
      window.history &&
      typeof window.history.replaceState === "function"
    ) {
      window.history.replaceState(window.history.state, document.title, nextUrl);
    }
  }

  //###################################################################################
  // (8) APLICAR CLASSES VISUAIS
  //###################################################################################

  function aplicarClasseContextoV6() {
    const url = getCurrentUrlV6();

    if (!document.body) {
      return;
    }

    if (urlIndicaAdminProcessOnlyV6(url)) {
      document.body.classList.add("appverbo-admin-process-only");
      document.body.classList.add("appverbo-admin-submenu-stable");
      document.body.classList.remove("appverbo-admin-subprocess-context");
      document.body.classList.remove("appverbo-admin-sessoes");
      iniciarObservadorProcessOnlyV6();
      limparAbaAtivaComRepeticaoV6();
      manterMenuSubprocessosVisivelV6();
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    pararObservadorProcessOnlyV6();

    if (urlIndicaAdminSubprocessContextV6(url)) {
      document.body.classList.add("appverbo-admin-subprocess-context");
      document.body.classList.add("appverbo-admin-submenu-stable");
      manterMenuSubprocessosVisivelV6();
    } else {
      document.body.classList.remove("appverbo-admin-subprocess-context");
      document.body.classList.remove("appverbo-admin-submenu-stable");
    }

    if (urlIndicaSubprocessoSessoesV6(url)) {
      document.body.classList.add("appverbo-admin-sessoes");
    } else {
      document.body.classList.remove("appverbo-admin-sessoes");
    }
  }

  function ativarModoAdminProcessOnlyV6() {
    if (!document.body) {
      return;
    }

    if (window.history && typeof window.history.replaceState === "function") {
      window.history.replaceState(
        window.history.state,
        document.title,
        "/users/new?menu=administrativo"
      );
    }

    document.body.classList.add("appverbo-admin-process-only");
    document.body.classList.add("appverbo-admin-submenu-stable");
    document.body.classList.remove("appverbo-admin-subprocess-context");
    document.body.classList.remove("appverbo-admin-sessoes");

    iniciarObservadorProcessOnlyV6();
    limparAbaAtivaComRepeticaoV6();
    manterMenuSubprocessosVisivelV6();
    markReadyV6();
  }

  //###################################################################################
  // (9) INICIALIZAR ESTADO
  //###################################################################################

  function inicializarV6() {
    normalizarUrlSessoesV6();
    normalizarUrlAdminProcessOnlyV6();
    aplicarClasseContextoV6();
    markReadyV6();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.requestAnimationFrame(inicializarV6);
    }, { once: true });
  } else {
    window.requestAnimationFrame(inicializarV6);
  }

  window.addEventListener("load", inicializarV6, { once: true });
  window.addEventListener("pageshow", inicializarV6);

  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(inicializarV6);
  });

  //###################################################################################
  // (10) CLIQUES: PROCESSO E SUBPROCESSOS
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
      prepararCliqueSubprocessoV6(clickedTopSubprocess);
      window.setTimeout(manterMenuSubprocessosVisivelV6, 0);
      window.setTimeout(manterMenuSubprocessosVisivelV6, 60);
      window.setTimeout(manterMenuSubprocessosVisivelV6, 180);
      window.setTimeout(aplicarClasseContextoV6, 220);
      return;
    }

    const menuButton = target.closest("button[data-menu]");

    if (menuButton && cleanValueV6(menuButton.getAttribute("data-menu")) === "administrativo") {
      window.setTimeout(ativarModoAdminProcessOnlyV6, 0);
      window.setTimeout(ativarModoAdminProcessOnlyV6, 60);
      window.setTimeout(ativarModoAdminProcessOnlyV6, 180);
      return;
    }

    const editLink = target.closest(".admin-subprocess-action-link-v1");

    if (editLink) {
      marcarMenuEstavelV6();
      window.setTimeout(aplicarClasseContextoV6, 0);
    }
  }, true);
})();
// APPVERBO_NAVIGATION_SMOOTH_V6_END
