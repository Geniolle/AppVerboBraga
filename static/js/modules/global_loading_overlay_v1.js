// APPVERBO_GLOBAL_LOADING_OVERLAY_V1_START
//###################################################################################
// (GLOBAL_LOADING_OVERLAY_V1) Indicador global de carregamento/navegacao, reutilizavel
// em toda a app. Ativado em: refresh/navegacao real do browser (via beforeunload,
// cobre tambem submits e redirects que navegam, incluindo o location.replace do guard
// de reload->Home) e navegacao client-side que troca de processo (ver chamadas em
// applyContentForMenuTarget, unica rotina que resolve boot/clique de sidebar/clique de
// aba). Contador de referencias evita esconder cedo demais quando ha mais de uma causa
// simultanea; timeout de seguranca evita ficar preso caso algum caminho esqueca de
// esconder.
//###################################################################################

(function () {
  "use strict";

  var OVERLAY_ID = "appverbo-global-loading-overlay";
  var VISIBLE_CLASS = "appverbo-global-loading-overlay--visible";
  var SAFETY_TIMEOUT_MS = 10000;
  var activeCount = 0;
  var safetyTimeoutHandle = null;

  function getOverlayElement() {
    return document.getElementById(OVERLAY_ID);
  }

  function logDebug(event, payload) {
    if (typeof window.logAppVerboNavigationBootDebugV1 === "function") {
      window.logAppVerboNavigationBootDebugV1(event, payload);
    }
  }

  function clearSafetyTimeout() {
    if (safetyTimeoutHandle) {
      window.clearTimeout(safetyTimeoutHandle);
      safetyTimeoutHandle = null;
    }
  }

  function forceHide(reason) {
    activeCount = 0;
    clearSafetyTimeout();
    var overlay = getOverlayElement();
    if (!overlay) {
      return;
    }
    overlay.classList.remove(VISIBLE_CLASS);
    overlay.setAttribute("aria-hidden", "true");
    logDebug("global_loading_overlay:hide", { reason: String(reason || "unspecified") });
  }

  function showGlobalLoadingOverlayV1(reason) {
    var overlay = getOverlayElement();
    if (!overlay) {
      return;
    }
    activeCount += 1;
    overlay.classList.add(VISIBLE_CLASS);
    overlay.setAttribute("aria-hidden", "false");
    logDebug("global_loading_overlay:show", {
      reason: String(reason || "unspecified"),
      activeCount: activeCount
    });

    clearSafetyTimeout();
    safetyTimeoutHandle = window.setTimeout(function () {
      logDebug("global_loading_overlay:safety_timeout", { activeCount: activeCount });
      forceHide("safety_timeout");
    }, SAFETY_TIMEOUT_MS);
  }

  function hideGlobalLoadingOverlayV1(reason) {
    if (activeCount > 0) {
      activeCount -= 1;
    }
    if (activeCount > 0) {
      logDebug("global_loading_overlay:hide_skipped_still_active", {
        reason: String(reason || "unspecified"),
        activeCount: activeCount
      });
      return;
    }
    forceHide(reason);
  }

  window.showGlobalLoadingOverlayV1 = showGlobalLoadingOverlayV1;
  window.hideGlobalLoadingOverlayV1 = hideGlobalLoadingOverlayV1;

  window.addEventListener("beforeunload", function () {
    showGlobalLoadingOverlayV1("beforeunload");
  });

  window.addEventListener("pageshow", function () {
    // Cobre tanto o primeiro paint de uma pagina nova como o restauro via bfcache
    // (Firefox/Safari podem reexibir a pagina anterior sem disparar um load novo,
    // deixando o overlay "preso" visivel se nao for limpo aqui).
    forceHide("pageshow");
  });
})();
// APPVERBO_GLOBAL_LOADING_OVERLAY_V1_END
