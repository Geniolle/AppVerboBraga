//###################################################################################
// APPVERBOBRAGA - APPVERBO DIALOG V1
//###################################################################################

(function (window, document) {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function toSafeString_v1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function removeExistingDialog_v1() {
    const existingOverlay = document.querySelector(".appverbo-alert-overlay-v1");

    if (existingOverlay && existingOverlay.parentNode) {
      existingOverlay.parentNode.removeChild(existingOverlay);
    }
  }

  //###################################################################################
  // (2) ALERT DIALOG
  //###################################################################################

  function alert_v1(options) {
    const safeOptions = options && typeof options === "object" ? options : {};
    const title = toSafeString_v1(safeOptions.title).trim() || "Aviso";
    const message = toSafeString_v1(safeOptions.message).trim() || "Ocorreu uma validação.";
    const confirmLabel = toSafeString_v1(safeOptions.confirmLabel).trim() || "OK";
    const closeOnBackdrop = safeOptions.closeOnBackdrop !== false;
    const closeOnEscape = safeOptions.closeOnEscape !== false;

    removeExistingDialog_v1();

    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "appverbo-confirm-overlay-v1 appverbo-alert-overlay-v1";
      overlay.setAttribute("role", "dialog");
      overlay.setAttribute("aria-modal", "true");
      overlay.setAttribute("aria-labelledby", "appverbo-alert-title-v1");

      const dialog = document.createElement("div");
      dialog.className = "appverbo-confirm-dialog-v1 appverbo-alert-dialog-v1";

      const titleEl = document.createElement("h3");
      titleEl.className = "appverbo-confirm-title-v1 appverbo-alert-title-v1";
      titleEl.id = "appverbo-alert-title-v1";
      titleEl.textContent = title;

      const messageEl = document.createElement("p");
      messageEl.className = "appverbo-confirm-message-v1 appverbo-alert-message-v1";
      messageEl.textContent = message;

      const actionsEl = document.createElement("div");
      actionsEl.className = "appverbo-confirm-actions-v1 appverbo-alert-actions-v1";

      const confirmBtn = document.createElement("button");
      confirmBtn.type = "button";
      confirmBtn.className = "appverbo-confirm-action-v1";
      confirmBtn.textContent = confirmLabel;

      actionsEl.appendChild(confirmBtn);
      dialog.appendChild(titleEl);
      dialog.appendChild(messageEl);
      dialog.appendChild(actionsEl);
      overlay.appendChild(dialog);

      function closeDialog_v1() {
        if (overlay.parentNode) {
          overlay.parentNode.removeChild(overlay);
        }

        document.removeEventListener("keydown", onKeyDown_v1);
        resolve(true);
      }

      function onKeyDown_v1(event) {
        if (closeOnEscape && event.key === "Escape") {
          closeDialog_v1();
        }
      }

      confirmBtn.addEventListener("click", closeDialog_v1);

      overlay.addEventListener("click", (event) => {
        if (closeOnBackdrop && event.target === overlay) {
          closeDialog_v1();
        }
      });

      document.addEventListener("keydown", onKeyDown_v1);
      document.body.appendChild(overlay);
      confirmBtn.focus();
    });
  }

  window.AppVerboDialogV1 = {
    alert: alert_v1
  };
})(window, document);
