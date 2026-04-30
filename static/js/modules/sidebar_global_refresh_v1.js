(function () {
  "use strict";

  //###################################################################################
  // (1) CONFIGURACAO
  //###################################################################################

  const POLL_INTERVAL_MS = 5000;
  const REFRESH_ENDPOINT = "/settings/menu/sidebar-refresh-version";

  let initialVersion = "";
  let initialized = false;
  let isChecking = false;
  let stopped = false;

  //###################################################################################
  // (2) VERIFICAR VERSAO GLOBAL
  //###################################################################################

  function shouldIgnoreCurrentPage() {
    const path = String(window.location.pathname || "");
    return !path.startsWith("/users/new");
  }

  function getCurrentVersion(payload) {
    if (!payload || typeof payload !== "object") {
      return "";
    }

    return String(payload.version || "").trim();
  }

  function checkRefreshVersion() {
    if (stopped || isChecking || shouldIgnoreCurrentPage()) {
      return;
    }

    isChecking = true;

    fetch(REFRESH_ENDPOINT, {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        "Accept": "application/json",
        "X-Requested-With": "fetch"
      }
    })
      .then((response) => {
        if (response.status === 401 || response.status === 403) {
          stopped = true;
          return null;
        }

        if (!response.ok) {
          return null;
        }

        return response.json();
      })
      .then((payload) => {
        if (!payload || stopped) {
          return;
        }

        const currentVersion = getCurrentVersion(payload);

        if (!currentVersion) {
          return;
        }

        if (!initialized) {
          initialized = true;
          initialVersion = currentVersion;
          return;
        }

        if (currentVersion !== initialVersion) {
          stopped = true;
          window.location.reload();
        }
      })
      .catch((error) => {
        console.warn("Falha ao verificar refresh global do sidebar:", error);
      })
      .finally(() => {
        isChecking = false;
      });
  }

  //###################################################################################
  // (3) INICIALIZAR POLLING
  //###################################################################################

  function initGlobalRefreshWatcher() {
    if (shouldIgnoreCurrentPage()) {
      return;
    }

    checkRefreshVersion();
    window.setInterval(checkRefreshVersion, POLL_INTERVAL_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGlobalRefreshWatcher);
  } else {
    initGlobalRefreshWatcher();
  }
})();
