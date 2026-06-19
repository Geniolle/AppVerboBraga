// APPVERBO_NAVIGATION_SMOOTH_V5_START
//###################################################################################
// (1) FUNCOES BASE
//###################################################################################

(function () {
  "use strict";

  let observerV5 = null;
  let clearActiveTimerV5 = null;

  function getCurrentUrlV5() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function cleanValueV5(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeLookupTextV5(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ");
  }

  function markReadyV5() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");
  }

  //###################################################################################
  // (2) DETETAR ESTADO ADMINISTRATIVO
  //###################################################################################

  function urlIndicaAdminV5(url) {
    return Boolean(
      url &&
      url.pathname === "/users/new" &&
      cleanValueV5(url.searchParams.get("menu")) === "administrativo"
    );
  }

  function urlIndicaAdminProcessOnlyV5(url) {
    if (!urlIndicaAdminV5(url)) {
      return false;
    }

    const adminTab = cleanValueV5(url.searchParams.get("admin_tab"));
    const target = cleanValueV5(url.searchParams.get("target"));
    const settingsEditKey = cleanValueV5(url.searchParams.get("settings_edit_key"));
    const sidebarSectionEditKey = cleanValueV5(url.searchParams.get("sidebar_section_edit_key"));
    const settingsTab = cleanValueV5(url.searchParams.get("settings_tab"));
    const sidebarSectionsTab = cleanValueV5(url.searchParams.get("sidebar_sections_tab"));
    const hash = cleanValueV5((url.hash || "").replace(/^#/, ""));

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

  function urlIndicaSubprocessoSessoesV5(url) {
    if (!urlIndicaAdminV5(url)) {
      return false;
    }

    const adminTab = cleanValueV5(url.searchParams.get("admin_tab"));
    const target = cleanValueV5(url.searchParams.get("target"));
    const hash = cleanValueV5((url.hash || "").replace(/^#/, ""));
    const settingsTab = cleanValueV5(url.searchParams.get("settings_tab")).replace(/_/g, "-");
    const sidebarSectionsTab = cleanValueV5(url.searchParams.get("sidebar_sections_tab")).replace(/_/g, "-");
    const sidebarSectionEditKey = cleanValueV5(url.searchParams.get("sidebar_section_edit_key"));

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

  //###################################################################################
  // (3) LIMPAR ABA ATIVA DOS SUBPROCESSOS NO MODO SOMENTE PROCESSO
  //###################################################################################

  function limparAbaAtivaSubprocessoV5() {
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

  function iniciarObservadorProcessOnlyV5() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu || observerV5) {
      return;
    }

    observerV5 = new MutationObserver(function () {
      if (!document.body || !document.body.classList.contains("appverbo-admin-process-only")) {
        return;
      }

      limparAbaAtivaSubprocessoV5();
    });

    observerV5.observe(submenu, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["class", "aria-selected", "data-active", "data-selected"]
    });
  }

  function pararObservadorProcessOnlyV5() {
    if (!observerV5) {
      return;
    }

    observerV5.disconnect();
    observerV5 = null;
  }

  function limparAbaAtivaComRepeticaoV5() {
    limparAbaAtivaSubprocessoV5();

    [0, 20, 80, 160, 320, 650].forEach(function (delay) {
      window.setTimeout(function () {
        if (document.body && document.body.classList.contains("appverbo-admin-process-only")) {
          limparAbaAtivaSubprocessoV5();
        }
      }, delay);
    });

    if (clearActiveTimerV5) {
      window.clearInterval(clearActiveTimerV5);
    }

    let count = 0;
    clearActiveTimerV5 = window.setInterval(function () {
      count += 1;

      if (!document.body || !document.body.classList.contains("appverbo-admin-process-only") || count > 20) {
        window.clearInterval(clearActiveTimerV5);
        clearActiveTimerV5 = null;
        return;
      }

      limparAbaAtivaSubprocessoV5();
    }, 100);
  }

  //###################################################################################
  // (4) RESOLVER DESTINO CANONICO DE QUALQUER SUBPROCESSO
  //###################################################################################

  function buildAdminSubprocessUrlV5(config) {
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

  function resolverHrefExistenteV5(element) {
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

  function resolverSubprocessoPeloElementoV5(element) {
    if (!element) {
      return null;
    }

    const existingHref = resolverHrefExistenteV5(element);

    if (existingHref) {
      return existingHref;
    }

    const rawAdminTab = cleanValueV5(
      element.getAttribute("data-admin-tab") ||
      element.getAttribute("data-tab") ||
      element.getAttribute("data-admin-target") ||
      ""
    );

    const rawTarget = cleanValueV5(
      element.getAttribute("data-target") ||
      element.getAttribute("data-menu-target") ||
      element.getAttribute("aria-controls") ||
      ""
    ).replace(/^#/, "");

    if (rawAdminTab === "entidade" || rawTarget === "create-entity-card") {
      return buildAdminSubprocessUrlV5({
        adminTab: "entidade",
        target: "create-entity-card"
      });
    }

    if (rawAdminTab === "utilizador" || rawTarget === "create-user-card") {
      return buildAdminSubprocessUrlV5({
        adminTab: "utilizador",
        target: "create-user-card"
      });
    }

    if (rawAdminTab === "sessoes" || rawTarget === "admin-sidebar-sections-card") {
      return buildAdminSubprocessUrlV5({
        adminTab: "sessoes",
        sidebarSectionsTab: "sessoes",
        target: "admin-sidebar-sections-card"
      });
    }

    if (rawAdminTab === "contas" || rawAdminTab === "menu" || rawTarget === "admin-account-status-card") {
      return buildAdminSubprocessUrlV5({
        adminTab: "contas",
        target: "admin-account-status-card"
      });
    }

    const lookup = normalizeLookupTextV5([
      element.textContent || "",
      element.id || "",
      element.className || "",
      element.getAttribute("title") || "",
      element.getAttribute("aria-label") || ""
    ].join(" "));

    if (lookup.includes("entidade")) {
      return buildAdminSubprocessUrlV5({
        adminTab: "entidade",
        target: "create-entity-card"
      });
    }

    if (lookup.includes("utilizador") || lookup.includes("usuario")) {
      return buildAdminSubprocessUrlV5({
        adminTab: "utilizador",
        target: "create-user-card"
      });
    }

    if (lookup.includes("sessao") || lookup.includes("sessoes") || lookup.includes("sessões")) {
      return buildAdminSubprocessUrlV5({
        adminTab: "sessoes",
        sidebarSectionsTab: "sessoes",
        target: "admin-sidebar-sections-card"
      });
    }

    if (lookup.includes("menu") || lookup.includes("conta") || lookup.includes("configuracao")) {
      return buildAdminSubprocessUrlV5({
        adminTab: "contas",
        target: "admin-account-status-card"
      });
    }

    return null;
  }

  //###################################################################################
  // (5) ABRIR SUBPROCESSO DIRETO SEM DEPENDER DE ORDEM DE CLIQUES
  //###################################################################################

  function abrirSubprocessoDiretoV5(event, element) {
    const destination = resolverSubprocessoPeloElementoV5(element);

    if (!destination) {
      return false;
    }

    if (event) {
      event.preventDefault();
      event.stopPropagation();

      if (typeof event.stopImmediatePropagation === "function") {
        event.stopImmediatePropagation();
      }
    }

    if (document.body) {
      document.body.classList.remove("appverbo-admin-process-only");
      document.body.classList.add("appverbo-subprocess-direct-opening");
      document.body.classList.remove("appverbo-admin-sessoes");
    }

    pararObservadorProcessOnlyV5();

    const currentPath = window.location.pathname + window.location.search + window.location.hash;

    if (currentPath === destination) {
      if (document.body) {
        document.body.classList.remove("appverbo-subprocess-direct-opening");
      }
      return true;
    }

    window.location.assign(destination);
    return true;
  }

  //###################################################################################
  // (6) NORMALIZAR URLS ESPECIAIS
  //###################################################################################

  function normalizarUrlSessoesV5() {
    const url = getCurrentUrlV5();

    if (!urlIndicaSubprocessoSessoesV5(url)) {
      return;
    }

    let changed = false;

    if (cleanValueV5(url.searchParams.get("admin_tab")) !== "sessoes") {
      url.searchParams.set("admin_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV5(url.searchParams.get("sidebar_sections_tab"))) {
      url.searchParams.set("sidebar_sections_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV5(url.searchParams.get("target"))) {
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

  function normalizarUrlAdminProcessOnlyV5() {
    const url = getCurrentUrlV5();

    if (!urlIndicaAdminProcessOnlyV5(url)) {
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
  // (7) APLICAR CLASSES VISUAIS
  //###################################################################################

  function aplicarClasseContextoV5() {
    const url = getCurrentUrlV5();

    if (!document.body) {
      return;
    }

    if (urlIndicaAdminProcessOnlyV5(url)) {
      document.body.classList.add("appverbo-admin-process-only");
      document.body.classList.remove("appverbo-admin-sessoes");
      document.body.classList.remove("appverbo-subprocess-direct-opening");
      iniciarObservadorProcessOnlyV5();
      limparAbaAtivaComRepeticaoV5();
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    document.body.classList.remove("appverbo-subprocess-direct-opening");
    pararObservadorProcessOnlyV5();

    if (urlIndicaSubprocessoSessoesV5(url)) {
      document.body.classList.add("appverbo-admin-sessoes");
    } else {
      document.body.classList.remove("appverbo-admin-sessoes");
    }
  }

  function ativarModoAdminProcessOnlyV5() {
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
    document.body.classList.remove("appverbo-admin-sessoes");
    document.body.classList.remove("appverbo-subprocess-direct-opening");

    iniciarObservadorProcessOnlyV5();
    limparAbaAtivaComRepeticaoV5();
    markReadyV5();
  }

  function desativarModoAdminProcessOnlyV5() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    pararObservadorProcessOnlyV5();

    window.requestAnimationFrame(aplicarClasseContextoV5);
  }

  //###################################################################################
  // (8) INICIALIZAR ESTADO
  //###################################################################################

  function inicializarV5() {
    normalizarUrlSessoesV5();
    normalizarUrlAdminProcessOnlyV5();
    aplicarClasseContextoV5();
    markReadyV5();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.requestAnimationFrame(inicializarV5);
    }, { once: true });
  } else {
    window.requestAnimationFrame(inicializarV5);
  }

  window.addEventListener("load", inicializarV5, { once: true });
  window.addEventListener("pageshow", inicializarV5);

  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(inicializarV5);
  });

  //###################################################################################
  // (9) CLIQUES: PROCESSO ADMINISTRATIVO VS QUALQUER SUBPROCESSO
  //###################################################################################

  document.addEventListener("click", function (event) {
    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const clickedTopSubprocess = target.closest(
      "#submenu-items .submenu-item, #submenu-items button, #submenu-items a, button[data-admin-tab]"
    );

    if (
      clickedTopSubprocess &&
      document.body &&
      document.body.classList.contains("appverbo-admin-process-only")
    ) {
      abrirSubprocessoDiretoV5(event, clickedTopSubprocess);
      return;
    }

    const menuButton = target.closest("button[data-menu]");

    if (menuButton && cleanValueV5(menuButton.getAttribute("data-menu")) === "administrativo") {
      window.setTimeout(ativarModoAdminProcessOnlyV5, 0);
      window.setTimeout(ativarModoAdminProcessOnlyV5, 60);
      window.setTimeout(ativarModoAdminProcessOnlyV5, 180);
      return;
    }

    if (clickedTopSubprocess) {
      window.setTimeout(desativarModoAdminProcessOnlyV5, 0);
      window.setTimeout(desativarModoAdminProcessOnlyV5, 60);
      return;
    }

    const editLink = target.closest(".admin-subprocess-action-link-v1");

    if (editLink) {
      window.setTimeout(desativarModoAdminProcessOnlyV5, 0);
    }
  }, true);
})();
// APPVERBO_NAVIGATION_SMOOTH_V5_END
