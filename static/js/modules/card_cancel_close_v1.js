// APPVERBO_CARD_CANCEL_CLOSE_V1_MODULE_START
(function registerCardCancelCloseV1Module() {
  "use strict";

  const BOUND_FLAG_V1 = "__APPVERBO_CARD_CANCEL_CLOSE_V1_BOUND__";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function normalizeTextV1(value) {
    return String(value || "").trim();
  }

  function resolveReturnUrlV1(triggerEl) {
    if (!triggerEl) {
      return "";
    }

    const dataUrl = normalizeTextV1(triggerEl.getAttribute("data-card-cancel-return-url"));
    if (dataUrl) {
      return dataUrl;
    }

    return normalizeTextV1(triggerEl.getAttribute("href"));
  }

  function resetClosestFormV1(triggerEl) {
    if (!triggerEl || triggerEl.getAttribute("data-card-cancel-reset-form") === "0") {
      return;
    }

    const formEl = triggerEl.closest("form");
    if (!formEl || typeof formEl.reset !== "function") {
      return;
    }

    formEl.reset();
  }

  // Closes the nearest <details> ancestor.
  // Returns true if found and closed, false otherwise.
  function closeClosestDetailsV1(triggerEl) {
    if (!triggerEl || triggerEl.getAttribute("data-card-cancel-close-details") === "0") {
      return false;
    }

    const detailsEl = triggerEl.closest("details");
    if (!detailsEl) {
      return false;
    }

    detailsEl.open = false;
    return true;
  }

  //###################################################################################
  // (2) PUBLIC API
  //
  // Priority:
  //   1. Close the nearest <details> (CREATE collapse) — no page reload needed.
  //   2. Navigate to return_url via full page load — required for server-rendered
  //      EDIT cards where the DOM can only be updated by the server.
  //###################################################################################

  function handleCardCancelCloseV1(triggerEl) {
    if (!triggerEl) {
      return false;
    }

    resetClosestFormV1(triggerEl);

    if (closeClosestDetailsV1(triggerEl)) {
      return true;
    }

    const returnUrl = resolveReturnUrlV1(triggerEl);
    if (!returnUrl) {
      return false;
    }

    window.location.assign(returnUrl);
    return true;
  }

  //###################################################################################
  // (3) GLOBAL BIND
  //###################################################################################

  function bindCardCancelCloseV1() {
    if (window[BOUND_FLAG_V1]) {
      return;
    }

    window[BOUND_FLAG_V1] = true;

    document.addEventListener("click", function handleCardCancelClickV1(event) {
      const triggerEl = event.target && typeof event.target.closest === "function"
        ? event.target.closest("[data-card-cancel-close='1']")
        : null;

      if (!triggerEl) {
        return;
      }

      event.preventDefault();
      handleCardCancelCloseV1(triggerEl);
    });
  }

  bindCardCancelCloseV1();

  window.APPVERBO_HANDLE_CARD_CANCEL_CLOSE_V1 = handleCardCancelCloseV1;
})();
// APPVERBO_CARD_CANCEL_CLOSE_V1_MODULE_END
