// APPVERBO_NAVIGATION_SMOOTH_V2_START
//###################################################################################
// (1) NORMALIZAR URL DO SUBPROCESSO SESSOES NO REFRESH
//###################################################################################

(function () {
  "use strict";

  function getCurrentUrlV2() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function cleanValueV2(value) {
    return String(value || "").trim().toLowerCase();
  }

  function urlIndicaSubprocessoSessoesV2(url) {
    if (!url || url.pathname !== "/users/new") {
      return false;
    }

    const menu = cleanValueV2(url.searchParams.get("menu"));
    const adminTab = cleanValueV2(url.searchParams.get("admin_tab"));
    const target = cleanValueV2(url.searchParams.get("target"));
    const hash = cleanValueV2((url.hash || "").replace(/^#/, ""));
    const settingsTab = cleanValueV2(url.searchParams.get("settings_tab")).replace(/_/g, "-");
    const sidebarSectionsTab = cleanValueV2(url.searchParams.get("sidebar_sections_tab")).replace(/_/g, "-");
    const sidebarSectionEditKey = cleanValueV2(url.searchParams.get("sidebar_section_edit_key"));

    if (menu !== "administrativo") {
      return false;
    }

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

  function normalizarUrlSessoesV2() {
    const url = getCurrentUrlV2();

    if (!urlIndicaSubprocessoSessoesV2(url)) {
      return;
    }

    let changed = false;

    if (cleanValueV2(url.searchParams.get("admin_tab")) !== "sessoes") {
      url.searchParams.set("admin_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV2(url.searchParams.get("sidebar_sections_tab"))) {
      url.searchParams.set("sidebar_sections_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV2(url.searchParams.get("target"))) {
      url.searchParams.set("target", "admin-sidebar-sections-card");
      changed = true;
    }

    if (!url.hash) {
      url.hash = "admin-sidebar-sections-card";
      changed = true;
    }

    if (changed && window.history && typeof window.history.replaceState === "function") {
      const nextUrl = url.pathname + url.search + url.hash;
      window.history.replaceState(window.history.state, document.title, nextUrl);
    }
  }

  //###################################################################################
  // (2) APLICAR CLASSE DE CONTEXTO PARA EVITAR MISTURA VISUAL
  //###################################################################################

  function aplicarClasseContextoV2() {
    const url = getCurrentUrlV2();

    if (!document.body) {
      return;
    }

    if (urlIndicaSubprocessoSessoesV2(url)) {
      document.body.classList.add("appverbo-admin-sessoes");
    } else {
      document.body.classList.remove("appverbo-admin-sessoes");
    }
  }

  //###################################################################################
  // (3) LIBERTAR TELA APOS NORMALIZAR ESTADO
  //###################################################################################

  function liberarTelaV2() {
    if (!document.body) {
      return;
    }

    aplicarClasseContextoV2();
    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");
  }

  normalizarUrlSessoesV2();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      normalizarUrlSessoesV2();
      window.requestAnimationFrame(liberarTelaV2);
    }, { once: true });
  } else {
    window.requestAnimationFrame(liberarTelaV2);
  }

  window.addEventListener("pageshow", function () {
    normalizarUrlSessoesV2();
    liberarTelaV2();
  });

  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(aplicarClasseContextoV2);
  });

  //###################################################################################
  // (4) MARCAR NAVEGACAO LOCAL PARA REDUZIR PISCAR EM ABAS
  //###################################################################################

  let localNavigationTimer = null;

  function marcarNavegacaoLocalV2() {
    if (!document.body) {
      return;
    }

    document.body.classList.add("appverbo-local-navigation");

    if (localNavigationTimer) {
      window.clearTimeout(localNavigationTimer);
    }

    localNavigationTimer = window.setTimeout(function () {
      document.body.classList.remove("appverbo-local-navigation");
      aplicarClasseContextoV2();
      localNavigationTimer = null;
    }, 180);
  }

  document.addEventListener("click", function (event) {
    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const navigationControl = target.closest(
      "button[data-menu], button[data-admin-tab], button[data-profile-section], button[data-dynamic-process-section], .submenu-item, .profile-process-tab-btn, .admin-subprocess-action-link-v1"
    );

    if (!navigationControl) {
      return;
    }

    marcarNavegacaoLocalV2();
  }, true);
})();
// APPVERBO_NAVIGATION_SMOOTH_V2_END
