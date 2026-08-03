//###################################################################################
// (1) PROCESS REFERENCE REGISTRY
//###################################################################################
(function initAppGenesisProcessReferenceRegistryV1(global) {
  const existingRegistry =
    global.AppGenesisProcessReferenceRegistryV1 &&
    typeof global.AppGenesisProcessReferenceRegistryV1 === "object"
      ? global.AppGenesisProcessReferenceRegistryV1
      : null;

  if (existingRegistry) {
    return;
  }

  const processKeysRegistry =
    global.AppGenesisProcessKeysRegistryV1 &&
    typeof global.AppGenesisProcessKeysRegistryV1 === "object"
      ? global.AppGenesisProcessKeysRegistryV1
      : null;

  const HOME_MENU_KEY_V1 = "home";
  const PERFIL_MENU_KEY_V1 = "perfil";
  const ADMINISTRATIVO_MENU_KEY_V1 = "administrativo";
  const MEU_PERFIL_MENU_KEY = processKeysRegistry
    ? processKeysRegistry.MEU_PERFIL_MENU_KEY
    : "meu_perfil";
  const ESTRUTURAS_MENU_KEY_V1 = processKeysRegistry
    ? processKeysRegistry.ESTRUTURAS_MENU_KEY_V1
    : "sessoes";
  const EMPRESA_MENU_KEY_V1 = processKeysRegistry
    ? processKeysRegistry.EMPRESA_MENU_KEY_V1
    : "empresa";
  const PERFIL_AUTORIZACAO_MENU_KEY_V1 = "perfil_de_autorizacao";
  const ENTIDADE_SUBPROCESS_KEY_V1 = "entidade";
  const UTILIZADOR_SUBPROCESS_KEY_V1 = "utilizador";
  const MENU_SUBPROCESS_KEY_V1 = "menu";
  const OBJETO_AUTORIZACAO_SUBPROCESS_KEY_V1 = "objeto_de_autorizacao";

  global.AppGenesisProcessReferenceRegistryV1 = Object.freeze({
    HOME_MENU_KEY_V1,
    PERFIL_MENU_KEY_V1,
    ADMINISTRATIVO_MENU_KEY_V1,
    MEU_PERFIL_MENU_KEY,
    ESTRUTURAS_MENU_KEY_V1,
    EMPRESA_MENU_KEY_V1,
    PERFIL_AUTORIZACAO_MENU_KEY_V1,
    ENTIDADE_SUBPROCESS_KEY_V1,
    UTILIZADOR_SUBPROCESS_KEY_V1,
    MENU_SUBPROCESS_KEY_V1,
    OBJETO_AUTORIZACAO_SUBPROCESS_KEY_V1
  });
})(window);
