// APPVERBO_NAVIGATION_SMOOTH_V3_START
//###################################################################################
// (1) FUNCOES BASE
//###################################################################################

(function () {
  "use strict";

  function getCurrentUrlV3() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function cleanValueV3(value) {
    return String(value || "").trim().toLowerCase();
  }

  function removeActiveTopSubprocessTabsV3() {
    document
      .querySelectorAll("#submenu-items .active, #submenu-items [aria-selected='true']")
      .forEach(function (element) {
        element.classList.remove("active");
        element.setAttribute("aria-selected", "false");
      });
  }

  function markReadyV3() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");
  }

  //###################################################################################
  // (2) DETETAR CONTEXTOS
  //###################################################################################

  function urlIndicaAdminV3(url) {
    return Boolean(
      url &&
      url.pathname === "/users/new" &&
      cleanValueV3(url.searchParams.get("menu")) === "administrativo"
    );
  }

  function urlIndicaSubprocessoSessoesV3(url) {
    if (!urlIndicaAdminV3(url)) {
      return false;
    }

    const adminTab = cleanValueV3(url.searchParams.get("admin_tab"));
    const target = cleanValueV3(url.searchParams.get("target"));
    const hash = cleanValueV3((url.hash || "").replace(/^#/, ""));
    const settingsTab = cleanValueV3(url.searchParams.get("settings_tab")).replace(/_/g, "-");
    const sidebarSectionsTab = cleanValueV3(url.searchParams.get("sidebar_sections_tab")).replace(/_/g, "-");
    const sidebarSectionEditKey = cleanValueV3(url.searchParams.get("sidebar_section_edit_key"));

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

  function urlIndicaAdminProcessOnlyV3(url) {
    if (!urlIndicaAdminV3(url)) {
      return false;
    }

    const adminTab = cleanValueV3(url.searchParams.get("admin_tab"));
    const target = cleanValueV3(url.searchParams.get("target"));
    const settingsEditKey = cleanValueV3(url.searchParams.get("settings_edit_key"));
    const sidebarSectionEditKey = cleanValueV3(url.searchParams.get("sidebar_section_edit_key"));
    const settingsTab = cleanValueV3(url.searchParams.get("settings_tab"));
    const sidebarSectionsTab = cleanValueV3(url.searchParams.get("sidebar_sections_tab"));
    const hash = cleanValueV3((url.hash || "").replace(/^#/, ""));

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

  //###################################################################################
  // (3) NORMALIZAR URLS ESPECIAIS
  //###################################################################################

  function normalizarUrlSessoesV3() {
    const url = getCurrentUrlV3();

    if (!urlIndicaSubprocessoSessoesV3(url)) {
      return;
    }

    let changed = false;

    if (cleanValueV3(url.searchParams.get("admin_tab")) !== "sessoes") {
      url.searchParams.set("admin_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV3(url.searchParams.get("sidebar_sections_tab"))) {
      url.searchParams.set("sidebar_sections_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV3(url.searchParams.get("target"))) {
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

  function normalizarUrlAdminProcessOnlyV3() {
    const url = getCurrentUrlV3();

    if (!urlIndicaAdminProcessOnlyV3(url)) {
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
  // (4) APLICAR CLASSES VISUAIS
  //###################################################################################

  function aplicarClasseContextoV3() {
    const url = getCurrentUrlV3();

    if (!document.body) {
      return;
    }

    if (urlIndicaAdminProcessOnlyV3(url)) {
      document.body.classList.add("appverbo-admin-process-only");
      document.body.classList.remove("appverbo-admin-sessoes");
      removeActiveTopSubprocessTabsV3();
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");

    if (urlIndicaSubprocessoSessoesV3(url)) {
      document.body.classList.add("appverbo-admin-sessoes");
    } else {
      document.body.classList.remove("appverbo-admin-sessoes");
    }
  }

  function ativarModoAdminProcessOnlyV3() {
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
    removeActiveTopSubprocessTabsV3();
    markReadyV3();
  }

  function desativarModoAdminProcessOnlyV3() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    window.requestAnimationFrame(aplicarClasseContextoV3);
  }

  //###################################################################################
  // (5) INICIALIZAR ESTADO
  //###################################################################################

  function inicializarV3() {
    normalizarUrlSessoesV3();
    normalizarUrlAdminProcessOnlyV3();
    aplicarClasseContextoV3();
    markReadyV3();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.requestAnimationFrame(inicializarV3);
    }, { once: true });
  } else {
    window.requestAnimationFrame(inicializarV3);
  }

  window.addEventListener("pageshow", inicializarV3);

  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(inicializarV3);
  });

  //###################################################################################
  // (6) CLIQUES: PROCESSO ADMINISTRATIVO VS SUBPROCESSOS
  //###################################################################################

  document.addEventListener("click", function (event) {
    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const menuButton = target.closest("button[data-menu]");

    if (menuButton && cleanValueV3(menuButton.getAttribute("data-menu")) === "administrativo") {
      window.setTimeout(ativarModoAdminProcessOnlyV3, 0);
      window.setTimeout(ativarModoAdminProcessOnlyV3, 60);
      return;
    }

    const clickedTopSubprocess = target.closest(
      "#submenu-items .submenu-item, #submenu-items button, #submenu-items a, button[data-admin-tab]"
    );

    if (clickedTopSubprocess) {
      window.setTimeout(desativarModoAdminProcessOnlyV3, 0);
      window.setTimeout(desativarModoAdminProcessOnlyV3, 60);
      return;
    }

    const editLink = target.closest(".admin-subprocess-action-link-v1");

    if (editLink) {
      window.setTimeout(desativarModoAdminProcessOnlyV3, 0);
    }
  }, true);
})();
// APPVERBO_NAVIGATION_SMOOTH_V3_END
