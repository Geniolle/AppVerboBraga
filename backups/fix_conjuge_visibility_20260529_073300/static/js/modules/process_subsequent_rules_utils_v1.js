// APPVERBO_PROCESS_SUBSEQUENT_RULES_UTILS_V1_MODULE_START
(function registerProcessSubsequentRulesUtilsV1Module() {
  "use strict";

  window.APPVERBO_CREATE_PROCESS_SUBSEQUENT_RULES_UTILS_API_V1 =
    function createProcessSubsequentRulesUtilsApiV1(options) {
      const deps = options && typeof options === "object" ? options : {};
      const normalizeMenuKey =
        typeof deps.normalizeMenuKey === "function"
          ? deps.normalizeMenuKey
          : function normalizeMenuKeyFallback(value) {
              return String(value || "").trim().toLowerCase();
            };
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
      const processSubsequentOperators = new Set(["equals", "not_equals", "is_empty", "is_not_empty"]);

      //###################################################################################
      // (1) NORMALIZACAO DE REGRAS SUBSEQUENTES
      //###################################################################################
      function normalizeProcessSubsequentOperator(value) {
        const cleanOperator = String(value || "equals").trim().toLowerCase();
        return processSubsequentOperators.has(cleanOperator) ? cleanOperator : "equals";
      }

      function normalizeProcessSubsequentRules(rawRules) {
        if (!Array.isArray(rawRules)) {
          return [];
        }
        return rawRules
          .map((rawRule) => {
            if (!rawRule || typeof rawRule !== "object") {
              return null;
            }
            const triggerField = normalizeMenuKey(rawRule.trigger_field);
            const targetField = normalizeMenuKey(rawRule.field_key || rawRule.subsequent_field);
            if (!triggerField || !targetField) {
              return null;
            }
            const operator = normalizeProcessSubsequentOperator(rawRule.operator || rawRule.condition);
            return {
              key: normalizeMenuKey(rawRule.key),
              triggerField,
              targetField,
              operator,
              triggerValue: operator === "is_empty" || operator === "is_not_empty"
                ? ""
                : String(rawRule.trigger_value || "").trim()
            };
          })
          .filter(Boolean);
      }

      //###################################################################################
      // (2) AVALIACAO E VISIBILIDADE
      //###################################################################################
      function isProcessSubsequentRuleSatisfied(rule, valuesByField = {}) {
        const currentValue = String(valuesByField[rule.triggerField] || "").trim();
        const normalizedCurrentValue = normalizeLookupText(currentValue);
        const normalizedRuleValue = normalizeLookupText(rule.triggerValue);
        switch (normalizeProcessSubsequentOperator(rule.operator)) {
          case "is_empty":
            return currentValue === "";
          case "is_not_empty":
            return currentValue !== "";
          case "not_equals":
            return normalizedCurrentValue !== normalizedRuleValue;
          default:
            return normalizedCurrentValue === normalizedRuleValue;
        }
      }

      function getHiddenProcessTargets(rules, valuesByField = {}) {
        const groupedRules = new Map();
        normalizeProcessSubsequentRules(rules).forEach((rule) => {
          if (!groupedRules.has(rule.targetField)) {
            groupedRules.set(rule.targetField, []);
          }
          groupedRules.get(rule.targetField).push(rule);
        });
        const hiddenTargets = new Set();
        groupedRules.forEach((targetRules, targetField) => {
          //###################################################################################
          //(SUBSEQUENT_RULES) OR POR MESMO triggerField+operator, AND ENTRE GRUPOS
          //###################################################################################
          const groupedByCondition = new Map();
          targetRules.forEach((rule) => {
            const conditionKey = `${normalizeMenuKey(rule.triggerField)}::${normalizeProcessSubsequentOperator(rule.operator)}`;
            if (!groupedByCondition.has(conditionKey)) {
              groupedByCondition.set(conditionKey, []);
            }
            groupedByCondition.get(conditionKey).push(rule);
          });

          let isTargetVisible = true;
          groupedByCondition.forEach((conditionRules) => {
            if (!isTargetVisible) {
              return;
            }

            const operator = normalizeProcessSubsequentOperator(
              conditionRules[0] && conditionRules[0].operator
            );

            const conditionMet =
              (operator === "equals" || operator === "not_equals") && conditionRules.length > 1
                ? conditionRules.some((rule) => isProcessSubsequentRuleSatisfied(rule, valuesByField))
                : conditionRules.every((rule) => isProcessSubsequentRuleSatisfied(rule, valuesByField));

            if (!conditionMet) {
              isTargetVisible = false;
            }
          });

          if (!isTargetVisible) {
            hiddenTargets.add(targetField);
          }
        });
        return hiddenTargets;
      }

      return {
        normalizeProcessSubsequentOperator,
        normalizeProcessSubsequentRules,
        isProcessSubsequentRuleSatisfied,
        getHiddenProcessTargets
      };
    };
})();
// APPVERBO_PROCESS_SUBSEQUENT_RULES_UTILS_V1_MODULE_END
