(function () {
  "use strict";

  //###################################################################################
  // (1) AUTOSAVE ANTIGO DESATIVADO
  //###################################################################################

  function sidebarSectionsAutosaveDesativado_v2() {
    window.APPGENESIS_SIDEBAR_SECTIONS_AUTOSAVE_DISABLED_V2 = true;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", sidebarSectionsAutosaveDesativado_v2);
  } else {
    sidebarSectionsAutosaveDesativado_v2();
  }
})();
