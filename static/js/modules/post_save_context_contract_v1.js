//###################################################################################
// (1) CONTRATO PARTILHADO DE CONTEXTO POS-SAVE
//###################################################################################

(function () {
  "use strict";

  const STORAGE_KEY = "appgenesis:post-save-context-v3";
  const MAX_AGE_MS = 120000;

  function getCurrentUrl() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function isFeedbackUrl(url) {
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

  function copyFeedbackParams(sourceUrl, targetUrl) {
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

  function clearFeedbackMarkersFromUrl() {
    const url = getCurrentUrl();

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

  function hasProtectedReloadContext(url) {
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

  function readStoredContext() {
    try {
      const rawValue = window.sessionStorage.getItem(STORAGE_KEY) || "";

      if (!rawValue) {
        return null;
      }

      window.sessionStorage.removeItem(STORAGE_KEY);

      const parsedValue = JSON.parse(rawValue);
      const createdAt = Number(parsedValue && parsedValue.createdAt || 0);

      if (!createdAt || Date.now() - createdAt > MAX_AGE_MS) {
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

  function storeContext(context) {
    if (!context || typeof context.url !== "string" || !context.url.trim()) {
      return false;
    }

    try {
      window.sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          url: String(context.url).trim(),
          createdAt: Number(context.createdAt) || Date.now()
        })
      );
      return true;
    } catch (error) {
      return false;
    }
  }

  window.AppGenesisPostSaveContextContractV1 = {
    storageKey: STORAGE_KEY,
    maxAgeMs: MAX_AGE_MS,
    getCurrentUrl,
    isFeedbackUrl,
    copyFeedbackParams,
    clearFeedbackMarkersFromUrl,
    hasProtectedReloadContext,
    readStoredContext,
    storeContext
  };
})();
