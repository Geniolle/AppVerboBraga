// APPGENESIS_PROCESS_EDITOR_DEBUG_V1_START
//###################################################################################
// (PROCESS_EDITOR_DEBUG_V1) LOGS DE DIAGNOSTICO DO EDITOR DE PROCESSO, ATRAS DE FLAG
//###################################################################################

function isAppGenesisProcessEditorDebugEnabledV1() {
  try {
    return window.localStorage.getItem("appgenesis_debug_process_editor") === "1";
  } catch (error) {
    return false;
  }
}

function logAppGenesisProcessEditorDebugV1(event, payload) {
  if (!isAppGenesisProcessEditorDebugEnabledV1()) {
    return;
  }
  try {
    // eslint-disable-next-line no-console
    console.log("[AppGenesis][ProcessEditorDebug]", event, payload || {});
  } catch (error) {
    // Ignorar falhas de logging (ex.: console indisponivel).
  }
}
// APPGENESIS_PROCESS_EDITOR_DEBUG_V1_END

// APPGENESIS_NAVIGATION_BOOT_DEBUG_V1_START
//###################################################################################
// (NAVIGATION_BOOT_DEBUG_V1) LOGS DE DIAGNOSTICO DO BOOT DE NAVEGACAO, ATRAS DE FLAG
//###################################################################################

function isAppGenesisNavigationBootDebugEnabledV1() {
  try {
    return window.localStorage.getItem("appgenesis_debug_navigation_boot") === "1";
  } catch (error) {
    return false;
  }
}

function logAppGenesisNavigationBootDebugV1(event, payload) {
  if (!isAppGenesisNavigationBootDebugEnabledV1()) {
    return;
  }
  try {
    // eslint-disable-next-line no-console
    console.log("[AppGenesis][NavigationBootDebug]", event, payload || {});
  } catch (error) {
    // Ignorar falhas de logging (ex.: console indisponivel).
  }
}
// APPGENESIS_NAVIGATION_BOOT_DEBUG_V1_END

// APPGENESIS_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_START
//###################################################################################
// (POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3) RETORNO POS-SAVE VS REFRESH MANUAL
//
// Este ficheiro carrega no <head>, antes do parser chegar ao <body>, de propósito: a decisão de
// normalizar um reload para Home tem de acontecer antes de qualquer HTML da pagina antiga (ex.:
// Estruturas > Menu) ser inserido no DOM/pintado, para nao haver flash visual do menu errado antes
// de mostrar Home.
//###################################################################################

const APPGENESIS_POST_SAVE_CONTEXT_KEY_V3 = "appgenesis:post-save-context-v3";
const APPGENESIS_POST_SAVE_CONTEXT_MAX_AGE_MS_V3 = 120000;

function getAppGenesisCurrentUrlPostSaveV3() {
  try {
    return new URL(window.location.href);
  } catch (error) {
    return null;
  }
}

function isAppGenesisPostSaveFeedbackUrlV3(url) {
  if (!url) {
    return false;
  }

  if (url.searchParams.get("appgenesis_after_save") === "1") {
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

function readAndClearAppGenesisPostSaveContextV3() {
  try {
    const rawValue = window.sessionStorage.getItem(APPGENESIS_POST_SAVE_CONTEXT_KEY_V3) || "";

    logAppGenesisProcessEditorDebugV1("readAndClearAppGenesisPostSaveContextV3:raw_session_storage", {
      href: window.location.href,
      rawValue: rawValue || null
    });

    if (!rawValue) {
      return null;
    }

    window.sessionStorage.removeItem(APPGENESIS_POST_SAVE_CONTEXT_KEY_V3);

    const parsedValue = JSON.parse(rawValue);
    const createdAt = Number(parsedValue && parsedValue.createdAt || 0);

    if (!createdAt || Date.now() - createdAt > APPGENESIS_POST_SAVE_CONTEXT_MAX_AGE_MS_V3) {
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
  const url = getAppGenesisCurrentUrlPostSaveV3();

  if (!url) {
    return;
  }

  let changed = false;

  Array.from(url.searchParams.keys()).forEach((rawKey) => {
    const key = String(rawKey || "").trim().toLowerCase();

    if (key === "appgenesis_after_save") {
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
  const currentUrl = getAppGenesisCurrentUrlPostSaveV3();

  logAppGenesisProcessEditorDebugV1("redirectToStoredPostSaveContextV3:entry", {
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

  const currentHasFeedback = isAppGenesisPostSaveFeedbackUrlV3(currentUrl);

  // Regra global: se a URL atual ja e o destino pos-save calculado pelo backend (marcador
  // appgenesis_after_save=1 ou parametros de sucesso/erro), ela e sempre a fonte da verdade e
  // nunca deve ser substituida pela URL pre-submit guardada em sessionStorage -- vale para
  // qualquer processo configuravel, sem excecoes por menu/aba especifico (antes so cobria
  // "administrativo" e "perfil_de_autorizacao", deixando "sessoes"/Menu vulneravel a este
  // mesmo bug de reversao de navegacao apos Guardar).
  if (currentHasFeedback) {
    return false;
  }

  targetUrl.searchParams.set("appgenesis_after_save", "1");
  copyPostSaveFeedbackParamsV3(currentUrl, targetUrl);

  const targetPath = targetUrl.pathname + targetUrl.search + targetUrl.hash;
  const currentPath = currentUrl.pathname + currentUrl.search + currentUrl.hash;

  if (targetPath === currentPath) {
    logAppGenesisProcessEditorDebugV1("redirectToStoredPostSaveContextV3:skip_same_path", {
      currentPath,
      targetPath
    });
    return false;
  }

  logAppGenesisProcessEditorDebugV1("redirectToStoredPostSaveContextV3:location.replace", {
    currentPath,
    targetPath,
    storedContextUrl: storedContext.url,
    reason: "URL guardada em sessionStorage antes do submit difere da URL atual apos o redirect do backend"
  });
  window.location.replace(targetPath);
  return true;
}

function isBrowserReloadNavigationV1() {
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

  return navigationType === "reload";
}

function normalizeReloadToHomeV1() {
  // Regra global: um F5/reload normal do browser deve sempre devolver o utilizador para Home,
  // independentemente de qual menu/aba/target estava ativo por navegacao client-side (que nao
  // atualiza a URL) ou de a URL ainda trazer marcadores de sucesso/erro de um save anterior
  // (ex.: "settings_success"). A unica excecao e um contexto de edicao em curso genuinamente
  // fragil (ver hasProtectedReloadNavigationContextV1), onde perder o estado ao dar F5
  // significaria perder trabalho nao guardado, nao apenas "esquecer" onde o utilizador estava.
  if (!isBrowserReloadNavigationV1() || window.location.pathname !== "/users/new") {
    return false;
  }

  const currentUrlForRefreshGuard = getAppGenesisCurrentUrlPostSaveV3();
  const isPostSaveFeedbackUrl = isAppGenesisPostSaveFeedbackUrlV3(currentUrlForRefreshGuard);
  const hasProtectedReloadContext = hasProtectedReloadNavigationContextV1(currentUrlForRefreshGuard);

  logAppGenesisNavigationBootDebugV1("reload_guard:evaluate", {
    href: window.location.href,
    navigationType: "reload",
    isPostSaveFeedbackUrl,
    hasProtectedReloadContext,
    resolvedMenuFromUrl: currentUrlForRefreshGuard
      ? String(currentUrlForRefreshGuard.searchParams.get("menu") || "").trim()
      : "",
    resolvedTargetFromUrl: currentUrlForRefreshGuard
      ? String(currentUrlForRefreshGuard.searchParams.get("target") || currentUrlForRefreshGuard.hash || "").trim()
      : ""
  });

  if (hasProtectedReloadContext) {
    return false;
  }

  const homeUrl = "/users/new?menu=home";
  const currentPathAndQuery = `${window.location.pathname}${window.location.search}`;

  if (currentPathAndQuery === homeUrl && !window.location.hash) {
    return false;
  }

  logAppGenesisNavigationBootDebugV1("reload_guard:location_replace_home", {
    from: window.location.href,
    to: homeUrl,
    hadPostSaveFeedbackMarkers: isPostSaveFeedbackUrl
  });
  window.location.replace(homeUrl);
  return true;
}

const appgenesisStoredPostSaveContextV3 = readAndClearAppGenesisPostSaveContextV3();

if (redirectToStoredPostSaveContextV3(appgenesisStoredPostSaveContextV3)) {
  // A navegacao continua no mesmo processo/aba onde o POST foi executado.
} else if (!normalizeReloadToHomeV1()) {
  const currentUrlForFeedbackCleanup = getAppGenesisCurrentUrlPostSaveV3();

  if (isAppGenesisPostSaveFeedbackUrlV3(currentUrlForFeedbackCleanup)) {
    window.setTimeout(clearPostSaveFeedbackMarkersFromUrlV3, 600);
  }
}
// APPGENESIS_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3_END
