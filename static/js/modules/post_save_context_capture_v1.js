//###################################################################################
// (1) CAPTURA PARTILHADA DO CONTEXTO POS-SAVE
//###################################################################################

(function () {
  "use strict";

  const contract = window.AppGenesisPostSaveContextContractV1 || null;

  function getCurrentUrl() {
    return contract && typeof contract.getCurrentUrl === "function"
      ? contract.getCurrentUrl()
      : new URL(window.location.href);
  }

  function buildCapturedContext(form) {
    const currentUrl = getCurrentUrl();
    const action = String(form && (form.getAttribute("action") || form.action) || "").trim();
    const method = String(form && (form.getAttribute("method") || form.method || "post") || "post")
      .trim()
      .toLowerCase();

    return {
      url: currentUrl.pathname + currentUrl.search + currentUrl.hash,
      createdAt: Date.now(),
      action,
      method
    };
  }

  function captureForm(form) {
    if (!form || String(form.getAttribute("method") || form.method || "post").trim().toLowerCase() !== "post") {
      return false;
    }

    const context = buildCapturedContext(form);
    return contract && typeof contract.storeContext === "function"
      ? contract.storeContext(context)
      : false;
  }

  window.AppGenesisPostSaveContextCaptureV1 = {
    buildCapturedContext,
    captureForm
  };
})();
