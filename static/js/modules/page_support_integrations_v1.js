//###################################################################################
// (1) PAGE SUPPORT INTEGRATIONS V1
//###################################################################################
(function registerPageSupportIntegrationsV1() {
  "use strict";

  function setupPageSupportIntegrationsV1(context = {}) {
    if (typeof window.APPVERBO_SETUP_GENERATED_INVITE_LINK_COPY_V1 === "function") {
      window.APPVERBO_SETUP_GENERATED_INVITE_LINK_COPY_V1();
    }

    if (typeof window.APPVERBO_SETUP_CREATE_USER_GENERATE_LINK_SHORTCUT_V1 === "function") {
      window.APPVERBO_SETUP_CREATE_USER_GENERATE_LINK_SHORTCUT_V1({
        currentEntityId: context.currentEntityId
      });
    }

    if (typeof window.APPVERBO_SETUP_SIDEBAR_SECTIONS_EDITOR_V1 === "function") {
      window.APPVERBO_SETUP_SIDEBAR_SECTIONS_EDITOR_V1();
    }
  }

  window.APPVERBO_SETUP_PAGE_SUPPORT_INTEGRATIONS_V1 = setupPageSupportIntegrationsV1;
})();
