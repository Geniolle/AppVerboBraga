// APPVERBO_SUBPROCESS_ACTIVE_GUARD_V1_START
//###################################################################################
// (1) FUNCOES BASE
//###################################################################################

(function () {
  "use strict";

  let guardObserverV1 = null;
  let guardRunningV1 = false;
  let repeatTimerV1 = null;

  function cleanValueV1(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeTextV1(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ");
  }

  function getCurrentUrlV1() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function isAdminPageV1(url) {
    return Boolean(
      url &&
      url.pathname === "/users/new" &&
      cleanValueV1(url.searchParams.get("menu")) === "administrativo"
    );
  }

  function shouldBypassGuardV1() {
    return Boolean(
      document.querySelector("script[src*='appverbo_navigation_smooth_v7.js']")
    );
  }

  //###################################################################################
  // (2) DESCOBRIR QUAL SUBPROCESSO DEVE ESTAR ATIVO
  //###################################################################################

  function getTabFromUrlV1() {
    const url = getCurrentUrlV1();

    if (!isAdminPageV1(url)) {
      return "";
    }

    const adminTab = cleanValueV1(url.searchParams.get("admin_tab"));
    const target = cleanValueV1(url.searchParams.get("target"));
    const hash = cleanValueV1((url.hash || "").replace(/^#/, ""));
    const settingsTab = cleanValueV1(url.searchParams.get("settings_tab")).replace(/_/g, "-");
    const sidebarSectionsTab = cleanValueV1(url.searchParams.get("sidebar_sections_tab")).replace(/_/g, "-");
    const sidebarSectionEditKey = cleanValueV1(url.searchParams.get("sidebar_section_edit_key"));

    if (
      adminTab === "entidade" ||
      target.includes("entity") ||
      target.includes("entidade") ||
      hash.includes("entity") ||
      hash.includes("entidade")
    ) {
      return "entidade";
    }

    if (
      adminTab === "utilizador" ||
      target.includes("user") ||
      target.includes("utilizador") ||
      hash.includes("user") ||
      hash.includes("utilizador")
    ) {
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
      target.includes("sessoes") ||
      hash.includes("admin-sidebar-sections") ||
      hash.includes("sidebar-sections") ||
      hash.includes("sessoes")
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
      target.includes("account-status") ||
      hash.includes("admin-account-status") ||
      hash.includes("account-status")
    ) {
      return "contas";
    }

    if (
      adminTab === "perfil" ||
      target.includes("admin-perfil-card") ||
      hash.includes("admin-perfil-card")
    ) {
      return "perfil";
    }

    return "";
  }

  function getTabFromElementV1(element) {
    if (!element) {
      return "";
    }

    const rawAdminTab = cleanValueV1(
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

    const rawTarget = cleanValueV1(
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

    const href = element.getAttribute("href") || "";
    if (href) {
      try {
        const url = new URL(href, window.location.origin);
        const adminTabFromHref = cleanValueV1(url.searchParams.get("admin_tab"));
        const targetFromHref = cleanValueV1(url.searchParams.get("target"));

        if (adminTabFromHref === "entidade" || targetFromHref.includes("entity")) {
          return "entidade";
        }

        if (adminTabFromHref === "utilizador" || targetFromHref.includes("user")) {
          return "utilizador";
        }

        if (adminTabFromHref === "sessoes" || targetFromHref.includes("sidebar-sections")) {
          return "sessoes";
        }

        if (
          adminTabFromHref === "menu" ||
          targetFromHref.includes("admin-menu-card") ||
          targetFromHref.includes("settings-menu-edit-card")
        ) {
          return "menu";
        }

        if (
          adminTabFromHref === "definicoes" ||
          targetFromHref.includes("admin-definicoes-card")
        ) {
          return "definicoes";
        }

        if (adminTabFromHref === "contas" || targetFromHref.includes("account")) {
          return "contas";
        }
      } catch (error) {
        // ignora href invalido
      }
    }

    const lookup = normalizeTextV1([
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

  //###################################################################################
  // (3) APLICAR CLASSES DE BODY
  //###################################################################################

  function syncBodyClassesV1(activeTab) {
    if (!document.body) {
      return;
    }

    [
      "appverbo-admin-tab-entidade",
      "appverbo-admin-tab-utilizador",
      "appverbo-admin-tab-sessoes",
      "appverbo-admin-tab-menu",
      "appverbo-admin-tab-definicoes",
      "appverbo-admin-tab-contas"
    ].forEach(function (className) {
      document.body.classList.remove(className);
    });

    if (activeTab === "entidade") {
      document.body.classList.add("appverbo-admin-tab-entidade");
      document.body.classList.remove("appverbo-admin-sessoes");
      return;
    }

    if (activeTab === "utilizador") {
      document.body.classList.add("appverbo-admin-tab-utilizador");
      document.body.classList.remove("appverbo-admin-sessoes");
      return;
    }

    if (activeTab === "sessoes") {
      document.body.classList.add("appverbo-admin-tab-sessoes");
      document.body.classList.add("appverbo-admin-sessoes");
      return;
    }

    if (activeTab === "menu") {
      document.body.classList.add("appverbo-admin-tab-menu");
      document.body.classList.remove("appverbo-admin-sessoes");
      return;
    }

    if (activeTab === "definicoes") {
      document.body.classList.add("appverbo-admin-tab-definicoes");
      document.body.classList.remove("appverbo-admin-sessoes");
      return;
    }

    if (activeTab === "contas") {
      document.body.classList.add("appverbo-admin-tab-contas");
      document.body.classList.remove("appverbo-admin-sessoes");
    }
  }

  //###################################################################################
  // (4) FORCAR APENAS UMA ABA ATIVA
  //###################################################################################

  function getSubmenuItemsV1() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu) {
      return [];
    }

    const items = Array.from(
      submenu.querySelectorAll(".submenu-item, button, a, [data-admin-tab], [data-tab], [aria-controls]")
    );

    return items.filter(function (element) {
      return getTabFromElementV1(element) !== "";
    });
  }

  function applyActiveTabV1(preferredTab) {
    if (guardRunningV1) {
      return;
    }

    const activeTab = preferredTab || getTabFromUrlV1();
    const submenu = document.getElementById("submenu-items");

    if (!submenu) {
      return;
    }

    guardRunningV1 = true;

    try {
      syncBodyClassesV1(activeTab);

      const items = getSubmenuItemsV1();
      let hasActiveItem = false;

      items.forEach(function (element) {
        const elementTab = getTabFromElementV1(element);
        const isActive = Boolean(activeTab && elementTab === activeTab);

        element.classList.toggle("active", isActive);
        element.classList.toggle("selected", isActive);
        element.classList.toggle("is-active", isActive);
        element.setAttribute("aria-selected", isActive ? "true" : "false");
        element.setAttribute("data-appverbo-subprocess-tab", elementTab);

        if (isActive) {
          element.setAttribute("data-appverbo-force-active", "true");
          element.removeAttribute("data-appverbo-force-inactive");
          hasActiveItem = true;
        } else {
          element.setAttribute("data-appverbo-force-inactive", "true");
          element.removeAttribute("data-appverbo-force-active");
          element.removeAttribute("data-active");
          element.removeAttribute("data-selected");
        }
      });

      if (!activeTab || !hasActiveItem) {
        items.forEach(function (element) {
          element.classList.remove("active");
          element.classList.remove("selected");
          element.classList.remove("is-active");
          element.setAttribute("aria-selected", "false");
          element.setAttribute("data-appverbo-force-inactive", "true");
          element.removeAttribute("data-appverbo-force-active");
          element.removeAttribute("data-active");
          element.removeAttribute("data-selected");
        });
      }
    } finally {
      guardRunningV1 = false;
    }
  }

  function applyActiveTabRepeatedV1(tab) {
    applyActiveTabV1(tab);

    [0, 20, 60, 120, 240, 500, 900].forEach(function (delay) {
      window.setTimeout(function () {
        applyActiveTabV1(tab);
      }, delay);
    });

    if (repeatTimerV1) {
      window.clearInterval(repeatTimerV1);
    }

    let count = 0;
    repeatTimerV1 = window.setInterval(function () {
      count += 1;

      if (count > 20) {
        window.clearInterval(repeatTimerV1);
        repeatTimerV1 = null;
        return;
      }

      applyActiveTabV1(tab);
    }, 100);
  }

  //###################################################################################
  // (5) OBSERVAR ALTERACOES DE OUTROS SCRIPTS
  //###################################################################################

  function startObserverV1() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu || guardObserverV1) {
      return;
    }

    guardObserverV1 = new MutationObserver(function () {
      if (guardRunningV1) {
        return;
      }

      window.requestAnimationFrame(function () {
        applyActiveTabV1();
      });
    });

    guardObserverV1.observe(submenu, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: [
        "class",
        "aria-selected",
        "data-active",
        "data-selected",
        "data-appverbo-force-active",
        "data-appverbo-force-inactive"
      ]
    });
  }

  //###################################################################################
  // (6) INICIALIZAR E ESCUTAR CLIQUES
  //###################################################################################

  function initV1() {
    if (shouldBypassGuardV1()) {
      return;
    }

    startObserverV1();
    applyActiveTabRepeatedV1();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initV1, { once: true });
  } else {
    initV1();
  }

  window.addEventListener("load", initV1, { once: true });
  window.addEventListener("pageshow", initV1);

  window.addEventListener("popstate", function () {
    if (shouldBypassGuardV1()) {
      return;
    }

    window.requestAnimationFrame(function () {
      applyActiveTabRepeatedV1();
    });
  });

  document.addEventListener("click", function (event) {
    if (shouldBypassGuardV1()) {
      return;
    }

    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const clickedSubprocess = target.closest(
      "#submenu-items .submenu-item, #submenu-items button, #submenu-items a, #submenu-items [data-admin-tab], #submenu-items [aria-controls]"
    );

    if (!clickedSubprocess) {
      return;
    }

    const clickedTab = getTabFromElementV1(clickedSubprocess);

    if (!clickedTab) {
      return;
    }

    applyActiveTabRepeatedV1(clickedTab);
  }, true);
})();
// APPVERBO_SUBPROCESS_ACTIVE_GUARD_V1_END
