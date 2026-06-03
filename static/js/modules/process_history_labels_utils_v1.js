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

      function isSingleRecordProcessMenu(menuKey, menuLabel, sectionLabel) {
        const normalizedMenuKey = normalizeLookupText(menuKey).replace(/\s+/g, "_");
        const joined = buildNormalizedJoinedText(menuKey, menuLabel, sectionLabel);
        if (!normalizedMenuKey && !joined) {
          return false;
        }
        return (
          normalizedMenuKey === "empresa" ||
          normalizedMenuKey === "meu_perfil" ||
          normalizedMenuKey === "perfil" ||
          joined.includes("meu perfil") ||
          joined.includes("perfil pessoal")
        );
      }

      function pluralizeHistoryLabel(label) {
        const normalizedLabel = normalizeLookupText(label);
        if (!normalizedLabel) {
          return "registos";
        }
        if (normalizedLabel.endsWith("s")) {
          return normalizedLabel;
        }
        if (normalizedLabel.endsWith("ao")) {
          return `${normalizedLabel.slice(0, -2)}oes`;
        }
        if (normalizedLabel.endsWith("al")) {
          return `${normalizedLabel.slice(0, -2)}ais`;
        }
        if (normalizedLabel.endsWith("el")) {
          return `${normalizedLabel.slice(0, -2)}eis`;
        }
        if (normalizedLabel.endsWith("il")) {
          return `${normalizedLabel.slice(0, -2)}is`;
        }
        if (normalizedLabel.endsWith("ol")) {
          return `${normalizedLabel.slice(0, -2)}ois`;
        }
        if (normalizedLabel.endsWith("ul")) {
          return `${normalizedLabel.slice(0, -2)}uis`;
        }
        return `${normalizedLabel}s`;
      }

      function isHistoryProcessMenu(menuKey, menuLabel, sectionLabel) {
        const joined = buildNormalizedJoinedText(menuKey, menuLabel, sectionLabel);
        if (!joined) {
          return false;
        }
        if (isSingleRecordProcessMenu(menuKey, menuLabel, sectionLabel)) {
          return false;
        }
        return true;
      }

      function getHistoryRecordLabels(menuKey, menuLabel, sectionLabel) {
        const normalizedMenuLabel = normalizeLookupText(menuLabel);
        const normalizedSectionLabel = normalizeLookupText(sectionLabel);
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
        const genericSingularLabel = normalizedMenuLabel || normalizedSectionLabel || "registo";
        return {
          singular: genericSingularLabel,
          plural: pluralizeHistoryLabel(genericSingularLabel)
        };
      }

      return {
        isAbsenceProcessMenu,
        isHistoryProcessMenu,
        getHistoryRecordLabels
      };
    };
})();
// APPVERBO_PROCESS_HISTORY_LABELS_UTILS_V1_MODULE_END
