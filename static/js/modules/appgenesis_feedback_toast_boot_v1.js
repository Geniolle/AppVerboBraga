//###################################################################################
// (1) BOOT GLOBAL DE FEEDBACK POR TOAST
//###################################################################################
(function initAppGenesisFeedbackToastBootV1() {
  function run() {
    if (
      window.AppGenesisProcessShell &&
      typeof window.AppGenesisProcessShell.enhanceFeedbackToasts === "function"
    ) {
      window.AppGenesisProcessShell.enhanceFeedbackToasts({ source: "url" });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run, { once: true });
    return;
  }

  run();
})();
