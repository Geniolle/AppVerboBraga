// APPVERBO_USER_DROPDOWN_UI_V1_MODULE_START
(function registerUserDropdownUiV1Module() {
  "use strict";

  window.APPVERBO_CREATE_USER_DROPDOWN_UI_API_V1 = function createUserDropdownUiApiV1() {
    //###################################################################################
    // (1) ACOES BASE
    //###################################################################################
    function closeUserDropdown(userDropdownEl, userMenuTriggerEl) {
      if (!userDropdownEl || !userMenuTriggerEl) {
        return;
      }
      userDropdownEl.hidden = true;
      userMenuTriggerEl.setAttribute("aria-expanded", "false");
    }

    function openUserDropdown(userDropdownEl, userMenuTriggerEl) {
      if (!userDropdownEl || !userMenuTriggerEl) {
        return;
      }
      userDropdownEl.hidden = false;
      userMenuTriggerEl.setAttribute("aria-expanded", "true");
    }

    function toggleUserDropdown(userDropdownEl, userMenuTriggerEl) {
      if (!userDropdownEl || !userMenuTriggerEl) {
        return;
      }
      const expanded = userMenuTriggerEl.getAttribute("aria-expanded") === "true";
      if (expanded) {
        closeUserDropdown(userDropdownEl, userMenuTriggerEl);
      } else {
        openUserDropdown(userDropdownEl, userMenuTriggerEl);
      }
    }

    return {
      closeUserDropdown,
      openUserDropdown,
      toggleUserDropdown
    };
  };
})();
// APPVERBO_USER_DROPDOWN_UI_V1_MODULE_END
