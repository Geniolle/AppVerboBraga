// APPVERBO_ADMIN_ENTIDADE_V2_USERS_NEW_START
(function setupAdminEntidadeV2UsersNewV2() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function hasEntidadeV2RootV2() {
    return Boolean(document.querySelector("[data-admin-entidade-v2-integrated='1']"));
  }

  function hideElementV2(element) {
    if (!element) {
      return;
    }

    element.dataset.adminEntidadeV2LegacyHidden = "1";
    element.hidden = true;
    element.style.display = "none";
  }

  //###################################################################################
  // (2) OCULTAR LEGADO DA ENTIDADE QUANDO V2 ESTIVER ATIVO
  //###################################################################################

  function hideLegacyEntidadeCardsV2() {
    if (!hasEntidadeV2RootV2()) {
      return;
    }

    const legacySelectors = [
      "#create-entity-card",
      "#edit-entity-card",
      "#entities-card",
      "#active-entities-card",
      "#inactive-entities-card",
      "#entity-list-card",
      "#entity-active-card",
      "#entity-inactive-card",
      "#entity-view-card"
    ];

    const legacySummaryCardIds = new Set(["recent-entities-card", "inactive-entities-card"]);

    legacySelectors.forEach((selector) => {
      document.querySelectorAll(selector).forEach(hideElementV2);
    });

    document.querySelectorAll("section[id], .card[id]").forEach((element) => {
      const elementId = String(element.id || "").toLowerCase();

      if (!elementId) {
        return;
      }

      if (legacySummaryCardIds.has(elementId)) {
        return;
      }

      const isLegacyEntityCard =
        elementId.includes("entity") ||
        elementId.includes("entities") ||
        elementId.includes("entidade");

      if (!isLegacyEntityCard) {
        return;
      }

      if (element.closest("[data-admin-entidade-v2-integrated='1']")) {
        return;
      }

      hideElementV2(element);
    });
  }

  //###################################################################################
  // (3) GARANTIR TARGET V2 NA URL
  //###################################################################################

  function ensureEntidadeV2TargetV2() {
    if (!hasEntidadeV2RootV2()) {
      return;
    }

    try {
      const params = new URLSearchParams(window.location.search);

      if (params.get("menu") !== "administrativo" || params.get("admin_tab") !== "entidade") {
        return;
      }

      const currentTarget = params.get("target") || "";

      if (currentTarget && currentTarget.includes("admin-subprocess-v2-entidade")) {
        return;
      }

      params.set("target", "#admin-subprocess-v2-entidade");

      const cleanUrl = window.location.pathname + "?" + params.toString() + window.location.hash;

      if (window.history && typeof window.history.replaceState === "function") {
        window.history.replaceState(window.history.state, document.title, cleanUrl);
      }
    } catch (error) {
      // Ignora ambiente sem URLSearchParams.
    }
  }

  function runEntidadeV2IntegrationV2() {
    hideLegacyEntidadeCardsV2();
    ensureEntidadeV2TargetV2();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", runEntidadeV2IntegrationV2);
  } else {
    runEntidadeV2IntegrationV2();
  }

  window.setTimeout(runEntidadeV2IntegrationV2, 100);
  window.setTimeout(runEntidadeV2IntegrationV2, 400);
  window.setTimeout(runEntidadeV2IntegrationV2, 1200);
})();
// APPVERBO_ADMIN_ENTIDADE_V2_USERS_NEW_END
