
// APPVERBO_ADMIN_SUBPROCESSES_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) VISUALIZAR DETALHES GENERICO
  //###################################################################################

  function instalarVisualizarAdminSubprocessV1() {
    if (window.__appverboAdminSubprocessV1 === true) {
      return;
    }

    window.__appverboAdminSubprocessV1 = true;

    document.addEventListener("click", function (event) {
      const button = event.target.closest("[data-admin-subprocess-view]");

      if (!button) {
        return;
      }

      event.preventDefault();

      const title = button.getAttribute("data-view-title") || "Detalhes";
      const details = button.getAttribute("data-view-details") || "";

      alert(title + (details ? "\n" + details : ""));
    });
  }

  //###################################################################################
  // (2) INICIAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarVisualizarAdminSubprocessV1);
  }
  else {
    instalarVisualizarAdminSubprocessV1();
  }
})();
// APPVERBO_ADMIN_SUBPROCESSES_V1_END
