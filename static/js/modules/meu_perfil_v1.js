//###################################################################################
// (1) DOMINIO CANONICO: MEU PERFIL
//###################################################################################
(function initAppGenesisMeuPerfilV1(global) {
  if (global.AppGenesisMeuPerfilV1 && typeof global.AppGenesisMeuPerfilV1 === "object") {
    return;
  }

  const bootstrap = global.__APPGENESIS_BOOTSTRAP__ || {};
  const meuPerfilBootstrap = (
    bootstrap.meuPerfil &&
    typeof bootstrap.meuPerfil === "object" &&
    !Array.isArray(bootstrap.meuPerfil)
  )
    ? bootstrap.meuPerfil
    : {};

  const MENU_KEY = "meu_perfil";
  const TAB_TARGETS = {
    pessoal: "#perfil-pessoal-card",
    morada: "#perfil-morada-card",
    treinamento: "#dados-treinamento-card"
  };

  function normalizeMenuKey(value) {
    const cleanValue = String(value || "").trim().toLowerCase();
    if (!cleanValue) {
      return "";
    }
    if (cleanValue === "perfil" || cleanValue === "documentos" || cleanValue === MENU_KEY) {
      return MENU_KEY;
    }
    return cleanValue;
  }

  function normalizeTabKey(value) {
    const cleanValue = String(value || "").trim().toLowerCase();
    if (cleanValue === "morada" || cleanValue === "treinamento") {
      return cleanValue;
    }
    return "pessoal";
  }

  function resolveTabTarget(tabKey) {
    return TAB_TARGETS[normalizeTabKey(tabKey)] || TAB_TARGETS.pessoal;
  }

  function resolvePersonalCardTarget() {
    const bootstrapTarget = String(meuPerfilBootstrap.personalCardTarget || "").trim();
    return bootstrapTarget || TAB_TARGETS.pessoal;
  }

  function getTabs() {
    const tabs = Array.isArray(meuPerfilBootstrap.tabs) ? meuPerfilBootstrap.tabs : [];
    if (tabs.length) {
      return tabs;
    }
    return [
      { key: "pessoal", label: "Pessoal", target: TAB_TARGETS.pessoal },
      { key: "morada", label: "Morada", target: TAB_TARGETS.morada },
      { key: "treinamento", label: "Treinamento", target: TAB_TARGETS.treinamento }
    ];
  }

  function getBootstrap() {
    const activeTab = normalizeTabKey(meuPerfilBootstrap.activeTab || "pessoal");
    const activePersonalSection = String(
      meuPerfilBootstrap.activePersonalSection ||
      meuPerfilBootstrap.activeSection ||
      ""
    ).trim().toLowerCase();
    return {
      menuKey: normalizeMenuKey(meuPerfilBootstrap.menuKey || MENU_KEY) || MENU_KEY,
      tabs: getTabs(),
      activeTab,
      activeTarget: resolveTabTarget(activeTab),
      activeSection: activePersonalSection,
      activePersonalSection,
      personalSections: Array.isArray(meuPerfilBootstrap.personalSections)
        ? meuPerfilBootstrap.personalSections
        : [],
      personalFieldSectionMap: meuPerfilBootstrap.personalFieldSectionMap && typeof meuPerfilBootstrap.personalFieldSectionMap === "object"
        ? meuPerfilBootstrap.personalFieldSectionMap
        : {},
      visibleFields: Array.isArray(meuPerfilBootstrap.visibleFields)
        ? meuPerfilBootstrap.visibleFields
        : [],
      fieldLabels: meuPerfilBootstrap.fieldLabels && typeof meuPerfilBootstrap.fieldLabels === "object"
        ? meuPerfilBootstrap.fieldLabels
        : {},
      personalCardTarget: resolvePersonalCardTarget()
    };
  }

  global.AppGenesisMeuPerfilV1 = Object.freeze({
    MENU_KEY,
    TAB_TARGETS,
    normalizeMenuKey,
    normalizeTabKey,
    resolvePersonalCardTarget,
    resolveTabTarget,
    getTabs,
    getBootstrap
  });
})(window);
