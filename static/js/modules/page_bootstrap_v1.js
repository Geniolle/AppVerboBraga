//###################################################################################
// (1) PAGE BOOTSTRAP V1
//###################################################################################
(function registerPageBootstrapV1() {
  "use strict";

  function setupPageBootstrapV1(context = {}) {
    const avatarDataUri = context.buildAvatarDataUri(context.currentUserName);
    if (context.userAvatarImageEl) {
      context.userAvatarImageEl.src = avatarDataUri;
    }
    if (context.dropdownAvatarImageEl) {
      context.dropdownAvatarImageEl.src = avatarDataUri;
    }

    context.menuButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        context.activateMenu(context.normalizeMenuKey(btn.dataset.menu), { resetDynamicToFirst: true });
      });
    });

    context.profileEditButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const cardId = button.getAttribute("data-edit-target");
        if (!cardId) {
          return;
        }
        context.closeAllProfileEdits();
        const card = document.getElementById(cardId);
        if (!card) {
          return;
        }
        card.classList.add("editing");
        if (cardId === "dynamic-process-card" && context.dynamicProcessCreateCardEl) {
          context.dynamicProcessCreateCardEl.classList.add("is-editing");
        }
      });
    });

    function bindDynamicProcessEditToggleV1(toggleEl) {
      if (!toggleEl || toggleEl.dataset.appverboDynamicEditBoundV1 === "1") {
        return;
      }
      toggleEl.dataset.appverboDynamicEditBoundV1 = "1";
      toggleEl.addEventListener("click", () => {
        if (context.dynamicProcessHistoryActionInputEl) {
          context.dynamicProcessHistoryActionInputEl.value = "create";
        }
        if (context.dynamicProcessHistoryRecordIdInputEl) {
          context.dynamicProcessHistoryRecordIdInputEl.value = "";
        }
        if (context.dynamicProcessSubmitBtnEl) {
          context.dynamicProcessSubmitBtnEl.textContent = "Guardar";
        }
        if (context.dynamicProcessEditFormEl) {
          context.dynamicProcessEditFormEl.reset();
        }
        if (context.dynamicProcessCardEl) {
          context.dynamicProcessCardEl.classList.remove("dynamic-process-history-show-readonly");
        }
      });
    }

    bindDynamicProcessEditToggleV1(context.dynamicProcessEditToggleEl);
    bindDynamicProcessEditToggleV1(document.getElementById("dynamic-process-header-edit-toggle"));

    context.profileEditCancelButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const cardId = button.getAttribute("data-edit-cancel");
        if (!cardId) {
          return;
        }
        const card = document.getElementById(cardId);
        if (!card) {
          return;
        }
        card.classList.remove("editing");
        if (cardId === "dynamic-process-card") {
          card.classList.remove("dynamic-process-history-show-readonly");
        }
        if (cardId === "dynamic-process-card" && context.dynamicProcessCreateCardEl) {
          context.dynamicProcessCreateCardEl.classList.remove("is-editing");
        }
        const form = card.querySelector(".profile-edit-form");
        if (form) {
          form.reset();
        }
      });
    });

    if (context.trainingOutrosEnabledEl) {
      context.trainingOutrosEnabledEl.addEventListener("change", () => {
        context.syncTrainingOutrosState();
      });
    }

    if (context.userMenuTriggerEl) {
      context.userMenuTriggerEl.addEventListener("click", (event) => {
        event.stopPropagation();
        context.toggleUserDropdown();
      });
    }

    context.userDropdownLinks.forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        const primaryMenuKey = context.normalizeMenuKey(
          link.getAttribute("data-dropdown-menu") || "perfil"
        );
        const fallbackMenuKey = context.normalizeMenuKey(
          link.getAttribute("data-dropdown-menu-fallback") || ""
        );
        const forceFirstSubprocess = ["1", "true", "on", "yes"].includes(
          String(link.getAttribute("data-dropdown-force-first") || "")
            .trim()
            .toLowerCase()
        );

        let menuKey = primaryMenuKey;
        if (!context.menuConfig[menuKey] && fallbackMenuKey && context.menuConfig[fallbackMenuKey]) {
          menuKey = fallbackMenuKey;
        }

        const targetSelector = link.getAttribute("data-dropdown-target") || "";
        if (!context.menuConfig[menuKey]) {
          context.closeUserDropdown();
          return;
        }
        if (targetSelector) {
          context.selectedTargetByMenu[menuKey] = targetSelector;
        }
        if (forceFirstSubprocess && typeof context.activateMenu === "function") {
          context.activateMenu(menuKey, { resetDynamicToFirst: true });

          if (targetSelector) {
            const targetCard = document.querySelector(targetSelector);
            if (targetCard) {
              targetCard.scrollIntoView({ behavior: "smooth", block: "start" });
            }
          }
        } else {
          context.activateMenuTarget(menuKey, targetSelector);
        }
        context.closeUserDropdown();
      });
    });

    document.addEventListener("click", (event) => {
      if (!context.userMenuEl || !context.userDropdownEl || context.userDropdownEl.hidden) {
        return;
      }
      if (!context.userMenuEl.contains(event.target)) {
        context.closeUserDropdown();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        context.closeUserDropdown();
      }
    });

    window.addEventListener("hashchange", () => {
      context.handleHashNavigation(window.location.hash || "");
    });

    context.syncTrainingOutrosState();
    context.renderHomeCharts();
    context.setupReadOnlyCards();
    context.setupProfileProcessTabs();
    context.setupMeuPerfilQuantityRules();
    context.setupConditionalProcessVisibility();
    context.setupProcessEditTabs();
    context.setupProcessFieldsBuilder();
    context.setupProcessAdditionalFieldsManagerV2_guard_v1();
    window.setTimeout(() => {
      try {
        context.setupProcessAdditionalFieldsManagerV2_guard_v1();
      } catch (_error) {
      }
    }, 150);
    window.setTimeout(() => {
      try {
        context.setupProcessAdditionalFieldsManagerV2_guard_v1();
      } catch (_error) {
      }
    }, 600);
    if (typeof context.setupPageSupportIntegrations === "function") {
      context.setupPageSupportIntegrations();
    } else {
      if (typeof context.setupGeneratedInviteLinkCopy === "function") {
        context.setupGeneratedInviteLinkCopy();
      }
      if (typeof context.setupCreateUserGenerateLinkShortcut === "function") {
        context.setupCreateUserGenerateLinkShortcut();
      }
      if (typeof context.setupSidebarSectionsEditor === "function") {
        context.setupSidebarSectionsEditor();
      }
    }
    context.setupTableLimiter("recent-entities");
    context.setupTableLimiter("inactive-entities");
    context.setupTableLimiter("admin-users");

    const sidebarMenuKeys = new Set(Array.from(context.menuButtons).map((btn) => context.normalizeMenuKey(btn.dataset.menu)));
    let startupMenu = context.menuConfig[context.initialMenu] ? context.initialMenu : "home";
    if (!sidebarMenuKeys.has(startupMenu) && startupMenu !== "perfil") {
      if (sidebarMenuKeys.has("home")) {
        startupMenu = "home";
      } else {
        const firstSidebarMenu = Array.from(sidebarMenuKeys.values())[0];
        startupMenu = firstSidebarMenu || "home";
      }
    }
    context.activateMenu(startupMenu, { resetDynamicToFirst: false });
    context.handleHashNavigation(window.location.hash || "");
  }

  window.APPVERBO_SETUP_PAGE_BOOTSTRAP_V1 = setupPageBootstrapV1;
})();
