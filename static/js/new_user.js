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
const appGenesisProfileFieldRegistryV1 =
  window.AppGenesisProfileFieldRegistryV1 &&
  typeof window.AppGenesisProfileFieldRegistryV1 === "object"
    ? window.AppGenesisProfileFieldRegistryV1
    : null;
const appGenesisProcessSubsequentVisibilityRuntimeV1 =
  window.AppGenesisProcessSubsequentVisibilityRuntimeV1 &&
  typeof window.AppGenesisProcessSubsequentVisibilityRuntimeV1 === "object"
    ? window.AppGenesisProcessSubsequentVisibilityRuntimeV1
    : null;
const appGenesisProcessQuantityRuntimeV1 =
  window.AppGenesisProcessQuantityRuntimeV1 &&
  typeof window.AppGenesisProcessQuantityRuntimeV1 === "object"
    ? window.AppGenesisProcessQuantityRuntimeV1
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
const OBJETO_AUTORIZACAO_SUBPROCESS_KEY_V1 = appGenesisProcessReferenceRegistryV1
  ? appGenesisProcessReferenceRegistryV1.OBJETO_AUTORIZACAO_SUBPROCESS_KEY_V1
  : "objeto_de_autorizacao";
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

function logMissingNavigationRuntimeV1(moduleName) {
  if (!APPGENESIS_DEBUG_TABS_V1 || !moduleName) {
    return;
  }

  console.warn("[AppGenesis Tabs Debug] navigation runtime missing:", moduleName);
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
const meuPerfilDomain = window.AppGenesisMeuPerfilV1 || null;
const meuPerfilBootstrap = meuPerfilDomain && typeof meuPerfilDomain.getBootstrap === "function"
  ? meuPerfilDomain.getBootstrap()
  : (
    bootstrap.meuPerfil &&
    typeof bootstrap.meuPerfil === "object" &&
    !Array.isArray(bootstrap.meuPerfil)
  )
    ? bootstrap.meuPerfil
    : {};
const profilePersonalFieldLabels = (
  meuPerfilBootstrap.fieldLabels &&
  typeof meuPerfilBootstrap.fieldLabels === "object" &&
  !Array.isArray(meuPerfilBootstrap.fieldLabels)
)
  ? meuPerfilBootstrap.fieldLabels
  : {};
function getMeuPerfilPersonalCardTargetV1() {
  const bootstrapTarget = String(meuPerfilBootstrap.personalCardTarget || "").trim();
  if (bootstrapTarget) {
    return bootstrapTarget;
  }
  if (meuPerfilDomain && typeof meuPerfilDomain.resolvePersonalCardTarget === "function") {
    return meuPerfilDomain.resolvePersonalCardTarget();
  }
  return "#perfil-pessoal-card";
}
function getMeuPerfilPersonalCardElV1(root) {
  const target = getMeuPerfilPersonalCardTargetV1();
  const scope = root && typeof root.querySelector === "function" ? root : document;
  return (
    scope.querySelector(target) ||
    document.querySelector(target) ||
    document.getElementById(String(target || "").replace(/^#/, ""))
  );
}
const initialProfileTab = meuPerfilDomain && typeof meuPerfilDomain.normalizeTabKey === "function"
  ? meuPerfilDomain.normalizeTabKey(meuPerfilBootstrap.activeTab || bootstrap.initialProfileTab || "pessoal")
  : (bootstrap.initialProfileTab || "pessoal");
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
const processSupportedTypes = new Set(["text", "number", "email", "phone", "date", "time", "flag", "list"]);
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

function getCurrentProfileSectionV1(root) {
  if (
    appGenesisProfileFieldRegistryV1 &&
    typeof appGenesisProfileFieldRegistryV1.getCurrentProfileSection === "function"
  ) {
    return appGenesisProfileFieldRegistryV1.getCurrentProfileSection(root);
  }

  return "";
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
  if (
    appGenesisProcessSubsequentVisibilityRuntimeV1 &&
    typeof appGenesisProcessSubsequentVisibilityRuntimeV1.normalizeOperator === "function"
  ) {
    return appGenesisProcessSubsequentVisibilityRuntimeV1.normalizeOperator(value);
  }

  const cleanOperator = String(value || "equals").trim().toLowerCase();
  return processSubsequentOperators.has(cleanOperator) ? cleanOperator : "equals";
}

function normalizeProcessSubsequentRules(rawRules) {
  if (
    appGenesisProcessSubsequentVisibilityRuntimeV1 &&
    typeof appGenesisProcessSubsequentVisibilityRuntimeV1.normalizeRules === "function"
  ) {
    return appGenesisProcessSubsequentVisibilityRuntimeV1.normalizeRules(rawRules);
  }

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
  if (
    appGenesisProcessSubsequentVisibilityRuntimeV1 &&
    typeof appGenesisProcessSubsequentVisibilityRuntimeV1.getHiddenTargets === "function"
  ) {
    return appGenesisProcessSubsequentVisibilityRuntimeV1.getHiddenTargets(rules, valuesByField);
  }

  const groupedRules = new Map();
  normalizeProcessSubsequentRules(rules).forEach((rule) => {
    if (!groupedRules.has(rule.targetField)) {
      groupedRules.set(rule.targetField, []);
    }
    groupedRules.get(rule.targetField).push(rule);
  });
  const hiddenTargets = new Set();
  groupedRules.forEach((targetRules, targetField) => {
    if (!targetRules.every((rule) => isProcessSubsequentRuleSatisfied(rule, valuesByField))) {
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

function resolveMeuPerfilQuantitySectionKeyV1(rule, fieldSectionMap, currentSectionKey) {
  const explicitSectionKey = normalizeMenuKey(rule && (rule.sectionKey || rule.section_key || rule.section));
  if (explicitSectionKey) {
    return explicitSectionKey;
  }

  const headerKey = normalizeMenuKey(rule && (rule.headerKey || rule.header_key));
  if (headerKey) {
    return headerKey;
  }

  const repeatedFieldSections = new Set();
  const sectionMap = fieldSectionMap instanceof Map ? fieldSectionMap : new Map();
  (Array.isArray(rule && rule.repeatedFieldKeys) ? rule.repeatedFieldKeys : []).forEach((fieldKey) => {
    const cleanFieldKey = normalizeMenuKey(fieldKey);
    if (!cleanFieldKey) {
      return;
    }
    const sectionKey = normalizeMenuKey(sectionMap.get(cleanFieldKey));
    if (sectionKey) {
      repeatedFieldSections.add(sectionKey);
    }
  });

  if (repeatedFieldSections.size === 1) {
    return repeatedFieldSections.values().next().value || "";
  }

  const quantityFieldKey = normalizeMenuKey(rule && (rule.quantityFieldKey || rule.quantity_field_key));
  if (quantityFieldKey) {
    const quantityFieldSectionKey = normalizeMenuKey(sectionMap.get(quantityFieldKey));
    if (quantityFieldSectionKey) {
      return quantityFieldSectionKey;
    }
  }

  return normalizeMenuKey(currentSectionKey);
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
  if (
    appGenesisProcessQuantityRuntimeV1 &&
    typeof appGenesisProcessQuantityRuntimeV1.normalizeItems === "function"
  ) {
    return appGenesisProcessQuantityRuntimeV1.normalizeItems(rawItems);
  }

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
  if (
    appGenesisProcessQuantityRuntimeV1 &&
    typeof appGenesisProcessQuantityRuntimeV1.normalizeRules === "function"
  ) {
    return appGenesisProcessQuantityRuntimeV1.normalizeRules(rawRules);
  }

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

function buildProcessSections(setting, processValuesByField = {}) {
  const resolvedProcessSections = Array.isArray(setting && setting.process_sections)
    ? setting.process_sections
    : [];
  const processRows = Array.isArray(setting.process_visible_field_rows)
    ? setting.process_visible_field_rows
    : [];
  const visibleFieldOrder = Array.isArray(setting.process_visible_fields)
    ? setting.process_visible_fields
    : [];
  const quantityRepeatedFieldKeys = getProcessQuantityRepeatedFieldKeys(setting);
  const optionMetaByKey = new Map();
  const processListsByKey = new Map();
  const processLists = Array.isArray(setting.process_lists) ? setting.process_lists : [];
  processLists.forEach((processList) => {
    const listKey = normalizeMenuKey(processList && processList.key);
    if (!listKey) {
      return;
    }
    processListsByKey.set(
      listKey,
      Array.isArray(processList.items) ? processList.items.map((item) => String(item || "").trim()).filter(Boolean) : []
    );
  });
  const processOptions = Array.isArray(setting.process_field_options)
    ? setting.process_field_options
    : [];
  processOptions.forEach((option) => {
    const optionKey = normalizeMenuKey(option.key);
    if (!optionKey) {
      return;
    }
    const optionLabel = toSentenceCaseText(option.label) || optionKey;
    const optionType = normalizeProcessFieldType(option.field_type);
    const optionSize = normalizeProcessFieldSize(option.size, optionType);
    const optionRequiredRaw = Object.prototype.hasOwnProperty.call(option, "is_required")
      ? option.is_required
      : option.required;
    const resolvedListOptions = Array.isArray(option.list_options)
      ? option.list_options.map((item) => String(item || "").trim()).filter(Boolean)
      : [];
    const optionListKey = normalizeMenuKey(option.list_key || option.listKey);
    optionMetaByKey.set(optionKey, {
      label: optionLabel,
      fieldType: optionType,
      size: optionSize,
      listKey: optionListKey,
      listOptions: resolvedListOptions.length
        ? resolvedListOptions
        : processListsByKey.get(optionListKey) || [],
      isRequired: normalizeProcessFieldRequired(optionRequiredRaw)
    });
  });

  function buildFieldEntry(fieldKey, fieldMeta = {}) {
    const normalizedFieldType = normalizeProcessFieldType(fieldMeta.fieldType);
    const storageKey = getProcessStorageKey(setting.key, fieldKey);
    const fieldValue = processValuesByField[fieldKey];
    return {
      key: fieldKey,
      label: toSentenceCaseText(fieldMeta.label || fieldKey),
      fieldType: normalizedFieldType === "header" ? "text" : normalizedFieldType,
      size: normalizeProcessFieldSize(fieldMeta.size, normalizedFieldType),
      isRequired: Boolean(fieldMeta.isRequired),
      listKey: normalizeMenuKey(fieldMeta.listKey),
      listOptions: Array.isArray(fieldMeta.listOptions) ? fieldMeta.listOptions.slice() : [],
      value: typeof fieldValue === "string" ? fieldValue : "",
      storageKey
    };
  }

  function buildSectionsFromVisibleFieldOrder() {
    if (!visibleFieldOrder.length) {
      return [];
    }

    const sectionMap = new Map();
    const sectionOrder = [];
    const seenFieldBySection = new Map();
    let activeSectionKey = "__geral__";

    function ensureSection(sectionKey, sectionLabel) {
      const cleanSectionKey = String(sectionKey || "__geral__");
      if (!sectionMap.has(cleanSectionKey)) {
        sectionMap.set(cleanSectionKey, {
          key: cleanSectionKey,
          label: cleanSectionKey === "__geral__"
            ? "Geral"
            : toSentenceCaseText(sectionLabel || "Aba"),
          fields: []
        });
        sectionOrder.push(cleanSectionKey);
      }
      return sectionMap.get(cleanSectionKey);
    }

    visibleFieldOrder.forEach((rawFieldKey) => {
      const fieldKey = normalizeMenuKey(rawFieldKey);
      if (!fieldKey) {
        return;
      }
      if (quantityRepeatedFieldKeys.has(fieldKey)) {
        return;
      }

      const fieldMeta = optionMetaByKey.get(fieldKey) || {};
      const fieldType = normalizeProcessFieldType(fieldMeta.fieldType);
      const fieldLabel = toSentenceCaseText(fieldMeta.label || fieldKey);

      if (fieldType === "header") {
        activeSectionKey = fieldKey;
        ensureSection(fieldKey, fieldLabel);
        return;
      }

      const sectionKey = activeSectionKey || "__geral__";
      const sectionMeta = optionMetaByKey.get(sectionKey) || {};
      const sectionLabel = sectionKey === "__geral__"
        ? "Geral"
        : toSentenceCaseText(sectionMeta.label || sectionKey);
      const section = ensureSection(sectionKey, sectionLabel);
      let seenFieldKeys = seenFieldBySection.get(sectionKey);
      if (!seenFieldKeys) {
        seenFieldKeys = new Set();
        seenFieldBySection.set(sectionKey, seenFieldKeys);
      }
      if (seenFieldKeys.has(fieldKey)) {
        return;
      }
      seenFieldKeys.add(fieldKey);
      section.fields.push(buildFieldEntry(fieldKey, fieldMeta));
    });

    return sectionOrder
      .map((sectionKey) => sectionMap.get(sectionKey))
      .filter(Boolean);
  }

  if (resolvedProcessSections.length) {
    const sections = [];
    resolvedProcessSections.forEach((section) => {
      if (!section || typeof section !== "object") {
        return;
      }
      const sectionKey = normalizeMenuKey(section.key);
      if (!sectionKey) {
        return;
      }
      const sectionLabel = toSentenceCaseText(section.label || sectionKey || "Aba");
      const fieldKeys = Array.isArray(section.field_keys)
        ? section.field_keys
        : [];
      const fields = [];
      const seenFieldKeys = new Set();
      fieldKeys.forEach((rawFieldKey) => {
        const fieldKey = normalizeMenuKey(rawFieldKey);
        if (!fieldKey || seenFieldKeys.has(fieldKey)) {
          return;
        }
        if (quantityRepeatedFieldKeys.has(fieldKey)) {
          return;
        }
        const fieldMeta = optionMetaByKey.get(fieldKey) || {};
        if (normalizeProcessFieldType(fieldMeta.fieldType) === "header") {
          return;
        }
        seenFieldKeys.add(fieldKey);
        fields.push(buildFieldEntry(fieldKey, fieldMeta));
      });

      sections.push({
        key: sectionKey,
        label: sectionLabel,
        quantityRuleKeys: Array.isArray(section.quantity_rule_keys)
          ? section.quantity_rule_keys.map((item) => normalizeMenuKey(item)).filter(Boolean)
          : [],
        fields
      });
    });

    if (sections.length) {
      if (sections.length === 1 && sections[0].key === "__geral__") {
        return sections[0].fields.map((field) => ({
          key: `field:${field.key}`,
          label: field.label,
          fields: [field]
        }));
      }
      return sections;
    }
  }

  if (!processRows.length) {
    const fallbackSections = buildSectionsFromVisibleFieldOrder();
    if (fallbackSections.length === 1 && fallbackSections[0].key === "__geral__") {
      return fallbackSections[0].fields.map((field) => ({
        key: `field:${field.key}`,
        label: field.label,
        fields: [field]
      }));
    }
    return fallbackSections;
  }

  const sectionMap = new Map();
  const sectionOrder = [];
  const seenFieldBySection = new Map();

  function ensureSection(sectionKey, sectionLabel) {
    const cleanSectionKey = String(sectionKey || "__geral__");
    if (!sectionMap.has(cleanSectionKey)) {
      sectionMap.set(cleanSectionKey, {
        key: cleanSectionKey,
        label: cleanSectionKey === "__geral__"
          ? "Geral"
          : toSentenceCaseText(sectionLabel || "Aba"),
        fields: []
      });
      sectionOrder.push(cleanSectionKey);
    }
    return sectionMap.get(cleanSectionKey);
  }

  processRows.forEach((row) => {
    const fieldKey = normalizeMenuKey(row.field_key);
    if (!fieldKey) {
      return;
    }
    if (quantityRepeatedFieldKeys.has(fieldKey)) {
      return;
    }
    const headerKey = normalizeMenuKey(row.header_key);
    const sectionKey = headerKey || "__geral__";
    const sectionLabel = headerKey
      ? toSentenceCaseText((optionMetaByKey.get(headerKey) || {}).label || headerKey)
      : "Geral";
    const section = ensureSection(sectionKey, sectionLabel);
    let seenFieldKeys = seenFieldBySection.get(sectionKey);
    if (!seenFieldKeys) {
      seenFieldKeys = new Set();
      seenFieldBySection.set(sectionKey, seenFieldKeys);
    }
    if (seenFieldKeys.has(fieldKey)) {
      return;
    }
    seenFieldKeys.add(fieldKey);
    const fieldMeta = optionMetaByKey.get(fieldKey) || {};
    section.fields.push(buildFieldEntry(fieldKey, fieldMeta));
  });

  visibleFieldOrder.forEach((rawFieldKey) => {
    const fieldKey = normalizeMenuKey(rawFieldKey);
    if (!fieldKey || sectionMap.has(fieldKey)) {
      return;
    }
    const fieldMeta = optionMetaByKey.get(fieldKey) || {};
    if (normalizeProcessFieldType(fieldMeta.fieldType) !== "header") {
      return;
    }
    ensureSection(fieldKey, toSentenceCaseText(fieldMeta.label || fieldKey));
  });

  const groupedSections = sectionOrder
    .map((sectionKey) => sectionMap.get(sectionKey))
    .filter(Boolean);

  if (groupedSections.length === 1 && groupedSections[0].key === "__geral__") {
    return groupedSections[0].fields.map((field) => ({
      key: `field:${field.key}`,
      label: field.label,
      fields: [field]
    }));
  }
  return groupedSections;
}

const menuConfig = appGenesisProcessMenuConfigBuilderV1
  ? appGenesisProcessMenuConfigBuilderV1.menuConfig
  : {};

const ESTRUTURAS_MENU_KEY_V1 = appGenesisProcessKeysRegistryV1
  ? appGenesisProcessKeysRegistryV1.ESTRUTURAS_MENU_KEY_V1
  : "sessoes";
const EMPRESA_MENU_KEY_V1 = appGenesisProcessKeysRegistryV1
  ? appGenesisProcessKeysRegistryV1.EMPRESA_MENU_KEY_V1
  : "empresa";
if (
  appGenesisAdminTargetRegistryV1 &&
  typeof appGenesisAdminTargetRegistryV1.configure === "function"
) {
  appGenesisAdminTargetRegistryV1.configure({
    normalizeMenuKey,
    normalizeTarget: normalizeTargetV1,
    getSidebarAdminSubprocessSetting: getSidebarAdminSubprocessSettingV1,
    getSidebarAdminMenuKeyByTarget: getSidebarAdminSubprocessMenuKeyByTargetV1,
    ESTRUTURAS_MENU_KEY_V1,
    EMPRESA_MENU_KEY_V1
  });
}
function filterProcessExtraMenuItemsV1(dynamicItems) {
  return (Array.isArray(dynamicItems) ? dynamicItems : []).filter((item) => {
    const sectionKey = String(item && item.dynamicProcessSectionKey ? item.dynamicProcessSectionKey : "")
      .trim()
      .toLowerCase();
    if (!sectionKey) {
      return false;
    }
    return sectionKey !== "__geral__" && !sectionKey.startsWith("field:");
  });
}

function buildStructuredProcessMenuItemsV1(menuKey, dynamicItems = []) {
  if (
    appGenesisProcessMenuConfigBuilderV1 &&
    typeof appGenesisProcessMenuConfigBuilderV1.buildStructuredProcessMenuItemsV1 === "function"
  ) {
    return appGenesisProcessMenuConfigBuilderV1.buildStructuredProcessMenuItemsV1(
      menuKey,
      dynamicItems
    );
  }
  return null;
}

function mergeDynamicProcessMenus() {
  if (
    appGenesisProcessMenuConfigBuilderV1 &&
    typeof appGenesisProcessMenuConfigBuilderV1.mergeDynamicProcessMenus === "function"
  ) {
    return appGenesisProcessMenuConfigBuilderV1.mergeDynamicProcessMenus();
  }
  return menuConfig;
}

if (
  appGenesisProcessMenuConfigBuilderV1 &&
  typeof appGenesisProcessMenuConfigBuilderV1.configure === "function"
) {
  appGenesisProcessMenuConfigBuilderV1.configure({
    normalizeMenuKey,
    normalizeMenuLabelPreserveCase,
    toSentenceCaseText,
    buildProcessSections,
    meuPerfil: meuPerfilBootstrap,
    getDynamicProcessLayoutConfig,
    getSidebarAdminSubprocessSetting: getSidebarAdminSubprocessSettingV1,
    filterProcessExtraMenuItems: filterProcessExtraMenuItemsV1,
    buildMenuItemUniqueKey: buildMenuItemUniqueKey_v1,
    dashboardData,
    sidebarMenuSettings,
    visibleSidebarMenuKeys,
    menuProcessValuesMap,
    currentUserName,
    currentUserEmail,
    currentUserPhone,
    currentUserAccountStatus,
    currentUserMemberStatus,
    currentUserEntities,
    currentUserIsAdmin,
    initialMenu,
    initialDynamicProcessSection,
    MEU_PERFIL_MENU_KEY,
    ESTRUTURAS_MENU_KEY_V1,
    EMPRESA_MENU_KEY_V1,
    documentRef: document
  });
}

if (
  appGenesisProcessMenuConfigBuilderV1 &&
  typeof appGenesisProcessMenuConfigBuilderV1.initializeMenuConfig === "function"
) {
  appGenesisProcessMenuConfigBuilderV1.initializeMenuConfig();
}

const itemsEl = document.getElementById("submenu-items");
const processShellHeaderEl = document.getElementById("process-shell-header");
const processShellTitleEl = document.getElementById("process-shell-title");
const processShellActionsEl = document.getElementById("process-shell-actions");
const menuButtons = document.querySelectorAll(".menu-item");
const scopedCards = document.querySelectorAll("[data-menu-scope]");
const userMenuEl = document.getElementById("user-menu");
const userMenuTriggerEl = document.getElementById("user-menu-trigger");
const userDropdownEl = document.getElementById("user-dropdown");
const userAvatarImageEl = document.getElementById("user-avatar-image");
const dropdownAvatarImageEl = document.getElementById("dropdown-avatar-image");
const userDropdownLinks = document.querySelectorAll("[data-dropdown-target]");
const profileEditButtons = document.querySelectorAll("[data-edit-target]");
const trainingOutrosEnabledEl = document.getElementById("edit_training_outros_enabled");
const trainingOutrosInputEl = document.getElementById("edit_training_outros");
const processFieldsBuilderEl = document.getElementById("process-fields-builder");
const dynamicProcessCardEl = document.getElementById("dynamic-process-card");
const dynamicProcessActionCardEl = document.getElementById("dynamic-process-action-card");
const dynamicProcessTitleEl = document.getElementById("dynamic-process-title");
const dynamicProcessDescriptionEl = document.getElementById("dynamic-process-description");
const dynamicProcessSectionLabelEl = document.getElementById("dynamic-process-section-label");
const dynamicProcessReadOnlyGridEl = document.getElementById("dynamic-process-readonly-grid");
const dynamicProcessEditGridEl = document.getElementById("dynamic-process-edit-grid");
const dynamicProcessEditFormEl = document.getElementById("dynamic-process-edit-form");
const dynamicProcessMenuKeyInputEl = document.getElementById("dynamic-process-menu-key");
const dynamicProcessSectionKeyInputEl = document.getElementById("dynamic-process-section-key");
const dynamicProcessHistoryActionInputEl = document.getElementById("dynamic-process-history-action");
const dynamicProcessHistoryRecordIdInputEl = document.getElementById("dynamic-process-history-record-id");
const dynamicProcessHistoryRecordStateInputEl = document.getElementById("dynamic-process-history-record-state");
const dynamicProcessSubmitBtnEl = document.getElementById("dynamic-process-submit-btn");
const dynamicProcessEditToggleEl = document.getElementById("dynamic-process-edit-toggle");
const dynamicProcessEmptyEl = document.getElementById("dynamic-process-empty");
const dynamicProcessHistoryBlockEl = document.getElementById("dynamic-process-history-block");
const dynamicProcessHistoryTitleEl = document.getElementById("dynamic-process-history-title");
const dynamicProcessHistoryTableEl = document.getElementById("dynamic-process-history-table");
const dynamicProcessHistoryHeadEl = document.getElementById("dynamic-process-history-head");
const dynamicProcessHistoryBodyEl = document.getElementById("dynamic-process-history-body");
const dynamicProcessHistoryEmptyEl = document.getElementById("dynamic-process-history-empty");
const dynamicProcessActiveCardEl = document.getElementById("dynamic-process-active-card");
const dynamicProcessActiveTitleEl = document.getElementById("dynamic-process-active-title");
const dynamicProcessActiveTableEl = document.getElementById("dynamic-process-active-table");
const dynamicProcessActiveHeadEl = document.getElementById("dynamic-process-active-head");
const dynamicProcessActiveBodyEl = document.getElementById("dynamic-process-active-body");
const dynamicProcessActiveEmptyEl = document.getElementById("dynamic-process-active-empty");
const dynamicProcessActiveLimiterEl = document.getElementById("dynamic-process-active-limiter");
const dynamicProcessInactiveCardEl = document.getElementById("dynamic-process-inactive-card");
const dynamicProcessInactiveTitleEl = document.getElementById("dynamic-process-inactive-title");
const dynamicProcessInactiveTableEl = document.getElementById("dynamic-process-inactive-table");
const dynamicProcessInactiveHeadEl = document.getElementById("dynamic-process-inactive-head");
const dynamicProcessInactiveBodyEl = document.getElementById("dynamic-process-inactive-body");
const dynamicProcessInactiveEmptyEl = document.getElementById("dynamic-process-inactive-empty");
const dynamicProcessInactiveLimiterEl = document.getElementById("dynamic-process-inactive-limiter");
let homeSelectedTarget = "#home-summary-card";
let profileSelectedTarget = meuPerfilDomain && typeof meuPerfilDomain.resolveTabTarget === "function"
  ? meuPerfilDomain.resolveTabTarget(meuPerfilBootstrap.activeTab || initialProfileTab)
  : "#perfil-pessoal-card";
// APPGENESIS_ADMIN_TARGET_RESOLVER_V1_START
const NATIVE_ADMIN_TARGETS_V1 = appGenesisAdminTargetRegistryV1
  ? appGenesisAdminTargetRegistryV1.NATIVE_ADMIN_TARGETS_V1
  : new Set();
const ESTRUTURAS_NATIVE_TARGETS_V1 = appGenesisAdminTargetRegistryV1
  ? appGenesisAdminTargetRegistryV1.ESTRUTURAS_NATIVE_TARGETS_V1
  : new Set();
const EMPRESA_NATIVE_TARGETS_V1 = appGenesisAdminTargetRegistryV1
  ? appGenesisAdminTargetRegistryV1.EMPRESA_NATIVE_TARGETS_V1
  : new Set();
function normalizeTargetV1(value) {
  if (
    appGenesisProcessKeysRegistryV1 &&
    typeof appGenesisProcessKeysRegistryV1.normalizeTarget === "function"
  ) {
    return appGenesisProcessKeysRegistryV1.normalizeTarget(value);
  }

  const cleanValue = String(value || "").trim();
  if (!cleanValue) {
    return "";
  }
  return cleanValue.startsWith("#") ? cleanValue : "#" + cleanValue;
}
const AUTHORIZATION_PROFILE_TARGET_ALIAS_MAP_V1 = appGenesisAdminTargetRegistryV1
  ? appGenesisAdminTargetRegistryV1.AUTHORIZATION_PROFILE_TARGET_ALIAS_MAP_V1
  : Object.freeze({});
const AUTH_PROFILE_NATIVE_TARGETS_V1 = appGenesisAdminTargetRegistryV1
  ? appGenesisAdminTargetRegistryV1.AUTH_PROFILE_NATIVE_TARGETS_V1
  : new Set();
function normalizeAuthorizationProfileTargetV1(value) {
  if (
    appGenesisAdminTargetRegistryV1 &&
    typeof appGenesisAdminTargetRegistryV1.normalizeAuthorizationProfileTarget === "function"
  ) {
    return appGenesisAdminTargetRegistryV1.normalizeAuthorizationProfileTarget(value);
  }
  logMissingNavigationRuntimeV1("admin_target_registry_v1.normalizeAuthorizationProfileTarget");
  return "";
}
function authorizationProfileTargetsMatchV1(leftTarget, rightTarget) {
  if (
    appGenesisAdminTargetRegistryV1 &&
    typeof appGenesisAdminTargetRegistryV1.authorizationProfileTargetsMatch === "function"
  ) {
    return appGenesisAdminTargetRegistryV1.authorizationProfileTargetsMatch(leftTarget, rightTarget);
  }
  logMissingNavigationRuntimeV1("admin_target_registry_v1.authorizationProfileTargetsMatch");
  return normalizeTargetV1(leftTarget) === normalizeTargetV1(rightTarget);
}
function isNativeAdminTargetV1(value) {
  if (
    appGenesisAdminTargetRegistryV1 &&
    typeof appGenesisAdminTargetRegistryV1.isNativeAdminTarget === "function"
  ) {
    return appGenesisAdminTargetRegistryV1.isNativeAdminTarget(value);
  }
  logMissingNavigationRuntimeV1("admin_target_registry_v1.isNativeAdminTarget");
  return false;
}
function isNativeTargetForMenuV1(menuKey, value) {
  if (
    appGenesisAdminTargetRegistryV1 &&
    typeof appGenesisAdminTargetRegistryV1.isNativeTargetForMenu === "function"
  ) {
    return appGenesisAdminTargetRegistryV1.isNativeTargetForMenu(menuKey, value);
  }
  logMissingNavigationRuntimeV1("admin_target_registry_v1.isNativeTargetForMenu");
  return false;
}
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
let meuPerfilSelectedTarget = profileSelectedTarget;
let meuPerfilSelectedProfileSection = String(
  meuPerfilBootstrap.activePersonalSection ||
  meuPerfilBootstrap.activeSection ||
  ""
).trim().toLowerCase();
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
    getMeuPerfilSelectedProfileSection: () => meuPerfilSelectedProfileSection,
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
    getMeuPerfilSelectedProfileSection: () => meuPerfilSelectedProfileSection,
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
    getMeuPerfilPersonalCardTarget: getMeuPerfilPersonalCardTargetV1,
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


//###################################################################################
// (SUBMENU SUPERIOR REUTILIZAVEL) WRAPPER FINO DO CONTROLLER GENERICO
//###################################################################################

function renderHomeCharts() {
  if (!window.Chart) {
    return;
  }

  const entityCanvas = document.getElementById("home-entities-chart");
  if (entityCanvas && !entityCanvas.dataset.chartReady) {
    new Chart(entityCanvas, {
      type: "doughnut",
      data: {
        labels: (dashboardData.entity_status || {}).labels || [],
        datasets: [
          {
            data: (dashboardData.entity_status || {}).values || [],
            backgroundColor: ["#1f7a49", "#d07a31"],
            borderColor: "#ffffff",
            borderWidth: 2
          }
        ]
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } }
      }
    });
    entityCanvas.dataset.chartReady = "1";
  }

  const profileCanvas = document.getElementById("home-profiles-chart");
  if (profileCanvas && !profileCanvas.dataset.chartReady) {
    new Chart(profileCanvas, {
      type: "bar",
      data: {
        labels: (dashboardData.users_by_profile || {}).labels || [],
        datasets: [
          {
            label: "Utilizadores",
            data: (dashboardData.users_by_profile || {}).values || [],
            backgroundColor: ["#2f6db4", "#3f84d6", "#58a3ec"],
            borderRadius: 7,
            maxBarThickness: 62
          }
        ]
      },
      options: {
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0 }
          }
        },
        plugins: { legend: { display: false } }
      }
    });
    profileCanvas.dataset.chartReady = "1";
  }
}

function getInitials(name) {
  const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) {
    return "U";
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function buildAvatarDataUri(name) {
  const initials = getInitials(name);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#3777dc"/>
          <stop offset="100%" stop-color="#244ea5"/>
        </linearGradient>
      </defs>
      <rect width="96" height="96" rx="48" fill="url(#g)"/>
      <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="700">${initials}</text>
    </svg>
  `;
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}

function closeUserDropdown() {
  if (!userDropdownEl || !userMenuTriggerEl) {
    return;
  }
  userDropdownEl.hidden = true;
  userMenuTriggerEl.setAttribute("aria-expanded", "false");
}

function openUserDropdown() {
  if (!userDropdownEl || !userMenuTriggerEl) {
    return;
  }
  userDropdownEl.hidden = false;
  userMenuTriggerEl.setAttribute("aria-expanded", "true");
}

function toggleUserDropdown() {
  if (!userDropdownEl || !userMenuTriggerEl) {
    return;
  }
  const expanded = userMenuTriggerEl.getAttribute("aria-expanded") === "true";
  if (expanded) {
    closeUserDropdown();
  } else {
    openUserDropdown();
  }
}

function isTruthyFlagValue(value) {
  const cleanValue = String(value || "").trim().toLowerCase();
  return ["1", "true", "sim", "yes", "on"].includes(cleanValue);
}

function getDynamicProcessInputType(fieldType) {
  if (fieldType === "email") {
    return "email";
  }
  if (fieldType === "number") {
    return "number";
  }
  if (fieldType === "phone") {
    return "tel";
  }
  if (fieldType === "date") {
    return "date";
  }
  if (fieldType === "time") {
    return "time";
  }
  return "text";
}

function normalizeDateInputValue(rawValue) {
  const cleanValue = String(rawValue || "").trim();
  if (!cleanValue) {
    return "";
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(cleanValue)) {
    return cleanValue;
  }
  const slashMatch = cleanValue.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (slashMatch) {
    const [, day, month, year] = slashMatch;
    return `${year}-${month}-${day}`;
  }
  return "";
}

function isStartDateField(field) {
  const joined = `${normalizeLookupText(field.key)} ${normalizeLookupText(field.label)}`.trim();
  if (!joined) {
    return false;
  }
  return joined.includes("data inicio") || joined.includes(" inicio") || joined.endsWith("inicio");
}

function isEndDateField(field) {
  const joined = `${normalizeLookupText(field.key)} ${normalizeLookupText(field.label)}`.trim();
  if (!joined) {
    return false;
  }
  return joined.includes("data fim") || joined.includes(" fim") || joined.endsWith("fim");
}

function setupAbsenceDateRangeValidation(sectionFields, inputsByFieldKey) {
  if (!Array.isArray(sectionFields) || !inputsByFieldKey || typeof inputsByFieldKey.get !== "function") {
    return;
  }
  let startDateInputEl = null;
  let endDateInputEl = null;
  sectionFields.forEach((field) => {
    if (normalizeProcessFieldType(field.fieldType) !== "date") {
      return;
    }
    const inputEl = inputsByFieldKey.get(normalizeMenuKey(field.key));
    if (!inputEl) {
      return;
    }
    if (!startDateInputEl && isStartDateField(field)) {
      startDateInputEl = inputEl;
    }
    if (!endDateInputEl && isEndDateField(field)) {
      endDateInputEl = inputEl;
    }
  });
  if (!startDateInputEl || !endDateInputEl) {
    return;
  }

  const syncDateRangeRule = () => {
    const startDateValue = normalizeDateInputValue(startDateInputEl.value);
    const endDateValue = normalizeDateInputValue(endDateInputEl.value);
    if (startDateValue) {
      endDateInputEl.min = startDateValue;
    } else {
      endDateInputEl.removeAttribute("min");
    }
    if (startDateValue && endDateValue && endDateValue < startDateValue) {
      endDateInputEl.setCustomValidity("Data fim não pode ser menor que a data início.");
    } else {
      endDateInputEl.setCustomValidity("");
    }
  };

  startDateInputEl.addEventListener("input", syncDateRangeRule);
  endDateInputEl.addEventListener("input", syncDateRangeRule);
  syncDateRangeRule();
}

function renderDynamicProcessHistory(menuKey, sectionKey, sectionLabel, sectionFields, recordLabels) {
  if (
    !dynamicProcessHistoryBlockEl ||
    !dynamicProcessHistoryTableEl ||
    !dynamicProcessHistoryHeadEl ||
    !dynamicProcessHistoryBodyEl ||
    !dynamicProcessHistoryEmptyEl
  ) {
    return;
  }

  const cleanMenuKey = normalizeMenuKey(menuKey);
  const cleanSectionKey = String(sectionKey || "").trim();
  const historyRowsRaw = Array.isArray(menuProcessHistoryMap[cleanMenuKey])
    ? menuProcessHistoryMap[cleanMenuKey]
    : [];
  const historyRows = historyRowsRaw.filter((item) => item && typeof item === "object");
  const visibleRows = historyRows.filter((item) => {
    const rowSectionKey = String(item.section_key || "").trim();
    if (!cleanSectionKey) {
      return true;
    }
    if (!rowSectionKey) {
      return true;
    }
    return rowSectionKey === cleanSectionKey;
  });

  dynamicProcessHistoryHeadEl.innerHTML = "";
  dynamicProcessHistoryBodyEl.innerHTML = "";

  const normalizedFields = Array.isArray(sectionFields)
    ? sectionFields.filter((field) => field && typeof field === "object")
    : [];
  const tableFields = normalizedFields.filter((field) => String(field.key || "").trim());
  const showStateColumn = String(recordLabels.singular || "") === "departamento";

  if (!tableFields.length || !visibleRows.length) {
    dynamicProcessHistoryTableEl.style.display = "none";
    dynamicProcessHistoryEmptyEl.style.display = "";
    dynamicProcessHistoryEmptyEl.textContent = `Sem ${recordLabels.plural} criados.`;
    dynamicProcessHistoryBlockEl.style.display = "";
    if (dynamicProcessHistoryTitleEl) {
      dynamicProcessHistoryTitleEl.textContent = `Lista de ${recordLabels.plural} criados`;
    }
    return;
  }

  const headRowEl = document.createElement("tr");
  const createdHeadEl = document.createElement("th");
  createdHeadEl.textContent = "Criado em";
  headRowEl.appendChild(createdHeadEl);
  tableFields.forEach((field) => {
    const thEl = document.createElement("th");
    thEl.textContent = toSentenceCaseText(field.label || field.key);
    headRowEl.appendChild(thEl);
  });
  if (showStateColumn) {
    const stateHeadEl = document.createElement("th");
    stateHeadEl.textContent = "Estado";
    headRowEl.appendChild(stateHeadEl);
  }
  const actionsHeadEl = document.createElement("th");
  actionsHeadEl.textContent = "Ações";
  headRowEl.appendChild(actionsHeadEl);
  dynamicProcessHistoryHeadEl.appendChild(headRowEl);

  visibleRows.forEach((row) => {
    const trEl = document.createElement("tr");
    const rowRecordId = String(row.record_id || "").trim();

    const createdCellEl = document.createElement("td");
    createdCellEl.textContent = String(row.created_at || "-").trim() || "-";
    trEl.appendChild(createdCellEl);

    const values = row.values && typeof row.values === "object" ? row.values : {};
    tableFields.forEach((field) => {
      const fieldKey = normalizeMenuKey(field.key);
      const tdEl = document.createElement("td");
      const rawValue = String(values[fieldKey] || "").trim();
      if (normalizeProcessFieldType(field.fieldType) === "flag") {
        tdEl.textContent = isTruthyFlagValue(rawValue) ? "Sim" : "Não";
      } else {
        tdEl.textContent = rawValue || "-";
      }
      trEl.appendChild(tdEl);
    });
    if (showStateColumn) {
      const stateCellEl = document.createElement("td");
      const rawStateValue = normalizeLookupText(values.__estado || "");
      stateCellEl.textContent = rawStateValue === "inativo" ? "Inativo" : "Ativo";
      trEl.appendChild(stateCellEl);
    }

    const actionsCellEl = document.createElement("td");
    const actionsWrapEl = document.createElement("div");
    actionsWrapEl.className = "table-actions";

    const editBtnEl = document.createElement("button");
    editBtnEl.type = "button";
    editBtnEl.className = "table-icon-btn";
    editBtnEl.title = `Editar ${recordLabels.singular}`;
    editBtnEl.setAttribute("aria-label", `Editar ${recordLabels.singular}`);
    editBtnEl.innerHTML = "&#9998;";
    editBtnEl.disabled = !rowRecordId;
    editBtnEl.addEventListener("click", () => {
      if (!rowRecordId || !dynamicProcessEditFormEl) {
        return;
      }
      if (dynamicProcessHistoryActionInputEl) {
        dynamicProcessHistoryActionInputEl.value = "update";
      }
      if (dynamicProcessHistoryRecordIdInputEl) {
        dynamicProcessHistoryRecordIdInputEl.value = rowRecordId;
      }
      if (dynamicProcessSubmitBtnEl) {
        dynamicProcessSubmitBtnEl.textContent = "Guardar";
      }
      if (dynamicProcessCardEl) {
        dynamicProcessCardEl.classList.add("editing");
      }

      const values = row.values && typeof row.values === "object" ? row.values : {};
      tableFields.forEach((field) => {
        const fieldKey = normalizeMenuKey(field.key);
        if (!fieldKey) {
          return;
        }
        const inputName = `process_field__${fieldKey}`;
        const inputEl = dynamicProcessEditFormEl.querySelector(`[name="${inputName}"]`);
        if (!inputEl) {
          return;
        }
        const rawValue = String(values[fieldKey] || "").trim();
        if (inputEl.type === "checkbox") {
          const normalizedFlag = isTruthyFlagValue(rawValue);
          inputEl.checked = normalizedFlag;
          inputEl.dispatchEvent(new Event("input", { bubbles: true }));
          return;
        }
        let normalizedValue = rawValue;
        if (normalizeProcessFieldType(field.fieldType) === "date") {
          normalizedValue = normalizeDateInputValue(rawValue);
        }
        inputEl.value = normalizedValue;
        inputEl.dispatchEvent(new Event("input", { bubbles: true }));
      });
      if (showStateColumn) {
        const stateSelectEl = dynamicProcessEditFormEl.querySelector("[name='process_state']");
        if (stateSelectEl) {
          const rawStateValue = normalizeLookupText(values.__estado || "");
          stateSelectEl.value = rawStateValue === "inativo" ? "inativo" : "ativo";
        }
      }

      dynamicProcessEditFormEl.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    actionsWrapEl.appendChild(editBtnEl);

    const deleteBtnEl = document.createElement("button");
    deleteBtnEl.type = "button";
    deleteBtnEl.className = "table-icon-btn table-icon-btn-danger";
    deleteBtnEl.title = `Eliminar ${recordLabels.singular}`;
    deleteBtnEl.setAttribute("aria-label", `Eliminar ${recordLabels.singular}`);
    deleteBtnEl.innerHTML = "&#128465;";
    deleteBtnEl.disabled = !rowRecordId;
    deleteBtnEl.addEventListener("click", () => {
      if (!rowRecordId || !dynamicProcessEditFormEl) {
        return;
      }
      if (!window.confirm(`Deseja eliminar este ${recordLabels.singular}?`)) {
        return;
      }
      if (dynamicProcessHistoryActionInputEl) {
        dynamicProcessHistoryActionInputEl.value = "delete";
      }
      if (dynamicProcessHistoryRecordIdInputEl) {
        dynamicProcessHistoryRecordIdInputEl.value = rowRecordId;
      }
      dynamicProcessEditFormEl.submit();
    });
    actionsWrapEl.appendChild(deleteBtnEl);

    actionsCellEl.appendChild(actionsWrapEl);
    trEl.appendChild(actionsCellEl);

    dynamicProcessHistoryBodyEl.appendChild(trEl);
  });

  dynamicProcessHistoryTableEl.style.display = "";
  dynamicProcessHistoryEmptyEl.style.display = "none";
  dynamicProcessHistoryBlockEl.style.display = "";
  if (dynamicProcessHistoryTitleEl) {
    dynamicProcessHistoryTitleEl.textContent = `Lista de ${recordLabels.plural} criados`;
  }
}

function normalizeDynamicProcessRecordState(rawValue) {
  const cleanValue = normalizeLookupText(rawValue || "");
  if (
    cleanValue === "inativo" ||
    cleanValue === "inactive" ||
    cleanValue === "0" ||
    cleanValue === "false" ||
    cleanValue === "off"
  ) {
    return "inativo";
  }
  return "ativo";
}

function getDynamicProcessRecordState(row, layoutConfig) {
  const values = row && row.values && typeof row.values === "object" ? row.values : {};
  const statusFieldKey = normalizeMenuKey(layoutConfig && layoutConfig.statusFieldKey || "__estado") || "__estado";
  return normalizeDynamicProcessRecordState(values[statusFieldKey]);
}

function splitDynamicProcessListRows(rows, layoutConfig) {
  const normalizedRows = Array.isArray(rows) ? rows.filter((row) => row && typeof row === "object") : [];
  return normalizedRows.reduce((accumulator, row) => {
    if (!layoutConfig || !layoutConfig.stateEnabled) {
      accumulator.active.push(row);
      return accumulator;
    }
    if (getDynamicProcessRecordState(row, layoutConfig) === "inativo") {
      accumulator.inactive.push(row);
    } else {
      accumulator.active.push(row);
    }
    return accumulator;
  }, { active: [], inactive: [] });
}

function resetDynamicProcessListCardsV1() {
  [
    dynamicProcessActiveCardEl,
    dynamicProcessInactiveCardEl
  ].forEach((cardEl) => {
    if (cardEl) {
      cardEl.style.display = "none";
    }
  });
  [
    dynamicProcessActiveHeadEl,
    dynamicProcessActiveBodyEl,
    dynamicProcessInactiveHeadEl,
    dynamicProcessInactiveBodyEl
  ].forEach((sectionEl) => {
    if (sectionEl) {
      sectionEl.innerHTML = "";
    }
  });
  [
    dynamicProcessActiveEmptyEl,
    dynamicProcessInactiveEmptyEl
  ].forEach((emptyEl) => {
    if (emptyEl) {
      emptyEl.style.display = "none";
    }
  });
  [
    dynamicProcessActiveLimiterEl,
    dynamicProcessInactiveLimiterEl
  ].forEach((limiterEl) => {
    if (limiterEl) {
      limiterEl.style.display = "none";
      limiterEl.innerHTML = "";
    }
  });
}

function populateDynamicProcessListFormV1(sectionFields, row, layoutConfig) {
  if (!dynamicProcessEditFormEl) {
    return;
  }

  dynamicProcessEditFormEl.reset();
  const values = row && row.values && typeof row.values === "object" ? row.values : {};
  if (dynamicProcessHistoryActionInputEl) {
    dynamicProcessHistoryActionInputEl.value = "update";
  }
  if (dynamicProcessHistoryRecordIdInputEl) {
    dynamicProcessHistoryRecordIdInputEl.value = String(row && row.record_id || "").trim();
  }
  if (dynamicProcessHistoryRecordStateInputEl) {
    dynamicProcessHistoryRecordStateInputEl.value = "";
  }
  if (dynamicProcessSubmitBtnEl) {
    dynamicProcessSubmitBtnEl.textContent = "Guardar";
  }
  if (dynamicProcessCardEl) {
    dynamicProcessCardEl.classList.add("editing");
  }
  if (dynamicProcessTitleEl) {
    dynamicProcessTitleEl.textContent = layoutConfig && layoutConfig.editTitle
      ? layoutConfig.editTitle
      : "Editar registo";
  }

  sectionFields.forEach((field) => {
    const fieldKey = normalizeMenuKey(field && field.key);
    if (!fieldKey) {
      return;
    }
    const inputEl = dynamicProcessEditFormEl.querySelector(`[name="process_field__${fieldKey}"]`);
    if (!inputEl) {
      return;
    }
    const rawValue = String(values[fieldKey] || "").trim();
    if (inputEl.type === "checkbox") {
      inputEl.checked = isTruthyFlagValue(rawValue);
      inputEl.dispatchEvent(new Event("input", { bubbles: true }));
      return;
    }
    const normalizedValue = normalizeProcessFieldType(field && field.fieldType) === "date"
      ? normalizeDateInputValue(rawValue)
      : rawValue;
    inputEl.value = normalizedValue;
    inputEl.dispatchEvent(new Event("input", { bubbles: true }));
  });

  if (layoutConfig && layoutConfig.stateEnabled) {
    const stateSelectEl = dynamicProcessEditFormEl.querySelector("[name='process_state']");
    if (stateSelectEl) {
      stateSelectEl.value = getDynamicProcessRecordState(row, layoutConfig);
    }
  }

  dynamicProcessEditFormEl.scrollIntoView({ behavior: "smooth", block: "start" });
}

function submitDynamicProcessListRecordStateV1(rowRecordId, nextState) {
  if (!dynamicProcessEditFormEl || !rowRecordId) {
    return;
  }
  if (dynamicProcessHistoryActionInputEl) {
    dynamicProcessHistoryActionInputEl.value = "toggle_status";
  }
  if (dynamicProcessHistoryRecordIdInputEl) {
    dynamicProcessHistoryRecordIdInputEl.value = rowRecordId;
  }
  if (dynamicProcessHistoryRecordStateInputEl) {
    dynamicProcessHistoryRecordStateInputEl.value = nextState;
  }
  dynamicProcessEditFormEl.submit();
}

function submitDynamicProcessListRecordDeleteV1(rowRecordId, singularLabel) {
  if (!dynamicProcessEditFormEl || !rowRecordId) {
    return;
  }
  if (!window.confirm(`Deseja eliminar este ${singularLabel}?`)) {
    return;
  }
  if (dynamicProcessHistoryActionInputEl) {
    dynamicProcessHistoryActionInputEl.value = "delete";
  }
  if (dynamicProcessHistoryRecordIdInputEl) {
    dynamicProcessHistoryRecordIdInputEl.value = rowRecordId;
  }
  if (dynamicProcessHistoryRecordStateInputEl) {
    dynamicProcessHistoryRecordStateInputEl.value = "";
  }
  dynamicProcessEditFormEl.submit();
}

function normalizeDynamicProcessListColumnSourceV1(rawValue) {
  const normalizedValue = normalizeLookupText(rawValue || "");
  if (
    normalizedValue === "field" ||
    normalizedValue === "visible_field" ||
    normalizedValue === "field_value" ||
    normalizedValue === "campo"
  ) {
    return "field";
  }
  if (
    normalizedValue === "menu_visibility_scope" ||
    normalizedValue === "visibility_scope" ||
    normalizedValue === "scope" ||
    normalizedValue === "system" ||
    normalizedValue === "sistema"
  ) {
    return "menu_visibility_scope";
  }
  if (normalizedValue === "status" || normalizedValue === "estado") {
    return "status";
  }
  return "";
}

function resolveDynamicProcessListColumnsV1(sectionFields, layoutConfig) {
  const availableFields = Array.isArray(sectionFields)
    ? sectionFields.filter((field) => field && normalizeMenuKey(field.key))
    : [];
  const availableFieldsByKey = new Map(
    availableFields.map((field) => [normalizeMenuKey(field.key), field])
  );
  const configuredColumns = Array.isArray(layoutConfig && layoutConfig.columns)
    ? layoutConfig.columns
    : [];
  const resolvedColumns = [];
  const emittedColumnKeys = new Set();
  const usedFieldKeys = new Set();
  let hasFieldColumn = false;
  let hasSystemColumn = false;
  let hasStatusColumn = false;

  function appendFieldColumn(fieldKey, column, defaultCssClass, defaultAlwaysVisible) {
    const normalizedFieldKey = normalizeMenuKey(fieldKey);
    const fieldMeta = normalizedFieldKey
      ? availableFieldsByKey.get(normalizedFieldKey)
      : null;
    if (!fieldMeta) {
      return false;
    }
    const columnKey = normalizeMenuKey(column && column.key) || normalizedFieldKey;
    if (!columnKey || emittedColumnKeys.has(columnKey)) {
      return false;
    }
    emittedColumnKeys.add(columnKey);
    usedFieldKeys.add(normalizedFieldKey);
    hasFieldColumn = true;
    resolvedColumns.push({
      key: columnKey,
      label: String(
        column && column.label
          ? column.label
          : fieldMeta && fieldMeta.label
            ? fieldMeta.label
            : fieldMeta && fieldMeta.key
              ? fieldMeta.key
              : "Campo"
      ).trim() || "Campo",
      sourceKind: "field",
      fieldKey: normalizedFieldKey,
      fieldType: normalizeProcessFieldType(fieldMeta && fieldMeta.fieldType),
      cssClass: String(column && column.cssClass || defaultCssClass || "").trim(),
      responsivePriority: Number.parseInt(
        column && column.responsivePriority || 0,
        10
      ) || 0,
      alwaysVisible: Boolean(
        column && typeof column.alwaysVisible === "boolean"
          ? column.alwaysVisible
          : defaultAlwaysVisible
      )
    });
    return true;
  }

  configuredColumns.forEach((column) => {
    if (!column || typeof column !== "object") {
      return;
    }
    const sourceKind = normalizeDynamicProcessListColumnSourceV1(
      column.sourceKind || column.source
    );
    if (!sourceKind) {
      return;
    }
    if (sourceKind === "field") {
      const explicitFieldKey = normalizeMenuKey(column.fieldKey);
      if (explicitFieldKey) {
        appendFieldColumn(explicitFieldKey, column, "admin-col-main-v1", !hasFieldColumn);
        return;
      }
      const nextField = availableFields.find((field) => !usedFieldKeys.has(normalizeMenuKey(field.key)));
      if (nextField) {
        appendFieldColumn(nextField.key, column, "admin-col-main-v1", !hasFieldColumn);
      }
      return;
    }
    if (sourceKind === "menu_visibility_scope") {
      const columnKey = normalizeMenuKey(column.key) || "system";
      if (emittedColumnKeys.has(columnKey)) {
        return;
      }
      emittedColumnKeys.add(columnKey);
      hasSystemColumn = true;
      resolvedColumns.push({
        key: columnKey,
        label: String(column.label || "Sistema").trim() || "Sistema",
        sourceKind,
        cssClass: String(column.cssClass || "admin-col-system-v1").trim() || "admin-col-system-v1",
        responsivePriority: Number.parseInt(column.responsivePriority || 0, 10) || 0,
        alwaysVisible: Boolean(column.alwaysVisible)
      });
      return;
    }
    if (sourceKind === "status" && layoutConfig && layoutConfig.stateEnabled) {
      const columnKey = normalizeMenuKey(column.key) || "status";
      if (emittedColumnKeys.has(columnKey)) {
        return;
      }
      emittedColumnKeys.add(columnKey);
      hasStatusColumn = true;
      resolvedColumns.push({
        key: columnKey,
        label: String(column.label || "Estado").trim() || "Estado",
        sourceKind,
        cssClass: String(column.cssClass || "admin-col-status-v1").trim() || "admin-col-status-v1",
        responsivePriority: Number.parseInt(column.responsivePriority || 0, 10) || 0,
        alwaysVisible: true
      });
    }
  });

  if (!hasFieldColumn && availableFields.length) {
    appendFieldColumn(availableFields[0].key, {}, "admin-col-main-v1", true);
  }

  if (layoutConfig && layoutConfig.includeRemainingFields) {
    availableFields.forEach((field, index) => {
      const fieldKey = normalizeMenuKey(field && field.key);
      if (!fieldKey || usedFieldKeys.has(fieldKey)) {
        return;
      }
      appendFieldColumn(fieldKey, {
        responsivePriority: index + 2
      }, "", false);
    });
  }

  if (!hasSystemColumn && layoutConfig && layoutConfig.showSystemColumn) {
    resolvedColumns.push({
      key: "system",
      label: "Sistema",
      sourceKind: "menu_visibility_scope",
      cssClass: "admin-col-system-v1",
      responsivePriority: 2,
      alwaysVisible: false
    });
    hasSystemColumn = true;
  }

  if (!hasStatusColumn && layoutConfig && layoutConfig.stateEnabled) {
    resolvedColumns.push({
      key: "status",
      label: "Estado",
      sourceKind: "status",
      cssClass: "admin-col-status-v1",
      responsivePriority: 0,
      alwaysVisible: true
    });
  }

  return resolvedColumns;
}

function resolveDynamicProcessListCellTextV1(row, column, layoutConfig) {
  const values = row && row.values && typeof row.values === "object" ? row.values : {};
  if (!column || typeof column !== "object") {
    return "-";
  }
  if (column.sourceKind === "menu_visibility_scope") {
    return String(layoutConfig && layoutConfig.visibilityScopeLabel || "").trim() || "-";
  }
  if (column.sourceKind === "status") {
    return getDynamicProcessRecordState(row, layoutConfig) === "inativo" ? "Inativo" : "Ativo";
  }
  if (column.sourceKind === "field") {
    const rawValue = String(values[normalizeMenuKey(column.fieldKey)] || "").trim();
    return column.fieldType === "flag"
      ? (isTruthyFlagValue(rawValue) ? "Sim" : "Não")
      : (rawValue || "-");
  }
  return "-";
}

function appendDynamicProcessListCellV1(trEl, row, column, layoutConfig) {
  if (!trEl || !column) {
    return;
  }
  const tdEl = document.createElement("td");
  if (column.cssClass) {
    tdEl.className = column.cssClass;
  }
  tdEl.setAttribute("data-admin-column-key", column.key || "");
  if (column.responsivePriority) {
    tdEl.setAttribute("data-admin-responsive-priority", String(column.responsivePriority));
  }
  if (column.alwaysVisible) {
    tdEl.setAttribute("data-admin-always-visible", "1");
  }

  if (column.sourceKind === "status") {
    const normalizedState = getDynamicProcessRecordState(row, layoutConfig);
    const badgeEl = document.createElement("span");
    badgeEl.className = normalizedState === "inativo"
      ? "admin-subprocess-badge-v1 admin-subprocess-badge-inactive-v1"
      : "admin-subprocess-badge-v1 admin-subprocess-badge-active-v1";
    badgeEl.textContent = normalizedState === "inativo" ? "Inativo" : "Ativo";
    tdEl.appendChild(badgeEl);
    trEl.appendChild(tdEl);
    return;
  }

  tdEl.textContent = resolveDynamicProcessListCellTextV1(row, column, layoutConfig);
  trEl.appendChild(tdEl);
}

function createDynamicProcessListActionsCellV1(row, sectionFields, layoutConfig) {
  const rowRecordId = String(row && row.record_id || "").trim();
  const actionsCellEl = document.createElement("td");
  actionsCellEl.className = "admin-col-actions-v1";
  actionsCellEl.setAttribute("data-admin-column-key", "actions");
  actionsCellEl.setAttribute("data-admin-always-visible", "1");

  const actionsWrapEl = document.createElement("div");
  actionsWrapEl.className = "table-actions admin-subprocess-row-actions-v1";

  const editBtnEl = document.createElement("button");
  editBtnEl.type = "button";
  editBtnEl.className = "admin-subprocess-action-btn-v1";
  editBtnEl.title = `Editar ${layoutConfig.singularLabel}`;
  editBtnEl.setAttribute("aria-label", `Editar ${layoutConfig.singularLabel}`);
  editBtnEl.innerHTML = "&#9998;";
  editBtnEl.disabled = !rowRecordId;
  editBtnEl.addEventListener("click", () => {
    if (!rowRecordId) {
      return;
    }
    populateDynamicProcessListFormV1(sectionFields, row, layoutConfig);
  });
  actionsWrapEl.appendChild(editBtnEl);

  if (layoutConfig.stateEnabled) {
    const currentState = getDynamicProcessRecordState(row, layoutConfig);
    const nextState = currentState === "inativo" ? "ativo" : "inativo";
    const toggleBtnEl = document.createElement("button");
    toggleBtnEl.type = "button";
    toggleBtnEl.className = "admin-subprocess-action-btn-v1";
    toggleBtnEl.title = nextState === "ativo"
      ? `Ativar ${layoutConfig.singularLabel}`
      : `Inativar ${layoutConfig.singularLabel}`;
    toggleBtnEl.setAttribute("aria-label", toggleBtnEl.title);
    toggleBtnEl.innerHTML = nextState === "ativo" ? "&#8635;" : "&#9208;";
    toggleBtnEl.disabled = !rowRecordId;
    toggleBtnEl.addEventListener("click", () => {
      submitDynamicProcessListRecordStateV1(rowRecordId, nextState);
    });
    actionsWrapEl.appendChild(toggleBtnEl);
  }

  if (getDynamicProcessRecordState(row, layoutConfig) === "inativo") {
    const deleteBtnEl = document.createElement("button");
    deleteBtnEl.type = "button";
    deleteBtnEl.className = "admin-subprocess-action-btn-v1 admin-subprocess-action-btn-danger-v1";
    deleteBtnEl.title = `Eliminar ${layoutConfig.singularLabel}`;
    deleteBtnEl.setAttribute("aria-label", `Eliminar ${layoutConfig.singularLabel}`);
    deleteBtnEl.innerHTML = "&#128465;";
    deleteBtnEl.disabled = !rowRecordId;
    deleteBtnEl.addEventListener("click", () => {
      submitDynamicProcessListRecordDeleteV1(rowRecordId, layoutConfig.singularLabel);
    });
    actionsWrapEl.appendChild(deleteBtnEl);
  }

  actionsCellEl.appendChild(actionsWrapEl);
  return actionsCellEl;
}

function renderDynamicProcessListTableCardV1(options) {
  const safeOptions = options && typeof options === "object" ? options : {};
  const cardEl = safeOptions.cardEl;
  const titleEl = safeOptions.titleEl;
  const tableEl = safeOptions.tableEl;
  const headEl = safeOptions.headEl;
  const bodyEl = safeOptions.bodyEl;
  const emptyEl = safeOptions.emptyEl;
  const limiterEl = safeOptions.limiterEl;
  const rows = Array.isArray(safeOptions.rows) ? safeOptions.rows : [];
  const sectionFields = Array.isArray(safeOptions.sectionFields) ? safeOptions.sectionFields : [];
  const layoutConfig = safeOptions.layoutConfig || {};
  const title = String(safeOptions.title || "").trim();
  const emptyMessage = String(safeOptions.emptyMessage || "").trim();
  const resolvedColumns = resolveDynamicProcessListColumnsV1(sectionFields, layoutConfig);

  if (!cardEl || !tableEl || !headEl || !bodyEl || !emptyEl) {
    return;
  }

  if (titleEl) {
    titleEl.textContent = title;
  }

  headEl.innerHTML = "";
  bodyEl.innerHTML = "";
  emptyEl.textContent = emptyMessage;
  cardEl.style.display = "";

  const headerRowEl = document.createElement("tr");
  resolvedColumns.forEach((column) => {
    const thEl = document.createElement("th");
    if (column.cssClass) {
      thEl.className = column.cssClass;
    }
    thEl.setAttribute("data-admin-column-key", column.key || "");
    if (column.responsivePriority) {
      thEl.setAttribute("data-admin-responsive-priority", String(column.responsivePriority));
    }
    if (column.alwaysVisible) {
      thEl.setAttribute("data-admin-always-visible", "1");
    }
    thEl.textContent = String(column.label || "Campo").trim() || "Campo";
    headerRowEl.appendChild(thEl);
  });

  const actionsHeadEl = document.createElement("th");
  actionsHeadEl.className = "admin-col-actions-v1";
  actionsHeadEl.setAttribute("data-admin-column-key", "actions");
  actionsHeadEl.setAttribute("data-admin-always-visible", "1");
  actionsHeadEl.textContent = "AÇÕES";
  headerRowEl.appendChild(actionsHeadEl);
  headEl.appendChild(headerRowEl);

  rows.forEach((row) => {
    const trEl = document.createElement("tr");
    resolvedColumns.forEach((column) => {
      appendDynamicProcessListCellV1(trEl, row, column, layoutConfig);
    });

    trEl.appendChild(
      createDynamicProcessListActionsCellV1(row, sectionFields, layoutConfig)
    );
    bodyEl.appendChild(trEl);
  });

  tableEl.style.display = "";
  emptyEl.style.display = rows.length ? "none" : "";
  if (limiterEl) {
    limiterEl.style.display = "";
    limiterEl.innerHTML = "";
  }

  enhanceProcessShellTables(cardEl);
}

function buildProcessOptionMetaMap(setting) {
  const metaByKey = new Map();
  const processListsByKey = new Map();
  const processLists = Array.isArray(setting && setting.process_lists) ? setting.process_lists : [];
  processLists.forEach((processList) => {
    const listKey = normalizeMenuKey(processList && processList.key);
    if (!listKey) {
      return;
    }
    processListsByKey.set(
      listKey,
      Array.isArray(processList.items)
        ? processList.items.map((item) => String(item || "").trim()).filter(Boolean)
        : []
    );
  });

  const processOptions = Array.isArray(setting && setting.process_field_options)
    ? setting.process_field_options
    : [];
  processOptions.forEach((option) => {
    const optionKey = normalizeMenuKey(option && option.key);
    if (!optionKey) {
      return;
    }
    const fieldType = normalizeProcessFieldType(option.field_type);
    const listKey = normalizeMenuKey(option.list_key || option.listKey);
    const optionRequiredRaw = Object.prototype.hasOwnProperty.call(option || {}, "is_required")
      ? option.is_required
      : option.required;
    metaByKey.set(optionKey, {
      key: optionKey,
      label: toSentenceCaseText(option.label || optionKey) || optionKey,
      fieldType,
      size: normalizeProcessFieldSize(option.size, fieldType),
      listKey,
      listOptions: processListsByKey.get(listKey) || [],
      isRequired: normalizeProcessFieldRequired(optionRequiredRaw)
    });
  });

  return metaByKey;
}

function collectCurrentDynamicProcessQuantityValues(menuKey) {
  const cleanMenuKey = normalizeMenuKey(menuKey);
  const baseValues = (
    menuProcessQuantityValuesMap &&
    menuProcessQuantityValuesMap[cleanMenuKey] &&
    typeof menuProcessQuantityValuesMap[cleanMenuKey] === "object"
  )
    ? JSON.parse(JSON.stringify(menuProcessQuantityValuesMap[cleanMenuKey]))
    : {};
  if (!dynamicProcessEditFormEl) {
    return baseValues;
  }

  const payloadInputs = dynamicProcessEditFormEl.querySelectorAll("[name^='process_quantity_payload__']");
  payloadInputs.forEach((inputEl) => {
    const ruleKey = normalizeMenuKey(String(inputEl.getAttribute("name") || "").replace(/^process_quantity_payload__/, ""));
    if (!ruleKey) {
      return;
    }
    try {
      const parsed = JSON.parse(String(inputEl.value || "[]"));
      baseValues[ruleKey] = normalizeProcessQuantityItems(parsed);
    } catch (error) {
      baseValues[ruleKey] = [];
    }
  });

  const fieldInputs = dynamicProcessEditFormEl.querySelectorAll("[data-process-quantity-field-key]");
  fieldInputs.forEach((controlEl) => {
    const ruleKey = normalizeMenuKey(controlEl.getAttribute("data-process-quantity-rule-key"));
    const itemIndex = Number.parseInt(String(controlEl.getAttribute("data-process-quantity-index") || "").trim(), 10);
    const fieldKey = normalizeMenuKey(controlEl.getAttribute("data-process-quantity-field-key"));
    if (!ruleKey || !fieldKey || !Number.isFinite(itemIndex) || itemIndex < 0) {
      return;
    }
    if (!Array.isArray(baseValues[ruleKey])) {
      baseValues[ruleKey] = [];
    }
    while (baseValues[ruleKey].length <= itemIndex) {
      baseValues[ruleKey].push({});
    }
    const itemValues = baseValues[ruleKey][itemIndex];
    if (controlEl.type === "checkbox") {
      itemValues[fieldKey] = controlEl.checked ? "1" : "0";
      return;
    }
    itemValues[fieldKey] = String(controlEl.value || "").trim();
  });

  return baseValues;
}

function syncDynamicProcessQuantityHiddenInputs(menuKey, quantityValuesByRule) {
  if (!dynamicProcessEditFormEl) {
    return;
  }
  dynamicProcessEditFormEl
    .querySelectorAll("[data-process-quantity-payload='1']")
    .forEach((inputEl) => inputEl.remove());

  const cleanMenuKey = normalizeMenuKey(menuKey);
  Object.keys(quantityValuesByRule || {}).forEach((rawRuleKey) => {
    const ruleKey = normalizeMenuKey(rawRuleKey);
    if (!ruleKey) {
      return;
    }
    const hiddenInputEl = document.createElement("input");
    hiddenInputEl.type = "hidden";
    hiddenInputEl.name = `process_quantity_payload__${ruleKey}`;
    hiddenInputEl.value = JSON.stringify(normalizeProcessQuantityItems(quantityValuesByRule[ruleKey]));
    hiddenInputEl.setAttribute("data-process-quantity-payload", "1");
    hiddenInputEl.setAttribute("data-process-quantity-menu-key", cleanMenuKey);
    hiddenInputEl.setAttribute("data-process-quantity-rule-key", ruleKey);
    dynamicProcessEditFormEl.appendChild(hiddenInputEl);
  });
}

function collectCurrentMeuPerfilQuantityValues() {
  const cleanMenuKey = MEU_PERFIL_MENU_KEY;
  const baseValues = (
    menuProcessQuantityValuesMap &&
    menuProcessQuantityValuesMap[cleanMenuKey] &&
    typeof menuProcessQuantityValuesMap[cleanMenuKey] === "object"
  )
    ? JSON.parse(JSON.stringify(menuProcessQuantityValuesMap[cleanMenuKey]))
    : {};
  const personalCardEl = getMeuPerfilPersonalCardElV1();
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  if (!formEl) {
    return baseValues;
  }

  formEl.querySelectorAll("[data-meu-perfil-quantity-payload='1']").forEach((inputEl) => {
    const ruleKey = normalizeMenuKey(String(inputEl.getAttribute("name") || "").replace(/^process_quantity_payload__/, ""));
    if (!ruleKey) {
      return;
    }
    try {
      baseValues[ruleKey] = normalizeProcessQuantityItems(JSON.parse(String(inputEl.value || "[]")));
    } catch (error) {
      baseValues[ruleKey] = [];
    }
  });

  formEl.querySelectorAll("[data-meu-perfil-quantity-field-key]").forEach((controlEl) => {
    const ruleKey = normalizeMenuKey(controlEl.getAttribute("data-meu-perfil-quantity-rule-key"));
    const fieldKey = normalizeMenuKey(controlEl.getAttribute("data-meu-perfil-quantity-field-key"));
    const itemIndex = Number.parseInt(String(controlEl.getAttribute("data-meu-perfil-quantity-index") || "").trim(), 10);
    if (!ruleKey || !fieldKey || !Number.isFinite(itemIndex) || itemIndex < 0) {
      return;
    }
    if (!Array.isArray(baseValues[ruleKey])) {
      baseValues[ruleKey] = [];
    }
    while (baseValues[ruleKey].length <= itemIndex) {
      baseValues[ruleKey].push({});
    }
    if (controlEl.type === "checkbox") {
      baseValues[ruleKey][itemIndex][fieldKey] = controlEl.checked ? "1" : "0";
      return;
    }
    baseValues[ruleKey][itemIndex][fieldKey] = String(controlEl.value || "").trim();
  });

  return baseValues;
}

function syncMeuPerfilQuantityHiddenInputs(quantityValuesByRule) {
  const personalCardEl = getMeuPerfilPersonalCardElV1();
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  if (!formEl) {
    return;
  }

  formEl.querySelectorAll("[data-meu-perfil-quantity-payload='1']").forEach((inputEl) => inputEl.remove());

  Object.keys(quantityValuesByRule || {}).forEach((rawRuleKey) => {
    const ruleKey = normalizeMenuKey(rawRuleKey);
    if (!ruleKey) {
      return;
    }
    const hiddenInputEl = document.createElement("input");
    hiddenInputEl.type = "hidden";
    hiddenInputEl.name = `process_quantity_payload__${ruleKey}`;
    hiddenInputEl.value = JSON.stringify(normalizeProcessQuantityItems(quantityValuesByRule[ruleKey]));
    hiddenInputEl.setAttribute("data-meu-perfil-quantity-payload", "1");
    formEl.appendChild(hiddenInputEl);
  });
}

function renderMeuPerfilQuantityGroups() {
  const runtimeRefs = newUserPageBootstrapStateV1.lastContext && newUserPageBootstrapStateV1.lastContext.runtimeRefs
    ? newUserPageBootstrapStateV1.lastContext.runtimeRefs
    : null;
  const quantityContext = runtimeRefs && runtimeRefs.profile
    ? runtimeRefs.profile.quantityContext
    : null;

  if (
    appGenesisProcessQuantityRuntimeV1 &&
    typeof appGenesisProcessQuantityRuntimeV1.render === "function" &&
    quantityContext
  ) {
    appGenesisProcessQuantityRuntimeV1.render(quantityContext);
    if (typeof appGenesisProcessQuantityRuntimeV1.sync === "function") {
      appGenesisProcessQuantityRuntimeV1.sync(quantityContext);
    }
    return;
  }

  const personalCardEl = getMeuPerfilPersonalCardElV1();
  const readonlyGridEl = personalCardEl ? personalCardEl.querySelector(".profile-readonly .personal-grid") : null;
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  const editGridEl = formEl ? formEl.querySelector(".personal-grid") : null;
  const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
  const normalizedRules = normalizeProcessQuantityRules(setting && setting.process_quantity_fields);
  if (!readonlyGridEl && !editGridEl) {
    return;
  }

  if (readonlyGridEl) {
    readonlyGridEl.querySelectorAll("[data-meu-perfil-quantity-generated='1']").forEach((node) => node.remove());
  }
  if (editGridEl) {
    editGridEl.querySelectorAll("[data-meu-perfil-quantity-generated='1']").forEach((node) => node.remove());
  }

  if (!setting || !normalizedRules.length) {
    syncMeuPerfilQuantityHiddenInputs({});
    return;
  }

  const processValuesByField = collectCurrentMeuPerfilProcessValues();
  const quantityValuesByRule = collectCurrentMeuPerfilQuantityValues();
  const nextQuantityValuesByRule = { ...quantityValuesByRule };
  const optionMetaByKey = buildProcessOptionMetaMap(setting);
  const fieldSectionMap = getFieldSectionMap(setting);
  const activeSectionKey = normalizeMenuKey(
    meuPerfilSelectedProfileSection ||
    meuPerfilBootstrap.activePersonalSection ||
    ""
  );

  normalizedRules.forEach((rule) => {
    const ruleSectionKey = resolveMeuPerfilQuantitySectionKeyV1(rule, fieldSectionMap, activeSectionKey);
    if (ruleSectionKey && activeSectionKey && ruleSectionKey !== activeSectionKey) {
      return;
    }
    const readOnlyAnchorEl = readonlyGridEl
      ? readonlyGridEl.querySelector(`[data-profile-field-key="${rule.quantityFieldKey}"]`)
      : null;
    const editAnchorEl = editGridEl
      ? editGridEl.querySelector(`[data-profile-field-key="${rule.quantityFieldKey}"]`)
      : null;

    const sourceValueRaw = Number.parseInt(String(processValuesByField[rule.quantityFieldKey] || "").trim(), 10);
    const desiredCount = Number.isFinite(sourceValueRaw)
      ? Math.min(Math.max(sourceValueRaw, 0), rule.maxItems)
      : 0;
    const sourceIndex = profilePersonalVisibleFields.indexOf(rule.quantityFieldKey);
    const baseOrder = sourceIndex >= 0 ? ((sourceIndex + 1) * 10) : ((profilePersonalVisibleFields.length + 1) * 10);
    if (readOnlyAnchorEl) {
      readOnlyAnchorEl.style.order = String(baseOrder);
    }
    if (editAnchorEl) {
      editAnchorEl.style.order = String(baseOrder);
    }
    const existingItems = normalizeProcessQuantityItems(nextQuantityValuesByRule[rule.key]);
    const nextItems = [];
    for (let index = 0; index < desiredCount; index += 1) {
      nextItems.push(existingItems[index] && typeof existingItems[index] === "object"
        ? { ...existingItems[index] }
        : {});
    }
    nextQuantityValuesByRule[rule.key] = nextItems;

    if (readonlyGridEl && nextItems.length) {
      const groupEl = document.createElement("div");
      groupEl.className = "personal-item";
      groupEl.style.gridColumn = "1 / -1";
      groupEl.style.order = String(baseOrder + 1);
      groupEl.setAttribute("data-profile-section-pane", ruleSectionKey || "");
      groupEl.setAttribute("data-meu-perfil-quantity-generated", "1");

      const titleEl = document.createElement("span");
      titleEl.className = "personal-label";
      titleEl.textContent = rule.label;
      groupEl.appendChild(titleEl);

      nextItems.forEach((itemValues, index) => {
        const itemWrapEl = document.createElement("div");
        itemWrapEl.className = "dynamic-process-quantity-item";
        itemWrapEl.style.marginTop = index === 0 ? "8px" : "12px";

        const itemHeadingEl = document.createElement("strong");
        itemHeadingEl.className = "personal-value";
        itemHeadingEl.textContent = `${rule.itemLabel} ${index + 1}`;
        itemWrapEl.appendChild(itemHeadingEl);

        rule.repeatedFieldKeys.forEach((fieldKey) => {
          const fieldMeta = optionMetaByKey.get(fieldKey) || {};
          const valueRowEl = document.createElement("div");
          valueRowEl.className = "dynamic-process-quantity-value-row";

          const valueLabelEl = document.createElement("span");
          valueLabelEl.className = "dynamic-process-quantity-value-label";
          valueLabelEl.textContent = `${fieldMeta.label || profilePersonalFieldLabels[fieldKey] || fieldKey}:`;

          const rawValue = String(itemValues[fieldKey] || "").trim();
          const valueTextEl = document.createElement("strong");
          valueTextEl.className = "personal-value";
          valueTextEl.textContent = normalizeProcessFieldType(fieldMeta.fieldType) === "flag"
            ? (isTruthyFlagValue(rawValue) ? "Sim" : "Não")
            : (rawValue || "-");

          valueRowEl.appendChild(valueLabelEl);
          valueRowEl.appendChild(valueTextEl);
          itemWrapEl.appendChild(valueRowEl);
        });

        groupEl.appendChild(itemWrapEl);
      });

      if (readOnlyAnchorEl && readOnlyAnchorEl.parentNode === readonlyGridEl) {
        readonlyGridEl.insertBefore(groupEl, readOnlyAnchorEl.nextSibling);
      } else {
        readonlyGridEl.appendChild(groupEl);
      }
    }

    if (editGridEl && nextItems.length) {
      const blockEl = document.createElement("div");
      blockEl.className = "field full dynamic-process-quantity-editor-block";
      blockEl.style.order = String(baseOrder + 1);
      blockEl.setAttribute("data-profile-section-pane", ruleSectionKey || "");
      blockEl.setAttribute("data-meu-perfil-quantity-generated", "1");
      blockEl.setAttribute("data-meu-perfil-quantity-source-key", rule.quantityFieldKey);

      const titleEl = document.createElement("label");
      titleEl.className = "dynamic-process-quantity-title";
      titleEl.textContent = rule.label;
      blockEl.appendChild(titleEl);

      nextItems.forEach((itemValues, index) => {
        const itemWrapEl = document.createElement("div");
        itemWrapEl.className = "dynamic-process-quantity-item-edit";

        const itemHeadingEl = document.createElement("h4");
        itemHeadingEl.textContent = `${rule.itemLabel} ${index + 1}`;
        itemWrapEl.appendChild(itemHeadingEl);

        const itemGridEl = document.createElement("div");
        itemGridEl.className = "grid settings-general-grid";

        rule.repeatedFieldKeys.forEach((fieldKey) => {
          const fieldMeta = optionMetaByKey.get(fieldKey) || {};
          const fieldType = normalizeProcessFieldType(fieldMeta.fieldType);
          const fieldContainerEl = document.createElement("div");
          fieldContainerEl.className = "field";

          const inputId = `meu_perfil_quantity_${rule.key}_${index}_${fieldKey}`.replace(/[^a-z0-9_]+/gi, "_");
          const currentValue = String(itemValues[fieldKey] || "").trim();
          const labelEl = document.createElement("label");
          labelEl.setAttribute("for", inputId);
          labelEl.textContent = fieldMeta.isRequired ? `${fieldMeta.label || profilePersonalFieldLabels[fieldKey] || fieldKey} *` : (fieldMeta.label || profilePersonalFieldLabels[fieldKey] || fieldKey);
          fieldContainerEl.appendChild(labelEl);

          let controlEl = null;
          if (fieldType === "flag") {
            const wrapperEl = document.createElement("label");
            wrapperEl.className = "profile-custom-flag-control";
            controlEl = document.createElement("input");
            controlEl.type = "checkbox";
            controlEl.value = "1";
            controlEl.checked = isTruthyFlagValue(currentValue);
            wrapperEl.appendChild(controlEl);
            const spanEl = document.createElement("span");
            spanEl.textContent = "Ativo";
            wrapperEl.appendChild(spanEl);
            fieldContainerEl.appendChild(wrapperEl);
          } else if (fieldType === "list") {
            controlEl = document.createElement("select");
            const placeholderEl = document.createElement("option");
            placeholderEl.value = "";
            placeholderEl.textContent = "Selecione";
            controlEl.appendChild(placeholderEl);
            (Array.isArray(fieldMeta.listOptions) ? fieldMeta.listOptions : []).forEach((optionValue) => {
              const optionEl = document.createElement("option");
              optionEl.value = String(optionValue || "").trim();
              optionEl.textContent = String(optionValue || "").trim();
              optionEl.selected = optionEl.value === currentValue;
              controlEl.appendChild(optionEl);
            });
            fieldContainerEl.appendChild(controlEl);
          } else {
            controlEl = document.createElement("input");
            controlEl.type = getDynamicProcessInputType(fieldType);
            controlEl.value = currentValue;
            if (fieldType === "date" && !currentValue) {
              controlEl.placeholder = "dd/mm/aaaa";
            }
            if (fieldMeta.size && processTextualTypes.has(fieldType)) {
              controlEl.maxLength = Number(fieldMeta.size) || 255;
            }
            fieldContainerEl.appendChild(controlEl);
          }

          if (!controlEl) {
            return;
          }
          controlEl.id = inputId;
          controlEl.name = `process_quantity_field__${rule.key}__${index}__${fieldKey}`;
          if (fieldMeta.isRequired && fieldType !== "flag") {
            controlEl.required = true;
          }
          controlEl.setAttribute("data-meu-perfil-quantity-rule-key", rule.key);
          controlEl.setAttribute("data-meu-perfil-quantity-index", String(index));
          controlEl.setAttribute("data-meu-perfil-quantity-field-key", fieldKey);
          ["input", "change"].forEach((eventName) => {
            controlEl.addEventListener(eventName, () => {
              syncMeuPerfilQuantityHiddenInputs(collectCurrentMeuPerfilQuantityValues());
            });
          });

          itemGridEl.appendChild(fieldContainerEl);
        });

        itemWrapEl.appendChild(itemGridEl);
        blockEl.appendChild(itemWrapEl);
      });

      if (editAnchorEl && editAnchorEl.parentNode === editGridEl) {
        editGridEl.insertBefore(blockEl, editAnchorEl.nextSibling);
      } else {
        editGridEl.appendChild(blockEl);
      }
    }
  });

  syncMeuPerfilQuantityHiddenInputs(nextQuantityValuesByRule);
  if (typeof window.reorderMeuPerfilProfileFields === "function") {
    window.reorderMeuPerfilProfileFields();
  }
}

function renderDynamicProcessQuantityGroups(
  menuKey,
  setting,
  selectedSection,
  sectionFields,
  processValuesByField,
  processQuantityValuesByRule
) {
  const runtimeRefs = newUserPageBootstrapStateV1.lastContext && newUserPageBootstrapStateV1.lastContext.runtimeRefs
    ? newUserPageBootstrapStateV1.lastContext.runtimeRefs
    : null;
  const quantityContext = runtimeRefs && runtimeRefs.dynamicProcess
    ? runtimeRefs.dynamicProcess.quantityContext
    : null;

  if (
    appGenesisProcessQuantityRuntimeV1 &&
    typeof appGenesisProcessQuantityRuntimeV1.render === "function" &&
    quantityContext
  ) {
    appGenesisProcessQuantityRuntimeV1.render(quantityContext);
    if (typeof appGenesisProcessQuantityRuntimeV1.sync === "function") {
      appGenesisProcessQuantityRuntimeV1.sync(quantityContext);
    }
    return;
  }

  const cleanMenuKey = normalizeMenuKey(menuKey);
  const normalizedRules = normalizeProcessQuantityRules(setting && setting.process_quantity_fields);
  if (!normalizedRules.length) {
    syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, {});
    return;
  }

  const selectedSectionKey = normalizeMenuKey(selectedSection && selectedSection.key) || "__geral__";
  const optionMetaByKey = buildProcessOptionMetaMap(setting);
  const currentSectionFieldKeys = new Set(
    Array.isArray(sectionFields)
      ? sectionFields
        .map((field) => normalizeMenuKey(field && field.key))
        .filter(Boolean)
      : []
  );
  const rulesForSection = normalizedRules.filter((rule) => {
    if (rule.headerKey) {
      return rule.headerKey === selectedSectionKey;
    }
    return currentSectionFieldKeys.has(rule.quantityFieldKey);
  });

  if (!rulesForSection.length) {
    syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, processQuantityValuesByRule || {});
    return;
  }

  const nextQuantityValuesByRule = {
    ...(processQuantityValuesByRule && typeof processQuantityValuesByRule === "object"
      ? processQuantityValuesByRule
      : {})
  };

  rulesForSection.forEach((rule) => {
    const sourceValueRaw = Number.parseInt(String(processValuesByField[rule.quantityFieldKey] || "").trim(), 10);
    const desiredCount = Number.isFinite(sourceValueRaw)
      ? Math.min(Math.max(sourceValueRaw, 0), rule.maxItems)
      : 0;
    const existingItems = normalizeProcessQuantityItems(nextQuantityValuesByRule[rule.key]);
    const nextItems = [];

    for (let index = 0; index < desiredCount; index += 1) {
      nextItems.push(existingItems[index] && typeof existingItems[index] === "object"
        ? { ...existingItems[index] }
        : {});
    }

    nextQuantityValuesByRule[rule.key] = nextItems;

    if (dynamicProcessReadOnlyGridEl) {
      const readOnlyBlockEl = document.createElement("div");
      readOnlyBlockEl.className = "dynamic-process-quantity-group";

      const readOnlyTitleEl = document.createElement("div");
      readOnlyTitleEl.className = "dynamic-process-quantity-title";
      readOnlyTitleEl.textContent = rule.label;
      readOnlyBlockEl.appendChild(readOnlyTitleEl);

      if (!nextItems.length) {
        const emptyEl = document.createElement("p");
        emptyEl.className = "empty";
        emptyEl.textContent = `Sem ${String(rule.itemLabel || "item").toLowerCase()}s registados.`;
        readOnlyBlockEl.appendChild(emptyEl);
      } else {
        nextItems.forEach((itemValues, index) => {
          const itemCardEl = document.createElement("div");
          itemCardEl.className = "personal-item dynamic-process-quantity-item";

          const itemLabelEl = document.createElement("span");
          itemLabelEl.className = "personal-label";
          itemLabelEl.textContent = `${rule.itemLabel} ${index + 1}`;
          itemCardEl.appendChild(itemLabelEl);

          rule.repeatedFieldKeys.forEach((fieldKey) => {
            const fieldMeta = optionMetaByKey.get(fieldKey) || {};
            const valueRowEl = document.createElement("div");
            valueRowEl.className = "dynamic-process-quantity-value-row";

            const valueLabelEl = document.createElement("span");
            valueLabelEl.className = "dynamic-process-quantity-value-label";
            valueLabelEl.textContent = `${fieldMeta.label || fieldKey}:`;

            const rawValue = String(itemValues[fieldKey] || "").trim();
            const valueTextEl = document.createElement("strong");
            valueTextEl.className = "personal-value";
            valueTextEl.textContent = normalizeProcessFieldType(fieldMeta.fieldType) === "flag"
              ? (isTruthyFlagValue(rawValue) ? "Sim" : "Não")
              : (rawValue || "-");

            valueRowEl.appendChild(valueLabelEl);
            valueRowEl.appendChild(valueTextEl);
            itemCardEl.appendChild(valueRowEl);
          });

          readOnlyBlockEl.appendChild(itemCardEl);
        });
      }

      dynamicProcessReadOnlyGridEl.appendChild(readOnlyBlockEl);
    }

    if (dynamicProcessEditGridEl) {
      const editBlockEl = document.createElement("div");
      editBlockEl.className = "field full dynamic-process-quantity-editor-block";
      editBlockEl.dataset.processQuantityRuleKey = rule.key;

      const blockTitleEl = document.createElement("label");
      blockTitleEl.className = "dynamic-process-quantity-title";
      blockTitleEl.textContent = rule.label;
      editBlockEl.appendChild(blockTitleEl);

      if (!nextItems.length) {
        const emptyEl = document.createElement("p");
        emptyEl.className = "empty";
        emptyEl.textContent = `Informe ${rule.quantityFieldKey === rule.itemLabel ? "uma quantidade" : "a quantidade"} para gerar blocos.`;
        editBlockEl.appendChild(emptyEl);
      } else {
        nextItems.forEach((itemValues, index) => {
          const itemWrapEl = document.createElement("div");
          itemWrapEl.className = "dynamic-process-quantity-item-edit";

          const itemHeadingEl = document.createElement("h4");
          itemHeadingEl.textContent = `${rule.itemLabel} ${index + 1}`;
          itemWrapEl.appendChild(itemHeadingEl);

          const itemGridEl = document.createElement("div");
          itemGridEl.className = "grid settings-general-grid";

          rule.repeatedFieldKeys.forEach((fieldKey) => {
            const fieldMeta = optionMetaByKey.get(fieldKey) || {};
            const fieldType = normalizeProcessFieldType(fieldMeta.fieldType);
            const fieldContainerEl = document.createElement("div");
            fieldContainerEl.className = "field";

            const inputId = `dynamic_quantity_${cleanMenuKey}_${rule.key}_${index}_${fieldKey}`
              .replace(/[^a-z0-9_]+/gi, "_");
            const currentValue = String(itemValues[fieldKey] || "").trim();

            const labelEl = document.createElement("label");
            labelEl.setAttribute("for", inputId);
            labelEl.textContent = fieldMeta.isRequired ? `${fieldMeta.label || fieldKey} *` : (fieldMeta.label || fieldKey);
            fieldContainerEl.appendChild(labelEl);

            if (fieldType === "flag") {
              const wrapperEl = document.createElement("label");
              wrapperEl.className = "profile-custom-flag-control";

              const inputEl = document.createElement("input");
              inputEl.id = inputId;
              inputEl.type = "checkbox";
              inputEl.value = "1";
              inputEl.checked = isTruthyFlagValue(currentValue);
              inputEl.defaultChecked = inputEl.checked;
              inputEl.setAttribute("data-process-quantity-rule-key", rule.key);
              inputEl.setAttribute("data-process-quantity-index", String(index));
              inputEl.setAttribute("data-process-quantity-field-key", fieldKey);

              const textEl = document.createElement("span");
              textEl.textContent = "Ativo";

              wrapperEl.appendChild(inputEl);
              wrapperEl.appendChild(textEl);
              fieldContainerEl.appendChild(wrapperEl);
            } else if (fieldType === "list") {
              const selectEl = document.createElement("select");
              selectEl.id = inputId;
              selectEl.required = Boolean(fieldMeta.isRequired);
              selectEl.setAttribute("data-process-quantity-rule-key", rule.key);
              selectEl.setAttribute("data-process-quantity-index", String(index));
              selectEl.setAttribute("data-process-quantity-field-key", fieldKey);

              const defaultOptionEl = document.createElement("option");
              defaultOptionEl.value = "";
              defaultOptionEl.textContent = "Selecione";
              selectEl.appendChild(defaultOptionEl);

              (Array.isArray(fieldMeta.listOptions) ? fieldMeta.listOptions : []).forEach((optionValue) => {
                const optionEl = document.createElement("option");
                optionEl.value = String(optionValue || "");
                optionEl.textContent = String(optionValue || "");
                if (String(optionValue || "") === currentValue) {
                  optionEl.selected = true;
                }
                selectEl.appendChild(optionEl);
              });

              fieldContainerEl.appendChild(selectEl);
            } else {
              const inputEl = document.createElement("input");
              const normalizedValue = fieldType === "date"
                ? normalizeDateInputValue(currentValue)
                : currentValue;
              inputEl.id = inputId;
              inputEl.type = getDynamicProcessInputType(fieldType);
              inputEl.value = normalizedValue;
              inputEl.defaultValue = normalizedValue;
              inputEl.required = Boolean(fieldMeta.isRequired);
              if (fieldType === "number") {
                inputEl.inputMode = "numeric";
              }
              if (
                typeof fieldMeta.size === "number" &&
                fieldMeta.size > 0 &&
                processTextualTypes.has(fieldType)
              ) {
                inputEl.maxLength = fieldMeta.size;
              }
              inputEl.setAttribute("data-process-quantity-rule-key", rule.key);
              inputEl.setAttribute("data-process-quantity-index", String(index));
              inputEl.setAttribute("data-process-quantity-field-key", fieldKey);
              fieldContainerEl.appendChild(inputEl);
            }

            itemGridEl.appendChild(fieldContainerEl);
          });

          itemWrapEl.appendChild(itemGridEl);
          editBlockEl.appendChild(itemWrapEl);
        });
      }

      dynamicProcessEditGridEl.appendChild(editBlockEl);
    }
  });

  syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, nextQuantityValuesByRule);
}

function collectCurrentDynamicProcessValues(menuKey) {
  const cleanMenuKey = normalizeMenuKey(menuKey);
  const baseValues = (
    menuProcessValuesMap &&
    menuProcessValuesMap[cleanMenuKey] &&
    typeof menuProcessValuesMap[cleanMenuKey] === "object"
  )
    ? { ...menuProcessValuesMap[cleanMenuKey] }
    : {};
  if (!dynamicProcessEditFormEl) {
    return baseValues;
  }

  const controls = dynamicProcessEditFormEl.querySelectorAll("[name^='process_field__']");
  controls.forEach((controlEl) => {
    const fieldKey = normalizeMenuKey(String(controlEl.getAttribute("name") || "").replace(/^process_field__/, ""));
    if (!fieldKey) {
      return;
    }
    if (controlEl.type === "checkbox") {
      baseValues[fieldKey] = controlEl.checked ? "1" : "0";
      return;
    }
    baseValues[fieldKey] = String(controlEl.value || "").trim();
  });

  return baseValues;
}

function renderDynamicProcessCard(menuKey, sectionKey) {
  debugTabsLogV1("renderDynamicProcessCard", { menuKey, sectionKey });
  if (!dynamicProcessCardEl) {
    return;
  }
  const cleanMenuKey = normalizeMenuKey(menuKey);
  const menuData = dynamicProcessDataByMenu[cleanMenuKey];
  const processSetting = getSidebarMenuSetting(cleanMenuKey);
  const currentProcessValuesByField = collectCurrentDynamicProcessValues(cleanMenuKey);
  const currentProcessQuantityValuesByRule = collectCurrentDynamicProcessQuantityValues(cleanMenuKey);
  dynamicProcessCardEl.classList.remove("editing");
  dynamicProcessCardEl.classList.remove("dynamic-process-open");

  if (dynamicProcessReadOnlyGridEl) {
    dynamicProcessReadOnlyGridEl.innerHTML = "";
  }
  if (dynamicProcessEditGridEl) {
    dynamicProcessEditGridEl.innerHTML = "";
  }
  resetDynamicProcessListCardsV1();
  if (dynamicProcessReadOnlyGridEl && dynamicProcessReadOnlyGridEl.parentElement) {
    dynamicProcessReadOnlyGridEl.parentElement.style.display = "";
  }
  if (dynamicProcessHistoryBlockEl) {
    dynamicProcessHistoryBlockEl.style.display = "none";
  }

  if (!menuData) {
    if (dynamicProcessTitleEl) {
      dynamicProcessTitleEl.textContent = "Processo";
    }
    if (dynamicProcessDescriptionEl) {
      dynamicProcessDescriptionEl.textContent = "Campos configurados para este processo.";
    }
    if (dynamicProcessSectionLabelEl) {
      dynamicProcessSectionLabelEl.textContent = "";
    }
    if (dynamicProcessMenuKeyInputEl) {
      dynamicProcessMenuKeyInputEl.value = "";
      dynamicProcessMenuKeyInputEl.defaultValue = "";
    }
    if (dynamicProcessSectionKeyInputEl) {
      dynamicProcessSectionKeyInputEl.value = "";
      dynamicProcessSectionKeyInputEl.defaultValue = "";
    }
    setDynamicProcessEditToggleVisible(false);
    if (dynamicProcessHistoryActionInputEl) {
      dynamicProcessHistoryActionInputEl.value = "create";
    }
    if (dynamicProcessHistoryRecordIdInputEl) {
      dynamicProcessHistoryRecordIdInputEl.value = "";
    }
    if (dynamicProcessSubmitBtnEl) {
      dynamicProcessSubmitBtnEl.textContent = "Guardar";
    }
    if (dynamicProcessEmptyEl) {
      dynamicProcessEmptyEl.style.display = "";
      dynamicProcessEmptyEl.textContent = "Sem campos configurados para esta aba.";
    }
    syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, {});
    return;
  }

  const hiddenTargets = getHiddenProcessTargets(
    processSetting ? processSetting.process_subsequent_fields : [],
    currentProcessValuesByField
  );
  const fieldSectionMap = getFieldSectionMap(processSetting);
  const visibleSections = menuData.sections.filter(
    (section) => !hiddenTargets.has(normalizeMenuKey(section && section.key))
  );
  if (itemsEl) {
    const submenuLinks = itemsEl.querySelectorAll(".submenu-item[data-dynamic-process-section]");
    submenuLinks.forEach((linkEl) => {
      const linkSectionKey = normalizeMenuKey(linkEl.dataset.dynamicProcessSection);
      linkEl.style.display = hiddenTargets.has(linkSectionKey) ? "none" : "";
    });
  }

  const cleanSectionKey = String(sectionKey || selectedDynamicSectionByMenu[cleanMenuKey] || "").trim();
  let selectedSection = visibleSections.find((section) => String(section.key || "") === cleanSectionKey);
  if (!selectedSection) {
    selectedSection = visibleSections[0];
  }
  if (selectedSection) {
    selectedDynamicSectionByMenu[cleanMenuKey] = String(selectedSection.key || "");
    setActiveSubmenu("#dynamic-process-card", {
      dynamicProcessSectionKey: String(selectedSection.key || "")
    });
  }

  const menuLabel = toSentenceCaseText(menuData.menuLabel || "Processo");
  const sectionLabel = selectedSection
    ? toSentenceCaseText(selectedSection.label || "Campos")
    : "Campos";
  const layoutConfig = getDynamicProcessLayoutConfig(processSetting, menuLabel, sectionLabel);
  const listProcessLayoutMode = Boolean(layoutConfig.isListProcess);
  const absenceProcessMode = isAbsenceProcessMenu(cleanMenuKey, menuLabel, sectionLabel);
  // "uses_record_history" (calculado no backend a partir de process_record_uses_history/process_layout
  // no menu_config) permite ativar o modo "Criar <processo>" com lista de registos para qualquer
  // processo via configuracao, sem depender apenas dos padroes legados hardcoded abaixo.
  const historyProcessMode = Boolean(processSetting && processSetting.uses_record_history) ||
    isHistoryProcessMenu(cleanMenuKey, menuLabel, sectionLabel);
  const recordProcessMode = historyProcessMode || listProcessLayoutMode;
  const historyRecordLabels = { singular: layoutConfig.singularLabel, plural: layoutConfig.pluralLabel };
  const showStateField = listProcessLayoutMode
    ? Boolean(layoutConfig.stateEnabled)
    : (historyProcessMode && !absenceProcessMode && historyRecordLabels.singular === "departamento");
  dynamicProcessCardEl.classList.toggle("dynamic-process-open", absenceProcessMode);

  if (dynamicProcessTitleEl) {
    dynamicProcessTitleEl.textContent = sectionLabel || menuLabel;
  }
  if (dynamicProcessDescriptionEl) {
    dynamicProcessDescriptionEl.textContent = "Campos visíveis definidos na configuração desta pasta.";
  }
  if (dynamicProcessSectionLabelEl) {
    dynamicProcessSectionLabelEl.textContent = `Pasta: ${menuLabel} | Aba: ${sectionLabel}`;
  }
  if (dynamicProcessMenuKeyInputEl) {
    dynamicProcessMenuKeyInputEl.value = cleanMenuKey;
    dynamicProcessMenuKeyInputEl.defaultValue = cleanMenuKey;
  }
  if (dynamicProcessSectionKeyInputEl) {
    const resolvedSectionKey = String(selectedSection ? (selectedSection.key || "") : "");
    dynamicProcessSectionKeyInputEl.value = resolvedSectionKey;
    dynamicProcessSectionKeyInputEl.defaultValue = resolvedSectionKey;
  }
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

  const selectedSectionKey = normalizeMenuKey(selectedSection ? selectedSection.key : "");
  const sectionFields = selectedSection && Array.isArray(selectedSection.fields)
    ? selectedSection.fields.filter((field) => {
        const fieldKey = normalizeMenuKey(field && field.key);
        const fieldSectionKey = fieldSectionMap.get(fieldKey) || selectedSectionKey;
        return !hiddenTargets.has(fieldKey) && !hiddenTargets.has(fieldSectionKey);
      })
    : [];
  const hasQuantityRulesForSection = normalizeProcessQuantityRules(
    processSetting ? processSetting.process_quantity_fields : []
  ).some((rule) => (
    rule.headerKey
      ? rule.headerKey === selectedSectionKey
      : sectionFields.some((field) => normalizeMenuKey(field && field.key) === rule.quantityFieldKey)
  ));
  if (!sectionFields.length && !hasQuantityRulesForSection) {
    setDynamicProcessEditToggleVisible(false);
    if (dynamicProcessEmptyEl) {
      dynamicProcessEmptyEl.style.display = "";
      dynamicProcessEmptyEl.textContent = "Sem campos configurados para esta aba.";
    }
    if (dynamicProcessHistoryBlockEl) {
      dynamicProcessHistoryBlockEl.style.display = "none";
    }
    syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, currentProcessQuantityValuesByRule);
    return;
  }

  if (dynamicProcessEditToggleEl) {
    setDynamicProcessEditToggleVisible(false);
    if (!absenceProcessMode && (sectionFields.length || hasQuantityRulesForSection)) {
      setDynamicProcessEditToggleVisible(true);
      dynamicProcessEditToggleEl.textContent = listProcessLayoutMode
        ? layoutConfig.createTitle
        : (historyProcessMode ? `Criar ${historyRecordLabels.singular}` : "Editar");
    }
  }
  if (dynamicProcessEmptyEl) {
    dynamicProcessEmptyEl.style.display = "none";
  }

  const renderedInputsByFieldKey = new Map();
  sectionFields.forEach((field) => {
    const fieldKey = normalizeMenuKey(field.key);
    if (!fieldKey) {
      return;
    }
    const fieldLabel = toSentenceCaseText(field.label || fieldKey);
    const fieldType = normalizeProcessFieldType(field.fieldType);
    const fieldSize = normalizeProcessFieldSize(field.size, fieldType);
    const fieldRequired = Boolean(field.isRequired) && fieldType !== "flag";
    const readOnlyValue = String(field.value || "").trim();
    const fieldValue = absenceProcessMode ? "" : readOnlyValue;
    const editDefaultValue = recordProcessMode ? "" : fieldValue;

    if (dynamicProcessReadOnlyGridEl) {
      const readOnlyItemEl = document.createElement("div");
      readOnlyItemEl.className = "personal-item";
      readOnlyItemEl.dataset.processFieldKey = fieldKey;

      const labelEl = document.createElement("span");
      labelEl.className = "personal-label";
      labelEl.textContent = fieldLabel;

      const valueEl = document.createElement("strong");
      valueEl.className = "personal-value";
      if (fieldType === "flag") {
        valueEl.textContent = isTruthyFlagValue(fieldValue) ? "Sim" : "Não";
      } else {
        valueEl.textContent = fieldValue || "-";
      }

      readOnlyItemEl.appendChild(labelEl);
      readOnlyItemEl.appendChild(valueEl);
      dynamicProcessReadOnlyGridEl.appendChild(readOnlyItemEl);
    }

    if (dynamicProcessEditGridEl) {
      const fieldContainerEl = document.createElement("div");
      fieldContainerEl.className = "field";
      fieldContainerEl.dataset.processFieldKey = fieldKey;

      const inputId = `dynamic_process_${cleanMenuKey}_${String(selectedSection ? (selectedSection.key || "") : "")}_${fieldKey}`
        .replace(/[^a-z0-9_]+/gi, "_");
      const inputName = `process_field__${fieldKey}`;

      const labelEl = document.createElement("label");
      labelEl.setAttribute("for", inputId);
      labelEl.textContent = fieldRequired ? `${fieldLabel} *` : fieldLabel;

      if (fieldType === "flag") {
        const wrapperEl = document.createElement("label");
        wrapperEl.className = "profile-custom-flag-control";

        const inputEl = document.createElement("input");
        inputEl.id = inputId;
        inputEl.type = "checkbox";
        inputEl.name = inputName;
        inputEl.value = "1";
        inputEl.checked = isTruthyFlagValue(editDefaultValue);
        inputEl.defaultChecked = inputEl.checked;

        const textEl = document.createElement("span");
        textEl.textContent = "Ativo";

        wrapperEl.appendChild(inputEl);
        wrapperEl.appendChild(textEl);
        renderedInputsByFieldKey.set(fieldKey, inputEl);

        fieldContainerEl.appendChild(labelEl);
        fieldContainerEl.appendChild(wrapperEl);
      } else if (fieldType === "list") {
        const selectEl = document.createElement("select");
        selectEl.id = inputId;
        selectEl.name = inputName;
        selectEl.required = fieldRequired;

        const defaultOptionEl = document.createElement("option");
        defaultOptionEl.value = "";
        defaultOptionEl.textContent = "Selecione";
        selectEl.appendChild(defaultOptionEl);

        const listOptions = Array.isArray(field.listOptions) ? field.listOptions : [];
        listOptions.forEach((optionValue) => {
          const optionEl = document.createElement("option");
          optionEl.value = String(optionValue || "");
          optionEl.textContent = String(optionValue || "");
          if (String(optionValue || "") === editDefaultValue) {
            optionEl.selected = true;
          }
          selectEl.appendChild(optionEl);
        });

        renderedInputsByFieldKey.set(fieldKey, selectEl);
        fieldContainerEl.appendChild(labelEl);
        fieldContainerEl.appendChild(selectEl);
      } else {
        const inputEl = document.createElement("input");
        const inputValue = fieldType === "date"
          ? normalizeDateInputValue(editDefaultValue)
          : editDefaultValue;
        inputEl.id = inputId;
        inputEl.name = inputName;
        inputEl.type = getDynamicProcessInputType(fieldType);
        inputEl.value = inputValue;
        inputEl.defaultValue = inputValue;
        inputEl.required = fieldRequired;
        if (fieldType === "date" && typeof inputEl.showPicker === "function") {
          const openDatePicker = () => {
            try {
              inputEl.showPicker();
            } catch (error) {
              // Some browsers block showPicker outside trusted user events.
            }
          };
          inputEl.addEventListener("click", openDatePicker);
          inputEl.addEventListener("focus", openDatePicker);
        }
        if (fieldType === "number") {
          inputEl.inputMode = "numeric";
        }
        if (typeof fieldSize === "number" && fieldSize > 0 && processTextualTypes.has(fieldType)) {
          inputEl.maxLength = fieldSize;
        }
        renderedInputsByFieldKey.set(fieldKey, inputEl);

        fieldContainerEl.appendChild(labelEl);
        fieldContainerEl.appendChild(inputEl);
      }

      dynamicProcessEditGridEl.appendChild(fieldContainerEl);
    }
  });

  if (showStateField && dynamicProcessEditGridEl) {
    const stateFieldEl = document.createElement("div");
    stateFieldEl.className = "field";

    const stateInputId = `dynamic_process_${cleanMenuKey}_${String(selectedSection ? (selectedSection.key || "") : "")}_estado`
      .replace(/[^a-z0-9_]+/gi, "_");

    const stateLabelEl = document.createElement("label");
    stateLabelEl.setAttribute("for", stateInputId);
    stateLabelEl.textContent = "Estado";

    const stateSelectEl = document.createElement("select");
    stateSelectEl.id = stateInputId;
    stateSelectEl.name = "process_state";
    stateSelectEl.innerHTML = `
      <option value="ativo" selected>Ativo</option>
      <option value="inativo">Inativo</option>
    `;

    stateFieldEl.appendChild(stateLabelEl);
    stateFieldEl.appendChild(stateSelectEl);
    dynamicProcessEditGridEl.appendChild(stateFieldEl);
  }

  if (absenceProcessMode) {
    setupAbsenceDateRangeValidation(sectionFields, renderedInputsByFieldKey);
  }

  renderDynamicProcessQuantityGroups(
    cleanMenuKey,
    processSetting,
    selectedSection,
    sectionFields,
    currentProcessValuesByField,
    currentProcessQuantityValuesByRule
  );

  if (listProcessLayoutMode) {
    const historyRowsRaw = Array.isArray(menuProcessHistoryMap[cleanMenuKey])
      ? menuProcessHistoryMap[cleanMenuKey]
      : [];
    const visibleRows = historyRowsRaw.filter((item) => {
      const rowSectionKey = String(item && item.section_key || "").trim();
      if (!selectedSection) {
        return true;
      }
      if (!rowSectionKey) {
        return true;
      }
      return rowSectionKey === String(selectedSection.key || "");
    });
    const splitRows = splitDynamicProcessListRows(visibleRows, layoutConfig);

    if (dynamicProcessTitleEl) {
      dynamicProcessTitleEl.textContent = layoutConfig.createTitle;
    }
    if (dynamicProcessReadOnlyGridEl && dynamicProcessReadOnlyGridEl.parentElement) {
      dynamicProcessReadOnlyGridEl.parentElement.style.display = "none";
    }
    if (dynamicProcessHistoryBlockEl) {
      dynamicProcessHistoryBlockEl.style.display = "none";
    }

    renderDynamicProcessListTableCardV1({
      cardEl: dynamicProcessActiveCardEl,
      titleEl: dynamicProcessActiveTitleEl,
      tableEl: dynamicProcessActiveTableEl,
      headEl: dynamicProcessActiveHeadEl,
      bodyEl: dynamicProcessActiveBodyEl,
      emptyEl: dynamicProcessActiveEmptyEl,
      limiterEl: dynamicProcessActiveLimiterEl,
      rows: splitRows.active,
      sectionFields,
      layoutConfig,
      title: layoutConfig.activeTitle,
      emptyMessage: layoutConfig.emptyActiveMessage
    });
    renderDynamicProcessListTableCardV1({
      cardEl: dynamicProcessInactiveCardEl,
      titleEl: dynamicProcessInactiveTitleEl,
      tableEl: dynamicProcessInactiveTableEl,
      headEl: dynamicProcessInactiveHeadEl,
      bodyEl: dynamicProcessInactiveBodyEl,
      emptyEl: dynamicProcessInactiveEmptyEl,
      limiterEl: dynamicProcessInactiveLimiterEl,
      rows: splitRows.inactive,
      sectionFields,
      layoutConfig,
      title: layoutConfig.inactiveTitle,
      emptyMessage: layoutConfig.emptyInactiveMessage
    });
    return;
  }

  if (historyProcessMode) {
    renderDynamicProcessHistory(
      cleanMenuKey,
      selectedSection ? (selectedSection.key || "") : "",
      sectionLabel,
      sectionFields,
      historyRecordLabels
    );
  } else if (dynamicProcessHistoryBlockEl) {
    dynamicProcessHistoryBlockEl.style.display = "none";
  }
}

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
  logMissingNavigationRuntimeV1("admin_target_registry_v1.getAdminSubprocessKeyByTarget");
  return "";
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
    dynamicProcessActionCardEl,
    dynamicProcessActiveCardEl,
    dynamicProcessInactiveCardEl,
    debugTabsLog: debugTabsLogV1,
    logNavigationBootDebug: logAppGenesisNavigationBootDebugV1,
    documentRef: document,
    windowRef: window
  });
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

// Alias explícito pedido para o mecanismo de ativação de grupo de cards de subprocesso -- é a
// mesma função, exposta com o nome documentado para depuração/testes a partir do console.
window.activateSubprocessCardsV1 = function (menuKey, targetSelector, source) {
  return applyContentForMenuTarget(menuKey, targetSelector, source);
};

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
  logMissingNavigationRuntimeV1("admin_target_registry_v1.normalizeSubmenuTargetAlias");
  return normalizeTargetV1(targetSelector);
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
function isDynamicProcessActionCardContextV1() {
  const cleanMenuKey = normalizeMenuKey(activeMenuKey || "");
  if (!cleanMenuKey || cleanMenuKey === MEU_PERFIL_MENU_KEY || cleanMenuKey === "perfil") {
    return false;
  }

  return normalizeTargetV1(selectedTargetByMenu[cleanMenuKey] || "") === "#dynamic-process-card";
}

function setDynamicProcessEditToggleVisible(isVisible) {
  const shouldShowDynamicProcessCard = isDynamicProcessActionCardContextV1();
  if (dynamicProcessActionCardEl) {
    dynamicProcessActionCardEl.style.display = isVisible && shouldShowDynamicProcessCard ? "" : "none";
  }
  if (!dynamicProcessEditToggleEl) {
    return;
  }
  if (isVisible && shouldShowDynamicProcessCard) {
    dynamicProcessEditToggleEl.style.removeProperty("display");
  } else {
    dynamicProcessEditToggleEl.style.setProperty("display", "none", "important");
  }
}

// O botao "Criar/Editar" do processo dinamico vive num card de acao separado
// (#dynamic-process-action-card), fora de #dynamic-process-card, por isso nao e alcancado pela
// regra CSS ".card.editing .profile-edit-toggle". Repoe a visibilidade aqui sempre que o card deixa
// de estar em edicao (Cancelar/Guardar via JS, sem recarregar a pagina).
function restoreDynamicProcessEditToggleVisibility() {
  if (
    dynamicProcessEditToggleEl &&
    dynamicProcessCardEl &&
    !dynamicProcessCardEl.classList.contains("editing") &&
    isDynamicProcessActionCardContextV1()
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
  if (isDynamicProcessActionCardContextV1()) {
    restoreDynamicProcessEditToggleVisibility();
  } else {
    setDynamicProcessEditToggleVisible(false);
  }
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

function getMeuPerfilSectionPaneNodesV1(personalCardEl, sectionKey) {
  if (!personalCardEl) {
    return [];
  }

  const cleanSection = String(sectionKey || "").trim().toLowerCase();
  if (!cleanSection) {
    return [];
  }

  const selector = `[data-profile-section-pane="${cleanSection.replace(/"/g, '\\"')}"]`;
  return Array.from(personalCardEl.querySelectorAll(selector));
}

function hasVisibleMeuPerfilSectionContentV1(personalCardEl, sectionKey) {
  return getMeuPerfilSectionPaneNodesV1(personalCardEl, sectionKey).some((paneEl) => {
    if (!paneEl) {
      return false;
    }

    const style = window.getComputedStyle(paneEl);
    return style.display !== "none" && style.visibility !== "hidden" && !paneEl.hidden;
  });
}

function resolveMeuPerfilVisibleSectionKeyV1(personalCardEl, sectionKey) {
  if (!personalCardEl) {
    return String(sectionKey || "").trim().toLowerCase();
  }

  const normalizedPreferredSection = String(sectionKey || "").trim().toLowerCase();
  const orderedSections = [];

  Array.from(personalCardEl.querySelectorAll("[data-profile-section-pane]")).forEach((paneEl) => {
    const paneSection = String(paneEl.getAttribute("data-profile-section-pane") || "").trim().toLowerCase();
    if (paneSection && !orderedSections.includes(paneSection)) {
      orderedSections.push(paneSection);
    }
  });

  const visibleSections = orderedSections.filter((paneSection) => {
    return hasVisibleMeuPerfilSectionContentV1(personalCardEl, paneSection);
  });

  if (normalizedPreferredSection && orderedSections.includes(normalizedPreferredSection)) {
    return normalizedPreferredSection;
  }

  if (visibleSections.length) {
    return visibleSections[0];
  }

  return orderedSections[0] || normalizedPreferredSection || "geral";
}

function resolveMeuPerfilVisibleSectionKeyV2(personalCardEl, sectionKey, hiddenSectionKeys) {
  const normalizedPreferredSection = String(sectionKey || "").trim().toLowerCase();
  const hiddenSet = hiddenSectionKeys instanceof Set
    ? hiddenSectionKeys
    : new Set(
      Array.isArray(hiddenSectionKeys)
        ? hiddenSectionKeys.map((item) => String(item || "").trim().toLowerCase()).filter(Boolean)
        : []
    );
  const orderedSections = [];

  if (!personalCardEl || typeof personalCardEl.querySelectorAll !== "function") {
    return {
      sectionKey: normalizedPreferredSection || "geral",
      hasVisibleSection: false
    };
  }

  Array.from(personalCardEl.querySelectorAll("[data-profile-section-pane]")).forEach((paneEl) => {
    const paneSection = String(paneEl.getAttribute("data-profile-section-pane") || "").trim().toLowerCase();
    if (paneSection && !orderedSections.includes(paneSection)) {
      orderedSections.push(paneSection);
    }
  });

  const visibleSections = orderedSections.filter((paneSection) => {
    if (hiddenSet.has(paneSection)) {
      return false;
    }
    return hasVisibleMeuPerfilSectionContentV1(personalCardEl, paneSection);
  });

  if (
    normalizedPreferredSection &&
    orderedSections.includes(normalizedPreferredSection) &&
    !hiddenSet.has(normalizedPreferredSection)
  ) {
    return {
      sectionKey: normalizedPreferredSection,
      hasVisibleSection: true
    };
  }

  if (visibleSections.length) {
    return {
      sectionKey: visibleSections[0],
      hasVisibleSection: true
    };
  }

  if (normalizedPreferredSection && orderedSections.includes(normalizedPreferredSection)) {
    return {
      sectionKey: normalizedPreferredSection,
      hasVisibleSection: false
    };
  }

  return {
    sectionKey: orderedSections[0] || normalizedPreferredSection || "geral",
    hasVisibleSection: false
  };
}

function setupProfileProcessTabs() {
  const personalCardEl = getMeuPerfilPersonalCardElV1();
  if (!personalCardEl) {
    return;
  }
  const sectionPanes = personalCardEl.querySelectorAll("[data-profile-section-pane]");
  if (!sectionPanes.length) {
    return;
  }

  function activateSection(sectionKey) {
    const normalizedSection = String(sectionKey || "").trim().toLowerCase() || "geral";
    const orderedSections = Array.from(sectionPanes).reduce((acc, paneEl) => {
      const paneSection = String(
        paneEl.getAttribute("data-profile-section-pane") || "geral"
      ).trim().toLowerCase();
      if (paneSection && !acc.includes(paneSection)) {
        acc.push(paneSection);
      }
      return acc;
    }, []);
    const effectiveSection = orderedSections.includes(normalizedSection)
      ? normalizedSection
      : orderedSections[0] || normalizedSection || "geral";

    sectionPanes.forEach((paneEl) => {
      const paneSection = String(
        paneEl.getAttribute("data-profile-section-pane") || "geral"
      ).trim().toLowerCase();
      paneEl.style.display = paneSection === effectiveSection ? "" : "none";
    });
    const sectionInputEl = personalCardEl.querySelector("[data-meu-perfil-section-input]");
    if (sectionInputEl) {
      sectionInputEl.value = effectiveSection;
    }
    setupAllocationSectionMultiValue(personalCardEl, effectiveSection);
    meuPerfilSelectedProfileSection = effectiveSection;
    renderMeuPerfilQuantityGroups();
    window.dispatchEvent(
      new CustomEvent("appgenesis:meu-perfil:layout-updated", {
        detail: { sectionKey: effectiveSection }
      })
    );
  }

  window.activateProfilePersonalSection = activateSection;
  activateSection(meuPerfilSelectedProfileSection);
}

function collectCurrentMeuPerfilProcessValues() {
  const personalCardEl = getMeuPerfilPersonalCardElV1();
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  const valuesByField = {};
  if (!formEl) {
    return valuesByField;
  }

  if (
    appGenesisProfileFieldRegistryV1 &&
    typeof appGenesisProfileFieldRegistryV1.collectProfileValues === "function"
  ) {
    return appGenesisProfileFieldRegistryV1.collectProfileValues(formEl);
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

function applyMeuPerfilProcessSubsequentVisibility() {
  const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
  const personalCardEl = getMeuPerfilPersonalCardElV1();
  if (!setting || !personalCardEl) {
    return;
  }

  if (
    appGenesisProcessSubsequentVisibilityRuntimeV1 &&
    typeof appGenesisProcessSubsequentVisibilityRuntimeV1.refresh === "function"
  ) {
    const evaluation = appGenesisProcessSubsequentVisibilityRuntimeV1.refresh({
      mode: "profile",
      root: personalCardEl,
    formEl: personalCardEl.querySelector(".profile-edit-form"),
    setting,
    rules: setting.process_subsequent_fields,
    getValues: collectCurrentMeuPerfilProcessValues,
    getCurrentSection: getCurrentProfileSectionV1
    });

    hiddenMeuPerfilSectionKeys = evaluation && evaluation.hiddenTargets ? evaluation.hiddenTargets : new Set();
    if (typeof window.activateProfilePersonalSection === "function") {
      window.activateProfilePersonalSection(
        resolveMeuPerfilVisibleSectionKeyV2(
          personalCardEl,
          meuPerfilSelectedProfileSection,
          hiddenMeuPerfilSectionKeys
        ).sectionKey
      );
    }
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
      linkEl.style.display = hiddenMeuPerfilSectionKeys.has(sectionKey) ? "none" : "";
    });
  }

  if (typeof window.activateProfilePersonalSection === "function") {
    window.activateProfilePersonalSection(
      resolveMeuPerfilVisibleSectionKeyV2(
        personalCardEl,
        meuPerfilSelectedProfileSection,
        hiddenMeuPerfilSectionKeys
      ).sectionKey
    );
  }
  if (itemsEl) {
    const selectedLinkEl = itemsEl.querySelector(
      `.submenu-item[data-profile-section="${String(meuPerfilSelectedProfileSection || "").replace(/"/g, '\\"')}"]`
    );
    if (selectedLinkEl && selectedLinkEl.style.display !== "none") {
      setActiveSubmenu(getMeuPerfilPersonalCardTargetV1(), {
        profileSection: String(meuPerfilSelectedProfileSection || "")
      });
      return;
    }
    const firstVisibleLinkEl = Array.from(itemsEl.querySelectorAll(".submenu-item[data-profile-section]")).find(
      (linkEl) => linkEl.style.display !== "none"
    );
    if (firstVisibleLinkEl) {
      meuPerfilSelectedProfileSection = String(firstVisibleLinkEl.dataset.profileSection || "");
      setActiveSubmenu(getMeuPerfilPersonalCardTargetV1(), {
        profileSection: String(meuPerfilSelectedProfileSection || "")
      });
    }
  }
  renderMeuPerfilQuantityGroups();
}

function setupMeuPerfilQuantityRules() {
  const personalCardEl = getMeuPerfilPersonalCardElV1();
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
  if (!formEl || !setting) {
    return;
  }

  if (
    !appGenesisProcessQuantityRuntimeV1 ||
    typeof appGenesisProcessQuantityRuntimeV1.initialize !== "function"
  ) {
    return;
  }

  appGenesisProcessQuantityRuntimeV1.initialize({
    mode: "profile",
    adapterName: "profile",
    root: personalCardEl,
    formEl,
    setting,
    rules: setting.process_quantity_fields,
    getSetting: () => setting,
    getValues: collectCurrentMeuPerfilQuantityValues,
    getCurrentSection: getCurrentProfileSectionV1,
    readonlyGridEl: personalCardEl.querySelector(".profile-readonly .personal-grid"),
    editGridEl: formEl.querySelector(".personal-grid")
  });
}

function setupConditionalProcessVisibility() {
  const personalCardEl = getMeuPerfilPersonalCardElV1();
  const personalFormEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  if (
    appGenesisProcessSubsequentVisibilityRuntimeV1 &&
    typeof appGenesisProcessSubsequentVisibilityRuntimeV1.initialize === "function" &&
    personalFormEl
  ) {
    appGenesisProcessSubsequentVisibilityRuntimeV1.initialize({
      mode: "profile",
      root: personalCardEl,
      formEl: personalFormEl,
      setting: getSidebarMenuSetting(MEU_PERFIL_MENU_KEY),
      rules: getSidebarMenuSetting(MEU_PERFIL_MENU_KEY) && getSidebarMenuSetting(MEU_PERFIL_MENU_KEY).process_subsequent_fields,
      getValues: collectCurrentMeuPerfilProcessValues,
      getCurrentSection: getCurrentProfileSectionV1,
      getMeuPerfilPersonalCardTarget: getMeuPerfilPersonalCardTargetV1
    });
  }

  if (
    appGenesisProcessQuantityRuntimeV1 &&
    typeof appGenesisProcessQuantityRuntimeV1.initialize === "function" &&
    dynamicProcessEditFormEl
  ) {
    const cleanMenuKey = normalizeMenuKey(dynamicProcessMenuKeyInputEl ? dynamicProcessMenuKeyInputEl.value : "");
    const setting = cleanMenuKey ? getSidebarMenuSetting(cleanMenuKey) : null;
    if (setting) {
      appGenesisProcessQuantityRuntimeV1.initialize({
        mode: "dynamic",
        adapterName: "dynamic",
        root: document,
        formEl: dynamicProcessEditFormEl,
        setting,
        rules: setting.process_quantity_fields,
        getSetting: () => setting,
        getValues: () => collectCurrentDynamicProcessQuantityValues(cleanMenuKey),
        getCurrentSection: () => normalizeMenuKey(dynamicProcessSectionKeyInputEl ? dynamicProcessSectionKeyInputEl.value : ""),
        readonlyGridEl: dynamicProcessReadOnlyGridEl || null,
        editGridEl: dynamicProcessEditGridEl || null
      });
    }
  }
}

function restoreInitialProfileSectionFromUrlV2() {
  const personalCardEl = getMeuPerfilPersonalCardElV1();
  if (!personalCardEl || typeof window.activateProfilePersonalSection !== "function") {
    return;
  }

  const currentUrl = new URL(window.location.href);
  const sectionKey = normalizeMenuKey(
    currentUrl.searchParams.get("profile_tab") ||
    currentUrl.searchParams.get("profile_section") ||
    currentUrl.searchParams.get("section_key") ||
    currentUrl.searchParams.get("dynamic_process_section") ||
    currentUrl.searchParams.get("target") ||
    ""
  );

  if (!sectionKey) {
    return;
  }

  const sectionInputEl = personalCardEl.querySelector(
    "input[name='profile_section'], [data-meu-perfil-section-input], [data-profile-section-input]"
  );
  if (sectionInputEl) {
    sectionInputEl.value = sectionKey;
    sectionInputEl.defaultValue = sectionKey;
  }

  const candidates = Array.from(
    personalCardEl.querySelectorAll(
      "[data-profile-section-tab], [data-profile-section-button], .profile-section-tab, button, a"
    )
  );
  const tab = candidates.find((candidate) => {
    const dataKey = normalizeMenuKey(
      candidate.dataset.profileSection ||
      candidate.dataset.profileSectionKey ||
      candidate.dataset.profileSectionTab ||
      candidate.dataset.sectionKey ||
      ""
    );

    if (dataKey && dataKey === sectionKey) {
      return true;
    }
    return false;
  });

  if (tab && typeof tab.click === "function") {
    tab.click();
  }

  window.activateProfilePersonalSection(sectionKey);
  document.dispatchEvent(new CustomEvent("appgenesis:profile-section-restored", { detail: { sectionKey } }));
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

document.addEventListener("appgenesis:cancelled", function (event) {
  const detail = event && event.detail ? event.detail : {};
  const card = detail.card;
  const cardId = card && card.id ? card.id : "";

  if (cardId === "dynamic-process-card") {
    resetDynamicProcessCancelStateV1();
  }

  if (
    cardId === "dynamic-process-card" ||
    cardId === String(getMeuPerfilPersonalCardTargetV1()).replace(/^#/, "") ||
    cardId === "perfil-morada-card" ||
    cardId === "dados-treinamento-card"
  ) {
    syncTrainingOutrosState();
  }
});

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

function setupProcessFieldsBuilder() {
  if (!processFieldsBuilderEl) {
    return;
  }
  const optionsRaw = processFieldsBuilderEl.getAttribute("data-field-options") || "[]";
  const headerOptionsRaw = processFieldsBuilderEl.getAttribute("data-header-options") || "[]";
  let fieldOptions = [];
  let headerOptions = [];
  try {
    fieldOptions = JSON.parse(optionsRaw);
  } catch (error) {
    fieldOptions = [];
  }
  try {
    headerOptions = JSON.parse(headerOptionsRaw);
  } catch (error) {
    headerOptions = [];
  }
  if (!Array.isArray(fieldOptions) || !fieldOptions.length) {
    return;
  }
  if (!Array.isArray(headerOptions)) {
    headerOptions = [];
  }

  const containerEl = document.getElementById("process-visible-fields-container");
  const addButtonEl = document.getElementById("process-field-add-btn");
  const formEl = processFieldsBuilderEl.closest("form");
  if (!containerEl || !addButtonEl || !formEl) {
    return;
  }

  function renderFieldOptions(selectedKey) {
    return fieldOptions
      .map((option) => {
        const optionKey = String(option.key || "");
        const optionLabel = String(option.label || optionKey);
        const isSelected = optionKey === String(selectedKey || "");
        return `<option value="${optionKey}"${isSelected ? " selected" : ""}>${optionLabel}</option>`;
      })
      .join("");
  }

  function renderHeaderOptions(selectedKey) {
    const cleanSelectedKey = String(selectedKey || "").trim();
    const optionsHtml = headerOptions
      .map((option) => {
        const optionKey = String(option.key || "");
        const optionLabel = String(option.label || optionKey);
        const isSelected = optionKey === cleanSelectedKey;
        return `<option value="${optionKey}"${isSelected ? " selected" : ""}>${optionLabel}</option>`;
      })
      .join("");
    return `<option value="">Sem cabeçalho</option>${optionsHtml}`;
  }

  function updateRemoveButtonsState() {
    const removeButtons = containerEl.querySelectorAll(".process-field-remove-btn");
    const isSingleRow = removeButtons.length <= 1;
    removeButtons.forEach((button) => {
      button.disabled = isSingleRow;
      button.classList.toggle("table-icon-btn-disabled", isSingleRow);
      button.setAttribute(
        "title",
        isSingleRow ? "É necessário manter pelo menos um campo" : "Remover campo"
      );
      button.setAttribute(
        "aria-label",
        isSingleRow ? "É necessário manter pelo menos um campo" : "Remover campo"
      );
    });
  }

  function bindRemoveButton(buttonEl) {
    buttonEl.addEventListener("click", () => {
      const rows = containerEl.querySelectorAll(".process-field-row");
      if (rows.length <= 1) {
        updateRemoveButtonsState();
        return;
      }
      const rowEl = buttonEl.closest(".process-field-row");
      if (rowEl) {
        rowEl.remove();
      }
      updateRemoveButtonsState();
    });
  }

  function createFieldRow(selectedKey, selectedHeaderKey) {
    const rowEl = document.createElement("div");
    rowEl.className = "process-field-row";
    rowEl.innerHTML = `
      <div class="field">
        <label>Campo</label>
        <select name="visible_fields" class="process-field-select">
          ${renderFieldOptions(selectedKey || fieldOptions[0].key)}
        </select>
      </div>
      <div class="field">
        <label>Cabeçalho</label>
        <select name="visible_headers" class="process-field-header-select">
          ${renderHeaderOptions(selectedHeaderKey || "")}
        </select>
      </div>
      <button
        type="button"
        class="table-icon-btn table-icon-btn-danger process-field-remove-btn"
        title="Remover campo"
        aria-label="Remover campo"
      >
        &#10005;
      </button>
    `;
    const removeButtonEl = rowEl.querySelector(".process-field-remove-btn");
    if (removeButtonEl) {
      bindRemoveButton(removeButtonEl);
    }
    return rowEl;
  }

  containerEl.querySelectorAll(".process-field-remove-btn").forEach((buttonEl) => {
    bindRemoveButton(buttonEl);
  });

  addButtonEl.addEventListener("click", () => {
    containerEl.appendChild(createFieldRow(fieldOptions[0].key, ""));
    updateRemoveButtonsState();
  });

  formEl.addEventListener("submit", () => {
    const seenFieldKeys = new Set();
    const selects = containerEl.querySelectorAll("select[name='visible_fields']");
    selects.forEach((selectEl) => {
      const cleanValue = String(selectEl.value || "").trim();
      if (!cleanValue || seenFieldKeys.has(cleanValue)) {
        selectEl.removeAttribute("name");
        const rowEl = selectEl.closest(".process-field-row");
        if (rowEl) {
          const headerSelectEl = rowEl.querySelector("select[name='visible_headers']");
          if (headerSelectEl) {
            headerSelectEl.removeAttribute("name");
          }
        }
        return;
      }
      seenFieldKeys.add(cleanValue);
    });
  });

  if (!containerEl.querySelector(".process-field-row")) {
    containerEl.appendChild(createFieldRow(fieldOptions[0].key, ""));
  }
  if (fieldOptions.length <= 1) {
    addButtonEl.disabled = true;
    addButtonEl.classList.add("table-icon-btn-disabled");
    addButtonEl.setAttribute("title", "Não há mais campos para adicionar");
    addButtonEl.setAttribute("aria-label", "Não há mais campos para adicionar");
  }
  updateRemoveButtonsState();
}

function setupProcessAdditionalFieldsBuilder() {
  const builderEl = document.getElementById("process-additional-fields-builder");
  if (!builderEl) {
    return;
  }

  const fieldTypesRaw = builderEl.getAttribute("data-field-types") || "[]";
  let fieldTypes = [];
  try {
    fieldTypes = JSON.parse(fieldTypesRaw);
  } catch (error) {
    fieldTypes = [];
  }
  if (!Array.isArray(fieldTypes) || !fieldTypes.length) {
    fieldTypes = [
      { key: "text", label: "Texto" },
      { key: "number", label: "Número" },
      { key: "email", label: "Email" },
      { key: "phone", label: "Telefone" },
      { key: "date", label: "Data" },
      { key: "flag", label: "Flag" }
    ];
  }

  const containerEl = document.getElementById("process-additional-fields-container");
  const addButtonEl = document.getElementById("process-additional-field-add-btn");
  const formEl = builderEl.closest("form");
  const moveFormEl = document.getElementById("process-additional-field-move-form");
  const limiterEl = document.getElementById("process-additional-fields-limiter");
  const pageSizeEl = document.getElementById("process-additional-fields-page-size");
  const prevEl = document.getElementById("process-additional-fields-prev");
  const nextEl = document.getElementById("process-additional-fields-next");
  const pageEl = document.getElementById("process-additional-fields-page");
  if (!containerEl || !addButtonEl || !formEl) {
    return;
  }

  const sizedTypes = new Set(["text", "number", "email", "phone"]);
  let additionalFieldsPageSize = Number.parseInt(pageSizeEl ? pageSizeEl.value : "5", 10) || 5;
  let additionalFieldsCurrentPage = 1;

  function renderTypeOptions(selectedType) {
    return fieldTypes
      .map((item) => {
        const optionKey = String(item.key || "");
        const optionLabel = String(item.label || optionKey);
        const isSelected = optionKey === String(selectedType || "text");
        return `<option value="${optionKey}"${isSelected ? " selected" : ""}>${optionLabel}</option>`;
      })
      .join("");
  }

  function syncRowState(rowEl) {
    const typeSelectEl = rowEl.querySelector("select[name='additional_field_type']");
    const requiredSelectEl = rowEl.querySelector("select[name='additional_field_required']");
    const sizeInputEl = rowEl.querySelector("input[name='additional_field_size']");
    if (!typeSelectEl || !sizeInputEl) {
      return;
    }
    const cleanType = String(typeSelectEl.value || "text").trim().toLowerCase();
    if (cleanType === "header" && requiredSelectEl) {
      requiredSelectEl.value = "0";
    }
    rowEl.classList.toggle("process-additional-field-row-header", cleanType === "header");
    const isSizeEnabled = sizedTypes.has(cleanType);
    if (isSizeEnabled) {
      sizeInputEl.readOnly = false;
      sizeInputEl.classList.remove("process-additional-size-readonly");
      if (!String(sizeInputEl.value || "").trim()) {
        sizeInputEl.value = "30";
      }
    } else {
      sizeInputEl.value = "";
      sizeInputEl.readOnly = true;
      sizeInputEl.classList.add("process-additional-size-readonly");
    }
  }

  function renderAdditionalFieldsPagination() {
    if (!limiterEl || !pageSizeEl || !prevEl || !nextEl || !pageEl) {
      return;
    }

    const rowEls = Array.from(containerEl.querySelectorAll(".process-additional-field-row"));
    if (!rowEls.length) {
      limiterEl.style.display = "none";
      return;
    }

    const totalPages = Math.max(1, Math.ceil(rowEls.length / additionalFieldsPageSize));
    if (additionalFieldsCurrentPage > totalPages) {
      additionalFieldsCurrentPage = totalPages;
    }

    const start = (additionalFieldsCurrentPage - 1) * additionalFieldsPageSize;
    const end = start + additionalFieldsPageSize;

    rowEls.forEach((rowEl, index) => {
      rowEl.style.display = index >= start && index < end ? "" : "none";
    });

    pageEl.textContent = String(additionalFieldsCurrentPage);
    prevEl.disabled = additionalFieldsCurrentPage <= 1;
    nextEl.disabled = additionalFieldsCurrentPage >= totalPages;
    limiterEl.style.display = rowEls.length > additionalFieldsPageSize ? "flex" : "none";
  }

  function bindRemoveButton(buttonEl) {
    buttonEl.addEventListener("click", () => {
      const rowEl = buttonEl.closest(".process-additional-field-row");
      if (rowEl) {
        rowEl.remove();
        renderAdditionalFieldsPagination();
      }
    });
  }

  function submitMoveRequest(buttonEl) {
    if (!moveFormEl || !buttonEl) {
      return;
    }

    const menuKey = String(buttonEl.getAttribute("data-menu-key") || "").trim();
    const fieldKey = String(buttonEl.getAttribute("data-field-key") || "").trim();
    const direction = String(buttonEl.getAttribute("data-move-direction") || "").trim().toLowerCase();
    const redirectMenu = String(buttonEl.getAttribute("data-redirect-menu") || "").trim();
    const redirectTarget = String(buttonEl.getAttribute("data-redirect-target") || "#settings-menu-edit-card").trim();

    if (!menuKey || !fieldKey || (direction !== "up" && direction !== "down")) {
      return;
    }

    const menuKeyEl = moveFormEl.querySelector('input[name="menu_key"]');
    const fieldKeyEl = moveFormEl.querySelector('input[name="field_key"]');
    const directionEl = moveFormEl.querySelector('input[name="direction"]');
    const redirectMenuEl = moveFormEl.querySelector('input[name="redirect_menu"]');
    const redirectTargetEl = moveFormEl.querySelector('input[name="redirect_target"]');

    if (!menuKeyEl || !fieldKeyEl || !directionEl || !redirectMenuEl || !redirectTargetEl) {
      return;
    }

    menuKeyEl.value = menuKey;
    fieldKeyEl.value = fieldKey;
    directionEl.value = direction;
    redirectMenuEl.value = redirectMenu;
    redirectTargetEl.value = redirectTarget;

    moveFormEl.submit();
  }

  function bindRow(rowEl) {
    const removeButtonEl = rowEl.querySelector(".process-additional-field-remove-btn");
    if (removeButtonEl) {
      bindRemoveButton(removeButtonEl);
    }
    rowEl.querySelectorAll(".process-additional-field-move-btn").forEach((buttonEl) => {
      if (buttonEl.dataset.moveBound === "1") {
        return;
      }
      buttonEl.dataset.moveBound = "1";
      buttonEl.addEventListener("click", () => {
        submitMoveRequest(buttonEl);
      });
    });
    const typeSelectEl = rowEl.querySelector("select[name='additional_field_type']");
    if (typeSelectEl) {
      typeSelectEl.addEventListener("change", () => {
        syncRowState(rowEl);
      });
    }
    syncRowState(rowEl);
  }

  function createAdditionalFieldRow(initialValue, initialType, initialRequired, initialSize) {
    const rowEl = document.createElement("div");
    rowEl.className = "process-field-row process-additional-field-row";
    rowEl.innerHTML = `
      <input type="hidden" name="additional_field_key" value="">
      <div class="field">
        <label>Nome do campo adicional</label>
        <input
          type="text"
          name="additional_field_label"
          maxlength="80"
          placeholder="Ex.: Data de batismo"
          value="${String(initialValue || "").replace(/"/g, "&quot;")}"
        >
      </div>
      <div class="field">
        <label>Tipo do campo</label>
        <select name="additional_field_type" class="process-additional-field-type-select">
          ${renderTypeOptions(initialType || "text")}
        </select>
      </div>
      <div class="field">
        <label>Obrigatório</label>
        <select name="additional_field_required" class="process-additional-field-required-select">
          <option value="0"${String(initialRequired || "0") === "0" ? " selected" : ""}>Não</option>
          <option value="1"${String(initialRequired || "0") === "1" ? " selected" : ""}>Sim</option>
        </select>
      </div>
      <div class="field">
        <label>Tamanho</label>
        <input
          type="number"
          name="additional_field_size"
          class="process-additional-field-size-input"
          min="1"
          max="255"
          placeholder=""
          value="${String(initialSize || "")}"
        >
      </div>
      <button
        type="button"
        class="table-icon-btn table-icon-btn-danger process-additional-field-remove-btn"
        title="Remover campo adicional"
        aria-label="Remover campo adicional"
      >
        &#10005;
      </button>
    `;
    bindRow(rowEl);
    return rowEl;
  }

  containerEl.querySelectorAll(".process-additional-field-row").forEach((rowEl) => {
    bindRow(rowEl);
  });

  addButtonEl.addEventListener("click", () => {
    const rowEl = createAdditionalFieldRow("", "text", "0", "30");
    containerEl.appendChild(rowEl);
    const totalRows = containerEl.querySelectorAll(".process-additional-field-row").length;
    additionalFieldsCurrentPage = Math.max(1, Math.ceil(totalRows / additionalFieldsPageSize));
    renderAdditionalFieldsPagination();
    const inputEl = rowEl.querySelector("input[name='additional_field_label']");
    if (inputEl) {
      inputEl.focus();
    }
  });

  if (pageSizeEl && prevEl && nextEl && pageEl) {
    pageSizeEl.addEventListener("change", () => {
      additionalFieldsPageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
      additionalFieldsCurrentPage = 1;
      renderAdditionalFieldsPagination();
    });

    prevEl.addEventListener("click", () => {
      if (additionalFieldsCurrentPage <= 1) {
        return;
      }
      additionalFieldsCurrentPage -= 1;
      renderAdditionalFieldsPagination();
    });

    nextEl.addEventListener("click", () => {
      const rowCount = containerEl.querySelectorAll(".process-additional-field-row").length;
      const totalPages = Math.max(1, Math.ceil(rowCount / additionalFieldsPageSize));
      if (additionalFieldsCurrentPage >= totalPages) {
        return;
      }
      additionalFieldsCurrentPage += 1;
      renderAdditionalFieldsPagination();
    });
  }

  formEl.addEventListener("submit", () => {
    const rowEls = containerEl.querySelectorAll(".process-additional-field-row");
    rowEls.forEach((rowEl) => {
      const keyEl = rowEl.querySelector("input[name='additional_field_key']");
      const labelEl = rowEl.querySelector("input[name='additional_field_label']");
      const typeEl = rowEl.querySelector("select[name='additional_field_type']");
      const requiredEl = rowEl.querySelector("select[name='additional_field_required']");
      const sizeEl = rowEl.querySelector("input[name='additional_field_size']");
      if (!labelEl || !typeEl || !requiredEl || !sizeEl) {
        return;
      }
      const cleanLabel = String(labelEl.value || "").trim();
      labelEl.value = cleanLabel;
      const cleanType = String(typeEl.value || "text").trim().toLowerCase();
      if (cleanType === "header") {
        requiredEl.value = "0";
      }
      const isSizeEnabled = sizedTypes.has(cleanType);
      if (!isSizeEnabled) {
        sizeEl.value = "";
      }

      if (!cleanLabel) {
        if (keyEl) {
          keyEl.removeAttribute("name");
        }
        labelEl.removeAttribute("name");
        typeEl.removeAttribute("name");
        requiredEl.removeAttribute("name");
        sizeEl.removeAttribute("name");
      }
    });
  });

  renderAdditionalFieldsPagination();
}


function normalizeProcessEditTabKey_v1(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/_/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

// A URL nao e atualizada quando o utilizador clica numa aba interna (ver abaixo), por isso
// window.location fica parado na aba de entrada (ex.: "geral"). O mecanismo global de
// post-save-context (linha ~8194) captura essa URL parada no momento do submit e usa-a para
// reconstruir o destino apos o redirect do servidor, sobrepondo-se ao settings_tab correto
// que o backend ja devolve. Sincronizar aqui evita que essa aba fique presa em "geral".
function syncProcessEditTabToUrl_v1(tabKey) {
  if (settingsAction !== "edit" || !settingsEditKey) {
    return;
  }
  try {
    const url = new URL(window.location.href);
    if (normalizeProcessEditTabKey_v1(url.searchParams.get("settings_tab")) === tabKey) {
      return;
    }
    url.searchParams.set("settings_tab", tabKey);
    const newHref = url.pathname + url.search + url.hash;
    logAppGenesisProcessEditorDebugV1("syncProcessEditTabToUrl_v1:history.replaceState", {
      previousHref: window.location.href,
      newHref,
      tabKey,
      caller: "syncProcessEditTabToUrl_v1"
    });
    window.history.replaceState(window.history.state, document.title, newHref);
  } catch (error) {
    // Ignorar falha ao sincronizar o URL da aba ativa; a navegacao normal continua a funcionar.
  }
}

function setupProcessEditTabs() {
  const tabLinks = document.querySelectorAll("[data-process-edit-tab]");
  const panes = document.querySelectorAll("[data-process-edit-pane]");
  if (!tabLinks.length || !panes.length) {
    return;
  }

  function activateProcessTab(tabKey) {
    const normalizedTabKey = normalizeProcessEditTabKey_v1(tabKey);
    const hasTargetTab = Array.from(tabLinks).some(
      (tabLink) => (tabLink.getAttribute("data-process-edit-tab") || "") === normalizedTabKey
    );
    const resolvedTabKey = hasTargetTab ? normalizedTabKey : "geral";
    tabLinks.forEach((tabLink) => {
      const isActive = tabLink.getAttribute("data-process-edit-tab") === resolvedTabKey;
      tabLink.classList.toggle("active", isActive);
      tabLink.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    panes.forEach((pane) => {
      const isActive = pane.getAttribute("data-process-edit-pane") === resolvedTabKey;
      pane.classList.toggle("active", isActive);
    });
    logAppGenesisProcessEditorDebugV1("setupProcessEditTabs:activateProcessTab", {
      requestedTabKey: tabKey,
      resolvedTabKey,
      href: window.location.href
    });
    return resolvedTabKey;
  }

  tabLinks.forEach((tabLink) => {
    tabLink.addEventListener("click", (event) => {
      event.preventDefault();
      const tabKey = tabLink.getAttribute("data-process-edit-tab") || "geral";
      const resolvedTabKey = activateProcessTab(tabKey);
      syncProcessEditTabToUrl_v1(resolvedTabKey);
    });
  });

  if (settingsAction === "edit") {
    const urlSettingsTab = normalizeProcessEditTabKey_v1(
      new URLSearchParams(window.location.search).get("settings_tab")
    );
    const cleanSettingsTab = String(settingsTab || "").trim() || urlSettingsTab;
    if (cleanSettingsTab) {
      activateProcessTab(cleanSettingsTab);
    } else {
      activateProcessTab("campos-config");
    }
  } else {
    activateProcessTab("geral");
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

const avatarDataUri = buildAvatarDataUri(currentUserName);
if (userAvatarImageEl) {
  userAvatarImageEl.src = avatarDataUri;
}
if (dropdownAvatarImageEl) {
  dropdownAvatarImageEl.src = avatarDataUri;
}

if (
  appGenesisProcessMenuRuntimeV1 &&
  typeof appGenesisProcessMenuRuntimeV1.bindMenuButtonListeners === "function"
) {
  appGenesisProcessMenuRuntimeV1.bindMenuButtonListeners();
}

profileEditButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const cardId = button.getAttribute("data-edit-target");
    if (!cardId) {
      return;
    }
    closeAllProfileEdits();
    const card = document.getElementById(cardId);
    if (!card) {
      return;
    }
    card.classList.add("editing");
  });
});

if (dynamicProcessEditToggleEl) {
  dynamicProcessEditToggleEl.addEventListener("click", () => {
    // O botao vive num card separado (#dynamic-process-action-card), fora de #dynamic-process-card,
    // por isso a regra CSS ".card.editing .profile-edit-toggle" nao o alcanca mais. Escondemos aqui
    // explicitamente; restoreDynamicProcessEditToggleVisibility() reverte ao cancelar/fechar.
    setDynamicProcessEditToggleVisible(false);
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
    if (dynamicProcessEditFormEl) {
      dynamicProcessEditFormEl.reset();
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
  });
}

if (trainingOutrosEnabledEl) {
  trainingOutrosEnabledEl.addEventListener("change", () => {
    syncTrainingOutrosState();
  });
}

if (userMenuTriggerEl) {
  userMenuTriggerEl.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleUserDropdown();
  });
}

userDropdownLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    const menuKey = normalizeMenuKey(link.getAttribute("data-dropdown-menu") || "perfil");
    const targetSelector = link.getAttribute("data-dropdown-target") || "";
    if (!menuConfig[menuKey]) {
      closeUserDropdown();
      return;
    }
    if (targetSelector) {
      selectedTargetByMenu[menuKey] = targetSelector;
    }
    activateMenuTarget(menuKey, targetSelector);
    closeUserDropdown();
  });
});

document.addEventListener("click", (event) => {
  if (!userMenuEl || !userDropdownEl || userDropdownEl.hidden) {
    return;
  }
  if (!userMenuEl.contains(event.target)) {
    closeUserDropdown();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeUserDropdown();
  }
});

function setupGeneratedInviteLinkCopy() {
  const copyButtonEl = document.getElementById("generated-invite-link-copy-btn");
  if (!copyButtonEl) {
    return;
  }
  const targetId = String(copyButtonEl.getAttribute("data-copy-target") || "").trim();
  if (!targetId) {
    return;
  }
  const inputEl = document.getElementById(targetId);
  if (!inputEl) {
    return;
  }
  const defaultLabel = copyButtonEl.textContent || "Copiar";
  const showButtonFeedback = (label) => {
    copyButtonEl.textContent = label;
    window.setTimeout(() => {
      copyButtonEl.textContent = defaultLabel;
    }, 1200);
  };

  copyButtonEl.addEventListener("click", async () => {
    const copyValue = String(inputEl.value || "").trim();
    if (!copyValue) {
      showButtonFeedback("Sem link");
      return;
    }
    try {
      if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
        await navigator.clipboard.writeText(copyValue);
      } else {
        inputEl.removeAttribute("readonly");
        inputEl.select();
        document.execCommand("copy");
        inputEl.setAttribute("readonly", "readonly");
      }
      showButtonFeedback("Copiado");
    } catch (_error) {
      showButtonFeedback("Falhou");
    }
  });
}

// APPGENESIS_USER_CREATE_ACTION_MODE_V1_START
(function setupUserCreateActionModeV1() {
  "use strict";

  function syncUserCreateActionModeV1(root) {
    var scope = root || document;
    var card = scope.querySelector
      ? scope.querySelector("#create-user-card")
      : document.querySelector("#create-user-card");
    if (!card) {
      return;
    }
    var details = card.querySelector("#create-user-collapse");
    var isCreateOpen = Boolean(details && details.open);
    card
      .querySelectorAll("[data-appgenesis-hide-when-user-create-open='1']")
      .forEach(function (el) {
        el.hidden = isCreateOpen;
        el.setAttribute("aria-hidden", isCreateOpen ? "true" : "false");
      });
  }

  document.addEventListener("toggle", function (event) {
    if (
      event.target &&
      event.target.matches &&
      event.target.matches("#create-user-collapse")
    ) {
      syncUserCreateActionModeV1(document);
    }
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      syncUserCreateActionModeV1(document);
    });
  } else {
    syncUserCreateActionModeV1(document);
  }

  window.AppGenesisSyncUserCreateActionModeV1 = syncUserCreateActionModeV1;
})();
// APPGENESIS_USER_CREATE_ACTION_MODE_V1_END

function setupCreateUserGenerateLinkShortcut() {
  const shortcutButtonEl = document.getElementById("create-user-generate-link-shortcut-btn");
  if (!shortcutButtonEl) {
    return;
  }
  const linkSlotEl = document.querySelector(".entity-create-link-slot");

  if (linkSlotEl && !linkSlotEl.querySelector(".entity-create-link-output, .entity-create-link-message")) {
    linkSlotEl.style.display = "none";
  }

  function renderGenerateLinkContent(contentEl) {
    if (!linkSlotEl) {
      return;
    }
    linkSlotEl.innerHTML = "";
    linkSlotEl.appendChild(contentEl);
    linkSlotEl.style.display = "";
  }

  function showGenerateLinkMessage(message) {
    const messageEl = document.createElement("div");
    messageEl.className = "entity-create-link-message";
    messageEl.textContent = message;
    renderGenerateLinkContent(messageEl);
  }

  function showGeneratedSignupLink(signupLink) {
    const outputEl = document.createElement("div");
    outputEl.className = "entity-create-link-output";

    const inputEl = document.createElement("input");
    inputEl.id = "generated-invite-link-input";
    inputEl.type = "text";
    inputEl.className = "readonly-field";
    inputEl.value = signupLink;
    inputEl.readOnly = true;

    const copyButtonEl = document.createElement("button");
    copyButtonEl.id = "generated-invite-link-copy-btn";
    copyButtonEl.type = "button";
    copyButtonEl.className = "action-btn-secondary entity-create-link-copy-btn";
    copyButtonEl.setAttribute("data-copy-target", "generated-invite-link-input");
    copyButtonEl.textContent = "Copiar";

    outputEl.appendChild(inputEl);
    outputEl.appendChild(copyButtonEl);
    renderGenerateLinkContent(outputEl);
    setupGeneratedInviteLinkCopy();
  }

  shortcutButtonEl.addEventListener("click", (event) => {
    event.preventDefault();
    if (!Number.isFinite(currentEntityId) || currentEntityId <= 0) {
      showGenerateLinkMessage("Selecione uma entidade antes de gerar o link.");
      return;
    }
    const signupUrl = new URL("/login", window.location.origin);
    signupUrl.searchParams.set("mode", "signup");
    signupUrl.searchParams.set("entity_id", String(currentEntityId));
    showGeneratedSignupLink(signupUrl.toString());
  });
}

// APPGENESIS_UTILIZADOR_INVITE_LINK_HEADER_V1_START
// Reposiciona (nao clona) o botao "Gerar link de convite" e o seu slot de
// saida -- originalmente dentro de #create-user-card -- para dentro do
// cartao ativo de Utilizador (#admin-users-created-card). Necessario porque
// #create-user-card passou a ter data-admin-subprocess-inline-create-enabled
// e por isso fica display:none quando o formulario de criacao esta fechado
// (ver admin_subprocess_inline_create_v1.css), o que esconderia o botao e o
// link gerado independentemente do estado do formulario de criacao. O botao
// e marcado no template com data-admin-subprocess-inline-action="1" para ser
// recolocado no cabecalho pelo mecanismo generico ensureCardHeaderStructure
// (process_shell_runtime_v1.js) -- o mesmo que ja reposiciona o botao
// "+ Criar utilizador". Endpoint/logica de clique inalterados: apenas a
// posicao no DOM muda. Idempotente: seguro chamar mais de uma vez.
function relocateUtilizadorInviteLinkButtonV1() {
  const activeCard = document.getElementById("admin-users-created-card");
  const shortcutBtn = document.getElementById("create-user-generate-link-shortcut-btn");
  if (!activeCard || !shortcutBtn) {
    return;
  }
  if (shortcutBtn.parentElement !== activeCard) {
    activeCard.appendChild(shortcutBtn);
  }
  shortcutBtn.hidden = false;
}

function relocateUtilizadorInviteLinkSlotV1() {
  const activeCard = document.getElementById("admin-users-created-card");
  const linkSlotEl = document.querySelector(".entity-create-link-slot");
  if (!activeCard || !linkSlotEl) {
    return;
  }
  const headerEl = activeCard.querySelector(":scope > .appgenesis-card-header-v1");
  const desiredNextSibling = headerEl ? headerEl.nextSibling : activeCard.firstChild;
  if (linkSlotEl.parentElement !== activeCard || linkSlotEl.previousSibling !== headerEl) {
    activeCard.insertBefore(linkSlotEl, desiredNextSibling);
  }
  linkSlotEl.hidden = false;
}
// APPGENESIS_UTILIZADOR_INVITE_LINK_HEADER_V1_END

function setupSidebarSectionsEditor() {
  const sectionsBodyEl = document.getElementById("sidebar-sections-created-body");
  if (!sectionsBodyEl) {
    return;
  }

  const refreshActionStates = () => {
    const rows = Array.from(sectionsBodyEl.querySelectorAll("[data-sidebar-section-row]"));
    rows.forEach((rowEl, index) => {
      const upBtn = rowEl.querySelector("[data-sidebar-section-action='up']");
      const downBtn = rowEl.querySelector("[data-sidebar-section-action='down']");
      const removeBtn = rowEl.querySelector("[data-sidebar-section-action='remove']");
      const sectionKey = String(rowEl.getAttribute("data-sidebar-section-key") || "").trim().toLowerCase();
      const isProtected = sectionKey === "geral" || sectionKey === "igreja";

      if (upBtn) {
        upBtn.disabled = index === 0;
        upBtn.classList.toggle("table-icon-btn-disabled", upBtn.disabled);
      }
      if (downBtn) {
        downBtn.disabled = index === rows.length - 1;
        downBtn.classList.toggle("table-icon-btn-disabled", downBtn.disabled);
      }
      if (removeBtn) {
        removeBtn.disabled = rows.length <= 1 || isProtected;
        removeBtn.classList.toggle("table-icon-btn-disabled", removeBtn.disabled);
      }
    });
  };

  sectionsBodyEl.addEventListener("click", (event) => {
    const actionBtn = event.target.closest("[data-sidebar-section-action]");
    if (!actionBtn) {
      return;
    }
    const actionType = String(actionBtn.getAttribute("data-sidebar-section-action") || "").trim().toLowerCase();
    const rowEl = actionBtn.closest("[data-sidebar-section-row]");
    if (!rowEl || actionBtn.disabled) {
      return;
    }

    if (actionType === "up") {
      const previousRow = rowEl.previousElementSibling;
      if (previousRow) {
        sectionsBodyEl.insertBefore(rowEl, previousRow);
      }
      refreshActionStates();
      return;
    }

    if (actionType === "down") {
      const nextRow = rowEl.nextElementSibling;
      if (nextRow) {
        sectionsBodyEl.insertBefore(nextRow, rowEl);
      }
      refreshActionStates();
      return;
    }

    if (actionType === "remove") {
      rowEl.remove();
      refreshActionStates();
    }
  });

  refreshActionStates();
}

if (
  appGenesisProcessMenuRuntimeV1 &&
  typeof appGenesisProcessMenuRuntimeV1.bindHashChangeListener === "function"
) {
  appGenesisProcessMenuRuntimeV1.bindHashChangeListener();
}

syncTrainingOutrosState();
renderHomeCharts();
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
// (MENU) CHAVE UNICA PARA ITENS DINAMICOS DO PROCESSO - V1
//###################################################################################

function buildMenuItemUniqueKey_v1(item) {
  const target = String(item && item.target ? item.target : "").trim();
  const sectionKey = String(item && item.dynamicProcessSectionKey ? item.dynamicProcessSectionKey : "").trim();
  const profileSection = String(item && item.profileSection ? item.profileSection : "").trim();
  const label = String(item && item.label ? item.label : "").trim();

  return `${target}::${sectionKey}::${profileSection}::${label}`;
}

// APPGENESIS_MEU_PERFIL_QUANTITY_RENDERER_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_RENDERER_V1) CAMPOS QUANTIDADE NO FORMULARIO MEU PERFIL
//###################################################################################

(function setupMeuPerfilQuantityRendererV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function toSafeStringMeuPerfilQuantityV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function getMeuPerfilSettingQuantityV1() {
    if (typeof getSidebarMenuSetting === "function") {
      const foundSetting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
      if (foundSetting) {
        return foundSetting;
      }
    }

    return (Array.isArray(sidebarMenuSettings) ? sidebarMenuSettings : []).find((setting) => {
      return normalizeMenuKey(setting && setting.key) === MEU_PERFIL_MENU_KEY;
    }) || null;
  }

  function getFormControlByNameQuantityV1(form, name) {
    const cleanName = toSafeStringMeuPerfilQuantityV1(name);
    if (!form || !cleanName) {
      return null;
    }

    return Array.from(form.elements || []).find((element) => {
      return toSafeStringMeuPerfilQuantityV1(element.name) === cleanName;
    }) || null;
  }

  function getMeuPerfilQuantityFormV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function getMeuPerfilQuantityValuesV1(ruleKey) {
    const cleanRuleKey = normalizeMenuKey(ruleKey);
    const valuesByMenu = (
      menuProcessQuantityValuesMap &&
      typeof menuProcessQuantityValuesMap === "object" &&
      !Array.isArray(menuProcessQuantityValuesMap)
    )
      ? menuProcessQuantityValuesMap[MEU_PERFIL_MENU_KEY]
      : null;

    if (!valuesByMenu || typeof valuesByMenu !== "object" || Array.isArray(valuesByMenu)) {
      return [];
    }

    return normalizeProcessQuantityItems(valuesByMenu[cleanRuleKey]);
  }

  function buildListOptionsMapQuantityV1(setting) {
    const optionsMap = new Map();

    (Array.isArray(setting && setting.process_lists) ? setting.process_lists : []).forEach((processList) => {
      const listKey = normalizeMenuKey(processList && processList.key);
      if (!listKey) {
        return;
      }

      optionsMap.set(
        listKey,
        Array.isArray(processList.items)
          ? processList.items.map((item) => toSafeStringMeuPerfilQuantityV1(item).trim()).filter(Boolean)
          : []
      );
    });

    return optionsMap;
  }

  function buildFieldMetaMapQuantityV1(setting) {
    const listOptionsByKey = buildListOptionsMapQuantityV1(setting);
    const fieldMetaMap = new Map();

    (Array.isArray(setting && setting.process_field_options) ? setting.process_field_options : []).forEach((option) => {
      const fieldKey = normalizeMenuKey(option && option.key);
      if (!fieldKey) {
        return;
      }

      const fieldType = normalizeProcessFieldType(option.field_type);
      const listKey = normalizeMenuKey(option.list_key || option.listKey);
      const resolvedListOptions = Array.isArray(option.list_options)
        ? option.list_options.map((item) => toSafeStringMeuPerfilQuantityV1(item).trim()).filter(Boolean)
        : [];

      fieldMetaMap.set(fieldKey, {
        key: fieldKey,
        label: toSentenceCaseText(option.label || fieldKey),
        fieldType,
        size: normalizeProcessFieldSize(option.size, fieldType),
        isRequired: normalizeProcessFieldRequired(
          Object.prototype.hasOwnProperty.call(option, "is_required")
            ? option.is_required
            : option.required
        ),
        listKey,
        listOptions: resolvedListOptions.length
          ? resolvedListOptions
          : listOptionsByKey.get(listKey) || []
      });
    });

    return fieldMetaMap;
  }

  function resolveQuantityControlNameV1(fieldKey) {
    if (
      appGenesisProfileFieldRegistryV1 &&
      typeof appGenesisProfileFieldRegistryV1.resolveControlName === "function"
    ) {
      return appGenesisProfileFieldRegistryV1.resolveControlName(fieldKey);
    }

    const cleanFieldKey = normalizeMenuKey(fieldKey);
    if (!cleanFieldKey) {
      return "";
    }

    if (cleanFieldKey.startsWith("custom_")) {
      return "custom_field__" + cleanFieldKey;
    }

    const builtinNames = {
      nome: "full_name",
      telefone: "primary_phone",
      email: "login_email",
      pais: "country",
      data_nascimento: "birth_date",
      autorizacao_whatsapp: "whatsapp_notice_opt_in"
    };

    return builtinNames[cleanFieldKey] || cleanFieldKey;
  }

  function parseQuantityCountV1(rawValue, maxItems) {
    const parsedValue = Number.parseInt(toSafeStringMeuPerfilQuantityV1(rawValue).trim(), 10);
    const parsedMaxItems = Number.parseInt(toSafeStringMeuPerfilQuantityV1(maxItems || "1").trim(), 10);
    const safeMaxItems = Number.isFinite(parsedMaxItems) ? Math.min(Math.max(parsedMaxItems, 1), 50) : 1;

    if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
      return 0;
    }

    return Math.min(parsedValue, safeMaxItems);
  }

  function readQuantityControlValueV1(control, fieldType) {
    if (!control) {
      return "";
    }

    if (fieldType === "flag") {
      return control.checked ? "1" : "0";
    }

    return toSafeStringMeuPerfilQuantityV1(control.value).trim();
  }

  function createQuantityFieldControlV1(rule, itemIndex, fieldMeta, existingValue) {
    const fieldType = normalizeProcessFieldType(fieldMeta.fieldType);
    const fieldName = "process_quantity_field__" + rule.key + "__" + itemIndex + "__" + fieldMeta.key;
    let control = null;

    if (fieldType === "list") {
      control = document.createElement("select");
      const emptyOption = document.createElement("option");
      emptyOption.value = "";
      emptyOption.textContent = "Selecione";
      control.appendChild(emptyOption);

      (Array.isArray(fieldMeta.listOptions) ? fieldMeta.listOptions : []).forEach((optionValue) => {
        const option = document.createElement("option");
        option.value = optionValue;
        option.textContent = optionValue;
        if (toSafeStringMeuPerfilQuantityV1(existingValue) === toSafeStringMeuPerfilQuantityV1(optionValue)) {
          option.selected = true;
        }
        control.appendChild(option);
      });
    } else {
      control = document.createElement("input");
      if (fieldType === "flag") {
        control.type = "checkbox";
        control.value = "1";
        control.checked = ["1", "true", "sim", "yes", "on"].includes(
          toSafeStringMeuPerfilQuantityV1(existingValue).trim().toLowerCase()
        );
      } else {
        control.type = getDynamicProcessInputType(fieldType);
      }

      if (fieldType !== "flag") {
        control.value = toSafeStringMeuPerfilQuantityV1(existingValue);
      }
    }

    control.name = fieldName;
    control.dataset.processQuantityRuleKey = rule.key;
    control.dataset.processQuantityItemIndex = String(itemIndex);
    control.dataset.processQuantityFieldKey = fieldMeta.key;

    if (fieldMeta.isRequired && fieldType !== "flag") {
      control.required = true;
    }

    if (fieldMeta.size && ["text", "email", "phone"].includes(fieldType)) {
      control.maxLength = fieldMeta.size;
    }

    return control;
  }

  function syncQuantityPayloadV1(rule, host) {
    const rows = Array.from(host.querySelectorAll("[data-process-quantity-item-index]"));
    const payload = [];

    rows.forEach((row) => {
      const item = {};

      Array.from(row.querySelectorAll("[data-process-quantity-field-key]")).forEach((control) => {
        const fieldKey = normalizeMenuKey(control.dataset.processQuantityFieldKey);
        if (!fieldKey) {
          return;
        }

        const fieldType = normalizeProcessFieldType(control.dataset.processQuantityFieldType || control.type);
        const value = readQuantityControlValueV1(control, fieldType);

        if (value) {
          item[fieldKey] = value;
        }
      });

      payload.push(item);
    });

    const payloadInput = host.querySelector("input[name='process_quantity_payload__" + rule.key + "']");
    if (payloadInput) {
      payloadInput.value = JSON.stringify(payload);
    }
  }

  //###################################################################################
  // (2) RENDERIZAR UMA REGRA
  //###################################################################################

  function setupMeuPerfilQuantityRuleV1(form, setting, rule, fieldMetaMap) {
    const quantityControlName = resolveQuantityControlNameV1(rule.quantityFieldKey);
    const quantityControl = getFormControlByNameQuantityV1(form, quantityControlName);

    if (!quantityControl) {
      return;
    }

    const quantityFieldWrapper = quantityControl.closest(".field") || quantityControl.parentElement;
    const personalGrid = quantityControl.closest(".personal-grid") || form.querySelector(".personal-grid") || form;
    const sectionPane = rule.headerKey
      || toSafeStringMeuPerfilQuantityV1(quantityFieldWrapper && quantityFieldWrapper.dataset.profileSectionPane)
      || "";

    let host = form.querySelector("[data-profile-quantity-rule-key='" + rule.key + "']");

    if (!host) {
      host = document.createElement("div");
      host.className = "field full profile-quantity-rule-v1";
      host.dataset.profileQuantityRuleKey = rule.key;
      host.dataset.profileSectionPane = sectionPane;

      if (quantityFieldWrapper && quantityFieldWrapper.parentElement) {
        quantityFieldWrapper.insertAdjacentElement("afterend", host);
      } else {
        personalGrid.appendChild(host);
      }
    }

    let payloadInput = host.querySelector("input[name='process_quantity_payload__" + rule.key + "']");

    if (!payloadInput) {
      payloadInput = document.createElement("input");
      payloadInput.type = "hidden";
      payloadInput.name = "process_quantity_payload__" + rule.key;
      payloadInput.value = "[]";
      host.appendChild(payloadInput);
    }

    function renderQuantityBlocksV1() {
      const existingItems = getMeuPerfilQuantityValuesV1(rule.key);
      const requestedCount = parseQuantityCountV1(quantityControl.value, rule.maxItems);
      const fallbackCount = requestedCount || existingItems.length;
      const count = parseQuantityCountV1(String(fallbackCount), rule.maxItems);

      Array.from(host.querySelectorAll(".profile-quantity-items-wrap-v1")).forEach((element) => {
        element.remove();
      });

      if (!count) {
        payloadInput.value = "[]";
        return;
      }

      const wrapper = document.createElement("div");
      wrapper.className = "profile-quantity-items-wrap-v1";
      wrapper.dataset.processQuantityRuleKey = rule.key;

      for (let itemIndex = 0; itemIndex < count; itemIndex += 1) {
        const itemValues = existingItems[itemIndex] || {};
        const itemBlock = document.createElement("div");
        itemBlock.className = "profile-quantity-item-v1";
        itemBlock.dataset.processQuantityItemIndex = String(itemIndex);

        const itemTitle = document.createElement("h4");
        itemTitle.className = "profile-quantity-item-title-v1";
        itemTitle.textContent = (rule.itemLabel || "Item") + " " + (itemIndex + 1);
        itemBlock.appendChild(itemTitle);

        const fieldsGrid = document.createElement("div");
        fieldsGrid.className = "personal-grid profile-quantity-item-grid-v1";

        rule.repeatedFieldKeys.forEach((fieldKey) => {
          const fieldMeta = fieldMetaMap.get(fieldKey);

          if (!fieldMeta) {
            return;
          }

          const fieldWrapper = document.createElement("div");
          fieldWrapper.className = "field";
          fieldWrapper.dataset.profileSectionPane = sectionPane;
          fieldWrapper.dataset.profileFieldKey = fieldKey;

          const label = document.createElement("label");
          label.textContent = fieldMeta.label + (fieldMeta.isRequired ? " *" : "");

          const control = createQuantityFieldControlV1(
            rule,
            itemIndex,
            fieldMeta,
            itemValues[fieldKey] || ""
          );

          control.dataset.processQuantityFieldType = fieldMeta.fieldType;

          control.addEventListener("input", function () {
            syncQuantityPayloadV1(rule, host);
          });
          control.addEventListener("change", function () {
            syncQuantityPayloadV1(rule, host);
          });

          fieldWrapper.appendChild(label);
          fieldWrapper.appendChild(control);
          fieldsGrid.appendChild(fieldWrapper);
        });

        itemBlock.appendChild(fieldsGrid);
        wrapper.appendChild(itemBlock);
      }

      host.appendChild(wrapper);
      syncQuantityPayloadV1(rule, host);
    }

    quantityControl.addEventListener("input", renderQuantityBlocksV1);
    quantityControl.addEventListener("change", renderQuantityBlocksV1);

    if (!toSafeStringMeuPerfilQuantityV1(quantityControl.value).trim()) {
      const existingItems = getMeuPerfilQuantityValuesV1(rule.key);
      if (existingItems.length) {
        quantityControl.value = String(Math.min(existingItems.length, rule.maxItems || existingItems.length));
      }
    }

    renderQuantityBlocksV1();
  }

  //###################################################################################
  // (3) INICIALIZAR TODAS AS REGRAS
  //###################################################################################

  function setupMeuPerfilQuantityRulesV1() {
    const form = getMeuPerfilQuantityFormV1();
    const setting = getMeuPerfilSettingQuantityV1();

    if (!form || !setting || form.dataset.meuPerfilQuantityRendererBoundV1 === "1") {
      return;
    }

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    if (!rules.length) {
      return;
    }

    const fieldMetaMap = buildFieldMetaMapQuantityV1(setting);

    form.dataset.meuPerfilQuantityRendererBoundV1 = "1";

    rules.forEach((rule) => {
      setupMeuPerfilQuantityRuleV1(form, setting, rule, fieldMetaMap);
    });

    form.addEventListener("submit", function () {
      Array.from(form.querySelectorAll("[data-profile-quantity-rule-key]")).forEach((host) => {
        const ruleKey = normalizeMenuKey(host.dataset.profileQuantityRuleKey);
        const rule = rules.find((item) => item.key === ruleKey);
        if (rule) {
          syncQuantityPayloadV1(rule, host);
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupMeuPerfilQuantityRulesV1);
  } else {
    setupMeuPerfilQuantityRulesV1();
  }

  window.setTimeout(setupMeuPerfilQuantityRulesV1, 150);
  window.setTimeout(setupMeuPerfilQuantityRulesV1, 600);
})();

// APPGENESIS_MEU_PERFIL_QUANTITY_RENDERER_V1_END

// APPGENESIS_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1) VISUALIZACAO DOS CAMPOS QUANTIDADE
//###################################################################################

(function setupMeuPerfilQuantityReadonlyRendererV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeTextQuantityReadonlyV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function getMeuPerfilSettingQuantityReadonlyV1() {
    if (typeof getSidebarMenuSetting === "function") {
      const foundSetting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
      if (foundSetting) {
        return foundSetting;
      }
    }

    return (Array.isArray(sidebarMenuSettings) ? sidebarMenuSettings : []).find((setting) => {
      return normalizeMenuKey(setting && setting.key) === MEU_PERFIL_MENU_KEY;
    }) || null;
  }

  function getReadonlyGridQuantityReadonlyV1() {
    return document.querySelector(`${getMeuPerfilPersonalCardTargetV1()} .profile-readonly .personal-grid`);
  }

  function getQuantityReadonlyValuesV1(ruleKey) {
    const cleanRuleKey = normalizeMenuKey(ruleKey);
    const valuesByMenu = (
      menuProcessQuantityValuesMap &&
      typeof menuProcessQuantityValuesMap === "object" &&
      !Array.isArray(menuProcessQuantityValuesMap)
    )
      ? menuProcessQuantityValuesMap[MEU_PERFIL_MENU_KEY]
      : null;

    if (!valuesByMenu || typeof valuesByMenu !== "object" || Array.isArray(valuesByMenu)) {
      return [];
    }

    return normalizeProcessQuantityItems(valuesByMenu[cleanRuleKey]);
  }

  function buildFieldMetaMapQuantityReadonlyV1(setting) {
    const metaMap = new Map();

    (Array.isArray(setting && setting.process_field_options) ? setting.process_field_options : []).forEach((option) => {
      const fieldKey = normalizeMenuKey(option && option.key);

      if (!fieldKey) {
        return;
      }

      metaMap.set(fieldKey, {
        key: fieldKey,
        label: toSentenceCaseText(option.label || fieldKey),
        fieldType: normalizeProcessFieldType(option.field_type)
      });
    });

    return metaMap;
  }

  function formatReadonlyValueQuantityReadonlyV1(value, fieldType) {
    const cleanValue = safeTextQuantityReadonlyV1(value).trim();

    if (!cleanValue) {
      return "-";
    }

    if (fieldType === "flag") {
      return ["1", "true", "sim", "yes", "on"].includes(cleanValue.toLowerCase())
        ? "Sim"
        : "Não";
    }

    return cleanValue;
  }

  function applyCurrentProfileSectionToQuantityReadonlyV1(host) {
    if (!host) {
      return;
    }

    const sectionInput = document.querySelector("[data-meu-perfil-section-input]");
    const currentSection = normalizeMenuKey(sectionInput ? sectionInput.value : "");
    const hostSection = normalizeMenuKey(host.dataset.profileSectionPane);

    if (!currentSection || !hostSection) {
      return;
    }

    host.style.display = currentSection === hostSection ? "" : "none";
  }

  function findInsertionPointQuantityReadonlyV1(grid, rule) {
    if (!grid || !rule) {
      return null;
    }

    const quantityFieldKey = normalizeMenuKey(rule.quantityFieldKey);

    if (!quantityFieldKey) {
      return null;
    }

    return grid.querySelector("[data-profile-field-key='" + quantityFieldKey + "']");
  }

  //###################################################################################
  // (2) RENDERIZAR REGRA READONLY
  //###################################################################################

  function renderReadonlyRuleQuantityReadonlyV1(grid, setting, rule, fieldMetaMap) {
    const values = getQuantityReadonlyValuesV1(rule.key);

    if (!Array.isArray(values) || !values.length) {
      return;
    }

    const host = document.createElement("div");

    host.className = "personal-item profile-quantity-readonly-v1";
    host.style.gridColumn = "1 / -1";
    host.dataset.profileQuantityReadonlyRuleKey = rule.key;
    host.dataset.profileSectionPane = rule.headerKey || "";

    const mainLabel = document.createElement("span");
    mainLabel.className = "personal-label";
    mainLabel.textContent = rule.label || rule.itemLabel || "Itens";
    host.appendChild(mainLabel);

    const listWrapper = document.createElement("div");
    listWrapper.className = "profile-quantity-readonly-list-v1";

    values.forEach((itemValues, itemIndex) => {
      const itemBlock = document.createElement("div");
      itemBlock.className = "profile-quantity-readonly-item-v1";

      const itemTitle = document.createElement("strong");
      itemTitle.className = "personal-value profile-quantity-readonly-title-v1";
      itemTitle.textContent = (rule.itemLabel || "Item") + " " + (itemIndex + 1);
      itemBlock.appendChild(itemTitle);

      const fieldsList = document.createElement("div");
      fieldsList.className = "profile-quantity-readonly-fields-v1";

      rule.repeatedFieldKeys.forEach((fieldKey) => {
        const cleanFieldKey = normalizeMenuKey(fieldKey);
        const fieldMeta = fieldMetaMap.get(cleanFieldKey) || {
          label: cleanFieldKey,
          fieldType: "text"
        };

        const row = document.createElement("div");
        row.className = "profile-quantity-readonly-field-v1";

        const label = document.createElement("span");
        label.className = "personal-label";
        label.textContent = fieldMeta.label || cleanFieldKey;

        const value = document.createElement("strong");
        value.className = "personal-value";
        value.textContent = formatReadonlyValueQuantityReadonlyV1(
          itemValues ? itemValues[cleanFieldKey] : "",
          fieldMeta.fieldType
        );

        row.appendChild(label);
        row.appendChild(value);
        fieldsList.appendChild(row);
      });

      itemBlock.appendChild(fieldsList);
      listWrapper.appendChild(itemBlock);
    });

    host.appendChild(listWrapper);

    const insertionPoint = findInsertionPointQuantityReadonlyV1(grid, rule);

    if (insertionPoint && insertionPoint.parentElement === grid) {
      insertionPoint.insertAdjacentElement("afterend", host);
    } else {
      grid.appendChild(host);
    }

    applyCurrentProfileSectionToQuantityReadonlyV1(host);
  }

  //###################################################################################
  // (3) RENDERIZAR TODAS AS REGRAS
  //###################################################################################

  function renderMeuPerfilQuantityReadonlyV1() {
    const grid = getReadonlyGridQuantityReadonlyV1();
    const setting = getMeuPerfilSettingQuantityReadonlyV1();

    if (!grid || !setting) {
      return;
    }

    Array.from(grid.querySelectorAll("[data-profile-quantity-readonly-rule-key]")).forEach((element) => {
      element.remove();
    });

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    if (!rules.length) {
      return;
    }

    const fieldMetaMap = buildFieldMetaMapQuantityReadonlyV1(setting);

    rules.forEach((rule) => {
      renderReadonlyRuleQuantityReadonlyV1(grid, setting, rule, fieldMetaMap);
    });
  }

  //###################################################################################
  // (4) SINCRONIZAR COM AS ABAS DO MEU PERFIL
  //###################################################################################

  function refreshMeuPerfilQuantityReadonlyVisibilityV1() {
    document
      .querySelectorAll("[data-profile-quantity-readonly-rule-key]")
      .forEach(applyCurrentProfileSectionToQuantityReadonlyV1);
  }

  document.addEventListener("click", function () {
    window.setTimeout(refreshMeuPerfilQuantityReadonlyVisibilityV1, 0);
    window.setTimeout(refreshMeuPerfilQuantityReadonlyVisibilityV1, 80);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderMeuPerfilQuantityReadonlyV1);
  } else {
    renderMeuPerfilQuantityReadonlyV1();
  }

  window.setTimeout(renderMeuPerfilQuantityReadonlyV1, 150);
  window.setTimeout(renderMeuPerfilQuantityReadonlyV1, 600);
})();

// APPGENESIS_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_END



// Legacy post-save, initial profile section, and subsequent-visibility engines removed after migration to canonical modules.\n\n/* APPGENESIS_AUTO_DISMISS_FLASH_MESSAGES_V1_START */
function appgenesisAutoDismissFlashMessages_v1() {
  const successAlerts = Array.from(document.querySelectorAll(".alert.ok"));

  successAlerts.forEach((alertElement) => {
    if (!alertElement || alertElement.dataset.appgenesisAutoDismiss === "1") {
      return;
    }

    alertElement.dataset.appgenesisAutoDismiss = "1";

    window.setTimeout(() => {
      alertElement.style.transition = "opacity 250ms ease, max-height 250ms ease, margin 250ms ease, padding 250ms ease";
      alertElement.style.opacity = "0";
      alertElement.style.maxHeight = "0";
      alertElement.style.marginTop = "0";
      alertElement.style.marginBottom = "0";
      alertElement.style.paddingTop = "0";
      alertElement.style.paddingBottom = "0";
      alertElement.style.overflow = "hidden";

      window.setTimeout(() => {
        alertElement.remove();
      }, 300);
    }, 5000);
  });

  const url = new URL(window.location.href);
  const transientParams = [
    "success",
    "profile_success",
    "settings_success",
  ];

  let changed = false;

  transientParams.forEach((paramName) => {
    if (url.searchParams.has(paramName)) {
      url.searchParams.delete(paramName);
      changed = true;
    }
  });

  if (changed) {
    const cleanUrl = `${url.pathname}${url.search}${url.hash}`;
    window.history.replaceState({}, document.title, cleanUrl);
  }
}

document.addEventListener("DOMContentLoaded", appgenesisAutoDismissFlashMessages_v1);
/* APPGENESIS_AUTO_DISMISS_FLASH_MESSAGES_V1_END */

// APPGENESIS_ADMIN_POPSTATE_NAV_V1_START
window.addEventListener("popstate", function () {
  try {
    const params = new URLSearchParams(window.location.search);
    const menuKeyFromUrl = normalizeMenuKey(String(params.get("menu") || "").trim());
    if (menuKeyFromUrl !== "administrativo" || !menuConfig["administrativo"]) {
      return;
    }
    const adminTab = String(params.get("admin_tab") || "").trim().toLowerCase();
    const resolvedTarget = resolveAdminSelectedTargetV1({
      initialAdminTab: adminTab,
      startupHash: "",
      initialMenuTarget: String(params.get("target") || ""),
      settingsEditKey: ""
    });
    if (!resolvedTarget) {
      return;
    }
    selectedTargetByMenu["administrativo"] = resolvedTarget;
    setActiveSubmenu(resolvedTarget);
    applyContentForMenuTarget("administrativo", resolvedTarget);
    if (resolvedTarget === "#dynamic-process-card") {
      const sectionKey = adminTab || String(selectedDynamicSectionByMenu["administrativo"] || "");
      if (sectionKey) {
        selectedDynamicSectionByMenu["administrativo"] = sectionKey;
      }
      renderDynamicProcessCard(
        "administrativo",
        String(selectedDynamicSectionByMenu["administrativo"] || "")
      );
    }
    debugTabsLogV1("popstate:admin-restored", { adminTab, resolvedTarget });
  } catch (_) {}
});
// APPGENESIS_ADMIN_POPSTATE_NAV_V1_END

//###################################################################################
// (9) ORQUESTRACAO DA PAGINA
//###################################################################################

const newUserPageBootstrapStateV1 = {
  initialized: false,
  references: null,
  lastContext: null
};

function collectNewUserDomReferencesV1(root = document) {
  const scopeRoot = root && typeof root.querySelector === "function" ? root : document;

  return {
    documentRef: scopeRoot,
    bodyEl: scopeRoot.body || null,
    mainEl: typeof scopeRoot.querySelector === "function" ? scopeRoot.querySelector("main") : null,
    pageRootEl: typeof scopeRoot.querySelector === "function"
      ? scopeRoot.querySelector("[data-appgenesis-new-user-page]")
      : null,
    shellEl: typeof scopeRoot.querySelector === "function"
      ? scopeRoot.querySelector("[data-process-shell]")
      : null,
    menuRootEl: typeof scopeRoot.querySelector === "function"
      ? scopeRoot.querySelector("[data-process-menu-root]")
      : null,
    formEl: typeof scopeRoot.querySelector === "function"
      ? scopeRoot.querySelector("form")
      : null
  };
}

function getNewUserRuntimeRefsV1(context) {
  if (!context || typeof context !== "object") {
    return null;
  }

  if (!context.runtimeRefs || typeof context.runtimeRefs !== "object") {
    context.runtimeRefs = {};
  }

  return context.runtimeRefs;
}

function initializeNavigationRuntimeV1(context = {}) {
  if (context.navigationRuntimeInitialized) {
    return context;
  }

  const runtimeRefs = getNewUserRuntimeRefsV1(context);

  if (runtimeRefs) {
    runtimeRefs.navigation = {
      root: context.documentRef || document
    };
  }

  if (
    appGenesisProcessMenuRuntimeV1 &&
    typeof appGenesisProcessMenuRuntimeV1.bindMenuButtonListeners === "function"
  ) {
    appGenesisProcessMenuRuntimeV1.bindMenuButtonListeners();
  }

  if (
    appGenesisProcessMenuRuntimeV1 &&
    typeof appGenesisProcessMenuRuntimeV1.bindHashChangeListener === "function"
  ) {
    appGenesisProcessMenuRuntimeV1.bindHashChangeListener();
  }

  if (typeof syncTrainingOutrosState === "function") {
    syncTrainingOutrosState();
  }
  if (typeof renderHomeCharts === "function") {
    renderHomeCharts();
  }
  if (typeof setupReadOnlyCards === "function") {
    setupReadOnlyCards();
  }
  if (typeof setupProfileProcessTabs === "function") {
    setupProfileProcessTabs();
  }

  context.navigationRuntimeInitialized = true;
  return context;
}

function initializeProfileRuntimeV1(context = {}) {
  if (context.profileRuntimeInitialized) {
    return context;
  }

  const personalCardEl = getMeuPerfilPersonalCardElV1();
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  const setting = typeof getSidebarMenuSetting === "function" ? getSidebarMenuSetting(MEU_PERFIL_MENU_KEY) : null;
  const runtimeRefs = getNewUserRuntimeRefsV1(context);

  if (!personalCardEl || !formEl || !setting) {
    context.profileRuntimeInitialized = true;
    return context;
  }

  const quantityAdapter = appGenesisProcessQuantityRuntimeV1 &&
    typeof appGenesisProcessQuantityRuntimeV1.createMeuPerfilQuantityAdapterV1 === "function"
      ? appGenesisProcessQuantityRuntimeV1.createMeuPerfilQuantityAdapterV1({
          root: personalCardEl,
          getSetting: () => setting
        })
      : null;
  const quantityContext = {
    mode: "profile",
    adapterName: "profile",
    root: personalCardEl,
    formEl,
    readonlyGridEl: personalCardEl.querySelector(".profile-readonly .personal-grid"),
    editGridEl: formEl.querySelector(".personal-grid"),
    setting,
    rules: setting.process_quantity_fields,
    getSetting: () => setting,
    getValues: collectCurrentMeuPerfilQuantityValues,
    getCurrentSection: getCurrentProfileSectionV1,
    adapter: quantityAdapter || undefined
  };
  const subsequentContext = {
    mode: "profile",
    root: personalCardEl,
    formEl,
    setting,
    rules: setting.process_subsequent_fields,
    getValues: collectCurrentMeuPerfilProcessValues,
    getCurrentSection: getCurrentProfileSectionV1
  };

  if (
    appGenesisProcessQuantityRuntimeV1 &&
    typeof appGenesisProcessQuantityRuntimeV1.initialize === "function"
  ) {
    appGenesisProcessQuantityRuntimeV1.initialize(quantityContext);
  }

  if (
    appGenesisProcessSubsequentVisibilityRuntimeV1 &&
    typeof appGenesisProcessSubsequentVisibilityRuntimeV1.initialize === "function"
  ) {
    appGenesisProcessSubsequentVisibilityRuntimeV1.initialize(subsequentContext);
  }

  if (runtimeRefs) {
    runtimeRefs.profile = {
      personalCardEl,
      formEl,
      setting,
      quantityAdapter,
      quantityContext,
      subsequentContext
    };
  }

  context.profileRuntimeInitialized = true;
  return context;
}

function initializeDynamicProcessRuntimeV1(context = {}) {
  if (context.dynamicProcessRuntimeInitialized) {
    return context;
  }

  const formEl = dynamicProcessEditFormEl;
  const cleanMenuKey = normalizeMenuKey(dynamicProcessMenuKeyInputEl ? dynamicProcessMenuKeyInputEl.value : "");
  const setting = cleanMenuKey && typeof getSidebarMenuSetting === "function" ? getSidebarMenuSetting(cleanMenuKey) : null;
  const runtimeRefs = getNewUserRuntimeRefsV1(context);

  if (!formEl || !setting) {
    context.dynamicProcessRuntimeInitialized = true;
    return context;
  }

  const quantityAdapter = appGenesisProcessQuantityRuntimeV1 &&
    typeof appGenesisProcessQuantityRuntimeV1.createDynamicProcessQuantityAdapterV1 === "function"
      ? appGenesisProcessQuantityRuntimeV1.createDynamicProcessQuantityAdapterV1({
          root: document,
          formEl,
          readonlyGridEl: dynamicProcessReadOnlyGridEl || null,
          editGridEl: dynamicProcessEditGridEl || null,
          getSetting: () => setting,
          getCurrentSection: () => normalizeMenuKey(dynamicProcessSectionKeyInputEl ? dynamicProcessSectionKeyInputEl.value : "")
        })
      : null;
  const quantityContext = {
    mode: "dynamic",
    adapterName: "dynamic",
    root: document,
    formEl,
    readonlyGridEl: dynamicProcessReadOnlyGridEl || null,
    editGridEl: dynamicProcessEditGridEl || null,
    setting,
    rules: setting.process_quantity_fields,
    getSetting: () => setting,
    getValues: () => collectCurrentDynamicProcessQuantityValues(cleanMenuKey),
    getCurrentSection: () => normalizeMenuKey(dynamicProcessSectionKeyInputEl ? dynamicProcessSectionKeyInputEl.value : ""),
    adapter: quantityAdapter || undefined
  };
  const subsequentContext = {
    mode: "dynamic",
    root: document,
    formEl,
    setting,
    rules: setting.process_subsequent_fields,
    getValues: () => collectCurrentDynamicProcessValues(cleanMenuKey),
    getCurrentSection: () => normalizeMenuKey(dynamicProcessSectionKeyInputEl ? dynamicProcessSectionKeyInputEl.value : "")
  };

  if (
    appGenesisProcessQuantityRuntimeV1 &&
    typeof appGenesisProcessQuantityRuntimeV1.initialize === "function"
  ) {
    appGenesisProcessQuantityRuntimeV1.initialize(quantityContext);
  }

  if (
    appGenesisProcessSubsequentVisibilityRuntimeV1 &&
    typeof appGenesisProcessSubsequentVisibilityRuntimeV1.initialize === "function"
  ) {
    appGenesisProcessSubsequentVisibilityRuntimeV1.initialize(subsequentContext);
  }

  if (runtimeRefs) {
    runtimeRefs.dynamicProcess = {
      formEl,
      setting,
      quantityAdapter,
      quantityContext,
      subsequentContext
    };
  }

  context.dynamicProcessRuntimeInitialized = true;
  return context;
}

function initializeAdminRuntimeV1(context = {}) {
  if (context.adminRuntimeInitialized) {
    return context;
  }

  const runtimeRefs = getNewUserRuntimeRefsV1(context);

  if (typeof setupProcessFieldsBuilder === "function") {
    setupProcessFieldsBuilder();
  }
  if (typeof setupProcessAdditionalFieldsManagerV3 === "function") {
    setupProcessAdditionalFieldsManagerV3();
  }

  if (runtimeRefs) {
    runtimeRefs.admin = {
      builderInitialized: true,
      additionalFieldsManagerInitialized: true
    };
  }

  context.adminRuntimeInitialized = true;
  return context;
}

function initializeTableRuntimeV1(context = {}) {
  if (context.tableRuntimeInitialized) {
    return context;
  }

  const runtimeRefs = getNewUserRuntimeRefsV1(context);
  const prefixes = [
    "recent-entities",
    "inactive-entities",
    "admin-users",
    "menu-ativo",
    "menu-inativo",
    "sessoes-ativo",
    "sessoes-inativo"
  ];

  if (typeof setupTableLimiter === "function") {
    prefixes.forEach((prefix) => {
      setupTableLimiter(prefix);
    });
  }

  if (runtimeRefs) {
    runtimeRefs.table = { prefixes };
  }

  context.tableRuntimeInitialized = true;
  return context;
}

function initializeInviteRuntimeV1(context = {}) {
  if (context.inviteRuntimeInitialized) {
    return context;
  }

  const runtimeRefs = getNewUserRuntimeRefsV1(context);

  if (typeof setupGeneratedInviteLinkCopy === "function") {
    setupGeneratedInviteLinkCopy();
  }
  if (typeof setupCreateUserGenerateLinkShortcut === "function") {
    setupCreateUserGenerateLinkShortcut();
  }

  if (runtimeRefs) {
    runtimeRefs.invite = {
      linkCopyInitialized: true,
      shortcutInitialized: true
    };
  }

  context.inviteRuntimeInitialized = true;
  return context;
}

function initializeProcessSettingsRuntimeV1(context = {}) {
  if (context.processSettingsRuntimeInitialized) {
    return context;
  }

  const runtimeRefs = getNewUserRuntimeRefsV1(context);

  if (typeof setupProcessEditTabs === "function") {
    setupProcessEditTabs();
  }

  if (runtimeRefs) {
    runtimeRefs.processSettings = {
      tabsInitialized: true
    };
  }

  context.processSettingsRuntimeInitialized = true;
  return context;
}

function initializePostSaveRuntimeV1(context = {}) {
  if (context.postSaveRuntimeInitialized) {
    return context;
  }

  const runtimeRefs = getNewUserRuntimeRefsV1(context);

  if (
    window.AppGenesisPostSaveContextCaptureV1 &&
    typeof window.AppGenesisPostSaveContextCaptureV1.initialize === "function"
  ) {
    const captureContext = window.AppGenesisPostSaveContextCaptureV1.initialize({
      root: context.documentRef || document
    });

    if (runtimeRefs) {
      runtimeRefs.postSave = {
        captureContext
      };
    }
  }

  context.postSaveRuntimeInitialized = true;

  if (typeof appgenesisAutoDismissFlashMessages_v1 === "function") {
    appgenesisAutoDismissFlashMessages_v1();
  }

  return context;
}

function initializeNewUserPageV1() {
  if (newUserPageBootstrapStateV1.initialized) {
    return newUserPageBootstrapStateV1.lastContext || newUserPageBootstrapStateV1;
  }

  const references = collectNewUserDomReferencesV1(document);
  const context = {
    bootstrap,
    documentRef: document,
    windowRef: window,
    references
  };

  initializeNavigationRuntimeV1(context);
  initializeProfileRuntimeV1(context);
  initializeDynamicProcessRuntimeV1(context);
  initializeAdminRuntimeV1(context);
  initializeTableRuntimeV1(context);
  initializeInviteRuntimeV1(context);
  initializeProcessSettingsRuntimeV1(context);
  initializePostSaveRuntimeV1(context);

  if (
    appGenesisProcessMenuRuntimeV1 &&
    typeof appGenesisProcessMenuRuntimeV1.activateMenu === "function"
  ) {
    appGenesisProcessMenuRuntimeV1.activateMenu(startupMenu, {
      resetDynamicToFirst: false,
      source: "bootstrap:finalize"
    });
  }

  if (
    appGenesisProcessMenuRuntimeV1 &&
    typeof appGenesisProcessMenuRuntimeV1.handleHashNavigation === "function"
  ) {
    appGenesisProcessMenuRuntimeV1.handleHashNavigation(window.location.hash || "");
  }

  newUserPageBootstrapStateV1.initialized = true;
  newUserPageBootstrapStateV1.references = references;
  newUserPageBootstrapStateV1.lastContext = context;

  document.dispatchEvent(
    new CustomEvent("appgenesis:new-user-page-ready", {
      detail: context
    })
  );

  return context;
}

window.AppGenesisNewUserPageV1 = Object.freeze({
  collectNewUserDomReferencesV1,
  initializeNavigationRuntimeV1,
  initializeProfileRuntimeV1,
  initializeDynamicProcessRuntimeV1,
  initializeAdminRuntimeV1,
  initializeTableRuntimeV1,
  initializeInviteRuntimeV1,
  initializeProcessSettingsRuntimeV1,
  initializePostSaveRuntimeV1,
  initializeNewUserPageV1
});

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeNewUserPageV1, { once: true });
} else {
  initializeNewUserPageV1();
}
