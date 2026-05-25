// APPVERBO_AUTO_DISMISS_FLASH_MESSAGES_V1_MODULE_START
(function registerAutoDismissFlashMessagesV1Module() {
  "use strict";

  window.APPVERBO_SETUP_AUTO_DISMISS_FLASH_MESSAGES_V1 = function setupAutoDismissFlashMessagesV1(options) {
    const deps = options && typeof options === "object" ? options : {};
/* APPVERBO_AUTO_DISMISS_FLASH_MESSAGES_V1_START */
function appverboAutoDismissFlashMessages_v1() {
  const successAlerts = Array.from(document.querySelectorAll(".alert.ok"));

  successAlerts.forEach((alertElement) => {
    if (!alertElement || alertElement.dataset.appverboAutoDismiss === "1") {
      return;
    }

    alertElement.dataset.appverboAutoDismiss = "1";

    window.setTimeout(() => {
      alertElement.style.transition = "opacity 250ms ease, max-height 250ms ease, margin 250ms ease, padding 250ms ease";
      alertElement.style.opacity = "0";
      alertElement.style.maxHeight = "0";
      alertElement.style.marginTop = "0";
      alertElement.style.marginBottom = "0";
      alertElement.style.paddingTop = "0";
      alertElement.style.paddingBottom = "0";
      alertElement.style.overflow = "hidden";

      window.setTimeout(() => {
        alertElement.remove();
      }, 300);
    }, 5000);
  });

  const url = new URL(window.location.href);
  const transientParams = [
    "success",
    "profile_success",
    "settings_success",
  ];

  let changed = false;

  transientParams.forEach((paramName) => {
    if (url.searchParams.has(paramName)) {
      url.searchParams.delete(paramName);
      changed = true;
    }
  });

  if (changed) {
    const cleanUrl = `${url.pathname}${url.search}${url.hash}`;
    window.history.replaceState({}, document.title, cleanUrl);
  }
}

document.addEventListener("DOMContentLoaded", appverboAutoDismissFlashMessages_v1);
/* APPVERBO_AUTO_DISMISS_FLASH_MESSAGES_V1_END */
  };
})();
// APPVERBO_AUTO_DISMISS_FLASH_MESSAGES_V1_MODULE_END
