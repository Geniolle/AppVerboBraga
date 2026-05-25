// APPVERBO_PAGE_DOM_REGISTRY_V1_MODULE_START
(function registerPageDomRegistryV1Module() {
  "use strict";

  window.APPVERBO_BUILD_PAGE_DOM_REGISTRY_V1 = function buildPageDomRegistryV1() {
    return {
      itemsEl: document.getElementById("submenu-items"),
      menuTabsCardEl: document.getElementById("menu-tabs-card"),
      menuButtons: document.querySelectorAll(".menu-item"),
      scopedCards: document.querySelectorAll("[data-menu-scope]"),
      userMenuEl: document.getElementById("user-menu"),
      userMenuTriggerEl: document.getElementById("user-menu-trigger"),
      userDropdownEl: document.getElementById("user-dropdown"),
      userAvatarImageEl: document.getElementById("user-avatar-image"),
      dropdownAvatarImageEl: document.getElementById("dropdown-avatar-image"),
      userDropdownLinks: document.querySelectorAll("[data-dropdown-target]"),
      profileEditButtons: document.querySelectorAll("[data-edit-target]"),
      profileEditCancelButtons: document.querySelectorAll("[data-edit-cancel]"),
      trainingOutrosEnabledEl: document.getElementById("edit_training_outros_enabled"),
      trainingOutrosInputEl: document.getElementById("edit_training_outros"),
      processFieldsBuilderEl: document.getElementById("process-fields-builder"),
      dynamicProcessCreateCardEl: document.getElementById("dynamic-process-create-card"),
      dynamicProcessCardEl: document.getElementById("dynamic-process-card"),
      dynamicProcessTitleEl: document.getElementById("dynamic-process-title"),
      dynamicProcessDescriptionEl: document.getElementById("dynamic-process-description"),
      dynamicProcessSectionLabelEl: document.getElementById("dynamic-process-section-label"),
      dynamicProcessReadOnlyEl: document.getElementById("dynamic-process-readonly"),
      dynamicProcessReadOnlyGridEl: document.getElementById("dynamic-process-readonly-grid"),
      dynamicProcessEditGridEl: document.getElementById("dynamic-process-edit-grid"),
      dynamicProcessEditFormEl: document.getElementById("dynamic-process-edit-form"),
      dynamicProcessMenuKeyInputEl: document.getElementById("dynamic-process-menu-key"),
      dynamicProcessSectionKeyInputEl: document.getElementById("dynamic-process-section-key"),
      dynamicProcessHistoryActionInputEl: document.getElementById("dynamic-process-history-action"),
      dynamicProcessHistoryRecordIdInputEl: document.getElementById("dynamic-process-history-record-id"),
      dynamicProcessSubmitBtnEl: document.getElementById("dynamic-process-submit-btn"),
      dynamicProcessEditToggleEl: document.getElementById("dynamic-process-edit-toggle"),
      dynamicProcessEmptyEl: document.getElementById("dynamic-process-empty"),
      dynamicProcessHistoryBlockEl: document.getElementById("dynamic-process-history-block"),
      dynamicProcessHistoryTitleEl: document.getElementById("dynamic-process-history-title"),
      dynamicProcessHistoryTableEl: document.getElementById("dynamic-process-history-table"),
      dynamicProcessHistoryHeadEl: document.getElementById("dynamic-process-history-head"),
      dynamicProcessHistoryBodyEl: document.getElementById("dynamic-process-history-body"),
      dynamicProcessHistoryEmptyEl: document.getElementById("dynamic-process-history-empty"),
      dynamicProcessHistoryActiveCardEl: document.getElementById("dynamic-process-history-active-card"),
      dynamicProcessHistoryActiveTitleEl: document.getElementById("dynamic-process-history-active-title"),
      dynamicProcessHistoryActiveTableEl: document.getElementById("dynamic-process-history-active-table"),
      dynamicProcessHistoryActiveHeadEl: document.getElementById("dynamic-process-history-active-head"),
      dynamicProcessHistoryActiveBodyEl: document.getElementById("dynamic-process-history-active-body"),
      dynamicProcessHistoryActiveEmptyEl: document.getElementById("dynamic-process-history-active-empty"),
      dynamicProcessHistoryInactiveCardEl: document.getElementById("dynamic-process-history-inactive-card"),
      dynamicProcessHistoryInactiveTitleEl: document.getElementById("dynamic-process-history-inactive-title"),
      dynamicProcessHistoryInactiveTableEl: document.getElementById("dynamic-process-history-inactive-table"),
      dynamicProcessHistoryInactiveHeadEl: document.getElementById("dynamic-process-history-inactive-head"),
      dynamicProcessHistoryInactiveBodyEl: document.getElementById("dynamic-process-history-inactive-body"),
      dynamicProcessHistoryInactiveEmptyEl: document.getElementById("dynamic-process-history-inactive-empty")
    };
  };
})();
// APPVERBO_PAGE_DOM_REGISTRY_V1_MODULE_END
