//###################################################################################
// (1) MENU CONFIG RUNTIME V1
//###################################################################################
(function registerMenuConfigRuntimeV1() {
  "use strict";

  function buildMenuConfigRuntimeV1(context = {}) {
    const normalizeMenuKey = typeof context.normalizeMenuKey === "function"
      ? context.normalizeMenuKey
      : (value) => String(value || "").trim().toLowerCase();
    const MEU_PERFIL_MENU_KEY = String(context.MEU_PERFIL_MENU_KEY || "meu_perfil");

    const menuConfig = {
      home: {
        title: "Home",
        description: "Resumo geral do sistema.",
        singleView: true,
        toggleOnMenuClick: true,
        items: [{ label: "Resumo Geral", target: "#home-summary-card" }],
        details: [
          { label: "Entidades", value: String(((context.dashboardData || {}).totals || {}).entities || 0) },
          { label: "Utilizadores", value: String(((context.dashboardData || {}).totals || {}).users || 0) }
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
          { label: "Nome", value: context.currentUserName },
          { label: "Email", value: context.currentUserEmail },
          { label: "Telefone", value: context.currentUserPhone },
          { label: "Conta", value: context.currentUserAccountStatus },
          { label: "Membro", value: context.currentUserMemberStatus },
          { label: "Entidades", value: context.currentUserEntities },
          { label: "Tipo de acesso", value: "Utilizador" }
        ]
      },
      links: {
        title: "Links",
        description: "Atalhos internos do painel.",
        items: [{ label: "Sessao atual", target: "#sessao-card" }],
        details: [
          { label: "Modulo", value: "Links" },
          { label: "Status", value: "Ativo" }
        ]
      },
      contato: {
        title: "Contacto",
        description: "Informacoes e opcoes de contacto.",
        items: [
          { label: "Dados do utilizador ligado", target: "#sessao-card" }
        ],
        details: [
          { label: "Email", value: context.currentUserEmail },
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

    if (context.currentUserIsAdmin) {
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
            Array.isArray(context.profilePersonalSections) && context.profilePersonalSections.length
              ? context.profilePersonalSections.map((section) => ({
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
          description: "Acesso a opcoes de conta e estado.",
          items: [
            { label: "Estado da conta", target: "#create-user-card" },
            { label: "Historico de criacao", target: "#recent-users-card" }
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
            { label: "Ultimos criados", target: "#recent-users-card" },
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

    let homeSelectedTarget = "#home-summary-card";
    let profileSelectedTarget = "#perfil-pessoal-card";
    if (context.initialProfileTab === "morada") {
      profileSelectedTarget = "#perfil-morada-card";
    } else if (context.initialProfileTab === "treinamento") {
      profileSelectedTarget = "#dados-treinamento-card";
    }

    let adminSelectedTarget = "#dynamic-process-card";
    const meuPerfilSelectedTarget = "#perfil-pessoal-card";

    const requestedMeuPerfilProfileSection = normalizeMenuKey(
      (typeof window !== "undefined" && window.location && window.location.search)
        ? new URLSearchParams(window.location.search).get("profile_section")
        : ""
    );
    const meuPerfilSelectedProfileSection = (
      Array.isArray(context.profilePersonalSections) && context.profilePersonalSections.length
    )
      ? String(requestedMeuPerfilProfileSection || context.profilePersonalSections[0].key || "")
      : "";

    if (context.initialAdminTab === "entidade") {
      adminSelectedTarget = "#create-entity-card";
    } else if (context.initialAdminTab === "utilizador") {
      adminSelectedTarget = "#create-user-card";
    } else if (context.initialAdminTab === "sessoes") {
      adminSelectedTarget = "#admin-sidebar-sections-card";
    } else if (context.initialAdminTab === "menu") {
      adminSelectedTarget = "#admin-menu-card";
    } else if (context.initialAdminTab === "definicoes") {
      adminSelectedTarget = "#admin-definicoes-card";
    } else if (context.initialAdminTab === "contas") {
      adminSelectedTarget = "#admin-account-status-card";
    }

    if (context.startupHash === "#home-summary-card") {
      homeSelectedTarget = context.startupHash;
    }

    if (
      context.startupHash === "#create-user-card" ||
      context.startupHash === "#edit-user-card" ||
      context.startupHash === "#admin-user-shadow-readonly-card" ||
      context.startupHash === "#admin-user-shadow-inactive-card" ||
      context.startupHash === "#admin-users-created-card" ||
      context.startupHash === "#inactive-users-card"
    ) {
      adminSelectedTarget = "#create-user-card";
    } else if (
      context.startupHash === "#create-entity-card" ||
      context.startupHash === "#edit-entity-card" ||
      context.startupHash === "#admin-subprocess-v2-entidade"
    ) {
      adminSelectedTarget = "#create-entity-card";
    } else if (context.startupHash === "#admin-sidebar-sections-card") {
      adminSelectedTarget = "#admin-sidebar-sections-card";
    } else if (
      context.startupHash === "#admin-menu-card" ||
      context.startupHash === "#admin-menu-card-inactive" ||
      context.startupHash === "#admin-menu-card-create"
    ) {
      adminSelectedTarget = "#admin-menu-card";
    } else if (
      context.startupHash === "#admin-definicoes-card" ||
      context.startupHash === "#admin-definicoes-card-create" ||
      context.startupHash === "#admin-definicoes-card-inactive" ||
      context.startupHash === "#admin-definicoes-card-edit"
    ) {
      adminSelectedTarget = "#admin-definicoes-card";
    } else if (context.startupHash === "#settings-menu-edit-card") {
      adminSelectedTarget = "#settings-menu-edit-card";
    }

    if (!context.startupHash && context.settingsEditKey) {
      adminSelectedTarget = "#settings-menu-edit-card";
    }
    if (!context.startupHash && context.initialMenu === "administrativo" && !context.settingsEditKey && !context.initialMenuTarget) {
      adminSelectedTarget = "#dynamic-process-card";
    }

    const selectedTargetByMenu = {
      home: homeSelectedTarget,
      perfil: profileSelectedTarget,
      administrativo: adminSelectedTarget,
      [MEU_PERFIL_MENU_KEY]: meuPerfilSelectedTarget
    };

    Object.keys(context.dynamicProcessDataByMenu || {}).forEach((menuKey) => {
      if (menuKey === "administrativo" && selectedTargetByMenu[menuKey] === "#settings-menu-edit-card") {
        return;
      }
      selectedTargetByMenu[menuKey] = "#dynamic-process-card";
    });

    if (!context.startupHash && context.initialMenuTarget && menuConfig[context.initialMenu]) {
      const cleanInitialTarget = String(context.initialMenuTarget || "");
      const initialMenuItems = Array.isArray(menuConfig[context.initialMenu].items)
        ? menuConfig[context.initialMenu].items
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
        selectedTargetByMenu[context.initialMenu] = cleanInitialTarget;
      }
    }

    if (
      !context.startupHash &&
      context.initialDynamicProcessSection &&
      context.selectedDynamicSectionByMenu &&
      context.selectedDynamicSectionByMenu[context.initialMenu]
    ) {
      context.selectedDynamicSectionByMenu[context.initialMenu] = String(context.initialDynamicProcessSection);
    }

    return {
      menuConfig,
      selectedTargetByMenu,
      meuPerfilSelectedProfileSection,
      hiddenMeuPerfilSectionKeys: new Set(),
      activeMenuKey: ""
    };
  }

  window.APPVERBO_BUILD_MENU_CONFIG_RUNTIME_V1 = buildMenuConfigRuntimeV1;
})();
