// APPVERBO_PROCESS_ABSENCE_DATE_VALIDATION_V1_MODULE_START
(function registerProcessAbsenceDateValidationV1Module() {
  "use strict";

  window.APPVERBO_CREATE_PROCESS_ABSENCE_DATE_VALIDATION_API_V1 =
    function createProcessAbsenceDateValidationApiV1(options) {
      const deps = options && typeof options === "object" ? options : {};
      const normalizeProcessFieldType =
        typeof deps.normalizeProcessFieldType === "function"
          ? deps.normalizeProcessFieldType
          : function normalizeProcessFieldTypeFallback(value) {
              return String(value || "text").trim().toLowerCase();
            };
      const normalizeMenuKey =
        typeof deps.normalizeMenuKey === "function"
          ? deps.normalizeMenuKey
          : function normalizeMenuKeyFallback(value) {
              return String(value || "").trim().toLowerCase();
            };
      const isStartDateField =
        typeof deps.isStartDateField === "function"
          ? deps.isStartDateField
          : function isStartDateFieldFallback() {
              return false;
            };
      const isEndDateField =
        typeof deps.isEndDateField === "function"
          ? deps.isEndDateField
          : function isEndDateFieldFallback() {
              return false;
            };
      const normalizeDateInputValue =
        typeof deps.normalizeDateInputValue === "function"
          ? deps.normalizeDateInputValue
          : function normalizeDateInputValueFallback(rawValue) {
              return String(rawValue || "").trim();
            };

      //###################################################################################
      // (1) VALIDACAO DE INTERVALO DE DATAS (ASSIDUIDADE/AUSENCIA)
      //###################################################################################
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
            endDateInputEl.setCustomValidity("Data fim nao pode ser menor que a data inicio.");
          } else {
            endDateInputEl.setCustomValidity("");
          }
        };

        startDateInputEl.addEventListener("input", syncDateRangeRule);
        endDateInputEl.addEventListener("input", syncDateRangeRule);
        syncDateRangeRule();
      }

      return {
        setupAbsenceDateRangeValidation
      };
    };
})();
// APPVERBO_PROCESS_ABSENCE_DATE_VALIDATION_V1_MODULE_END
