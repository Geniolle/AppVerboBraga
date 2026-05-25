// APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_MODULE_START
(function registerReturnUrlPostSaveCaptureV4Module() {
  "use strict";

  function normalizeMenuKeyFallbackV4(value) {
    return String(value === null || value === undefined ? "" : value).trim().toLowerCase();
  }

  function normalizeLookupTextFallbackV4(value) {
    return String(value === null || value === undefined ? "" : value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  window.APPVERBO_SETUP_RETURN_URL_POST_SAVE_CAPTURE_V4 = function setupReturnUrlPostSaveCaptureV4(options) {
    const deps = options && typeof options === "object" ? options : {};

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
      : normalizeMenuKeyFallbackV4;
    const normalizeLookupText = typeof deps.normalizeLookupText === "function"
      ? deps.normalizeLookupText
      : normalizeLookupTextFallbackV4;

// APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_START
//###################################################################################
// (RETURN_URL_POST_SAVE_CAPTURE_V4) ENVIAR CONTEXTO ATUAL ANTES DO POST
//###################################################################################

(function setupReturnUrlPostSaveCaptureV4() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeReturnUrlTextV4(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeReturnUrlKeyV4(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeReturnUrlTextV4(value).trim().toLowerCase();
  }

  function normalizeReturnUrlLookupV4(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeReturnUrlTextV4(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function ensureHiddenReturnUrlInputV4(form, name) {
    let input = form.querySelector("input[name='" + name + "']");

    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }

    return input;
  }

  function getCurrentUrlReturnUrlV4() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return new URL("/users/new", window.location.origin);
    }
  }

  function getFormActionReturnUrlV4(form) {
    return safeReturnUrlTextV4(form && (form.getAttribute("action") || form.action));
  }

  function getFormMethodReturnUrlV4(form) {
    return safeReturnUrlTextV4(form && (form.getAttribute("method") || form.method || "post"))
      .trim()
      .toLowerCase();
  }

  function getFormValueReturnUrlV4(form, names) {
    if (!form) {
      return "";
    }

    for (const name of names) {
      const control = form.querySelector("[name='" + name + "']");

      if (!control) {
        continue;
      }

      const value = safeReturnUrlTextV4(control.value).trim();

      if (value) {
        return value;
      }
    }

    return "";
  }

  //###################################################################################
  // (2) DETECTAR ABA DO MEU PERFIL
  //###################################################################################

  function getProfileSectionFromInputReturnUrlV4() {
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
      const value = normalizeReturnUrlKeyV4(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getProfileSectionFromActiveTabReturnUrlV4() {
    const sections = Array.isArray(window.profilePersonalSections || profilePersonalSections)
      ? (window.profilePersonalSections || profilePersonalSections)
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

      const dataSection = normalizeReturnUrlKeyV4(
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      if (dataSection) {
        return dataSection;
      }

      const activeLabel = normalizeReturnUrlLookupV4(activeElement.textContent);

      if (!activeLabel) {
        continue;
      }

      for (const section of sections) {
        const sectionLabel = normalizeReturnUrlLookupV4(section && section.label);

        if (sectionLabel && sectionLabel === activeLabel) {
          return normalizeReturnUrlKeyV4(section && section.key);
        }
      }
    }

    return "";
  }

  function getProfileSectionFromVisiblePaneReturnUrlV4() {
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

      const sectionKey = normalizeReturnUrlKeyV4(pane.dataset.profileSectionPane);

      if (sectionKey) {
        return sectionKey;
      }
    }

    return "";
  }

  function getCurrentProfileSectionReturnUrlV4() {
    return (
      getProfileSectionFromInputReturnUrlV4() ||
      getProfileSectionFromActiveTabReturnUrlV4() ||
      getProfileSectionFromVisiblePaneReturnUrlV4()
    );
  }

  //###################################################################################
  // (3) DETECTAR PROCESSO DINAMICO
  //###################################################################################

  function getCurrentMenuReturnUrlV4(form) {
    const url = getCurrentUrlReturnUrlV4();

    const formMenu = normalizeReturnUrlKeyV4(
      getFormValueReturnUrlV4(form, [
        "menu",
        "menu_key",
        "process_menu_key",
        "dynamic_menu_key"
      ])
    );

    if (formMenu) {
      return formMenu;
    }

    const urlMenu = normalizeReturnUrlKeyV4(url.searchParams.get("menu"));

    if (urlMenu) {
      return urlMenu;
    }

    if (typeof initialMenu !== "undefined") {
      return normalizeReturnUrlKeyV4(initialMenu);
    }

    return "";
  }

  function getCurrentDynamicSectionReturnUrlV4(menuKey) {
    const formSection = normalizeReturnUrlKeyV4(
      getFormValueReturnUrlV4(document, [
        "dynamic_process_section",
        "section_key",
        "process_section",
        "active_section"
      ])
    );

    if (formSection) {
      return formSection;
    }

    if (
      typeof selectedDynamicSectionByMenu === "object" &&
      selectedDynamicSectionByMenu !== null &&
      menuKey &&
      selectedDynamicSectionByMenu[menuKey]
    ) {
      return normalizeReturnUrlKeyV4(selectedDynamicSectionByMenu[menuKey]);
    }

    const activeElement = document.querySelector(
      "#dynamic-process-card .active, " +
      "#dynamic-process-card [aria-selected='true'], " +
      "[data-dynamic-process-section-key].active, " +
      "[data-dynamic-process-section-key][aria-selected='true']"
    );

    if (activeElement) {
      return normalizeReturnUrlKeyV4(
        activeElement.dataset.dynamicProcessSectionKey ||
        activeElement.dataset.sectionKey ||
        ""
      );
    }

    return "";
  }

  //###################################################################################
  // (4) CONSTRUIR return_url
  //###################################################################################

  function buildReturnUrlPostSaveV4(form) {
    const url = getCurrentUrlReturnUrlV4();
    const action = getFormActionReturnUrlV4(form);
    const actionLookup = normalizeReturnUrlLookupV4(action);

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
      url.searchParams.delete(paramName);
    });

    url.pathname = "/users/new";

    if (actionLookup.includes("/users/profile/personal")) {
      const profileSection = getCurrentProfileSectionReturnUrlV4();

      url.searchParams.set("menu", "meu_perfil");
      url.searchParams.set("target", "#perfil-pessoal-card");
      url.searchParams.set("profile_tab", "pessoal");

      if (profileSection) {
        url.searchParams.set("profile_section", profileSection);
      }
    } else {
      const menuKey = getCurrentMenuReturnUrlV4(form);

      if (menuKey) {
        url.searchParams.set("menu", menuKey);
      }

      const target = getFormValueReturnUrlV4(form, ["target", "return_target"]);

      if (target) {
        url.searchParams.set("target", target);
      }

      const dynamicSection = getCurrentDynamicSectionReturnUrlV4(menuKey);

      if (dynamicSection) {
        url.searchParams.set("dynamic_process_section", dynamicSection);
      }
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

    url.searchParams.set("appverbo_after_save", "1");

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (5) SINCRONIZAR NO FORMULARIO
  //###################################################################################

  function syncReturnUrlPostSaveV4(form) {
    if (!form) {
      return;
    }

    const method = getFormMethodReturnUrlV4(form);

    if (method && method !== "post") {
      return;
    }

    const returnUrl = buildReturnUrlPostSaveV4(form);

    ensureHiddenReturnUrlInputV4(form, "return_url").value = returnUrl;
    ensureHiddenReturnUrlInputV4(form, "appverbo_after_save").value = "1";

    try {
      window.sessionStorage.setItem(
        "appverbo:return-url-post-save-v4",
        JSON.stringify({
          url: returnUrl,
          createdAt: Date.now()
        })
      );
    } catch (error) {
      // Ignora sessionStorage indisponivel.
    }
  }

  document.addEventListener("submit", function (event) {
    syncReturnUrlPostSaveV4(event.target);
  }, true);

  document.addEventListener("click", function (event) {
    const submitControl = event.target && event.target.closest
      ? event.target.closest("button[type='submit'], input[type='submit'], button:not([type])")
      : null;

    if (!submitControl || !submitControl.form) {
      return;
    }

    syncReturnUrlPostSaveV4(submitControl.form);
  }, true);

  document.addEventListener("formdata", function (event) {
    if (!event || !event.formData || !event.target) {
      return;
    }

    syncReturnUrlPostSaveV4(event.target);

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
    !window.HTMLFormElement.prototype.__appverboReturnUrlPostSavePatchedV4
  ) {
    const nativeSubmit = window.HTMLFormElement.prototype.submit;

    window.HTMLFormElement.prototype.submit = function patchedSubmitReturnUrlPostSaveV4() {
      syncReturnUrlPostSaveV4(this);
      return nativeSubmit.call(this);
    };

    window.HTMLFormElement.prototype.__appverboReturnUrlPostSavePatchedV4 = true;
  }
})();

// APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_END
  };
})();
// APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_MODULE_END
