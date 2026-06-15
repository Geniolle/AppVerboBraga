//###################################################################################
// (1) ADMIN SERVER-RENDER VISIBILITY GUARD V1
//###################################################################################
(function registerAdminServerRenderVisibilityGuardV1() {
  "use strict";

  const SUPPORTED_MENU_SCOPES_V1 = new Set(["administrativo", "sessoes"]);
  const ADMIN_BODY_CLASSES_V1 = Object.freeze([
    "appverbo-admin-tab-entidade",
    "appverbo-admin-tab-utilizador",
    "appverbo-admin-tab-sessoes",
    "appverbo-admin-tab-menu",
    "appverbo-admin-tab-definicoes",
    "appverbo-admin-tab-contas",
    "appverbo-admin-tab-perfil"
  ]);
  const SERVER_RENDER_TAB_IDS_V1 = Object.freeze({
    sessoes: Object.freeze([
      "menu-tabs-card",
      "admin-sidebar-sections-card-create",
      "admin-sidebar-sections-form-card",
      "admin-sidebar-sections-card",
      "admin-sidebar-sections-card-inactive"
    ]),
    menu: Object.freeze([
      "menu-tabs-card",
      "admin-menu-card-create",
      "settings-menu-edit-card",
      "admin-menu-card",
      "admin-menu-card-inactive"
    ]),
    definicoes: Object.freeze([
      "menu-tabs-card",
      "admin-definicoes-card-create",
      "admin-definicoes-card-edit",
      "admin-definicoes-card",
      "admin-definicoes-card-inactive"
    ]),
    perfil: Object.freeze([
      "menu-tabs-card",
      "admin-perfil-card-create",
      "admin-perfil-card-edit",
      "admin-perfil-card",
      "admin-perfil-card-inactive"
    ])
  });

  //###################################################################################
  // (2) HELPERS
  //###################################################################################

  function cleanValueV1(value) {
    return String(value || "").trim().toLowerCase();
  }

  function getCurrentUrlV1() {
    try {
      return new URL(window.location.href);
    } catch (_error) {
      return null;
    }
  }

  function isSupportedRouteV1(url) {
    return Boolean(
      url &&
      url.pathname === "/users/new" &&
      SUPPORTED_MENU_SCOPES_V1.has(cleanValueV1(url.searchParams.get("menu")))
    );
  }

  function showElementV1(element) {
    if (!element || !element.style) {
      return;
    }

    element.removeAttribute("hidden");
    element.style.setProperty("display", "block", "important");
    element.style.setProperty("visibility", "visible", "important");
    element.style.setProperty("opacity", "1", "important");
  }

  function hideElementV1(element) {
    if (!element || !element.style) {
      return;
    }

    element.style.setProperty("display", "none", "important");
  }

  function getKnownServerRenderIdsV1() {
    const ids = new Set();
    Object.keys(SERVER_RENDER_TAB_IDS_V1).forEach(function (tabKey) {
      (SERVER_RENDER_TAB_IDS_V1[tabKey] || []).forEach(function (cardId) {
        if (cardId) {
          ids.add(cardId);
        }
      });
    });
    return ids;
  }

  function resolveServerRenderTabV1(url) {
    if (!isSupportedRouteV1(url)) {
      return "";
    }

    const adminTab = cleanValueV1(url.searchParams.get("admin_tab"));
    const target = cleanValueV1(url.searchParams.get("target"));
    const hash = cleanValueV1((url.hash || "").replace(/^#/, ""));
    const settingsTab = cleanValueV1(url.searchParams.get("settings_tab")).replace(/_/g, "-");
    const sidebarSectionsTab = cleanValueV1(url.searchParams.get("sidebar_sections_tab")).replace(/_/g, "-");

    if (
      adminTab === "sessoes" ||
      settingsTab === "sessoes" ||
      sidebarSectionsTab === "sessoes" ||
      target.includes("admin-sidebar-sections") ||
      hash.includes("admin-sidebar-sections")
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
      adminTab === "perfil" ||
      target.includes("admin-perfil-card") ||
      hash.includes("admin-perfil-card")
    ) {
      return "perfil";
    }

    return "";
  }

  function syncBodyClassesV1(activeTab) {
    if (!document.body || !activeTab) {
      return;
    }

    ADMIN_BODY_CLASSES_V1.forEach(function (className) {
      document.body.classList.remove(className);
    });

    document.body.classList.remove("appverbo-admin-process-only");
    document.body.classList.add("appverbo-admin-subprocess-context");
    document.body.classList.add("appverbo-admin-submenu-stable");
    document.body.classList.toggle("appverbo-admin-sessoes", activeTab === "sessoes");
    document.body.classList.toggle("appverbo-sessoes-render-ok", activeTab === "sessoes");
    document.body.classList.add("appverbo-admin-tab-" + activeTab);
  }

  function syncCardsByTabV1(activeTab) {
    const visibleIds = new Set(SERVER_RENDER_TAB_IDS_V1[activeTab] || []);
    const knownIds = getKnownServerRenderIdsV1();

    document.querySelectorAll("[data-admin-subprocess]").forEach(function (card) {
      const subprocessKey = cleanValueV1(card.getAttribute("data-admin-subprocess"));
      if (!Object.prototype.hasOwnProperty.call(SERVER_RENDER_TAB_IDS_V1, subprocessKey)) {
        return;
      }

      if (subprocessKey === activeTab) {
        showElementV1(card);
      } else {
        hideElementV1(card);
      }
    });

    knownIds.forEach(function (cardId) {
      const card = document.getElementById(cardId);
      if (!card) {
        return;
      }

      if (visibleIds.has(cardId)) {
        showElementV1(card);
      } else if (!card.hasAttribute("data-admin-subprocess")) {
        hideElementV1(card);
      }
    });
  }

  //###################################################################################
  // (3) APPLY GUARD
  //###################################################################################

  function applyServerRenderVisibilityGuardV1() {
    const url = getCurrentUrlV1();
    const activeTab = resolveServerRenderTabV1(url);

    if (!activeTab) {
      return;
    }

    syncBodyClassesV1(activeTab);
    syncCardsByTabV1(activeTab);

    window.dispatchEvent(new CustomEvent("appverbo:admin-card-stack-order-v1"));
  }

  //###################################################################################
  // (4) INIT
  //###################################################################################

  document.addEventListener("DOMContentLoaded", applyServerRenderVisibilityGuardV1, { once: true });
  window.addEventListener("load", applyServerRenderVisibilityGuardV1, { once: true });
  window.addEventListener("pageshow", applyServerRenderVisibilityGuardV1);
  window.setTimeout(applyServerRenderVisibilityGuardV1, 120);
  window.setTimeout(applyServerRenderVisibilityGuardV1, 350);
  window.setTimeout(applyServerRenderVisibilityGuardV1, 800);
})();
