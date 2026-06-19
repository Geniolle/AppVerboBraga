// APPVERBO_NAVIGATION_SMOOTH_V4_START
//###################################################################################
// (1) FUNCOES BASE
//###################################################################################

(function () {
  "use strict";

  let observerV4 = null;
  let clearActiveTimerV4 = null;

  function getCurrentUrlV4() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function cleanValueV4(value) {
    return String(value || "").trim().toLowerCase();
  }

  function markReadyV4() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");
  }

  //###################################################################################
  // (2) DETETAR ESTADO ADMINISTRATIVO
  //###################################################################################

  function urlIndicaAdminV4(url) {
    return Boolean(
      url &&
      url.pathname === "/users/new" &&
      cleanValueV4(url.searchParams.get("menu")) === "administrativo"
    );
  }

  function urlIndicaAdminProcessOnlyV4(url) {
    if (!urlIndicaAdminV4(url)) {
      return false;
    }

    const adminTab = cleanValueV4(url.searchParams.get("admin_tab"));
    const target = cleanValueV4(url.searchParams.get("target"));
    const settingsEditKey = cleanValueV4(url.searchParams.get("settings_edit_key"));
    const sidebarSectionEditKey = cleanValueV4(url.searchParams.get("sidebar_section_edit_key"));
    const settingsTab = cleanValueV4(url.searchParams.get("settings_tab"));
    const sidebarSectionsTab = cleanValueV4(url.searchParams.get("sidebar_sections_tab"));
    const hash = cleanValueV4((url.hash || "").replace(/^#/, ""));

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

  function urlIndicaSubprocessoSessoesV4(url) {
    if (!urlIndicaAdminV4(url)) {
      return false;
    }

    const adminTab = cleanValueV4(url.searchParams.get("admin_tab"));
    const target = cleanValueV4(url.searchParams.get("target"));
    const hash = cleanValueV4((url.hash || "").replace(/^#/, ""));
    const settingsTab = cleanValueV4(url.searchParams.get("settings_tab")).replace(/_/g, "-");
    const sidebarSectionsTab = cleanValueV4(url.searchParams.get("sidebar_sections_tab")).replace(/_/g, "-");
    const sidebarSectionEditKey = cleanValueV4(url.searchParams.get("sidebar_section_edit_key"));

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
  // (3) LIMPAR ABA ATIVA DOS SUBPROCESSOS
  //###################################################################################

  function limparAbaAtivaSubprocessoV4() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu) {
      return;
    }

    submenu
      .querySelectorAll(".active, [aria-selected='true'], [data-active='true']")
      .forEach(function (element) {
        element.classList.remove("active");
        element.classList.remove("selected");
        element.classList.remove("is-active");
        element.setAttribute("aria-selected", "false");
        element.removeAttribute("data-active");
        element.removeAttribute("data-selected");
      });
  }

  function iniciarObservadorProcessOnlyV4() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu || observerV4) {
      return;
    }

    observerV4 = new MutationObserver(function () {
      if (!document.body || !document.body.classList.contains("appverbo-admin-process-only")) {
        return;
      }

      limparAbaAtivaSubprocessoV4();
    });

    observerV4.observe(submenu, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["class", "aria-selected", "data-active", "data-selected"]
    });
  }

  function pararObservadorProcessOnlyV4() {
    if (!observerV4) {
      return;
    }

    observerV4.disconnect();
    observerV4 = null;
  }

  function limparAbaAtivaComRepeticaoV4() {
    limparAbaAtivaSubprocessoV4();

    const delays = [0, 20, 80, 160, 320, 650];

    delays.forEach(function (delay) {
      window.setTimeout(function () {
        if (document.body && document.body.classList.contains("appverbo-admin-process-only")) {
          limparAbaAtivaSubprocessoV4();
        }
      }, delay);
    });

    if (clearActiveTimerV4) {
      window.clearInterval(clearActiveTimerV4);
    }

    let count = 0;
    clearActiveTimerV4 = window.setInterval(function () {
      count += 1;

      if (!document.body || !document.body.classList.contains("appverbo-admin-process-only") || count > 20) {
        window.clearInterval(clearActiveTimerV4);
        clearActiveTimerV4 = null;
        return;
      }

      limparAbaAtivaSubprocessoV4();
    }, 100);
  }

  //###################################################################################
  // (4) NORMALIZAR URLS ESPECIAIS
  //###################################################################################

  function normalizarUrlSessoesV4() {
    const url = getCurrentUrlV4();

    if (!urlIndicaSubprocessoSessoesV4(url)) {
      return;
    }

    let changed = false;

    if (cleanValueV4(url.searchParams.get("admin_tab")) !== "sessoes") {
      url.searchParams.set("admin_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV4(url.searchParams.get("sidebar_sections_tab"))) {
      url.searchParams.set("sidebar_sections_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV4(url.searchParams.get("target"))) {
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

  function normalizarUrlAdminProcessOnlyV4() {
    const url = getCurrentUrlV4();

    if (!urlIndicaAdminProcessOnlyV4(url)) {
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
  // (5) APLICAR CLASSES VISUAIS
  //###################################################################################

  function aplicarClasseContextoV4() {
    const url = getCurrentUrlV4();

    if (!document.body) {
      return;
    }

    if (urlIndicaAdminProcessOnlyV4(url)) {
      document.body.classList.add("appverbo-admin-process-only");
      document.body.classList.remove("appverbo-admin-sessoes");
      iniciarObservadorProcessOnlyV4();
      limparAbaAtivaComRepeticaoV4();
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    pararObservadorProcessOnlyV4();

    if (urlIndicaSubprocessoSessoesV4(url)) {
      document.body.classList.add("appverbo-admin-sessoes");
    } else {
      document.body.classList.remove("appverbo-admin-sessoes");
    }
  }

  function ativarModoAdminProcessOnlyV4() {
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

    iniciarObservadorProcessOnlyV4();
    limparAbaAtivaComRepeticaoV4();
    markReadyV4();
  }

  function desativarModoAdminProcessOnlyV4() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    pararObservadorProcessOnlyV4();

    window.requestAnimationFrame(aplicarClasseContextoV4);
  }

  //###################################################################################
  // (6) INICIALIZAR ESTADO
  //###################################################################################

  function inicializarV4() {
    normalizarUrlSessoesV4();
    normalizarUrlAdminProcessOnlyV4();
    aplicarClasseContextoV4();
    markReadyV4();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.requestAnimationFrame(inicializarV4);
    }, { once: true });
  } else {
    window.requestAnimationFrame(inicializarV4);
  }

  window.addEventListener("load", inicializarV4, { once: true });
  window.addEventListener("pageshow", inicializarV4);

  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(inicializarV4);
  });

  //###################################################################################
  // (7) CLIQUES: PROCESSO ADMINISTRATIVO VS SUBPROCESSOS
  //###################################################################################

  document.addEventListener("click", function (event) {
    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const menuButton = target.closest("button[data-menu]");

    if (menuButton && cleanValueV4(menuButton.getAttribute("data-menu")) === "administrativo") {
      window.setTimeout(ativarModoAdminProcessOnlyV4, 0);
      window.setTimeout(ativarModoAdminProcessOnlyV4, 60);
      window.setTimeout(ativarModoAdminProcessOnlyV4, 180);
      return;
    }

    const clickedTopSubprocess = target.closest(
      "#submenu-items .submenu-item, #submenu-items button, #submenu-items a, button[data-admin-tab]"
    );

    if (clickedTopSubprocess) {
      window.setTimeout(desativarModoAdminProcessOnlyV4, 0);
      window.setTimeout(desativarModoAdminProcessOnlyV4, 60);
      return;
    }

    const editLink = target.closest(".admin-subprocess-action-link-v1");

    if (editLink) {
      window.setTimeout(desativarModoAdminProcessOnlyV4, 0);
    }
  }, true);
})();
// APPVERBO_NAVIGATION_SMOOTH_V4_END
