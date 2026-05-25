//###################################################################################
// (1) TRAINING OUTROS STATE V1
//###################################################################################
(function registerTrainingOutrosStateV1() {
  "use strict";

  function syncTrainingOutrosStateV1(context = {}) {
    const trainingOutrosInputEl = context.trainingOutrosInputEl || null;
    const trainingOutrosEnabledEl = context.trainingOutrosEnabledEl || null;

    if (!trainingOutrosInputEl) {
      return;
    }

    const isEnabled = trainingOutrosEnabledEl ? trainingOutrosEnabledEl.checked : false;
    trainingOutrosInputEl.disabled = !isEnabled;
    if (!isEnabled) {
      trainingOutrosInputEl.value = "";
    }
  }

  window.APPVERBO_SYNC_TRAINING_OUTROS_STATE_V1 = syncTrainingOutrosStateV1;
})();
