from pathlib import Path

ROOT = Path.cwd()

admin_tabs_path = ROOT / "appverbo" / "process_settings" / "admin_tabs.py"
admin_tabs_js_path = ROOT / "static" / "js" / "process_settings" / "adminProcessTabs_v1.js"
new_user_js_path = ROOT / "static" / "js" / "new_user.js"

admin_tabs_content = '''from __future__ import annotations

from typing import Any


####################################################################################
# (1) DEFINICAO GLOBAL DAS ABAS DO ADMINISTRATIVO -> MENU
####################################################################################

ADMIN_PROCESS_SETTINGS_TABS: tuple[dict[str, str], ...] = (
    {"key": "geral", "label": "Geral"},
    {"key": "configuracao_campos", "label": "Configuração dos campos"},
    {"key": "campos_adicionais", "label": "Campos adicionais"},
    {"key": "lista", "label": "Listas"},
    {"key": "campos_subsequentes", "label": "Campos Subsequentes"},
)


####################################################################################
# (2) NORMALIZAR CHAVE DA ABA
####################################################################################

def normalize_settings_tab_key_v1(value: Any) -> str:
    clean_value = str(value or "").strip().lower()
    clean_value = clean_value.replace("-", "_")
    return clean_value


####################################################################################
# (3) DEVOLVER ABAS PADRAO
####################################################################################

def get_admin_process_settings_tabs_v1() -> list[dict[str, str]]:
    return [dict(item) for item in ADMIN_PROCESS_SETTINGS_TABS]


####################################################################################
# (4) RESOLVER ABA ATIVA
####################################################################################

def resolve_admin_process_settings_tab_v1(raw_tab: Any) -> str:
    clean_tab = normalize_settings_tab_key_v1(raw_tab)

    available_tabs = {
        str(item["key"]).strip().lower()
        for item in ADMIN_PROCESS_SETTINGS_TABS
    }

    if clean_tab in available_tabs:
        return clean_tab

    return "geral"
'''

admin_tabs_js_content = '''//###################################################################################
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
    { key: "campos_adicionais", label: "Campos adicionais" },
    { key: "lista", label: "Listas" },
    { key: "campos_subsequentes", label: "Campos Subsequentes" }
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
'''

admin_tabs_path.write_text(admin_tabs_content, encoding="utf-8")
admin_tabs_js_path.write_text(admin_tabs_js_content, encoding="utf-8")

new_user_js_content = new_user_js_path.read_text(encoding="utf-8")

if '"campos-subsequentes": "campos-subsequentes"' not in new_user_js_content:
    new_user_js_content = new_user_js_content.replace(
        '    "adicionais": "campos-adicionais"',
        '    "adicionais": "campos-adicionais",\n'
        '    "lista": "lista",\n'
        '    "listas": "lista",\n'
        '    "campos-subsequentes": "campos-subsequentes",\n'
        '    "campos_subsequentes": "campos-subsequentes",\n'
        '    "subsequentes": "campos-subsequentes",\n'
        '    "subsequent": "campos-subsequentes",\n'
        '    "subsequent-rules": "campos-subsequentes"'
    )

new_user_js_path.write_text(new_user_js_content, encoding="utf-8")

print("Aba Campos Subsequentes aplicada nos ficheiros de abas.")
