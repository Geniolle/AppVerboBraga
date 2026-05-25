// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_START
(function initPostSaveContextNavigationGuardV3() {
  "use strict";

  //###################################################################################
  // (1) CONSTANTES E HELPERS
  //###################################################################################

  const APPVERBO_POST_SAVE_CONTEXT_KEY_V3 = "appverbo:post-save-context-v3";
  const APPVERBO_POST_SAVE_CONTEXT_MAX_AGE_MS_V3 = 120000;

  function getAppVerboCurrentUrlPostSaveV3() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function isAppVerboPostSaveFeedbackUrlV3(url) {
    if (!url) {
      return false;
    }

    if (url.searchParams.get("appverbo_after_save") === "1") {
      return true;
    }

    for (const rawKey of url.searchParams.keys()) {
      const key = String(rawKey || "").trim().toLowerCase();

      if (
        key === "success" ||
        key === "error" ||
        key.endsWith("_success") ||
        key.endsWith("_error")
      ) {
        return true;
      }
    }

    return false;
  }

  function hasStableUsersNewContextV3(url) {
    if (!url || url.pathname !== "/users/new") {
      return false;
    }

    const menuValue = String(url.searchParams.get("menu") || "").trim().toLowerCase();
    const targetValue = String(url.searchParams.get("target") || "").trim();

    if (menuValue && menuValue !== "home") {
      return true;
    }

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

    return contextParams.some((paramName) => {
      const value = String(url.searchParams.get(paramName) || "").trim();
      return Boolean(value);
    });
  }

  function readAndClearAppVerboPostSaveContextV3() {
    try {
      const rawValue = window.sessionStorage.getItem(APPVERBO_POST_SAVE_CONTEXT_KEY_V3) || "";

      if (!rawValue) {
        return null;
      }

      window.sessionStorage.removeItem(APPVERBO_POST_SAVE_CONTEXT_KEY_V3);

      const parsedValue = JSON.parse(rawValue);
      const createdAt = Number(parsedValue && parsedValue.createdAt || 0);

      if (!createdAt || Date.now() - createdAt > APPVERBO_POST_SAVE_CONTEXT_MAX_AGE_MS_V3) {
        return null;
      }

      if (!parsedValue || typeof parsedValue.url !== "string" || !parsedValue.url.trim()) {
        return null;
      }

      return parsedValue;
    } catch (error) {
      return null;
    }
  }

  function copyPostSaveFeedbackParamsV3(sourceUrl, targetUrl) {
    if (!sourceUrl || !targetUrl) {
      return;
    }

    Array.from(sourceUrl.searchParams.keys()).forEach((rawKey) => {
      const key = String(rawKey || "").trim().toLowerCase();

      if (
        key === "success" ||
        key === "error" ||
        key.endsWith("_success") ||
        key.endsWith("_error")
      ) {
        targetUrl.searchParams.set(rawKey, sourceUrl.searchParams.get(rawKey) || "");
      }
    });
  }

  function clearPostSaveFeedbackMarkersFromUrlV3() {
    const url = getAppVerboCurrentUrlPostSaveV3();

    if (!url) {
      return;
    }

    let changed = false;

    Array.from(url.searchParams.keys()).forEach((rawKey) => {
      const key = String(rawKey || "").trim().toLowerCase();

      if (key === "appverbo_after_save") {
        url.searchParams.delete(rawKey);
        changed = true;
      }
    });

    if (!changed || !window.history || typeof window.history.replaceState !== "function") {
      return;
    }

    const cleanQuery = url.searchParams.toString();
    const cleanUrl = url.pathname + (cleanQuery ? "?" + cleanQuery : "") + url.hash;

    window.history.replaceState(window.history.state, document.title, cleanUrl);
  }

  //###################################################################################
  // (2) REGRAS DE REDIRECIONAMENTO POS-SAVE
  //###################################################################################

  function redirectToStoredPostSaveContextV3(storedContext) {
    const currentUrl = getAppVerboCurrentUrlPostSaveV3();

    if (!storedContext || !storedContext.url || !currentUrl || currentUrl.pathname !== "/users/new") {
      return false;
    }

    // Se o POST devolveu a propria pagina com erro inline (sem redirect e sem
    // marcadores de feedback na URL), nao devemos navegar outra vez. Caso
    // contrario, o utilizador ve a mensagem de erro por um instante e ela
    // desaparece quando o JS reabre o contexto guardado.
    if (!isAppVerboPostSaveFeedbackUrlV3(currentUrl)) {
      return false;
    }

    //###################################################################################
    // (V3.0) PRESERVAR CONTEXTO EXPLICITO DA URL ATUAL
    //###################################################################################
    // Quando o backend devolve uma URL com contexto estavel (menu/aba/target), ela
    // deve prevalecer sobre qualquer contexto antigo guardado no sessionStorage.
    if (hasStableUsersNewContextV3(currentUrl)) {
      return false;
    }

    //###################################################################################
    // (V3.1) PRESERVAR CONTEXTO EXPLICITO DA ABA SESSÕES
    //###################################################################################
    // Quando o backend já devolve admin_tab=sessoes (ou sidebar_sections_tab=sessoes),
    // não devemos reabrir contexto antigo do sessionStorage. Isso evita saltar para outra
    // tela após criar/editar/mover/eliminar sessão.
    const currentAdminTab = String(currentUrl.searchParams.get("admin_tab") || "").trim().toLowerCase();
    const currentSidebarTab = String(currentUrl.searchParams.get("sidebar_sections_tab") || "").trim().toLowerCase();
    const currentTarget = String(currentUrl.searchParams.get("target") || "").trim().toLowerCase().replace(/^#/, "");
    const currentHash = String(currentUrl.hash || "").trim().toLowerCase().replace(/^#/, "");
    const isSessionsTargetContext =
      currentTarget.startsWith("admin-sidebar-sections-") ||
      currentHash.startsWith("admin-sidebar-sections-");

    if (currentAdminTab === "sessoes" || currentSidebarTab === "sessoes" || isSessionsTargetContext) {
      return false;
    }

    let targetUrl = null;

    try {
      targetUrl = new URL(storedContext.url, window.location.origin);
    } catch (error) {
      return false;
    }

    if (targetUrl.pathname !== "/users/new") {
      return false;
    }

    targetUrl.searchParams.set("appverbo_after_save", "1");
    copyPostSaveFeedbackParamsV3(currentUrl, targetUrl);

    const targetPath = targetUrl.pathname + targetUrl.search + targetUrl.hash;
    const currentPath = currentUrl.pathname + currentUrl.search + currentUrl.hash;

    if (targetPath === currentPath) {
      return false;
    }

    window.location.replace(targetPath);
    return true;
  }

  function runPostSaveContextNavigationGuardV3() {
    const appverboStoredPostSaveContextV3 = readAndClearAppVerboPostSaveContextV3();

    if (redirectToStoredPostSaveContextV3(appverboStoredPostSaveContextV3)) {
      // A navegacao continua no mesmo processo/aba onde o POST foi executado.
      return;
    }

    const navigationEntries = (
      typeof window !== "undefined" &&
      window.performance &&
      typeof window.performance.getEntriesByType === "function"
    )
      ? window.performance.getEntriesByType("navigation")
      : [];

    const navigationType = navigationEntries.length
      ? String(navigationEntries[0].type || "")
      : "";

    const currentUrlForRefreshGuard = getAppVerboCurrentUrlPostSaveV3();
    const isPostSaveFeedbackUrl = isAppVerboPostSaveFeedbackUrlV3(currentUrlForRefreshGuard);
    const hasExplicitMenuContext = Boolean(
      currentUrlForRefreshGuard &&
      (
        String(currentUrlForRefreshGuard.searchParams.get("menu") || "").trim() ||
        String(currentUrlForRefreshGuard.searchParams.get("target") || "").trim() ||
        String(currentUrlForRefreshGuard.searchParams.get("profile_section") || "").trim()
      )
    );

    if (
      navigationType === "reload" &&
      window.location.pathname === "/users/new" &&
      !isPostSaveFeedbackUrl &&
      !hasExplicitMenuContext
    ) {
      const homeUrl = "/users/new?menu=home";
      const currentPathAndQuery = `${window.location.pathname}${window.location.search}`;

      if (currentPathAndQuery !== homeUrl || window.location.hash) {
        window.location.replace(homeUrl);
      }
    }

    if (isPostSaveFeedbackUrl) {
      window.setTimeout(clearPostSaveFeedbackMarkersFromUrlV3, 600);
    }
  }

  //###################################################################################
  // (3) EXPORT E INICIALIZACAO
  //###################################################################################

  window.APPVERBO_RUN_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3 = runPostSaveContextNavigationGuardV3;
  runPostSaveContextNavigationGuardV3();
})();
// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_END
