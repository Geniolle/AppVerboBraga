// new_user/07_navigation.js: Navegacao: conteudo por menu, submenu, ativacao de menu e hash.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

function applyContentForMenu(menuKey) {
  if (
    appGenesisProcessCardsVisibilityV1 &&
    typeof appGenesisProcessCardsVisibilityV1.applyContentForMenu === "function"
  ) {
    return appGenesisProcessCardsVisibilityV1.applyContentForMenu(menuKey);
  }
}

// APPGENESIS_ADMIN_SUBPROCESS_GROUP_V1_START
function getAdminSubprocessKeyByTargetV1(target) {
  if (
    appGenesisAdminTargetRegistryV1 &&
    typeof appGenesisAdminTargetRegistryV1.getAdminSubprocessKeyByTarget === "function"
  ) {
    return appGenesisAdminTargetRegistryV1.getAdminSubprocessKeyByTarget(target);
  }
  const cleanTarget = normalizeTargetV1(target);
  const sidebarAdminMenuKey = getSidebarAdminSubprocessMenuKeyByTargetV1(cleanTarget);
  if (sidebarAdminMenuKey) {
    const sidebarAdminSubprocessSetting = getSidebarAdminSubprocessSettingV1(sidebarAdminMenuKey);
    return sidebarAdminSubprocessSetting ? sidebarAdminSubprocessSetting.subprocessKey : "";
  }
  const targetMap = {
    "#create-entity-card": ENTIDADE_SUBPROCESS_KEY_V1,
    "#edit-entity-card": ENTIDADE_SUBPROCESS_KEY_V1,
    "#recent-entities-card": ENTIDADE_SUBPROCESS_KEY_V1,
    "#inactive-entities-card": ENTIDADE_SUBPROCESS_KEY_V1,
    "#create-user-card": UTILIZADOR_SUBPROCESS_KEY_V1,
    "#edit-user-card": UTILIZADOR_SUBPROCESS_KEY_V1,
    "#admin-users-created-card": UTILIZADOR_SUBPROCESS_KEY_V1,
    "#inactive-users-card": UTILIZADOR_SUBPROCESS_KEY_V1,
    "#admin-sidebar-sections-card": ESTRUTURAS_MENU_KEY_V1,
    "#admin-sidebar-sections-form-card": ESTRUTURAS_MENU_KEY_V1,
    "#admin-sidebar-sections-card-active": ESTRUTURAS_MENU_KEY_V1,
    "#admin-sidebar-sections-card-inactive": ESTRUTURAS_MENU_KEY_V1,
    "#settings-card": MENU_SUBPROCESS_KEY_V1,
    "#settings-menu-edit-card": MENU_SUBPROCESS_KEY_V1,
    "#admin-account-status-card": MENU_SUBPROCESS_KEY_V1,
    "#admin-account-create-card": MENU_SUBPROCESS_KEY_V1,
    "#menu-subprocess-card": MENU_SUBPROCESS_KEY_V1,
    "#menu-subprocess-card-active": MENU_SUBPROCESS_KEY_V1,
    "#menu-subprocess-card-inactive": MENU_SUBPROCESS_KEY_V1,
    "#auth-profile-card": PERFIL_AUTORIZACAO_MENU_KEY_V1,
    "#auth-profile-form-card": PERFIL_AUTORIZACAO_MENU_KEY_V1,
    "#auth-profile-active-card": PERFIL_AUTORIZACAO_MENU_KEY_V1,
    "#auth-profile-inactive-card": PERFIL_AUTORIZACAO_MENU_KEY_V1,
    "#funcoes-administrativas-card": "funcoes_administrativas",
    "#funcoes-administrativas-form-card": "funcoes_administrativas",
    "#funcoes-administrativas-active-card": "funcoes_administrativas",
    "#funcoes-administrativas-inactive-card": "funcoes_administrativas",
    "#departamentos-card": "departamentos",
    "#departamentos-form-card": "departamentos",
    "#departamentos-active-card": "departamentos",
    "#departamentos-inactive-card": "departamentos",
  };
  return targetMap[cleanTarget] || "";
}

// activateSubprocessCardsV1: rotina única de ativação de card principal + cards relacionados
// (lista de ativos / lista de inativos) de um subprocesso administrativo (ex.: Menu, Sessões,
// Perfil de autorização). É a MESMA função usada tanto no boot inicial (bootstrap -> activateMenu
// -> aqui) quanto em qualquer navegação por clique (sidebar, submenu, hash, dropdown) -- não há
// rotina duplicada: todos os pontos de entrada de navegação client-side convergem para aqui.
// Agrupamento: cards com o mesmo "data-admin-subprocess" que o target resolvido (ex.: "menu") são
// mostrados/escondidos em conjunto, então card de ação + Menus ativos + Menus inativos entram e
// saem juntos sem precisar de hardcode por processo.
function applyContentForMenuTarget(menuKey, targetSelector, source = "unspecified") {
  if (
    appGenesisProcessCardsVisibilityV1 &&
    typeof appGenesisProcessCardsVisibilityV1.applyContentForMenuTarget === "function"
  ) {
    return appGenesisProcessCardsVisibilityV1.applyContentForMenuTarget(
      menuKey,
      targetSelector,
      source
    );
  }
}

function clearSubmenuActiveLinks(links) {
  if (
    appGenesisProcessSubmenuRuntimeV1 &&
    typeof appGenesisProcessSubmenuRuntimeV1.clearSubmenuActiveLinks === "function"
  ) {
    return appGenesisProcessSubmenuRuntimeV1.clearSubmenuActiveLinks(links);
  }
}

function normalizeSubmenuTargetAlias(targetSelector) {
  if (
    appGenesisAdminTargetRegistryV1 &&
    typeof appGenesisAdminTargetRegistryV1.normalizeSubmenuTargetAlias === "function"
  ) {
    return appGenesisAdminTargetRegistryV1.normalizeSubmenuTargetAlias(targetSelector);
  }
  const cleanTarget = String(targetSelector || "").trim();
  const normalizedAuthorizationProfileTarget = normalizeAuthorizationProfileTargetV1(cleanTarget);
  if (normalizedAuthorizationProfileTarget) {
    return normalizedAuthorizationProfileTarget;
  }
  const sidebarAdminMenuKey = getSidebarAdminSubprocessMenuKeyByTargetV1(cleanTarget);
  if (sidebarAdminMenuKey) {
    const sidebarAdminSubprocessSetting = getSidebarAdminSubprocessSettingV1(sidebarAdminMenuKey);
    if (
      sidebarAdminSubprocessSetting &&
      cleanTarget === sidebarAdminSubprocessSetting.editTarget
    ) {
      return sidebarAdminSubprocessSetting.defaultTarget;
    }
  }
  const targetAliasMap = {
    "#edit-user-card": "#create-user-card",
    "#admin-users-created-card": "#create-user-card",
    "#inactive-users-card": "#create-user-card",
    "#create-entity-card": "#recent-entities-card",
    "#edit-entity-card": "#recent-entities-card",
    "#inactive-entities-card": "#recent-entities-card",
    "#admin-account-create-card": "#menu-subprocess-card-active",
    "#settings-menu-edit-card": "#menu-subprocess-card-active",
    "#admin-sidebar-sections-form-card": "#admin-sidebar-sections-card"
  };
  return targetAliasMap[cleanTarget] || cleanTarget;
}

function setActiveSubmenu(targetSelector, selectedLinkEl = null) {
  if (
    appGenesisProcessSubmenuRuntimeV1 &&
    typeof appGenesisProcessSubmenuRuntimeV1.setActiveSubmenu === "function"
  ) {
    const result = appGenesisProcessSubmenuRuntimeV1.setActiveSubmenu(
      targetSelector,
      selectedLinkEl
    );
    refreshProcessShellBreadcrumbV1();
    return result;
  }
  refreshProcessShellBreadcrumbV1();
}

// .appgenesis-process-action-toggle-v1 define "display: inline-flex !important" no CSS, por isso um
// simples "el.style.display = 'none'" nao consegue escondê-lo; e preciso usar setProperty com
// prioridade "important" para vencer a regra do stylesheet.
function setDynamicProcessEditToggleVisible(isVisible) {
  const isProfileMenu = [PERFIL_MENU_KEY_V1, MEU_PERFIL_MENU_KEY].includes(normalizeMenuKey(activeMenuKey));
  if (isProfileMenu) {
    isVisible = false;
  }
  if (!dynamicProcessEditToggleEl) {
    return;
  }
  if (isVisible) {
    dynamicProcessEditToggleEl.style.removeProperty("display");
  } else {
    dynamicProcessEditToggleEl.style.setProperty("display", "none", "important");
  }
}

// Repoe a visibilidade do botao "Criar/Editar" do processo dinamico quando o card deixa de estar em edicao.
function restoreDynamicProcessEditToggleVisibility() {
  // So repoe quando o proprio processo dinamico esta visivel: senao (ex.: Administrativo > Entidade
  // depois de Guardar) o botao Editar aparece num card vazio.
  if (
    dynamicProcessEditToggleEl &&
    dynamicProcessCardEl &&
    dynamicProcessCardEl.offsetParent !== null &&
    !dynamicProcessCardEl.classList.contains("editing")
  ) {
    setDynamicProcessEditToggleVisible(true);
  }
}

function closeAllProfileEdits() {
  if (
    window.AppGenesisCancelControllerV1 &&
    typeof window.AppGenesisCancelControllerV1.closeAllOpenEditors === "function"
  ) {
    window.AppGenesisCancelControllerV1.closeAllOpenEditors(document);
    syncTrainingOutrosState();
    restoreDynamicProcessEditToggleVisibility();
    return;
  }

  const editingCards = document.querySelectorAll(".card.editing");
  editingCards.forEach((card) => {
    card.classList.remove("editing");
    const form = card.querySelector(".profile-edit-form");
    if (form) {
      form.reset();
    }
  });
  syncTrainingOutrosState();
  restoreDynamicProcessEditToggleVisibility();
}

function resetDynamicProcessCancelStateV1() {
  setDynamicProcessEditToggleVisible(true);
  if (dynamicProcessHistoryActionInputEl) {
    dynamicProcessHistoryActionInputEl.value = "create";
  }
  if (dynamicProcessHistoryRecordIdInputEl) {
    dynamicProcessHistoryRecordIdInputEl.value = "";
  }
  if (dynamicProcessHistoryRecordStateInputEl) {
    dynamicProcessHistoryRecordStateInputEl.value = "";
  }
  if (dynamicProcessSubmitBtnEl) {
    dynamicProcessSubmitBtnEl.textContent = "Guardar";
  }

  const currentMenuKey = normalizeMenuKey(dynamicProcessMenuKeyInputEl && dynamicProcessMenuKeyInputEl.value);
  const currentSetting = getSidebarMenuSetting(currentMenuKey);

  if (dynamicProcessTitleEl && currentSetting) {
    const layoutConfig = getDynamicProcessLayoutConfig(
      currentSetting,
      currentSetting.label || currentMenuKey,
      ""
    );

    if (layoutConfig.isListProcess) {
      dynamicProcessTitleEl.textContent = layoutConfig.createTitle;
    }
  }
}

function renderSubmenu(menuKey) {
  if (
    appGenesisProcessSubmenuRuntimeV1 &&
    typeof appGenesisProcessSubmenuRuntimeV1.renderSubmenu === "function"
  ) {
    return appGenesisProcessSubmenuRuntimeV1.renderSubmenu(menuKey);
  }
}

function getDefaultTargetForMenu(menuKey, config, options = {}) {
  if (
    appGenesisProcessNavigationStateV1 &&
    typeof appGenesisProcessNavigationStateV1.getDefaultTargetForMenu === "function"
  ) {
    return appGenesisProcessNavigationStateV1.getDefaultTargetForMenu(
      menuKey,
      config,
      options
    );
  }
  return "";
}

function refreshProcessShellBreadcrumbV1() {
  if (
    processShellHeaderController &&
    typeof processShellHeaderController.refresh === "function"
  ) {
    processShellHeaderController.refresh();
  }
}

function syncActiveTabTitle(tabsContainerSelector, titleSelector, ignoredLabels) {
  var ignored = new Set(
    (Array.isArray(ignoredLabels) ? ignoredLabels : ["Mais"])
      .map(function (s) { return String(s || "").trim().toLowerCase(); })
  );
  var container = document.querySelector(tabsContainerSelector);
  var titleEl = document.querySelector(titleSelector);
  if (!container || !titleEl) {
    return;
  }
  var activeTab = container.querySelector(".submenu-item.active");
  if (!activeTab) {
    return;
  }
  var label = String(activeTab.textContent || "").trim();
  if (!label || ignored.has(label.toLowerCase())) {
    refreshProcessShellBreadcrumbV1();
    return;
  }
  titleEl.textContent = label;
  refreshProcessShellBreadcrumbV1();
}

function activateMenu(menuKey, options = {}) {
  if (
    appGenesisProcessMenuRuntimeV1 &&
    typeof appGenesisProcessMenuRuntimeV1.activateMenu === "function"
  ) {
    return appGenesisProcessMenuRuntimeV1.activateMenu(menuKey, options);
  }
}

function activateMenuTarget(menuKey, targetSelector, source = "unspecified") {
  if (
    appGenesisProcessMenuRuntimeV1 &&
    typeof appGenesisProcessMenuRuntimeV1.activateMenuTarget === "function"
  ) {
    return appGenesisProcessMenuRuntimeV1.activateMenuTarget(
      menuKey,
      targetSelector,
      source
    );
  }
}

function handleHashNavigation(rawHash) {
  if (
    appGenesisProcessMenuRuntimeV1 &&
    typeof appGenesisProcessMenuRuntimeV1.handleHashNavigation === "function"
  ) {
    return appGenesisProcessMenuRuntimeV1.handleHashNavigation(rawHash);
  }
}
