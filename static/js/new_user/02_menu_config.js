// new_user/02_menu_config.js: Configuracao de menus/processos, elementos do DOM e alvos nativos.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

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
      isRequired: normalizeProcessFieldRequired(optionRequiredRaw),
      editableWhen: option.editable_when || null,
      requiredWhen: option.required_when || null,
      visibleWhen: option.visible_when || null,
      autoDocumentNumber: option.auto_document_number || null,
      addButtonLabel: option.add_button_label || null,
      rowFields: Array.isArray(option.row_fields) ? option.row_fields : []
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
      editableWhen: fieldMeta.editableWhen || null,
      requiredWhen: fieldMeta.requiredWhen || null,
      visibleWhen: fieldMeta.visibleWhen || null,
      autoDocumentNumber: fieldMeta.autoDocumentNumber || null,
      addButtonLabel: fieldMeta.addButtonLabel || null,
      rowFields: Array.isArray(fieldMeta.rowFields) ? fieldMeta.rowFields : [],
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
const EMPRESA_NATIVE_TARGETS_V1 = new Set(["#empresa-card"]);

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
    getDynamicProcessLayoutConfig,
    getSidebarAdminSubprocessSetting: getSidebarAdminSubprocessSettingV1,
    filterProcessExtraMenuItems: filterProcessExtraMenuItemsV1,
    buildMenuItemUniqueKey: buildMenuItemUniqueKey_v1,
    dashboardData,
    profilePersonalSections,
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
  appGenesisProcessMenuConfigBuilderV1.initializeMenuConfig({ profilePersonalSections });
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
const dynamicProcessTitleEl = document.getElementById("dynamic-process-title");
const dynamicProcessDescriptionEl = document.getElementById("dynamic-process-description");
const dynamicProcessSectionLabelEl = document.getElementById("dynamic-process-section-label");
const dynamicProcessReadOnlyGridEl = document.getElementById("dynamic-process-readonly-grid");
const dynamicProcessEditGridEl = document.getElementById("dynamic-process-edit-grid");
const dynamicProcessEditFormEl = document.getElementById("dynamic-process-edit-form");
// Verdadeiro enquanto populateDynamicProcessListFormV1 preenche o formulario (evita redesenhos durante o preenchimento).
let dynamicProcessPopulatingV1 = false;
// Formulario de processo de lista: posicao original e linha onde esta aberto (edicao/criacao inline).
let dynamicProcessInlineOriginV1 = null;
let dynamicProcessInlineHolderV1 = null;
// Valores do formulario inline no momento em que abriu (para saber se houve alteracoes).
let dynamicProcessInlineSnapshotV1 = "";
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
let profileSelectedTarget = "#perfil-pessoal-card";
// APPGENESIS_ADMIN_TARGET_RESOLVER_V1_START
const NATIVE_ADMIN_TARGETS_V1 = appGenesisAdminTargetRegistryV1
  ? appGenesisAdminTargetRegistryV1.NATIVE_ADMIN_TARGETS_V1
  : new Set([
      "#create-entity-card",
      "#edit-entity-card",
      "#recent-entities-card",
      "#inactive-entities-card",
      "#create-user-card",
      "#edit-user-card",
      "#admin-users-created-card",
      "#inactive-users-card",
      "#admin-account-create-card",
      "#admin-account-status-card",
      "#admin-sidebar-sections-card",
      "#admin-sidebar-sections-form-card",
      "#settings-card",
      "#settings-menu-edit-card"
    ]);
const ESTRUTURAS_NATIVE_TARGETS_V1 = appGenesisAdminTargetRegistryV1
  ? appGenesisAdminTargetRegistryV1.ESTRUTURAS_NATIVE_TARGETS_V1
  : new Set([
      "#admin-account-create-card",
      "#admin-account-status-card",
      "#menu-subprocess-card",
      "#menu-subprocess-card-active",
      "#menu-subprocess-card-inactive",
      "#admin-sidebar-sections-card",
      "#admin-sidebar-sections-card-active",
      "#admin-sidebar-sections-card-inactive",
      "#admin-sidebar-sections-form-card",
      "#settings-card",
      "#settings-menu-edit-card"
    ]);
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
  : Object.freeze({
      "#auth-profile": "#auth-profile-card",
      "#auth-profile-card": "#auth-profile-card",
      "#auth-profile-active-card": "#auth-profile-card",
      "#auth-profile-inactive-card": "#auth-profile-card",
      "#auth-profile-form-card": "#auth-profile-card",
    });
const AUTH_PROFILE_NATIVE_TARGETS_V1 = appGenesisAdminTargetRegistryV1
  ? appGenesisAdminTargetRegistryV1.AUTH_PROFILE_NATIVE_TARGETS_V1
  : new Set(Object.keys(AUTHORIZATION_PROFILE_TARGET_ALIAS_MAP_V1));
function normalizeAuthorizationProfileTargetV1(value) {
  if (
    appGenesisAdminTargetRegistryV1 &&
    typeof appGenesisAdminTargetRegistryV1.normalizeAuthorizationProfileTarget === "function"
  ) {
    return appGenesisAdminTargetRegistryV1.normalizeAuthorizationProfileTarget(value);
  }
  return AUTHORIZATION_PROFILE_TARGET_ALIAS_MAP_V1[normalizeTargetV1(value)] || "";
}
function authorizationProfileTargetsMatchV1(leftTarget, rightTarget) {
  if (
    appGenesisAdminTargetRegistryV1 &&
    typeof appGenesisAdminTargetRegistryV1.authorizationProfileTargetsMatch === "function"
  ) {
    return appGenesisAdminTargetRegistryV1.authorizationProfileTargetsMatch(leftTarget, rightTarget);
  }
  const normalizedLeftTarget = normalizeAuthorizationProfileTargetV1(leftTarget);
  const normalizedRightTarget = normalizeAuthorizationProfileTargetV1(rightTarget);
  if (normalizedLeftTarget || normalizedRightTarget) {
    return normalizedLeftTarget === normalizedRightTarget;
  }
  return normalizeTargetV1(leftTarget) === normalizeTargetV1(rightTarget);
}
function isNativeAdminTargetV1(value) {
  if (
    appGenesisAdminTargetRegistryV1 &&
    typeof appGenesisAdminTargetRegistryV1.isNativeAdminTarget === "function"
  ) {
    return appGenesisAdminTargetRegistryV1.isNativeAdminTarget(value);
  }
  return NATIVE_ADMIN_TARGETS_V1.has(normalizeTargetV1(value));
}
function isNativeTargetForMenuV1(menuKey, value) {
  if (
    appGenesisAdminTargetRegistryV1 &&
    typeof appGenesisAdminTargetRegistryV1.isNativeTargetForMenu === "function"
  ) {
    return appGenesisAdminTargetRegistryV1.isNativeTargetForMenu(menuKey, value);
  }
  const cleanMenuKey = normalizeMenuKey(menuKey);
  let cleanTarget = normalizeTargetV1(value);

  if (!cleanTarget) {
    return false;
  }

  // Normalize subprocess target suffixes (like -active, -inactive, -form-card)
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

  if (cleanMenuKey === ADMINISTRATIVO_MENU_KEY_V1) {
    return NATIVE_ADMIN_TARGETS_V1.has(cleanTarget) || NATIVE_ADMIN_TARGETS_V1.has(normalizeTargetV1(value));
  }

  if (cleanMenuKey === ESTRUTURAS_MENU_KEY_V1) {
    return ESTRUTURAS_NATIVE_TARGETS_V1.has(cleanTarget) || ESTRUTURAS_NATIVE_TARGETS_V1.has(normalizeTargetV1(value));
  }

  if (cleanMenuKey === EMPRESA_MENU_KEY_V1) {
    return EMPRESA_NATIVE_TARGETS_V1.has(cleanTarget) || EMPRESA_NATIVE_TARGETS_V1.has(normalizeTargetV1(value));
  }

  if (cleanMenuKey === PERFIL_AUTORIZACAO_MENU_KEY_V1) {
    return (
      AUTH_PROFILE_NATIVE_TARGETS_V1.has(cleanTarget) ||
      AUTH_PROFILE_NATIVE_TARGETS_V1.has(normalizeTargetV1(value))
    );
  }

  const sidebarAdminSubprocessSetting = getSidebarAdminSubprocessSettingV1(cleanMenuKey);
  if (sidebarAdminSubprocessSetting) {
    return (
      cleanTarget === sidebarAdminSubprocessSetting.defaultTarget ||
      cleanTarget === sidebarAdminSubprocessSetting.editTarget ||
      normalizeTargetV1(value) === sidebarAdminSubprocessSetting.defaultTarget ||
      normalizeTargetV1(value) === sidebarAdminSubprocessSetting.editTarget
    );
  }

  return false;
}



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
