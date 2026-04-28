//###################################################################################
// APPVERBOBRAGA - ADMINISTRATIVO -> MENU - ABAS INTERNAS DO PROCESSO
//###################################################################################

(function (window) {
  "use strict";

  //###################################################################################
  // (1) ABAS PADRAO
  //###################################################################################

  const DEFAULT_ADMIN_PROCESS_SETTINGS_TABS = [
    { key: "geral", label: "Geral" },
    { key: "configuracao_campos", label: "Configuração dos campos" },
    { key: "campos_adicionais", label: "Campos adicionais" }
  ];

  //###################################################################################
  // (2) NORMALIZAR CHAVE DA ABA
  //###################################################################################

  function normalizeSettingsTabKey_v1(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/-/g, "_");
  }

  //###################################################################################
  // (3) OBTER ABAS A PARTIR DO PROCESSO
  //###################################################################################

  function getAdminProcessSettingsTabs_v1(setting) {
    if (!setting || setting.settings_tabs_enabled !== true) {
      return [];
    }

    const rawTabs = Array.isArray(setting.settings_tabs) && setting.settings_tabs.length
      ? setting.settings_tabs
      : DEFAULT_ADMIN_PROCESS_SETTINGS_TABS;

    return rawTabs
      .map(function (tab) {
        return {
          key: normalizeSettingsTabKey_v1(tab.key),
          label: String(tab.label || tab.key || "").trim()
        };
      })
      .filter(function (tab) {
        return tab.key && tab.label;
      });
  }

  //###################################################################################
  // (4) RESOLVER ABA ATIVA
  //###################################################################################

  function resolveAdminProcessSettingsTab_v1(setting, requestedTab) {
    const tabs = getAdminProcessSettingsTabs_v1(setting);
    const allowedKeys = new Set(tabs.map(function (tab) {
      return tab.key;
    }));

    const cleanRequestedTab = normalizeSettingsTabKey_v1(requestedTab);

    if (allowedKeys.has(cleanRequestedTab)) {
      return cleanRequestedTab;
    }

    return tabs.length ? tabs[0].key : "";
  }

  //###################################################################################
  // (5) CRIAR ITEMS PARA RENDERIZAR NO MENU DE ABAS
  //###################################################################################

  function buildAdminProcessSettingsTabItems_v1(setting, targetSelector, requestedTab) {
    const tabs = getAdminProcessSettingsTabs_v1(setting);
    const activeTab = resolveAdminProcessSettingsTab_v1(setting, requestedTab);

    return tabs.map(function (tab) {
      return {
        label: tab.label,
        target: targetSelector || "#settings-menu-edit-card",
        settingsTab: tab.key,
        active: tab.key === activeTab
      };
    });
  }

  //###################################################################################
  // (6) EXPOR FUNCOES NO WINDOW
  //###################################################################################

  window.AppVerboAdminProcessTabs_v1 = {
    DEFAULT_ADMIN_PROCESS_SETTINGS_TABS: DEFAULT_ADMIN_PROCESS_SETTINGS_TABS,
    normalizeSettingsTabKey_v1: normalizeSettingsTabKey_v1,
    getAdminProcessSettingsTabs_v1: getAdminProcessSettingsTabs_v1,
    resolveAdminProcessSettingsTab_v1: resolveAdminProcessSettingsTab_v1,
    buildAdminProcessSettingsTabItems_v1: buildAdminProcessSettingsTabItems_v1
  };
})(window);
