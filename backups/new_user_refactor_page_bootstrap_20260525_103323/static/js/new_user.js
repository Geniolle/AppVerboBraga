// APPVERBO_POST_SAVE_CONTEXT_NAVIGATION_GUARD_V3
// O fluxo de navegacao pos-save foi extraido para:
// static/js/modules/post_save_context_navigation_guard_v3.js
const APPVERBO_POST_SAVE_CONTEXT_KEY_V3 = "appverbo:post-save-context-v3";

const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
const MEU_PERFIL_MENU_KEY = "meu_perfil";
const EMPRESA_MENU_KEY = "empresa";
const EMPRESA_INTERNAL_NUMBER_FIELD_KEY = "entity_internal_number";
const EMPRESA_LOGO_UPLOAD_FIELD_KEY = "entity_logo_file";
const EMPRESA_LOGO_CURRENT_FIELD_KEY = "entity_logo_current";
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
const initialAdminTab = bootstrap.initialAdminTab || "entidade";
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
const readOnlyDynamicProcessMenuKeys = new Set();


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

function isEmpresaProcessField(menuKey, fieldKey) {
  return (
    normalizeMenuKey(menuKey) === EMPRESA_MENU_KEY &&
    normalizeMenuKey(fieldKey) !== ""
  );
}

function isEmpresaReadOnlyField(menuKey, fieldKey) {
  return (
    isEmpresaProcessField(menuKey, fieldKey) &&
    normalizeMenuKey(fieldKey) === EMPRESA_INTERNAL_NUMBER_FIELD_KEY
  );
}

function isEmpresaLogoUploadField(menuKey, fieldKey) {
  return (
    isEmpresaProcessField(menuKey, fieldKey) &&
    normalizeMenuKey(fieldKey) === EMPRESA_LOGO_UPLOAD_FIELD_KEY
  );
}

function isEmpresaLogoCurrentField(menuKey, fieldKey) {
  return (
    isEmpresaProcessField(menuKey, fieldKey) &&
    normalizeMenuKey(fieldKey) === EMPRESA_LOGO_CURRENT_FIELD_KEY
  );
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
  if (typeof window.APPVERBO_BUILD_PROCESS_SECTIONS_V1 !== "function") {
    return [];
  }

  return window.APPVERBO_BUILD_PROCESS_SECTIONS_V1({
    setting,
    processValuesByField,
    helpers: {
      normalizeMenuKey,
      getProcessQuantityRepeatedFieldKeys,
      toSentenceCaseText,
      normalizeProcessFieldType,
      normalizeProcessFieldSize,
      normalizeProcessFieldRequired,
      getProcessStorageKey
    }
  });
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

// APPVERBO_MENU_DYNAMIC_MERGE_V1_START
(function runMenuDynamicMergeV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_MENU_DYNAMIC_NAVIGATION_CORE_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_MENU_DYNAMIC_NAVIGATION_CORE_V1({ source: "merge-stub" });
})();
// APPVERBO_MENU_DYNAMIC_MERGE_V1_END

const itemsEl = document.getElementById("submenu-items");
const menuTabsCardEl = document.getElementById("menu-tabs-card");
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
const dynamicProcessCreateCardEl = document.getElementById("dynamic-process-create-card");
const dynamicProcessCardEl = document.getElementById("dynamic-process-card");
const dynamicProcessTitleEl = document.getElementById("dynamic-process-title");
const dynamicProcessDescriptionEl = document.getElementById("dynamic-process-description");
const dynamicProcessSectionLabelEl = document.getElementById("dynamic-process-section-label");
const dynamicProcessReadOnlyEl = document.getElementById("dynamic-process-readonly");
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
const dynamicProcessHistoryActiveCardEl = document.getElementById("dynamic-process-history-active-card");
const dynamicProcessHistoryActiveTitleEl = document.getElementById("dynamic-process-history-active-title");
const dynamicProcessHistoryActiveTableEl = document.getElementById("dynamic-process-history-active-table");
const dynamicProcessHistoryActiveHeadEl = document.getElementById("dynamic-process-history-active-head");
const dynamicProcessHistoryActiveBodyEl = document.getElementById("dynamic-process-history-active-body");
const dynamicProcessHistoryActiveEmptyEl = document.getElementById("dynamic-process-history-active-empty");
const dynamicProcessHistoryInactiveCardEl = document.getElementById("dynamic-process-history-inactive-card");
const dynamicProcessHistoryInactiveTitleEl = document.getElementById("dynamic-process-history-inactive-title");
const dynamicProcessHistoryInactiveTableEl = document.getElementById("dynamic-process-history-inactive-table");
const dynamicProcessHistoryInactiveHeadEl = document.getElementById("dynamic-process-history-inactive-head");
const dynamicProcessHistoryInactiveBodyEl = document.getElementById("dynamic-process-history-inactive-body");
const dynamicProcessHistoryInactiveEmptyEl = document.getElementById("dynamic-process-history-inactive-empty");
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
} else if (initialAdminTab === "utilizador") {
  adminSelectedTarget = "#create-user-card";
} else if (initialAdminTab === "sessoes") {
  adminSelectedTarget = "#admin-sidebar-sections-card";
} else if (initialAdminTab === "menu") {
  adminSelectedTarget = "#admin-menu-card";
} else if (initialAdminTab === "definicoes") {
  adminSelectedTarget = "#admin-definicoes-card";
} else if (initialAdminTab === "contas") {
  adminSelectedTarget = "#admin-account-status-card";
}
if (startupHash === "#home-summary-card") {
  homeSelectedTarget = startupHash;
}
if (
  startupHash === "#create-user-card" ||
  startupHash === "#edit-user-card" ||
  startupHash === "#admin-user-shadow-readonly-card" ||
  startupHash === "#admin-user-shadow-inactive-card" ||
  startupHash === "#admin-users-created-card" ||
  startupHash === "#inactive-users-card"
) {
  adminSelectedTarget = "#create-user-card";
} else if (
  startupHash === "#create-entity-card" ||
  startupHash === "#edit-entity-card" ||
  startupHash === "#admin-subprocess-v2-entidade"
) {
  adminSelectedTarget = "#create-entity-card";
} else if (startupHash === "#admin-sidebar-sections-card") {
  adminSelectedTarget = "#admin-sidebar-sections-card";
} else if (
  startupHash === "#admin-menu-card" ||
  startupHash === "#admin-menu-card-inactive" ||
  startupHash === "#admin-menu-card-create"
) {
  adminSelectedTarget = "#admin-menu-card";
} else if (
  startupHash === "#admin-definicoes-card" ||
  startupHash === "#admin-definicoes-card-create" ||
  startupHash === "#admin-definicoes-card-inactive" ||
  startupHash === "#admin-definicoes-card-edit"
) {
  adminSelectedTarget = "#admin-definicoes-card";
} else if (startupHash === "#settings-menu-edit-card") {
  adminSelectedTarget = "#settings-menu-edit-card";
}
if (!startupHash && settingsEditKey) {
  adminSelectedTarget = "#settings-menu-edit-card";
}
if (!startupHash && initialMenu === "administrativo" && !settingsEditKey && !initialMenuTarget) {
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
  if (
    targetExistsInItems ||
    cleanInitialTarget === "#settings-menu-edit-card" ||
    cleanInitialTarget === "#admin-menu-card-create" ||
    cleanInitialTarget === "#admin-definicoes-card-create" ||
    cleanInitialTarget === "#admin-definicoes-card-inactive" ||
    cleanInitialTarget === "#admin-definicoes-card-edit"
  ) {
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
  if (typeof window.APPVERBO_RENDER_DYNAMIC_PROCESS_HISTORY_V1 !== "function") {
    return;
  }

  window.APPVERBO_RENDER_DYNAMIC_PROCESS_HISTORY_V1({
    menuKey,
    sectionKey,
    sectionLabel,
    sectionFields,
    recordLabels,
    helpers: {
      normalizeMenuKey,
      normalizeLookupText,
      normalizeProcessFieldType,
      normalizeDateInputValue,
      toSentenceCaseText,
      isTruthyFlagValue
    },
    data: {
      menuProcessHistoryMap
    },
    elements: {
      dynamicProcessHistoryBlockEl,
      dynamicProcessHistoryTableEl,
      dynamicProcessHistoryHeadEl,
      dynamicProcessHistoryBodyEl,
      dynamicProcessHistoryEmptyEl,
      dynamicProcessHistoryActiveCardEl,
      dynamicProcessHistoryActiveTitleEl,
      dynamicProcessHistoryActiveTableEl,
      dynamicProcessHistoryActiveHeadEl,
      dynamicProcessHistoryActiveBodyEl,
      dynamicProcessHistoryActiveEmptyEl,
      dynamicProcessHistoryInactiveCardEl,
      dynamicProcessHistoryInactiveTitleEl,
      dynamicProcessHistoryInactiveTableEl,
      dynamicProcessHistoryInactiveHeadEl,
      dynamicProcessHistoryInactiveBodyEl,
      dynamicProcessHistoryInactiveEmptyEl,
      dynamicProcessHistoryTitleEl,
      dynamicProcessReadOnlyGridEl,
      dynamicProcessReadOnlyEl,
      dynamicProcessEditFormEl,
      dynamicProcessHistoryActionInputEl,
      dynamicProcessHistoryRecordIdInputEl,
      dynamicProcessSubmitBtnEl,
      dynamicProcessCardEl,
      dynamicProcessCreateCardEl
    }
  });
}
function isMeuPerfilQuantityV4GeneratedTarget(targetEl) {
  if (!targetEl || typeof targetEl.closest !== "function") {
    return false;
  }

  if (targetEl.dataset && (
    targetEl.dataset.appverboQuantityFieldKeyV4 ||
    targetEl.dataset.appverboQuantityRuleKeyV4
  )) {
    return true;
  }

  return Boolean(
    targetEl.closest("[data-appverbo-quantity-edit-generated-v4='1']")
  );
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
  if (dynamicProcessCreateCardEl) {
    dynamicProcessCreateCardEl.classList.remove("is-editing");
  }
  if (dynamicProcessCardEl) {
    dynamicProcessCardEl.classList.remove("dynamic-process-history-show-readonly");
  }
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

// APPVERBO_PROFILE_PROCESS_RUNTIME_CORE_V1_START
(function runProfileProcessRuntimeCoreV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_PROFILE_PROCESS_RUNTIME_CORE_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_PROFILE_PROCESS_RUNTIME_CORE_V1({});
})();
// APPVERBO_PROFILE_PROCESS_RUNTIME_CORE_V1_END

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

  function getFilteredRows() {
    return rows.filter((row) => row.dataset.adminSearchMatchV1 !== "0");
  }

  function getTotalPages() {
    const filteredRows = getFilteredRows();
    return Math.max(1, Math.ceil(filteredRows.length / pageSize));
  }

  function render() {
    const filteredRows = getFilteredRows();
    const totalPages = getTotalPages();
    if (currentPage > totalPages) {
      currentPage = totalPages;
    }
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;

    const filteredRowSet = new Set(filteredRows);
    rows.forEach((row) => {
      if (!filteredRowSet.has(row)) {
        row.style.display = "none";
      }
    });

    filteredRows.forEach((row, index) => {
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

  tableEl.addEventListener("admin-table-filter-changed", () => {
    currentPage = 1;
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
  if (typeof window.APPVERBO_SETUP_PROCESS_FIELDS_BUILDER_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_PROCESS_FIELDS_BUILDER_V1();
}

function setupProcessAdditionalFieldsBuilder() {
  if (typeof window.APPVERBO_SETUP_PROCESS_ADDITIONAL_FIELDS_BUILDER_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_PROCESS_ADDITIONAL_FIELDS_BUILDER_V1();
}


// APPVERBO_PROCESS_ADDITIONAL_FIELDS_MANAGER_V2_MOVED_TO_MODULE
// Implementacao extraida para static/js/modules/process_additional_fields_manager_v2.js

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
      tabLink.style.removeProperty("background");
      tabLink.style.removeProperty("background-color");
      tabLink.style.removeProperty("border-color");
      tabLink.style.removeProperty("color");
      tabLink.classList.toggle("active", isActive);
      tabLink.classList.toggle("is-active", isActive);
      tabLink.setAttribute("aria-selected", isActive ? "true" : "false");
      if (isActive) {
        tabLink.setAttribute("data-active", "true");
        tabLink.setAttribute("data-selected", "true");
        tabLink.removeAttribute("data-appverbo-force-active");
        tabLink.removeAttribute("data-appverbo-force-inactive");
        tabLink.removeAttribute("data-appverbo-menu-active");
      } else {
        tabLink.removeAttribute("data-active");
        tabLink.removeAttribute("data-selected");
        tabLink.removeAttribute("data-appverbo-force-active");
        tabLink.removeAttribute("data-appverbo-force-inactive");
        tabLink.removeAttribute("data-appverbo-menu-active");
      }
    });
    panes.forEach((pane) => {
      const isActive = pane.getAttribute("data-process-edit-pane") === resolvedTabKey;
      pane.classList.toggle("active", isActive);
    });
    window.dispatchEvent(new CustomEvent("appverbo:normalize-tabs-width-v1"));
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

let appverboMenuNavigationControllerV1 = null;

function getMenuNavigationControllerV1() {
  if (appverboMenuNavigationControllerV1) {
    return appverboMenuNavigationControllerV1;
  }
  if (typeof window.APPVERBO_CREATE_MENU_NAVIGATION_CONTROLLER_V1 !== "function") {
    return null;
  }
  appverboMenuNavigationControllerV1 = window.APPVERBO_CREATE_MENU_NAVIGATION_CONTROLLER_V1({
    menuConfig,
    itemsEl,
    menuTabsCardEl,
    menuButtons,
    MEU_PERFIL_MENU_KEY,
    toSentenceCaseText,
    normalizeMenuKey,
    closeAllProfileEdits,
    setActiveSubmenu,
    applyContentForMenuTarget,
    applyContentForMenu,
    renderDynamicProcessCard,
    applyMeuPerfilProcessSubsequentVisibility,
    selectedTargetByMenu,
    selectedDynamicSectionByMenu,
    setActiveMenuKey: (nextMenuKey) => {
      activeMenuKey = nextMenuKey;
    },
    getMeuPerfilSelectedProfileSection: () => meuPerfilSelectedProfileSection,
    setMeuPerfilSelectedProfileSection: (nextSectionKey) => {
      meuPerfilSelectedProfileSection = String(nextSectionKey || "");
    }
  });
  return appverboMenuNavigationControllerV1;
}

function renderSubmenu(menuKey) {
  const controller = getMenuNavigationControllerV1();
  if (!controller) {
    return;
  }
  controller.renderSubmenu(menuKey);
}

function getDefaultTargetForMenu(menuKey, config, options = {}) {
  const controller = getMenuNavigationControllerV1();
  if (!controller) {
    return "";
  }
  return controller.getDefaultTargetForMenu(menuKey, config, options);
}

function activateMenu(menuKey, options = {}) {
  const controller = getMenuNavigationControllerV1();
  if (!controller) {
    return;
  }
  controller.activateMenu(menuKey, options);
}

function activateMenuTarget(menuKey, targetSelector) {
  const controller = getMenuNavigationControllerV1();
  if (!controller) {
    return;
  }
  controller.activateMenuTarget(menuKey, targetSelector);
}

function handleHashNavigation(rawHash) {
  const controller = getMenuNavigationControllerV1();
  if (!controller) {
    return;
  }
  controller.handleHashNavigation(rawHash);
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
    if (cardId === "dynamic-process-card" && dynamicProcessCreateCardEl) {
      dynamicProcessCreateCardEl.classList.add("is-editing");
    }
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
    if (dynamicProcessCardEl) {
      dynamicProcessCardEl.classList.remove("dynamic-process-history-show-readonly");
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
    if (cardId === "dynamic-process-card") {
      card.classList.remove("dynamic-process-history-show-readonly");
    }
    if (cardId === "dynamic-process-card" && dynamicProcessCreateCardEl) {
      dynamicProcessCreateCardEl.classList.remove("is-editing");
    }
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
  if (typeof window.APPVERBO_SETUP_GENERATED_INVITE_LINK_COPY_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_GENERATED_INVITE_LINK_COPY_V1();
}

function setupCreateUserGenerateLinkShortcut() {
  if (typeof window.APPVERBO_SETUP_CREATE_USER_GENERATE_LINK_SHORTCUT_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_CREATE_USER_GENERATE_LINK_SHORTCUT_V1({
    currentEntityId
  });
}

function setupSidebarSectionsEditor() {
  if (typeof window.APPVERBO_SETUP_SIDEBAR_SECTIONS_EDITOR_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_SIDEBAR_SECTIONS_EDITOR_V1();
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

  if (typeof window.setupProcessAdditionalFieldsManagerV2 === "function") {
    window.setupProcessAdditionalFieldsManagerV2();
  }
}

// APPVERBO_MEU_PERFIL_QUANTITY_RENDERER_V1_START
(function runMeuPerfilQuantityRendererV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_RENDERER_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_RENDERER_V1({});
})();
// APPVERBO_MEU_PERFIL_QUANTITY_RENDERER_V1_END

// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_START
(function runMeuPerfilQuantityReadonlyRendererV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1({});
})();
// APPVERBO_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_END

// APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_START
(function runMeuPerfilQuantityOriginDedupV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1({});
})();
// APPVERBO_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_END

// APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_START
(function runMeuPerfilEditSectionFilterV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_MEU_PERFIL_EDIT_SECTION_FILTER_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_MEU_PERFIL_EDIT_SECTION_FILTER_V1({});
})();
// APPVERBO_MEU_PERFIL_EDIT_SECTION_FILTER_V1_END

// APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START
(function runKeepCurrentProcessAfterProfileSaveV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1({});
})();
// APPVERBO_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_END

// APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_START
(function runPostSaveContextCaptureV3FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_POST_SAVE_CONTEXT_CAPTURE_V3 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_POST_SAVE_CONTEXT_CAPTURE_V3({
    APPVERBO_POST_SAVE_CONTEXT_KEY_V3,
    MEU_PERFIL_MENU_KEY,
    initialMenu,
    profilePersonalSections,
    selectedDynamicSectionByMenu,
    normalizeMenuKey,
    normalizeLookupText
  });
})();
// APPVERBO_POST_SAVE_CONTEXT_CAPTURE_V3_END

// APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_START
(function runReturnUrlPostSaveCaptureV4FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_RETURN_URL_POST_SAVE_CAPTURE_V4 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_RETURN_URL_POST_SAVE_CAPTURE_V4({
    initialMenu,
    profilePersonalSections,
    selectedDynamicSectionByMenu,
    normalizeMenuKey,
    normalizeLookupText
  });
})();
// APPVERBO_RETURN_URL_POST_SAVE_CAPTURE_V4_END

// APPVERBO_FRONTEND_RETURN_URL_POST_SAVE_V6_START
(function runFrontendReturnUrlPostSaveV6FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_FRONTEND_RETURN_URL_POST_SAVE_V6 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_FRONTEND_RETURN_URL_POST_SAVE_V6({
    initialMenu,
    profilePersonalSections,
    normalizeMenuKey,
    normalizeLookupText
  });
})();
// APPVERBO_FRONTEND_RETURN_URL_POST_SAVE_V6_END

// APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_START
(function runInitialProfileSectionFromUrlV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_INITIAL_PROFILE_SECTION_FROM_URL_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_INITIAL_PROFILE_SECTION_FROM_URL_V1({
    normalizeMenuKey,
    normalizeLookupText,
    profilePersonalSections
  });
})();
// APPVERBO_INITIAL_PROFILE_SECTION_FROM_URL_V1_END

// APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1_START
(function runMeuPerfilSubsequentVisibilityV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1({
    activeMenuKey,
    MEU_PERFIL_MENU_KEY,
    sidebarMenuSettings,
    profilePersonalSections,
    normalizeMenuKey,
    normalizeLookupText,
    getSidebarMenuSetting,
    normalizeProcessFieldType,
    normalizeProcessSubsequentRules,
    getHiddenProcessTargets,
    isMeuPerfilQuantityV4GeneratedTarget
  });
})();
// APPVERBO_MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1_END
/* APPVERBO_AUTO_DISMISS_FLASH_MESSAGES_V1_START */
(function runAutoDismissFlashMessagesV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_AUTO_DISMISS_FLASH_MESSAGES_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_AUTO_DISMISS_FLASH_MESSAGES_V1({});
})();
/* APPVERBO_AUTO_DISMISS_FLASH_MESSAGES_V1_END */

// APPVERBO_MEU_PERFIL_QUANTITY_SUBMIT_SYNC_V1_START
(function runMeuPerfilQuantitySubmitSyncV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_SUBMIT_SYNC_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_SUBMIT_SYNC_V1({
    collectCurrentMeuPerfilQuantityValues,
    syncMeuPerfilQuantityHiddenInputs
  });
})();
// APPVERBO_MEU_PERFIL_QUANTITY_SUBMIT_SYNC_V1_END

// APPVERBO_MESSAGE_DISMISS_SAFE_V5_START
(function runMessageDismissSafeV5FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_MESSAGE_DISMISS_SAFE_V5 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_MESSAGE_DISMISS_SAFE_V5({});
})();
// APPVERBO_MESSAGE_DISMISS_SAFE_V5_END

// APPVERBO_MARK_READY_V1_START
(function runMarkReadyV1FromModule() {
  "use strict";

  if (typeof window.APPVERBO_SETUP_MARK_READY_V1 !== "function") {
    return;
  }

  window.APPVERBO_SETUP_MARK_READY_V1({});
})();
// APPVERBO_MARK_READY_V1_END
