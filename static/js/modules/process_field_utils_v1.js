// APPVERBO_PROCESS_FIELD_UTILS_V1_MODULE_START
(function registerProcessFieldUtilsV1Module() {
  "use strict";

  window.APPVERBO_CREATE_PROCESS_FIELD_UTILS_API_V1 = function createProcessFieldUtilsApiV1(options) {
    const deps = options && typeof options === "object" ? options : {};
    const legacyDocumentosMenuKey = String(deps.legacyDocumentosMenuKey || "documentos").trim().toLowerCase();
    const meuPerfilMenuKey = String(deps.meuPerfilMenuKey || "meu_perfil").trim().toLowerCase();
    const processTextualTypes = new Set(["text", "textarea", "number", "email", "phone", "link"]);
    const processSupportedTypes = new Set(["text", "textarea", "number", "email", "phone", "date", "time", "flag", "list", "link"]);

    //###################################################################################
    // (1) NORMALIZACAO BASE
    //###################################################################################
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
      if (cleanKey === legacyDocumentosMenuKey) {
        return meuPerfilMenuKey;
      }
      if (cleanKey === "configuracao") {
        return "administrativo";
      }
      return cleanKey;
    }

    function normalizeLookupText(value) {
      return String(value || "")
        .trim()
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
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

    //###################################################################################
    // (2) PROCESS FIELDS
    //###################################################################################
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
      const maxSize = fieldType === "textarea" ? 4000 : 255;
      const defaultSize = fieldType === "textarea" ? 4000 : 255;
      if (!Number.isFinite(parsedSize)) {
        return defaultSize;
      }
      return Math.min(maxSize, Math.max(1, parsedSize));
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

    return {
      normalizeSettingsTabKey,
      normalizeMenuKey,
      normalizeLookupText,
      toSentenceCaseText,
      normalizeProcessFieldType,
      normalizeProcessFieldSize,
      normalizeProcessFieldRequired,
      getProcessStorageKey
    };
  };
})();
// APPVERBO_PROCESS_FIELD_UTILS_V1_MODULE_END
