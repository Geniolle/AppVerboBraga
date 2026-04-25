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
if (navigationType === "reload" && window.location.pathname === "/users/new") {
  const homeUrl = "/users/new?menu=home";
  const currentPathAndQuery = `${window.location.pathname}${window.location.search}`;
  if (currentPathAndQuery !== homeUrl || window.location.hash) {
    window.location.replace(homeUrl);
  }
}

const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
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
const initialProfileTab = bootstrap.initialProfileTab || "pessoal";
const initialMenu = bootstrap.initialMenu || "home";
const initialMenuTarget = bootstrap.initialMenuTarget || "";
const initialDynamicProcessSection = bootstrap.initialDynamicProcessSection || "";
const initialAdminTab = bootstrap.initialAdminTab || "utilizador";
const currentEntityId = Number.parseInt(String(bootstrap.currentEntityId || "").trim(), 10);
const settingsAction = bootstrap.settingsAction || "";
const settingsTab = bootstrap.settingsTab || "";
const settingsEditKey = bootstrap.settingsEditKey || "";
const sidebarMenuSettings = Array.isArray(bootstrap.sidebarMenuSettings) ? bootstrap.sidebarMenuSettings : [];
const visibleSidebarMenuKeys = new Set(
  (Array.isArray(bootstrap.visibleSidebarMenuKeys) ? bootstrap.visibleSidebarMenuKeys : [])
    .map((menuKey) => String(menuKey || "").trim().toLowerCase())
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
const startupHash = window.location.hash || "";
const dynamicProcessDataByMenu = {};
const selectedDynamicSectionByMenu = {};
const processTextualTypes = new Set(["text", "number", "email", "phone"]);
const processSupportedTypes = new Set(["text", "number", "email", "phone", "date", "flag"]);

function normalizeMenuKey(value) {
  return String(value || "").trim().toLowerCase();
}

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
  const optionMetaByKey = new Map();
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
    optionMetaByKey.set(optionKey, {
      label: optionLabel,
      fieldType: optionType,
      size: optionSize,
      isRequired: normalizeProcessFieldRequired(option.is_required ?? option.required)
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
    configuracao: {
      title: "Configuração",
      description: "Configuração de processos de sistema.",
      singleView: true,
      toggleOnMenuClick: true,
      items: [
        { label: "Configuração", target: "#configuracao-account-status-card" }
      ],
      details: [
        { label: "Modulo", value: "Configuração" },
        { label: "Acesso", value: "Permitido" }
      ]
    },
    documentos: {
      title: "Meu perfil",
      description: "Dados do meu perfil.",
      singleView: true,
      toggleOnMenuClick: true,
      items: (
        Array.isArray(profilePersonalSections) && profilePersonalSections.length
          ? profilePersonalSections.map((section) => ({
              label: String(section.label || "Dados pessoais"),
              target: "#perfil-pessoal-card",
              profileSection: String(section.key || "geral")
            }))
          : [{ label: "Dados pessoais", target: "#perfil-pessoal-card", profileSection: "geral" }]
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
    if (menuKey === "documentos") {
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
          { label: "Configuração", target: "#admin-account-status-card" }
        ];
        const mergedItems = dynamicItems.filter((item) => {
          const sectionKey = String(item.dynamicProcessSectionKey || "").trim().toLowerCase();
          if (!sectionKey) {
            return false;
          }
          return sectionKey !== "__geral__" && !sectionKey.startsWith("field:");
        });
        const seenTargets = new Set(baseItems.map((item) => String(item.target || "")));
        const dynamicExtraItems = mergedItems.filter((item) => {
          const targetKey = String(item.target || "");
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
      if (menuKey === "configuracao") {
        menuConfig[menuKey] = {
          ...existingConfig,
          title: cleanMenuLabel || existingConfig.title,
          items: [
            { label: "Configuração", target: "#configuracao-account-status-card" },
            ...dynamicItems
          ]
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
let documentsSelectedTarget = "#perfil-pessoal-card";
let documentsSelectedProfileSection = (
  Array.isArray(profilePersonalSections) && profilePersonalSections.length
)
  ? String(profilePersonalSections[0].key || "geral")
  : "geral";
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
  documentos: documentsSelectedTarget
};
Object.keys(dynamicProcessDataByMenu).forEach((menuKey) => {
  if (menuKey === "administrativo" && selectedTargetByMenu[menuKey] === "#settings-menu-edit-card") {
    return;
  }
  if (menuKey === "configuracao") {
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

function renderDynamicProcessCard(menuKey, sectionKey) {
  if (!dynamicProcessCardEl) {
    return;
  }
  const cleanMenuKey = normalizeMenuKey(menuKey);
  const menuData = dynamicProcessDataByMenu[cleanMenuKey];
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
    return;
  }

  const cleanSectionKey = String(sectionKey || selectedDynamicSectionByMenu[cleanMenuKey] || "").trim();
  let selectedSection = menuData.sections.find((section) => String(section.key || "") === cleanSectionKey);
  if (!selectedSection) {
    selectedSection = menuData.sections[0];
  }
  if (selectedSection) {
    selectedDynamicSectionByMenu[cleanMenuKey] = String(selectedSection.key || "");
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

  const sectionFields = selectedSection && Array.isArray(selectedSection.fields)
    ? selectedSection.fields
    : [];
  if (!sectionFields.length) {
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
    return;
  }

  if (dynamicProcessEditToggleEl) {
    dynamicProcessEditToggleEl.style.display = "none";
    if (!absenceProcessMode) {
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
    const scopes = rawScope.split(",").map((value) => value.trim()).filter(Boolean);
    card.style.display = scopes.includes(menuKey) ? "" : "none";
  });
  if (dynamicProcessCardEl) {
    dynamicProcessCardEl.style.display = "none";
  }
}

function applyContentForMenuTarget(menuKey, targetSelector) {
  scopedCards.forEach((card) => {
    const rawScope = card.getAttribute("data-menu-scope") || "";
    const scopes = rawScope.split(",").map((value) => value.trim()).filter(Boolean);
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
    const isConfiguracaoSettingsGroupedBlock =
      menuKey === "configuracao" &&
      targetSelector === "#settings-menu-edit-card" &&
      (
        card.id === "configuracao-account-status-card" ||
        card.id === "settings-menu-edit-card"
      );
    card.style.display =
      targetSelector === ("#" + card.id) ||
      isEntityGroupedBlock ||
      isUserGroupedBlock ||
      isSettingsGroupedBlock ||
      isConfiguracaoSettingsGroupedBlock
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
      Array.from(sectionPanes).map((paneEl) =>
        String(paneEl.getAttribute("data-profile-section-pane") || "geral").trim().toLowerCase()
      )
    );
    const effectiveSection = availableSections.has(normalizedSection)
      ? normalizedSection
      : (Array.from(availableSections)[0] || "geral");

    sectionPanes.forEach((paneEl) => {
      const paneSection = String(
        paneEl.getAttribute("data-profile-section-pane") || "geral"
      ).trim().toLowerCase();
      paneEl.style.display = paneSection === effectiveSection ? "" : "none";
    });
    documentsSelectedProfileSection = effectiveSection;
  }

  window.activateProfilePersonalSection = activateSection;
  activateSection(documentsSelectedProfileSection);
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
  if (!containerEl || !addButtonEl || !formEl) {
    return;
  }

  const sizedTypes = new Set(["text", "number", "email", "phone"]);

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
    if (cleanType === "header" && rowEl.parentElement === containerEl) {
      const firstRowEl = containerEl.querySelector(".process-additional-field-row");
      if (firstRowEl && firstRowEl !== rowEl) {
        containerEl.insertBefore(rowEl, firstRowEl);
      }
    }
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

  function bindRemoveButton(buttonEl) {
    buttonEl.addEventListener("click", () => {
      const rowEl = buttonEl.closest(".process-additional-field-row");
      if (rowEl) {
        rowEl.remove();
      }
    });
  }

  function bindRow(rowEl) {
    const removeButtonEl = rowEl.querySelector(".process-additional-field-remove-btn");
    if (removeButtonEl) {
      bindRemoveButton(removeButtonEl);
    }
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
          placeholder="Ex.: 30"
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
    const inputEl = rowEl.querySelector("input[name='additional_field_label']");
    if (inputEl) {
      inputEl.focus();
    }
  });

  formEl.addEventListener("submit", () => {
    const headerRows = [];
    const nonHeaderRows = [];
    containerEl.querySelectorAll(".process-additional-field-row").forEach((rowEl) => {
      const typeEl = rowEl.querySelector("select[name='additional_field_type']");
      const cleanType = String(typeEl ? typeEl.value : "text").trim().toLowerCase();
      if (cleanType === "header") {
        headerRows.push(rowEl);
      } else {
        nonHeaderRows.push(rowEl);
      }
    });
    [...headerRows, ...nonHeaderRows].forEach((rowEl) => {
      containerEl.appendChild(rowEl);
    });

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
        menuKey === "documentos" &&
        typeof window.activateProfilePersonalSection === "function"
      ) {
        const sectionKey = String(item.profileSection || "geral");
        documentsSelectedProfileSection = sectionKey;
        window.activateProfilePersonalSection(sectionKey);
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
  const targetButton = Array.from(menuButtons).find((btn) => btn.dataset.menu === menuKey);
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
      menuKey === "documentos" &&
      typeof window.activateProfilePersonalSection === "function"
    ) {
      let selectedSectionItem = menuItems.find(
        (item) => String(item.profileSection || "") === documentsSelectedProfileSection
      );
      if (!selectedSectionItem) {
        selectedSectionItem = menuItems.find((item) => item.target === defaultTarget) || menuItems[0];
      }
      if (selectedSectionItem) {
        const selectedSectionKey = String(selectedSectionItem.profileSection || "geral");
        documentsSelectedProfileSection = selectedSectionKey;
        window.activateProfilePersonalSection(selectedSectionKey);
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
  }

  const params = new URLSearchParams(window.location.search || "");
  const currentQueryMenu = normalizeMenuKey(params.get("menu") || "");
  const hashTargetMenuMap = {
    "#create-user-card": "administrativo",
    "#create-entity-card": "administrativo",
    "#admin-account-status-card": "administrativo",
    "#admin-account-create-card": currentQueryMenu === "configuracao" ? "configuracao" : "administrativo",
    "#configuracao-account-status-card": "configuracao",
    "#settings-menu-edit-card": currentQueryMenu === "configuracao" ? "configuracao" : "administrativo"
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
    activateMenu(btn.dataset.menu, { resetDynamicToFirst: true });
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
    const menuKey = link.getAttribute("data-dropdown-menu") || "perfil";
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

window.addEventListener("hashchange", () => {
  handleHashNavigation(window.location.hash || "");
});

syncTrainingOutrosState();
renderHomeCharts();
setupReadOnlyCards();
setupProfileProcessTabs();
setupProcessEditTabs();
setupProcessFieldsBuilder();
setupProcessAdditionalFieldsBuilder();
setupGeneratedInviteLinkCopy();
setupCreateUserGenerateLinkShortcut();
setupTableLimiter("recent-entities");
setupTableLimiter("inactive-entities");
setupTableLimiter("admin-users");
const sidebarMenuKeys = new Set(Array.from(menuButtons).map((btn) => btn.dataset.menu));
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

