// APPVERBO_PROCESS_HISTORY_LABELS_UTILS_V1_MODULE_START
(function registerProcessHistoryLabelsUtilsV1Module() {
  "use strict";

  window.APPVERBO_CREATE_PROCESS_HISTORY_LABELS_UTILS_API_V1 =
    function createProcessHistoryLabelsUtilsApiV1(options) {
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

      function buildNormalizedJoinedText(menuKey, menuLabel, sectionLabel) {
        return [
          normalizeLookupText(menuKey),
          normalizeLookupText(menuLabel),
          normalizeLookupText(sectionLabel)
        ]
          .filter(Boolean)
          .join(" ");
      }

      //###################################################################################
      // (1) CLASSIFICACAO DE CONTEXTO DE HISTORICO
      //###################################################################################
      function isAbsenceProcessMenu(menuKey, menuLabel, sectionLabel) {
        const joined = buildNormalizedJoinedText(menuKey, menuLabel, sectionLabel);
        if (!joined) {
          return false;
        }
        return joined.includes("assiduidade") || joined.includes("ausencia");
      }

      function isHistoryProcessMenu(menuKey, menuLabel, sectionLabel) {
        const joined = buildNormalizedJoinedText(menuKey, menuLabel, sectionLabel);
        if (!joined) {
          return false;
        }
        return (
          isAbsenceProcessMenu(menuKey, menuLabel, sectionLabel) ||
          joined.includes("departamento") ||
          joined.includes("musica")
        );
      }

      function getHistoryRecordLabels(menuKey, menuLabel, sectionLabel) {
        const joined = buildNormalizedJoinedText(menuKey, menuLabel, sectionLabel);
        if (isAbsenceProcessMenu(menuKey, menuLabel, sectionLabel)) {
          return { singular: "ausencia", plural: "ausencias" };
        }
        if (joined.includes("departamento")) {
          return { singular: "departamento", plural: "departamentos" };
        }
        if (joined.includes("musica")) {
          return { singular: "musica", plural: "musicas" };
        }
        return { singular: "registo", plural: "registos" };
      }

      return {
        isAbsenceProcessMenu,
        isHistoryProcessMenu,
        getHistoryRecordLabels
      };
    };
})();
// APPVERBO_PROCESS_HISTORY_LABELS_UTILS_V1_MODULE_END
