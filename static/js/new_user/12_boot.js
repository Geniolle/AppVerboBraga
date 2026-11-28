// new_user/12_boot.js: Arranque da pagina (ativacao do menu inicial).
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

if (
  appGenesisProcessMenuRuntimeV1 &&
  typeof appGenesisProcessMenuRuntimeV1.bindHashChangeListener === "function"
) {
  appGenesisProcessMenuRuntimeV1.bindHashChangeListener();
}

syncTrainingOutrosState();
renderHomeCharts();
setupReadOnlyCards();
setupProfileProcessTabs();
setupMeuPerfilQuantityRules();
setupConditionalProcessVisibility();
setupProcessEditTabs();
logAppGenesisProcessEditorDebugV1("page_load:after_setup_snapshot", {
  href: window.location.href,
  activeTabKey: (function () {
    const activeLink = document.querySelector(".process-edit-tab-link.active");
    return activeLink ? activeLink.getAttribute("data-process-edit-tab") : null;
  })(),
  activePaneKey: (function () {
    const activePane = document.querySelector(".process-edit-pane.active");
    return activePane ? activePane.getAttribute("data-process-edit-pane") : null;
  })(),
  activeSidebarMenuKey: (function () {
    const activeMenuBtn = document.querySelector(".menu-item.active");
    return activeMenuBtn ? activeMenuBtn.getAttribute("data-menu") : null;
  })()
});
setupProcessFieldsBuilder();
setupProcessAdditionalFieldsManagerV2_guard_v1();
window.setTimeout(() => {
  try {
    setupProcessAdditionalFieldsManagerV2_guard_v1();
  } catch (_error) {
  }
}, 150);
window.setTimeout(() => {
  try {
    setupProcessAdditionalFieldsManagerV2_guard_v1();
  } catch (_error) {
  }
}, 600);
setupGeneratedInviteLinkCopy();
setupCreateUserGenerateLinkShortcut();
relocateUtilizadorInviteLinkButtonV1();
setupSidebarSectionsEditor();
if (
  window.AppGenesisProcessShell &&
  (
    typeof window.AppGenesisProcessShell.enhanceTableActionMenus === "function" ||
    typeof window.AppGenesisProcessShell.enhanceLoadMoreTables === "function" ||
    typeof window.AppGenesisProcessShell.enhanceSearchableTableCards === "function" ||
    typeof window.AppGenesisProcessShell.enhanceResponsiveTableColumns === "function"
  )
) {
  enhanceProcessShellTables(document);
}
relocateUtilizadorInviteLinkSlotV1();
setupTableLimiter("recent-entities");
setupTableLimiter("inactive-entities");
setupTableLimiter("admin-users");
setupTableLimiter("menu-ativo");
setupTableLimiter("menu-inativo");
setupTableLimiter("sessoes-ativo");
setupTableLimiter("sessoes-inativo");
// APPGENESIS_PREVENT_AUTH_PROFILE_FALLBACK_V1_START
// Função para validar se o perfil de autorização foi explicitamente solicitado.
function hasExplicitAuthProfileContextV1() {
  if (
    appGenesisProcessNavigationStateV1 &&
    typeof appGenesisProcessNavigationStateV1.hasExplicitAuthProfileContextV1 === "function"
  ) {
    return appGenesisProcessNavigationStateV1.hasExplicitAuthProfileContextV1();
  }
  return false;
}
// APPGENESIS_PREVENT_AUTH_PROFILE_FALLBACK_V1_END

const sidebarMenuKeys = new Set(Array.from(menuButtons).map((btn) => normalizeMenuKey(btn.dataset.menu)));
let startupMenu = (
  appGenesisProcessNavigationStateV1 &&
  typeof appGenesisProcessNavigationStateV1.resolveStartupMenu === "function"
)
  ? appGenesisProcessNavigationStateV1.resolveStartupMenu({
      initialMenu,
      menuConfig,
      sidebarMenuKeys
    })
  : "home";
(function logAppGenesisBootNavigationDebugV1() {
  const navigationEntries = (
    window.performance && typeof window.performance.getEntriesByType === "function"
  )
    ? window.performance.getEntriesByType("navigation")
    : [];
  const navigationType = navigationEntries.length ? String(navigationEntries[0].type || "") : "";
  const urlParams = new URLSearchParams(window.location.search);

  logAppGenesisNavigationBootDebugV1("boot:resolve", {
    href: window.location.href,
    navigationType,
    urlMenu: urlParams.get("menu"),
    urlAdminTab: urlParams.get("admin_tab"),
    urlTarget: urlParams.get("target"),
    urlHash: window.location.hash || "",
    bootstrapInitialMenu: bootstrap.initialMenu || null,
    bootstrapInitialAdminTab: bootstrap.initialAdminTab || null,
    bootstrapInitialMenuTarget: bootstrap.initialMenuTarget || null,
    bootstrapInitialDynamicProcessSection: bootstrap.initialDynamicProcessSection || null,
    bootstrapSettingsAction: bootstrap.settingsAction || null,
    bootstrapSettingsEditKey: bootstrap.settingsEditKey || null,
    bootstrapSettingsTab: bootstrap.settingsTab || null,
    resolvedStartupMenu: startupMenu,
    stateSource: urlParams.get("menu") ? "querystring" : (bootstrap.initialMenu ? "bootstrap" : "fallback_home")
  });
})();

activateMenu(startupMenu, { resetDynamicToFirst: false, source: "boot" });
handleHashNavigation(window.location.hash || "");

logAppGenesisNavigationBootDebugV1("boot:activated", {
  href: window.location.href,
  activeMenuKey: (typeof window.__appgenesisGetActiveMenuKeyV1 === "function")
    ? window.__appgenesisGetActiveMenuKeyV1()
    : null
});

//###################################################################################
// (99) COMPATIBILIDADE - BLOQUEIO DO MANAGER V2 QUANDO O V3 ESTIVER ATIVO
//###################################################################################

function setupProcessAdditionalFieldsManagerV2_guard_v1() {
  if (document.querySelector("[data-process-additional-fields-manager-v3='1']")) {
    return;
  }

  if (typeof setupProcessAdditionalFieldsManagerV2 === "function") {
    setupProcessAdditionalFieldsManagerV2();
  }
}
