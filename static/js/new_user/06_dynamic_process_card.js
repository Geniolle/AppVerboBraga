// new_user/06_dynamic_process_card.js: Processo dinamico: card principal.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

function renderDynamicProcessCard(menuKey, sectionKey) {
  debugTabsLogV1("renderDynamicProcessCard", { menuKey, sectionKey });
  if (!dynamicProcessCardEl) {
    return;
  }
  const cleanMenuKey = normalizeMenuKey(menuKey);
  const menuData = dynamicProcessDataByMenu[cleanMenuKey];
  const processSetting = getSidebarMenuSetting(cleanMenuKey);
  const currentProcessValuesByField = collectCurrentDynamicProcessValues(cleanMenuKey);
  const currentProcessQuantityValuesByRule = collectCurrentDynamicProcessQuantityValues(cleanMenuKey);
  dynamicProcessCardEl.classList.remove("editing");
  dynamicProcessCardEl.classList.remove("dynamic-process-open");

  if (dynamicProcessReadOnlyGridEl) {
    dynamicProcessReadOnlyGridEl.innerHTML = "";
  }
  if (dynamicProcessEditGridEl) {
    dynamicProcessEditGridEl.innerHTML = "";
  }
  resetDynamicProcessListCardsV1();
  if (dynamicProcessReadOnlyGridEl && dynamicProcessReadOnlyGridEl.parentElement) {
    dynamicProcessReadOnlyGridEl.parentElement.style.display = "";
  }
  if (dynamicProcessHistoryBlockEl) {
    dynamicProcessHistoryBlockEl.style.display = "none";
  }

  if (!menuData) {
    if (dynamicProcessTitleEl) {
      dynamicProcessTitleEl.textContent = "Processo";
    }
    if (dynamicProcessDescriptionEl) {
      dynamicProcessDescriptionEl.textContent = "Campos configurados para este processo.";
    }
    if (dynamicProcessSectionLabelEl) {
      dynamicProcessSectionLabelEl.textContent = "";
    }
    if (dynamicProcessMenuKeyInputEl) {
      dynamicProcessMenuKeyInputEl.value = "";
      dynamicProcessMenuKeyInputEl.defaultValue = "";
    }
    if (dynamicProcessSectionKeyInputEl) {
      dynamicProcessSectionKeyInputEl.value = "";
      dynamicProcessSectionKeyInputEl.defaultValue = "";
    }
    setDynamicProcessEditToggleVisible(false);
    if (dynamicProcessHistoryActionInputEl) {
      dynamicProcessHistoryActionInputEl.value = "create";
    }
    if (dynamicProcessHistoryRecordIdInputEl) {
      dynamicProcessHistoryRecordIdInputEl.value = "";
    }
    if (dynamicProcessSubmitBtnEl) {
      dynamicProcessSubmitBtnEl.textContent = "Guardar";
    }
    if (dynamicProcessEmptyEl) {
      dynamicProcessEmptyEl.style.display = "";
      dynamicProcessEmptyEl.textContent = "Sem campos configurados para esta aba.";
    }
    syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, {});
    return;
  }

  const hiddenTargets = getHiddenProcessTargets(
    processSetting ? processSetting.process_subsequent_fields : [],
    currentProcessValuesByField
  );
  const fieldSectionMap = getFieldSectionMap(processSetting);
  const visibleSections = menuData.sections.filter(
    (section) => !hiddenTargets.has(normalizeMenuKey(section && section.key))
  );
  if (itemsEl) {
    const submenuLinks = itemsEl.querySelectorAll(".submenu-item[data-dynamic-process-section]");
    submenuLinks.forEach((linkEl) => {
      const linkSectionKey = normalizeMenuKey(linkEl.dataset.dynamicProcessSection);
      linkEl.style.display = hiddenTargets.has(linkSectionKey) ? "none" : "";
    });
  }

  const cleanSectionKey = String(sectionKey || selectedDynamicSectionByMenu[cleanMenuKey] || "").trim();
  let selectedSection = visibleSections.find((section) => String(section.key || "") === cleanSectionKey);
  if (!selectedSection) {
    selectedSection = visibleSections[0];
  }
  if (selectedSection) {
    selectedDynamicSectionByMenu[cleanMenuKey] = String(selectedSection.key || "");
    setActiveSubmenu("#dynamic-process-card", {
      dynamicProcessSectionKey: String(selectedSection.key || "")
    });
  }

  const menuLabel = toSentenceCaseText(menuData.menuLabel || "Processo");
  const sectionLabel = selectedSection
    ? toSentenceCaseText(selectedSection.label || "Campos")
    : "Campos";
  const layoutConfig = getDynamicProcessLayoutConfig(processSetting, menuLabel, sectionLabel);
  const listProcessLayoutMode = Boolean(layoutConfig.isListProcess);
  // Processos normais: devolve os cards que a lista escondeu.
  if (!listProcessLayoutMode) {
    [dynamicProcessCardEl].forEach((cardEl) => {
      if (cardEl && cardEl.dataset.hiddenByListV1 === "1") {
        delete cardEl.dataset.hiddenByListV1;
        cardEl.style.display = "";
      }
    });
  }
  const absenceProcessMode = isAbsenceProcessMenu(cleanMenuKey, menuLabel, sectionLabel);
  // "uses_record_history" (calculado no backend a partir de process_record_uses_history/process_layout
  // no menu_config) permite ativar o modo "Criar <processo>" com lista de registos para qualquer
  // processo via configuracao, sem depender apenas dos padroes legados hardcoded abaixo.
  const historyProcessMode = Boolean(processSetting && processSetting.uses_record_history) ||
    isHistoryProcessMenu(cleanMenuKey, menuLabel, sectionLabel);
  const recordProcessMode = historyProcessMode || listProcessLayoutMode;
  const historyRecordLabels = { singular: layoutConfig.singularLabel, plural: layoutConfig.pluralLabel };
  const showStateField = listProcessLayoutMode
    ? Boolean(layoutConfig.stateEnabled)
    : (historyProcessMode && !absenceProcessMode && historyRecordLabels.singular === "departamento");
  dynamicProcessCardEl.classList.toggle("dynamic-process-open", absenceProcessMode);

  if (dynamicProcessTitleEl) {
    dynamicProcessTitleEl.textContent = sectionLabel || menuLabel;
  }
  if (dynamicProcessDescriptionEl) {
    dynamicProcessDescriptionEl.textContent = "Campos visíveis definidos na configuração desta pasta.";
  }
  if (dynamicProcessSectionLabelEl) {
    dynamicProcessSectionLabelEl.textContent = `Pasta: ${menuLabel} | Aba: ${sectionLabel}`;
  }
  if (dynamicProcessMenuKeyInputEl) {
    dynamicProcessMenuKeyInputEl.value = cleanMenuKey;
    dynamicProcessMenuKeyInputEl.defaultValue = cleanMenuKey;
  }
  if (dynamicProcessEditFormEl) {
    dynamicProcessEditFormEl.dataset.menuKey = cleanMenuKey;
  }
  if (dynamicProcessSectionKeyInputEl) {
    const resolvedSectionKey = String(selectedSection ? (selectedSection.key || "") : "");
    dynamicProcessSectionKeyInputEl.value = resolvedSectionKey;
    dynamicProcessSectionKeyInputEl.defaultValue = resolvedSectionKey;
  }
  if (dynamicProcessHistoryActionInputEl) {
    dynamicProcessHistoryActionInputEl.value = "create";
  }
  if (dynamicProcessHistoryRecordIdInputEl) {
    dynamicProcessHistoryRecordIdInputEl.value = "";
  }
  if (dynamicProcessHistoryRecordStateInputEl) {
    dynamicProcessHistoryRecordStateInputEl.value = "";
  }
  if (dynamicProcessSubmitBtnEl) {
    dynamicProcessSubmitBtnEl.textContent = "Guardar";
  }

  const selectedSectionKey = normalizeMenuKey(selectedSection ? selectedSection.key : "");
  const sectionFields = selectedSection && Array.isArray(selectedSection.fields)
    ? selectedSection.fields.filter((field) => {
        const fieldKey = normalizeMenuKey(field && field.key);
        const fieldSectionKey = fieldSectionMap.get(fieldKey) || selectedSectionKey;
        return !hiddenTargets.has(fieldKey) && !hiddenTargets.has(fieldSectionKey);
      })
    : [];
  const hasQuantityRulesForSection = normalizeProcessQuantityRules(
    processSetting ? processSetting.process_quantity_fields : []
  ).some((rule) => (
    rule.headerKey
      ? rule.headerKey === selectedSectionKey
      : sectionFields.some((field) => normalizeMenuKey(field && field.key) === rule.quantityFieldKey)
  ));
  if (!sectionFields.length && !hasQuantityRulesForSection) {
    setDynamicProcessEditToggleVisible(false);
    if (dynamicProcessEmptyEl) {
      dynamicProcessEmptyEl.style.display = "";
      dynamicProcessEmptyEl.textContent = "Sem campos configurados para esta aba.";
    }
    if (dynamicProcessHistoryBlockEl) {
      dynamicProcessHistoryBlockEl.style.display = "none";
    }
    syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, currentProcessQuantityValuesByRule);
    return;
  }

  if (dynamicProcessEditToggleEl) {
    setDynamicProcessEditToggleVisible(false);
    if (!absenceProcessMode && (sectionFields.length || hasQuantityRulesForSection)) {
      setDynamicProcessEditToggleVisible(true);
      dynamicProcessEditToggleEl.textContent = listProcessLayoutMode
        ? layoutConfig.createTitle
        : (historyProcessMode ? `Criar ${historyRecordLabels.singular}` : "Editar");
    }
  }
  if (dynamicProcessEmptyEl) {
    dynamicProcessEmptyEl.style.display = "none";
  }

  const renderedInputsByFieldKey = new Map();
  // Toggle switches (flags) ficam sempre no fim do formulario; a ordem relativa dos demais campos e mantida.
  const orderedSectionFields = [
    ...sectionFields.filter((field) => normalizeProcessFieldType(field.fieldType) !== "flag"),
    ...sectionFields.filter((field) => normalizeProcessFieldType(field.fieldType) === "flag"),
  ];
  orderedSectionFields.forEach((field) => {
    const fieldKey = normalizeMenuKey(field.key);
    if (!fieldKey) {
      return;
    }
    const fieldLabel = toSentenceCaseText(field.label || fieldKey);
    const fieldType = normalizeProcessFieldType(field.fieldType);
    const fieldSize = normalizeProcessFieldSize(field.size, fieldType);
    const fieldRequired = Boolean(field.isRequired) && fieldType !== "flag";
    const readOnlyValue = String(field.value || "").trim();
    const fieldValue = absenceProcessMode ? "" : readOnlyValue;
    const editDefaultValue = recordProcessMode ? "" : fieldValue;

    if (dynamicProcessReadOnlyGridEl) {
      const readOnlyItemEl = document.createElement("div");
      readOnlyItemEl.className = "personal-item";
      readOnlyItemEl.dataset.processFieldKey = fieldKey;

      const labelEl = document.createElement("span");
      labelEl.className = "personal-label";
      labelEl.textContent = fieldLabel;

      const valueEl = document.createElement("strong");
      valueEl.className = "personal-value";
      if (fieldType === "flag") {
        valueEl.textContent = isTruthyFlagValue(fieldValue) ? "Sim" : "Não";
      } else {
        valueEl.textContent = fieldValue || "-";
      }

      readOnlyItemEl.appendChild(labelEl);
      readOnlyItemEl.appendChild(valueEl);
      dynamicProcessReadOnlyGridEl.appendChild(readOnlyItemEl);
    }

    if (dynamicProcessEditGridEl) {
      const fieldContainerEl = document.createElement("div");
      fieldContainerEl.className = "field";
      fieldContainerEl.dataset.processFieldKey = fieldKey;
      if (field.editableWhen) {
        fieldContainerEl.dataset.editableWhen = JSON.stringify(field.editableWhen);
      }
      if (field.requiredWhen) {
        fieldContainerEl.dataset.requiredWhen = JSON.stringify(field.requiredWhen);
      }
      if (field.visibleWhen) {
        fieldContainerEl.dataset.visibleWhen = JSON.stringify(field.visibleWhen);
      }
      if (field.autoDocumentNumber) {
        fieldContainerEl.dataset.autoDocumentNumber = JSON.stringify(field.autoDocumentNumber);
      }
      if (field.addButtonLabel) {
        fieldContainerEl.dataset.addButtonLabel = field.addButtonLabel;
      }
      fieldContainerEl.dataset.fieldLabel = fieldLabel;

      const inputId = `dynamic_process_${cleanMenuKey}_${String(selectedSection ? (selectedSection.key || "") : "")}_${fieldKey}`
        .replace(/[^a-z0-9_]+/gi, "_");
      const inputName = `process_field__${fieldKey}`;

      const labelEl = document.createElement("label");
      labelEl.setAttribute("for", inputId);
      labelEl.textContent = fieldRequired ? `${fieldLabel} *` : fieldLabel;

      if (fieldType === "flag") {
        const wrapperEl = document.createElement("label");
        wrapperEl.className = "profile-custom-flag-control";

        const inputEl = document.createElement("input");
        inputEl.id = inputId;
        inputEl.type = "checkbox";
        inputEl.name = inputName;
        inputEl.value = "1";
        inputEl.checked = isTruthyFlagValue(editDefaultValue);
        inputEl.defaultChecked = inputEl.checked;

        const textEl = document.createElement("span");
        textEl.textContent = "Ativo";

        wrapperEl.appendChild(inputEl);
        wrapperEl.appendChild(textEl);
        renderedInputsByFieldKey.set(fieldKey, inputEl);

        fieldContainerEl.appendChild(labelEl);
        fieldContainerEl.appendChild(wrapperEl);
      } else if (fieldType === "list") {
        const selectEl = document.createElement("select");
        selectEl.id = inputId;
        selectEl.name = inputName;
        selectEl.required = fieldRequired;

        const defaultOptionEl = document.createElement("option");
        defaultOptionEl.value = "";
        defaultOptionEl.textContent = "Selecione";
        selectEl.appendChild(defaultOptionEl);

        const listOptions = Array.isArray(field.listOptions) ? field.listOptions : [];
        listOptions.forEach((optionValue) => {
          const optionEl = document.createElement("option");
          optionEl.value = String(optionValue || "");
          optionEl.textContent = String(optionValue || "");
          if (String(optionValue || "") === editDefaultValue) {
            optionEl.selected = true;
          }
          selectEl.appendChild(optionEl);
        });

        renderedInputsByFieldKey.set(fieldKey, selectEl);
        fieldContainerEl.appendChild(labelEl);
        fieldContainerEl.appendChild(selectEl);
      } else if (fieldType === "longtext") {
        const areaEl = document.createElement("textarea");
        areaEl.id = inputId;
        areaEl.name = inputName;
        areaEl.rows = 8;
        areaEl.value = editDefaultValue;
        areaEl.required = fieldRequired;
        renderedInputsByFieldKey.set(fieldKey, areaEl);
        fieldContainerEl.appendChild(labelEl);
        fieldContainerEl.appendChild(areaEl);
      } else if (fieldType === "rows") {
        const hiddenEl = document.createElement("input");
        hiddenEl.type = "hidden";
        hiddenEl.name = inputName;
        hiddenEl.value = "[]";
        const rowsWrapEl = document.createElement("div");
        rowsWrapEl.className = "dynamic-process-rows-container-v1";
        rowsWrapEl._hiddenEl = hiddenEl;
        rowsWrapEl.appendChild(hiddenEl);
        buildProcessRowsEditorV1(rowsWrapEl, field.rowFields || []);
        renderedInputsByFieldKey.set(fieldKey, hiddenEl);
        fieldContainerEl.appendChild(labelEl);
        fieldContainerEl.appendChild(rowsWrapEl);
      } else {
        const inputEl = document.createElement("input");
        const inputValue = fieldType === "date"
          ? normalizeDateInputValue(editDefaultValue)
          : editDefaultValue;
        inputEl.id = inputId;
        inputEl.name = inputName;
        inputEl.type = getDynamicProcessInputType(fieldType);
        inputEl.value = inputValue;
        inputEl.defaultValue = inputValue;
        inputEl.required = fieldRequired;
        if (fieldType === "date" && typeof inputEl.showPicker === "function") {
          const openDatePicker = () => {
            try {
              inputEl.showPicker();
            } catch (error) {
              // Some browsers block showPicker outside trusted user events.
            }
          };
          inputEl.addEventListener("click", openDatePicker);
          inputEl.addEventListener("focus", openDatePicker);
        }
        if (fieldType === "number") {
          inputEl.inputMode = "numeric";
        }
        if (typeof fieldSize === "number" && fieldSize > 0 && processTextualTypes.has(fieldType)) {
          inputEl.maxLength = fieldSize;
        }
        renderedInputsByFieldKey.set(fieldKey, inputEl);

        fieldContainerEl.appendChild(labelEl);
        fieldContainerEl.appendChild(inputEl);
      }

      dynamicProcessEditGridEl.appendChild(fieldContainerEl);
    }
  });

  if (showStateField && dynamicProcessEditGridEl) {
    const stateFieldEl = document.createElement("div");
    stateFieldEl.className = "field";

    const stateInputId = `dynamic_process_${cleanMenuKey}_${String(selectedSection ? (selectedSection.key || "") : "")}_estado`
      .replace(/[^a-z0-9_]+/gi, "_");

    const stateLabelEl = document.createElement("label");
    stateLabelEl.setAttribute("for", stateInputId);
    stateLabelEl.textContent = "Estado";

    const stateSelectEl = document.createElement("select");
    stateSelectEl.id = stateInputId;
    stateSelectEl.name = "process_state";
    stateSelectEl.innerHTML = `
      <option value="ativo" selected>Ativo</option>
      <option value="inativo">Inativo</option>
    `;

    stateFieldEl.appendChild(stateLabelEl);
    stateFieldEl.appendChild(stateSelectEl);
    dynamicProcessEditGridEl.appendChild(stateFieldEl);
  }

  if (absenceProcessMode) {
    setupAbsenceDateRangeValidation(sectionFields, renderedInputsByFieldKey);
  }

  renderDynamicProcessQuantityGroups(
    cleanMenuKey,
    processSetting,
    selectedSection,
    sectionFields,
    currentProcessValuesByField,
    currentProcessQuantityValuesByRule
  );

  if (listProcessLayoutMode) {
    const historyRowsRaw = Array.isArray(menuProcessHistoryMap[cleanMenuKey])
      ? menuProcessHistoryMap[cleanMenuKey]
      : [];
    const visibleRows = historyRowsRaw.filter((item) => {
      const rowSectionKey = String(item && item.section_key || "").trim();
      if (!selectedSection) {
        return true;
      }
      if (!rowSectionKey) {
        return true;
      }
      return rowSectionKey === String(selectedSection.key || "");
    });
    const sortFieldKey = normalizeMenuKey(processSetting && processSetting.process_record_sort_field);
    if (sortFieldKey) {
      visibleRows.sort((left, right) => {
        const leftValue = String((left && left.values && left.values[sortFieldKey]) || "");
        const rightValue = String((right && right.values && right.values[sortFieldKey]) || "");
        return leftValue.localeCompare(rightValue, "pt", { sensitivity: "base" });
      });
    }
    const splitRows = splitDynamicProcessListRows(visibleRows, layoutConfig);

    if (dynamicProcessTitleEl) {
      dynamicProcessTitleEl.textContent = layoutConfig.createTitle;
    }
    if (dynamicProcessReadOnlyGridEl && dynamicProcessReadOnlyGridEl.parentElement) {
      dynamicProcessReadOnlyGridEl.parentElement.style.display = "none";
    }
    if (dynamicProcessHistoryBlockEl) {
      dynamicProcessHistoryBlockEl.style.display = "none";
    }

    closeDynamicProcessInlineFormV1();
    // Escondido por atributo (regra CSS !important), para nao ser reposto por outros redesenhos.
    [dynamicProcessCardEl].forEach((cardEl) => {
      if (cardEl) {
        cardEl.dataset.hiddenByListV1 = "1";
      }
    });
    renderDynamicProcessListTableCardV1({
      cardEl: dynamicProcessActiveCardEl,
      titleEl: dynamicProcessActiveTitleEl,
      tableEl: dynamicProcessActiveTableEl,
      headEl: dynamicProcessActiveHeadEl,
      bodyEl: dynamicProcessActiveBodyEl,
      emptyEl: dynamicProcessActiveEmptyEl,
      limiterEl: dynamicProcessActiveLimiterEl,
      rows: splitRows.active,
      sectionFields,
      layoutConfig,
      title: layoutConfig.activeTitle,
      emptyMessage: layoutConfig.emptyActiveMessage,
      onCreate: () => openDynamicProcessCreateInlineV1(sectionFields, layoutConfig, dynamicProcessActiveBodyEl)
    });
    renderDynamicProcessListTableCardV1({
      cardEl: dynamicProcessInactiveCardEl,
      titleEl: dynamicProcessInactiveTitleEl,
      tableEl: dynamicProcessInactiveTableEl,
      headEl: dynamicProcessInactiveHeadEl,
      bodyEl: dynamicProcessInactiveBodyEl,
      emptyEl: dynamicProcessInactiveEmptyEl,
      limiterEl: dynamicProcessInactiveLimiterEl,
      rows: splitRows.inactive,
      sectionFields,
      layoutConfig,
      title: layoutConfig.inactiveTitle,
      emptyMessage: layoutConfig.emptyInactiveMessage
    });
    return;
  }

  if (historyProcessMode) {
    renderDynamicProcessHistory(
      cleanMenuKey,
      selectedSection ? (selectedSection.key || "") : "",
      sectionLabel,
      sectionFields,
      historyRecordLabels
    );
  } else if (dynamicProcessHistoryBlockEl) {
    dynamicProcessHistoryBlockEl.style.display = "none";
  }
}
