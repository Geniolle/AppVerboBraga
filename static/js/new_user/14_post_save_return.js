// new_user/14_post_save_return.js: Contexto e URL de retorno apos guardar.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

// APPGENESIS_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_END

// APPGENESIS_POST_SAVE_CONTEXT_CAPTURE_V3_START
//###################################################################################
// (POST_SAVE_CONTEXT_CAPTURE_V3) GUARDAR PROCESSO/ABA ANTES DE QUALQUER POST
//###################################################################################

(function setupAppGenesisPostSaveContextCaptureV3() {
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

  function resolveAuthoritativeActiveMenuKeyForPostSaveV1() {
    // Sinal autoritativo do menu de topo realmente ativo na SPA (exposto por new_user.js em
    // window.__appgenesisGetActiveMenuKeyV1, ver ativacao de menu). Navegacao por clique para
    // qualquer menu que nao seja "administrativo" nao atualiza a URL (nao faz pushState), entao
    // window.location.href/bootstrap ficam desatualizados assim que o utilizador navega por
    // clique -- usar esse sinal evita que um submit feito depois de navegar por clique (ex.:
    // Estruturas > Menu) seja guardado com o menu errado (ex.: "home") e redirecionado para o
    // lugar errado apos o backend processar o POST.
    if (typeof window.__appgenesisGetActiveMenuKeyV1 !== "function") {
      return "";
    }

    try {
      return normalizePostSaveKeyV3(window.__appgenesisGetActiveMenuKeyV1());
    } catch (error) {
      return "";
    }
  }

  function currentMenuFromUrlOrBootstrapPostSaveV3(form) {
    const currentUrl = getCurrentUrlPostSaveV3();

    // Um campo "menu" explicito no formulario e uma sobreposicao deliberada e tem prioridade
    // sobre tudo o resto.
    const explicitFormMenu = normalizePostSaveKeyV3(
      readFirstFormValuePostSaveV3(form, ["menu"])
    );

    if (explicitFormMenu) {
      logAppGenesisProcessEditorDebugV1("currentMenuFromUrlOrBootstrapPostSaveV3:resolved", {
        source: "explicit_form_menu_field",
        value: explicitFormMenu
      });
      return explicitFormMenu;
    }

    const authoritativeActiveMenu = resolveAuthoritativeActiveMenuKeyForPostSaveV1();

    if (authoritativeActiveMenu) {
      logAppGenesisProcessEditorDebugV1("currentMenuFromUrlOrBootstrapPostSaveV3:resolved", {
        source: "authoritative_active_menu_key",
        value: authoritativeActiveMenu
      });
      return authoritativeActiveMenu;
    }

    // O "menu" ja presente na URL atual reflete o contexto de navegacao onde o formulario foi
    // aberto (ex.: o editor de processo dentro de "administrativo"/"sessoes") e tem prioridade
    // sobre "redirect_menu"/"menu_key" do formulario. "redirect_menu" costuma ser um valor fixo
    // definido no template e "menu_key" identifica o item a editar (ex.: "calendario"), nao o
    // menu de navegacao em si — usa-los antes da URL fazia o guardar "saltar" para um contexto
    // diferente daquele onde o utilizador estava.
    const urlMenu = normalizePostSaveKeyV3(currentUrl.searchParams.get("menu"));

    if (urlMenu) {
      logAppGenesisProcessEditorDebugV1("currentMenuFromUrlOrBootstrapPostSaveV3:resolved", {
        source: "current_url_menu",
        value: urlMenu
      });
      return urlMenu;
    }

    const fallbackFormMenu = normalizePostSaveKeyV3(
      readFirstFormValuePostSaveV3(form, [
        "redirect_menu",
        "menu_key",
        "process_menu_key",
        "dynamic_menu_key",
        "settings_edit_key"
      ])
    );

    if (fallbackFormMenu) {
      logAppGenesisProcessEditorDebugV1("currentMenuFromUrlOrBootstrapPostSaveV3:resolved", {
        source: "fallback_form_menu_field",
        value: fallbackFormMenu
      });
      return fallbackFormMenu;
    }

    if (typeof initialMenu !== "undefined") {
      const bootstrapMenu = normalizePostSaveKeyV3(initialMenu);

      if (bootstrapMenu) {
        logAppGenesisProcessEditorDebugV1("currentMenuFromUrlOrBootstrapPostSaveV3:resolved", {
          source: "bootstrap_initial_menu",
          value: bootstrapMenu
        });
        return bootstrapMenu;
      }
    }

    logAppGenesisProcessEditorDebugV1("currentMenuFromUrlOrBootstrapPostSaveV3:resolved", {
      source: "none",
      value: ""
    });
    return "";
  }

  //###################################################################################
  // (2) CONSTRUIR URL DE RETORNO
  //###################################################################################

  function findConfigProvidedReturnUrlV1(form) {
    // Subprocessos administrativos (menu, sessoes, perfil de autorizacao, objeto de autorizacao)
    // injetam a sua propria URL de retorno, calculada e validada pelo backend, num campo hidden
    // cujo nome termina em "_return_url" (ex.: "subprocess_return_url", "sidebar_section_return_url",
    // "auth_profile_return_url" -- ver return_url_field em appgenesis/admin_subprocesses/registry.py).
    // Essa e a fonte mais confiavel de "para onde voltar apos o POST": ao contrario da
    // reconstrucao generica abaixo (baseada em URL/bootstrap, que fica desatualizada em
    // navegacao client-side sem pushState), o backend ja sabe exatamente o menu/aba/target
    // corretos porque foi ele quem renderizou o card. Usar essa URL evita redirecionar o
    // utilizador para o lugar errado apos guardar/mover/apagar um item nesses subprocessos.
    if (!form || typeof form.querySelectorAll !== "function") {
      return "";
    }

    const candidates = Array.from(form.querySelectorAll("input[type='hidden']")).filter((input) => {
      const name = String(input.name || "");
      return name.length > "_return_url".length && name.endsWith("_return_url");
    });

    for (let i = 0; i < candidates.length; i += 1) {
      const value = String(candidates[i].value || "").trim();

      if (value) {
        return value;
      }
    }

    return "";
  }

  function buildPostSaveReturnUrlV3(form) {
    const configProvidedReturnUrl = findConfigProvidedReturnUrlV1(form);

    if (configProvidedReturnUrl) {
      let configReturnUrlObj = null;

      try {
        configReturnUrlObj = new URL(configProvidedReturnUrl, window.location.origin);
      } catch (error) {
        configReturnUrlObj = null;
      }

      if (configReturnUrlObj && configReturnUrlObj.pathname === "/users/new") {
        configReturnUrlObj.searchParams.set("appgenesis_after_save", "1");

        logAppGenesisProcessEditorDebugV1("buildPostSaveReturnUrlV3:resolved", {
          source: "config_provided_return_url_field",
          value: configReturnUrlObj.pathname + configReturnUrlObj.search + configReturnUrlObj.hash
        });

        return configReturnUrlObj.pathname + configReturnUrlObj.search + configReturnUrlObj.hash;
      }
    }

    const currentUrl = getCurrentUrlPostSaveV3();

    currentUrl.pathname = "/users/new";

    const action = getFormActionPostSaveV3(form);
    const actionLookup = normalizePostSaveLookupV3(action);
    const isEntityUpdateAction = actionLookup.includes("/entities/update");
    let menuKey = currentMenuFromUrlOrBootstrapPostSaveV3(form);

    if (actionLookup.includes("/users/profile/personal")) {
      menuKey = MEU_PERFIL_MENU_KEY;
      currentUrl.searchParams.set("menu", MEU_PERFIL_MENU_KEY);
      currentUrl.searchParams.set("target", "#perfil-pessoal-card");
      currentUrl.searchParams.set("profile_tab", "pessoal");

      const profileSection = getCurrentProfileSectionPostSaveV3();

      if (profileSection) {
        currentUrl.searchParams.set("profile_section", profileSection);
      }
    } else {
      if (isEntityUpdateAction) {
        currentUrl.searchParams.set("menu", "administrativo");
        currentUrl.searchParams.set("admin_tab", "entidade");
        currentUrl.searchParams.set("target", "#recent-entities-card");
        currentUrl.searchParams.delete("entity_edit_id");
        currentUrl.searchParams.delete("entity_view");
        currentUrl.searchParams.delete("user_edit_id");
        currentUrl.searchParams.delete("user_view");
        currentUrl.searchParams.delete("settings_edit_key");
        currentUrl.searchParams.delete("settings_action");
        currentUrl.searchParams.delete("settings_tab");
        currentUrl.searchParams.delete("profile_tab");
        currentUrl.searchParams.delete("profile_section");
        currentUrl.searchParams.delete("dynamic_process_section");
        currentUrl.searchParams.delete("section_key");
        currentUrl.searchParams.delete("sidebar_section_edit_key");
        currentUrl.hash = "#recent-entities-card";
      } else {
        if (menuKey) {
          currentUrl.searchParams.set("menu", menuKey);
        }

        const formTarget = readFirstFormValuePostSaveV3(form, ["target", "return_target"]);

        if (formTarget) {
          currentUrl.searchParams.set("target", formTarget);
        }

        const formAdminTab = normalizePostSaveKeyV3(
          readFirstFormValuePostSaveV3(form, [
            "return_admin_tab",
            "admin_tab",
            "active_admin_tab"
          ])
        );

        if (formAdminTab) {
          currentUrl.searchParams.set("admin_tab", formAdminTab);
        }

        if (
          currentUrl.searchParams.get("menu") === "administrativo" &&
          !currentUrl.searchParams.get("admin_tab") &&
          (
            actionLookup.includes("/users/delete") ||
            actionLookup.includes("/users/update") ||
            actionLookup.includes("/users/new") ||
            actionLookup.includes("/users/resend")
          )
        ) {
          currentUrl.searchParams.set("admin_tab", "utilizador");
        }

        if (
          currentUrl.searchParams.get("menu") === "administrativo" &&
          !currentUrl.searchParams.get("admin_tab") &&
          actionLookup.includes("/entities/")
        ) {
          currentUrl.searchParams.set("admin_tab", "entidade");
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
        const currentMenuKey = normalizePostSaveKeyV3(currentUrl.searchParams.get("menu"));

        if (
          settingsEditKey &&
          (currentMenuKey === "administrativo" || currentMenuKey === ESTRUTURAS_MENU_KEY_V1)
        ) {
          currentUrl.searchParams.set("settings_edit_key", settingsEditKey);
          currentUrl.searchParams.set("settings_action", settingsAction || "edit");

          if (settingsTab) {
            currentUrl.searchParams.set("settings_tab", settingsTab);
          }

          if (
            currentMenuKey === ESTRUTURAS_MENU_KEY_V1 &&
            !currentUrl.searchParams.get("admin_tab")
          ) {
            currentUrl.searchParams.set("admin_tab", "contas");
          }

          if (!currentUrl.searchParams.get("target")) {
            currentUrl.searchParams.set("target", "#settings-menu-edit-card");
          }
        }

        if (
          settingsEditKey &&
          (currentMenuKey === "administrativo" || currentMenuKey === ESTRUTURAS_MENU_KEY_V1)
        ) {
          currentUrl.searchParams.delete("dynamic_process_section");
          currentUrl.searchParams.delete("section_key");
        } else {
          const dynamicSection = getDynamicSectionPostSaveV3(menuKey);

          if (dynamicSection) {
            currentUrl.searchParams.set("dynamic_process_section", dynamicSection);
          }
        }
      }
    }

    currentUrl.searchParams.set("appgenesis_after_save", "1");

    return currentUrl.pathname + currentUrl.search + currentUrl.hash;
  }

  //###################################################################################
  // (3) GUARDAR CONTEXTO
  //###################################################################################

  function debugRelevantFormFieldsV1(form) {
    const fieldNames = [
      "menu_key",
      "redirect_menu",
      "redirect_target",
      "settings_edit_key",
      "settings_action",
      "settings_tab",
      "target",
      "dynamic_process_section"
    ];
    const values = {};
    fieldNames.forEach((name) => {
      const control = form && typeof form.querySelector === "function"
        ? form.querySelector("[name='" + name + "']")
        : null;
      values[name] = control ? control.value : undefined;
    });
    return values;
  }

  function storePostSaveContextV3(form) {
    if (!form) {
      return;
    }

    const method = getFormMethodPostSaveV3(form);

    if (method && method !== "post") {
      return;
    }

    logAppGenesisProcessEditorDebugV1("storePostSaveContextV3:submit", {
      formAction: form.getAttribute("action") || form.action,
      formMethod: method,
      locationHrefBeforeSubmit: window.location.href,
      hiddenInputs: debugRelevantFormFieldsV1(form)
    });

    const returnUrl = buildPostSaveReturnUrlV3(form);

    logAppGenesisProcessEditorDebugV1("storePostSaveContextV3:computed_return_url", {
      returnUrl
    });

    try {
      window.sessionStorage.setItem(
        APPGENESIS_POST_SAVE_CONTEXT_KEY_V3,
        JSON.stringify({
          url: returnUrl,
          createdAt: Date.now()
        })
      );
    } catch (error) {
      // Ignora falhas de sessionStorage.
    }

    ensureHiddenPostSaveInputV3(form, "appgenesis_after_save").value = "1";
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
      !window.HTMLFormElement.prototype.__appgenesisPostSaveContextPatchedV3
    ) {
      const nativeSubmit = window.HTMLFormElement.prototype.submit;

      window.HTMLFormElement.prototype.submit = function patchedSubmitPostSaveContextV3() {
        storePostSaveContextV3(this);
        return nativeSubmit.call(this);
      };

      window.HTMLFormElement.prototype.__appgenesisPostSaveContextPatchedV3 = true;
    }
  }

  bindPostSaveContextCaptureV3();
})();

// APPGENESIS_POST_SAVE_CONTEXT_CAPTURE_V3_END

// APPGENESIS_RETURN_URL_POST_SAVE_CAPTURE_V4_START
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

    // Sinal autoritativo do menu de topo realmente ativo na SPA (ver mesmo padrao em
    // resolveAuthoritativeActiveMenuKeyForPostSaveV1, noutro escopo de IIFE deste ficheiro):
    // navegacao por clique para menus que nao sejam "administrativo" nao atualiza a URL, entao
    // "urlMenu" abaixo fica desatualizado assim que o utilizador navega por clique.
    if (typeof window.__appgenesisGetActiveMenuKeyV1 === "function") {
      try {
        const authoritativeActiveMenu = normalizeReturnUrlKeyV4(window.__appgenesisGetActiveMenuKeyV1());
        if (authoritativeActiveMenu) {
          return authoritativeActiveMenu;
        }
      } catch (error) {
        // Ignora falha e cai no fallback pelo URL/bootstrap.
      }
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
    const isEntityUpdateAction = actionLookup.includes("/entities/update");

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
      if (isEntityUpdateAction) {
        url.searchParams.set("menu", "administrativo");
        url.searchParams.set("admin_tab", "entidade");
        url.searchParams.set("target", "#recent-entities-card");
        url.searchParams.delete("entity_edit_id");
        url.searchParams.delete("entity_view");
        url.searchParams.delete("user_edit_id");
        url.searchParams.delete("user_view");
        url.searchParams.delete("settings_edit_key");
        url.searchParams.delete("settings_action");
        url.searchParams.delete("settings_tab");
        url.searchParams.delete("profile_tab");
        url.searchParams.delete("profile_section");
        url.searchParams.delete("dynamic_process_section");
        url.searchParams.delete("section_key");
        url.searchParams.delete("sidebar_section_edit_key");
        url.hash = "#recent-entities-card";
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
    }

    url.searchParams.set("appgenesis_after_save", "1");

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
    ensureHiddenReturnUrlInputV4(form, "appgenesis_after_save").value = "1";

    try {
      window.sessionStorage.setItem(
        "appgenesis:return-url-post-save-v4",
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
    const afterSaveInput = event.target.querySelector("input[name='appgenesis_after_save']");

    if (returnUrlInput) {
      event.formData.set("return_url", returnUrlInput.value);
    }

    if (afterSaveInput) {
      event.formData.set("appgenesis_after_save", afterSaveInput.value);
    }
  }, true);

  if (
    window.HTMLFormElement &&
    window.HTMLFormElement.prototype &&
    !window.HTMLFormElement.prototype.__appgenesisReturnUrlPostSavePatchedV4
  ) {
    const nativeSubmit = window.HTMLFormElement.prototype.submit;

    window.HTMLFormElement.prototype.submit = function patchedSubmitReturnUrlPostSaveV4() {
      syncReturnUrlPostSaveV4(this);
      return nativeSubmit.call(this);
    };

    window.HTMLFormElement.prototype.__appgenesisReturnUrlPostSavePatchedV4 = true;
  }
})();

// APPGENESIS_RETURN_URL_POST_SAVE_CAPTURE_V4_END

// APPGENESIS_FRONTEND_RETURN_URL_POST_SAVE_V6_START
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

  function buildReturnUrlPostSaveV6(form) {
    const url = getCurrentUrlReturnUrlV6();
    const actionLookup = normalizeReturnUrlLookupV6(getFormActionReturnUrlV6(form));
    const isEntityUpdateAction = actionLookup.includes("/entities/update");

    url.pathname = "/users/new";
    url.searchParams.set("appgenesis_after_save", "1");

    if (actionLookup.includes("/users/profile/personal")) {
      // URL limpa: sem parametros do editor de processo (admin_tab, settings_*), senao o retorno cai no editor.
      const profileSection = getCurrentProfileSectionReturnUrlV6();
      const profileUrl = new URL("/users/new", window.location.origin);

      profileUrl.searchParams.set("appgenesis_after_save", "1");
      profileUrl.searchParams.set("menu", "meu_perfil");
      profileUrl.searchParams.set("target", "#perfil-pessoal-card");
      profileUrl.searchParams.set("profile_tab", "pessoal");

      if (profileSection) {
        profileUrl.searchParams.set("profile_section", profileSection);
      }

      return profileUrl.pathname + profileUrl.search + "#perfil-pessoal-card";
    }

    if (isEntityUpdateAction) {
      url.searchParams.set("menu", "administrativo");
      url.searchParams.set("admin_tab", "entidade");
      url.searchParams.set("target", "#recent-entities-card");
      url.searchParams.delete("entity_edit_id");
      url.searchParams.delete("entity_view");
      url.searchParams.delete("user_edit_id");
      url.searchParams.delete("user_view");
      url.searchParams.delete("settings_edit_key");
      url.searchParams.delete("settings_action");
      url.searchParams.delete("settings_tab");
      url.searchParams.delete("profile_tab");
      url.searchParams.delete("profile_section");
      url.searchParams.delete("dynamic_process_section");
      url.searchParams.delete("section_key");
      url.searchParams.delete("sidebar_section_edit_key");
      url.hash = "#recent-entities-card";

      return url.pathname + url.search + url.hash;
    }

    const menuKey = getCurrentMenuReturnUrlV6(form);

    if (menuKey) {
      url.searchParams.set("menu", menuKey);
    }

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
    ensureHiddenReturnUrlInputV6(form, "appgenesis_after_save").value = "1";
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
    const afterSaveInput = event.target.querySelector("input[name='appgenesis_after_save']");

    if (returnUrlInput) {
      event.formData.set("return_url", returnUrlInput.value);
    }

    if (afterSaveInput) {
      event.formData.set("appgenesis_after_save", afterSaveInput.value);
    }
  }, true);

  if (
    window.HTMLFormElement &&
    window.HTMLFormElement.prototype &&
    !window.HTMLFormElement.prototype.__appgenesisReturnUrlPostSavePatchedV6
  ) {
    const nativeSubmit = window.HTMLFormElement.prototype.submit;

    window.HTMLFormElement.prototype.submit = function patchedSubmitReturnUrlPostSaveV6() {
      syncReturnUrlPostSaveV6(this);
      return nativeSubmit.call(this);
    };

    window.HTMLFormElement.prototype.__appgenesisReturnUrlPostSavePatchedV6 = true;
  }
})();
