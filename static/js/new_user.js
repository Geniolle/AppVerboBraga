// APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_START
const APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1 = "appverbo:form-save-navigation-v1";

function readAndClearAppVerboFormSaveNavigationMarkerV1() {
  try {
    const markerValue = window.sessionStorage.getItem(APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1) || "";
    if (markerValue) {
      window.sessionStorage.removeItem(APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1);
    }
    return markerValue;
  } catch (error) {
    return "";
  }
}

function markAppVerboFormSaveNavigationV1(form) {
  if (!form) {
    return;
  }

  const method = String(form.getAttribute("method") || form.method || "").trim().toLowerCase();

  if (method && method !== "post") {
    return;
  }

  try {
    window.sessionStorage.setItem(APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1, "1");

    window.setTimeout(() => {
      try {
        if (document.visibilityState !== "hidden") {
          window.sessionStorage.removeItem(APPVERBO_FORM_SAVE_NAVIGATION_MARKER_V1);
        }
      } catch (error) {
        // Ignora falhas de sessionStorage.
      }
    }, 5000);
  } catch (error) {
    // Ignora falhas de sessionStorage.
  }
}

document.addEventListener("submit", (event) => {
  markAppVerboFormSaveNavigationV1(event.target);
}, true);

document.addEventListener("click", (event) => {
  const submitControl = event.target && event.target.closest
    ? event.target.closest("button[type='submit'], input[type='submit'], button:not([type])")
    : null;

  if (!submitControl || !submitControl.form) {
    return;
  }

  markAppVerboFormSaveNavigationV1(submitControl.form);
}, true);

const appverboFormSaveNavigationMarkerV1 = readAndClearAppVerboFormSaveNavigationMarkerV1();

const navigationEntries = (
  typeof window !== "undefined" &&
  window.performance &&
  typeof window.performance.getEntriesByType === "function"
)
  ? window.performance.getEntriesByType("navigation")
  : [];
const navigationType = navigationEntries.length
  ? String(navigationEntries[0].type || "")
  : "";

if (
  navigationType === "reload" &&
  window.location.pathname === "/users/new" &&
  appverboFormSaveNavigationMarkerV1 !== "1"
) {
  const homeUrl = "/users/new?menu=home";
  const currentPathAndQuery = `${window.location.pathname}${window.location.search}`;
  if (currentPathAndQuery !== homeUrl || window.location.hash) {
    window.location.replace(homeUrl);
  }
}
// APPVERBO_FORM_SAVE_NAVIGATION_GUARD_V1_END

const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
const MEU_PERFIL_MENU_KEY = "meu_perfil";
const LEGACY_DOCUMENTOS_MENU_KEY = "documentos";
const currentUserName = bootstrap.currentUserName || "";
const currentUserEmail = bootstrap.currentUserEmail || "";
const currentUserIsAdmin = Boolean(bootstrap.currentUserIsAdmin);
const currentUserCanManageAllEntities = Boolean(bootstrap.currentUserCanManageAllEntities);
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
const initialProfileTab = bootstrap.initialProfileTab || "pessoal";
const initialMenu = normalizeMenuKey(bootstrap.initialMenu || "home") || "home";
const initialMenuTarget = bootstrap.initialMenuTarget || "";
const initialDynamicProcessSection = bootstrap.initialDynamicProcessSection || "";
const initialAdminTab = bootstrap.initialAdminTab || "utilizador";
const currentEntityId = Number.parseInt(String(bootstrap.currentEntityId || "").trim(), 10);
const settingsAction = bootstrap.settingsAction || "";
const settingsTab = normalizeSettingsTabKey(bootstrap.settingsTab || "");
const settingsEditKey = normalizeMenuKey(bootstrap.settingsEditKey || "");
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
const dynamicProcessDataByMenu = {};
const selectedDynamicSectionByMenu = {};
const processTextualTypes = new Set(["text", "number", "email", "phone"]);
const processSupportedTypes = new Set(["text", "number", "email", "phone", "date", "flag", "list"]);
const processSubsequentOperators = new Set(["equals", "not_equals", "is_empty", "is_not_empty"]);


function normalizeSettingsTabKey(value) {
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
  const cleanKey = String(value || "").trim().toLowerCase();
  if (cleanKey === LEGACY_DOCUMENTOS_MENU_KEY) {
    return MEU_PERFIL_MENU_KEY;
  }
  if (cleanKey === "configuracao") {
    return "administrativo";
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
  return isAbsenceProcessMenu(menuKey, menuLabel, sectionLabel) || joined.includes("departamento");
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
  return { singular: "registo", plural: "registos" };
}

function buildProcessSections(setting, processValuesByField = {}) {
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
    optionMetaByKey.set(optionKey, {
      label: optionLabel,
      fieldType: optionType,
      size: optionSize,
      listKey: normalizeMenuKey(option.list_key || option.listKey),
      listOptions: processListsByKey.get(normalizeMenuKey(option.list_key || option.listKey)) || [],
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

const menuConfig = {
  home: {
    title: "Home",
    description: "Resumo geral do sistema.",
    singleView: true,
    toggleOnMenuClick: true,
    items: [{ label: "Resumo Geral", target: "#home-summary-card" }],
    details: [
      { label: "Entidades", value: String((dashboardData.totals || {}).entities || 0) },
      { label: "Utilizadores", value: String((dashboardData.totals || {}).users || 0) }
    ]
  },
  perfil: {
    title: "Perfil",
    description: "Opcoes do perfil do utilizador.",
    singleView: true,
    toggleOnMenuClick: true,
    items: [
      { label: "Dados pessoais", target: "#perfil-pessoal-card" },
      { label: "Dados de morada", target: "#perfil-morada-card" },
      { label: "Dados de Treinamento", target: "#dados-treinamento-card" }
    ],
    details: [
      { label: "Nome", value: currentUserName },
      { label: "Email", value: currentUserEmail },
      { label: "Telefone", value: currentUserPhone },
      { label: "Conta", value: currentUserAccountStatus },
      { label: "Membro", value: currentUserMemberStatus },
      { label: "Entidades", value: currentUserEntities },
      { label: "Tipo de acesso", value: "Utilizador" }
    ]
  },
  links: {
    title: "Links",
    description: "Atalhos internos do painel.",
    items: [{ label: "Sessão atual", target: "#sessao-card" }],
    details: [
      { label: "Modulo", value: "Links" },
      { label: "Status", value: "Ativo" }
    ]
  },
  contato: {
    title: "Contacto",
    description: "Informações e opções de contacto.",
    items: [
      { label: "Dados do utilizador ligado", target: "#sessao-card" }
    ],
    details: [
      { label: "Email", value: currentUserEmail },
      { label: "Canal", value: "Interno" }
    ]
  },
  tutorial: {
    title: "Tutorial",
    description: "Guia rapido de uso desta tela.",
    items: [{ label: "Passo 1: atualizar perfil", target: "#perfil-pessoal-card" }],
    details: [
      { label: "Modo", value: "Guiado" },
      { label: "Dificuldade", value: "Basico" }
    ]
  }
};

if (currentUserIsAdmin) {
  Object.assign(menuConfig, {
    administrativo: {
      title: "Administrativo",
      description: "Ferramentas administrativas do utilizador.",
      singleView: true,
      items: [],
      details: [
        { label: "Modulo", value: "Administrativo" },
        { label: "Acesso", value: "Permitido" }
      ]
    },
    [MEU_PERFIL_MENU_KEY]: {
      title: "Meu perfil",
      description: "Dados do meu perfil.",
      singleView: true,
      toggleOnMenuClick: true,
      items: (
        Array.isArray(profilePersonalSections) && profilePersonalSections.length
          ? profilePersonalSections.map((section) => ({
              label: String(section.label || "Dados pessoais"),
              target: "#perfil-pessoal-card",
              profileSection: String(section.key || "")
            }))
          : []
      ),
      details: [
        { label: "Modulo", value: "Meu perfil" },
        { label: "Status", value: "Ativo" }
      ]
    },
    funcionarios: {
      title: "Funcionarios",
      description: "Gestao de funcionarios e acessos.",
      items: [
        { label: "Criar registo de funcionario", target: "#create-user-card" },
        { label: "Ver registos recentes", target: "#recent-users-card" }
      ],
      details: [
        { label: "Modulo", value: "Funcionarios" },
        { label: "Status", value: "Ativo" }
      ]
    },
    financeiro: {
      title: "Financeiro",
      description: "Acesso a opções de conta e estado.",
      items: [
        { label: "Estado da conta", target: "#create-user-card" },
        { label: "Histórico de criação", target: "#recent-users-card" }
      ],
      details: [
        { label: "Modulo", value: "Financeiro" },
        { label: "Status", value: "Ativo" }
      ]
    },
    relatorios: {
      title: "Relatorios",
      description: "Relatorios e historico de utilizadores.",
      items: [
        { label: "Últimos criados", target: "#recent-users-card" },
        { label: "Voltar ao formulario", target: "#create-user-card" }
      ],
      details: [
        { label: "Modulo", value: "Relatorios" },
        { label: "Status", value: "Ativo" }
      ]
    }
  });

  menuConfig.links.items.push({ label: "Criar utilizador", target: "#create-user-card" });
  menuConfig.tutorial.items = [
    { label: "Passo 1: criar utilizador", target: "#create-user-card" },
    { label: "Passo 2: validar em historico", target: "#recent-users-card" }
  ];
}

function mergeDynamicProcessMenus() {
  sidebarMenuSettings.forEach((setting) => {
    const menuKey = normalizeMenuKey(setting.key);
    if (!menuKey || menuKey === "perfil") {
      return;
    }
    if (menuKey === MEU_PERFIL_MENU_KEY) {
      return;
    }
    if (visibleSidebarMenuKeys.size && !visibleSidebarMenuKeys.has(menuKey)) {
      return;
    }

    const cleanMenuLabel = toSentenceCaseText(setting.label) || "Processo";
    const existingConfig = menuConfig[menuKey];

    const menuValuesByField = (
      menuProcessValuesMap &&
      typeof menuProcessValuesMap[menuKey] === "object" &&
      menuProcessValuesMap[menuKey] !== null
    )
      ? menuProcessValuesMap[menuKey]
      : {};
    let sections = buildProcessSections(setting, menuValuesByField);
    if (!sections.length) {
      delete dynamicProcessDataByMenu[menuKey];
      delete selectedDynamicSectionByMenu[menuKey];
      if (existingConfig) {
        menuConfig[menuKey] = {
          ...existingConfig,
          items: []
        };
      } else {
        menuConfig[menuKey] = {
          title: cleanMenuLabel,
          description: "Campos configurados para este processo.",
          singleView: true,
          toggleOnMenuClick: true,
          items: [],
          details: [
            { label: "Modulo", value: cleanMenuLabel },
            { label: "Status", value: "Ativo" }
          ]
        };
      }
      return;
    }
    dynamicProcessDataByMenu[menuKey] = {
      menuLabel: cleanMenuLabel,
      sections
    };
    if (
      menuKey === normalizeMenuKey(initialMenu) &&
      initialDynamicProcessSection &&
      sections.some((section) => String(section.key || "") === String(initialDynamicProcessSection))
    ) {
      selectedDynamicSectionByMenu[menuKey] = String(initialDynamicProcessSection);
    } else {
      selectedDynamicSectionByMenu[menuKey] = sections[0].key;
    }

    const dynamicItems = sections.map((section) => ({
      label: toSentenceCaseText(section.label || "Campos"),
      target: "#dynamic-process-card",
      dynamicProcessSectionKey: String(section.key || "__empty__")
    }));
    if (existingConfig) {
      if (menuKey === "administrativo") {
        const baseItems = [
          { label: "Utilizador", target: "#create-user-card" },
          { label: "Entidade", target: "#create-entity-card" },
          { label: "Menu", target: "#admin-account-status-card" },
          { label: "Sessões", target: "#admin-sidebar-sections-card" }
        ];
        const mergedItems = dynamicItems.filter((item) => {
          const sectionKey = String(item.dynamicProcessSectionKey || "").trim().toLowerCase();
          if (!sectionKey) {
            return false;
          }
          return sectionKey !== "__geral__" && !sectionKey.startsWith("field:");
        });
        const seenTargets = new Set(baseItems.map((item) => buildMenuItemUniqueKey_v1(item)));
        const dynamicExtraItems = mergedItems.filter((item) => {
          const targetKey = buildMenuItemUniqueKey_v1(item);
          if (!targetKey || seenTargets.has(targetKey)) {
            return false;
          }
          seenTargets.add(targetKey);
          return true;
        });
        const resolvedItems = [...baseItems, ...dynamicExtraItems];
        menuConfig[menuKey] = {
          ...existingConfig,
          items: resolvedItems
        };
        return;
      }
      menuConfig[menuKey] = {
        ...existingConfig,
        items: dynamicItems
      };
      return;
    }
    menuConfig[menuKey] = {
      title: cleanMenuLabel,
      description: "Campos configurados para este processo.",
      singleView: true,
      toggleOnMenuClick: true,
      items: dynamicItems,
      details: [
        { label: "Modulo", value: cleanMenuLabel },
        { label: "Status", value: "Ativo" }
      ]
    };
  });
}

mergeDynamicProcessMenus();

const itemsEl = document.getElementById("submenu-items");
const menuButtons = document.querySelectorAll(".menu-item");
const scopedCards = document.querySelectorAll("[data-menu-scope]");
const userMenuEl = document.getElementById("user-menu");
const userMenuTriggerEl = document.getElementById("user-menu-trigger");
const userDropdownEl = document.getElementById("user-dropdown");
const userAvatarImageEl = document.getElementById("user-avatar-image");
const dropdownAvatarImageEl = document.getElementById("dropdown-avatar-image");
const userDropdownLinks = document.querySelectorAll("[data-dropdown-target]");
const profileEditButtons = document.querySelectorAll("[data-edit-target]");
const profileEditCancelButtons = document.querySelectorAll("[data-edit-cancel]");
const trainingOutrosEnabledEl = document.getElementById("edit_training_outros_enabled");
const trainingOutrosInputEl = document.getElementById("edit_training_outros");
const processFieldsBuilderEl = document.getElementById("process-fields-builder");
const dynamicProcessCardEl = document.getElementById("dynamic-process-card");
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
const dynamicProcessSubmitBtnEl = document.getElementById("dynamic-process-submit-btn");
const dynamicProcessEditToggleEl = document.getElementById("dynamic-process-edit-toggle");
const dynamicProcessEmptyEl = document.getElementById("dynamic-process-empty");
const dynamicProcessHistoryBlockEl = document.getElementById("dynamic-process-history-block");
const dynamicProcessHistoryTitleEl = document.getElementById("dynamic-process-history-title");
const dynamicProcessHistoryTableEl = document.getElementById("dynamic-process-history-table");
const dynamicProcessHistoryHeadEl = document.getElementById("dynamic-process-history-head");
const dynamicProcessHistoryBodyEl = document.getElementById("dynamic-process-history-body");
const dynamicProcessHistoryEmptyEl = document.getElementById("dynamic-process-history-empty");
let homeSelectedTarget = "#home-summary-card";
let profileSelectedTarget = "#perfil-pessoal-card";
if (initialProfileTab === "morada") {
  profileSelectedTarget = "#perfil-morada-card";
} else if (initialProfileTab === "treinamento") {
  profileSelectedTarget = "#dados-treinamento-card";
}
let adminSelectedTarget = "#dynamic-process-card";
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
if (initialAdminTab === "entidade") {
  adminSelectedTarget = "#create-entity-card";
} else if (initialAdminTab === "contas") {
  adminSelectedTarget = "#admin-account-status-card";
}
if (startupHash === "#home-summary-card") {
  homeSelectedTarget = startupHash;
}
if (startupHash === "#create-user-card" || startupHash === "#edit-user-card") {
  adminSelectedTarget = "#create-user-card";
} else if (startupHash === "#create-entity-card" || startupHash === "#edit-entity-card") {
  adminSelectedTarget = "#create-entity-card";
} else if (startupHash === "#admin-account-status-card") {
  adminSelectedTarget = "#admin-account-status-card";
} else if (startupHash === "#settings-menu-edit-card") {
  adminSelectedTarget = "#settings-menu-edit-card";
}
if (!startupHash && settingsEditKey) {
  adminSelectedTarget = "#settings-menu-edit-card";
}
if (!startupHash && initialMenu === "administrativo" && !settingsEditKey) {
  adminSelectedTarget = "#dynamic-process-card";
}
const selectedTargetByMenu = {
  home: homeSelectedTarget,
  perfil: profileSelectedTarget,
  administrativo: adminSelectedTarget,
  [MEU_PERFIL_MENU_KEY]: meuPerfilSelectedTarget
};
Object.keys(dynamicProcessDataByMenu).forEach((menuKey) => {
  if (menuKey === "administrativo" && selectedTargetByMenu[menuKey] === "#settings-menu-edit-card") {
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
    (item) => String(item.target || "") === cleanInitialTarget
  );
  if (targetExistsInItems || cleanInitialTarget === "#settings-menu-edit-card") {
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
  const personalCardEl = document.getElementById("perfil-pessoal-card");
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
  const personalCardEl = document.getElementById("perfil-pessoal-card");
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
  const personalCardEl = document.getElementById("perfil-pessoal-card");
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
  const activeSectionKey = normalizeMenuKey(meuPerfilSelectedProfileSection || (profilePersonalSections[0] && profilePersonalSections[0].key) || "");

  normalizedRules.forEach((rule) => {
    const ruleSectionKey = normalizeMenuKey(rule.headerKey || activeSectionKey || "");
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
            ? (isTruthyFlagValue(rawValue) ? "Sim" : "NÃ£o")
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
            controlEl.type = fieldType === "email"
              ? "email"
              : fieldType === "phone"
                ? "tel"
                : fieldType === "number"
                  ? "number"
                  : fieldType === "date"
                    ? "date"
                    : "text";
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
    if (dynamicProcessEditToggleEl) {
      dynamicProcessEditToggleEl.style.display = "none";
    }
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
    if (itemsEl) {
      const selectedLinkEl = itemsEl.querySelector(
        `.submenu-item[data-dynamic-process-section="${String(selectedSection.key || "").replace(/"/g, '\\"')}"]`
      );
      if (selectedLinkEl) {
        setActiveSubmenu("#dynamic-process-card", selectedLinkEl);
      }
    }
  }

  const menuLabel = toSentenceCaseText(menuData.menuLabel || "Processo");
  const sectionLabel = selectedSection
    ? toSentenceCaseText(selectedSection.label || "Campos")
    : "Campos";
  const absenceProcessMode = isAbsenceProcessMenu(cleanMenuKey, menuLabel, sectionLabel);
  const historyProcessMode = isHistoryProcessMenu(cleanMenuKey, menuLabel, sectionLabel);
  const historyRecordLabels = getHistoryRecordLabels(cleanMenuKey, menuLabel, sectionLabel);
  const showStateField = historyProcessMode && !absenceProcessMode && historyRecordLabels.singular === "departamento";
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
    if (dynamicProcessEditToggleEl) {
      dynamicProcessEditToggleEl.style.display = "none";
    }
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
    dynamicProcessEditToggleEl.style.display = "none";
    if (!absenceProcessMode && (sectionFields.length || hasQuantityRulesForSection)) {
      dynamicProcessEditToggleEl.style.display = "";
      dynamicProcessEditToggleEl.textContent = historyProcessMode ? "Criar" : "Editar";
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
    const editDefaultValue = historyProcessMode ? "" : fieldValue;

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
  scopedCards.forEach((card) => {
    const rawScope = card.getAttribute("data-menu-scope") || "";
    const scopes = rawScope.split(",").map((value) => normalizeMenuKey(value)).filter(Boolean);
    card.style.display = scopes.includes(menuKey) ? "" : "none";
  });
  if (dynamicProcessCardEl) {
    dynamicProcessCardEl.style.display = "none";
  }
}

function applyContentForMenuTarget(menuKey, targetSelector) {
  scopedCards.forEach((card) => {
    const rawScope = card.getAttribute("data-menu-scope") || "";
    const scopes = rawScope.split(",").map((value) => normalizeMenuKey(value)).filter(Boolean);
    if (!scopes.includes(menuKey)) {
      card.style.display = "none";
      return;
    }
    const isEntityGroupedBlock =
      menuKey === "administrativo" &&
      targetSelector === "#create-entity-card" &&
      (
        card.id === "create-entity-card" ||
        card.id === "edit-entity-card" ||
        card.id === "recent-entities-card" ||
        card.id === "inactive-entities-card"
      );
    const isUserGroupedBlock =
      menuKey === "administrativo" &&
      targetSelector === "#create-user-card" &&
      (
        card.id === "create-user-card" ||
        card.id === "edit-user-card" ||
        card.id === "admin-users-created-card"
      );
    const isSettingsGroupedBlock =
      menuKey === "administrativo" &&
      targetSelector === "#settings-menu-edit-card" &&
      (
        card.id === "admin-account-create-card" ||
        card.id === "settings-menu-edit-card" ||
        card.id === "admin-account-status-card"
      );
    card.style.display =
      targetSelector === ("#" + card.id) ||
      isEntityGroupedBlock ||
      isUserGroupedBlock ||
      isSettingsGroupedBlock
        ? ""
        : "none";
  });
  if (dynamicProcessCardEl) {
    dynamicProcessCardEl.style.display = targetSelector === "#dynamic-process-card" ? "" : "none";
  }
}

function clearSubmenuActiveLinks(links) {
  links.forEach((link) => {
    link.classList.remove("active");
  });
}

function setActiveSubmenu(targetSelector, selectedLinkEl = null) {
  if (!itemsEl) {
    return;
  }
  const links = itemsEl.querySelectorAll(".submenu-item");
  clearSubmenuActiveLinks(links);
  if (selectedLinkEl) {
    selectedLinkEl.classList.add("active");
    return;
  }
  const firstMatch = Array.from(links).find(
    (link) => link.getAttribute("href") === targetSelector
  );
  if (firstMatch) {
    firstMatch.classList.add("active");
  }
}

function closeAllProfileEdits() {
  const editingCards = document.querySelectorAll(".card.editing");
  editingCards.forEach((card) => {
    card.classList.remove("editing");
    const form = card.querySelector(".profile-edit-form");
    if (form) {
      form.reset();
    }
  });
  syncTrainingOutrosState();
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
      linkEl.style.display = hiddenMeuPerfilSectionKeys.has(sectionKey) ? "none" : "";
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
      setActiveSubmenu("#perfil-pessoal-card", selectedLinkEl);
      return;
    }
    const firstVisibleLinkEl = Array.from(itemsEl.querySelectorAll(".submenu-item[data-profile-section]")).find(
      (linkEl) => linkEl.style.display !== "none"
    );
    if (firstVisibleLinkEl) {
      meuPerfilSelectedProfileSection = String(firstVisibleLinkEl.dataset.profileSection || "");
      setActiveSubmenu("#perfil-pessoal-card", firstVisibleLinkEl);
    }
  }
  renderMeuPerfilQuantityGroups();
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
      personalFormEl.addEventListener(eventName, () => {
        applyMeuPerfilProcessSubsequentVisibility();
      });
    });
  }

  if (dynamicProcessEditFormEl && dynamicProcessEditFormEl.dataset.boundSubsequentVisibility !== "1") {
    dynamicProcessEditFormEl.dataset.boundSubsequentVisibility = "1";
    ["input", "change"].forEach((eventName) => {
      dynamicProcessEditFormEl.addEventListener(eventName, () => {
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

function setupTableLimiter(prefix) {
  const tableEl = document.getElementById(`${prefix}-table`);
  const limiterEl = document.getElementById(`${prefix}-limiter`);
  const pageSizeEl = document.getElementById(`${prefix}-page-size`);
  const prevEl = document.getElementById(`${prefix}-prev`);
  const nextEl = document.getElementById(`${prefix}-next`);
  const pageEl = document.getElementById(`${prefix}-page`);
  if (!tableEl || !limiterEl || !pageSizeEl || !prevEl || !nextEl || !pageEl) {
    return;
  }

  const rows = Array.from(tableEl.querySelectorAll("tbody tr"));
  if (!rows.length) {
    limiterEl.style.display = "none";
    return;
  }

  let pageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
  let currentPage = 1;

  function getTotalPages() {
    return Math.max(1, Math.ceil(rows.length / pageSize));
  }

  function render() {
    const totalPages = getTotalPages();
    if (currentPage > totalPages) {
      currentPage = totalPages;
    }
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    rows.forEach((row, index) => {
      row.style.display = index >= start && index < end ? "" : "none";
    });
    pageEl.textContent = String(currentPage);
    prevEl.disabled = currentPage <= 1;
    nextEl.disabled = currentPage >= totalPages;
  }

  pageSizeEl.addEventListener("change", () => {
    pageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
    currentPage = 1;
    render();
  });

  prevEl.addEventListener("click", () => {
    if (currentPage <= 1) {
      return;
    }
    currentPage -= 1;
    render();
  });

  nextEl.addEventListener("click", () => {
    const totalPages = getTotalPages();
    if (currentPage >= totalPages) {
      return;
    }
    currentPage += 1;
    render();
  });

  render();
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

function setupProcessAdditionalFieldsManagerV2() {
  const builderEl = document.getElementById("process-additional-fields-builder");
  const formEl = builderEl ? builderEl.closest("form[data-additional-fields-manager-v2='1']") : null;
  if (!builderEl || !formEl) {
    return;
  }
  if (builderEl.dataset.additionalFieldsManagerV2Bound === "1") {
    return;
  }

  const containerEl = document.getElementById("process-additional-fields-container");
  const editorKeyEl = document.getElementById("process-additional-field-editor-key");
  const editorLabelEl = document.getElementById("process-additional-field-editor-label");
  const editorTypeEl = document.getElementById("process-additional-field-editor-type");
  const editorRequiredEl = document.getElementById("process-additional-field-editor-required");
  const editorSizeFieldEl = document.getElementById("process-additional-field-editor-size-field");
  const editorSizeEl = document.getElementById("process-additional-field-editor-size");
  const editorListFieldEl = document.getElementById("process-additional-field-editor-list-field");
  const editorListKeyEl = document.getElementById("process-additional-field-editor-list-key");
  const feedbackEl = document.getElementById("process-additional-field-editor-feedback");
  const addButtonEl = document.getElementById("process-additional-field-add-btn");
  const clearButtonEl = document.getElementById("process-additional-field-clear-btn");
  const tableBodyEl = document.getElementById("process-additional-fields-created-body");
  const emptyEl = document.getElementById("process-additional-fields-empty");
  const limiterEl = document.getElementById("process-additional-fields-limiter");
  const pageSizeEl = document.getElementById("process-additional-fields-page-size");
  const prevEl = document.getElementById("process-additional-fields-prev");
  const nextEl = document.getElementById("process-additional-fields-next");
  const pageEl = document.getElementById("process-additional-fields-page");
  const fieldTypesRaw = builderEl.getAttribute("data-field-types") || "[]";
  const processListsRaw = builderEl.getAttribute("data-process-lists") || "[]";

  if (
    !containerEl ||
    !editorKeyEl ||
    !editorLabelEl ||
    !editorTypeEl ||
    !editorRequiredEl ||
    !editorSizeFieldEl ||
    !editorSizeEl ||
    !editorListFieldEl ||
    !editorListKeyEl ||
    !feedbackEl ||
    !addButtonEl ||
    !clearButtonEl ||
    !tableBodyEl ||
    !emptyEl ||
    !limiterEl ||
    !pageSizeEl ||
    !prevEl ||
    !nextEl ||
    !pageEl
  ) {
    return;
  }

  let fieldTypes = [];
  let processLists = [];
  let tempIndex = 1;
  let currentPage = 1;
  let pageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
  const sizedTypes = new Set(["text", "number", "email", "phone"]);

  try {
    fieldTypes = JSON.parse(fieldTypesRaw);
  } catch (_error) {
    fieldTypes = [];
  }
  try {
    processLists = JSON.parse(processListsRaw);
  } catch (_error) {
    processLists = [];
  }

  const typeLabelByKey = new Map(
    (Array.isArray(fieldTypes) ? fieldTypes : []).map((item) => [
      String(item.key || "").trim().toLowerCase(),
      String(item.label || item.key || "").trim()
    ])
  );
  typeLabelByKey.set("list", "Lista");

  function normalizeKey(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function getListLabel(listKey) {
    const cleanListKey = normalizeKey(listKey);
    const matched = (Array.isArray(processLists) ? processLists : []).find((item) => {
      return normalizeKey(item.key) === cleanListKey;
    });
    return matched ? String(matched.label || matched.key || "-") : "-";
  }

  function syncEditorState() {
    const cleanType = String(editorTypeEl.value || "text").trim().toLowerCase();
    const isHeader = cleanType === "header";
    const isList = cleanType === "list";
    const sizeEnabled = sizedTypes.has(cleanType);

    editorRequiredEl.disabled = isHeader;
    if (isHeader) {
      editorRequiredEl.value = "0";
    }

    editorSizeFieldEl.style.display = sizeEnabled ? "" : "none";
    editorSizeEl.readOnly = !sizeEnabled;
    editorSizeEl.classList.toggle("process-additional-size-readonly", !sizeEnabled);
    if (!sizeEnabled) {
      editorSizeEl.value = "";
    } else if (!String(editorSizeEl.value || "").trim()) {
      editorSizeEl.value = "30";
    }

    editorListFieldEl.style.display = isList ? "" : "none";
    editorListKeyEl.disabled = !isList;
    if (!isList) {
      editorListKeyEl.value = "";
    }
  }

  function setEditorFeedback(message, type = "error") {
    feedbackEl.textContent = String(message || "").trim();
    feedbackEl.style.display = feedbackEl.textContent ? "" : "none";
    feedbackEl.classList.toggle("error", type === "error");
    feedbackEl.classList.toggle("ok", type === "ok");
  }

  function clearEditor() {
    editorKeyEl.value = "";
    editorLabelEl.value = "";
    editorTypeEl.value = "text";
    editorRequiredEl.value = "0";
    editorSizeEl.value = "30";
    editorListKeyEl.value = "";
    addButtonEl.textContent = "Guardar";
    setEditorFeedback("");
    syncEditorState();
  }

  function readStoreRow(rowEl) {
    const keyEl = rowEl.querySelector("input[name='additional_field_key']");
    const labelEl = rowEl.querySelector("input[name='additional_field_label']");
    const typeEl = rowEl.querySelector("select[name='additional_field_type'], input[name='additional_field_type']");
    const requiredEl = rowEl.querySelector("select[name='additional_field_required'], input[name='additional_field_required']");
    const sizeEl = rowEl.querySelector("input[name='additional_field_size']");
    const listKeyEl = rowEl.querySelector("select[name='additional_field_list_key'], input[name='additional_field_list_key']");
    if (!labelEl || !typeEl || !requiredEl || !sizeEl) {
      return null;
    }

    return {
      key: String(keyEl ? keyEl.value : rowEl.getAttribute("data-field-key") || "").trim(),
      label: String(labelEl.value || "").trim(),
      fieldType: String(typeEl.value || "text").trim().toLowerCase(),
      isRequired: String(requiredEl.value || "0").trim() === "1",
      size: String(sizeEl.value || "").trim(),
      listKey: String(listKeyEl ? listKeyEl.value : "").trim()
    };
  }

  function readStoreRows() {
    return Array.from(containerEl.children)
      .map((rowEl) => readStoreRow(rowEl))
      .filter((row) => row && row.label);
  }

  function createHiddenInput(name, value) {
    const inputEl = document.createElement("input");
    inputEl.type = "hidden";
    inputEl.name = name;
    inputEl.value = String(value || "");
    return inputEl;
  }

  function buildStoreRow(fieldData) {
    const rowEl = document.createElement("div");
    rowEl.className = "process-additional-field-store-row";
    rowEl.setAttribute("data-field-key", fieldData.key);
    rowEl.appendChild(createHiddenInput("additional_field_key", fieldData.key));
    rowEl.appendChild(createHiddenInput("additional_field_label", fieldData.label));
    rowEl.appendChild(createHiddenInput("additional_field_type", fieldData.fieldType));
    rowEl.appendChild(createHiddenInput("additional_field_required", fieldData.isRequired ? "1" : "0"));
    rowEl.appendChild(createHiddenInput("additional_field_size", fieldData.size || ""));
    rowEl.appendChild(createHiddenInput("additional_field_list_key", fieldData.listKey || ""));
    return rowEl;
  }

  function removeStoreRow(fieldKey) {
    const rowEl = Array.from(containerEl.children).find((item) => {
      return String(item.getAttribute("data-field-key") || "").trim() === String(fieldKey || "").trim();
    });
    if (rowEl) {
      rowEl.remove();
    }
  }

  function upsertStoreRow(fieldData) {
    const existingRowEl = Array.from(containerEl.children).find((item) => {
      return String(item.getAttribute("data-field-key") || "").trim() === String(fieldData.key || "").trim();
    });
    const nextSiblingEl = existingRowEl ? existingRowEl.nextSibling : null;

    removeStoreRow(fieldData.key);

    const newRowEl = buildStoreRow(fieldData);
    if (nextSiblingEl) {
      containerEl.insertBefore(newRowEl, nextSiblingEl);
    } else {
      containerEl.appendChild(newRowEl);
    }
  }

  function buildPayloadFromEditor() {
    const cleanLabel = String(editorLabelEl.value || "").trim();
    if (!cleanLabel) {
      setEditorFeedback("Informe o nome do campo adicional.");
      editorLabelEl.focus();
      return null;
    }

    const cleanType = String(editorTypeEl.value || "text").trim().toLowerCase();
    const cleanKey = String(editorKeyEl.value || "").trim() || `tmp_${normalizeKey(cleanLabel) || "campo"}_${tempIndex++}`;
    const duplicateLabel = readStoreRows().some((row) => {
      return row.key !== cleanKey && String(row.label || "").trim().toLowerCase() === cleanLabel.toLowerCase();
    });
    if (duplicateLabel) {
      setEditorFeedback("Já existe um campo adicional com esse nome.");
      editorLabelEl.focus();
      return null;
    }

    return {
      key: cleanKey,
      label: cleanLabel,
      fieldType: cleanType,
      isRequired: cleanType === "header" ? false : String(editorRequiredEl.value || "0") === "1",
      size: sizedTypes.has(cleanType) ? String(editorSizeEl.value || "").trim() || "30" : "",
      listKey: cleanType === "list" ? String(editorListKeyEl.value || "").trim() : ""
    };
  }

  function fillEditor(fieldData) {
    editorKeyEl.value = fieldData.key;
    editorLabelEl.value = fieldData.label;
    editorTypeEl.value = fieldData.fieldType || "text";
    editorRequiredEl.value = fieldData.isRequired ? "1" : "0";
    editorSizeEl.value = fieldData.size || "30";
    editorListKeyEl.value = fieldData.listKey || "";
    addButtonEl.textContent = "Atualizar campo";
    syncEditorState();
    editorLabelEl.focus();
  }

  function moveStoreRow(fieldKey, direction) {
    const rowEls = Array.from(containerEl.children);
    const currentIndex = rowEls.findIndex((rowEl) => {
      return String(rowEl.getAttribute("data-field-key") || "").trim() === String(fieldKey || "").trim();
    });
    const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
    if (currentIndex < 0 || targetIndex < 0 || targetIndex >= rowEls.length) {
      return;
    }
    const currentRowEl = rowEls[currentIndex];
    const targetRowEl = rowEls[targetIndex];
    if (direction === "up") {
      containerEl.insertBefore(currentRowEl, targetRowEl);
    } else {
      containerEl.insertBefore(targetRowEl, currentRowEl);
    }
  }

  function renderPagination() {
    const rowEls = Array.from(tableBodyEl.querySelectorAll("tr"));
    if (!rowEls.length) {
      limiterEl.style.display = "none";
      return;
    }

    const totalPages = Math.max(1, Math.ceil(rowEls.length / pageSize));
    if (currentPage > totalPages) {
      currentPage = totalPages;
    }

    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;

    rowEls.forEach((rowEl, index) => {
      rowEl.style.display = index >= start && index < end ? "" : "none";
    });

    pageEl.textContent = String(currentPage);
    prevEl.disabled = currentPage <= 1;
    nextEl.disabled = currentPage >= totalPages;
    limiterEl.style.display = rowEls.length > pageSize ? "flex" : "none";
  }

  function renderTable() {
    const rows = readStoreRows();
    tableBodyEl.innerHTML = "";

    if (!rows.length) {
      emptyEl.style.display = "";
      limiterEl.style.display = "none";
      return;
    }

    emptyEl.style.display = "none";
    rows.forEach((row) => {
      const trEl = document.createElement("tr");
      trEl.setAttribute("data-field-key", row.key);
      trEl.innerHTML = [
        `<td>${escapeHtml(row.label)}</td>`,
        `<td>${escapeHtml(typeLabelByKey.get(row.fieldType) || row.fieldType || "-")}</td>`,
        `<td>${row.isRequired ? "Sim" : "Não"}</td>`,
        `<td>${escapeHtml(row.size || "-")}</td>`,
        `<td>${escapeHtml(row.fieldType === "list" ? getListLabel(row.listKey) : "-")}</td>`,
        '<td><div class="table-actions">',
        '<button type="button" class="table-icon-btn" data-additional-field-action="edit" title="Modificar campo" aria-label="Modificar campo">&#9998;</button>',
        '<button type="button" class="table-icon-btn" data-additional-field-action="up" title="Mover para cima" aria-label="Mover para cima">&#8593;</button>',
        '<button type="button" class="table-icon-btn" data-additional-field-action="down" title="Mover para baixo" aria-label="Mover para baixo">&#8595;</button>',
        '<button type="button" class="table-icon-btn table-icon-btn-danger" data-additional-field-action="delete" title="Remover campo" aria-label="Remover campo">&#128465;</button>',
        "</div></td>"
      ].join("");
      tableBodyEl.appendChild(trEl);
    });

    renderPagination();
  }

  function handleAddAdditionalFieldV2() {
    const payload = buildPayloadFromEditor();
    if (!payload) {
      return;
    }
    upsertStoreRow(payload);
    clearEditor();
    setEditorFeedback("Campo adicional preparado para guardar.", "ok");
    currentPage = Math.max(1, Math.ceil(readStoreRows().length / pageSize));
    renderTable();
  }

  function handleClearAdditionalFieldV2() {
    clearEditor();
  }

  addButtonEl.addEventListener("click", handleAddAdditionalFieldV2);
  clearButtonEl.addEventListener("click", handleClearAdditionalFieldV2);
  window.__appverboAddAdditionalFieldV2 = handleAddAdditionalFieldV2;
  window.__appverboClearAdditionalFieldV2 = handleClearAdditionalFieldV2;

  editorTypeEl.addEventListener("change", () => {
    syncEditorState();
  });

  pageSizeEl.addEventListener("change", () => {
    pageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
    currentPage = 1;
    renderPagination();
  });

  prevEl.addEventListener("click", () => {
    if (currentPage <= 1) {
      return;
    }
    currentPage -= 1;
    renderPagination();
  });

  nextEl.addEventListener("click", () => {
    const totalPages = Math.max(1, Math.ceil(tableBodyEl.querySelectorAll("tr").length / pageSize));
    if (currentPage >= totalPages) {
      return;
    }
    currentPage += 1;
    renderPagination();
  });

  tableBodyEl.addEventListener("click", (event) => {
    const actionBtn = event.target.closest("[data-additional-field-action]");
    if (!actionBtn) {
      return;
    }

    const action = String(actionBtn.getAttribute("data-additional-field-action") || "").trim();
    const rowEl = actionBtn.closest("tr[data-field-key]");
    const fieldKey = String(rowEl ? rowEl.getAttribute("data-field-key") || "" : "").trim();
    const fieldData = readStoreRows().find((row) => row.key === fieldKey);
    if (!action || !fieldKey || !fieldData) {
      return;
    }

    if (action === "edit") {
      fillEditor(fieldData);
      return;
    }
    if (action === "delete") {
      removeStoreRow(fieldKey);
      if (String(editorKeyEl.value || "").trim() === fieldKey) {
        clearEditor();
      }
      renderTable();
      return;
    }
    if (action === "up" || action === "down") {
      moveStoreRow(fieldKey, action);
      renderTable();
    }
  });

  formEl.addEventListener("submit", () => {
    if (String(editorLabelEl.value || "").trim()) {
      const payload = buildPayloadFromEditor();
      if (payload) {
        upsertStoreRow(payload);
      }
    }
  });

  clearEditor();
  renderTable();
  builderEl.dataset.additionalFieldsManagerV2Bound = "1";
}

function setupProcessEditTabs() {
  const tabLinks = document.querySelectorAll("[data-process-edit-tab]");
  const panes = document.querySelectorAll("[data-process-edit-pane]");
  if (!tabLinks.length || !panes.length) {
    return;
  }

  function activateProcessTab(tabKey) {
    const hasTargetTab = Array.from(tabLinks).some(
      (tabLink) => (tabLink.getAttribute("data-process-edit-tab") || "") === tabKey
    );
    const resolvedTabKey = hasTargetTab ? tabKey : "geral";
    tabLinks.forEach((tabLink) => {
      const isActive = tabLink.getAttribute("data-process-edit-tab") === resolvedTabKey;
      tabLink.classList.toggle("active", isActive);
      tabLink.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    panes.forEach((pane) => {
      const isActive = pane.getAttribute("data-process-edit-pane") === resolvedTabKey;
      pane.classList.toggle("active", isActive);
    });
  }

  tabLinks.forEach((tabLink) => {
    tabLink.addEventListener("click", (event) => {
      event.preventDefault();
      const tabKey = tabLink.getAttribute("data-process-edit-tab") || "geral";
      activateProcessTab(tabKey);
    });
  });

  if (settingsAction === "edit") {
    const cleanSettingsTab = String(settingsTab || "").trim();
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
  const config = menuConfig[menuKey];
  if (!config || !itemsEl) {
    return;
  }

  itemsEl.innerHTML = "";
  itemsEl.style.display = "flex";

  config.items.forEach((item) => {
    const link = document.createElement("a");
    link.className = "submenu-item";
    link.href = item.target;
    link.textContent = toSentenceCaseText(item.label);
    if (item.profileSection) {
      link.dataset.profileSection = String(item.profileSection);
    }
    if (item.dynamicProcessSectionKey) {
      link.dataset.dynamicProcessSection = String(item.dynamicProcessSectionKey);
    }
    link.addEventListener("click", (event) => {
      event.preventDefault();
      closeAllProfileEdits();
      selectedTargetByMenu[menuKey] = item.target;
      setActiveSubmenu(item.target, link);
      applyContentForMenuTarget(menuKey, item.target);
      if (item.dynamicProcessSectionKey) {
        selectedDynamicSectionByMenu[menuKey] = String(item.dynamicProcessSectionKey);
        renderDynamicProcessCard(menuKey, item.dynamicProcessSectionKey);
      }
      if (
        menuKey === MEU_PERFIL_MENU_KEY &&
        typeof window.activateProfilePersonalSection === "function"
      ) {
        const sectionKey = String(item.profileSection || "");
        meuPerfilSelectedProfileSection = sectionKey;
        window.activateProfilePersonalSection(sectionKey);
        applyMeuPerfilProcessSubsequentVisibility();
      }
    });
    itemsEl.appendChild(link);
  });

}

function getDefaultTargetForMenu(menuKey, config, options = {}) {
  const { forceFirstItem = false } = options;
  if (!Array.isArray(config.items) || !config.items.length) {
    const savedTarget = selectedTargetByMenu[menuKey];
    if (savedTarget === "#settings-menu-edit-card") {
      const settingsCardEl = document.querySelector(savedTarget);
      if (settingsCardEl) {
        return savedTarget;
      }
    }
    return "";
  }
  if (forceFirstItem) {
    return config.items[0].target;
  }
  const savedTarget = selectedTargetByMenu[menuKey];
  if (savedTarget) {
    if (config.items.some((item) => item.target === savedTarget)) {
      return savedTarget;
    }
    if (savedTarget === "#settings-menu-edit-card") {
      const settingsCardEl = document.querySelector(savedTarget);
      if (settingsCardEl) {
        return savedTarget;
      }
    }
  }
  return config.items[0].target;
}

function activateMenu(menuKey, options = {}) {
  const config = menuConfig[menuKey];
  if (!config) {
    return;
  }
  const { resetDynamicToFirst = false } = options;
  const targetButton = Array.from(menuButtons).find((btn) => normalizeMenuKey(btn.dataset.menu) === menuKey);
  const menuItems = Array.isArray(config.items) ? config.items : [];
  if (resetDynamicToFirst) {
    const firstDynamicItem = menuItems.find((item) => item.dynamicProcessSectionKey);
    if (firstDynamicItem) {
      selectedDynamicSectionByMenu[menuKey] = String(
        firstDynamicItem.dynamicProcessSectionKey || ""
      );
    }
  }

  closeAllProfileEdits();
  activeMenuKey = menuKey;
  menuButtons.forEach((item) => item.classList.remove("active"));
  if (targetButton) {
    targetButton.classList.add("active");
  }
  renderSubmenu(menuKey);

  const defaultTarget = getDefaultTargetForMenu(
    menuKey,
    config,
    { forceFirstItem: resetDynamicToFirst }
  );
  if (defaultTarget) {
    const savedDynamicSectionKey = String(selectedDynamicSectionByMenu[menuKey] || "");
    let selectedDynamicItem = null;
    if (defaultTarget === "#dynamic-process-card") {
      selectedDynamicItem = menuItems.find(
        (item) => String(item.dynamicProcessSectionKey || "") === savedDynamicSectionKey
      );
      if (!selectedDynamicItem) {
        selectedDynamicItem = menuItems.find((item) => item.target === "#dynamic-process-card") || null;
      }
    }

    selectedTargetByMenu[menuKey] = defaultTarget;
    if (selectedDynamicItem && itemsEl) {
      const selectedSectionKey = String(selectedDynamicItem.dynamicProcessSectionKey || "");
      const selectedLinkEl = itemsEl.querySelector(
        `.submenu-item[data-dynamic-process-section="${selectedSectionKey.replace(/"/g, '\\"')}"]`
      );
      if (selectedLinkEl) {
        setActiveSubmenu(defaultTarget, selectedLinkEl);
      } else {
        setActiveSubmenu(defaultTarget);
      }
      selectedDynamicSectionByMenu[menuKey] = selectedSectionKey;
      renderDynamicProcessCard(menuKey, selectedSectionKey);
    } else {
      setActiveSubmenu(defaultTarget);
    }
    applyContentForMenuTarget(menuKey, defaultTarget);
    if (
      menuKey === MEU_PERFIL_MENU_KEY &&
      typeof window.activateProfilePersonalSection === "function"
    ) {
      let selectedSectionItem = menuItems.find(
        (item) => String(item.profileSection || "") === meuPerfilSelectedProfileSection
      );
      if (!selectedSectionItem) {
        selectedSectionItem = menuItems.find((item) => item.target === defaultTarget) || menuItems[0];
      }
      if (selectedSectionItem) {
        const selectedSectionKey = String(selectedSectionItem.profileSection || "");
        meuPerfilSelectedProfileSection = selectedSectionKey;
        window.activateProfilePersonalSection(selectedSectionKey);
        applyMeuPerfilProcessSubsequentVisibility();
        const selectedLinkEl = itemsEl
          ? itemsEl.querySelector(
              `.submenu-item[data-profile-section="${selectedSectionKey.replace(/"/g, '\\"')}"]`
            )
          : null;
        if (selectedLinkEl) {
          setActiveSubmenu(defaultTarget, selectedLinkEl);
        }
      }
    }
    return;
  }
  applyContentForMenu(menuKey);
  setActiveSubmenu("");
}

function activateMenuTarget(menuKey, targetSelector) {
  const config = menuConfig[menuKey];
  if (!config) {
    return;
  }
  activateMenu(menuKey, { resetDynamicToFirst: false });
  if (!targetSelector) {
    return;
  }
  selectedTargetByMenu[menuKey] = targetSelector;
  setActiveSubmenu(targetSelector);
  applyContentForMenuTarget(menuKey, targetSelector);
  if (targetSelector === "#dynamic-process-card") {
    renderDynamicProcessCard(menuKey, selectedDynamicSectionByMenu[menuKey] || "");
  }
  const targetCard = document.querySelector(targetSelector);
  if (targetCard) {
    targetCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function handleHashNavigation(rawHash) {
  const cleanHash = String(rawHash || "").trim();
  if (!cleanHash) {
    return;
  }
  let normalizedHash = cleanHash;
  if (normalizedHash === "#edit-user-card") {
    normalizedHash = "#create-user-card";
  } else if (normalizedHash === "#edit-entity-card") {
    normalizedHash = "#create-entity-card";
  } else if (normalizedHash === "#configuracao-account-status-card") {
    normalizedHash = "#admin-account-status-card";
  }

  const hashTargetMenuMap = {
    "#create-user-card": "administrativo",
    "#create-entity-card": "administrativo",
    "#admin-account-status-card": "administrativo",
    "#admin-sidebar-sections-card": "administrativo",
    "#admin-account-create-card": "administrativo",
    "#settings-menu-edit-card": "administrativo"
  };
  const targetMenu = hashTargetMenuMap[normalizedHash];
  if (targetMenu) {
    activateMenuTarget(targetMenu, normalizedHash);
  }
}

const avatarDataUri = buildAvatarDataUri(currentUserName);
if (userAvatarImageEl) {
  userAvatarImageEl.src = avatarDataUri;
}
if (dropdownAvatarImageEl) {
  dropdownAvatarImageEl.src = avatarDataUri;
}

menuButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    activateMenu(normalizeMenuKey(btn.dataset.menu), { resetDynamicToFirst: true });
  });
});

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
    if (dynamicProcessHistoryActionInputEl) {
      dynamicProcessHistoryActionInputEl.value = "create";
    }
    if (dynamicProcessHistoryRecordIdInputEl) {
      dynamicProcessHistoryRecordIdInputEl.value = "";
    }
    if (dynamicProcessSubmitBtnEl) {
      dynamicProcessSubmitBtnEl.textContent = "Guardar";
    }
    if (dynamicProcessEditFormEl) {
      dynamicProcessEditFormEl.reset();
    }
  });
}

profileEditCancelButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const cardId = button.getAttribute("data-edit-cancel");
    if (!cardId) {
      return;
    }
    const card = document.getElementById(cardId);
    if (!card) {
      return;
    }
    card.classList.remove("editing");
    const form = card.querySelector(".profile-edit-form");
    if (form) {
      form.reset();
    }
  });
});

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

function setupCreateUserGenerateLinkShortcut() {
  const shortcutButtonEl = document.getElementById("create-user-generate-link-shortcut-btn");
  if (!shortcutButtonEl) {
    return;
  }
  const linkSlotEl = document.querySelector(".entity-create-link-slot");

  function renderGenerateLinkContent(contentEl) {
    if (!linkSlotEl) {
      return;
    }
    linkSlotEl.innerHTML = "";
    linkSlotEl.appendChild(contentEl);
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

window.addEventListener("hashchange", () => {
  handleHashNavigation(window.location.hash || "");
});

syncTrainingOutrosState();
renderHomeCharts();
setupReadOnlyCards();
setupProfileProcessTabs();
setupMeuPerfilQuantityRules();
setupConditionalProcessVisibility();
setupProcessEditTabs();
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
setupSidebarSectionsEditor();
setupTableLimiter("recent-entities");
setupTableLimiter("inactive-entities");
setupTableLimiter("admin-users");
const sidebarMenuKeys = new Set(Array.from(menuButtons).map((btn) => normalizeMenuKey(btn.dataset.menu)));
let startupMenu = menuConfig[initialMenu] ? initialMenu : "home";
if (!sidebarMenuKeys.has(startupMenu) && startupMenu !== "perfil") {
  if (sidebarMenuKeys.has("home")) {
    startupMenu = "home";
  } else {
    const firstSidebarMenu = Array.from(sidebarMenuKeys.values())[0];
    startupMenu = firstSidebarMenu || "home";
  }
}
activateMenu(startupMenu, { resetDynamicToFirst: false });
handleHashNavigation(window.location.hash || "");



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

// APPVERBO_MEU_PERFIL_QUANTITY_RENDERER_V1_START
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
        listOptions: listOptionsByKey.get(listKey) || []
      });
    });

    return fieldMetaMap;
  }

  function resolveQuantityControlNameV1(fieldKey) {
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
      if (fieldType === "email") {
        control.type = "email";
      } else if (fieldType === "phone") {
        control.type = "tel";
      } else if (fieldType === "number") {
        control.type = "number";
      } else if (fieldType === "date") {
        control.type = "date";
      } else if (fieldType === "flag") {
        control.type = "checkbox";
        control.value = "1";
        control.checked = ["1", "true", "sim", "yes", "on"].includes(
          toSafeStringMeuPerfilQuantityV1(existingValue).trim().toLowerCase()
        );
      } else {
        control.type = "text";
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

// APPVERBO_MEU_PERFIL_QUANTITY_RENDERER_V1_END

// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_START
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
    return document.querySelector("#perfil-pessoal-card .profile-readonly .personal-grid");
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

// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_END
