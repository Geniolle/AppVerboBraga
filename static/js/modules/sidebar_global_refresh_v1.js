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
  let pauseOnceUntil = 0;

  //###################################################################################
  // (2) DEBUG
  //###################################################################################

  function isSidebarRefreshDebugEnabledV1() {
    try {
      return localStorage.getItem("appgenesisDebugSidebarRefresh") === "1";
    } catch (error) {
      return false;
    }
  }

  function logSidebarRefreshV1(event, payload) {
    if (!isSidebarRefreshDebugEnabledV1()) {
      return;
    }

    console.log("[SIDEBAR_REFRESH]", event, payload || {});
  }

  //###################################################################################
  // (3) UTILITARIOS
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

  function fetchRefreshVersionV1() {
    return fetch(REFRESH_ENDPOINT, {
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
          logSidebarRefreshV1("stop", {
            reason: "unauthorized",
            status: response.status
          });
          return null;
        }

        if (!response.ok) {
          return null;
        }

        return response.json();
      })
      .then((payload) => getCurrentVersion(payload))
      .catch((error) => {
        console.warn("Falha ao verificar refresh global do sidebar:", error);
        logSidebarRefreshV1("error", { error: String(error) });
        return "";
      });
  }

  function setBaselineV1(version, reason) {
    const cleanVersion = String(version || "").trim();

    if (!cleanVersion) {
      return "";
    }

    initialVersion = cleanVersion;
    initialized = true;

    if (reason === "local_ajax_save") {
      pauseOnceUntil = 0;
      logSidebarRefreshV1("baseline refreshed after local ajax save", {
        version: cleanVersion
      });
      return cleanVersion;
    }

    if (reason === "init") {
      logSidebarRefreshV1("init baseline", {
        version: cleanVersion
      });
      return cleanVersion;
    }

    logSidebarRefreshV1("set baseline", {
      version: cleanVersion,
      reason: String(reason || "").trim()
    });

    return cleanVersion;
  }

  function pauseOnceV1() {
    pauseOnceUntil = Date.now() + POLL_INTERVAL_MS + 2000;
    logSidebarRefreshV1("pause once", {
      until: pauseOnceUntil,
      baseline: initialVersion
    });
  }

  function shouldPauseNextReloadV1() {
    if (!pauseOnceUntil) {
      return false;
    }

    if (Date.now() > pauseOnceUntil) {
      pauseOnceUntil = 0;
      return false;
    }

    return true;
  }

  function refreshBaselineV1(reason) {
    if (stopped || shouldIgnoreCurrentPage()) {
      return Promise.resolve(initialVersion);
    }

    return fetchRefreshVersionV1().then((currentVersion) => {
      if (!currentVersion || stopped) {
        return initialVersion;
      }

      return setBaselineV1(
        currentVersion,
        reason === "local_ajax_save" ? "local_ajax_save" : "refresh"
      );
    });
  }

  //###################################################################################
  // (3.1) PARAR AO SAIR DA PAGINA (EVITA RELOAD PARA URL ANTIGA APOS SUBMIT)
  //###################################################################################
  // Regra global: qualquer verificacao de versao ja em curso (fetch pendente) que so resolva
  // depois do utilizador ja ter iniciado a navegacao para fora desta pagina (ex.: submeter
  // qualquer formulario, nao especifico de nenhum processo/aba/menu) nao pode chamar
  // window.location.reload(), senao recarrega a URL antiga e cancela/sobrepoe o redirect
  // legitimo do backend pos-submit. "pagehide" sozinho e tarde demais: so dispara quando a
  // resposta do destino ja esta a substituir o documento, mas a corrida acontece durante o
  // round-trip POST -> 303 -> GET, muito antes disso. Por isso paramos ja no instante do
  // "submit" (fase de captura, cobre qualquer form da pagina) e mantemos "pagehide" como
  // rede de seguranca para navegacoes que nao passam por um form (ex.: location.href direto).
  document.addEventListener("submit", function () {
    stopped = true;
  }, true);

  window.addEventListener("pagehide", function () {
    stopped = true;
  });

  //###################################################################################
  // (4) VERIFICAR VERSAO GLOBAL
  //###################################################################################

  function checkRefreshVersion() {
    if (stopped || isChecking || shouldIgnoreCurrentPage()) {
      return;
    }

    isChecking = true;

    fetchRefreshVersionV1()
      .then((currentVersion) => {
        if (!currentVersion || stopped) {
          return;
        }

        if (!initialized) {
          setBaselineV1(currentVersion, "init");
          return;
        }

        if (currentVersion !== initialVersion) {
          const paused = shouldPauseNextReloadV1();

          logSidebarRefreshV1("detected change", {
            baseline: initialVersion,
            currentVersion: currentVersion,
            paused: paused
          });

          if (paused) {
            setBaselineV1(currentVersion, "local_ajax_save");
            return;
          }

          stopped = true;
          logSidebarRefreshV1("reload", {
            baseline: initialVersion,
            currentVersion: currentVersion
          });
          window.location.reload();
        }
      })
      .finally(() => {
        isChecking = false;
      });
  }

  //###################################################################################
  // (5) API GLOBAL
  //###################################################################################

  window.AppGenesisSidebarGlobalRefreshV1 = {
    refreshBaseline: function () {
      return refreshBaselineV1(arguments[0] || "manual");
    },
    setBaseline: function (version) {
      return setBaselineV1(version, arguments[1] || "manual");
    },
    pauseOnce: function () {
      pauseOnceV1();
    }
  };

  //###################################################################################
  // (6) INICIALIZAR POLLING
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
