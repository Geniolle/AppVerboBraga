//###################################################################################
// (1) PROCESS ADDITIONAL FIELDS MANAGER V2 GUARD V1
//###################################################################################
(function registerProcessAdditionalFieldsManagerV2GuardV1() {
  "use strict";

  function setupProcessAdditionalFieldsManagerV2GuardV1() {
    if (document.querySelector("[data-process-additional-fields-manager-v3='1']")) {
      return;
    }

    if (typeof window.setupProcessAdditionalFieldsManagerV2 === "function") {
      window.setupProcessAdditionalFieldsManagerV2();
    }
  }

  window.APPVERBO_SETUP_PROCESS_ADDITIONAL_FIELDS_MANAGER_V2_GUARD_V1 = setupProcessAdditionalFieldsManagerV2GuardV1;
})();
