(function () {
  "use strict";

  // APPVERBO_PAGINA_DEFAULT_REFRESH_HOME_PROTECTED_AREA_V1_START
  // Regra visual do browser:
  // - reload normal em /users/new volta para HOME;
  // - retorno de salvar/criar preserva contexto via appverbo_after_save;
  // - não colocar regras de subprocessos aqui.
  // APPVERBO_PAGINA_DEFAULT_REFRESH_HOME_PROTECTED_AREA_V1_END

  if (window.__appverboPaginaDefaultRefreshHomeV1Loaded) {
    return;
  }

  window.__appverboPaginaDefaultRefreshHomeV1Loaded = true;

  function getNavigationType_v1() {
    const entries = (
      window.performance &&
      typeof window.performance.getEntriesByType === "function"
    )
      ? window.performance.getEntriesByType("navigation")
      : [];

    if (entries && entries.length && entries[0] && entries[0].type) {
      return entries[0].type;
    }

    if (
      window.performance &&
      window.performance.navigation &&
      window.performance.navigation.type === 1
    ) {
      return "reload";
    }

    return "";
  }

  function hasValue_v1(url, key) {
    return url.searchParams.has(key) && String(url.searchParams.get(key) || "").trim() !== "";
  }

  function hasStableContextParams_v1(url) {
    if (!url) {
      return false;
    }

    const menuValue = String(url.searchParams.get("menu") || "").trim().toLowerCase();
    if (menuValue && menuValue !== "home") {
      return true;
    }

    const targetValue = String(url.searchParams.get("target") || "").trim();
    if (targetValue) {
      return true;
    }

    const contextParams = [
      "admin_tab",
      "sidebar_sections_tab",
      "settings_edit_key",
      "settings_action",
      "settings_tab",
      "dynamic_process_section",
      "section_key",
      "profile_tab",
      "profile_section",
      "entity_edit_id",
      "user_edit_id",
      "definition_edit_id",
      "entity_view",
      "user_view"
    ];

    return contextParams.some((key) => hasValue_v1(url, key));
  }

  function shouldPreserveCurrentUrl_v1(url) {
    const preserveParams = [
      "appverbo_after_save",
      "success",
      "error",
      "invite_link",
      "entity_success",
      "entity_error",
      "profile_success",
      "profile_error",
      "settings_success",
      "settings_error"
    ];

    for (const key of preserveParams) {
      if (hasValue_v1(url, key)) {
        return true;
      }
    }

    if (hasStableContextParams_v1(url)) {
      return true;
    }

    return false;
  }

  function isUsersNewPage_v1(url) {
    return url.pathname === "/users/new";
  }

  function isAlreadyHome_v1(url) {
    const menu = String(url.searchParams.get("menu") || "home").trim().toLowerCase();

    return menu === "home" && !url.hash;
  }

  function redirectBrowserRefreshToHome_v1() {
    const currentUrl = new URL(window.location.href);

    if (!isUsersNewPage_v1(currentUrl)) {
      return;
    }

    if (getNavigationType_v1() !== "reload") {
      return;
    }

    if (shouldPreserveCurrentUrl_v1(currentUrl)) {
      return;
    }

    if (isAlreadyHome_v1(currentUrl)) {
      return;
    }

    window.location.replace("/users/new?menu=home");
  }

  redirectBrowserRefreshToHome_v1();
})();
