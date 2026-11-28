// new_user/04_dynamic_process_lists.js: Processo dinamico: historico, listas, editor de linhas.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

function renderDynamicProcessHistory(menuKey, sectionKey, sectionLabel, sectionFields, recordLabels) {
  if (
    !dynamicProcessHistoryBlockEl ||
    !dynamicProcessHistoryTableEl ||
    !dynamicProcessHistoryHeadEl ||
    !dynamicProcessHistoryBodyEl ||
    !dynamicProcessHistoryEmptyEl
  ) {
    return;
  }

  const cleanMenuKey = normalizeMenuKey(menuKey);
  const cleanSectionKey = String(sectionKey || "").trim();
  const historyRowsRaw = Array.isArray(menuProcessHistoryMap[cleanMenuKey])
    ? menuProcessHistoryMap[cleanMenuKey]
    : [];
  const historyRows = historyRowsRaw.filter((item) => item && typeof item === "object");
  const visibleRows = historyRows.filter((item) => {
    const rowSectionKey = String(item.section_key || "").trim();
    if (!cleanSectionKey) {
      return true;
    }
    if (!rowSectionKey) {
      return true;
    }
    return rowSectionKey === cleanSectionKey;
  });

  dynamicProcessHistoryHeadEl.innerHTML = "";
  dynamicProcessHistoryBodyEl.innerHTML = "";

  const normalizedFields = Array.isArray(sectionFields)
    ? sectionFields.filter((field) => field && typeof field === "object")
    : [];
  const tableFields = normalizedFields.filter((field) => String(field.key || "").trim());
  const showStateColumn = String(recordLabels.singular || "") === "departamento";

  if (!tableFields.length || !visibleRows.length) {
    dynamicProcessHistoryTableEl.style.display = "none";
    dynamicProcessHistoryEmptyEl.style.display = "";
    dynamicProcessHistoryEmptyEl.textContent = `Sem ${recordLabels.plural} criados.`;
    dynamicProcessHistoryBlockEl.style.display = "";
    if (dynamicProcessHistoryTitleEl) {
      dynamicProcessHistoryTitleEl.textContent = `Lista de ${recordLabels.plural} criados`;
    }
    return;
  }

  const headRowEl = document.createElement("tr");
  const createdHeadEl = document.createElement("th");
  createdHeadEl.textContent = "Criado em";
  headRowEl.appendChild(createdHeadEl);
  tableFields.forEach((field) => {
    const thEl = document.createElement("th");
    thEl.textContent = toSentenceCaseText(field.label || field.key);
    headRowEl.appendChild(thEl);
  });
  if (showStateColumn) {
    const stateHeadEl = document.createElement("th");
    stateHeadEl.textContent = "Estado";
    headRowEl.appendChild(stateHeadEl);
  }
  const actionsHeadEl = document.createElement("th");
  actionsHeadEl.textContent = "Ações";
  headRowEl.appendChild(actionsHeadEl);
  dynamicProcessHistoryHeadEl.appendChild(headRowEl);

  visibleRows.forEach((row) => {
    const trEl = document.createElement("tr");
    const rowRecordId = String(row.record_id || "").trim();

    const createdCellEl = document.createElement("td");
    createdCellEl.textContent = String(row.created_at || "-").trim() || "-";
    trEl.appendChild(createdCellEl);

    const values = row.values && typeof row.values === "object" ? row.values : {};
    tableFields.forEach((field) => {
      const fieldKey = normalizeMenuKey(field.key);
      const tdEl = document.createElement("td");
      const rawValue = String(values[fieldKey] || "").trim();
      if (normalizeProcessFieldType(field.fieldType) === "flag") {
        tdEl.textContent = isTruthyFlagValue(rawValue) ? "Sim" : "Não";
      } else {
        tdEl.textContent = rawValue || "-";
      }
      trEl.appendChild(tdEl);
    });
    if (showStateColumn) {
      const stateCellEl = document.createElement("td");
      const rawStateValue = normalizeLookupText(values.__estado || "");
      stateCellEl.textContent = rawStateValue === "inativo" ? "Inativo" : "Ativo";
      trEl.appendChild(stateCellEl);
    }

    const actionsCellEl = document.createElement("td");
    const actionsWrapEl = document.createElement("div");
    actionsWrapEl.className = "table-actions";

    const editBtnEl = document.createElement("button");
    editBtnEl.type = "button";
    editBtnEl.className = "table-icon-btn";
    editBtnEl.title = `Editar ${recordLabels.singular}`;
    editBtnEl.setAttribute("aria-label", `Editar ${recordLabels.singular}`);
    editBtnEl.innerHTML = "&#9998;";
    editBtnEl.disabled = !rowRecordId;
    editBtnEl.addEventListener("click", () => {
      if (!rowRecordId || !dynamicProcessEditFormEl) {
        return;
      }
      if (dynamicProcessHistoryActionInputEl) {
        dynamicProcessHistoryActionInputEl.value = "update";
      }
      if (dynamicProcessHistoryRecordIdInputEl) {
        dynamicProcessHistoryRecordIdInputEl.value = rowRecordId;
      }
      if (dynamicProcessSubmitBtnEl) {
        dynamicProcessSubmitBtnEl.textContent = "Guardar";
      }
      if (dynamicProcessCardEl) {
        dynamicProcessCardEl.classList.add("editing");
      }

      const values = row.values && typeof row.values === "object" ? row.values : {};
      tableFields.forEach((field) => {
        const fieldKey = normalizeMenuKey(field.key);
        if (!fieldKey) {
          return;
        }
        const inputName = `process_field__${fieldKey}`;
        const inputEl = dynamicProcessEditFormEl.querySelector(`[name="${inputName}"]`);
        if (!inputEl) {
          return;
        }
        const rawValue = String(values[fieldKey] || "").trim();
        if (inputEl.type === "checkbox") {
          const normalizedFlag = isTruthyFlagValue(rawValue);
          inputEl.checked = normalizedFlag;
          inputEl.dispatchEvent(new Event("input", { bubbles: true }));
          return;
        }
        let normalizedValue = rawValue;
        if (normalizeProcessFieldType(field.fieldType) === "date") {
          normalizedValue = normalizeDateInputValue(rawValue);
        }
        inputEl.value = normalizedValue;
        inputEl.dispatchEvent(new Event("input", { bubbles: true }));
      });
      if (showStateColumn) {
        const stateSelectEl = dynamicProcessEditFormEl.querySelector("[name='process_state']");
        if (stateSelectEl) {
          const rawStateValue = normalizeLookupText(values.__estado || "");
          stateSelectEl.value = rawStateValue === "inativo" ? "inativo" : "ativo";
        }
      }

      dynamicProcessEditFormEl.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    actionsWrapEl.appendChild(editBtnEl);

    const deleteBtnEl = document.createElement("button");
    deleteBtnEl.type = "button";
    deleteBtnEl.className = "table-icon-btn table-icon-btn-danger";
    deleteBtnEl.title = `Eliminar ${recordLabels.singular}`;
    deleteBtnEl.setAttribute("aria-label", `Eliminar ${recordLabels.singular}`);
    deleteBtnEl.innerHTML = "&#128465;";
    deleteBtnEl.disabled = !rowRecordId;
    deleteBtnEl.addEventListener("click", () => {
      if (!rowRecordId || !dynamicProcessEditFormEl) {
        return;
      }
      if (!window.confirm(`Deseja eliminar este ${recordLabels.singular}?`)) {
        return;
      }
      if (dynamicProcessHistoryActionInputEl) {
        dynamicProcessHistoryActionInputEl.value = "delete";
      }
      if (dynamicProcessHistoryRecordIdInputEl) {
        dynamicProcessHistoryRecordIdInputEl.value = rowRecordId;
      }
      dynamicProcessEditFormEl.submit();
    });
    actionsWrapEl.appendChild(deleteBtnEl);

    actionsCellEl.appendChild(actionsWrapEl);
    trEl.appendChild(actionsCellEl);

    dynamicProcessHistoryBodyEl.appendChild(trEl);
  });

  dynamicProcessHistoryTableEl.style.display = "";
  dynamicProcessHistoryEmptyEl.style.display = "none";
  dynamicProcessHistoryBlockEl.style.display = "";
  if (dynamicProcessHistoryTitleEl) {
    dynamicProcessHistoryTitleEl.textContent = `Lista de ${recordLabels.plural} criados`;
  }
}

function normalizeDynamicProcessRecordState(rawValue) {
  const cleanValue = normalizeLookupText(rawValue || "");
  if (
    cleanValue === "inativo" ||
    cleanValue === "inactive" ||
    cleanValue === "0" ||
    cleanValue === "false" ||
    cleanValue === "off"
  ) {
    return "inativo";
  }
  return "ativo";
}

function getDynamicProcessRecordState(row, layoutConfig) {
  // Registos de entidade trazem o estado do registo (ativo/inativo); usa-o antes do campo de valores.
  if (row && typeof row.state === "string" && row.state.trim()) {
    return normalizeDynamicProcessRecordState(row.state);
  }
  const values = row && row.values && typeof row.values === "object" ? row.values : {};
  const statusFieldKey = normalizeMenuKey(layoutConfig && layoutConfig.statusFieldKey || "__estado") || "__estado";
  return normalizeDynamicProcessRecordState(values[statusFieldKey]);
}

function splitDynamicProcessListRows(rows, layoutConfig) {
  const normalizedRows = Array.isArray(rows) ? rows.filter((row) => row && typeof row === "object") : [];
  return normalizedRows.reduce((accumulator, row) => {
    // Regra por campo (ex.: Musicas com OBSOLETA = Sim vao para os inativos), mesmo sem estado do registo.
    if (layoutConfig && layoutConfig.inactiveFieldKey) {
      const fieldValue = String((row.values && row.values[layoutConfig.inactiveFieldKey]) || "").trim().toLowerCase();
      if (fieldValue === layoutConfig.inactiveFieldValue) {
        accumulator.inactive.push(row);
      } else {
        accumulator.active.push(row);
      }
      return accumulator;
    }
    if (!layoutConfig || !layoutConfig.stateEnabled) {
      accumulator.active.push(row);
      return accumulator;
    }
    if (getDynamicProcessRecordState(row, layoutConfig) === "inativo") {
      accumulator.inactive.push(row);
    } else {
      accumulator.active.push(row);
    }
    return accumulator;
  }, { active: [], inactive: [] });
}

function resetDynamicProcessListCardsV1() {
  [
    dynamicProcessActiveCardEl,
    dynamicProcessInactiveCardEl
  ].forEach((cardEl) => {
    if (cardEl) {
      cardEl.style.display = "none";
    }
  });
  [
    dynamicProcessActiveHeadEl,
    dynamicProcessActiveBodyEl,
    dynamicProcessInactiveHeadEl,
    dynamicProcessInactiveBodyEl
  ].forEach((sectionEl) => {
    if (sectionEl) {
      sectionEl.innerHTML = "";
    }
  });
  [
    dynamicProcessActiveEmptyEl,
    dynamicProcessInactiveEmptyEl
  ].forEach((emptyEl) => {
    if (emptyEl) {
      emptyEl.style.display = "none";
    }
  });
  [
    dynamicProcessActiveLimiterEl,
    dynamicProcessInactiveLimiterEl
  ].forEach((limiterEl) => {
    if (limiterEl) {
      // Nao apagar o conteudo: o controlador partilhado (process_shell) guarda referencias a estes elementos.
      limiterEl.style.display = "none";
    }
  });
}

// Nivel exibir no menu atual (marcador renderizado pelo servidor).
function isMenuReadOnlyV1() {
  return Boolean(document.querySelector(".access-no-editar"));
}

// Visualizar: bloqueia os campos (disabled) guardando o estado anterior; editar repoe-o.
function applyDynamicProcessViewLockV1(formEl, lock) {
  if (!formEl) {
    return;
  }
  formEl.querySelectorAll("input:not([type='hidden']), select, textarea").forEach((fieldEl) => {
    if (lock) {
      if (fieldEl.dataset.viewLockPrev === undefined) {
        fieldEl.dataset.viewLockPrev = fieldEl.disabled ? "1" : "0";
      }
      fieldEl.disabled = true;
      return;
    }
    if (fieldEl.dataset.viewLockPrev !== undefined) {
      fieldEl.disabled = fieldEl.dataset.viewLockPrev === "1";
      delete fieldEl.dataset.viewLockPrev;
    }
  });
}

function populateDynamicProcessListFormV1(sectionFields, row, layoutConfig, options) {
  if (!dynamicProcessEditFormEl) {
    return;
  }

  applyDynamicProcessViewLockV1(dynamicProcessEditFormEl, false);
  const isViewOnly = Boolean(options && options.viewOnly);
  dynamicProcessEditFormEl.classList.toggle("dynamic-process-view-only-v1", isViewOnly);
  if (dynamicProcessCardEl) {
    dynamicProcessCardEl.classList.toggle("dynamic-process-view-only-v1", isViewOnly);
  }

  dynamicProcessEditFormEl.reset();
  const values = row && row.values && typeof row.values === "object" ? row.values : {};
  if (dynamicProcessHistoryActionInputEl) {
    dynamicProcessHistoryActionInputEl.value = "update";
  }
  if (dynamicProcessHistoryRecordIdInputEl) {
    dynamicProcessHistoryRecordIdInputEl.value = String(row && row.record_id || "").trim();
  }
  if (dynamicProcessHistoryRecordStateInputEl) {
    dynamicProcessHistoryRecordStateInputEl.value = "";
  }
  if (dynamicProcessSubmitBtnEl) {
    dynamicProcessSubmitBtnEl.textContent = "Guardar";
  }
  if (dynamicProcessCardEl) {
    dynamicProcessCardEl.classList.add("editing");
  }
  if (dynamicProcessTitleEl) {
    dynamicProcessTitleEl.textContent = isViewOnly
      ? "Exibir registo"
      : (layoutConfig && layoutConfig.editTitle ? layoutConfig.editTitle : "Editar registo");
  }

  dynamicProcessPopulatingV1 = true;
  try {
    sectionFields.forEach((field) => {
      const fieldKey = normalizeMenuKey(field && field.key);
      if (!fieldKey) {
        return;
      }
      const inputEl = dynamicProcessEditFormEl.querySelector(`[name="process_field__${fieldKey}"]`);
      if (!inputEl) {
        return;
      }
      const rawValue = String(values[fieldKey] || "").trim();
      if (inputEl.type === "checkbox") {
        inputEl.checked = isTruthyFlagValue(rawValue);
        inputEl.dispatchEvent(new Event("input", { bubbles: true }));
        return;
      }
      const normalizedValue = normalizeProcessFieldType(field && field.fieldType) === "date"
        ? normalizeDateInputValue(rawValue)
        : rawValue;
      inputEl.value = normalizedValue;
      inputEl.dispatchEvent(new Event("input", { bubbles: true }));
    });
  } finally {
    dynamicProcessPopulatingV1 = false;
  }
  resetProcessRowsFieldsV1(dynamicProcessEditFormEl, values);
  applyConditionalProcessFieldRulesV1(dynamicProcessEditFormEl);
  applyDynamicProcessViewLockV1(dynamicProcessEditFormEl, isViewOnly);
  // Repoe o estado de edicao do registo selecionado.
  if (dynamicProcessHistoryActionInputEl) {
    dynamicProcessHistoryActionInputEl.value = "update";
  }
  if (dynamicProcessHistoryRecordIdInputEl) {
    dynamicProcessHistoryRecordIdInputEl.value = String(row && row.record_id || "").trim();
  }

  if (layoutConfig && layoutConfig.stateEnabled) {
    const stateSelectEl = dynamicProcessEditFormEl.querySelector("[name='process_state']");
    if (stateSelectEl) {
      stateSelectEl.value = getDynamicProcessRecordState(row, layoutConfig);
    }
  }

  const populatedRecordId = String(row && row.record_id || "").trim();
  const anchorRowEl = [dynamicProcessActiveBodyEl, dynamicProcessInactiveBodyEl]
    .filter(Boolean)
    .map((bodyEl) => bodyEl.querySelector(`tr[data-record-id="${populatedRecordId}"]`))
    .find(Boolean) || null;
  placeDynamicProcessFormInRowV1(anchorRowEl, anchorRowEl ? anchorRowEl.parentElement : dynamicProcessActiveBodyEl);
  dynamicProcessEditFormEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Abre o formulario de criacao logo abaixo do cabecalho da lista (topo do corpo da tabela).
function openDynamicProcessCreateInlineV1(sectionFields, layoutConfig, bodyEl) {
  if (!dynamicProcessEditFormEl || !bodyEl) {
    return;
  }
  dynamicProcessEditFormEl.reset();
  resetProcessRowsFieldsV1(dynamicProcessEditFormEl, {});
  if (dynamicProcessHistoryActionInputEl) {
    dynamicProcessHistoryActionInputEl.value = "create";
  }
  if (dynamicProcessHistoryRecordIdInputEl) {
    dynamicProcessHistoryRecordIdInputEl.value = "";
  }
  if (dynamicProcessSubmitBtnEl) {
    dynamicProcessSubmitBtnEl.textContent = "Guardar";
  }
  placeDynamicProcessFormInRowV1(null, bodyEl);
  dynamicProcessEditFormEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Move o formulario para uma linha da tabela (apos anchorRowEl, ou no topo se nulo).
// Campo "rows" (ex.: Musica + Tom): linhas com "+" para adicionar e "-" para remover, como nas Funcoes.
// O valor vai para um input oculto em JSON: [{"musica": "...", "tom": "..."}].
function buildProcessRowsEditorV1(wrapEl, rowFields) {
  const hiddenEl = wrapEl._hiddenEl;
  const gridTemplate = `repeat(${Math.max(rowFields.length, 1)}, minmax(0, 1fr)) 36px`;
  const headEl = document.createElement("div");
  headEl.className = "dynamic-process-row-head-v1";
  headEl.style.gridTemplateColumns = gridTemplate;
  rowFields.forEach((rowField) => {
    const headCellEl = document.createElement("span");
    headCellEl.textContent = rowField.label + (rowField.required ? " *" : "");
    headEl.appendChild(headCellEl);
  });
  headEl.appendChild(document.createElement("span"));
  // Nome de cada sub-campo fica a esquerda do proprio campo (regra global); o cabecalho deixa de ser preciso.
  headEl.style.display = "none";
  const listEl = document.createElement("div");
  listEl.className = "dynamic-process-rows-list-v1";
  const addBtnEl = document.createElement("button");
  addBtnEl.type = "button";
  addBtnEl.className = "dynamic-process-row-add-v1";
  addBtnEl.textContent = "+";
  addBtnEl.setAttribute("aria-label", "Adicionar linha");
  addBtnEl.title = "Adicionar linha";
  wrapEl.appendChild(headEl);
  wrapEl.appendChild(listEl);
  wrapEl.appendChild(addBtnEl);

  const syncHidden = () => {
    const rows = [...listEl.querySelectorAll(".dynamic-process-row-v1")].map((rowEl) => {
      const rowValues = {};
      rowFields.forEach((rowField) => {
        const inputEl = rowEl.querySelector(`[data-row-field="${rowField.key}"]`);
        rowValues[rowField.key] = inputEl ? String(inputEl.value || "") : "";
      });
      return rowValues;
    });
    hiddenEl.value = JSON.stringify(rows.filter((rowValues) => Object.values(rowValues).some((value) => value.trim())));
  };
  // Liga/desliga os icones de video da linha conforme a musica escolhida tenha link.
  const refreshRowLinks = (rowEl) => {
    rowEl.querySelectorAll(".dynamic-process-row-link-v1").forEach((btnEl) => {
      const sourceEl = rowEl.querySelector(`[data-row-field="${btnEl.dataset.linkFrom}"]`);
      const chosenEl = sourceEl && sourceEl.tagName === "SELECT" ? sourceEl.options[sourceEl.selectedIndex] : null;
      btnEl.disabled = !(chosenEl && chosenEl.dataset.url);
    });
    // Icone de nota: o painel de letra (so leitura) acompanha a musica escolhida.
    rowEl.querySelectorAll(".dynamic-process-row-note-v1").forEach((btnEl) => {
      const sourceEl = rowEl.querySelector(`[data-row-field="${btnEl.dataset.lyricsFrom}"]`);
      const chosenEl = sourceEl && sourceEl.tagName === "SELECT" ? sourceEl.options[sourceEl.selectedIndex] : null;
      const panelEl = btnEl._lyricsPanelEl;
      btnEl.disabled = !(chosenEl && chosenEl.value);
      if (panelEl) {
        const lyrics = chosenEl ? String(chosenEl.dataset.lyrics || "") : "";
        panelEl.querySelector("textarea").value = lyrics || "Sem letra registada para esta música.";
        if (btnEl.disabled) {
          panelEl.hidden = true;
        }
      }
    });
  };
  const addRow = (values) => {
    const rowEl = document.createElement("div");
    rowEl.className = "dynamic-process-row-v1";
    rowEl.style.gridTemplateColumns = gridTemplate;
    rowFields.forEach((rowField) => {
      const listOptions = Array.isArray(rowField.list_options) ? rowField.list_options : [];
      let inputEl;
      if (rowField.readonly) {
        // Campo automatico: fechado (cinzento), preenchido a partir de outro campo da linha.
        inputEl = document.createElement("input");
        inputEl.type = "text";
        inputEl.readOnly = true;
        inputEl.tabIndex = -1;
        inputEl.className = "dynamic-process-row-readonly-v1";
        inputEl.value = String((values && values[rowField.key]) || "");
      } else if (listOptions.length) {
        inputEl = document.createElement("select");
        const emptyOptionEl = document.createElement("option");
        emptyOptionEl.value = "";
        emptyOptionEl.textContent = "Selecione";
        inputEl.appendChild(emptyOptionEl);
        listOptions.forEach((option) => {
          const optionEl = document.createElement("option");
          optionEl.value = String(option.value || "");
          optionEl.textContent = String(option.label || option.value || "");
          optionEl.dataset.extra = String(option.extra || "");
          optionEl.dataset.url = String(option.url || "");
          optionEl.dataset.lyrics = String(option.lyrics || "");
          inputEl.appendChild(optionEl);
        });
        inputEl.value = String((values && values[rowField.key]) || "");
        inputEl.addEventListener("change", () => {
          // Preenche os campos automaticos desta linha a partir da opcao escolhida.
          const chosenEl = inputEl.options[inputEl.selectedIndex];
          rowFields
            .filter((otherField) => otherField.autofill_from === rowField.key)
            .forEach((otherField) => {
              const autoEl = rowEl.querySelector(`[data-row-field="${otherField.key}"]`);
              if (autoEl) {
                autoEl.value = chosenEl ? String(chosenEl.dataset.extra || "") : "";
              }
            });
          refreshRowLinks(rowEl);
          syncHidden();
        });
      } else {
        inputEl = document.createElement("input");
        inputEl.type = "text";
        inputEl.value = String((values && values[rowField.key]) || "");
        inputEl.addEventListener("input", syncHidden);
      }
      inputEl.dataset.rowField = rowField.key;
      inputEl.setAttribute("aria-label", rowField.label);
      const cellEl = document.createElement("div");
      cellEl.className = "dynamic-process-row-cell-v1";
      const cellLabelEl = document.createElement("span");
      cellLabelEl.className = "dynamic-process-row-cell-label-v1";
      cellLabelEl.textContent = rowField.label + (rowField.required ? " *" : "");
      cellEl.appendChild(cellLabelEl);
      const controlWrapEl = document.createElement("div");
      controlWrapEl.className = "dynamic-process-row-control-v1";
      controlWrapEl.appendChild(inputEl);
      if (rowField.link_button_from) {
        // Icone de video: abre o link da musica escolhida em "link_button_from".
        const linkBtnEl = document.createElement("button");
        linkBtnEl.type = "button";
        linkBtnEl.className = "dynamic-process-row-link-v1";
        linkBtnEl.dataset.linkFrom = rowField.link_button_from;
        linkBtnEl.setAttribute("aria-label", "Abrir video");
        linkBtnEl.title = "Abrir video";
        linkBtnEl.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false" style="display:block;width:20px;height:20px;min-width:20px;flex:0 0 auto"><rect x="2" y="6" width="13" height="12" rx="2.5" fill="currentColor"/><path d="M15 10.5l6-3.5v10l-6-3.5z" fill="currentColor"/></svg>';
        linkBtnEl.addEventListener("click", () => {
          const sourceEl = rowEl.querySelector(`[data-row-field="${rowField.link_button_from}"]`);
          const chosenEl = sourceEl && sourceEl.tagName === "SELECT" ? sourceEl.options[sourceEl.selectedIndex] : null;
          const url = chosenEl ? String(chosenEl.dataset.url || "") : "";
          if (url) {
            window.open(url, "_blank", "noopener");
          }
        });
        controlWrapEl.appendChild(linkBtnEl);
      }
      if (rowField.lyrics_button_from) {
        // Icone de nota: mostra a letra da musica escolhida em "lyrics_button_from", numa linha abaixo, so leitura.
        const noteBtnEl = document.createElement("button");
        noteBtnEl.type = "button";
        noteBtnEl.className = "dynamic-process-row-note-v1";
        noteBtnEl.dataset.lyricsFrom = rowField.lyrics_button_from;
        noteBtnEl.setAttribute("aria-label", "Ver letra");
        noteBtnEl.title = "Ver letra";
        noteBtnEl.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false" style="display:block;width:20px;height:20px;min-width:20px;flex:0 0 auto"><path d="M9 18V5l11-2v13" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><circle cx="6" cy="18" r="3" fill="currentColor"/><circle cx="17" cy="16" r="3" fill="currentColor"/></svg>';
        const lyricsPanelEl = document.createElement("div");
        lyricsPanelEl.className = "dynamic-process-row-lyrics-v1";
        lyricsPanelEl.hidden = true;
        const lyricsLabelEl = document.createElement("span");
        lyricsLabelEl.className = "dynamic-process-row-cell-label-v1";
        lyricsLabelEl.textContent = "Letra";
        const lyricsTextEl = document.createElement("textarea");
        lyricsTextEl.readOnly = true;
        lyricsTextEl.tabIndex = -1;
        lyricsTextEl.rows = 8;
        lyricsTextEl.className = "dynamic-process-row-lyrics-text-v1";
        lyricsPanelEl.appendChild(lyricsLabelEl);
        lyricsPanelEl.appendChild(lyricsTextEl);
        noteBtnEl._lyricsPanelEl = lyricsPanelEl;
        noteBtnEl.addEventListener("click", () => {
          refreshRowLinks(rowEl);
          lyricsPanelEl.hidden = !lyricsPanelEl.hidden;
        });
        controlWrapEl.appendChild(noteBtnEl);
        rowEl._lyricsPanels = (rowEl._lyricsPanels || []).concat(lyricsPanelEl);
      }
      cellEl.appendChild(controlWrapEl);
      rowEl.appendChild(cellEl);
    });
    const removeBtnEl = document.createElement("button");
    removeBtnEl.type = "button";
    removeBtnEl.className = "dynamic-process-row-remove-v1";
    removeBtnEl.textContent = "−";
    removeBtnEl.setAttribute("aria-label", "Remover linha");
    removeBtnEl.addEventListener("click", () => {
      rowEl.remove();
      if (!listEl.children.length) {
        addRow({});
      }
      syncHidden();
    });
    rowEl.appendChild(removeBtnEl);
    // Paineis de letra ocupam a linha toda, abaixo dos campos da linha.
    (rowEl._lyricsPanels || []).forEach((panelEl) => rowEl.appendChild(panelEl));
    listEl.appendChild(rowEl);
    syncHidden();
  };
  addBtnEl.addEventListener("click", () => addRow({}));
  wrapEl._setRows = (rows) => {
    listEl.replaceChildren();
    (Array.isArray(rows) && rows.length ? rows : [{}]).forEach((rowValues) => addRow(rowValues));
    syncHidden();
  };
  wrapEl._setRows([]);
}

// Preenche (ou limpa) os campos "rows" do formulario com os valores do registo.
function resetProcessRowsFieldsV1(formEl, valuesByKey) {
  if (!formEl) {
    return;
  }
  formEl.querySelectorAll(".dynamic-process-rows-container-v1").forEach((wrapEl) => {
    const fieldKey = normalizeMenuKey(wrapEl.closest("[data-process-field-key]")?.dataset.processFieldKey);
    let rows = [];
    try {
      rows = JSON.parse(String((valuesByKey && valuesByKey[fieldKey]) || "[]"));
    } catch (error) {
      rows = [];
    }
    if (typeof wrapEl._setRows === "function") {
      wrapEl._setRows(Array.isArray(rows) ? rows : []);
    }
  });
}

// Campo calculado a partir de uma data (auto_document_number, ex.: R + AAMMDD): fechado e preenchido ao escolher a data.
function applyAutoDocumentNumbersV1(formEl) {
  formEl.querySelectorAll("[data-auto-document-number]").forEach((containerEl) => {
    let rule = null;
    try {
      rule = JSON.parse(containerEl.dataset.autoDocumentNumber || "null");
    } catch (error) {
      rule = null;
    }
    const inputEl = containerEl.querySelector("input");
    const dateEl = rule ? formEl.querySelector(`[name="process_field__${rule.date_field}"]`) : null;
    if (!inputEl || !dateEl) {
      return;
    }
    if (!dateEl._autoDocumentBound) {
      dateEl._autoDocumentBound = true;
      ["input", "change"].forEach((eventName) => {
        dateEl.addEventListener(eventName, () => applyAutoDocumentNumbersV1(formEl));
      });
    }
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(dateEl.value || "").trim());
    const weekdayNames = ["Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"];
    if (!match) {
      inputEl.value = "";
    } else if (rule.format === "weekday") {
      inputEl.value = weekdayNames[new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3])).getDay()];
    } else {
      inputEl.value = `${rule.prefix || ""}${match[1].slice(2)}${match[2]}${match[3]}`;
    }
    inputEl.readOnly = true;
    inputEl.tabIndex = -1;
    inputEl.classList.add("dynamic-process-auto-readonly-v1");
  });
}

// Regras por campo: editable_when, required_when e visible_when (equals ou is_not_empty).
function applyConditionalProcessFieldRulesV1(formEl) {
  if (!formEl) {
    return;
  }
  const readTriggerValue = (triggerField) => {
    const triggerEl = formEl.querySelector(`[name="process_field__${triggerField}"]`);
    if (!triggerEl) {
      return "";
    }
    if (triggerEl.type === "checkbox") {
      return triggerEl.checked ? "1" : "0";
    }
    return String(triggerEl.value || "").trim().toLowerCase();
  };
  const ruleMet = (rule) => {
    const current = readTriggerValue(rule.trigger_field);
    if (rule.operator === "is_not_empty") {
      return current !== "";
    }
    return current === String(rule.trigger_value).trim().toLowerCase();
  };
  formEl.querySelectorAll("[data-process-field-key]").forEach((containerEl) => {
    const editableRaw = containerEl.dataset.editableWhen;
    const requiredRaw = containerEl.dataset.requiredWhen;
    const visibleRaw = containerEl.dataset.visibleWhen;
    if (!editableRaw && !requiredRaw && !visibleRaw) {
      return;
    }
    const inputEl = containerEl.querySelector("input, select, textarea");
    if (!inputEl) {
      return;
    }
    const isRowsField = Boolean(containerEl.querySelector(".dynamic-process-rows-container-v1"));
    const labelEl = containerEl.querySelector("label");
    const fieldLabel = containerEl.dataset.fieldLabel || "";
    let visible = true;
    if (visibleRaw) {
      visible = ruleMet(JSON.parse(visibleRaw));
      containerEl.style.display = visible ? "" : "none";
    }
    let editable = true;
    if (editableRaw) {
      editable = ruleMet(JSON.parse(editableRaw));
    }
    containerEl.querySelectorAll("input, select, textarea").forEach((controlEl) => {
      controlEl.disabled = !visible || !editable;
    });
    let required = false;
    if (requiredRaw) {
      required = ruleMet(JSON.parse(requiredRaw));
    }
    if (!isRowsField) {
      inputEl.required = visible && required;
    }
    if (labelEl && fieldLabel && requiredRaw) {
      labelEl.textContent = required && visible ? `${fieldLabel} *` : fieldLabel;
    }
  });

  // Campos "adicionar": ficam ocultos ate o botao "+" ou ate terem valor (um par de cada vez).
  // O botao so aparece quando o campo anterior (ex.: Tom n) ja esta visivel.
  formEl.querySelectorAll("[data-process-field-key][data-add-button-label]").forEach((containerEl) => {
    const key = containerEl.dataset.processFieldKey;
    const inputEl = containerEl.querySelector("input, select, textarea");
    const revealed = formEl.dataset[`reveal_${key}`] === "1";
    const filled = Boolean(inputEl && String(inputEl.value || "").trim());
    const visible = revealed || filled;
    containerEl.style.display = visible ? "" : "none";
    if (inputEl) {
      inputEl.disabled = !visible;
    }
    if (!containerEl._addButtonEl) {
      const buttonEl = document.createElement("button");
      buttonEl.type = "button";
      buttonEl.className = "dynamic-process-add-pair-btn-v1";
      buttonEl.textContent = `+ ${containerEl.dataset.addButtonLabel}`;
      buttonEl.addEventListener("click", () => {
        formEl.dataset[`reveal_${key}`] = "1";
        applyConditionalProcessFieldRulesV1(formEl);
      });
      containerEl.parentNode.insertBefore(buttonEl, containerEl);
      containerEl._addButtonEl = buttonEl;
    }
    let previousEl = containerEl.previousElementSibling;
    while (previousEl && previousEl.classList.contains("dynamic-process-add-pair-btn-v1")) {
      previousEl = previousEl.previousElementSibling;
    }
    const previousShown = !previousEl || previousEl.style.display !== "none";
    containerEl._addButtonEl.style.display = !visible && previousShown ? "" : "none";
  });
  applyAutoDocumentNumbersV1(formEl);
}

function placeDynamicProcessFormInRowV1(anchorRowEl, bodyEl) {
  if (!dynamicProcessEditFormEl || !bodyEl) {
    return;
  }
  // Cada abertura do formulario comeca sem pares "+" revelados.
  Object.keys(dynamicProcessEditFormEl.dataset)
    .filter((datasetKey) => datasetKey.startsWith("reveal_"))
    .forEach((datasetKey) => delete dynamicProcessEditFormEl.dataset[datasetKey]);
  if (!dynamicProcessInlineOriginV1) {
    dynamicProcessInlineOriginV1 = {
      parent: dynamicProcessEditFormEl.parentNode,
      next: dynamicProcessEditFormEl.nextSibling
    };
  }
  let holderEl = dynamicProcessInlineHolderV1;
  if (!holderEl) {
    holderEl = document.createElement("tr");
    holderEl.className = "dynamic-process-inline-editor-row";
    const cellEl = document.createElement("td");
    cellEl.colSpan = Math.max(1, bodyEl.parentElement ? bodyEl.parentElement.querySelectorAll("thead th").length : 1);
    holderEl.appendChild(cellEl);
  }
  holderEl.firstElementChild.appendChild(dynamicProcessEditFormEl);
  applyConditionalProcessFieldRulesV1(dynamicProcessEditFormEl);
  if (anchorRowEl) {
    anchorRowEl.insertAdjacentElement("afterend", holderEl);
  } else {
    bodyEl.insertBefore(holderEl, bodyEl.firstChild);
  }
  dynamicProcessEditFormEl.style.display = "";
  dynamicProcessInlineHolderV1 = holderEl;
  dynamicProcessInlineSnapshotV1 = serializeDynamicProcessFormV1();
}

function serializeDynamicProcessFormV1() {
  if (!dynamicProcessEditFormEl) {
    return "";
  }
  return Array.from(dynamicProcessEditFormEl.querySelectorAll("input, select, textarea"))
    .map((el) => `${el.name || el.id}=${el.type === "checkbox" || el.type === "radio" ? String(el.checked) : String(el.value)}`)
    .join("&");
}

function dynamicProcessInlineHasChangesV1() {
  return Boolean(dynamicProcessInlineHolderV1) && serializeDynamicProcessFormV1() !== dynamicProcessInlineSnapshotV1;
}

// Devolve o formulario a sua posicao original e fecha a edicao inline.
function closeDynamicProcessInlineFormV1() {
  if (dynamicProcessEditFormEl && dynamicProcessInlineOriginV1 && dynamicProcessInlineOriginV1.parent) {
    const origin = dynamicProcessInlineOriginV1;
    const anchor = origin.next && origin.next.parentNode === origin.parent ? origin.next : null;
    origin.parent.insertBefore(dynamicProcessEditFormEl, anchor);
    dynamicProcessEditFormEl.style.display = "none";
  }
  if (dynamicProcessInlineHolderV1 && dynamicProcessInlineHolderV1.parentNode) {
    dynamicProcessInlineHolderV1.parentNode.removeChild(dynamicProcessInlineHolderV1);
  }
  dynamicProcessInlineHolderV1 = null;
}

function submitDynamicProcessListRecordStateV1(rowRecordId, nextState) {
  if (!dynamicProcessEditFormEl || !rowRecordId) {
    return;
  }
  if (dynamicProcessHistoryActionInputEl) {
    dynamicProcessHistoryActionInputEl.value = "toggle_status";
  }
  if (dynamicProcessHistoryRecordIdInputEl) {
    dynamicProcessHistoryRecordIdInputEl.value = rowRecordId;
  }
  if (dynamicProcessHistoryRecordStateInputEl) {
    dynamicProcessHistoryRecordStateInputEl.value = nextState;
  }
  dynamicProcessEditFormEl.submit();
}

function submitDynamicProcessListRecordDeleteV1(rowRecordId, singularLabel) {
  if (!dynamicProcessEditFormEl || !rowRecordId) {
    return;
  }
  if (!window.confirm(`Deseja eliminar este ${singularLabel}?`)) {
    return;
  }
  if (dynamicProcessHistoryActionInputEl) {
    dynamicProcessHistoryActionInputEl.value = "delete";
  }
  if (dynamicProcessHistoryRecordIdInputEl) {
    dynamicProcessHistoryRecordIdInputEl.value = rowRecordId;
  }
  if (dynamicProcessHistoryRecordStateInputEl) {
    dynamicProcessHistoryRecordStateInputEl.value = "";
  }
  dynamicProcessEditFormEl.submit();
}

function normalizeDynamicProcessListColumnSourceV1(rawValue) {
  const normalizedValue = normalizeLookupText(rawValue || "");
  if (
    normalizedValue === "field" ||
    normalizedValue === "visible_field" ||
    normalizedValue === "field_value" ||
    normalizedValue === "campo"
  ) {
    return "field";
  }
  if (
    normalizedValue === "menu_visibility_scope" ||
    normalizedValue === "visibility_scope" ||
    normalizedValue === "scope" ||
    normalizedValue === "system" ||
    normalizedValue === "sistema"
  ) {
    return "menu_visibility_scope";
  }
  if (normalizedValue === "status" || normalizedValue === "estado") {
    return "status";
  }
  return "";
}

function resolveDynamicProcessListColumnsV1(sectionFields, layoutConfig) {
  const availableFields = Array.isArray(sectionFields)
    ? sectionFields.filter((field) => field && normalizeMenuKey(field.key))
    : [];
  const availableFieldsByKey = new Map(
    availableFields.map((field) => [normalizeMenuKey(field.key), field])
  );
  const configuredColumns = Array.isArray(layoutConfig && layoutConfig.columns)
    ? layoutConfig.columns
    : [];
  const resolvedColumns = [];
  const emittedColumnKeys = new Set();
  const usedFieldKeys = new Set();
  let hasFieldColumn = false;
  let hasSystemColumn = false;
  let hasStatusColumn = false;

  function appendFieldColumn(fieldKey, column, defaultCssClass, defaultAlwaysVisible) {
    const normalizedFieldKey = normalizeMenuKey(fieldKey);
    const fieldMeta = normalizedFieldKey
      ? availableFieldsByKey.get(normalizedFieldKey)
      : null;
    if (!fieldMeta) {
      return false;
    }
    const columnKey = normalizeMenuKey(column && column.key) || normalizedFieldKey;
    if (!columnKey || emittedColumnKeys.has(columnKey)) {
      return false;
    }
    emittedColumnKeys.add(columnKey);
    usedFieldKeys.add(normalizedFieldKey);
    hasFieldColumn = true;
    resolvedColumns.push({
      key: columnKey,
      label: String(
        column && column.label
          ? column.label
          : fieldMeta && fieldMeta.label
            ? fieldMeta.label
            : fieldMeta && fieldMeta.key
              ? fieldMeta.key
              : "Campo"
      ).trim() || "Campo",
      sourceKind: "field",
      fieldKey: normalizedFieldKey,
      fieldType: normalizeProcessFieldType(fieldMeta && fieldMeta.fieldType),
      cssClass: String(column && column.cssClass || defaultCssClass || "").trim(),
      responsivePriority: Number.parseInt(
        column && column.responsivePriority || 0,
        10
      ) || 0,
      alwaysVisible: Boolean(
        column && typeof column.alwaysVisible === "boolean"
          ? column.alwaysVisible
          : defaultAlwaysVisible
      )
    });
    return true;
  }

  configuredColumns.forEach((column) => {
    if (!column || typeof column !== "object") {
      return;
    }
    const sourceKind = normalizeDynamicProcessListColumnSourceV1(
      column.sourceKind || column.source
    );
    if (!sourceKind) {
      return;
    }
    if (sourceKind === "field") {
      const explicitFieldKey = normalizeMenuKey(column.fieldKey);
      if (explicitFieldKey) {
        appendFieldColumn(explicitFieldKey, column, "admin-col-main-v1", !hasFieldColumn);
        return;
      }
      const nextField = availableFields.find((field) => !usedFieldKeys.has(normalizeMenuKey(field.key)));
      if (nextField) {
        appendFieldColumn(nextField.key, column, "admin-col-main-v1", !hasFieldColumn);
      }
      return;
    }
    if (sourceKind === "menu_visibility_scope") {
      const columnKey = normalizeMenuKey(column.key) || "system";
      if (emittedColumnKeys.has(columnKey)) {
        return;
      }
      emittedColumnKeys.add(columnKey);
      hasSystemColumn = true;
      resolvedColumns.push({
        key: columnKey,
        label: String(column.label || "Sistema").trim() || "Sistema",
        sourceKind,
        cssClass: String(column.cssClass || "admin-col-system-v1").trim() || "admin-col-system-v1",
        responsivePriority: Number.parseInt(column.responsivePriority || 0, 10) || 0,
        alwaysVisible: Boolean(column.alwaysVisible)
      });
      return;
    }
    if (sourceKind === "status" && layoutConfig && layoutConfig.stateEnabled) {
      const columnKey = normalizeMenuKey(column.key) || "status";
      if (emittedColumnKeys.has(columnKey)) {
        return;
      }
      emittedColumnKeys.add(columnKey);
      hasStatusColumn = true;
      resolvedColumns.push({
        key: columnKey,
        label: String(column.label || "Estado").trim() || "Estado",
        sourceKind,
        cssClass: String(column.cssClass || "admin-col-status-v1").trim() || "admin-col-status-v1",
        responsivePriority: Number.parseInt(column.responsivePriority || 0, 10) || 0,
        alwaysVisible: true
      });
    }
  });

  if (!hasFieldColumn && availableFields.length) {
    appendFieldColumn(availableFields[0].key, {}, "admin-col-main-v1", true);
  }

  if (layoutConfig && layoutConfig.includeRemainingFields) {
    availableFields.forEach((field, index) => {
      const fieldKey = normalizeMenuKey(field && field.key);
      if (!fieldKey || usedFieldKeys.has(fieldKey)) {
        return;
      }
      appendFieldColumn(fieldKey, {
        responsivePriority: index + 2
      }, "", false);
    });
  }

  if (!hasSystemColumn && layoutConfig && layoutConfig.showSystemColumn) {
    resolvedColumns.push({
      key: "system",
      label: "Sistema",
      sourceKind: "menu_visibility_scope",
      cssClass: "admin-col-system-v1",
      responsivePriority: 2,
      alwaysVisible: false
    });
    hasSystemColumn = true;
  }

  if (!hasStatusColumn && layoutConfig && layoutConfig.stateEnabled) {
    resolvedColumns.push({
      key: "status",
      label: "Estado",
      sourceKind: "status",
      cssClass: "admin-col-status-v1",
      responsivePriority: 0,
      alwaysVisible: true
    });
  }

  return resolvedColumns;
}

function resolveDynamicProcessListCellTextV1(row, column, layoutConfig) {
  const values = row && row.values && typeof row.values === "object" ? row.values : {};
  if (!column || typeof column !== "object") {
    return "-";
  }
  if (column.sourceKind === "menu_visibility_scope") {
    return String(layoutConfig && layoutConfig.visibilityScopeLabel || "").trim() || "-";
  }
  if (column.sourceKind === "status") {
    return getDynamicProcessRecordState(row, layoutConfig) === "inativo" ? "Inativo" : "Ativo";
  }
  if (column.sourceKind === "field") {
    const rawValue = String(values[normalizeMenuKey(column.fieldKey)] || "").trim();
    const rowsText = formatProcessRowsForListV1(rawValue);
    if (rowsText !== null) {
      return rowsText || "-";
    }
    // Datas na lista: dd/mm/aaaa (valor guardado em aaaa-mm-dd; sem conversao de fuso, e so data).
    const isoDateMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(rawValue);
    if (isoDateMatch) {
      return `${isoDateMatch[3]}/${isoDateMatch[2]}/${isoDateMatch[1]}`;
    }
    return column.fieldType === "flag"
      ? (isTruthyFlagValue(rawValue) ? "Sim" : "Não")
      : (rawValue || "-");
  }
  return "-";
}

function formatProcessRowsForListV1(rawValue) {
  if (!rawValue.startsWith("[{")) {
    return null;
  }
  try {
    const rows = JSON.parse(rawValue);
    if (!Array.isArray(rows)) {
      return null;
    }
    return rows
      .map((rowValues) => Object.values(rowValues || {}).map((value) => String(value || "").trim()).filter(Boolean).join(" / "))
      .filter(Boolean)
      .join(", ");
  } catch (error) {
    return null;
  }
}

function appendDynamicProcessListCellV1(trEl, row, column, layoutConfig) {
  if (!trEl || !column) {
    return;
  }
  const tdEl = document.createElement("td");
  if (column.cssClass) {
    tdEl.className = column.cssClass;
  }
  tdEl.setAttribute("data-admin-column-key", column.key || "");
  if (column.responsivePriority) {
    tdEl.setAttribute("data-admin-responsive-priority", String(column.responsivePriority));
  }
  if (column.alwaysVisible) {
    tdEl.setAttribute("data-admin-always-visible", "1");
  }

  if (column.sourceKind === "status") {
    const normalizedState = getDynamicProcessRecordState(row, layoutConfig);
    const badgeEl = document.createElement("span");
    badgeEl.className = normalizedState === "inativo"
      ? "admin-subprocess-badge-v1 admin-subprocess-badge-inactive-v1"
      : "admin-subprocess-badge-v1 admin-subprocess-badge-active-v1";
    badgeEl.textContent = normalizedState === "inativo" ? "Inativo" : "Ativo";
    tdEl.appendChild(badgeEl);
    trEl.appendChild(tdEl);
    return;
  }

  tdEl.textContent = resolveDynamicProcessListCellTextV1(row, column, layoutConfig);
  trEl.appendChild(tdEl);
}

function createDynamicProcessListActionsCellV1(row, sectionFields, layoutConfig) {
  const rowRecordId = String(row && row.record_id || "").trim();
  const actionsCellEl = document.createElement("td");
  actionsCellEl.className = "admin-col-actions-v1";
  actionsCellEl.setAttribute("data-admin-column-key", "actions");
  actionsCellEl.setAttribute("data-admin-always-visible", "1");

  const actionsWrapEl = document.createElement("div");
  actionsWrapEl.className = "table-actions admin-subprocess-row-actions-v1";

  const viewBtnEl = document.createElement("button");
  viewBtnEl.type = "button";
  viewBtnEl.className = "admin-subprocess-action-btn-v1";
  viewBtnEl.title = "Visualizar detalhes";
  viewBtnEl.setAttribute("aria-label", "Visualizar detalhes");
  viewBtnEl.innerHTML = "&#128065;";
  viewBtnEl.disabled = !rowRecordId;
  viewBtnEl.addEventListener("click", () => {
    if (!rowRecordId) {
      return;
    }
    populateDynamicProcessListFormV1(sectionFields, row, layoutConfig, { viewOnly: true });
  });
  actionsWrapEl.appendChild(viewBtnEl);

  const editBtnEl = document.createElement("button");
  editBtnEl.type = "button";
  editBtnEl.className = "admin-subprocess-action-btn-v1";
  editBtnEl.title = `Editar ${layoutConfig.singularLabel}`;
  editBtnEl.setAttribute("aria-label", `Editar ${layoutConfig.singularLabel}`);
  editBtnEl.innerHTML = "&#9998;";
  editBtnEl.disabled = !rowRecordId;
  editBtnEl.addEventListener("click", () => {
    if (!rowRecordId) {
      return;
    }
    populateDynamicProcessListFormV1(sectionFields, row, layoutConfig, { viewOnly: false });
  });
  actionsWrapEl.appendChild(editBtnEl);

  if (layoutConfig.stateEnabled) {
    const currentState = getDynamicProcessRecordState(row, layoutConfig);
    const nextState = currentState === "inativo" ? "ativo" : "inativo";
    const toggleBtnEl = document.createElement("button");
    toggleBtnEl.type = "button";
    toggleBtnEl.className = "admin-subprocess-action-btn-v1";
    toggleBtnEl.title = nextState === "ativo"
      ? `Ativar ${layoutConfig.singularLabel}`
      : `Inativar ${layoutConfig.singularLabel}`;
    toggleBtnEl.setAttribute("aria-label", toggleBtnEl.title);
    toggleBtnEl.innerHTML = nextState === "ativo" ? "&#8635;" : "&#9208;";
    toggleBtnEl.disabled = !rowRecordId;
    toggleBtnEl.addEventListener("click", () => {
      submitDynamicProcessListRecordStateV1(rowRecordId, nextState);
    });
    actionsWrapEl.appendChild(toggleBtnEl);
  }

  if (getDynamicProcessRecordState(row, layoutConfig) === "inativo") {
    const deleteBtnEl = document.createElement("button");
    deleteBtnEl.type = "button";
    deleteBtnEl.className = "admin-subprocess-action-btn-v1 admin-subprocess-action-btn-danger-v1";
    deleteBtnEl.title = `Eliminar ${layoutConfig.singularLabel}`;
    deleteBtnEl.setAttribute("aria-label", `Eliminar ${layoutConfig.singularLabel}`);
    deleteBtnEl.innerHTML = "&#128465;";
    deleteBtnEl.disabled = !rowRecordId;
    deleteBtnEl.addEventListener("click", () => {
      submitDynamicProcessListRecordDeleteV1(rowRecordId, layoutConfig.singularLabel);
    });
    actionsWrapEl.appendChild(deleteBtnEl);
  }

  actionsCellEl.appendChild(actionsWrapEl);
  return actionsCellEl;
}

function renderDynamicProcessListTableCardV1(options) {
  const safeOptions = options && typeof options === "object" ? options : {};
  const cardEl = safeOptions.cardEl;
  const titleEl = safeOptions.titleEl;
  const tableEl = safeOptions.tableEl;
  const headEl = safeOptions.headEl;
  const bodyEl = safeOptions.bodyEl;
  const emptyEl = safeOptions.emptyEl;
  const limiterEl = safeOptions.limiterEl;
  const rows = Array.isArray(safeOptions.rows) ? safeOptions.rows : [];
  const sectionFields = Array.isArray(safeOptions.sectionFields) ? safeOptions.sectionFields : [];
  const layoutConfig = safeOptions.layoutConfig || {};
  const title = String(safeOptions.title || "").trim();
  const emptyMessage = String(safeOptions.emptyMessage || "").trim();
  const resolvedColumns = resolveDynamicProcessListColumnsV1(sectionFields, layoutConfig);

  if (!cardEl || !tableEl || !headEl || !bodyEl || !emptyEl) {
    return;
  }

  if (titleEl) {
    titleEl.textContent = title;
  }

  headEl.innerHTML = "";
  bodyEl.innerHTML = "";
  bodyEl.__processListRowMap = new Map();
  emptyEl.textContent = emptyMessage;
  cardEl.style.display = "";

  // Botao "+" logo apos o titulo para criar registo (margin-right:auto no botao mantem os restantes elementos a direita).
  cardEl.querySelectorAll(".dynamic-process-list-create-btn-v1").forEach((btnEl) => btnEl.remove());
  // Titulo nao cresce e o "+" fica junto dele (regra de cartao com botao inline; ver admin_subprocess_inline_create_v1.css).
  if (typeof safeOptions.onCreate === "function") {
    cardEl.setAttribute("data-admin-subprocess-inline-create-enabled", "1");
  } else {
    cardEl.removeAttribute("data-admin-subprocess-inline-create-enabled");
  }
  if (titleEl && typeof safeOptions.onCreate === "function") {
    const createBtnEl = document.createElement("button");
    createBtnEl.type = "button";
    createBtnEl.className = "admin-subprocess-inline-create-btn-v1 dynamic-process-list-create-btn-v1";
    const createIconEl = document.createElement("span");
    createIconEl.className = "admin-subprocess-inline-create-icon-v1";
    createIconEl.setAttribute("aria-hidden", "true");
    createIconEl.textContent = "+";
    createBtnEl.appendChild(createIconEl);
    const createLabelEl = document.createElement("span");
    createLabelEl.textContent = String(layoutConfig.createTitle || "Criar");
    createBtnEl.appendChild(createLabelEl);
    createBtnEl.title = String(layoutConfig.createTitle || "Criar");
    createBtnEl.setAttribute("aria-label", String(layoutConfig.createTitle || "Criar"));
    createBtnEl.addEventListener("click", () => safeOptions.onCreate());
    titleEl.insertAdjacentElement("afterend", createBtnEl);
  }

  const headerRowEl = document.createElement("tr");
  resolvedColumns.forEach((column) => {
    const thEl = document.createElement("th");
    if (column.cssClass) {
      thEl.className = column.cssClass;
    }
    thEl.setAttribute("data-admin-column-key", column.key || "");
    if (column.responsivePriority) {
      thEl.setAttribute("data-admin-responsive-priority", String(column.responsivePriority));
    }
    if (column.alwaysVisible) {
      thEl.setAttribute("data-admin-always-visible", "1");
    }
    thEl.textContent = String(column.label || "Campo").trim() || "Campo";
    headerRowEl.appendChild(thEl);
  });

  const actionsHeadEl = document.createElement("th");
  actionsHeadEl.className = "admin-col-actions-v1";
  actionsHeadEl.setAttribute("data-admin-column-key", "actions");
  actionsHeadEl.setAttribute("data-admin-always-visible", "1");
  actionsHeadEl.textContent = "AÇÕES";
  headerRowEl.appendChild(actionsHeadEl);
  headEl.appendChild(headerRowEl);

  rows.forEach((row) => {
    const trEl = document.createElement("tr");
    resolvedColumns.forEach((column) => {
      appendDynamicProcessListCellV1(trEl, row, column, layoutConfig);
    });

    trEl.appendChild(
      createDynamicProcessListActionsCellV1(row, sectionFields, layoutConfig)
    );
    // Clicar na linha abre a edicao do registo (botoes e campos dentro da linha mantem a sua acao).
    const rowRecordKey = String(row && row.record_id || "").trim();
    if (rowRecordKey) {
      trEl.classList.add("dynamic-process-list-row-clickable-v1");
      trEl.dataset.recordId = rowRecordKey;
      bodyEl.__processListRowMap.set(rowRecordKey, { row, sectionFields, layoutConfig });
    }
    bodyEl.appendChild(trEl);
  });
  // Listener unico no tbody (sobrevive a linhas recriadas/clonadas pela tabela).
  if (!bodyEl.dataset.processListRowEditBound) {
    bodyEl.dataset.processListRowEditBound = "1";
    bodyEl.addEventListener("click", (event) => {
      const clickedRowEl = event.target.closest ? event.target.closest("tr[data-record-id]") : null;
      if (!clickedRowEl || !bodyEl.contains(clickedRowEl)) {
        return;
      }
      if (event.target.closest("button, a, input, select, textarea, label")) {
        return;
      }
      const entry = bodyEl.__processListRowMap && bodyEl.__processListRowMap.get(clickedRowEl.dataset.recordId);
      if (!entry) {
        return;
      }
      // Com alteracoes por guardar, o clique na linha nao navega (igual ao editor inline de Campos adicionais).
      if (dynamicProcessInlineHasChangesV1()) {
        return;
      }
      const openedRowEl = dynamicProcessInlineHolderV1 ? dynamicProcessInlineHolderV1.previousElementSibling : null;
      if (openedRowEl && openedRowEl.dataset && openedRowEl.dataset.recordId === clickedRowEl.dataset.recordId) {
        closeDynamicProcessInlineFormV1();
        return;
      }
      // Nivel exibir (marcador da pagina): clicar na linha abre em modo visualizar.
      populateDynamicProcessListFormV1(entry.sectionFields, entry.row, entry.layoutConfig, {
        viewOnly: isMenuReadOnlyV1(),
      });
    });
  }

  tableEl.style.display = "";
  emptyEl.style.display = rows.length ? "none" : "";
  if (limiterEl) {
    limiterEl.style.display = "";
  }

  enhanceProcessShellTables(cardEl);
}
