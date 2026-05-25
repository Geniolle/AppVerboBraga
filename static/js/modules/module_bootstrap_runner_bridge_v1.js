// APPVERBO_MODULE_BOOTSTRAP_RUNNER_BRIDGE_V1_MODULE_START
(function registerModuleBootstrapRunnerBridgeV1Module() {
  "use strict";

  window.APPVERBO_CREATE_MODULE_BOOTSTRAP_RUNNER_BRIDGE_API_V1 =
    function createModuleBootstrapRunnerBridgeApiV1() {
      function runStep(step, context = {}) {
        if (typeof window.APPVERBO_RUN_MODULE_BOOTSTRAP_STEP_V1 !== "function") {
          return;
        }
        window.APPVERBO_RUN_MODULE_BOOTSTRAP_STEP_V1(step, context);
      }

      return {
        runStep
      };
    };
})();
// APPVERBO_MODULE_BOOTSTRAP_RUNNER_BRIDGE_V1_MODULE_END
