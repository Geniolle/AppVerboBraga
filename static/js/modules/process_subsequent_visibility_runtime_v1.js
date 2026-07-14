//###################################################################################
// RUNTIME CANONICO PARA CAMPOS SUBSEQUENTES
//###################################################################################

(function () {
  "use strict";

  const profileRegistryV1 =
    window.AppGenesisProfileFieldRegistryV1 &&
    typeof window.AppGenesisProfileFieldRegistryV1 === "object"
      ? window.AppGenesisProfileFieldRegistryV1
      : null;

  const ALLOWED_OPERATORS = new Set(["equals", "not_equals", "is_empty", "is_not_empty"]);

  function toSafeString(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeKey(value) {
    return toSafeString(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function normalizeLookupText(value) {
    return toSafeString(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function normalizeOperator(value) {
    const cleanOperator = normalizeKey(value || "equals");
    return ALLOWED_OPERATORS.has(cleanOperator) ? cleanOperator : "equals";
  }

  function normalizeComparableValue(value) {
    return normalizeLookupText(value);
  }

  function isEmptyValue(value) {
    if (value === null || value === undefined) {
      return true;
    }
    if (Array.isArray(value)) {
      return value.length === 0;
    }
    if (typeof value === "boolean") {
      return false;
    }
    return normalizeComparableValue(value) === "";
  }

  function normalizeRules(rawRules) {
    if (!Array.isArray(rawRules)) {
      return [];
    }

    return rawRules
      .map((rawRule, index) => {
        if (!rawRule || typeof rawRule !== "object") {
          return null;
        }

        const triggerField = normalizeKey(rawRule.trigger_field || rawRule.triggerField);
        const targetField = normalizeKey(
          rawRule.target_field ||
          rawRule.targetField ||
          rawRule.field_key ||
          rawRule.fieldKey ||
          rawRule.subsequent_field ||
          rawRule.subsequentField
        );
        if (!triggerField || !targetField) {
          return null;
        }

        const operator = normalizeOperator(rawRule.operator || rawRule.condition);
        const triggerValue = operator === "is_empty" || operator === "is_not_empty"
          ? ""
          : toSafeString(rawRule.trigger_value || rawRule.triggerValue).trim();

        return {
          key: normalizeKey(rawRule.key) || `subseq_${index + 1}`,
          triggerField,
          targetField,
          operator,
          triggerValue
        };
      })
      .filter(Boolean);
  }

  function evaluateRule(rule, valuesByField) {
    if (!rule || typeof rule !== "object") {
      return false;
    }

    const value = toSafeString(valuesByField && valuesByField[normalizeKey(rule.triggerField)]).trim();
    const expected = toSafeString(rule.triggerValue).trim();
    const normalizedValue = normalizeComparableValue(value);
    const normalizedExpected = normalizeComparableValue(expected);

    switch (normalizeOperator(rule.operator)) {
      case "not_equals":
        return normalizedValue !== normalizedExpected;
      case "is_empty":
        return isEmptyValue(value);
      case "is_not_empty":
        return !isEmptyValue(value);
      case "equals":
      default:
        return normalizedValue === normalizedExpected;
    }
  }

  function evaluateRules(rules, valuesByField) {
    return normalizeRules(rules).reduce((hiddenTargets, rule) => {
      if (!evaluateRule(rule, valuesByField)) {
        hiddenTargets.add(rule.targetField);
      }
      return hiddenTargets;
    }, new Set());
  }

  function getHiddenTargets(rules, valuesByField) {
    return evaluateRules(rules, valuesByField);
  }

  function getProfileForm(root) {
    const scope = root && typeof root.querySelector === "function" ? root : document;
    return (
      scope.querySelector('form[action="/users/profile/personal"]') ||
      scope.querySelector("#perfil-pessoal-card form") ||
      null
    );
  }

  function getCurrentProfileSection(root) {
    if (profileRegistryV1 && typeof profileRegistryV1.getCurrentProfileSection === "function") {
      return normalizeKey(profileRegistryV1.getCurrentProfileSection(root));
    }

    const scope = root && typeof root.querySelector === "function" ? root : document;
    const activeTab = scope.querySelector(
      "#perfil-pessoal-card [data-profile-section-button].active, " +
      "#perfil-pessoal-card .profile-section-tab.active, " +
      "#perfil-pessoal-card .active"
    );

    if (activeTab) {
      return normalizeKey(
        activeTab.dataset.profileSection ||
        activeTab.dataset.profileSectionKey ||
        activeTab.dataset.profileSectionTab ||
        activeTab.dataset.sectionKey ||
        ""
      );
    }

    return "";
  }

  function resolveControlName(fieldKey) {
    if (profileRegistryV1 && typeof profileRegistryV1.resolveControlName === "function") {
      return profileRegistryV1.resolveControlName(fieldKey);
    }

    const cleanKey = normalizeKey(fieldKey);
    if (!cleanKey) {
      return "";
    }
    if (cleanKey.startsWith("custom_")) {
      return "custom_field__" + cleanKey;
    }

    const builtinNames = {
      nome: "full_name",
      telefone: "primary_phone",
      email: "login_email",
      pais: "country",
      data_nascimento: "birth_date",
      autorizacao_whatsapp: "whatsapp_notice_opt_in"
    };
    return builtinNames[cleanKey] || cleanKey;
  }

  function readControlValue(control, fieldType) {
    if (!control) {
      return "";
    }

    const safeType = normalizeKey(fieldType || control.type);
    if (safeType === "checkbox") {
      return control.checked ? "1" : "0";
    }
    if (safeType === "radio") {
      return control.checked ? toSafeString(control.value).trim() : "";
    }
    return toSafeString(control.value).trim();
  }

  function collectProfileValues(form) {
    if (profileRegistryV1 && typeof profileRegistryV1.collectProfileValues === "function") {
      return profileRegistryV1.collectProfileValues(form);
    }

    if (!form || typeof form.querySelectorAll !== "function") {
      return {};
    }

    const valuesByField = {};
    form.querySelectorAll("[name]").forEach((control) => {
      const fieldKey = normalizeKey(
        profileRegistryV1 && typeof profileRegistryV1.resolveFieldKeyFromControlName === "function"
          ? profileRegistryV1.resolveFieldKeyFromControlName(control.getAttribute("name"))
          : String(control.getAttribute("name") || "").replace(/^custom_field__/, "")
      );
      if (!fieldKey) {
        return;
      }
      valuesByField[fieldKey] = readControlValue(control, control.type);
    });
    return valuesByField;
  }

  function findProfileControl(form, fieldKey) {
    const scope = form && typeof form.querySelector === "function" ? form : document;
    const cleanKey = normalizeKey(fieldKey);

    if (
      profileRegistryV1 &&
      typeof profileRegistryV1.findProfileControl === "function"
    ) {
      const registryControl = profileRegistryV1.findProfileControl(scope, cleanKey);
      if (registryControl) {
        return registryControl;
      }
    }

    const controlName = resolveControlName(cleanKey);
    if (!controlName) {
      return null;
    }
    return scope.querySelector(`[name="${controlName}"]`) || null;
  }

  function getFieldWrappers(root, fieldKey) {
    const scope = root && typeof root.querySelectorAll === "function" ? root : document;
    const cleanKey = normalizeKey(fieldKey);
    const wrappers = [];

    scope.querySelectorAll("#perfil-pessoal-card [data-profile-field-key]").forEach((element) => {
      const wrapper = element.matches("[data-profile-field-key]") ? element : element.closest("[data-profile-field-key]");
      if (wrapper && normalizeKey(wrapper.dataset.profileFieldKey) === cleanKey) {
        wrappers.push(wrapper);
      }
    });

    return wrappers;
  }

  function getSectionTabs(root, sectionKey) {
    const scope = root && typeof root.querySelectorAll === "function" ? root : document;
    const cleanKey = normalizeKey(sectionKey);
    const tabs = [];

    scope.querySelectorAll(
      "#perfil-pessoal-card [data-profile-section-tab], " +
      "#perfil-pessoal-card [data-profile-section-button], " +
      "#perfil-pessoal-card .profile-section-tab, " +
      "#perfil-pessoal-card button, " +
      "#perfil-pessoal-card a"
    ).forEach((tab) => {
      const dataKey = normalizeKey(
        tab.dataset.profileSection ||
        tab.dataset.profileSectionKey ||
        tab.dataset.profileSectionTab ||
        tab.dataset.sectionKey ||
        ""
      );
      if (dataKey && dataKey === cleanKey) {
        tabs.push(tab);
      }
    });

    return tabs;
  }

  function setWrapperHidden(wrapper, hidden) {
    if (!wrapper) {
      return;
    }

    if (hidden) {
      if (wrapper.dataset.subsequentRuntimeHidden !== "1") {
        wrapper.dataset.subsequentRuntimeHidden = "1";
      }
      wrapper.hidden = true;
      wrapper.style.display = "none";
      wrapper.querySelectorAll("input, select, textarea, button").forEach((control) => {
        if (control.dataset.subsequentRuntimeDisabled !== "1" && !control.disabled) {
          control.dataset.subsequentRuntimeDisabled = "1";
          control.disabled = true;
        }
      });
      return;
    }

    if (wrapper.dataset.subsequentRuntimeHidden !== "1") {
      return;
    }

    delete wrapper.dataset.subsequentRuntimeHidden;
    wrapper.hidden = false;
    wrapper.style.display = "";
    wrapper.querySelectorAll("input, select, textarea, button").forEach((control) => {
      if (control.dataset.subsequentRuntimeDisabled === "1") {
        delete control.dataset.subsequentRuntimeDisabled;
        control.disabled = false;
      }
    });
  }

  function applyProfileVisibility(context, hiddenTargets) {
    const root = context && context.root ? context.root : document;
    const hiddenSet = hiddenTargets instanceof Set ? hiddenTargets : new Set();

    hiddenSet.forEach((fieldKey) => {
      getFieldWrappers(root, fieldKey).forEach((wrapper) => setWrapperHidden(wrapper, true));
      getSectionTabs(root, fieldKey).forEach((tab) => {
        tab.hidden = true;
        tab.style.display = "none";
      });
    });

    root.querySelectorAll("#perfil-pessoal-card [data-profile-field-key]").forEach((element) => {
      const wrapper = element.matches("[data-profile-field-key]") ? element : element.closest("[data-profile-field-key]");
      if (!wrapper) {
        return;
      }
      const cleanKey = normalizeKey(wrapper.dataset.profileFieldKey);
      setWrapperHidden(wrapper, hiddenSet.has(cleanKey));
    });

    root.querySelectorAll("#perfil-pessoal-card [data-profile-section-tab], #perfil-pessoal-card [data-profile-section-button]").forEach((tab) => {
      const cleanKey = normalizeKey(
        tab.dataset.profileSection ||
        tab.dataset.profileSectionKey ||
        tab.dataset.profileSectionTab ||
        tab.dataset.sectionKey ||
        ""
      );
      tab.hidden = hiddenSet.has(cleanKey);
      tab.style.display = hiddenSet.has(cleanKey) ? "none" : "";
    });

    if (typeof window.activateProfilePersonalSection === "function") {
      const currentSection = getCurrentProfileSection(root);
      if (currentSection && hiddenSet.has(currentSection)) {
        const nextVisible = Array.from(root.querySelectorAll("#perfil-pessoal-card [data-profile-section-tab], #perfil-pessoal-card [data-profile-section-button]"))
          .map((tab) => normalizeKey(tab.dataset.profileSection || tab.dataset.profileSectionKey || tab.dataset.profileSectionTab || tab.dataset.sectionKey || ""))
          .find((sectionKey) => sectionKey && !hiddenSet.has(sectionKey));
        if (nextVisible) {
          window.activateProfilePersonalSection(nextVisible);
        }
      }
    }

    return hiddenSet;
  }

  function evaluate(context) {
    const safeContext = context && typeof context === "object" ? context : {};
    const rules = normalizeRules(safeContext.rules || (safeContext.setting && (safeContext.setting.process_subsequent_fields || safeContext.setting.process_subsequent_rules || safeContext.setting.process_subsequent)) || []);
    const valuesByField = typeof safeContext.getValues === "function"
      ? safeContext.getValues()
      : (safeContext.valuesByField || {});
    return {
      rules,
      valuesByField,
      hiddenTargets: evaluateRules(rules, valuesByField)
    };
  }

  function apply(context) {
    const safeContext = context && typeof context === "object" ? context : {};
    const evaluation = safeContext.evaluation || evaluate(safeContext);

    if (safeContext.mode === "profile") {
      applyProfileVisibility(safeContext, evaluation.hiddenTargets);
    }

    return evaluation;
  }

  function refresh(context) {
    return apply(context);
  }

  function initialize(context) {
    const safeContext = context && typeof context === "object" ? context : {};
    const formEl = safeContext.formEl || getProfileForm(safeContext.root);

    if (formEl && formEl.dataset.processSubsequentVisibilityBoundV1 !== "1") {
      formEl.dataset.processSubsequentVisibilityBoundV1 = "1";
      ["input", "change"].forEach((eventName) => {
        formEl.addEventListener(eventName, () => {
          refresh(safeContext);
        });
      });
    }

    return safeContext;
  }

  function destroy(context) {
    return context || null;
  }

  window.AppGenesisProcessSubsequentVisibilityRuntimeV1 = {
    initialize,
    evaluate,
    apply,
    refresh,
    destroy,
    normalizeRules,
    normalizeOperator,
    normalizeComparableValue,
    evaluateRule,
    evaluateRules,
    getHiddenTargets,
    isEmptyValue,
    collectProfileValues,
    getProfileForm,
    getCurrentProfileSection,
    resolveControlName,
    readControlValue,
    findProfileControl
  };
})();
