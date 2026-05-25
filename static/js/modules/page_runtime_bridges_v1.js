// APPVERBO_PAGE_RUNTIME_BRIDGES_V1_MODULE_START
(function registerPageRuntimeBridgesV1Module() {
  "use strict";

  window.APPVERBO_CREATE_PAGE_RUNTIME_BRIDGES_API_V1 = function createPageRuntimeBridgesApiV1() {
    //###################################################################################
    // (1) BRIDGE HELPERS
    //###################################################################################
    function runSetupBridgeStep(stepName, payload) {
      if (typeof window.APPVERBO_RUN_SETUP_BRIDGE_V1 !== "function") {
        return;
      }
      window.APPVERBO_RUN_SETUP_BRIDGE_V1(stepName, payload);
    }

    function setupPageSupportIntegrations(currentEntityId) {
      if (typeof window.APPVERBO_SETUP_PAGE_SUPPORT_INTEGRATIONS_V1 !== "function") {
        return;
      }
      window.APPVERBO_SETUP_PAGE_SUPPORT_INTEGRATIONS_V1({
        currentEntityId
      });
    }

    //###################################################################################
    // (2) DYNAMIC PROCESS HISTORY BRIDGE
    //###################################################################################
    function renderDynamicProcessHistory(payload = {}) {
      if (typeof window.APPVERBO_RENDER_DYNAMIC_PROCESS_HISTORY_V1 !== "function") {
        return;
      }
      window.APPVERBO_RENDER_DYNAMIC_PROCESS_HISTORY_V1(payload);
    }

    return {
      runSetupBridgeStep,
      setupPageSupportIntegrations,
      renderDynamicProcessHistory
    };
  };
})();
// APPVERBO_PAGE_RUNTIME_BRIDGES_V1_MODULE_END
