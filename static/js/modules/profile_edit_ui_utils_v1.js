// APPVERBO_PROFILE_EDIT_UI_UTILS_V1_MODULE_START
(function registerProfileEditUiUtilsV1Module() {
  "use strict";

  window.APPVERBO_CREATE_PROFILE_EDIT_UI_UTILS_API_V1 = function createProfileEditUiUtilsApiV1() {
    //###################################################################################
    // (1) QUANTITY V4 TARGET HELPERS
    //###################################################################################
    function isMeuPerfilQuantityV4GeneratedTarget(targetEl) {
      if (!targetEl || typeof targetEl.closest !== "function") {
        return false;
      }

      if (targetEl.dataset && (
        targetEl.dataset.appverboQuantityFieldKeyV4 ||
        targetEl.dataset.appverboQuantityRuleKeyV4
      )) {
        return true;
      }

      return Boolean(
        targetEl.closest("[data-appverbo-quantity-edit-generated-v4='1']")
      );
    }

    //###################################################################################
    // (2) PROFILE EDIT UI RESET
    //###################################################################################
    function closeAllProfileEdits(options = {}) {
      const dynamicProcessCreateCardEl = options.dynamicProcessCreateCardEl || null;
      const dynamicProcessCardEl = options.dynamicProcessCardEl || null;
      const syncTrainingOutrosState =
        typeof options.syncTrainingOutrosState === "function"
          ? options.syncTrainingOutrosState
          : function noop() {};

      const editingCards = document.querySelectorAll(".card.editing");
      editingCards.forEach((card) => {
        card.classList.remove("editing");
        const form = card.querySelector(".profile-edit-form");
        if (form) {
          form.reset();
        }
      });
      if (dynamicProcessCreateCardEl) {
        dynamicProcessCreateCardEl.classList.remove("is-editing");
      }
      if (dynamicProcessCardEl) {
        dynamicProcessCardEl.classList.remove("dynamic-process-history-show-readonly");
      }
      syncTrainingOutrosState();
    }

    return {
      isMeuPerfilQuantityV4GeneratedTarget,
      closeAllProfileEdits
    };
  };
})();
// APPVERBO_PROFILE_EDIT_UI_UTILS_V1_MODULE_END
