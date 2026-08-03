//###################################################################################
// (1) PROCESS KEYS REGISTRY
//###################################################################################
(function initAppGenesisProcessKeysRegistryV1(global) {
  const existingRegistry =
    global.AppGenesisProcessKeysRegistryV1 &&
    typeof global.AppGenesisProcessKeysRegistryV1 === "object"
      ? global.AppGenesisProcessKeysRegistryV1
      : null;

  if (existingRegistry) {
    return;
  }

  const MEU_PERFIL_MENU_KEY = "meu_perfil";
  const LEGACY_DOCUMENTOS_MENU_KEY = "documentos";
  const ESTRUTURAS_MENU_KEY_V1 = "sessoes";
  const EMPRESA_MENU_KEY_V1 = "empresa";

  function normalizeSettingsTabKey(value) {
    const cleanTab = String(value || "")
      .trim()
      .toLowerCase()
      .replace(/_/g, "-")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-+|-+$/g, "");

    if (!cleanTab) {
      return "";
    }

    const aliases = {
      geral: "geral",
      "dados-gerais": "geral",
      "campos-config": "campos-config",
      "configuracao-dos-campos": "campos-config",
      "configuração-dos-campos": "campos-config",
      "campos-adicionais": "campos-adicionais",
      "campos-quantidade": "campos-quantidade",
      lista: "lista",
      listas: "lista",
      "campos-subsequentes": "campos-subsequentes",
      "subsequent-fields": "campos-subsequentes",
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

  function normalizeTarget(value) {
    const cleanValue = String(value || "").trim();
    if (!cleanValue) {
      return "";
    }
    return cleanValue.startsWith("#") ? cleanValue : "#" + cleanValue;
  }

  global.AppGenesisProcessKeysRegistryV1 = Object.freeze({
    MEU_PERFIL_MENU_KEY,
    LEGACY_DOCUMENTOS_MENU_KEY,
    ESTRUTURAS_MENU_KEY_V1,
    EMPRESA_MENU_KEY_V1,
    normalizeMenuKey,
    normalizeSettingsTabKey,
    normalizeTarget
  });
})(window);
