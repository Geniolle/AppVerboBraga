//###################################################################################
// (1) SETUP BRIDGES V1
//###################################################################################
(function registerSetupBridgesV1() {
  "use strict";

  function runSetupBridgeV1(action, context = {}) {
    const actionName = String(action || "").trim();

    if (actionName === "syncTrainingOutrosState") {
      if (typeof window.APPVERBO_SYNC_TRAINING_OUTROS_STATE_V1 !== "function") {
        return;
      }
      window.APPVERBO_SYNC_TRAINING_OUTROS_STATE_V1({
        trainingOutrosInputEl: context.trainingOutrosInputEl,
        trainingOutrosEnabledEl: context.trainingOutrosEnabledEl
      });
      return;
    }

    if (actionName === "setupTableLimiter") {
      if (typeof window.APPVERBO_SETUP_TABLE_LIMITER_V1 !== "function") {
        return;
      }
      window.APPVERBO_SETUP_TABLE_LIMITER_V1({
        prefix: context.prefix
      });
      return;
    }

    if (actionName === "setupReadOnlyCards") {
      if (typeof window.APPVERBO_SETUP_READ_ONLY_CARDS_V1 !== "function") {
        return;
      }
      window.APPVERBO_SETUP_READ_ONLY_CARDS_V1();
      return;
    }

    if (actionName === "setupProcessFieldsBuilder") {
      if (typeof window.APPVERBO_SETUP_PROCESS_FIELDS_BUILDER_V1 !== "function") {
        return;
      }
      window.APPVERBO_SETUP_PROCESS_FIELDS_BUILDER_V1();
      return;
    }

    if (actionName === "setupProcessAdditionalFieldsBuilder") {
      if (typeof window.APPVERBO_SETUP_PROCESS_ADDITIONAL_FIELDS_BUILDER_V1 !== "function") {
        return;
      }
      window.APPVERBO_SETUP_PROCESS_ADDITIONAL_FIELDS_BUILDER_V1();
      return;
    }

    if (actionName === "setupProcessEditTabs") {
      if (typeof window.APPVERBO_SETUP_PROCESS_EDIT_TABS_V1 !== "function") {
        return;
      }
      window.APPVERBO_SETUP_PROCESS_EDIT_TABS_V1({
        settingsAction: context.settingsAction,
        settingsTab: context.settingsTab
      });
    }
  }

  window.APPVERBO_RUN_SETUP_BRIDGE_V1 = runSetupBridgeV1;
})();
