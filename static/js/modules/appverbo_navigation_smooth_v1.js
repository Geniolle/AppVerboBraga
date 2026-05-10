// APPVERBO_NAVIGATION_SMOOTH_V1_START
//###################################################################################
// (1) LIBERTAR TELA APOS INICIALIZACAO
//###################################################################################

(function () {
  "use strict";

  function liberarTela() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.requestAnimationFrame(liberarTela);
    }, { once: true });
  } else {
    window.requestAnimationFrame(liberarTela);
  }

  window.addEventListener("pageshow", liberarTela);

  //###################################################################################
  // (2) REDUZIR PISCAR EM CLIQUES DE MENU/ABAS SEM BLOQUEAR O JS EXISTENTE
  //###################################################################################

  let localNavigationTimer = null;

  function marcarNavegacaoLocal() {
    if (!document.body) {
      return;
    }

    document.body.classList.add("appverbo-local-navigation");

    if (localNavigationTimer) {
      window.clearTimeout(localNavigationTimer);
    }

    localNavigationTimer = window.setTimeout(function () {
      document.body.classList.remove("appverbo-local-navigation");
      localNavigationTimer = null;
    }, 180);
  }

  document.addEventListener("click", function (event) {
    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const navigationControl = target.closest(
      "button[data-menu], button[data-admin-tab], button[data-profile-section], button[data-dynamic-process-section], .submenu-item, .profile-process-tab-btn"
    );

    if (!navigationControl) {
      return;
    }

    marcarNavegacaoLocal();
  }, true);
})();
// APPVERBO_NAVIGATION_SMOOTH_V1_END
