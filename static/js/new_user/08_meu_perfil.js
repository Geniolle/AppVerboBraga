// new_user/08_meu_perfil.js: Meu Perfil: abas, valores, visibilidade e regras.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

function normalizeProfileMultiValueList(rawValue) {
  return String(rawValue || "")
    .split(/\r?\n|,/)
    .map((item) => String(item || "").trim())
    .filter(Boolean);
}

function isAllocationProfileSection(sectionKey) {
  const cleanSection = normalizeLookupText(sectionKey);
  if (!cleanSection) {
    return false;
  }
  return cleanSection.includes("alocacao");
}

function setProfileControlValue(controlEl, value) {
  if (!controlEl) {
    return;
  }
  const cleanValue = String(value || "").trim();
  if (controlEl.tagName === "SELECT") {
    const options = Array.from(controlEl.options || []);
    const hasExactValue = options.some((option) => String(option.value || "") === cleanValue);
    if (hasExactValue) {
      controlEl.value = cleanValue;
      return;
    }
    const matchingOption = options.find(
      (option) => String(option.textContent || "").trim().toLowerCase() === cleanValue.toLowerCase()
    );
    controlEl.value = matchingOption ? String(matchingOption.value || "") : "";
    return;
  }
  controlEl.value = cleanValue;
}

function setupAllocationFieldMultiValue(fieldEl) {
  if (!fieldEl || fieldEl.getAttribute("data-allocation-multi-ready") === "1") {
    return;
  }
  const baseControlEl = fieldEl.querySelector(
    "input[name^='custom_field__']:not([type='checkbox']):not([type='hidden']), select[name^='custom_field__'], textarea[name^='custom_field__']"
  );
  if (!baseControlEl) {
    return;
  }
  const baseFieldName = String(baseControlEl.getAttribute("name") || "").trim();
  if (!baseFieldName) {
    return;
  }

  const baseLabelEl = fieldEl.querySelector("label");
  if (baseLabelEl && !baseLabelEl.classList.contains("profile-multi-value-label")) {
    baseLabelEl.classList.add("profile-multi-value-label");
  }

  const valuesListEl = document.createElement("div");
  valuesListEl.className = "profile-multi-value-list";

  const addButtonEl = document.createElement("button");
  addButtonEl.type = "button";
  addButtonEl.className = "table-icon-btn profile-multi-value-add-btn";
  addButtonEl.title = "Adicionar linha";
  addButtonEl.setAttribute("aria-label", "Adicionar linha");
  addButtonEl.innerHTML = "&#43;";
  if (baseLabelEl) {
    baseLabelEl.appendChild(addButtonEl);
  } else {
    fieldEl.appendChild(addButtonEl);
  }

  function createControlRow(controlEl, isRemovable) {
    const rowEl = document.createElement("div");
    rowEl.className = "profile-multi-value-row";
    rowEl.appendChild(controlEl);
    if (isRemovable) {
      const removeButtonEl = document.createElement("button");
      removeButtonEl.type = "button";
      removeButtonEl.className = "table-icon-btn table-icon-btn-danger profile-multi-value-remove-btn";
      removeButtonEl.title = "Remover linha";
      removeButtonEl.setAttribute("aria-label", "Remover linha");
      removeButtonEl.innerHTML = "&#10005;";
      removeButtonEl.addEventListener("click", () => {
        rowEl.remove();
      });
      rowEl.appendChild(removeButtonEl);
    }
    valuesListEl.appendChild(rowEl);
    return rowEl;
  }

  function createExtraControl(initialValue = "") {
    const clonedControlEl = baseControlEl.cloneNode(true);
    clonedControlEl.removeAttribute("id");
    clonedControlEl.name = baseFieldName;
    clonedControlEl.required = false;
    setProfileControlValue(clonedControlEl, initialValue);
    if (clonedControlEl.tagName !== "SELECT") {
      clonedControlEl.defaultValue = clonedControlEl.value;
    }
    return clonedControlEl;
  }

  const initialValues = normalizeProfileMultiValueList(baseControlEl.value);
  if (initialValues.length) {
    setProfileControlValue(baseControlEl, initialValues[0]);
  }
  baseControlEl.name = baseFieldName;

  fieldEl.insertBefore(valuesListEl, baseControlEl);
  createControlRow(baseControlEl, false);

  const extraValues = initialValues.slice(1);
  extraValues.forEach((value) => {
    createControlRow(createExtraControl(value), true);
  });

  addButtonEl.addEventListener("click", () => {
    const rowEl = createControlRow(createExtraControl(""), true);
    const inputEl = rowEl.querySelector("input, select, textarea");
    if (inputEl) {
      inputEl.focus();
    }
  });

  fieldEl.setAttribute("data-allocation-multi-ready", "1");
}

function setupAllocationSectionMultiValue(personalCardEl, sectionKey) {
  if (!personalCardEl || !isAllocationProfileSection(sectionKey)) {
    return;
  }
  const formEl = personalCardEl.querySelector(".profile-edit-form");
  if (!formEl) {
    return;
  }
  const cleanSection = String(sectionKey || "").trim().toLowerCase();
  const sectionFields = Array.from(formEl.querySelectorAll(".field[data-profile-section-pane]")).filter(
    (fieldEl) =>
      String(fieldEl.getAttribute("data-profile-section-pane") || "geral").trim().toLowerCase() === cleanSection
  );
  sectionFields.forEach((fieldEl) => {
    setupAllocationFieldMultiValue(fieldEl);
  });
}

function setupProfileProcessTabs() {
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  if (!personalCardEl) {
    return;
  }
  const sectionPanes = personalCardEl.querySelectorAll("[data-profile-section-pane]");
  if (!sectionPanes.length) {
    return;
  }

  function activateSection(sectionKey) {
    const normalizedSection = String(sectionKey || "").trim().toLowerCase() || "geral";
    const availableSections = new Set(
      Array.from(sectionPanes)
        .map((paneEl) =>
          String(paneEl.getAttribute("data-profile-section-pane") || "geral").trim().toLowerCase()
        )
        .filter((section) => !hiddenMeuPerfilSectionKeys.has(section))
    );
    const effectiveSection = availableSections.has(normalizedSection)
      ? normalizedSection
      : (Array.from(availableSections)[0] || "geral");

    sectionPanes.forEach((paneEl) => {
      const paneSection = String(
        paneEl.getAttribute("data-profile-section-pane") || "geral"
      ).trim().toLowerCase();
      paneEl.style.display = !hiddenMeuPerfilSectionKeys.has(paneSection) && paneSection === effectiveSection ? "" : "none";
    });
    const sectionInputEl = personalCardEl.querySelector("[data-meu-perfil-section-input]");
    if (sectionInputEl) {
      sectionInputEl.value = effectiveSection;
    }
    setupAllocationSectionMultiValue(personalCardEl, effectiveSection);
    meuPerfilSelectedProfileSection = effectiveSection;
  }

  window.activateProfilePersonalSection = activateSection;
  activateSection(meuPerfilSelectedProfileSection);
}

function collectCurrentMeuPerfilProcessValues() {
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  const valuesByField = {};
  if (!formEl) {
    return valuesByField;
  }

  const fixedFieldMap = {
    full_name: "nome",
    primary_phone: "telefone",
    login_email: "email",
    country: "pais",
    birth_date: "data_nascimento",
    whatsapp_notice_opt_in: "autorizacao_whatsapp"
  };

  formEl.querySelectorAll("[name]").forEach((controlEl) => {
    const rawName = String(controlEl.getAttribute("name") || "").trim();
    let fieldKey = "";
    if (rawName.startsWith("custom_field__")) {
      fieldKey = normalizeMenuKey(rawName.replace(/^custom_field__/, ""));
    } else {
      fieldKey = normalizeMenuKey(fixedFieldMap[rawName] || "");
    }
    if (!fieldKey) {
      return;
    }
    if (controlEl.type === "checkbox") {
      valuesByField[fieldKey] = controlEl.checked ? "1" : "0";
      return;
    }
    valuesByField[fieldKey] = String(controlEl.value || "").trim();
  });

  return valuesByField;
}

// So escreve quando o estado difere (evita ciclo com o MutationObserver).
function enforceMeuPerfilHiddenSectionLinksV1() {
  document.querySelectorAll(".submenu-item[data-profile-section]").forEach((linkEl) => {
    const sectionKey = normalizeMenuKey(linkEl.dataset.profileSection);
    const shouldHide = hiddenMeuPerfilSectionKeys.has(sectionKey);
    if (shouldHide) {
      // Confirma o estilo real: outro gestor pode limpar display entre redesenhos.
      if (linkEl.style.getPropertyValue("display") !== "none") {
        linkEl.style.setProperty("display", "none", "important");
      }
      linkEl.dataset.meuPerfilHidden = "1";
    } else if (linkEl.dataset.meuPerfilHidden === "1") {
      linkEl.style.removeProperty("display");
      delete linkEl.dataset.meuPerfilHidden;
    }
  });
}

function applyMeuPerfilProcessSubsequentVisibility() {
  const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  if (!setting || !personalCardEl) {
    return;
  }

  hiddenMeuPerfilSectionKeys = getHiddenProcessTargets(
    setting.process_subsequent_fields,
    collectCurrentMeuPerfilProcessValues()
  );

  if (itemsEl) {
    const submenuLinks = itemsEl.querySelectorAll(".submenu-item[data-profile-section]");
    submenuLinks.forEach((linkEl) => {
      const sectionKey = normalizeMenuKey(linkEl.dataset.profileSection);
      // !important: o gestor de abas com overflow (tabs_overflow_v1.js) limpa style.display ao recalcular.
      if (hiddenMeuPerfilSectionKeys.has(sectionKey)) {
        linkEl.style.setProperty("display", "none", "important");
      } else {
        linkEl.style.removeProperty("display");
      }
    });
  }

  if (typeof window.activateProfilePersonalSection === "function") {
    window.activateProfilePersonalSection(meuPerfilSelectedProfileSection);
  }
  if (itemsEl) {
    const selectedLinkEl = itemsEl.querySelector(
      `.submenu-item[data-profile-section="${String(meuPerfilSelectedProfileSection || "").replace(/"/g, '\\"')}"]`
    );
    if (selectedLinkEl && selectedLinkEl.style.display !== "none") {
      setActiveSubmenu("#perfil-pessoal-card", {
        profileSection: String(meuPerfilSelectedProfileSection || "")
      });
      return;
    }
    const firstVisibleLinkEl = Array.from(itemsEl.querySelectorAll(".submenu-item[data-profile-section]")).find(
      (linkEl) => linkEl.style.display !== "none"
    );
    if (firstVisibleLinkEl) {
      meuPerfilSelectedProfileSection = String(firstVisibleLinkEl.dataset.profileSection || "");
      setActiveSubmenu("#perfil-pessoal-card", {
        profileSection: String(meuPerfilSelectedProfileSection || "")
      });
    }
  }
  renderMeuPerfilQuantityGroups();
}

// Campos obrigatorios em abas ocultas bloqueiam a validacao do navegador sem mensagem visivel.
// Antes de validar o submit, suspende 'required' nos controlos ocultos e repoe nos visiveis.
function syncMeuPerfilHiddenRequiredFields() {
  const formEl = document.querySelector("#perfil-pessoal-card .profile-edit-form");
  if (!formEl) {
    return;
  }
  formEl.querySelectorAll("input, select, textarea").forEach((controlEl) => {
    if (controlEl.type === "hidden" || controlEl.disabled) {
      return;
    }
    const isHidden = controlEl.offsetParent === null;
    if (isHidden && controlEl.required) {
      controlEl.required = false;
      controlEl.dataset.meuPerfilRequiredOff = "1";
    } else if (!isHidden && controlEl.dataset.meuPerfilRequiredOff === "1") {
      controlEl.required = true;
      delete controlEl.dataset.meuPerfilRequiredOff;
    }
  });
}

function setupMeuPerfilQuantityRules() {
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
  if (!formEl || !setting) {
    return;
  }

  const normalizedRules = normalizeProcessQuantityRules(setting.process_quantity_fields);
  if (!normalizedRules.length) {
    syncMeuPerfilQuantityHiddenInputs({});
    return;
  }

  const quantityFieldKeys = new Set(
    normalizedRules
      .map((rule) => normalizeMenuKey(rule.quantityFieldKey))
      .filter(Boolean)
  );

  formEl.querySelectorAll("[name]").forEach((controlEl) => {
    const rawName = String(controlEl.getAttribute("name") || "").trim();
    let fieldKey = "";
    if (rawName.startsWith("custom_field__")) {
      fieldKey = normalizeMenuKey(rawName.replace(/^custom_field__/, ""));
    } else if (rawName === "full_name") {
      fieldKey = "nome";
    } else if (rawName === "primary_phone") {
      fieldKey = "telefone";
    } else if (rawName === "login_email") {
      fieldKey = "email";
    } else if (rawName === "country") {
      fieldKey = "pais";
    } else if (rawName === "birth_date") {
      fieldKey = "data_nascimento";
    }
    if (!quantityFieldKeys.has(fieldKey)) {
      return;
    }
    ["input", "change"].forEach((eventName) => {
      controlEl.addEventListener(eventName, () => {
        renderMeuPerfilQuantityGroups();
      });
    });
  });

  if (formEl.dataset.boundMeuPerfilQuantitySubmit !== "1") {
    formEl.dataset.boundMeuPerfilQuantitySubmit = "1";
    formEl.addEventListener("submit", () => {
      syncMeuPerfilQuantityHiddenInputs(collectCurrentMeuPerfilQuantityValues());
    });
  }

  renderMeuPerfilQuantityGroups();
}

function setupConditionalProcessVisibility() {
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  const personalFormEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  if (personalFormEl && personalFormEl.dataset.boundSubsequentVisibility !== "1") {
    personalFormEl.dataset.boundSubsequentVisibility = "1";
    ["input", "change"].forEach((eventName) => {
      personalFormEl.addEventListener(eventName, (event) => {
        // Digitar em campo de texto nao altera gatilhos (selects/checkbox usam change).
        // Reaplicar a cada tecla reconstroi o bloco de quantidade e faz a pagina tremer.
        const target = event && event.target;
        if (eventName === "input" && target && target.matches && target.matches("input:not([type=checkbox]):not([type=radio]):not([type=file])")) {
          return;
        }
        applyMeuPerfilProcessSubsequentVisibility();
      });
    });
    // Aplica ja no carregamento: sem isto abas ocultas por regra ficam visiveis ate a primeira alteracao.
    applyMeuPerfilProcessSubsequentVisibility();
    // O menu de abas e redesenhado por outros gestores (tabs_overflow_v1.js) depois do setup:
    // um observador volta a ocultar as abas que a regra manda ocultar.
    enforceMeuPerfilHiddenSectionLinksV1();
    new MutationObserver(enforceMeuPerfilHiddenSectionLinksV1).observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["style", "class"]
    });
  }

  if (dynamicProcessEditFormEl && dynamicProcessEditFormEl.dataset.boundSubsequentVisibility !== "1") {
    dynamicProcessEditFormEl.dataset.boundSubsequentVisibility = "1";
    ["input", "change"].forEach((eventName) => {
      dynamicProcessEditFormEl.addEventListener(eventName, () => {
        applyConditionalProcessFieldRulesV1(dynamicProcessEditFormEl);
        if (dynamicProcessPopulatingV1) {
          return;
        }
        // Editor inline aberto: redesenhar a lista fecharia o editor (perde a linha em edicao).
        if (dynamicProcessInlineHolderV1) {
          return;
        }
        const cleanMenuKey = normalizeMenuKey(dynamicProcessMenuKeyInputEl ? dynamicProcessMenuKeyInputEl.value : "");
        if (!cleanMenuKey) {
          return;
        }
        renderDynamicProcessCard(
          cleanMenuKey,
          selectedDynamicSectionByMenu[cleanMenuKey] || (dynamicProcessSectionKeyInputEl ? dynamicProcessSectionKeyInputEl.value : "")
        );
      });
    });
  }

  if (dynamicProcessEditFormEl && dynamicProcessEditFormEl.dataset.boundQuantitySync !== "1") {
    dynamicProcessEditFormEl.dataset.boundQuantitySync = "1";
    dynamicProcessEditFormEl.addEventListener("submit", () => {
      const cleanMenuKey = normalizeMenuKey(dynamicProcessMenuKeyInputEl ? dynamicProcessMenuKeyInputEl.value : "");
      if (!cleanMenuKey) {
        return;
      }
      syncDynamicProcessQuantityHiddenInputs(
        cleanMenuKey,
        collectCurrentDynamicProcessQuantityValues(cleanMenuKey)
      );
    });
  }
}

function syncTrainingOutrosState() {
  if (!trainingOutrosInputEl) {
    return;
  }
  const isEnabled = trainingOutrosEnabledEl ? trainingOutrosEnabledEl.checked : false;
  trainingOutrosInputEl.disabled = !isEnabled;
  if (!isEnabled) {
    trainingOutrosInputEl.value = "";
  }
}

function enhanceProcessShellTables(root) {
  const scopeRoot = root || document;
  if (!window.AppGenesisProcessShell) {
    return;
  }

  if (typeof window.AppGenesisProcessShell.enhanceSearchableTableCards === "function") {
    window.AppGenesisProcessShell.enhanceSearchableTableCards({ root: scopeRoot });
  }

  if (typeof window.AppGenesisProcessShell.enhanceLoadMoreTables === "function") {
    window.AppGenesisProcessShell.enhanceLoadMoreTables({ root: scopeRoot });
  }

  if (typeof window.AppGenesisProcessShell.enhanceTableActionMenus === "function") {
    window.AppGenesisProcessShell.enhanceTableActionMenus({ root: scopeRoot });
  }

  if (typeof window.AppGenesisProcessShell.enhanceConfirmableActions === "function") {
    window.AppGenesisProcessShell.enhanceConfirmableActions({ root: document });
  }

  if (typeof window.AppGenesisProcessShell.enhanceResponsiveTableColumns === "function") {
    window.AppGenesisProcessShell.enhanceResponsiveTableColumns({ root: scopeRoot });
  }
}

function setupTableLimiter(prefix) {
  const tableEl = document.getElementById(`${prefix}-table`);
  if (
    !tableEl ||
    !window.AppGenesisProcessShell ||
    (
      typeof window.AppGenesisProcessShell.enhanceTableActionMenus !== "function" &&
      typeof window.AppGenesisProcessShell.enhanceSearchableTableCards !== "function" &&
      typeof window.AppGenesisProcessShell.enhanceLoadMoreTables !== "function"
    )
  ) {
    return;
  }

  const scopeRoot = tableEl.closest(".card") || tableEl.parentElement || document;
  enhanceProcessShellTables(scopeRoot);
}

function setupReadOnlyCards() {
  const readonlyCards = document.querySelectorAll('.entity-panel-card[data-readonly-mode="1"]');
  readonlyCards.forEach((card) => {
    const controls = card.querySelectorAll("input, select, textarea, button");
    controls.forEach((control) => {
      if (control.tagName === "INPUT" && control.type === "hidden") {
        return;
      }
      if (control.hasAttribute("data-appgenesis-cancel")) {
        return;
      }
      control.disabled = true;
      control.required = false;
      control.classList.add("readonly-field");
    });
    const formEl = card.querySelector("form");
    if (formEl) {
      formEl.addEventListener("submit", (event) => {
        event.preventDefault();
      });
    }
  });
}
