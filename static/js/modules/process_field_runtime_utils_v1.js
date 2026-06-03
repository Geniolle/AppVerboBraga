// APPVERBO_PROCESS_FIELD_RUNTIME_UTILS_V1_MODULE_START
(function registerProcessFieldRuntimeUtilsV1Module() {
  "use strict";

  window.APPVERBO_CREATE_PROCESS_FIELD_RUNTIME_UTILS_API_V1 =
    function createProcessFieldRuntimeUtilsApiV1(options) {
      const deps = options && typeof options === "object" ? options : {};
      const normalizeLookupText =
        typeof deps.normalizeLookupText === "function"
          ? deps.normalizeLookupText
          : function normalizeLookupTextFallback(value) {
              return String(value || "")
                .trim()
                .toLowerCase()
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "");
            };

      //###################################################################################
      // (1) CAMPOS E TIPOS
      //###################################################################################
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
        if (fieldType === "link") {
          return "url";
        }
        if (fieldType === "date") {
          return "date";
        }
        if (fieldType === "time") {
          return "time";
        }
        return "text";
      }

      //###################################################################################
      // (2) DATAS DE PROCESSO
      //###################################################################################
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

      return {
        isTruthyFlagValue,
        getDynamicProcessInputType,
        normalizeDateInputValue,
        isStartDateField,
        isEndDateField
      };
    };
})();
// APPVERBO_PROCESS_FIELD_RUNTIME_UTILS_V1_MODULE_END
