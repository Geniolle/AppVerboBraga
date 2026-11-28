// new_user/01_state.js: Estado inicial (bootstrap), constantes e normalizadores partilhados.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.
(function initAppGenesisFeedbackToastsFromUrl() {
  if (
    window.AppGenesisProcessShell &&
    typeof window.AppGenesisProcessShell.enhanceFeedbackToasts === "function"
  ) {
    window.AppGenesisProcessShell.enhanceFeedbackToasts({ source: "url" });
  }
})();

const bootstrap = window.__APPGENESIS_BOOTSTRAP__ || {};
const appGenesisProcessKeysRegistryV1 =
  window.AppGenesisProcessKeysRegistryV1 &&
  typeof window.AppGenesisProcessKeysRegistryV1 === "object"
    ? window.AppGenesisProcessKeysRegistryV1
    : null;
const appGenesisProcessReferenceRegistryV1 =
  window.AppGenesisProcessReferenceRegistryV1 &&
  typeof window.AppGenesisProcessReferenceRegistryV1 === "object"
    ? window.AppGenesisProcessReferenceRegistryV1
    : null;
const appGenesisAdminTargetRegistryV1 =
  window.AppGenesisAdminTargetRegistryV1 &&
  typeof window.AppGenesisAdminTargetRegistryV1 === "object"
    ? window.AppGenesisAdminTargetRegistryV1
    : null;
const appGenesisProcessMenuConfigBuilderV1 =
  window.AppGenesisProcessMenuConfigBuilderV1 &&
  typeof window.AppGenesisProcessMenuConfigBuilderV1 === "object"
    ? window.AppGenesisProcessMenuConfigBuilderV1
    : null;
const appGenesisProcessNavigationStateV1 =
  window.AppGenesisProcessNavigationStateV1 &&
  typeof window.AppGenesisProcessNavigationStateV1 === "object"
    ? window.AppGenesisProcessNavigationStateV1
    : null;
const appGenesisProcessCardsVisibilityV1 =
  window.AppGenesisProcessCardsVisibilityV1 &&
  typeof window.AppGenesisProcessCardsVisibilityV1 === "object"
    ? window.AppGenesisProcessCardsVisibilityV1
    : null;
const appGenesisProcessSubmenuRuntimeV1 =
  window.AppGenesisProcessSubmenuRuntimeV1 &&
  typeof window.AppGenesisProcessSubmenuRuntimeV1 === "object"
    ? window.AppGenesisProcessSubmenuRuntimeV1
    : null;
const appGenesisProcessMenuRuntimeV1 =
  window.AppGenesisProcessMenuRuntimeV1 &&
  typeof window.AppGenesisProcessMenuRuntimeV1 === "object"
    ? window.AppGenesisProcessMenuRuntimeV1
    : null;
const MEU_PERFIL_MENU_KEY = appGenesisProcessKeysRegistryV1
  ? appGenesisProcessKeysRegistryV1.MEU_PERFIL_MENU_KEY
  : "meu_perfil";
const HOME_MENU_KEY_V1 = appGenesisProcessReferenceRegistryV1
  ? appGenesisProcessReferenceRegistryV1.HOME_MENU_KEY_V1
  : "home";
const PERFIL_MENU_KEY_V1 = appGenesisProcessReferenceRegistryV1
  ? appGenesisProcessReferenceRegistryV1.PERFIL_MENU_KEY_V1
  : "perfil";
const ADMINISTRATIVO_MENU_KEY_V1 = appGenesisProcessReferenceRegistryV1
  ? appGenesisProcessReferenceRegistryV1.ADMINISTRATIVO_MENU_KEY_V1
  : "administrativo";
const PERFIL_AUTORIZACAO_MENU_KEY_V1 = appGenesisProcessReferenceRegistryV1
  ? appGenesisProcessReferenceRegistryV1.PERFIL_AUTORIZACAO_MENU_KEY_V1
  : "perfil_de_autorizacao";
const ENTIDADE_SUBPROCESS_KEY_V1 = appGenesisProcessReferenceRegistryV1
  ? appGenesisProcessReferenceRegistryV1.ENTIDADE_SUBPROCESS_KEY_V1
  : "entidade";
const UTILIZADOR_SUBPROCESS_KEY_V1 = appGenesisProcessReferenceRegistryV1
  ? appGenesisProcessReferenceRegistryV1.UTILIZADOR_SUBPROCESS_KEY_V1
  : "utilizador";
const MENU_SUBPROCESS_KEY_V1 = appGenesisProcessReferenceRegistryV1
  ? appGenesisProcessReferenceRegistryV1.MENU_SUBPROCESS_KEY_V1
  : "menu";
const LEGACY_DOCUMENTOS_MENU_KEY = appGenesisProcessKeysRegistryV1
  ? appGenesisProcessKeysRegistryV1.LEGACY_DOCUMENTOS_MENU_KEY
  : "documentos";
const currentUserName = bootstrap.currentUserName || "";
const currentUserEmail = bootstrap.currentUserEmail || "";
const currentUserIsAdmin = Boolean(bootstrap.currentUserIsAdmin);
const currentUserCanManageTenantStructure = Boolean(bootstrap.currentUserCanManageTenantStructure);
const currentUserCanManageAllEntities = currentUserCanManageTenantStructure;

const APPGENESIS_DEBUG_TABS_V1 =
  new URLSearchParams(window.location.search).get("debug_tabs") === "1" ||
  window.localStorage.getItem("appgenesisDebugTabs") === "1";

function debugTabsLogV1(label, payload = {}) {
  if (!APPGENESIS_DEBUG_TABS_V1) return;
  console.log("[AppGenesis Tabs Debug]", label, payload);
}
const dashboardData = bootstrap.dashboardData || {};
const currentUserPhone = bootstrap.currentUserPhone || "";
const currentUserAccountStatus = bootstrap.currentUserAccountStatus || "";
const currentUserMemberStatus = bootstrap.currentUserMemberStatus || "";
const currentUserEntities = bootstrap.currentUserEntities || "";
const currentUserAddress = bootstrap.currentUserAddress || "";
const currentUserCity = bootstrap.currentUserCity || "";
const currentUserFreguesia = bootstrap.currentUserFreguesia || "";
const currentUserPostalCode = bootstrap.currentUserPostalCode || "";
const profilePersonalSections = Array.isArray(bootstrap.profilePersonalSections) ? bootstrap.profilePersonalSections : [];
const profilePersonalFieldLabels = (
  bootstrap.profilePersonalFieldLabels &&
  typeof bootstrap.profilePersonalFieldLabels === "object" &&
  !Array.isArray(bootstrap.profilePersonalFieldLabels)
)
  ? bootstrap.profilePersonalFieldLabels
  : {};
const initialMenu = normalizeMenuKey(bootstrap.initialMenu || HOME_MENU_KEY_V1) || HOME_MENU_KEY_V1;
const initialMenuTarget = bootstrap.initialMenuTarget || "";
const initialDynamicProcessSection = bootstrap.initialDynamicProcessSection || "";
const initialAdminTab = bootstrap.initialAdminTab || ENTIDADE_SUBPROCESS_KEY_V1;
const currentEntityId = Number.parseInt(String(bootstrap.currentEntityId || "").trim(), 10);
const settingsAction = bootstrap.settingsAction || "";
const settingsTab = normalizeSettingsTabKey(bootstrap.settingsTab || "");
const settingsEditKey = normalizeMenuKey(bootstrap.settingsEditKey || "");

logAppGenesisProcessEditorDebugV1("page_load:editor_bootstrap", {
  href: window.location.href,
  urlMenu: new URLSearchParams(window.location.search).get("menu"),
  urlSettingsEditKey: new URLSearchParams(window.location.search).get("settings_edit_key"),
  urlSettingsTab: new URLSearchParams(window.location.search).get("settings_tab"),
  urlSettingsAction: new URLSearchParams(window.location.search).get("settings_action"),
  bootstrapSettingsAction: bootstrap.settingsAction,
  bootstrapSettingsTab: bootstrap.settingsTab,
  bootstrapSettingsEditKey: bootstrap.settingsEditKey,
  sessionStoragePostSaveContext: (function () {
    try {
      return window.sessionStorage.getItem(APPGENESIS_POST_SAVE_CONTEXT_KEY_V3);
    } catch (error) {
      return null;
    }
  })()
});
const sidebarMenuSettings = Array.isArray(bootstrap.sidebarMenuSettings) ? bootstrap.sidebarMenuSettings : [];
const sidebarMenuSettingsByKey = new Map();
const visibleSidebarMenuKeys = new Set(
  (Array.isArray(bootstrap.visibleSidebarMenuKeys) ? bootstrap.visibleSidebarMenuKeys : [])
    .map((menuKey) => normalizeMenuKey(menuKey))
    .filter(Boolean)
);
const menuProcessValuesMap = (
  bootstrap.menuProcessValuesMap &&
  typeof bootstrap.menuProcessValuesMap === "object" &&
  !Array.isArray(bootstrap.menuProcessValuesMap)
)
  ? bootstrap.menuProcessValuesMap
  : {};
const menuProcessHistoryMap = (
  bootstrap.menuProcessHistoryMap &&
  typeof bootstrap.menuProcessHistoryMap === "object" &&
  !Array.isArray(bootstrap.menuProcessHistoryMap)
)
  ? bootstrap.menuProcessHistoryMap
  : {};
const menuProcessQuantityValuesMap = (
  bootstrap.menuProcessQuantityValuesMap &&
  typeof bootstrap.menuProcessQuantityValuesMap === "object" &&
  !Array.isArray(bootstrap.menuProcessQuantityValuesMap)
)
  ? bootstrap.menuProcessQuantityValuesMap
  : {};
const startupHash = window.location.hash || "";
const dynamicProcessDataByMenu = appGenesisProcessMenuConfigBuilderV1
  ? appGenesisProcessMenuConfigBuilderV1.dynamicProcessDataByMenu
  : {};
const selectedDynamicSectionByMenu = appGenesisProcessMenuConfigBuilderV1
  ? appGenesisProcessMenuConfigBuilderV1.selectedDynamicSectionByMenu
  : {};
const processTextualTypes = new Set(["text", "number", "email", "phone"]);
const processSupportedTypes = new Set(["text", "number", "email", "phone", "date", "time", "flag", "list", "rows", "longtext"]);
const processSubsequentOperators = new Set(["equals", "not_equals", "is_empty", "is_not_empty"]);


function normalizeSettingsTabKey(value) {
  if (
    appGenesisProcessKeysRegistryV1 &&
    typeof appGenesisProcessKeysRegistryV1.normalizeSettingsTabKey === "function"
  ) {
    return appGenesisProcessKeysRegistryV1.normalizeSettingsTabKey(value);
  }

  const cleanTab = String(value || "")
    .trim()
    .toLowerCase()
    .replace(/_/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");

  const aliases = {
    "geral": "geral",
    "configuracao-campos": "campos-config",
    "configuracao-dos-campos": "campos-config",
    "campos-configuracao": "campos-config",
    "campos-config": "campos-config",
    "config-fields": "campos-config",
    "campos-adicionais": "campos-adicionais",
    "campos-quantidade": "campos-quantidade",
    "campos_quantidade": "campos-quantidade",
    "quantity-fields": "campos-quantidade",
    "additional-fields": "campos-adicionais",
    "adicionais": "campos-adicionais",
    "lista": "lista",
    "listas": "lista",
    "campos-subsequentes": "campos-subsequentes",
    "campos_subsequentes": "campos-subsequentes",
    "subsequentes": "campos-subsequentes",
    "subsequent": "campos-subsequentes",
    "subsequent-rules": "campos-subsequentes"
  };

  return aliases[cleanTab] || "";
}

// Cliques em controlos de formulario (campos, labels) nao devem reescrever a visibilidade:
// o foco da data/texto era perdido a cada clique e o campo piscava.
function isFormControlClickV1(event) {
  const target = event && event.target;
  return Boolean(target && target.closest && target.closest("input, select, textarea, label"));
}

function normalizeMenuKey(value) {
  if (
    appGenesisProcessKeysRegistryV1 &&
    typeof appGenesisProcessKeysRegistryV1.normalizeMenuKey === "function"
  ) {
    return appGenesisProcessKeysRegistryV1.normalizeMenuKey(value);
  }

  const cleanKey = String(value || "").trim().toLowerCase();
  if (cleanKey === LEGACY_DOCUMENTOS_MENU_KEY) {
    return MEU_PERFIL_MENU_KEY;
  }
  if (cleanKey === "configuracao") {
    return ADMINISTRATIVO_MENU_KEY_V1;
  }
  return cleanKey;
}

sidebarMenuSettings.forEach((setting) => {
  const menuKey = normalizeMenuKey(setting && setting.key);
  if (!menuKey) {
    return;
  }
  sidebarMenuSettingsByKey.set(menuKey, setting);
});

function normalizeProcessFieldType(value) {
  const cleanType = String(value || "text").trim().toLowerCase();
  if (processSupportedTypes.has(cleanType)) {
    return cleanType;
  }
  return "text";
}

function normalizeProcessFieldSize(rawSize, fieldType) {
  if (!processTextualTypes.has(fieldType)) {
    return null;
  }
  const parsedSize = Number.parseInt(String(rawSize || "").trim(), 10);
  if (!Number.isFinite(parsedSize)) {
    return 255;
  }
  return Math.min(255, Math.max(1, parsedSize));
}

function normalizeProcessFieldRequired(rawRequired) {
  if (typeof rawRequired === "boolean") {
    return rawRequired;
  }
  const cleanValue = String(rawRequired || "").trim().toLowerCase();
  return ["1", "true", "sim", "yes", "on"].includes(cleanValue);
}

function getProcessStorageKey(menuKey, fieldKey) {
  const cleanMenuKey = normalizeMenuKey(menuKey);
  const cleanFieldKey = normalizeMenuKey(fieldKey);
  if (!cleanMenuKey || !cleanFieldKey) {
    return "";
  }
  return `process__${cleanMenuKey}__${cleanFieldKey}`;
}

function toSentenceCaseText(value) {
  const cleanText = String(value || "").trim().replace(/\s+/g, " ");
  if (!cleanText) {
    return "";
  }
  const loweredText = cleanText.toLocaleLowerCase("pt-PT");
  if (loweredText.length === 1) {
    return loweredText.toLocaleUpperCase("pt-PT");
  }
  return loweredText[0].toLocaleUpperCase("pt-PT") + loweredText.slice(1);
}

function normalizeMenuLabelPreserveCase(value) {
  return String(value || "").trim().replace(/\s+/g, " ");
}

function normalizeLookupText(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function getSidebarMenuSetting(menuKey) {
  return sidebarMenuSettingsByKey.get(normalizeMenuKey(menuKey)) || null;
}

function getSidebarAdminSubprocessSettingV1(menuKey) {
  const setting = getSidebarMenuSetting(menuKey);
  if (!setting || typeof setting !== "object") {
    return null;
  }

  const subprocessKey = normalizeMenuKey(setting.admin_subprocess_key);
  const defaultTarget = normalizeTargetV1(setting.admin_subprocess_default_target);
  const editTarget = normalizeTargetV1(setting.admin_subprocess_edit_target);

  if (!subprocessKey || !defaultTarget) {
    return null;
  }

  return {
    menuKey: normalizeMenuKey(setting.key),
    subprocessKey,
    defaultTarget,
    editTarget,
    pluralLabel: normalizeMenuLabelPreserveCase(
      setting.admin_subprocess_plural_label || setting.label || ""
    ) || "Registos"
  };
}

function getSidebarAdminSubprocessMenuKeyByTargetV1(targetSelector) {
  let cleanTarget = normalizeTargetV1(targetSelector);
  if (!cleanTarget) {
    return "";
  }

  // Support active/inactive/form suffixes for dynamic/native targets
  if (cleanTarget.endsWith("-active")) {
    cleanTarget = cleanTarget.substring(0, cleanTarget.length - 7);
  } else if (cleanTarget.endsWith("-inactive")) {
    cleanTarget = cleanTarget.substring(0, cleanTarget.length - 9);
  } else if (cleanTarget.endsWith("-form-card")) {
    cleanTarget = cleanTarget.substring(0, cleanTarget.length - 10) + "-card";
  }
  const normalizedAuthorizationProfileTarget = normalizeAuthorizationProfileTargetV1(cleanTarget);
  if (normalizedAuthorizationProfileTarget) {
    cleanTarget = normalizedAuthorizationProfileTarget;
  }

  const matchingSetting = (Array.isArray(sidebarMenuSettings) ? sidebarMenuSettings : []).find((setting) => {
    const resolvedSetting = getSidebarAdminSubprocessSettingV1(setting && setting.key);
    if (!resolvedSetting) {
      return false;
    }
    return (
      cleanTarget === resolvedSetting.defaultTarget ||
      cleanTarget === resolvedSetting.editTarget ||
      normalizeTargetV1(targetSelector) === resolvedSetting.defaultTarget ||
      normalizeTargetV1(targetSelector) === resolvedSetting.editTarget
    );
  });

  return matchingSetting ? normalizeMenuKey(matchingSetting.key) : "";
}

function normalizeProcessSubsequentOperator(value) {
  const cleanOperator = String(value || "equals").trim().toLowerCase();
  return processSubsequentOperators.has(cleanOperator) ? cleanOperator : "equals";
}

function normalizeProcessSubsequentRules(rawRules) {
  if (!Array.isArray(rawRules)) {
    return [];
  }
  return rawRules
    .map((rawRule) => {
      if (!rawRule || typeof rawRule !== "object") {
        return null;
      }
      const triggerField = normalizeMenuKey(rawRule.trigger_field);
      const targetField = normalizeMenuKey(rawRule.field_key || rawRule.subsequent_field);
      if (!triggerField || !targetField) {
        return null;
      }
      const operator = normalizeProcessSubsequentOperator(rawRule.operator || rawRule.condition);
      return {
        key: normalizeMenuKey(rawRule.key),
        triggerField,
        targetField,
        operator,
        triggerValue: operator === "is_empty" || operator === "is_not_empty"
          ? ""
          : String(rawRule.trigger_value || "").trim()
      };
    })
    .filter(Boolean);
}

function isProcessSubsequentRuleSatisfied(rule, valuesByField = {}) {
  const currentValue = String(valuesByField[rule.triggerField] || "").trim();
  const normalizedCurrentValue = normalizeLookupText(currentValue);
  const normalizedRuleValue = normalizeLookupText(rule.triggerValue);
  switch (normalizeProcessSubsequentOperator(rule.operator)) {
    case "is_empty":
      return currentValue === "";
    case "is_not_empty":
      return currentValue !== "";
    case "not_equals":
      return normalizedCurrentValue !== normalizedRuleValue;
    default:
      return normalizedCurrentValue === normalizedRuleValue;
  }
}

function getHiddenProcessTargets(rules, valuesByField = {}) {
  const groupedRules = new Map();
  normalizeProcessSubsequentRules(rules).forEach((rule) => {
    if (!groupedRules.has(rule.targetField)) {
      groupedRules.set(rule.targetField, []);
    }
    groupedRules.get(rule.targetField).push(rule);
  });
  const hiddenTargets = new Set();
  groupedRules.forEach((targetRules, targetField) => {
    // Regras do mesmo alvo: basta uma cumprida para o alvo ficar visivel (OR).
    if (!targetRules.some((rule) => isProcessSubsequentRuleSatisfied(rule, valuesByField))) {
      hiddenTargets.add(targetField);
    }
  });
  return hiddenTargets;
}

function getFieldSectionMap(setting) {
  const sectionMap = new Map();
  const rows = Array.isArray(setting && setting.process_visible_field_rows)
    ? setting.process_visible_field_rows
    : [];
  rows.forEach((row) => {
    const fieldKey = normalizeMenuKey(row && row.field_key);
    if (!fieldKey) {
      return;
    }
    sectionMap.set(fieldKey, normalizeMenuKey(row && row.header_key));
  });
  return sectionMap;
}

function getProcessQuantityStorageKey(menuKey, ruleKey) {
  const cleanMenuKey = normalizeMenuKey(menuKey);
  const cleanRuleKey = normalizeMenuKey(ruleKey);
  if (!cleanMenuKey || !cleanRuleKey) {
    return "";
  }
  return `quantity__${cleanMenuKey}__${cleanRuleKey}`;
}

function normalizeProcessQuantityItems(rawItems) {
  if (!Array.isArray(rawItems)) {
    return [];
  }
  return rawItems
    .map((rawItem) => {
      if (!rawItem || typeof rawItem !== "object") {
        return null;
      }
      const normalizedItem = {};
      Object.keys(rawItem).forEach((rawKey) => {
        const cleanKey = normalizeMenuKey(rawKey);
        if (!cleanKey) {
          return;
        }
        normalizedItem[cleanKey] = String(rawItem[rawKey] || "").trim();
      });
      return normalizedItem;
    })
    .filter(Boolean);
}

function normalizeProcessQuantityRules(rawRules) {
  if (!Array.isArray(rawRules)) {
    return [];
  }
  return rawRules
    .map((rawRule, index) => {
      if (!rawRule || typeof rawRule !== "object") {
        return null;
      }
      const key = normalizeMenuKey(rawRule.key || rawRule.rule_key || rawRule.ruleKey)
        || `qty_regra_${index + 1}`;
      const label = toSentenceCaseText(rawRule.label || rawRule.rule_label || rawRule.name || "Regra");
      const quantityFieldKey = normalizeMenuKey(rawRule.quantity_field_key || rawRule.quantityFieldKey);
      const headerKey = normalizeMenuKey(rawRule.header_key || rawRule.headerKey);
      const itemLabel = toSentenceCaseText(rawRule.item_label || rawRule.itemLabel || "Item") || "Item";
      const maxItemsRaw = Number.parseInt(String(rawRule.max_items || rawRule.maxItems || "1").trim(), 10);
      const maxItems = Number.isFinite(maxItemsRaw) ? Math.min(Math.max(maxItemsRaw, 1), 50) : 1;
      const repeatedFieldKeys = Array.isArray(rawRule.repeated_field_keys || rawRule.repeatedFieldKeys)
        ? (rawRule.repeated_field_keys || rawRule.repeatedFieldKeys)
        : [];
      const cleanRepeatedFieldKeys = [];
      const seenRepeatedFieldKeys = new Set();
      repeatedFieldKeys.forEach((rawFieldKey) => {
        const cleanFieldKey = normalizeMenuKey(rawFieldKey);
        if (!cleanFieldKey || seenRepeatedFieldKeys.has(cleanFieldKey)) {
          return;
        }
        seenRepeatedFieldKeys.add(cleanFieldKey);
        cleanRepeatedFieldKeys.push(cleanFieldKey);
      });
      if (!quantityFieldKey || !cleanRepeatedFieldKeys.length) {
        return null;
      }
      return {
        key,
        label,
        quantityFieldKey,
        repeatedFieldKeys: cleanRepeatedFieldKeys,
        headerKey,
        maxItems,
        itemLabel
      };
    })
    .filter(Boolean);
}

function getProcessQuantityRepeatedFieldKeys(setting) {
  const repeatedFieldKeys = new Set();
  normalizeProcessQuantityRules(setting && setting.process_quantity_fields).forEach((rule) => {
    rule.repeatedFieldKeys.forEach((fieldKey) => {
      repeatedFieldKeys.add(fieldKey);
    });
  });
  return repeatedFieldKeys;
}

function isAbsenceProcessMenu(menuKey, menuLabel, sectionLabel) {
  const joined = [
    normalizeLookupText(menuKey),
    normalizeLookupText(menuLabel),
    normalizeLookupText(sectionLabel)
  ]
    .filter(Boolean)
    .join(" ");
  if (!joined) {
    return false;
  }
  return joined.includes("assiduidade") || joined.includes("ausencia");
}

function isAuthorizationProfileProcessMenu(menuKey, menuLabel, sectionLabel) {
  const joined = [
    normalizeLookupText(menuKey),
    normalizeLookupText(menuLabel),
    normalizeLookupText(sectionLabel)
  ]
    .filter(Boolean)
    .join(" ");
  if (!joined) {
    return false;
  }
  return joined.includes("autorizacao");
}

function isHistoryProcessMenu(menuKey, menuLabel, sectionLabel) {
  const joined = [
    normalizeLookupText(menuKey),
    normalizeLookupText(menuLabel),
    normalizeLookupText(sectionLabel)
  ]
    .filter(Boolean)
    .join(" ");
  if (!joined) {
    return false;
  }
  return (
    isAbsenceProcessMenu(menuKey, menuLabel, sectionLabel) ||
    isAuthorizationProfileProcessMenu(menuKey, menuLabel, sectionLabel) ||
    joined.includes("departamento")
  );
}

function getHistoryRecordLabels(menuKey, menuLabel, sectionLabel) {
  const joined = [
    normalizeLookupText(menuKey),
    normalizeLookupText(menuLabel),
    normalizeLookupText(sectionLabel)
  ]
    .filter(Boolean)
    .join(" ");
  if (isAbsenceProcessMenu(menuKey, menuLabel, sectionLabel)) {
    return { singular: "ausência", plural: "ausências" };
  }
  if (joined.includes("departamento")) {
    return { singular: "departamento", plural: "departamentos" };
  }
  if (isAuthorizationProfileProcessMenu(menuKey, menuLabel, sectionLabel)) {
    return { singular: "perfil", plural: "perfis" };
  }
  return { singular: "registo", plural: "registos" };
}

function getDynamicProcessLayoutConfig(setting, menuLabel, sectionLabel) {
  const resolvedMenuLabel = String(menuLabel || setting && setting.label || "").trim();
  const resolvedSectionLabel = String(sectionLabel || "").trim();
  const singularLabel = String(
    setting && setting.process_record_singular_label
      ? setting.process_record_singular_label
      : getHistoryRecordLabels(
          setting && setting.key,
          resolvedMenuLabel,
          resolvedSectionLabel
        ).singular
  ).trim() || "registo";
  const pluralLabel = String(
    setting && setting.process_record_plural_label
      ? setting.process_record_plural_label
      : getHistoryRecordLabels(
          setting && setting.key,
          resolvedMenuLabel,
          resolvedSectionLabel
        ).plural
  ).trim() || "registos";
  const activeTitle = String(
    setting && setting.process_record_active_title
      ? setting.process_record_active_title
      : `${toSentenceCaseText(pluralLabel) || "Registos"} ativos`
  ).trim() || "Registos ativos";
  const inactiveTitle = String(
    setting && setting.process_record_inactive_title
      ? setting.process_record_inactive_title
      : `${toSentenceCaseText(pluralLabel) || "Registos"} inativos`
  ).trim() || "Registos inativos";
  const emptyActiveMessage = String(
    setting && setting.process_record_empty_active_message
      ? setting.process_record_empty_active_message
      : `Sem ${pluralLabel} ativos.`
  ).trim() || "Sem registos ativos.";
  const emptyInactiveMessage = String(
    setting && setting.process_record_empty_inactive_message
      ? setting.process_record_empty_inactive_message
      : `Sem ${pluralLabel} inativos.`
  ).trim() || "Sem registos inativos.";
  const rawListColumns = Array.isArray(setting && setting.process_list_columns)
    ? setting.process_list_columns
    : [];

  return {
    layout: String(setting && setting.process_layout || "").trim().toLowerCase(),
    isListProcess: Boolean(setting && setting.is_list_process),
    singularLabel,
    pluralLabel,
    createTitle: String(
      setting && setting.process_record_create_title
        ? setting.process_record_create_title
        : `Criar ${singularLabel}`
    ).trim() || `Criar ${singularLabel}`,
    editTitle: String(
      setting && setting.process_record_edit_title
        ? setting.process_record_edit_title
        : `Editar ${singularLabel}`
    ).trim() || `Editar ${singularLabel}`,
    activeTitle,
    inactiveTitle,
    emptyActiveMessage,
    emptyInactiveMessage,
    stateEnabled: Boolean(setting && setting.process_record_state_enabled),
    showSystemColumn: Boolean(setting && setting.process_record_show_system_column),
    includeRemainingFields: Boolean(setting && setting.process_record_include_remaining_fields),
    inactiveFieldKey: normalizeMenuKey(setting && setting.process_record_inactive_field_key),
    inactiveFieldValue: String(setting && setting.process_record_inactive_field_value || "").trim().toLowerCase(),
    statusFieldKey: String(
      setting && setting.process_record_status_field_key
        ? setting.process_record_status_field_key
        : "__estado"
    ).trim() || "__estado",
    visibilityScopeLabel: String(
      setting && setting.visibility_scope_label
        ? setting.visibility_scope_label
        : setting && setting.menu_config && setting.menu_config.visibility_scope_label
          ? setting.menu_config.visibility_scope_label
          : ""
    ).trim(),
    columns: rawListColumns
      .filter((column) => column && typeof column === "object")
      .map((column) => ({
        key: String(column.key || "").trim(),
        label: String(column.label || "").trim(),
        sourceKind: String(column.source_kind || column.sourceKind || column.source || "").trim().toLowerCase(),
        fieldKey: String(column.field_key || column.fieldKey || "").trim().toLowerCase(),
        cssClass: String(column.css_class || column.cssClass || "").trim(),
        responsivePriority: Number.parseInt(column.responsive_priority || column.responsivePriority || 0, 10) || 0,
        alwaysVisible: Boolean(column.always_visible || column.alwaysVisible)
      }))
  };
}
