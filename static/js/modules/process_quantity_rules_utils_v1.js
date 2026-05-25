// APPVERBO_PROCESS_QUANTITY_RULES_UTILS_V1_MODULE_START
(function registerProcessQuantityRulesUtilsV1Module() {
  "use strict";

  window.APPVERBO_CREATE_PROCESS_QUANTITY_RULES_UTILS_API_V1 =
    function createProcessQuantityRulesUtilsApiV1(options) {
      const deps = options && typeof options === "object" ? options : {};
      const normalizeMenuKey =
        typeof deps.normalizeMenuKey === "function"
          ? deps.normalizeMenuKey
          : function normalizeMenuKeyFallback(value) {
              return String(value || "").trim().toLowerCase();
            };
      const toSentenceCaseText =
        typeof deps.toSentenceCaseText === "function"
          ? deps.toSentenceCaseText
          : function toSentenceCaseTextFallback(value) {
              return String(value || "").trim();
            };

      //###################################################################################
      // (1) MAPEAMENTO DE CAMPOS/SECOES
      //###################################################################################
      function getFieldSectionMap(setting) {
        const sectionMap = new Map();
        const rows = Array.isArray(setting && setting.process_visible_field_rows)
          ? setting.process_visible_field_rows
          : [];
        rows.forEach((row) => {
          const fieldKey = normalizeMenuKey(row && row.field_key);
          if (!fieldKey) {
            return;
          }
          sectionMap.set(fieldKey, normalizeMenuKey(row && row.header_key));
        });
        return sectionMap;
      }

      function getProcessQuantityStorageKey(menuKey, ruleKey) {
        const cleanMenuKey = normalizeMenuKey(menuKey);
        const cleanRuleKey = normalizeMenuKey(ruleKey);
        if (!cleanMenuKey || !cleanRuleKey) {
          return "";
        }
        return `quantity__${cleanMenuKey}__${cleanRuleKey}`;
      }

      //###################################################################################
      // (2) NORMALIZACAO DE REGRAS/ITENS DE QUANTIDADE
      //###################################################################################
      function normalizeProcessQuantityItems(rawItems) {
        if (!Array.isArray(rawItems)) {
          return [];
        }
        return rawItems
          .map((rawItem) => {
            if (!rawItem || typeof rawItem !== "object") {
              return null;
            }
            const normalizedItem = {};
            Object.keys(rawItem).forEach((rawKey) => {
              const cleanKey = normalizeMenuKey(rawKey);
              if (!cleanKey) {
                return;
              }
              normalizedItem[cleanKey] = String(rawItem[rawKey] || "").trim();
            });
            return normalizedItem;
          })
          .filter(Boolean);
      }

      function normalizeProcessQuantityRules(rawRules) {
        if (!Array.isArray(rawRules)) {
          return [];
        }
        return rawRules
          .map((rawRule, index) => {
            if (!rawRule || typeof rawRule !== "object") {
              return null;
            }
            const key = normalizeMenuKey(rawRule.key || rawRule.rule_key || rawRule.ruleKey)
              || `qty_regra_${index + 1}`;
            const label = toSentenceCaseText(rawRule.label || rawRule.rule_label || rawRule.name || "Regra");
            const quantityFieldKey = normalizeMenuKey(rawRule.quantity_field_key || rawRule.quantityFieldKey);
            const headerKey = normalizeMenuKey(rawRule.header_key || rawRule.headerKey);
            const itemLabel = toSentenceCaseText(rawRule.item_label || rawRule.itemLabel || "Item") || "Item";
            const maxItemsRaw = Number.parseInt(String(rawRule.max_items || rawRule.maxItems || "1").trim(), 10);
            const maxItems = Number.isFinite(maxItemsRaw) ? Math.min(Math.max(maxItemsRaw, 1), 50) : 1;
            const repeatedFieldKeys = Array.isArray(rawRule.repeated_field_keys || rawRule.repeatedFieldKeys)
              ? (rawRule.repeated_field_keys || rawRule.repeatedFieldKeys)
              : [];
            const cleanRepeatedFieldKeys = [];
            const seenRepeatedFieldKeys = new Set();
            repeatedFieldKeys.forEach((rawFieldKey) => {
              const cleanFieldKey = normalizeMenuKey(rawFieldKey);
              if (!cleanFieldKey || seenRepeatedFieldKeys.has(cleanFieldKey)) {
                return;
              }
              seenRepeatedFieldKeys.add(cleanFieldKey);
              cleanRepeatedFieldKeys.push(cleanFieldKey);
            });
            if (!quantityFieldKey || !cleanRepeatedFieldKeys.length) {
              return null;
            }
            return {
              key,
              label,
              quantityFieldKey,
              repeatedFieldKeys: cleanRepeatedFieldKeys,
              headerKey,
              maxItems,
              itemLabel
            };
          })
          .filter(Boolean);
      }

      function getProcessQuantityRepeatedFieldKeys(setting) {
        const repeatedFieldKeys = new Set();
        normalizeProcessQuantityRules(setting && setting.process_quantity_fields).forEach((rule) => {
          rule.repeatedFieldKeys.forEach((fieldKey) => {
            repeatedFieldKeys.add(fieldKey);
          });
        });
        return repeatedFieldKeys;
      }

      return {
        getFieldSectionMap,
        getProcessQuantityStorageKey,
        normalizeProcessQuantityItems,
        normalizeProcessQuantityRules,
        getProcessQuantityRepeatedFieldKeys
      };
    };
})();
// APPVERBO_PROCESS_QUANTITY_RULES_UTILS_V1_MODULE_END
