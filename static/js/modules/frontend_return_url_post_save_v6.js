// APPVERBO_FRONTEND_RETURN_URL_POST_SAVE_V6_MODULE_START
(function registerFrontendReturnUrlPostSaveV6Module() {
  "use strict";

  function normalizeMenuKeyFallbackV6(value) {
    return String(value === null || value === undefined ? "" : value).trim().toLowerCase();
  }

  function normalizeLookupTextFallbackV6(value) {
    return String(value === null || value === undefined ? "" : value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  window.APPVERBO_SETUP_FRONTEND_RETURN_URL_POST_SAVE_V6 = function setupFrontendReturnUrlPostSaveV6(options) {
    const deps = options && typeof options === "object" ? options : {};

    const initialMenu = typeof deps.initialMenu === "undefined" ? "" : deps.initialMenu;
    const profilePersonalSections = Array.isArray(deps.profilePersonalSections)
      ? deps.profilePersonalSections
      : [];
    const normalizeMenuKey = typeof deps.normalizeMenuKey === "function"
      ? deps.normalizeMenuKey
      : normalizeMenuKeyFallbackV6;
    const normalizeLookupText = typeof deps.normalizeLookupText === "function"
      ? deps.normalizeLookupText
      : normalizeLookupTextFallbackV6;

// APPVERBO_FRONTEND_RETURN_URL_POST_SAVE_V6_START
//###################################################################################
// (FRONTEND_RETURN_URL_POST_SAVE_V6) ENVIAR RETURN_URL SEGURO ANTES DO POST
//###################################################################################

(function setupFrontendReturnUrlPostSaveV6() {
  "use strict";

  function safeReturnUrlTextV6(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeReturnUrlKeyV6(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeReturnUrlTextV6(value).trim().toLowerCase();
  }

  function normalizeReturnUrlLookupV6(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeReturnUrlTextV6(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function ensureHiddenReturnUrlInputV6(form, name) {
    let input = form.querySelector("input[name='" + name + "']");

    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }

    return input;
  }

  function getCurrentUrlReturnUrlV6() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return new URL("/users/new", window.location.origin);
    }
  }

  function getFormActionReturnUrlV6(form) {
    return safeReturnUrlTextV6(form && (form.getAttribute("action") || form.action));
  }

  function getFormMethodReturnUrlV6(form) {
    return safeReturnUrlTextV6(form && (form.getAttribute("method") || form.method || "post"))
      .trim()
      .toLowerCase();
  }

  function getFormValueReturnUrlV6(form, names) {
    if (!form) {
      return "";
    }

    for (const name of names) {
      const control = form.querySelector("[name='" + name + "']");

      if (!control) {
        continue;
      }

      const value = safeReturnUrlTextV6(control.value).trim();

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getProfileSectionFromInputsReturnUrlV6() {
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
      const value = normalizeReturnUrlKeyV6(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getProfileSectionFromActiveTabReturnUrlV6() {
    const sections = (typeof profilePersonalSections !== "undefined" && Array.isArray(profilePersonalSections))
      ? profilePersonalSections
      : [];

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

      const dataSection = normalizeReturnUrlKeyV6(
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      if (dataSection) {
        return dataSection;
      }

      const activeLabel = normalizeReturnUrlLookupV6(activeElement.textContent);

      if (!activeLabel) {
        continue;
      }

      for (const section of sections) {
        const sectionLabel = normalizeReturnUrlLookupV6(section && section.label);

        if (sectionLabel && sectionLabel === activeLabel) {
          return normalizeReturnUrlKeyV6(section && section.key);
        }
      }
    }

    return "";
  }

  function getProfileSectionFromVisiblePaneReturnUrlV6() {
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

      const sectionKey = normalizeReturnUrlKeyV6(pane.dataset.profileSectionPane);

      if (sectionKey) {
        return sectionKey;
      }
    }

    return "";
  }

  function getCurrentProfileSectionReturnUrlV6() {
    return (
      getProfileSectionFromInputsReturnUrlV6() ||
      getProfileSectionFromActiveTabReturnUrlV6() ||
      getProfileSectionFromVisiblePaneReturnUrlV6()
    );
  }

  function getCurrentMenuReturnUrlV6(form) {
    const currentUrl = getCurrentUrlReturnUrlV6();

    const urlMenu = normalizeReturnUrlKeyV6(currentUrl.searchParams.get("menu"));

    if (urlMenu) {
      return urlMenu;
    }

    const formMenu = normalizeReturnUrlKeyV6(
      getFormValueReturnUrlV6(form, [
        "menu",
        "menu_key",
        "process_menu_key",
        "dynamic_menu_key"
      ])
    );

    if (formMenu) {
      return formMenu;
    }

    if (typeof initialMenu !== "undefined") {
      return normalizeReturnUrlKeyV6(initialMenu);
    }

    return "";
  }

  function getCurrentSettingsTabReturnUrlV6(form) {
    const formTab = normalizeReturnUrlKeyV6(
      getFormValueReturnUrlV6(form, ["settings_tab"])
    );

    if (formTab) {
      return formTab;
    }

    const currentUrl = getCurrentUrlReturnUrlV6();
    const urlTab = normalizeReturnUrlKeyV6(currentUrl.searchParams.get("settings_tab"));

    if (urlTab) {
      return urlTab;
    }

    const activeTab = document.querySelector(
      "[data-process-edit-tab].active, " +
      "[data-process-edit-tab][aria-selected='true'], " +
      "[data-process-edit-tab][data-active='true'], " +
      ".process-edit-tab-link.active"
    );

    if (!activeTab) {
      return "";
    }

    return normalizeReturnUrlKeyV6(
      activeTab.dataset.processEditTab ||
      activeTab.getAttribute("data-process-edit-tab") ||
      ""
    );
  }

  function getSettingsEditContextReturnUrlV6(form, menuKey) {
    const currentUrl = getCurrentUrlReturnUrlV6();
    const settingsEditKey = normalizeReturnUrlKeyV6(
      getFormValueReturnUrlV6(form, ["settings_edit_key"]) ||
      currentUrl.searchParams.get("settings_edit_key") ||
      ""
    );
    const settingsAction = normalizeReturnUrlKeyV6(
      getFormValueReturnUrlV6(form, ["settings_action"]) ||
      currentUrl.searchParams.get("settings_action") ||
      ""
    );
    const settingsTab = getCurrentSettingsTabReturnUrlV6(form);

    const shouldKeepContext = (
      menuKey === "administrativo" &&
      (
        settingsEditKey ||
        settingsTab ||
        normalizeReturnUrlLookupV6(currentUrl.searchParams.get("target")).includes("settings-menu-edit-card")
      )
    );

    if (!shouldKeepContext) {
      return {
        settingsEditKey: "",
        settingsAction: "",
        settingsTab: ""
      };
    }

    return {
      settingsEditKey,
      settingsAction: settingsAction || (settingsEditKey ? "edit" : ""),
      settingsTab
    };
  }

  function isProcessSettingsActionReturnUrlV6(actionLookup) {
    const processSettingsActions = [
      "/settings/menu/process-fields",
      "/settings/menu/process-additional-fields",
      "/settings/menu/process-quantity-fields",
      "/settings/menu/process-lists",
      "/settings/menu/process-subsequent-fields"
    ];

    return processSettingsActions.some(function (actionPath) {
      return actionLookup.includes(actionPath);
    });
  }

  function buildReturnUrlPostSaveV6(form) {
    const url = getCurrentUrlReturnUrlV6();
    const actionLookup = normalizeReturnUrlLookupV6(getFormActionReturnUrlV6(form));

    [
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
      url.searchParams.delete(paramName);
    });

    url.pathname = "/users/new";
    url.searchParams.set("appverbo_after_save", "1");

    if (actionLookup.includes("/users/profile/personal")) {
      const profileSection = getCurrentProfileSectionReturnUrlV6();

      url.searchParams.set("menu", "meu_perfil");
      url.searchParams.set("target", "#perfil-pessoal-card");
      url.searchParams.set("profile_tab", "pessoal");
      url.searchParams.delete("admin_tab");
      url.searchParams.delete("sidebar_sections_tab");
      url.hash = "#perfil-pessoal-card";

      if (profileSection) {
        url.searchParams.set("profile_section", profileSection);
      }

      return url.pathname + url.search + url.hash;
    }

    if (actionLookup.includes("/users/profile/address")) {
      url.searchParams.set("menu", "meu_perfil");
      url.searchParams.set("target", "#perfil-morada-card");
      url.searchParams.set("profile_tab", "morada");
      url.searchParams.delete("admin_tab");
      url.searchParams.delete("sidebar_sections_tab");
      url.hash = "#perfil-morada-card";
      return url.pathname + url.search + url.hash;
    }

    if (actionLookup.includes("/users/profile/training")) {
      url.searchParams.set("menu", "meu_perfil");
      url.searchParams.set("target", "#dados-treinamento-card");
      url.searchParams.set("profile_tab", "treinamento");
      url.searchParams.delete("admin_tab");
      url.searchParams.delete("sidebar_sections_tab");
      url.hash = "#dados-treinamento-card";
      return url.pathname + url.search + url.hash;
    }

    if (actionLookup.includes("/users/profile/whatsapp/verify")) {
      const profileSection = getCurrentProfileSectionReturnUrlV6();

      url.searchParams.set("menu", "meu_perfil");
      url.searchParams.set("target", "#perfil-pessoal-card");
      url.searchParams.set("profile_tab", "pessoal");
      url.searchParams.delete("admin_tab");
      url.searchParams.delete("sidebar_sections_tab");
      url.hash = "#perfil-pessoal-card";

      if (profileSection) {
        url.searchParams.set("profile_section", profileSection);
      }

      return url.pathname + url.search + url.hash;
    }

    if (actionLookup.includes("/users/profile/process-data")) {
      url.searchParams.set("target", "#dynamic-process-card");
      url.hash = "#dynamic-process-card";
    }

    const menuKey = getCurrentMenuReturnUrlV6(form);

    if (menuKey) {
      url.searchParams.set("menu", menuKey);
    }

    const settingsContext = getSettingsEditContextReturnUrlV6(form, menuKey);

    const target = getFormValueReturnUrlV6(form, ["target", "return_target"]);

    if (target) {
      url.searchParams.set("target", target);
    }

    const sectionKey = normalizeReturnUrlKeyV6(
      getFormValueReturnUrlV6(form, [
        "section_key",
        "dynamic_process_section",
        "process_section",
        "active_section",
        "settings_tab"
      ])
    );

    if (sectionKey) {
      url.searchParams.set("dynamic_process_section", sectionKey);
      url.searchParams.set("section_key", sectionKey);
    }

    if (settingsContext.settingsEditKey) {
      url.searchParams.set("settings_edit_key", settingsContext.settingsEditKey);
    }
    if (settingsContext.settingsAction) {
      url.searchParams.set("settings_action", settingsContext.settingsAction);
    }
    if (settingsContext.settingsTab) {
      url.searchParams.set("settings_tab", settingsContext.settingsTab);
    }

    if (actionLookup.includes("/entities/update")) {
      url.searchParams.set("menu", "administrativo");
      url.searchParams.set("admin_tab", "entidade");
      url.searchParams.set("target", "#create-entity-card");
      url.searchParams.delete("dynamic_process_section");
      url.searchParams.delete("section_key");
      url.hash = "#create-entity-card";
    } else if (actionLookup.includes("/users/update")) {
      url.searchParams.set("menu", "administrativo");
      url.searchParams.set("admin_tab", "utilizador");
      url.searchParams.set("target", "#create-user-card");
      url.searchParams.delete("dynamic_process_section");
      url.searchParams.delete("section_key");
      url.hash = "#create-user-card";
    } else if (actionLookup.includes("/users/new")) {
      url.searchParams.set("menu", "administrativo");
      url.searchParams.set("admin_tab", "utilizador");
      url.searchParams.set("target", "#create-user-card");
      url.searchParams.delete("dynamic_process_section");
      url.searchParams.delete("section_key");
      url.hash = "#create-user-card";
    } else if (
      actionLookup.includes("/settings/menu/sidebar-section-save") ||
      actionLookup.includes("/settings/menu/sidebar-section-move-one") ||
      actionLookup.includes("/settings/menu/sidebar-section-delete-one") ||
      actionLookup.includes("/settings/menu/sidebar-sections")
    ) {
      url.searchParams.set("menu", "administrativo");
      url.searchParams.set("admin_tab", "sessoes");
      url.searchParams.set("sidebar_sections_tab", "sessoes");
      url.searchParams.set("target", "#admin-sidebar-sections-card");
      url.searchParams.delete("dynamic_process_section");
      url.searchParams.delete("section_key");
      url.hash = "#admin-sidebar-sections-card";
    } else if (isProcessSettingsActionReturnUrlV6(actionLookup)) {
      url.searchParams.set("menu", "administrativo");
      url.searchParams.set("admin_tab", "menu");
      url.searchParams.set("target", "#settings-menu-edit-card");
      url.hash = "#settings-menu-edit-card";

      if (settingsContext.settingsEditKey) {
        url.searchParams.set("settings_edit_key", settingsContext.settingsEditKey);
      } else {
        const formMenuKey = normalizeReturnUrlKeyV6(
          getFormValueReturnUrlV6(form, ["menu_key"])
        );
        if (formMenuKey) {
          url.searchParams.set("settings_edit_key", formMenuKey);
          url.searchParams.set("settings_action", "edit");
        }
      }

      if (settingsContext.settingsTab) {
        url.searchParams.set("settings_tab", settingsContext.settingsTab);
      }
    } else if (actionLookup.includes("/settings/menu/save")) {
      url.searchParams.set("menu", "administrativo");
      url.searchParams.set("admin_tab", "menu");
      url.searchParams.set("target", "#admin-menu-card");
      url.searchParams.delete("dynamic_process_section");
      url.searchParams.delete("section_key");
      url.hash = "#admin-menu-card";
    } else if (
      actionLookup.includes("/settings/definicoes/save") ||
      actionLookup.includes("/settings/definicoes/delete")
    ) {
      url.searchParams.set("menu", "administrativo");
      url.searchParams.set("admin_tab", "definicoes");
      url.searchParams.set("target", "#admin-definicoes-card");
      url.searchParams.delete("dynamic_process_section");
      url.searchParams.delete("section_key");
      url.hash = "#admin-definicoes-card";
    }

    return url.pathname + url.search + url.hash;
  }

  function syncReturnUrlPostSaveV6(form) {
    if (!form) {
      return;
    }

    const method = getFormMethodReturnUrlV6(form);

    if (method && method !== "post") {
      return;
    }

    const returnUrl = buildReturnUrlPostSaveV6(form);

    ensureHiddenReturnUrlInputV6(form, "return_url").value = returnUrl;
    ensureHiddenReturnUrlInputV6(form, "appverbo_after_save").value = "1";
  }

  document.addEventListener("submit", function (event) {
    syncReturnUrlPostSaveV6(event.target);
  }, true);

  document.addEventListener("click", function (event) {
    const submitControl = event.target && event.target.closest
      ? event.target.closest("button[type='submit'], input[type='submit'], button:not([type])")
      : null;

    if (!submitControl || !submitControl.form) {
      return;
    }

    syncReturnUrlPostSaveV6(submitControl.form);
  }, true);

  document.addEventListener("formdata", function (event) {
    if (!event || !event.formData || !event.target) {
      return;
    }

    syncReturnUrlPostSaveV6(event.target);

    const returnUrlInput = event.target.querySelector("input[name='return_url']");
    const afterSaveInput = event.target.querySelector("input[name='appverbo_after_save']");

    if (returnUrlInput) {
      event.formData.set("return_url", returnUrlInput.value);
    }

    if (afterSaveInput) {
      event.formData.set("appverbo_after_save", afterSaveInput.value);
    }
  }, true);

  if (
    window.HTMLFormElement &&
    window.HTMLFormElement.prototype &&
    !window.HTMLFormElement.prototype.__appverboReturnUrlPostSavePatchedV6
  ) {
    const nativeSubmit = window.HTMLFormElement.prototype.submit;

    window.HTMLFormElement.prototype.submit = function patchedSubmitReturnUrlPostSaveV6() {
      syncReturnUrlPostSaveV6(this);
      return nativeSubmit.call(this);
    };

    window.HTMLFormElement.prototype.__appverboReturnUrlPostSavePatchedV6 = true;
  }
})();

// APPVERBO_FRONTEND_RETURN_URL_POST_SAVE_V6_END
  };
})();
// APPVERBO_FRONTEND_RETURN_URL_POST_SAVE_V6_MODULE_END
