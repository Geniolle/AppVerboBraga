(function () {
    "use strict";

    //###################################################################################
    // (1) CONFIGURACAO
    //###################################################################################

    const LOGGER = "APPVERBO_SIDEBAR_GLOBAL_REFRESH_NOOP_V2";
    const VERSION = "20260511-disable-sidebar-global-refresh-polling-noop-v2";

    //###################################################################################
    // (2) ESTADO PUBLICO SEM POLLING E SEM FETCH
    //###################################################################################

    const state = {
        version: VERSION,
        disabled: true,
        disabledPolling: true,
        reason: "Modulo desativado para eliminar chamadas recorrentes ao sidebar-refresh-version.",
        lastCheckAt: 0,
        lastPayload: null,
        lastError: null
    };

    //###################################################################################
    // (3) FUNCOES NO-OP COMPATIVEIS COM CODIGO ANTIGO
    //###################################################################################

    function noop() {
        return null;
    }

    function checkOnce() {
        state.lastCheckAt = Date.now();
        return Promise.resolve(null);
    }

    function checkNow() {
        state.lastCheckAt = Date.now();
        return Promise.resolve(null);
    }

    function stopPolling() {
        state.disabled = true;
        state.disabledPolling = true;
        return true;
    }

    //###################################################################################
    // (4) API GLOBAL COMPATIVEL
    //###################################################################################

    const api = Object.freeze({
        version: VERSION,
        logger: LOGGER,
        state: state,
        start: noop,
        stop: stopPolling,
        stopPolling: stopPolling,
        checkOnce: checkOnce,
        checkNow: checkNow
    });

    window.APPVERBO_SIDEBAR_GLOBAL_REFRESH_V1 = api;
    window.AppVerboSidebarGlobalRefreshV1 = api;
    window.appverboSidebarGlobalRefreshV1 = api;

    try {
        console.info("[" + LOGGER + "] modulo em no-op total", {
            version: VERSION,
            disabledPolling: true
        });
    }
    catch (error) {
        return null;
    }
})();