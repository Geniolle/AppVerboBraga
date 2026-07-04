// APPVERBO_PROCESS_EDITOR_DEBUG_V1_START
//###################################################################################
// (PROCESS_EDITOR_DEBUG_V1) LOGS DE DIAGNOSTICO DO EDITOR DE PROCESSO, ATRAS DE FLAG
//###################################################################################

function isAppVerboProcessEditorDebugEnabledV1() {
  try {
    return window.localStorage.getItem("appverbo_debug_process_editor") === "1";
  } catch (error) {
    return false;
  }
}

function logAppVerboProcessEditorDebugV1(event, payload) {
  if (!isAppVerboProcessEditorDebugEnabledV1()) {
    return;
  }
  try {
    // eslint-disable-next-line no-console
    console.log("[AppVerbo][ProcessEditorDebug]", event, payload || {});
  } catch (error) {
    // Ignorar falhas de logging (ex.: console indisponivel).
  }
}
// APPVERBO_PROCESS_EDITOR_DEBUG_V1_END

// APPVERBO_NAVIGATION_BOOT_DEBUG_V1_START
//###################################################################################
// (NAVIGATION_BOOT_DEBUG_V1) LOGS DE DIAGNOSTICO DO BOOT DE NAVEGACAO, ATRAS DE FLAG
//###################################################################################

function isAppVerboNavigationBootDebugEnabledV1() {
  try {
    return window.localStorage.getItem("appverbo_debug_navigation_boot") === "1";
  } catch (error) {
    return false;
  }
}

function logAppVerboNavigationBootDebugV1(event, payload) {
  if (!isAppVerboNavigationBootDebugEnabledV1()) {
    return;
  }
  try {
    // eslint-disable-next-line no-console
    console.log("[AppVerbo][NavigationBootDebug]", event, payload || {});
  } catch (error) {
    // Ignorar falhas de logging (ex.: console indisponivel).
  }
}
// APPVERBO_NAVIGATION_BOOT_DEBUG_V1_END

// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_START
//###################################################################################
// (POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3) RETORNO POS-SAVE VS REFRESH MANUAL
//
// Este ficheiro carrega no <head>, antes do parser chegar ao <body>, de propósito: a decisão de
// normalizar um reload para Home tem de acontecer antes de qualquer HTML da pagina antiga (ex.:
// Estruturas > Menu) ser inserido no DOM/pintado, para nao haver flash visual do menu errado antes
// de mostrar Home.
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

function readAndClearAppVerboPostSaveContextV3() {
  try {
    const rawValue = window.sessionStorage.getItem(APPVERBO_POST_SAVE_CONTEXT_KEY_V3) || "";

    logAppVerboProcessEditorDebugV1("readAndClearAppVerboPostSaveContextV3:raw_session_storage", {
      href: window.location.href,
      rawValue: rawValue || null
    });

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

function hasProtectedReloadNavigationContextV1(url) {
  if (!url) {
    return false;
  }

  const protectedQueryKeys = [
    "settings_edit_key",
    "settings_action",
    "auth_profile_edit_key",
    "auth_objeto_edit_key",
    "sidebar_section_edit_key",
    "entity_edit_id",
    "user_edit_id",
    "entity_view",
    "user_view"
  ];

  if (protectedQueryKeys.some((key) => String(url.searchParams.get(key) || "").trim())) {
    return true;
  }

  const protectedTargets = new Set([
    "#settings-menu-edit-card",
    "#auth-profile-form-card",
    "#auth-objeto-form-card",
    "#admin-sidebar-sections-form-card",
    "#edit-user-card",
    "#edit-entity-card"
  ]);
  const target = String(url.searchParams.get("target") || url.hash || "").trim();

  return protectedTargets.has(target);
}

function redirectToStoredPostSaveContextV3(storedContext) {
  const currentUrl = getAppVerboCurrentUrlPostSaveV3();

  logAppVerboProcessEditorDebugV1("redirectToStoredPostSaveContextV3:entry", {
    currentHref: window.location.href,
    storedContextUrl: storedContext ? storedContext.url : null,
    storedContextCreatedAt: storedContext ? storedContext.createdAt : null
  });

  if (!storedContext || !storedContext.url || !currentUrl || currentUrl.pathname !== "/users/new") {
    return false;
  }

  const currentTarget = String(currentUrl.searchParams.get("target") || "").trim();
  const hasEntitySuccessListTarget = Boolean(
    String(currentUrl.searchParams.get("entity_success") || "").trim() &&
    currentTarget === "#recent-entities-card"
  );

  if (hasEntitySuccessListTarget) {
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

  const currentAdminTab = String(currentUrl.searchParams.get("admin_tab") || "").trim();
  const currentHasFeedback = isAppVerboPostSaveFeedbackUrlV3(currentUrl);
  const currentMenu = String(currentUrl.searchParams.get("menu") || "").trim();
  const storedAdminTab = String(targetUrl.searchParams.get("admin_tab") || "").trim();
  const storedMenu = String(targetUrl.searchParams.get("menu") || "").trim();

  if (currentHasFeedback && currentAdminTab) {
    if (!storedAdminTab || storedAdminTab !== currentAdminTab || storedMenu === "home") {
      return false;
    }
  }

  if (
    currentHasFeedback &&
    currentMenu === "perfil_de_autorizacao" &&
    storedMenu === "perfil_de_autorizacao"
  ) {
    return false;
  }

  targetUrl.searchParams.set("appverbo_after_save", "1");
  copyPostSaveFeedbackParamsV3(currentUrl, targetUrl);

  const targetPath = targetUrl.pathname + targetUrl.search + targetUrl.hash;
  const currentPath = currentUrl.pathname + currentUrl.search + currentUrl.hash;

  if (targetPath === currentPath) {
    logAppVerboProcessEditorDebugV1("redirectToStoredPostSaveContextV3:skip_same_path", {
      currentPath,
      targetPath
    });
    return false;
  }

  logAppVerboProcessEditorDebugV1("redirectToStoredPostSaveContextV3:location.replace", {
    currentPath,
    targetPath,
    storedContextUrl: storedContext.url,
    reason: "URL guardada em sessionStorage antes do submit difere da URL atual apos o redirect do backend"
  });
  window.location.replace(targetPath);
  return true;
}

const appverboStoredPostSaveContextV3 = readAndClearAppVerboPostSaveContextV3();

if (redirectToStoredPostSaveContextV3(appverboStoredPostSaveContextV3)) {
  // A navegacao continua no mesmo processo/aba onde o POST foi executado.
} else {
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
  const hasProtectedReloadContext = hasProtectedReloadNavigationContextV1(currentUrlForRefreshGuard);

  logAppVerboNavigationBootDebugV1("reload_guard:evaluate", {
    href: window.location.href,
    navigationType,
    isPostSaveFeedbackUrl,
    hasProtectedReloadContext,
    resolvedMenuFromUrl: currentUrlForRefreshGuard
      ? String(currentUrlForRefreshGuard.searchParams.get("menu") || "").trim()
      : "",
    resolvedTargetFromUrl: currentUrlForRefreshGuard
      ? String(currentUrlForRefreshGuard.searchParams.get("target") || currentUrlForRefreshGuard.hash || "").trim()
      : ""
  });

  if (
    navigationType === "reload" &&
    window.location.pathname === "/users/new" &&
    !isPostSaveFeedbackUrl &&
    !hasProtectedReloadContext
  ) {
    const homeUrl = "/users/new?menu=home";
    const currentPathAndQuery = `${window.location.pathname}${window.location.search}`;

    if (currentPathAndQuery !== homeUrl || window.location.hash) {
      logAppVerboNavigationBootDebugV1("reload_guard:location_replace_home", {
        from: window.location.href,
        to: homeUrl
      });
      window.location.replace(homeUrl);
    }
  }

  if (isPostSaveFeedbackUrl) {
    window.setTimeout(clearPostSaveFeedbackMarkersFromUrlV3, 600);
  }
}
// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_END
