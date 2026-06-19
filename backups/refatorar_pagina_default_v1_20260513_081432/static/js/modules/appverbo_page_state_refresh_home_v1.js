(function () {
  "use strict";

  if (window.__appverboPageStateRefreshHomeV1Loaded) {
    return;
  }

  window.__appverboPageStateRefreshHomeV1Loaded = true;

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
