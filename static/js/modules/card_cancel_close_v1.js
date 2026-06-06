// APPVERBO_CARD_CANCEL_CLOSE_V1_MODULE_START
(function registerCardCancelCloseV1Module() {
  "use strict";

  const BOUND_FLAG_V1 = "__APPVERBO_CARD_CANCEL_CLOSE_V1_BOUND__";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################
  function normalizeTextV1(value) {
    return String(value || "").trim();
  }

  function parseUrlV1(rawUrl) {
    const cleanUrl = normalizeTextV1(rawUrl);
    if (!cleanUrl) {
      return null;
    }

    try {
      return new URL(cleanUrl, window.location.origin);
    }
    catch (_error) {
      return null;
    }
  }

  function resolveTargetSelectorFromUrlV1(url) {
    if (!url) {
      return "";
    }

    const hash = normalizeTextV1(url.hash);
    if (hash && hash !== "#") {
      return hash.startsWith("#") ? hash : "#" + hash;
    }

    const targetParam = normalizeTextV1(url.searchParams.get("target"));
    if (!targetParam) {
      return "";
    }

    return targetParam.startsWith("#") ? targetParam : "#" + targetParam;
  }

  function resolveReturnUrlV1(triggerEl) {
    if (!triggerEl) {
      return "";
    }

    const dataUrl = normalizeTextV1(triggerEl.getAttribute("data-card-cancel-return-url"));
    if (dataUrl) {
      return dataUrl;
    }

    const href = normalizeTextV1(triggerEl.getAttribute("href"));
    if (href) {
      return href;
    }

    return "";
  }

  function shouldForceNavigationV1(triggerEl) {
    return Boolean(
      triggerEl &&
      normalizeTextV1(triggerEl.getAttribute("data-card-cancel-force-navigation")) === "1"
    );
  }

  function resetClosestFormV1(triggerEl) {
    if (!triggerEl || triggerEl.getAttribute("data-card-cancel-reset-form") === "0") {
      return;
    }

    const formEl = triggerEl.closest("form");
    if (!formEl || typeof formEl.reset !== "function") {
      return;
    }

    formEl.reset();
  }

  function closeClosestDetailsV1(triggerEl) {
    if (!triggerEl || triggerEl.getAttribute("data-card-cancel-close-details") === "0") {
      return false;
    }

    const detailsEl = triggerEl.closest("details");
    if (!detailsEl) {
      return false;
    }

    detailsEl.open = false;
    return true;
  }

  function activateUsersNewTargetV1(rawReturnUrl) {
    const parsedUrl = parseUrlV1(rawReturnUrl);
    if (!parsedUrl) {
      return false;
    }

    if (parsedUrl.origin !== window.location.origin) {
      return false;
    }

    if (parsedUrl.pathname !== "/users/new" || parsedUrl.pathname !== window.location.pathname) {
      return false;
    }

    const menuKey = normalizeTextV1(parsedUrl.searchParams.get("menu"));
    if (!menuKey) {
      return false;
    }

    if (typeof window.APPVERBO_CREATE_MENU_NAVIGATION_BRIDGE_API_V1 !== "function") {
      return false;
    }

    const bridgeApi = window.APPVERBO_CREATE_MENU_NAVIGATION_BRIDGE_API_V1();
    if (!bridgeApi || typeof bridgeApi.activateMenuTarget !== "function") {
      return false;
    }

    const targetSelector = resolveTargetSelectorFromUrlV1(parsedUrl);
    if (targetSelector && !document.querySelector(targetSelector)) {
      return false;
    }

    bridgeApi.activateMenuTarget(menuKey, targetSelector);

    try {
      const nextUrl = parsedUrl.pathname + parsedUrl.search + parsedUrl.hash;
      window.history.replaceState({}, document.title, nextUrl);
    }
    catch (_error) {
    }

    return true;
  }

  //###################################################################################
  // (2) PUBLIC API
  //###################################################################################
  function handleCardCancelCloseV1(triggerEl) {
    if (!triggerEl) {
      return false;
    }

    resetClosestFormV1(triggerEl);

    if (closeClosestDetailsV1(triggerEl)) {
      return true;
    }

    const returnUrl = resolveReturnUrlV1(triggerEl);
    if (!returnUrl) {
      return false;
    }

    if (shouldForceNavigationV1(triggerEl)) {
      window.location.assign(returnUrl);
      return true;
    }

    if (activateUsersNewTargetV1(returnUrl)) {
      return true;
    }

    window.location.assign(returnUrl);
    return true;
  }

  //###################################################################################
  // (3) GLOBAL BIND
  //###################################################################################
  function bindCardCancelCloseV1() {
    if (window[BOUND_FLAG_V1]) {
      return;
    }

    window[BOUND_FLAG_V1] = true;

    document.addEventListener("click", function handleCardCancelClickV1(event) {
      const triggerEl = event.target && typeof event.target.closest === "function"
        ? event.target.closest("[data-card-cancel-close='1']")
        : null;

      if (!triggerEl) {
        return;
      }

      event.preventDefault();
      handleCardCancelCloseV1(triggerEl);
    });
  }

  bindCardCancelCloseV1();

  window.APPVERBO_HANDLE_CARD_CANCEL_CLOSE_V1 = handleCardCancelCloseV1;
})();
// APPVERBO_CARD_CANCEL_CLOSE_V1_MODULE_END
