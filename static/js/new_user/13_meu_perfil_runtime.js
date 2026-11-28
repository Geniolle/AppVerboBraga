// new_user/13_meu_perfil_runtime.js: Meu Perfil: renderizadores de quantidade, filtro de secoes e processo atual apos guardar.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

// APPGENESIS_MEU_PERFIL_QUANTITY_RENDERER_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_RENDERER_V1) CAMPOS QUANTIDADE NO FORMULARIO MEU PERFIL
//###################################################################################

(function setupMeuPerfilQuantityRendererV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function toSafeStringMeuPerfilQuantityV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function getMeuPerfilSettingQuantityV1() {
    if (typeof getSidebarMenuSetting === "function") {
      const foundSetting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
      if (foundSetting) {
        return foundSetting;
      }
    }

    return (Array.isArray(sidebarMenuSettings) ? sidebarMenuSettings : []).find((setting) => {
      return normalizeMenuKey(setting && setting.key) === MEU_PERFIL_MENU_KEY;
    }) || null;
  }

  function getFormControlByNameQuantityV1(form, name) {
    const cleanName = toSafeStringMeuPerfilQuantityV1(name);
    if (!form || !cleanName) {
      return null;
    }

    return Array.from(form.elements || []).find((element) => {
      return toSafeStringMeuPerfilQuantityV1(element.name) === cleanName;
    }) || null;
  }

  function getMeuPerfilQuantityFormV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function getMeuPerfilQuantityValuesV1(ruleKey) {
    const cleanRuleKey = normalizeMenuKey(ruleKey);
    const valuesByMenu = (
      menuProcessQuantityValuesMap &&
      typeof menuProcessQuantityValuesMap === "object" &&
      !Array.isArray(menuProcessQuantityValuesMap)
    )
      ? menuProcessQuantityValuesMap[MEU_PERFIL_MENU_KEY]
      : null;

    if (!valuesByMenu || typeof valuesByMenu !== "object" || Array.isArray(valuesByMenu)) {
      return [];
    }

    return normalizeProcessQuantityItems(valuesByMenu[cleanRuleKey]);
  }

  function buildListOptionsMapQuantityV1(setting) {
    const optionsMap = new Map();

    (Array.isArray(setting && setting.process_lists) ? setting.process_lists : []).forEach((processList) => {
      const listKey = normalizeMenuKey(processList && processList.key);
      if (!listKey) {
        return;
      }

      optionsMap.set(
        listKey,
        Array.isArray(processList.items)
          ? processList.items.map((item) => toSafeStringMeuPerfilQuantityV1(item).trim()).filter(Boolean)
          : []
      );
    });

    return optionsMap;
  }

  function buildFieldMetaMapQuantityV1(setting) {
    const listOptionsByKey = buildListOptionsMapQuantityV1(setting);
    const fieldMetaMap = new Map();

    (Array.isArray(setting && setting.process_field_options) ? setting.process_field_options : []).forEach((option) => {
      const fieldKey = normalizeMenuKey(option && option.key);
      if (!fieldKey) {
        return;
      }

      const fieldType = normalizeProcessFieldType(option.field_type);
      const listKey = normalizeMenuKey(option.list_key || option.listKey);
      const resolvedListOptions = Array.isArray(option.list_options)
        ? option.list_options.map((item) => toSafeStringMeuPerfilQuantityV1(item).trim()).filter(Boolean)
        : [];

      fieldMetaMap.set(fieldKey, {
        key: fieldKey,
        label: toSentenceCaseText(option.label || fieldKey),
        fieldType,
        size: normalizeProcessFieldSize(option.size, fieldType),
        isRequired: normalizeProcessFieldRequired(
          Object.prototype.hasOwnProperty.call(option, "is_required")
            ? option.is_required
            : option.required
        ),
        listKey,
        listOptions: resolvedListOptions.length
          ? resolvedListOptions
          : listOptionsByKey.get(listKey) || []
      });
    });

    return fieldMetaMap;
  }

  function resolveQuantityControlNameV1(fieldKey) {
    const cleanFieldKey = normalizeMenuKey(fieldKey);
    if (!cleanFieldKey) {
      return "";
    }

    if (cleanFieldKey.startsWith("custom_")) {
      return "custom_field__" + cleanFieldKey;
    }

    const builtinNames = {
      nome: "full_name",
      telefone: "primary_phone",
      email: "login_email",
      pais: "country",
      data_nascimento: "birth_date",
      autorizacao_whatsapp: "whatsapp_notice_opt_in"
    };

    return builtinNames[cleanFieldKey] || cleanFieldKey;
  }

  function parseQuantityCountV1(rawValue, maxItems) {
    const parsedValue = Number.parseInt(toSafeStringMeuPerfilQuantityV1(rawValue).trim(), 10);
    const parsedMaxItems = Number.parseInt(toSafeStringMeuPerfilQuantityV1(maxItems || "1").trim(), 10);
    const safeMaxItems = Number.isFinite(parsedMaxItems) ? Math.min(Math.max(parsedMaxItems, 1), 50) : 1;

    if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
      return 0;
    }

    return Math.min(parsedValue, safeMaxItems);
  }

  function readQuantityControlValueV1(control, fieldType) {
    if (!control) {
      return "";
    }

    if (fieldType === "flag") {
      return control.checked ? "1" : "0";
    }

    return toSafeStringMeuPerfilQuantityV1(control.value).trim();
  }

  function createQuantityFieldControlV1(rule, itemIndex, fieldMeta, existingValue) {
    const fieldType = normalizeProcessFieldType(fieldMeta.fieldType);
    const fieldName = "process_quantity_field__" + rule.key + "__" + itemIndex + "__" + fieldMeta.key;
    let control = null;

    if (fieldType === "list") {
      control = document.createElement("select");
      const emptyOption = document.createElement("option");
      emptyOption.value = "";
      emptyOption.textContent = "Selecione";
      control.appendChild(emptyOption);

      (Array.isArray(fieldMeta.listOptions) ? fieldMeta.listOptions : []).forEach((optionValue) => {
        const option = document.createElement("option");
        option.value = optionValue;
        option.textContent = optionValue;
        if (toSafeStringMeuPerfilQuantityV1(existingValue) === toSafeStringMeuPerfilQuantityV1(optionValue)) {
          option.selected = true;
          option.defaultSelected = true;
        }
        control.appendChild(option);
      });
    } else {
      control = document.createElement("input");
      if (fieldType === "flag") {
        control.type = "checkbox";
        control.value = "1";
        control.checked = ["1", "true", "sim", "yes", "on"].includes(
          toSafeStringMeuPerfilQuantityV1(existingValue).trim().toLowerCase()
        );
        control.defaultChecked = control.checked;
      } else {
        control.type = getDynamicProcessInputType(fieldType);
      }

      if (fieldType !== "flag") {
        control.value = toSafeStringMeuPerfilQuantityV1(existingValue);
        // defaultValue: o Cancelar faz form.reset(), que repoe o valor guardado em vez de limpar.
        control.defaultValue = control.value;
      }
    }

    control.name = fieldName;
    control.dataset.processQuantityRuleKey = rule.key;
    control.dataset.processQuantityItemIndex = String(itemIndex);
    control.dataset.processQuantityFieldKey = fieldMeta.key;

    if (fieldMeta.isRequired && fieldType !== "flag") {
      control.required = true;
    }

    if (fieldMeta.size && ["text", "email", "phone"].includes(fieldType)) {
      control.maxLength = fieldMeta.size;
    }

    // Data: ano com 4 digitos (o browser aceita anos com mais digitos sem limite).
    if (fieldType === "date") {
      control.min = "1900-01-01";
      control.max = "9999-12-31";
      control.dataset.lastValidDate = control.value || "";
      control.addEventListener("input", () => {
        const yearMatch = /^(\d+)-/.exec(control.value || "");
        if (yearMatch && Number(yearMatch[1]) > 9999) {
          control.value = control.dataset.lastValidDate || "";
          return;
        }
        control.dataset.lastValidDate = control.value || "";
      });
    }

    return control;
  }

  function syncQuantityPayloadV1(rule, host) {
    const rows = Array.from(host.querySelectorAll("[data-process-quantity-item-index]"));
    const payload = [];

    rows.forEach((row) => {
      const item = {};

      Array.from(row.querySelectorAll("[data-process-quantity-field-key]")).forEach((control) => {
        const fieldKey = normalizeMenuKey(control.dataset.processQuantityFieldKey);
        if (!fieldKey) {
          return;
        }

        const fieldType = normalizeProcessFieldType(control.dataset.processQuantityFieldType || control.type);
        const value = readQuantityControlValueV1(control, fieldType);

        if (value) {
          item[fieldKey] = value;
        }
      });

      payload.push(item);
    });

    const payloadInput = host.querySelector("input[name='process_quantity_payload__" + rule.key + "']");
    if (payloadInput) {
      payloadInput.value = JSON.stringify(payload);
    }
  }

  //###################################################################################
  // (2) RENDERIZAR UMA REGRA
  //###################################################################################

  function setupMeuPerfilQuantityRuleV1(form, setting, rule, fieldMetaMap) {
    const quantityControlName = resolveQuantityControlNameV1(rule.quantityFieldKey);
    const quantityControl = getFormControlByNameQuantityV1(form, quantityControlName);

    if (!quantityControl) {
      return;
    }

    const quantityFieldWrapper = quantityControl.closest(".field") || quantityControl.parentElement;
    const personalGrid = quantityControl.closest(".personal-grid") || form.querySelector(".personal-grid") || form;
    const sectionPane = rule.headerKey
      || toSafeStringMeuPerfilQuantityV1(quantityFieldWrapper && quantityFieldWrapper.dataset.profileSectionPane)
      || "";

    let host = form.querySelector("[data-profile-quantity-rule-key='" + rule.key + "']");

    if (!host) {
      host = document.createElement("div");
      host.className = "field full profile-quantity-rule-v1";
      host.dataset.profileQuantityRuleKey = rule.key;
      host.dataset.profileSectionPane = sectionPane;

      if (quantityFieldWrapper && quantityFieldWrapper.parentElement) {
        quantityFieldWrapper.insertAdjacentElement("afterend", host);
      } else {
        personalGrid.appendChild(host);
      }
    }
    // Grupo repetido no fim da aba (depois dos campos fixos, ordem 190/200).
    host.style.order = "300";

    let payloadInput = host.querySelector("input[name='process_quantity_payload__" + rule.key + "']");

    if (!payloadInput) {
      payloadInput = document.createElement("input");
      payloadInput.type = "hidden";
      payloadInput.name = "process_quantity_payload__" + rule.key;
      payloadInput.value = "[]";
      host.appendChild(payloadInput);
    }

    function renderQuantityBlocksV1() {
      const existingItems = getMeuPerfilQuantityValuesV1(rule.key);
      const requestedCount = parseQuantityCountV1(quantityControl.value, rule.maxItems);
      const fallbackCount = requestedCount || existingItems.length;
      const count = parseQuantityCountV1(String(fallbackCount), rule.maxItems);

      Array.from(host.querySelectorAll(".profile-quantity-items-wrap-v1")).forEach((element) => {
        element.remove();
      });

      if (!count) {
        payloadInput.value = "[]";
        return;
      }

      const wrapper = document.createElement("div");
      wrapper.className = "profile-quantity-items-wrap-v1";
      wrapper.dataset.processQuantityRuleKey = rule.key;

      for (let itemIndex = 0; itemIndex < count; itemIndex += 1) {
        const itemValues = existingItems[itemIndex] || {};
        const itemBlock = document.createElement("div");
        itemBlock.className = "profile-quantity-item-v1";
        itemBlock.dataset.processQuantityItemIndex = String(itemIndex);

        const itemTitle = document.createElement("h4");
        itemTitle.className = "profile-quantity-item-title-v1";
        itemTitle.textContent = (rule.itemLabel || "Item") + " " + (itemIndex + 1);
        itemBlock.appendChild(itemTitle);

        const fieldsGrid = document.createElement("div");
        fieldsGrid.className = "personal-grid profile-quantity-item-grid-v1";

        rule.repeatedFieldKeys.forEach((fieldKey) => {
          const fieldMeta = fieldMetaMap.get(fieldKey);

          if (!fieldMeta) {
            return;
          }

          const fieldWrapper = document.createElement("div");
          fieldWrapper.className = "field";
          fieldWrapper.dataset.profileSectionPane = sectionPane;
          fieldWrapper.dataset.profileFieldKey = fieldKey;

          const label = document.createElement("label");
          label.textContent = fieldMeta.label + (fieldMeta.isRequired ? " *" : "");

          const control = createQuantityFieldControlV1(
            rule,
            itemIndex,
            fieldMeta,
            itemValues[fieldKey] || ""
          );

          control.dataset.processQuantityFieldType = fieldMeta.fieldType;

          control.addEventListener("input", function () {
            syncQuantityPayloadV1(rule, host);
          });
          control.addEventListener("change", function () {
            syncQuantityPayloadV1(rule, host);
          });

          fieldWrapper.appendChild(label);
          fieldWrapper.appendChild(control);
          fieldsGrid.appendChild(fieldWrapper);
        });

        itemBlock.appendChild(fieldsGrid);
        wrapper.appendChild(itemBlock);
      }

      host.appendChild(wrapper);
      syncQuantityPayloadV1(rule, host);
    }

    quantityControl.addEventListener("input", renderQuantityBlocksV1);
    quantityControl.addEventListener("change", renderQuantityBlocksV1);

    if (!toSafeStringMeuPerfilQuantityV1(quantityControl.value).trim()) {
      const existingItems = getMeuPerfilQuantityValuesV1(rule.key);
      if (existingItems.length) {
        quantityControl.value = String(Math.min(existingItems.length, rule.maxItems || existingItems.length));
      }
    }

    renderQuantityBlocksV1();
  }

  //###################################################################################
  // (3) INICIALIZAR TODAS AS REGRAS
  //###################################################################################

  function setupMeuPerfilQuantityRulesV1() {
    const form = getMeuPerfilQuantityFormV1();
    const setting = getMeuPerfilSettingQuantityV1();

    if (!form || !setting || form.dataset.meuPerfilQuantityRendererBoundV1 === "1") {
      return;
    }

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    if (!rules.length) {
      return;
    }

    const fieldMetaMap = buildFieldMetaMapQuantityV1(setting);

    form.dataset.meuPerfilQuantityRendererBoundV1 = "1";
    // Remove o payload antigo criado antes deste renderizador assumir o formulario.
    syncMeuPerfilQuantityHiddenInputs({});

    rules.forEach((rule) => {
      setupMeuPerfilQuantityRuleV1(form, setting, rule, fieldMetaMap);
    });

    form.addEventListener("submit", function () {
      Array.from(form.querySelectorAll("[data-profile-quantity-rule-key]")).forEach((host) => {
        const ruleKey = normalizeMenuKey(host.dataset.profileQuantityRuleKey);
        const rule = rules.find((item) => item.key === ruleKey);
        if (rule) {
          syncQuantityPayloadV1(rule, host);
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupMeuPerfilQuantityRulesV1);
  } else {
    setupMeuPerfilQuantityRulesV1();
  }

  window.setTimeout(setupMeuPerfilQuantityRulesV1, 150);
  window.setTimeout(setupMeuPerfilQuantityRulesV1, 600);
})();

// APPGENESIS_MEU_PERFIL_QUANTITY_RENDERER_V1_END

// APPGENESIS_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1) VISUALIZACAO DOS CAMPOS QUANTIDADE
//###################################################################################

(function setupMeuPerfilQuantityReadonlyRendererV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeTextQuantityReadonlyV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function getMeuPerfilSettingQuantityReadonlyV1() {
    if (typeof getSidebarMenuSetting === "function") {
      const foundSetting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
      if (foundSetting) {
        return foundSetting;
      }
    }

    return (Array.isArray(sidebarMenuSettings) ? sidebarMenuSettings : []).find((setting) => {
      return normalizeMenuKey(setting && setting.key) === MEU_PERFIL_MENU_KEY;
    }) || null;
  }

  function getReadonlyGridQuantityReadonlyV1() {
    return document.querySelector("#perfil-pessoal-card .profile-readonly .personal-grid");
  }

  function getQuantityReadonlyValuesV1(ruleKey) {
    const cleanRuleKey = normalizeMenuKey(ruleKey);
    const valuesByMenu = (
      menuProcessQuantityValuesMap &&
      typeof menuProcessQuantityValuesMap === "object" &&
      !Array.isArray(menuProcessQuantityValuesMap)
    )
      ? menuProcessQuantityValuesMap[MEU_PERFIL_MENU_KEY]
      : null;

    if (!valuesByMenu || typeof valuesByMenu !== "object" || Array.isArray(valuesByMenu)) {
      return [];
    }

    return normalizeProcessQuantityItems(valuesByMenu[cleanRuleKey]);
  }

  function buildFieldMetaMapQuantityReadonlyV1(setting) {
    const metaMap = new Map();

    (Array.isArray(setting && setting.process_field_options) ? setting.process_field_options : []).forEach((option) => {
      const fieldKey = normalizeMenuKey(option && option.key);

      if (!fieldKey) {
        return;
      }

      metaMap.set(fieldKey, {
        key: fieldKey,
        label: toSentenceCaseText(option.label || fieldKey),
        fieldType: normalizeProcessFieldType(option.field_type)
      });
    });

    return metaMap;
  }

  function formatReadonlyValueQuantityReadonlyV1(value, fieldType) {
    const cleanValue = safeTextQuantityReadonlyV1(value).trim();

    if (!cleanValue) {
      return "-";
    }

    if (fieldType === "flag") {
      return ["1", "true", "sim", "yes", "on"].includes(cleanValue.toLowerCase())
        ? "Sim"
        : "Não";
    }

    return cleanValue;
  }

  function applyCurrentProfileSectionToQuantityReadonlyV1(host) {
    if (!host) {
      return;
    }

    const sectionInput = document.querySelector("[data-meu-perfil-section-input]");
    const currentSection = normalizeMenuKey(sectionInput ? sectionInput.value : "");
    const hostSection = normalizeMenuKey(host.dataset.profileSectionPane);

    if (!currentSection || !hostSection) {
      return;
    }

    host.style.display = currentSection === hostSection ? "" : "none";
  }

  function findInsertionPointQuantityReadonlyV1(grid, rule) {
    if (!grid || !rule) {
      return null;
    }

    const quantityFieldKey = normalizeMenuKey(rule.quantityFieldKey);

    if (!quantityFieldKey) {
      return null;
    }

    return grid.querySelector("[data-profile-field-key='" + quantityFieldKey + "']");
  }

  //###################################################################################
  // (2) RENDERIZAR REGRA READONLY
  //###################################################################################

  function renderReadonlyRuleQuantityReadonlyV1(grid, setting, rule, fieldMetaMap) {
    let values = getQuantityReadonlyValuesV1(rule.key);

    if (!Array.isArray(values) || !values.length) {
      // Sem itens gravados: mostra os itens previstos pela quantidade (igual ao modo de edicao).
      const originEl = document.querySelector(
        "#perfil-pessoal-card [data-profile-field-key='" + rule.quantityFieldKey + "'] .personal-value"
      );
      const originCount = parseInt(originEl ? originEl.textContent.trim() : "", 10);
      if (!Number.isInteger(originCount) || originCount < 1) {
        return;
      }
      values = Array.from({length: Math.min(originCount, 50)}, () => ({}));
    }

    // Evita duplicados: cada render substitui o bloco de leitura anterior da regra.
    grid.querySelectorAll("[data-profile-quantity-readonly-rule-key='" + rule.key + "']").forEach((oldEl) => oldEl.remove());

    const host = document.createElement("div");

    host.className = "personal-item profile-quantity-readonly-v1";
    host.style.gridColumn = "1 / -1";
    host.dataset.profileQuantityReadonlyRuleKey = rule.key;
    host.dataset.profileSectionPane = rule.headerKey || "";

    const mainLabel = document.createElement("span");
    mainLabel.className = "personal-label";
    mainLabel.textContent = rule.label || rule.itemLabel || "Itens";
    host.appendChild(mainLabel);

    const listWrapper = document.createElement("div");
    listWrapper.className = "profile-quantity-readonly-list-v1";

    values.forEach((itemValues, itemIndex) => {
      const itemBlock = document.createElement("div");
      itemBlock.className = "profile-quantity-readonly-item-v1";

      const itemTitle = document.createElement("strong");
      itemTitle.className = "personal-value profile-quantity-readonly-title-v1";
      itemTitle.textContent = (rule.itemLabel || "Item") + " " + (itemIndex + 1);
      itemBlock.appendChild(itemTitle);

      const fieldsList = document.createElement("div");
      fieldsList.className = "profile-quantity-readonly-fields-v1";

      rule.repeatedFieldKeys.forEach((fieldKey) => {
        const cleanFieldKey = normalizeMenuKey(fieldKey);
        const fieldMeta = fieldMetaMap.get(cleanFieldKey) || {
          label: cleanFieldKey,
          fieldType: "text"
        };

        const row = document.createElement("div");
        row.className = "profile-quantity-readonly-field-v1";

        const label = document.createElement("span");
        label.className = "personal-label";
        label.textContent = fieldMeta.label || cleanFieldKey;

        const value = document.createElement("strong");
        value.className = "personal-value";
        value.textContent = formatReadonlyValueQuantityReadonlyV1(
          itemValues ? itemValues[cleanFieldKey] : "",
          fieldMeta.fieldType
        );

        row.appendChild(label);
        row.appendChild(value);
        fieldsList.appendChild(row);
      });

      itemBlock.appendChild(fieldsList);
      listWrapper.appendChild(itemBlock);
    });

    host.appendChild(listWrapper);

    const insertionPoint = findInsertionPointQuantityReadonlyV1(grid, rule);

    if (insertionPoint && insertionPoint.parentElement === grid) {
      insertionPoint.insertAdjacentElement("afterend", host);
    } else {
      grid.appendChild(host);
    }

    applyCurrentProfileSectionToQuantityReadonlyV1(host);
  }

  //###################################################################################
  // (3) RENDERIZAR TODAS AS REGRAS
  //###################################################################################

  function renderMeuPerfilQuantityReadonlyV1() {
    const grid = getReadonlyGridQuantityReadonlyV1();
    const setting = getMeuPerfilSettingQuantityReadonlyV1();

    if (!grid || !setting) {
      return;
    }

    Array.from(grid.querySelectorAll("[data-profile-quantity-readonly-rule-key]")).forEach((element) => {
      element.remove();
    });

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    if (!rules.length) {
      return;
    }

    const fieldMetaMap = buildFieldMetaMapQuantityReadonlyV1(setting);

    rules.forEach((rule) => {
      renderReadonlyRuleQuantityReadonlyV1(grid, setting, rule, fieldMetaMap);
    });
  }

  //###################################################################################
  // (4) SINCRONIZAR COM AS ABAS DO MEU PERFIL
  //###################################################################################

  function refreshMeuPerfilQuantityReadonlyVisibilityV1() {
    document
      .querySelectorAll("[data-profile-quantity-readonly-rule-key]")
      .forEach(applyCurrentProfileSectionToQuantityReadonlyV1);
  }

  document.addEventListener("click", function () {
    window.setTimeout(refreshMeuPerfilQuantityReadonlyVisibilityV1, 0);
    window.setTimeout(refreshMeuPerfilQuantityReadonlyVisibilityV1, 80);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderMeuPerfilQuantityReadonlyV1);
  } else {
    renderMeuPerfilQuantityReadonlyV1();
  }

  window.setTimeout(renderMeuPerfilQuantityReadonlyV1, 150);
  window.setTimeout(renderMeuPerfilQuantityReadonlyV1, 600);
})();

// APPGENESIS_MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1_END

// APPGENESIS_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1) EVITAR DUPLICACAO DO CAMPO ORIGEM
//###################################################################################

(function setupMeuPerfilQuantityOriginDedupV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeQuantityOriginDedupTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function getMeuPerfilQuantityOriginSettingV1() {
    if (typeof getSidebarMenuSetting === "function") {
      const foundSetting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
      if (foundSetting) {
        return foundSetting;
      }
    }

    return (Array.isArray(sidebarMenuSettings) ? sidebarMenuSettings : []).find((setting) => {
      return normalizeMenuKey(setting && setting.key) === MEU_PERFIL_MENU_KEY;
    }) || null;
  }

  function getMeuPerfilQuantityOriginFormV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function resolveQuantityOriginControlNameV1(fieldKey) {
    const cleanFieldKey = normalizeMenuKey(fieldKey);

    if (!cleanFieldKey) {
      return "";
    }

    if (cleanFieldKey.startsWith("custom_")) {
      return "custom_field__" + cleanFieldKey;
    }

    const builtinNames = {
      nome: "full_name",
      telefone: "primary_phone",
      email: "login_email",
      pais: "country",
      data_nascimento: "birth_date",
      autorizacao_whatsapp: "whatsapp_notice_opt_in"
    };

    return builtinNames[cleanFieldKey] || cleanFieldKey;
  }

  function getQuantityOriginCurrentSectionV1() {
    const sectionInput = document.querySelector("[data-meu-perfil-section-input]");
    return normalizeMenuKey(sectionInput ? sectionInput.value : "");
  }

  // Cabecalho onde o campo origem esta configurado (ex.: Dados pessoais), nao o cabecalho da regra de quantidade.
  function getQuantityOriginOwnSectionV1(quantityFieldKey) {
    const setting = getMeuPerfilQuantityOriginSettingV1() || {};
    return normalizeMenuKey(getFieldSectionMap(setting).get(normalizeMenuKey(quantityFieldKey)) || "");
  }

  function getQuantityOriginWrapperV1(control) {
    if (!control) {
      return null;
    }

    return control.closest(".field")
      || control.closest("[data-profile-field-key]")
      || control.parentElement;
  }

  function getControlsByNameV1(form, controlName) {
    if (!form || !controlName) {
      return [];
    }

    return Array.from(form.elements || []).filter((control) => {
      return safeQuantityOriginDedupTextV1(control.name) === controlName;
    });
  }

  function disableDuplicateWrapperV1(wrapper, fieldKey) {
    if (!wrapper) {
      return;
    }

    wrapper.dataset.profileQuantityOriginDuplicateV1 = "1";
    wrapper.dataset.profileFieldKey = normalizeMenuKey(fieldKey);
    wrapper.hidden = true;
    wrapper.style.display = "none";

    Array.from(wrapper.querySelectorAll("input, select, textarea, button")).forEach((control) => {
      control.disabled = true;
      control.dataset.profileQuantityOriginDuplicateDisabledV1 = "1";
    });
  }

  function enableKeptWrapperV1(wrapper, rule) {
    if (!wrapper || !rule) {
      return;
    }

    wrapper.dataset.profileQuantityOriginKeepV1 = "1";
    wrapper.dataset.profileFieldKey = normalizeMenuKey(rule.quantityFieldKey);
    if (wrapper.dataset.profileSubsequentHiddenV1 === "1") {
      return;
    }
    // O campo origem (ex.: Quantos filhos?) mantem o cabecalho configurado; so os grupos repetidos vao para o cabecalho da regra.

    wrapper.hidden = false;

    Array.from(wrapper.querySelectorAll("input, select, textarea, button")).forEach((control) => {
      if (control.dataset.profileQuantityOriginDuplicateDisabledV1 === "1") {
        return;
      }

      control.disabled = false;
    });
  }

  function applyQuantityOriginVisibilityV1(wrapper, rule) {
    if (!wrapper || !rule) {
      return;
    }

    if (wrapper.dataset.profileSubsequentHiddenV1 === "1") {
      wrapper.style.display = "none";
      return;
    }

    const currentSection = getQuantityOriginCurrentSectionV1();
    const targetSection = getQuantityOriginOwnSectionV1(rule.quantityFieldKey)
      || normalizeMenuKey(rule.headerKey || wrapper.dataset.profileSectionPane || "");

    if (!currentSection || !targetSection) {
      wrapper.style.display = "";
      return;
    }

    wrapper.style.display = currentSection === targetSection ? "" : "none";
  }

  //###################################################################################
  // (2) DEDUP POR REGRA
  //###################################################################################

  function dedupQuantityOriginRuleV1(form, rule) {
    const quantityFieldKey = normalizeMenuKey(rule && rule.quantityFieldKey);
    const controlName = resolveQuantityOriginControlNameV1(quantityFieldKey);

    if (!quantityFieldKey || !controlName) {
      return;
    }

    const controls = getControlsByNameV1(form, controlName);

    if (!controls.length) {
      return;
    }

    const wrappers = [];
    const seenWrappers = new Set();

    controls.forEach((control) => {
      const wrapper = getQuantityOriginWrapperV1(control);

      if (!wrapper || seenWrappers.has(wrapper)) {
        return;
      }

      seenWrappers.add(wrapper);
      wrappers.push(wrapper);
    });

    if (!wrappers.length) {
      return;
    }

    const targetSection = getQuantityOriginOwnSectionV1(quantityFieldKey)
      || normalizeMenuKey(rule.headerKey);

    let keepWrapper = null;

    if (targetSection) {
      keepWrapper = wrappers.find((wrapper) => {
        return normalizeMenuKey(wrapper.dataset.profileSectionPane) === targetSection;
      }) || null;
    }

    if (!keepWrapper) {
      keepWrapper = wrappers[0];
    }

    enableKeptWrapperV1(keepWrapper, rule);

    wrappers.forEach((wrapper) => {
      if (wrapper === keepWrapper) {
        return;
      }

      disableDuplicateWrapperV1(wrapper, quantityFieldKey);
    });

    applyQuantityOriginVisibilityV1(keepWrapper, rule);
  }

  //###################################################################################
  // (3) DEDUP GLOBAL
  //###################################################################################

  function dedupMeuPerfilQuantityOriginsV1() {
    const form = getMeuPerfilQuantityOriginFormV1();
    const setting = getMeuPerfilQuantityOriginSettingV1();

    if (!form || !setting) {
      return;
    }

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    if (!rules.length) {
      return;
    }

    rules.forEach((rule) => {
      dedupQuantityOriginRuleV1(form, rule);
    });
  }

  function scheduleDedupMeuPerfilQuantityOriginsV1() {
    window.setTimeout(dedupMeuPerfilQuantityOriginsV1, 0);
    window.setTimeout(dedupMeuPerfilQuantityOriginsV1, 80);
    window.setTimeout(dedupMeuPerfilQuantityOriginsV1, 250);
  }

  document.addEventListener("click", (event) => { if (!isFormControlClickV1(event)) scheduleDedupMeuPerfilQuantityOriginsV1(); }, true);
  // Sem 'input': a cada tecla reescrevia os atributos das origens de quantidade (pagina a tremer).
  document.addEventListener("change", scheduleDedupMeuPerfilQuantityOriginsV1, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleDedupMeuPerfilQuantityOriginsV1);
  } else {
    scheduleDedupMeuPerfilQuantityOriginsV1();
  }

  window.setTimeout(scheduleDedupMeuPerfilQuantityOriginsV1, 150);
  window.setTimeout(scheduleDedupMeuPerfilQuantityOriginsV1, 600);
})();

// APPGENESIS_MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1_END

// APPGENESIS_MEU_PERFIL_EDIT_SECTION_FILTER_V1_START
//###################################################################################
// (MEU_PERFIL_EDIT_SECTION_FILTER_V1) FILTRAR CAMPOS DO EDITAR POR ABA/CABECALHO
//###################################################################################

(function setupMeuPerfilEditSectionFilterV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeEditSectionTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeEditSectionKeyV1(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeEditSectionTextV1(value).trim().toLowerCase();
  }

  function normalizeEditSectionLookupV1(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeEditSectionTextV1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getMeuPerfilEditFormV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function sectionKeyFromLabelV1(label) {
    const cleanLabel = normalizeEditSectionLookupV1(label);

    if (!cleanLabel) {
      return "";
    }

    const sections = Array.isArray(profilePersonalSections) ? profilePersonalSections : [];

    for (const section of sections) {
      const sectionLabel = normalizeEditSectionLookupV1(section && section.label);

      if (sectionLabel && sectionLabel === cleanLabel) {
        return normalizeEditSectionKeyV1(section && section.key);
      }
    }

    return "";
  }

  function getCurrentProfileSectionFromInputV1() {
    const selectors = [
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    for (const selector of selectors) {
      const input = document.querySelector(selector);
      const value = normalizeEditSectionKeyV1(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getCurrentProfileSectionFromActiveTabV1() {
    const activeSelectors = [
      "[data-profile-section-tab].active",
      "[data-profile-section-tab][aria-selected='true']",
      "[data-profile-section-button].active",
      "[data-profile-section-button][aria-selected='true']",
      ".profile-section-tab.active",
      ".profile-section-tab[aria-selected='true']",
      "#perfil-pessoal-card .tab.active",
      "#perfil-pessoal-card .active"
    ];

    for (const selector of activeSelectors) {
      const activeElement = document.querySelector(selector);

      if (!activeElement) {
        continue;
      }

      const datasetValue = (
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      const datasetSection = normalizeEditSectionKeyV1(datasetValue);

      if (datasetSection) {
        return datasetSection;
      }

      const textSection = sectionKeyFromLabelV1(activeElement.textContent);

      if (textSection) {
        return textSection;
      }
    }

    return "";
  }

  function getCurrentProfileSectionV1() {
    return (
      getCurrentProfileSectionFromInputV1() ||
      getCurrentProfileSectionFromActiveTabV1() ||
      (
        Array.isArray(profilePersonalSections) &&
        profilePersonalSections.length
          ? normalizeEditSectionKeyV1(profilePersonalSections[0].key)
          : ""
      )
    );
  }

  function getElementSectionPaneV1(element) {
    if (!element) {
      return "";
    }

    return normalizeEditSectionKeyV1(
      element.dataset.profileSectionPane ||
      element.dataset.profileSection ||
      element.dataset.sectionKey ||
      ""
    );
  }

  function getVisibilityWrapperV1(element) {
    if (!element) {
      return null;
    }

    if (
      element.classList &&
      (
        element.classList.contains("field") ||
        element.classList.contains("profile-quantity-rule-v1") ||
        element.classList.contains("profile-quantity-readonly-v1")
      )
    ) {
      return element;
    }

    return (
      element.closest(".field") ||
      element.closest("[data-profile-quantity-rule-key]") ||
      element.closest("[data-profile-quantity-readonly-rule-key]") ||
      element
    );
  }

  function isDuplicateOriginWrapperV1(wrapper) {
    if (!wrapper || !wrapper.dataset) {
      return false;
    }

    return wrapper.dataset.profileQuantityOriginDuplicateV1 === "1";
  }

  function setWrapperVisibleBySectionV1(wrapper, currentSection, expectedSection) {
    if (!wrapper || !currentSection || !expectedSection) {
      return;
    }

    // Campo oculto por regra subsequente nao pode ser reexibido aqui (causava piscar a cada change).
    if (wrapper.dataset.profileSubsequentHiddenV1 === "1") {
      wrapper.hidden = true;
      wrapper.style.display = "none";
      return;
    }

    if (isDuplicateOriginWrapperV1(wrapper)) {
      wrapper.hidden = true;
      wrapper.style.display = "none";
      return;
    }

    if (currentSection === expectedSection) {
      wrapper.hidden = false;
      wrapper.style.display = "";
      return;
    }

    wrapper.hidden = true;
    wrapper.style.display = "none";
  }

  function applyQuantityHostsSectionV1(form) {
    if (!form || typeof getSidebarMenuSetting !== "function" || typeof normalizeProcessQuantityRules !== "function") {
      return;
    }

    const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);

    if (!setting) {
      return;
    }

    const rules = normalizeProcessQuantityRules(setting.process_quantity_fields);

    rules.forEach((rule) => {
      const ruleKey = normalizeEditSectionKeyV1(rule.key);
      const headerKey = normalizeEditSectionKeyV1(rule.headerKey);

      if (!ruleKey || !headerKey) {
        return;
      }

      const hosts = form.querySelectorAll(
        "[data-profile-quantity-rule-key='" + ruleKey + "'], " +
        "[data-profile-quantity-readonly-rule-key='" + ruleKey + "']"
      );

      hosts.forEach((host) => {
        host.dataset.profileSectionPane = headerKey;
      });
    });
  }

  //###################################################################################
  // (2) APLICAR FILTRO NO FORMULARIO EDITAR
  //###################################################################################

  function applyMeuPerfilEditSectionFilterV1() {
    const form = getMeuPerfilEditFormV1();

    if (!form) {
      return;
    }

    const currentSection = getCurrentProfileSectionV1();

    if (!currentSection) {
      return;
    }

    applyQuantityHostsSectionV1(form);

    const wrappers = new Set();

    Array.from(
      form.querySelectorAll("[data-profile-section-pane], [data-profile-section], [data-section-key]")
    ).forEach((element) => {
      const wrapper = getVisibilityWrapperV1(element);

      if (!wrapper || !form.contains(wrapper)) {
        return;
      }

      wrappers.add(wrapper);
    });

    Array.from(
      form.querySelectorAll("[data-profile-quantity-rule-key]")
    ).forEach((element) => {
      const wrapper = getVisibilityWrapperV1(element);

      if (!wrapper || !form.contains(wrapper)) {
        return;
      }

      wrappers.add(wrapper);
    });

    wrappers.forEach((wrapper) => {
      const wrapperSection = getElementSectionPaneV1(wrapper);

      if (!wrapperSection) {
        return;
      }

      setWrapperVisibleBySectionV1(wrapper, currentSection, wrapperSection);
    });
  }

  function scheduleMeuPerfilEditSectionFilterV1() {
    window.setTimeout(applyMeuPerfilEditSectionFilterV1, 0);
    window.setTimeout(applyMeuPerfilEditSectionFilterV1, 80);
    window.setTimeout(applyMeuPerfilEditSectionFilterV1, 250);
  }

  //###################################################################################
  // (3) EVENTOS
  //###################################################################################

  document.addEventListener("click", (event) => { if (!isFormControlClickV1(event)) scheduleMeuPerfilEditSectionFilterV1(); }, true);
  // Sem 'input': digitar nao muda de aba; reescrever wrappers a cada tecla faz a pagina tremer.
  document.addEventListener("change", scheduleMeuPerfilEditSectionFilterV1, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleMeuPerfilEditSectionFilterV1);
  } else {
    scheduleMeuPerfilEditSectionFilterV1();
  }

  window.setTimeout(scheduleMeuPerfilEditSectionFilterV1, 150);
  window.setTimeout(scheduleMeuPerfilEditSectionFilterV1, 600);
  window.setTimeout(scheduleMeuPerfilEditSectionFilterV1, 1200);
})();

// APPGENESIS_MEU_PERFIL_EDIT_SECTION_FILTER_V1_END

// APPGENESIS_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START
//###################################################################################
// (KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1) MANTER PROCESSO/ABA APOS GRAVAR
//###################################################################################

(function setupKeepCurrentProcessAfterProfileSaveV1() {
  "use strict";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function safeKeepProcessTextV1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeKeepProcessKeyV1(value) {
    if (typeof normalizeMenuKey === "function") {
      return normalizeMenuKey(value);
    }

    return safeKeepProcessTextV1(value).trim().toLowerCase();
  }

  function normalizeKeepProcessLookupV1(value) {
    if (typeof normalizeLookupText === "function") {
      return normalizeLookupText(value);
    }

    return safeKeepProcessTextV1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getProfilePersonalFormKeepProcessV1() {
    return document.querySelector("form[action='/users/profile/personal']")
      || document.querySelector('form[action="/users/profile/personal"]');
  }

  function ensureHiddenInputKeepProcessV1(form, name) {
    let input = form.querySelector("input[name='" + name + "']");

    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }

    return input;
  }

  function getSectionFromKnownInputKeepProcessV1() {
    const selectors = [
      "input[name='profile_section']",
      "[data-meu-perfil-section-input]",
      "[data-profile-section-input]"
    ];

    for (const selector of selectors) {
      const input = document.querySelector(selector);
      const value = normalizeKeepProcessKeyV1(input ? input.value : "");

      if (value) {
        return value;
      }
    }

    return "";
  }

  function getSectionFromActiveTabKeepProcessV1() {
    const sections = Array.isArray(profilePersonalSections) ? profilePersonalSections : [];

    const activeSelectors = [
      "[data-profile-section-tab].active",
      "[data-profile-section-tab][aria-selected='true']",
      "[data-profile-section-button].active",
      "[data-profile-section-button][aria-selected='true']",
      ".profile-section-tab.active",
      ".profile-section-tab[aria-selected='true']",
      "#perfil-pessoal-card .active"
    ];

    for (const selector of activeSelectors) {
      const activeElement = document.querySelector(selector);

      if (!activeElement) {
        continue;
      }

      const datasetValue = (
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      const datasetSection = normalizeKeepProcessKeyV1(datasetValue);

      if (datasetSection) {
        return datasetSection;
      }

      const activeLabel = normalizeKeepProcessLookupV1(activeElement.textContent);

      if (!activeLabel) {
        continue;
      }

      for (const section of sections) {
        const sectionLabel = normalizeKeepProcessLookupV1(section && section.label);

        if (sectionLabel && sectionLabel === activeLabel) {
          return normalizeKeepProcessKeyV1(section && section.key);
        }
      }
    }

    return "";
  }

  function getSectionFromVisiblePaneKeepProcessV1(form) {
    const panes = Array.from(
      form.querySelectorAll("[data-profile-section-pane]")
    );

    for (const pane of panes) {
      const style = window.getComputedStyle ? window.getComputedStyle(pane) : null;

      if (
        pane.hidden ||
        pane.style.display === "none" ||
        (style && style.display === "none")
      ) {
        continue;
      }

      const sectionKey = normalizeKeepProcessKeyV1(pane.dataset.profileSectionPane);

      if (sectionKey) {
        return sectionKey;
      }
    }

    return "";
  }

  function getCurrentProfileSectionKeepProcessV1(form) {
    return (
      getSectionFromKnownInputKeepProcessV1() ||
      getSectionFromActiveTabKeepProcessV1() ||
      getSectionFromVisiblePaneKeepProcessV1(form) ||
      (
        Array.isArray(profilePersonalSections) && profilePersonalSections.length
          ? normalizeKeepProcessKeyV1(profilePersonalSections[0].key)
          : ""
      )
    );
  }

  //###################################################################################
  // (2) SINCRONIZAR CONTEXTO ANTES DE GRAVAR
  //###################################################################################

  function syncProfileSaveContextKeepProcessV1(form) {
    if (!form) {
      return;
    }

    const action = safeKeepProcessTextV1(form.getAttribute("action") || form.action);

    if (!action.includes("/users/profile/personal")) {
      return;
    }

    const currentSection = getCurrentProfileSectionKeepProcessV1(form);

    ensureHiddenInputKeepProcessV1(form, "menu").value = MEU_PERFIL_MENU_KEY;
    ensureHiddenInputKeepProcessV1(form, "target").value = "#perfil-pessoal-card";

    if (currentSection) {
      ensureHiddenInputKeepProcessV1(form, "profile_section").value = currentSection;
    }

    ensureHiddenInputKeepProcessV1(form, "appgenesis_after_save").value = "1";
  }

  function bindProfileSaveContextKeepProcessV1() {
    const form = getProfilePersonalFormKeepProcessV1();

    if (!form || form.dataset.keepCurrentProcessAfterProfileSaveV1 === "1") {
      return;
    }

    form.dataset.keepCurrentProcessAfterProfileSaveV1 = "1";

    form.addEventListener("submit", function () {
      syncProfileSaveContextKeepProcessV1(form);
    }, true);

    form.addEventListener("click", function (event) {
      const submitControl = event.target && event.target.closest
        ? event.target.closest("button[type='submit'], input[type='submit'], button:not([type])")
        : null;

      if (!submitControl) {
        return;
      }

      syncProfileSaveContextKeepProcessV1(form);
    }, true);
  }

  //###################################################################################
  // (3) COBRIR SUBMIT NATIVO/PROGRAMATICO
  //###################################################################################

  if (
    window.HTMLFormElement &&
    window.HTMLFormElement.prototype &&
    !window.HTMLFormElement.prototype.__appgenesisKeepProcessSubmitPatchedV1
  ) {
    const nativeSubmit = window.HTMLFormElement.prototype.submit;

    window.HTMLFormElement.prototype.submit = function patchedSubmitKeepProcessV1() {
      syncProfileSaveContextKeepProcessV1(this);
      return nativeSubmit.call(this);
    };

    window.HTMLFormElement.prototype.__appgenesisKeepProcessSubmitPatchedV1 = true;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindProfileSaveContextKeepProcessV1);
  } else {
    bindProfileSaveContextKeepProcessV1();
  }

  window.setTimeout(bindProfileSaveContextKeepProcessV1, 150);
  window.setTimeout(bindProfileSaveContextKeepProcessV1, 600);
})();
