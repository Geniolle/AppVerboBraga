// APPVERBO_MARK_READY_V1_MODULE_START
(function registerMarkReadyV1Module() {
  "use strict";

  window.APPVERBO_SETUP_MARK_READY_V1 = function setupMarkReadyV1(options) {
    const deps = options && typeof options === "object" ? options : {};

// APPVERBO_MARK_READY_V1_START
//###################################################################################
// (ANTI_PISCAR) GARANTIR QUE A TELA E LIBERTADA APOS O JS PRINCIPAL
//###################################################################################

function appverboMarkReadyV1() {
  if (!document.body) {
    return;
  }

  document.body.classList.remove("appverbo-booting");
  document.body.classList.add("appverbo-ready");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", function () {
    window.requestAnimationFrame(appverboMarkReadyV1);
  }, { once: true });
} else {
  window.requestAnimationFrame(appverboMarkReadyV1);
}

window.addEventListener("load", appverboMarkReadyV1, { once: true });
// APPVERBO_MARK_READY_V1_END
  };
})();
// APPVERBO_MARK_READY_V1_MODULE_END
