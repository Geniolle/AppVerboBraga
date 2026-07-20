//###################################################################################
// (1) PROCESS MENU CONFIG BUILDER
//###################################################################################
(function initAppGenesisProcessMenuConfigBuilderV1(global) {
  const existingBuilder =
    global.AppGenesisProcessMenuConfigBuilderV1 &&
    typeof global.AppGenesisProcessMenuConfigBuilderV1 === "object"
      ? global.AppGenesisProcessMenuConfigBuilderV1
      : null;

  if (existingBuilder) {
    return;
  }

  const menuConfig = {};
  const dynamicProcessDataByMenu = {};
  const selectedDynamicSectionByMenu = {};

  const state = {
    normalizeMenuKey: function (value) {
      return String(value || "").trim().toLowerCase();
    },
    normalizeMenuLabelPreserveCase: function (value) {
      return String(value || "").trim();
    },
    toSentenceCaseText: function (value) {
      return String(value || "").trim();
    },
    buildProcessSections: function () {
      return [];
    },
    getDynamicProcessLayoutConfig: function () {
      return {};
    },
    getSidebarAdminSubprocessSetting: function () {
      return null;
    },
    filterProcessExtraMenuItems: function (items) {
      return Array.isArray(items) ? items : [];
    },
    buildMenuItemUniqueKey: function (item) {
      const cleanTarget = String(item && item.target ? item.target : "").trim();
      const cleanSectionKey = String(
        item && item.dynamicProcessSectionKey ? item.dynamicProcessSectionKey : ""
      ).trim();
      return cleanSectionKey ? cleanTarget + "::" + cleanSectionKey : cleanTarget;
    },
    dashboardData: {},
    profilePersonalSections: [],
    sidebarMenuSettings: [],
    visibleSidebarMenuKeys: new Set(),
    menuProcessValuesMap: {},
    currentUserName: "",
    currentUserEmail: "",
    currentUserPhone: "",
    currentUserAccountStatus: "",
    currentUserMemberStatus: "",
    currentUserEntities: "",
    currentUserIsAdmin: false,
    initialMenu: "",
    initialDynamicProcessSection: "",
    MEU_PERFIL_MENU_KEY: "meu_perfil",
    ESTRUTURAS_MENU_KEY_V1: "sessoes",
    EMPRESA_MENU_KEY_V1: "empresa",
    documentRef: global.document || null
  };

  function clearObject(target) {
    Object.keys(target).forEach((key) => {
      delete target[key];
    });
  }

  function configure(options) {
    const safeOptions = options && typeof options === "object" ? options : {};

    if (typeof safeOptions.normalizeMenuKey === "function") {
      state.normalizeMenuKey = safeOptions.normalizeMenuKey;
    }
    if (typeof safeOptions.normalizeMenuLabelPreserveCase === "function") {
      state.normalizeMenuLabelPreserveCase = safeOptions.normalizeMenuLabelPreserveCase;
    }
    if (typeof safeOptions.toSentenceCaseText === "function") {
      state.toSentenceCaseText = safeOptions.toSentenceCaseText;
    }
    if (typeof safeOptions.buildProcessSections === "function") {
      state.buildProcessSections = safeOptions.buildProcessSections;
    }
    if (typeof safeOptions.getDynamicProcessLayoutConfig === "function") {
      state.getDynamicProcessLayoutConfig = safeOptions.getDynamicProcessLayoutConfig;
    }
    if (typeof safeOptions.getSidebarAdminSubprocessSetting === "function") {
      state.getSidebarAdminSubprocessSetting = safeOptions.getSidebarAdminSubprocessSetting;
    }
    if (typeof safeOptions.filterProcessExtraMenuItems === "function") {
      state.filterProcessExtraMenuItems = safeOptions.filterProcessExtraMenuItems;
    }
    if (typeof safeOptions.buildMenuItemUniqueKey === "function") {
      state.buildMenuItemUniqueKey = safeOptions.buildMenuItemUniqueKey;
    }
    if (safeOptions.dashboardData && typeof safeOptions.dashboardData === "object") {
      state.dashboardData = safeOptions.dashboardData;
    }
    const safeMeuPerfil = safeOptions.meuPerfil && typeof safeOptions.meuPerfil === "object"
      ? safeOptions.meuPerfil
      : null;
    if (Array.isArray(safeMeuPerfil && safeMeuPerfil.personalSections)) {
      state.profilePersonalSections = safeMeuPerfil.personalSections;
    } else if (Array.isArray(safeOptions.profilePersonalSections)) {
      state.profilePersonalSections = safeOptions.profilePersonalSections;
    }
    if (Array.isArray(safeOptions.sidebarMenuSettings)) {
      state.sidebarMenuSettings = safeOptions.sidebarMenuSettings;
    }
    if (safeOptions.visibleSidebarMenuKeys instanceof Set) {
      state.visibleSidebarMenuKeys = safeOptions.visibleSidebarMenuKeys;
    } else if (Array.isArray(safeOptions.visibleSidebarMenuKeys)) {
      state.visibleSidebarMenuKeys = new Set(safeOptions.visibleSidebarMenuKeys);
    }
    if (
      safeOptions.menuProcessValuesMap &&
      typeof safeOptions.menuProcessValuesMap === "object" &&
      !Array.isArray(safeOptions.menuProcessValuesMap)
    ) {
      state.menuProcessValuesMap = safeOptions.menuProcessValuesMap;
    }
    if (typeof safeOptions.currentUserName === "string") {
      state.currentUserName = safeOptions.currentUserName;
    }
    if (typeof safeOptions.currentUserEmail === "string") {
      state.currentUserEmail = safeOptions.currentUserEmail;
    }
    if (typeof safeOptions.currentUserPhone === "string") {
      state.currentUserPhone = safeOptions.currentUserPhone;
    }
    if (typeof safeOptions.currentUserAccountStatus === "string") {
      state.currentUserAccountStatus = safeOptions.currentUserAccountStatus;
    }
    if (typeof safeOptions.currentUserMemberStatus === "string") {
      state.currentUserMemberStatus = safeOptions.currentUserMemberStatus;
    }
    if (typeof safeOptions.currentUserEntities === "string") {
      state.currentUserEntities = safeOptions.currentUserEntities;
    }
    state.currentUserIsAdmin = Boolean(safeOptions.currentUserIsAdmin);
    if (typeof safeOptions.initialMenu === "string") {
      state.initialMenu = safeOptions.initialMenu;
    }
    if (typeof safeOptions.initialDynamicProcessSection === "string") {
      state.initialDynamicProcessSection = safeOptions.initialDynamicProcessSection;
    }
    if (typeof safeOptions.MEU_PERFIL_MENU_KEY === "string" && safeOptions.MEU_PERFIL_MENU_KEY.trim()) {
      state.MEU_PERFIL_MENU_KEY = safeOptions.MEU_PERFIL_MENU_KEY.trim();
    }
    if (
      typeof safeOptions.ESTRUTURAS_MENU_KEY_V1 === "string" &&
      safeOptions.ESTRUTURAS_MENU_KEY_V1.trim()
    ) {
      state.ESTRUTURAS_MENU_KEY_V1 = safeOptions.ESTRUTURAS_MENU_KEY_V1.trim();
    }
    if (typeof safeOptions.EMPRESA_MENU_KEY_V1 === "string" && safeOptions.EMPRESA_MENU_KEY_V1.trim()) {
      state.EMPRESA_MENU_KEY_V1 = safeOptions.EMPRESA_MENU_KEY_V1.trim();
    }
    if (safeOptions.documentRef) {
      state.documentRef = safeOptions.documentRef;
    }
  }

  function buildBaseMenuConfig() {
    const baseMenuConfig = {
      home: {
        title: "Home",
        description: "Resumo geral do sistema.",
        singleView: true,
        toggleOnMenuClick: true,
        items: [{ label: "Resumo Geral", target: "#home-summary-card" }],
        details: [
          {
            label: "Entidades",
            value: String(((state.dashboardData || {}).totals || {}).entities || 0)
          },
          {
            label: "Utilizadores",
            value: String(((state.dashboardData || {}).totals || {}).users || 0)
          }
        ]
      },
      meu_perfil: {
        title: "Meu perfil",
        description: "Opcoes do perfil do utilizador.",
        singleView: true,
        toggleOnMenuClick: true,
        items: [
          { label: "Dados pessoais", target: "#perfil-pessoal-card" },
          { label: "Dados de morada", target: "#perfil-morada-card" },
          { label: "Dados de Treinamento", target: "#dados-treinamento-card" }
        ],
        details: [
          { label: "Nome", value: state.currentUserName },
          { label: "Email", value: state.currentUserEmail },
          { label: "Telefone", value: state.currentUserPhone },
          { label: "Conta", value: state.currentUserAccountStatus },
          { label: "Membro", value: state.currentUserMemberStatus },
          { label: "Entidades", value: state.currentUserEntities },
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
        items: [{ label: "Dados do utilizador ligado", target: "#sessao-card" }],
        details: [
          { label: "Email", value: state.currentUserEmail },
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

    if (!state.currentUserIsAdmin) {
      return baseMenuConfig;
    }

    Object.assign(baseMenuConfig, {
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
      [state.MEU_PERFIL_MENU_KEY]: {
        title: "Meus dados",
        description: "Dados do meu perfil.",
        singleView: true,
        toggleOnMenuClick: true,
        items: (
          Array.isArray(state.profilePersonalSections) && state.profilePersonalSections.length
            ? state.profilePersonalSections.map((section) => ({
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

    baseMenuConfig.links.items.push({ label: "Criar utilizador", target: "#create-user-card" });
    baseMenuConfig.tutorial.items = [
      { label: "Passo 1: criar utilizador", target: "#create-user-card" },
      { label: "Passo 2: validar em historico", target: "#recent-users-card" }
    ];

    return baseMenuConfig;
  }

  function buildStructuredProcessMenuItemsV1(menuKey, dynamicItems) {
    const cleanMenuKey = state.normalizeMenuKey(menuKey);
    let baseItems = null;

    if (cleanMenuKey === "administrativo") {
      baseItems = [
        { label: "Entidade", target: "#recent-entities-card" },
        { label: "Utilizador", target: "#create-user-card" }
      ];
    } else if (cleanMenuKey === state.ESTRUTURAS_MENU_KEY_V1) {
      baseItems = [
        { label: "Sessões", target: "#admin-sidebar-sections-card" },
        { label: "Menu", target: "#menu-subprocess-card-active" }
      ];
    } else if (cleanMenuKey === "perfil_de_autorizacao") {
      baseItems = [
        { label: "Perfis", target: "#auth-profile-card" },
        { label: "Objeto de autorização", target: "#auth-objeto-card" }
      ];
    }

    if (!Array.isArray(baseItems)) {
      return null;
    }

    if (
      cleanMenuKey === "administrativo" ||
      cleanMenuKey === state.ESTRUTURAS_MENU_KEY_V1 ||
      cleanMenuKey === "perfil_de_autorizacao"
    ) {
      return baseItems;
    }

    const mergedItems = state.filterProcessExtraMenuItems(dynamicItems);
    const seenTargets = new Set(baseItems.map((item) => state.buildMenuItemUniqueKey(item)));
    const dynamicExtraItems = mergedItems.filter((item) => {
      const targetKey = state.buildMenuItemUniqueKey(item);
      if (!targetKey || seenTargets.has(targetKey)) {
        return false;
      }
      seenTargets.add(targetKey);
      return true;
    });

    return baseItems.concat(dynamicExtraItems);
  }

  function mergeDynamicProcessMenus() {
    state.sidebarMenuSettings.forEach((setting) => {
      const menuKey = state.normalizeMenuKey(setting.key);
      if (!menuKey || menuKey === state.MEU_PERFIL_MENU_KEY) {
        return;
      }
      if (menuKey === "home") {
        const sidebarLabel = state.normalizeMenuLabelPreserveCase(setting.label);
        delete dynamicProcessDataByMenu.home;
        delete selectedDynamicSectionByMenu.home;
        if (sidebarLabel) {
          menuConfig.home = {
            ...menuConfig.home,
            title: sidebarLabel
          };
        }
        return;
      }
      if (menuKey === state.MEU_PERFIL_MENU_KEY) {
        const sidebarLabel = state.normalizeMenuLabelPreserveCase(setting.label);
        if (sidebarLabel) {
          menuConfig[state.MEU_PERFIL_MENU_KEY] = {
            ...menuConfig[state.MEU_PERFIL_MENU_KEY],
            title: sidebarLabel
          };
        }
        return;
      }
      if (state.visibleSidebarMenuKeys.size && !state.visibleSidebarMenuKeys.has(menuKey)) {
        return;
      }

      const cleanMenuLabel = state.normalizeMenuLabelPreserveCase(setting.label) || "Processo";
      const existingConfig = menuConfig[menuKey];
      const nativeSubprocessSetting = state.getSidebarAdminSubprocessSetting(menuKey);

      if (menuKey === state.EMPRESA_MENU_KEY_V1) {
        menuConfig[state.EMPRESA_MENU_KEY_V1] = {
          ...(existingConfig || {}),
          title: cleanMenuLabel,
          singleView: true,
          toggleOnMenuClick: true,
          items: [{ label: "Dados institucionais", target: "#empresa-card" }]
        };
        return;
      }

      if (
        nativeSubprocessSetting &&
        menuKey !== state.ESTRUTURAS_MENU_KEY_V1 &&
        menuKey !== "perfil_de_autorizacao"
      ) {
        delete dynamicProcessDataByMenu[menuKey];
        delete selectedDynamicSectionByMenu[menuKey];

        menuConfig[menuKey] = {
          ...(existingConfig || {}),
          title: cleanMenuLabel,
          description: "Registos configurados para este processo.",
          singleView: true,
          toggleOnMenuClick: true,
          items: [
            {
              label: nativeSubprocessSetting.pluralLabel,
              target: nativeSubprocessSetting.defaultTarget
            }
          ],
          details: [
            { label: "Modulo", value: cleanMenuLabel },
            { label: "Status", value: "Ativo" }
          ]
        };
        return;
      }

      const menuValuesByField = (
        state.menuProcessValuesMap &&
        typeof state.menuProcessValuesMap[menuKey] === "object" &&
        state.menuProcessValuesMap[menuKey] !== null
      )
        ? state.menuProcessValuesMap[menuKey]
        : {};
      const sections = state.buildProcessSections(setting, menuValuesByField);
      if (!sections.length) {
        const structuredItems = buildStructuredProcessMenuItemsV1(menuKey, []);
        delete dynamicProcessDataByMenu[menuKey];
        delete selectedDynamicSectionByMenu[menuKey];
        if (existingConfig) {
          menuConfig[menuKey] = {
            ...existingConfig,
            items: structuredItems || []
          };
        } else {
          menuConfig[menuKey] = {
            title: cleanMenuLabel,
            description: "Campos configurados para este processo.",
            singleView: true,
            toggleOnMenuClick: true,
            items: structuredItems || [],
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
        sections,
        layoutConfig: state.getDynamicProcessLayoutConfig(setting, cleanMenuLabel, "")
      };
      if (
        menuKey === state.normalizeMenuKey(state.initialMenu) &&
        state.initialDynamicProcessSection &&
        sections.some((section) => String(section.key || "") === String(state.initialDynamicProcessSection))
      ) {
        selectedDynamicSectionByMenu[menuKey] = String(state.initialDynamicProcessSection);
      } else {
        selectedDynamicSectionByMenu[menuKey] = sections[0].key;
      }

      const dynamicItems = sections.map((section) => ({
        label: state.toSentenceCaseText(section.label || "Campos"),
        target: "#dynamic-process-card",
        dynamicProcessSectionKey: String(section.key || "__empty__")
      }));
      if (existingConfig) {
        const resolvedStructuredItems = buildStructuredProcessMenuItemsV1(menuKey, dynamicItems);
        if (resolvedStructuredItems) {
          menuConfig[menuKey] = {
            ...existingConfig,
            items: resolvedStructuredItems
          };
          return;
        }
        menuConfig[menuKey] = {
          ...existingConfig,
          items: dynamicItems
        };
        return;
      }
      const defaultStructuredItems = buildStructuredProcessMenuItemsV1(menuKey, dynamicItems);
      menuConfig[menuKey] = {
        title: cleanMenuLabel,
        description: "Campos configurados para este processo.",
        singleView: true,
        toggleOnMenuClick: true,
        items: defaultStructuredItems || dynamicItems,
        details: [
          { label: "Modulo", value: cleanMenuLabel },
          { label: "Status", value: "Ativo" }
        ]
      };
    });

    return menuConfig;
  }

  function ensureAuthorizationProfileMenuConfig() {
    const documentRef = state.documentRef;
    if (
      menuConfig.perfil_de_autorizacao ||
      !(
        state.normalizeMenuKey(state.initialMenu) === "perfil_de_autorizacao" ||
        state.visibleSidebarMenuKeys.has("perfil_de_autorizacao") ||
        (documentRef && documentRef.getElementById("auth-profile-card")) ||
        (documentRef && documentRef.getElementById("auth-profile-active-card")) ||
        (documentRef && documentRef.getElementById("auth-objeto-card")) ||
        (documentRef && documentRef.getElementById("auth-objeto-active-card"))
      )
    ) {
      return;
    }

    menuConfig.perfil_de_autorizacao = {
      title: "Perfil de autorização",
      singleView: true,
      items: [
        { label: "Perfis", target: "#auth-profile-card" },
        { label: "Objeto de autorização", target: "#auth-objeto-card" }
      ]
    };
  }

  function initializeMenuConfig(options) {
    clearObject(menuConfig);
    clearObject(dynamicProcessDataByMenu);
    clearObject(selectedDynamicSectionByMenu);
    configure(options);
    Object.assign(menuConfig, buildBaseMenuConfig());
    mergeDynamicProcessMenus();
    ensureAuthorizationProfileMenuConfig();
    return {
      menuConfig,
      dynamicProcessDataByMenu,
      selectedDynamicSectionByMenu
    };
  }

  global.AppGenesisProcessMenuConfigBuilderV1 = Object.freeze({
    configure,
    initializeMenuConfig,
    menuConfig,
    dynamicProcessDataByMenu,
    selectedDynamicSectionByMenu,
    buildStructuredProcessMenuItemsV1,
    mergeDynamicProcessMenus,
    ensureAuthorizationProfileMenuConfig
  });
})(window);
