// new_user/10_runtime_wiring.js: Ligacao aos runtimes externos e listeners globais (ordem original).
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.
if (
  appGenesisProcessNavigationStateV1 &&
  typeof appGenesisProcessNavigationStateV1.configure === "function"
) {
  appGenesisProcessNavigationStateV1.configure({
    normalizeMenuKey,
    normalizeTarget: normalizeTargetV1,
    normalizeAuthorizationProfileTarget: normalizeAuthorizationProfileTargetV1,
    isNativeAdminTarget: isNativeAdminTargetV1,
    isNativeTargetForMenu: isNativeTargetForMenuV1,
    windowRef: window
  });
}
function resolveAdminSelectedTargetV1({
  initialAdminTab,
  startupHash: rawHash,
  initialMenuTarget: rawTarget,
  settingsEditKey: rawSettingsKey
}) {
  if (
    appGenesisProcessNavigationStateV1 &&
    typeof appGenesisProcessNavigationStateV1.resolveAdminSelectedTargetV1 === "function"
  ) {
    return appGenesisProcessNavigationStateV1.resolveAdminSelectedTargetV1({
      initialAdminTab,
      startupHash: rawHash,
      initialMenuTarget: rawTarget,
      settingsEditKey: rawSettingsKey
    });
  }
  return "#dynamic-process-card";
}
// APPGENESIS_ADMIN_TARGET_RESOLVER_V1_END
let meuPerfilSelectedTarget = "#perfil-pessoal-card";
const requestedMeuPerfilProfileSection = normalizeMenuKey(
  (typeof window !== "undefined" && window.location && window.location.search)
    ? new URLSearchParams(window.location.search).get("profile_section")
    : ""
);
let meuPerfilSelectedProfileSection = (
  Array.isArray(profilePersonalSections) && profilePersonalSections.length
)
  ? String(requestedMeuPerfilProfileSection || profilePersonalSections[0].key || "")
  : "";
let hiddenMeuPerfilSectionKeys = new Set();
if (startupHash === "#home-summary-card") {
  homeSelectedTarget = startupHash;
}
const adminSelectedTarget = resolveAdminSelectedTargetV1({
  initialAdminTab,
  startupHash,
  initialMenuTarget,
  settingsEditKey
});
const selectedTargetByMenu = {
  [HOME_MENU_KEY_V1]: homeSelectedTarget,
  [PERFIL_MENU_KEY_V1]: profileSelectedTarget,
  [ADMINISTRATIVO_MENU_KEY_V1]: adminSelectedTarget,
  // Estruturas (ESTRUTURAS_MENU_KEY_V1) partilha o mesmo conjunto nativo de cards por
  // admin_tab/target/hash que "administrativo" (ex.: menu-subprocess-card-active, usado pelo
  // editor de processo) -- getDefaultTargetForMenu/isNativeTargetForMenuV1 ja validam o alvo
  // contra ESTRUTURAS_NATIVE_TARGETS_V1 antes de aceita-lo, entao reaproveitar a mesma
  // resolucao aqui e' seguro e evita logica duplicada por menu.
  [ESTRUTURAS_MENU_KEY_V1]: adminSelectedTarget,
  [MEU_PERFIL_MENU_KEY]: meuPerfilSelectedTarget
};
if (
  appGenesisProcessNavigationStateV1 &&
  typeof appGenesisProcessNavigationStateV1.configure === "function"
) {
  appGenesisProcessNavigationStateV1.configure({
    selectedTargetByMenu
  });
}
let topSubmenuController = null;
if (
  appGenesisProcessSubmenuRuntimeV1 &&
  typeof appGenesisProcessSubmenuRuntimeV1.createTopSubmenuController === "function"
) {
  topSubmenuController = appGenesisProcessSubmenuRuntimeV1.createTopSubmenuController({
    container: itemsEl,
    windowRef: window,
    formatLabel: toSentenceCaseText,
    normalizeMenuKey,
    getActiveMenuKey: () => activeMenuKey,
    closeAllProfileEdits,
    selectedTargetByMenu,
    selectedDynamicSectionByMenu,
    debugTabsLog: debugTabsLogV1,
    logNavigationBootDebug: logAppGenesisNavigationBootDebugV1,
    setActiveSubmenu,
    applyContentForMenuTarget,
    getAdminSubprocessKeyByTarget: getAdminSubprocessKeyByTargetV1,
    renderDynamicProcessCard,
    MEU_PERFIL_MENU_KEY,
    setMeuPerfilSelectedProfileSection: (sectionKey) => {
      meuPerfilSelectedProfileSection = sectionKey;
    },
    activateProfilePersonalSection: (sectionKey) => {
      if (typeof window.activateProfilePersonalSection === "function") {
        window.activateProfilePersonalSection(sectionKey);
      }
    },
    applyMeuPerfilProcessSubsequentVisibility,
    syncActiveTabTitle,
    documentRef: document
  });
}
if (
  appGenesisProcessSubmenuRuntimeV1 &&
  typeof appGenesisProcessSubmenuRuntimeV1.configure === "function"
) {
  appGenesisProcessSubmenuRuntimeV1.configure({
    itemsEl,
    topSubmenuController,
    menuConfig,
    selectedTargetByMenu,
    selectedDynamicSectionByMenu,
    normalizeMenuKey,
    normalizeSubmenuTargetAlias,
    formatLabel: toSentenceCaseText,
    closeAllProfileEdits,
    applyContentForMenuTarget,
    renderDynamicProcessCard,
    getAdminSubprocessKeyByTarget: getAdminSubprocessKeyByTargetV1,
    debugTabsLog: debugTabsLogV1,
    logNavigationBootDebug: logAppGenesisNavigationBootDebugV1,
    getActiveMenuKey: () => activeMenuKey,
    refreshProcessShellBreadcrumb: refreshProcessShellBreadcrumbV1,
    setMeuPerfilSelectedProfileSection: (sectionKey) => {
      meuPerfilSelectedProfileSection = sectionKey;
    },
    activateProfilePersonalSection: (sectionKey) => {
      if (typeof window.activateProfilePersonalSection === "function") {
        window.activateProfilePersonalSection(sectionKey);
      }
    },
    applyMeuPerfilProcessSubsequentVisibility,
    syncActiveTabTitle,
    MEU_PERFIL_MENU_KEY,
    windowRef: window,
    documentRef: document
  });
}
if (
  appGenesisProcessMenuRuntimeV1 &&
  typeof appGenesisProcessMenuRuntimeV1.configure === "function"
) {
  appGenesisProcessMenuRuntimeV1.configure({
    menuConfig,
    menuButtons,
    selectedTargetByMenu,
    selectedDynamicSectionByMenu,
    normalizeMenuKey,
    renderSubmenu,
    getDefaultTargetForMenu,
    setActiveSubmenu,
    applyContentForMenuTarget,
    renderDynamicProcessCard,
    closeAllProfileEdits,
    syncActiveTabTitle,
    applyMeuPerfilProcessSubsequentVisibility,
    applyContentForMenu,
    getAdminSubprocessKeyByTarget: getAdminSubprocessKeyByTargetV1,
    getSidebarAdminSubprocessMenuKeyByTarget: getSidebarAdminSubprocessMenuKeyByTargetV1,
    normalizeAuthorizationProfileTarget: normalizeAuthorizationProfileTargetV1,
    debugTabsLog: debugTabsLogV1,
    logNavigationBootDebug: logAppGenesisNavigationBootDebugV1,
    getMeuPerfilSelectedProfileSection: () => meuPerfilSelectedProfileSection,
    setMeuPerfilSelectedProfileSection: (sectionKey) => {
      meuPerfilSelectedProfileSection = sectionKey;
    },
    activateProfilePersonalSection: (sectionKey) => {
      if (typeof window.activateProfilePersonalSection === "function") {
        window.activateProfilePersonalSection(sectionKey);
      }
    },
    setActiveMenuKey: (menuKey) => {
      activeMenuKey = menuKey;
    },
    getActiveMenuKey: () => activeMenuKey,
    MEU_PERFIL_MENU_KEY,
    ESTRUTURAS_MENU_KEY_V1,
    windowRef: window
  });
}
Object.keys(dynamicProcessDataByMenu).forEach((menuKey) => {
  if (isNativeTargetForMenuV1(menuKey, selectedTargetByMenu[menuKey])) {
    return;
  }
  selectedTargetByMenu[menuKey] = "#dynamic-process-card";
});
if (!startupHash && initialMenuTarget && menuConfig[initialMenu]) {
  const cleanInitialTarget = String(initialMenuTarget || "");
  const initialMenuItems = Array.isArray(menuConfig[initialMenu].items)
    ? menuConfig[initialMenu].items
    : [];
  const targetExistsInItems = initialMenuItems.some(
    (item) => (
      initialMenu === PERFIL_AUTORIZACAO_MENU_KEY_V1
        ? authorizationProfileTargetsMatchV1(item.target, cleanInitialTarget)
        : String(item.target || "") === cleanInitialTarget
    )
  );
  if (targetExistsInItems || isNativeTargetForMenuV1(initialMenu, cleanInitialTarget)) {
    selectedTargetByMenu[initialMenu] = cleanInitialTarget;
  }
}
if (
  !startupHash &&
  initialDynamicProcessSection &&
  selectedDynamicSectionByMenu[initialMenu]
) {
  selectedDynamicSectionByMenu[initialMenu] = String(initialDynamicProcessSection);
}
let activeMenuKey = "";
// Sinal autoritativo do menu de topo realmente ativo na SPA, para módulos externos (ex.:
// top_menu_active_v1.js) que não podem confiar apenas no URL: a navegação por clique entre
// menus que não sejam "administrativo" não faz pushState, por isso o URL fica desatualizado.
window.__appgenesisGetActiveMenuKeyV1 = function () {
  return activeMenuKey;
};
const processShellHeaderController = (
  processShellHeaderEl &&
  processShellTitleEl &&
  window.AppGenesisProcessShell &&
  typeof window.AppGenesisProcessShell.createProcessHeaderController === "function"
)
  ? window.AppGenesisProcessShell.createProcessHeaderController({
      root: processShellHeaderEl,
      titleEl: processShellTitleEl,
      actionsEl: processShellActionsEl,
      getTitle: () => {
        const activeConfig = menuConfig[activeMenuKey] || menuConfig[initialMenu];
        return activeConfig && activeConfig.title ? activeConfig.title : "Processo";
      },
      getActions: () => []
    })
  : null;
if (
  appGenesisProcessMenuRuntimeV1 &&
  typeof appGenesisProcessMenuRuntimeV1.configure === "function"
) {
  appGenesisProcessMenuRuntimeV1.configure({
    processShellHeaderController,
    refreshProcessShellBreadcrumb: refreshProcessShellBreadcrumbV1
  });
}
// APPGENESIS_ADMIN_SUBPROCESS_GROUP_V1_END

if (
  appGenesisProcessCardsVisibilityV1 &&
  typeof appGenesisProcessCardsVisibilityV1.configure === "function"
) {
  appGenesisProcessCardsVisibilityV1.configure({
    normalizeMenuKey,
    getSidebarAdminSubprocessSetting: getSidebarAdminSubprocessSettingV1,
    getAdminSubprocessKeyByTarget: getAdminSubprocessKeyByTargetV1,
    ESTRUTURAS_MENU_KEY_V1,
    scopedCards,
    dynamicProcessCardEl,
    dynamicProcessActiveCardEl,
    dynamicProcessInactiveCardEl,
    debugTabsLog: debugTabsLogV1,
    logNavigationBootDebug: logAppGenesisNavigationBootDebugV1,
    documentRef: document,
    windowRef: window
  });
}

// Alias explícito pedido para o mecanismo de ativação de grupo de cards de subprocesso -- é a
// mesma função, exposta com o nome documentado para depuração/testes a partir do console.
window.activateSubprocessCardsV1 = function (menuKey, targetSelector, source) {
  return applyContentForMenuTarget(menuKey, targetSelector, source);
};

document.addEventListener("click", (event) => {
  if (event.target.closest("#perfil-pessoal-card .profile-edit-form [type='submit']")) {
    syncMeuPerfilHiddenRequiredFields();
  }
}, true);

document.addEventListener("appgenesis:cancelled", function (event) {
  const detail = event && event.detail ? event.detail : {};
  const card = detail.card;
  const cardId = card && card.id ? card.id : "";

  if (cardId === "dynamic-process-card") {
    closeDynamicProcessInlineFormV1();
    resetDynamicProcessCancelStateV1();
  }

  if (
    cardId === "dynamic-process-card" ||
    cardId === "perfil-pessoal-card"
  ) {
    syncTrainingOutrosState();
  }
});
