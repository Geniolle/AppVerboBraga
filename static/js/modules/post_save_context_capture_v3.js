// APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_MODULE_START
(function registerPostSaveContextCaptureV3Module() {
  "use strict";

  function normalizeMenuKeyFallbackV3(value) {
    return String(value === null || value === undefined ? "" : value).trim().toLowerCase();
  }

  function normalizeLookupTextFallbackV3(value) {
    return String(value === null || value === undefined ? "" : value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  window.APPVERBO_SETUP_POST_SAVE_CONTEXT_CAPTURE_V3 = function setupPostSaveContextCaptureV3(options) {
    const deps = options && typeof options === "object" ? options : {};

    const APPVERBO_POST_SAVE_CONTEXT_KEY_V3 = String(
      deps.APPVERBO_POST_SAVE_CONTEXT_KEY_V3 || "appverbo:post-save-context-v3"
    );
    const MEU_PERFIL_MENU_KEY = String(deps.MEU_PERFIL_MENU_KEY || "meu_perfil");
    const initialMenu = typeof deps.initialMenu === "undefined" ? "" : deps.initialMenu;
    const profilePersonalSections = Array.isArray(deps.profilePersonalSections)
      ? deps.profilePersonalSections
      : [];
    const selectedDynamicSectionByMenu = (
      deps.selectedDynamicSectionByMenu && typeof deps.selectedDynamicSectionByMenu === "object"
    )
      ? deps.selectedDynamicSectionByMenu
      : {};
    const normalizeMenuKey = typeof deps.normalizeMenuKey === "function"
      ? deps.normalizeMenuKey
      : normalizeMenuKeyFallbackV3;
    const normalizeLookupText = typeof deps.normalizeLookupText === "function"
      ? deps.normalizeLookupText
      : normalizeLookupTextFallbackV3;

// APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_START
//###################################################################################
// (POST_SAVE_CONTEXT_CAPTURE_V3) GUARDAR PROCESSO/ABA ANTES DE QUALQUER POST
//###################################################################################

(function setupAppVerboPostSaveContextCaptureV3() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safePostSaveTextV3(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizePostSaveKeyV3(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safePostSaveTextV3(value).trim().toLowerCase();
  }

  function normalizePostSaveLookupV3(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safePostSaveTextV3(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function ensureHiddenPostSaveInputV3(form, name) {
    let input = form.querySelector("input[name='" + name + "']");

    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }

    return input;
  }

  function getFormActionPostSaveV3(form) {
    return safePostSaveTextV3(form && (form.getAttribute("action") || form.action));
  }

  function getFormMethodPostSaveV3(form) {
    return safePostSaveTextV3(form && (form.getAttribute("method") || form.method || "post"))
      .trim()
      .toLowerCase();
  }

  function readFirstFormValuePostSaveV3(form, names) {
    if (!form) {
      return "";
    }

    for (const name of names) {
      const control = form.querySelector("[name='" + name + "']");

      if (!control) {
        continue;
      }

      const value = safePostSaveTextV3(control.value).trim();

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getCurrentUrlPostSaveV3() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return new URL("/users/new", window.location.origin);
    }
  }

  function getProfileSectionFromInputPostSaveV3() {
    const selectors = [
      "#perfil-pessoal-card input[name='profile_section']",
      "#perfil-pessoal-card [data-meu-perfil-section-input]",
      "#perfil-pessoal-card [data-profile-section-input]",
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    for (const selector of selectors) {
      const input = document.querySelector(selector);
      const value = normalizePostSaveKeyV3(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getProfileSectionFromActiveTabPostSaveV3() {
    const sections = Array.isArray(profilePersonalSections) ? profilePersonalSections : [];

    const activeSelectors = [
      "#perfil-pessoal-card [data-profile-section-tab].active",
      "#perfil-pessoal-card [data-profile-section-tab][aria-selected='true']",
      "#perfil-pessoal-card [data-profile-section-button].active",
      "#perfil-pessoal-card [data-profile-section-button][aria-selected='true']",
      "#perfil-pessoal-card .profile-section-tab.active",
      "#perfil-pessoal-card .profile-section-tab[aria-selected='true']",
      "#perfil-pessoal-card .active"
    ];

    for (const selector of activeSelectors) {
      const activeElement = document.querySelector(selector);

      if (!activeElement) {
        continue;
      }

      const datasetSection = normalizePostSaveKeyV3(
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      if (datasetSection) {
        return datasetSection;
      }

      const activeLabel = normalizePostSaveLookupV3(activeElement.textContent);

      if (!activeLabel) {
        continue;
      }

      for (const section of sections) {
        const sectionLabel = normalizePostSaveLookupV3(section && section.label);

        if (sectionLabel && sectionLabel === activeLabel) {
          return normalizePostSaveKeyV3(section && section.key);
        }
      }
    }

    return "";
  }

  function getProfileSectionFromVisiblePanePostSaveV3() {
    const panes = Array.from(
      document.querySelectorAll("#perfil-pessoal-card [data-profile-section-pane]")
    );

    for (const pane of panes) {
      const style = window.getComputedStyle ? window.getComputedStyle(pane) : null;

      if (
        pane.hidden ||
        pane.style.display === "none" ||
        (style && style.display === "none")
      ) {
        continue;
      }

      const sectionKey = normalizePostSaveKeyV3(pane.dataset.profileSectionPane);

      if (sectionKey) {
        return sectionKey;
      }
    }

    return "";
  }

  function getCurrentProfileSectionPostSaveV3() {
    return (
      getProfileSectionFromInputPostSaveV3() ||
      getProfileSectionFromActiveTabPostSaveV3() ||
      getProfileSectionFromVisiblePanePostSaveV3() ||
      (
        Array.isArray(profilePersonalSections) && profilePersonalSections.length
          ? normalizePostSaveKeyV3(profilePersonalSections[0].key)
          : ""
      )
    );
  }

  function getDynamicSectionPostSaveV3(menuKey) {
    const formValue = readFirstFormValuePostSaveV3(document, [
      "dynamic_process_section",
      "section_key",
      "process_section",
      "active_section",
      "settings_tab"
    ]);

    if (formValue) {
      return normalizePostSaveKeyV3(formValue);
    }

    if (
      typeof selectedDynamicSectionByMenu === "object" &&
      selectedDynamicSectionByMenu !== null &&
      menuKey &&
      selectedDynamicSectionByMenu[menuKey]
    ) {
      return normalizePostSaveKeyV3(selectedDynamicSectionByMenu[menuKey]);
    }

    const activeElement = document.querySelector(
      "#dynamic-process-card .active, " +
      "#dynamic-process-card [aria-selected='true'], " +
      "[data-dynamic-process-section-key].active, " +
      "[data-dynamic-process-section-key][aria-selected='true']"
    );

    if (activeElement) {
      const datasetSection = normalizePostSaveKeyV3(
        activeElement.dataset.dynamicProcessSectionKey ||
        activeElement.dataset.sectionKey ||
        ""
      );

      if (datasetSection) {
        return datasetSection;
      }
    }

    return "";
  }

  function currentMenuFromUrlOrBootstrapPostSaveV3(form) {
    const currentUrl = getCurrentUrlPostSaveV3();

    const formMenu = normalizePostSaveKeyV3(
      readFirstFormValuePostSaveV3(form, [
        "menu",
        "menu_key",
        "process_menu_key",
        "dynamic_menu_key",
        "settings_edit_key"
      ])
    );

    if (formMenu) {
      return formMenu;
    }

    const urlMenu = normalizePostSaveKeyV3(currentUrl.searchParams.get("menu"));

    if (urlMenu) {
      return urlMenu;
    }

    if (typeof initialMenu !== "undefined") {
      const bootstrapMenu = normalizePostSaveKeyV3(initialMenu);

      if (bootstrapMenu) {
        return bootstrapMenu;
      }
    }

    return "";
  }

  //###################################################################################
  // (2) CONSTRUIR URL DE RETORNO
  //###################################################################################

  function buildPostSaveReturnUrlV3(form) {
    const currentUrl = getCurrentUrlPostSaveV3();

    [
      "admin_tab",
      "sidebar_sections_tab",
      "entity_edit_id",
      "user_edit_id",
      "definition_edit_id",
      "settings_edit_key",
      "settings_action",
      "sidebar_section_edit_key",
      "sidebar_section_return_url",
      "account_edit_id",
      "entity_view",
      "user_view"
    ].forEach(function (paramName) {
      currentUrl.searchParams.delete(paramName);
    });

    currentUrl.pathname = "/users/new";

    const action = getFormActionPostSaveV3(form);
    const actionLookup = normalizePostSaveLookupV3(action);
    let menuKey = currentMenuFromUrlOrBootstrapPostSaveV3(form);

    if (actionLookup.includes("/users/profile/personal")) {
      menuKey = MEU_PERFIL_MENU_KEY;
      currentUrl.searchParams.set("menu", MEU_PERFIL_MENU_KEY);
      currentUrl.searchParams.set("target", "#perfil-pessoal-card");
      currentUrl.searchParams.set("profile_tab", "pessoal");
      currentUrl.searchParams.delete("admin_tab");
      currentUrl.searchParams.delete("sidebar_sections_tab");
      currentUrl.hash = "#perfil-pessoal-card";

      const profileSection = getCurrentProfileSectionPostSaveV3();

      if (profileSection) {
        currentUrl.searchParams.set("profile_section", profileSection);
      }
    } else {
      if (actionLookup.includes("/users/profile/process-data")) {
        currentUrl.searchParams.set("target", "#dynamic-process-card");
        currentUrl.hash = "#dynamic-process-card";
      }

      if (menuKey) {
        currentUrl.searchParams.set("menu", menuKey);
      }

      const formTarget = readFirstFormValuePostSaveV3(form, ["target", "return_target"]);

      if (formTarget) {
        currentUrl.searchParams.set("target", formTarget);
      }

      const settingsEditKey = normalizePostSaveKeyV3(
        readFirstFormValuePostSaveV3(form, ["settings_edit_key", "menu_key"])
      );
      const settingsAction = normalizePostSaveKeyV3(
        readFirstFormValuePostSaveV3(form, ["settings_action"])
      );
      const settingsTab = normalizePostSaveKeyV3(
        readFirstFormValuePostSaveV3(form, ["settings_tab"])
      );

      if (settingsEditKey && currentUrl.searchParams.get("menu") === "administrativo") {
        currentUrl.searchParams.set("settings_edit_key", settingsEditKey);
        currentUrl.searchParams.set("settings_action", settingsAction || "edit");

        if (settingsTab) {
          currentUrl.searchParams.set("settings_tab", settingsTab);
        }

        if (!currentUrl.searchParams.get("target")) {
          currentUrl.searchParams.set("target", "#settings-menu-edit-card");
        }
      }

      const dynamicSection = getDynamicSectionPostSaveV3(menuKey);

      if (dynamicSection) {
        currentUrl.searchParams.set("dynamic_process_section", dynamicSection);
      }
    }

    if (actionLookup.includes("/entities/update")) {
      currentUrl.searchParams.set("menu", "administrativo");
      currentUrl.searchParams.set("admin_tab", "entidade");
      currentUrl.searchParams.set("target", "#create-entity-card");
      currentUrl.searchParams.delete("dynamic_process_section");
      currentUrl.searchParams.delete("section_key");
      currentUrl.hash = "#create-entity-card";
    } else if (actionLookup.includes("/users/update")) {
      currentUrl.searchParams.set("menu", "administrativo");
      currentUrl.searchParams.set("admin_tab", "utilizador");
      currentUrl.searchParams.set("target", "#create-user-card");
      currentUrl.searchParams.delete("dynamic_process_section");
      currentUrl.searchParams.delete("section_key");
      currentUrl.hash = "#create-user-card";
    } else if (actionLookup.includes("/users/new")) {
      currentUrl.searchParams.set("menu", "administrativo");
      currentUrl.searchParams.set("admin_tab", "utilizador");
      currentUrl.searchParams.set("target", "#create-user-card");
      currentUrl.searchParams.delete("dynamic_process_section");
      currentUrl.searchParams.delete("section_key");
      currentUrl.hash = "#create-user-card";
    } else if (
      actionLookup.includes("/settings/menu/sidebar-section-save") ||
      actionLookup.includes("/settings/menu/sidebar-section-move-one") ||
      actionLookup.includes("/settings/menu/sidebar-section-delete-one") ||
      actionLookup.includes("/settings/menu/sidebar-sections")
    ) {
      currentUrl.searchParams.set("menu", "administrativo");
      currentUrl.searchParams.set("admin_tab", "sessoes");
      currentUrl.searchParams.set("sidebar_sections_tab", "sessoes");
      currentUrl.searchParams.set("target", "#admin-sidebar-sections-card");
      currentUrl.searchParams.delete("dynamic_process_section");
      currentUrl.searchParams.delete("section_key");
      currentUrl.hash = "#admin-sidebar-sections-card";
    } else if (actionLookup.includes("/settings/menu/save")) {
      currentUrl.searchParams.set("menu", "administrativo");
      currentUrl.searchParams.set("admin_tab", "menu");
      currentUrl.searchParams.set("target", "#admin-menu-card");
      currentUrl.searchParams.delete("dynamic_process_section");
      currentUrl.searchParams.delete("section_key");
      currentUrl.hash = "#admin-menu-card";
    } else if (
      actionLookup.includes("/settings/definicoes/save") ||
      actionLookup.includes("/settings/definicoes/delete")
    ) {
      currentUrl.searchParams.set("menu", "administrativo");
      currentUrl.searchParams.set("admin_tab", "definicoes");
      currentUrl.searchParams.set("target", "#admin-definicoes-card");
      currentUrl.searchParams.delete("dynamic_process_section");
      currentUrl.searchParams.delete("section_key");
      currentUrl.hash = "#admin-definicoes-card";
    }

    currentUrl.searchParams.set("appverbo_after_save", "1");

    return currentUrl.pathname + currentUrl.search + currentUrl.hash;
  }

  //###################################################################################
  // (3) GUARDAR CONTEXTO
  //###################################################################################

  function storePostSaveContextV3(form) {
    if (!form) {
      return;
    }

    const method = getFormMethodPostSaveV3(form);

    if (method && method !== "post") {
      return;
    }

    const returnUrl = buildPostSaveReturnUrlV3(form);

    try {
      window.sessionStorage.setItem(
        APPVERBO_POST_SAVE_CONTEXT_KEY_V3,
        JSON.stringify({
          url: returnUrl,
          createdAt: Date.now()
        })
      );
    } catch (error) {
      // Ignora falhas de sessionStorage.
    }

    ensureHiddenPostSaveInputV3(form, "appverbo_after_save").value = "1";
    ensureHiddenPostSaveInputV3(form, "return_url").value = returnUrl;
  }

  function bindPostSaveContextCaptureV3() {
    document.addEventListener("submit", function (event) {
      storePostSaveContextV3(event.target);
    }, true);

    document.addEventListener("click", function (event) {
      const submitControl = event.target && event.target.closest
        ? event.target.closest("button[type='submit'], input[type='submit'], button:not([type])")
        : null;

      if (!submitControl || !submitControl.form) {
        return;
      }

      storePostSaveContextV3(submitControl.form);
    }, true);

    if (
      window.HTMLFormElement &&
      window.HTMLFormElement.prototype &&
      !window.HTMLFormElement.prototype.__appverboPostSaveContextPatchedV3
    ) {
      const nativeSubmit = window.HTMLFormElement.prototype.submit;

      window.HTMLFormElement.prototype.submit = function patchedSubmitPostSaveContextV3() {
        storePostSaveContextV3(this);
        return nativeSubmit.call(this);
      };

      window.HTMLFormElement.prototype.__appverboPostSaveContextPatchedV3 = true;
    }
  }

  bindPostSaveContextCaptureV3();
})();

// APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_END
  };
})();
// APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_MODULE_END
