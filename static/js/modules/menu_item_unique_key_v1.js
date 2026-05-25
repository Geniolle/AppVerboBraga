//###################################################################################
// (1) MENU ITEM UNIQUE KEY V1
//###################################################################################
(function registerMenuItemUniqueKeyV1() {
  "use strict";

  function buildMenuItemUniqueKeyV1(item) {
    const target = String(item && item.target ? item.target : "").trim();
    const sectionKey = String(item && item.dynamicProcessSectionKey ? item.dynamicProcessSectionKey : "").trim();
    const profileSection = String(item && item.profileSection ? item.profileSection : "").trim();
    const label = String(item && item.label ? item.label : "").trim();

    return `${target}::${sectionKey}::${profileSection}::${label}`;
  }

  window.APPVERBO_BUILD_MENU_ITEM_UNIQUE_KEY_V1 = buildMenuItemUniqueKeyV1;
})();
