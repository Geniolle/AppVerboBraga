//###################################################################################
// APPVERBOBRAGA - ADMIN TABLE FOOTER STANDARD V1 (COMPAT SHIM)
//###################################################################################

(function setupAdminTableFooterStandardV1Shim() {
  "use strict";

  if (window.__appverboAdminTableFooterStandardShimLoadedV1 === true) {
    return;
  }
  window.__appverboAdminTableFooterStandardShimLoadedV1 = true;

  function initializeIfReadyV1() {
    if (
      window.AppVerboAdminTableFooterStandard_v2 &&
      typeof window.AppVerboAdminTableFooterStandard_v2.initializeFooters_v2 === "function"
    ) {
      window.AppVerboAdminTableFooterStandard_v2.initializeFooters_v2(document);
      return true;
    }

    return false;
  }

  if (initializeIfReadyV1()) {
    return;
  }

  if (window.__appverboAdminTableFooterStandardV2ScriptRequestedV1 === true) {
    return;
  }
  window.__appverboAdminTableFooterStandardV2ScriptRequestedV1 = true;

  const scriptEl = document.createElement("script");
  scriptEl.src = "/static/js/modules/admin_table_footer_standard_v2.js";
  scriptEl.defer = true;

  scriptEl.addEventListener("load", function () {
    initializeIfReadyV1();
  });

  (document.head || document.documentElement).appendChild(scriptEl);
})();
