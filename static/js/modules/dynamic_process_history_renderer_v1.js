//###################################################################################
// (1) DYNAMIC PROCESS HISTORY RENDERER V1
//###################################################################################
(function registerDynamicProcessHistoryRendererV1() {
  "use strict";

  function renderDynamicProcessHistory(options = {}) {
    const {
      menuKey,
      sectionKey,
      sectionFields,
      recordLabels = {},
      helpers = {},
      data = {},
      elements = {}
    } = options;

    const {
      normalizeMenuKey,
      normalizeLookupText,
      normalizeProcessFieldType,
      normalizeDateInputValue,
      toSentenceCaseText,
      isTruthyFlagValue
    } = helpers;

    const { menuProcessHistoryMap = {} } = data;

    const {
      dynamicProcessHistoryBlockEl,
      dynamicProcessHistoryTableEl,
      dynamicProcessHistoryHeadEl,
      dynamicProcessHistoryBodyEl,
      dynamicProcessHistoryEmptyEl,
      dynamicProcessHistoryActiveCardEl,
      dynamicProcessHistoryActiveTitleEl,
      dynamicProcessHistoryActiveTableEl,
      dynamicProcessHistoryActiveHeadEl,
      dynamicProcessHistoryActiveBodyEl,
      dynamicProcessHistoryActiveEmptyEl,
      dynamicProcessHistoryInactiveCardEl,
      dynamicProcessHistoryInactiveTitleEl,
      dynamicProcessHistoryInactiveTableEl,
      dynamicProcessHistoryInactiveHeadEl,
      dynamicProcessHistoryInactiveBodyEl,
      dynamicProcessHistoryInactiveEmptyEl,
      dynamicProcessHistoryTitleEl,
      dynamicProcessReadOnlyGridEl,
      dynamicProcessReadOnlyEl,
      dynamicProcessEditFormEl,
      dynamicProcessHistoryActionInputEl,
      dynamicProcessHistoryRecordIdInputEl,
      dynamicProcessSubmitBtnEl,
      dynamicProcessCardEl,
      dynamicProcessCreateCardEl
    } = elements;
    const dynamicProcessSongAiFlagInputEl = document.getElementById("dynamic-process-song-ai-flag");

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
    const cleanSectionKey = String(sectionKey || "").trim().toLowerCase();
    const historyRowsRaw = Array.isArray(menuProcessHistoryMap[cleanMenuKey])
      ? menuProcessHistoryMap[cleanMenuKey]
      : [];
    const historyRows = historyRowsRaw.filter((item) => item && typeof item === "object");

    dynamicProcessHistoryHeadEl.innerHTML = "";
    dynamicProcessHistoryBodyEl.innerHTML = "";
    if (dynamicProcessHistoryActiveHeadEl) {
      dynamicProcessHistoryActiveHeadEl.innerHTML = "";
    }
    if (dynamicProcessHistoryActiveBodyEl) {
      dynamicProcessHistoryActiveBodyEl.innerHTML = "";
    }
    if (dynamicProcessHistoryInactiveHeadEl) {
      dynamicProcessHistoryInactiveHeadEl.innerHTML = "";
    }
    if (dynamicProcessHistoryInactiveBodyEl) {
      dynamicProcessHistoryInactiveBodyEl.innerHTML = "";
    }

    const normalizedFields = Array.isArray(sectionFields)
      ? sectionFields.filter((field) => field && typeof field === "object")
      : [];
    const tableFields = normalizedFields.filter((field) => String(field.key || "").trim());
    const sectionFieldKeys = new Set(
      tableFields
        .map((field) => normalizeMenuKey(field && field.key))
        .filter(Boolean)
    );
    const visibleRows = historyRows.filter((item) => {
      const rowSectionKey = String(item.section_key || "").trim().toLowerCase();
      if (!cleanSectionKey) {
        return true;
      }
      if (!rowSectionKey) {
        return true;
      }
      if (rowSectionKey === cleanSectionKey) {
        return true;
      }

      // Compatibilidade: registros legados foram gravados por campo (field:<key>)
      // e precisam continuar visíveis quando a seção atual passou a ser por header.
      if (rowSectionKey.startsWith("field:")) {
        const legacyFieldKey = normalizeMenuKey(rowSectionKey.slice("field:".length));
        if (legacyFieldKey && sectionFieldKeys.has(legacyFieldKey)) {
          return true;
        }
      }

      if (cleanSectionKey.startsWith("field:")) {
        const currentFieldKey = normalizeMenuKey(cleanSectionKey.slice("field:".length));
        if (currentFieldKey && rowSectionKey === currentFieldKey) {
          return true;
        }
      }

      if (sectionFieldKeys.size && sectionFieldKeys.has(normalizeMenuKey(rowSectionKey))) {
        return true;
      }

      return false;
    });
    const normalizedSingularLabel = normalizeLookupText(recordLabels.singular || "");
    const departmentHistoryMode = normalizedSingularLabel === "departamento";
    const showStateColumn = normalizedSingularLabel !== "ausencia";
    const singularLabel = toSentenceCaseText(recordLabels.singular || "registo").toLowerCase();
    const pluralLabel = toSentenceCaseText(recordLabels.plural || "registos").toLowerCase();

    const setLegacyHistoryState = (showTable, showEmpty = false) => {
      if (dynamicProcessHistoryTableEl) {
        dynamicProcessHistoryTableEl.style.display = showTable ? "" : "none";
      }
      if (dynamicProcessHistoryEmptyEl) {
        dynamicProcessHistoryEmptyEl.style.display = showEmpty ? "" : "none";
        dynamicProcessHistoryEmptyEl.textContent = `Sem ${pluralLabel} criados.`;
      }
    };

    const hideSeparatedHistoryCards = () => {
      if (dynamicProcessHistoryActiveCardEl) {
        dynamicProcessHistoryActiveCardEl.style.display = "none";
      }
      if (dynamicProcessHistoryInactiveCardEl) {
        dynamicProcessHistoryInactiveCardEl.style.display = "none";
      }
      if (dynamicProcessHistoryActiveTableEl) {
        dynamicProcessHistoryActiveTableEl.style.display = "none";
      }
      if (dynamicProcessHistoryInactiveTableEl) {
        dynamicProcessHistoryInactiveTableEl.style.display = "none";
      }
      if (dynamicProcessHistoryActiveEmptyEl) {
        dynamicProcessHistoryActiveEmptyEl.style.display = "none";
      }
      if (dynamicProcessHistoryInactiveEmptyEl) {
        dynamicProcessHistoryInactiveEmptyEl.style.display = "none";
      }
    };

    const getRowValues = (row) => (
      row && row.values && typeof row.values === "object"
        ? row.values
        : {}
    );

    const resolveRowState = (values) => {
      const rawStateValue = normalizeLookupText(values.__estado || "");
      return rawStateValue === "inativo" ? "inativo" : "ativo";
    };

    const resolveLinkHref = (rawValue) => {
      const cleanValue = String(rawValue || "").trim();
      if (!cleanValue) {
        return "";
      }
      if (/^https?:\/\//i.test(cleanValue)) {
        return cleanValue;
      }
      return `https://${cleanValue}`;
    };

    const createHeadRow = (headElement, includeStateColumn, includeCreatedColumn = false) => {
      if (!headElement) {
        return;
      }
      headElement.innerHTML = "";
      const headRowEl = document.createElement("tr");
      if (includeCreatedColumn) {
        const createdHeadEl = document.createElement("th");
        createdHeadEl.textContent = "Criado em";
        headRowEl.appendChild(createdHeadEl);
      }
      tableFields.forEach((field) => {
        const thEl = document.createElement("th");
        thEl.textContent = toSentenceCaseText(field.label || field.key);
        headRowEl.appendChild(thEl);
      });
      if (includeStateColumn) {
        const stateHeadEl = document.createElement("th");
        stateHeadEl.textContent = "Estado";
        headRowEl.appendChild(stateHeadEl);
      }
      const actionsHeadEl = document.createElement("th");
      actionsHeadEl.textContent = "Ações";
      headRowEl.appendChild(actionsHeadEl);
      headElement.appendChild(headRowEl);
    };

    const populateReadOnlyFromRow = (values) => {
      if (!dynamicProcessReadOnlyGridEl) {
        return;
      }
      dynamicProcessReadOnlyGridEl.innerHTML = "";
      tableFields.forEach((field) => {
        const fieldKey = normalizeMenuKey(field.key);
        const fieldType = normalizeProcessFieldType(field.fieldType);
        const itemEl = document.createElement("div");
        itemEl.className = "personal-item";

        const labelEl = document.createElement("span");
        labelEl.className = "personal-label";
        labelEl.textContent = toSentenceCaseText(field.label || field.key);

        const valueEl = document.createElement("strong");
        valueEl.className = "personal-value";
        const rawValue = String(values[fieldKey] || "").trim();
        if (fieldType === "flag") {
          valueEl.textContent = isTruthyFlagValue(rawValue) ? "Sim" : "Não";
        } else if (fieldType === "link" && rawValue) {
          const linkEl = document.createElement("a");
          linkEl.href = resolveLinkHref(rawValue);
          linkEl.target = "_blank";
          linkEl.rel = "noopener noreferrer";
          linkEl.textContent = rawValue;
          linkEl.style.textDecoration = "underline";
          valueEl.textContent = "";
          valueEl.appendChild(linkEl);
        } else {
          valueEl.textContent = rawValue || "-";
        }

        itemEl.appendChild(labelEl);
        itemEl.appendChild(valueEl);
        dynamicProcessReadOnlyGridEl.appendChild(itemEl);
      });

      if (showStateColumn) {
        const stateItemEl = document.createElement("div");
        stateItemEl.className = "personal-item";

        const stateLabelEl = document.createElement("span");
        stateLabelEl.className = "personal-label";
        stateLabelEl.textContent = "Estado";

        const stateValueEl = document.createElement("strong");
        stateValueEl.className = "personal-value";
        stateValueEl.textContent = resolveRowState(values) === "inativo" ? "Inativo" : "Ativo";

        stateItemEl.appendChild(stateLabelEl);
        stateItemEl.appendChild(stateValueEl);
        dynamicProcessReadOnlyGridEl.appendChild(stateItemEl);
      }
    };

    const openRecordForEdit = (rowRecordId, values) => {
      if (!rowRecordId || !dynamicProcessEditFormEl) {
        return;
      }
      if (dynamicProcessSongAiFlagInputEl) {
        dynamicProcessSongAiFlagInputEl.value = "0";
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
        dynamicProcessCardEl.classList.remove("dynamic-process-history-show-readonly");
      }
      if (dynamicProcessReadOnlyEl) {
        dynamicProcessReadOnlyEl.style.display = "none";
      }
      if (dynamicProcessCreateCardEl) {
        dynamicProcessCreateCardEl.classList.add("is-editing");
      }

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
          inputEl.checked = isTruthyFlagValue(rawValue);
          inputEl.dispatchEvent(new Event("input", { bubbles: true }));
          return;
        }
        if (inputEl.type === "file") {
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
          stateSelectEl.value = resolveRowState(values);
        }
      }

      dynamicProcessEditFormEl.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    const openRecordForView = (values) => {
      if (dynamicProcessSongAiFlagInputEl) {
        dynamicProcessSongAiFlagInputEl.value = "0";
      }
      populateReadOnlyFromRow(values);
      if (dynamicProcessHistoryActionInputEl) {
        dynamicProcessHistoryActionInputEl.value = "create";
      }
      if (dynamicProcessHistoryRecordIdInputEl) {
        dynamicProcessHistoryRecordIdInputEl.value = "";
      }
      if (dynamicProcessSubmitBtnEl) {
        dynamicProcessSubmitBtnEl.textContent = "Guardar";
      }
      if (dynamicProcessCardEl) {
        dynamicProcessCardEl.classList.remove("editing");
        dynamicProcessCardEl.classList.add("dynamic-process-history-show-readonly");
        dynamicProcessCardEl.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      if (dynamicProcessReadOnlyEl) {
        dynamicProcessReadOnlyEl.style.display = "";
      }
      if (dynamicProcessCreateCardEl) {
        dynamicProcessCreateCardEl.classList.remove("is-editing");
      }
    };

    const renderRows = (
      rows,
      bodyElement,
      includeStateColumn,
      allowDeleteForInactive,
      includeCreatedColumn = false
    ) => {
      if (!bodyElement) {
        return;
      }
      bodyElement.innerHTML = "";
      rows.forEach((row) => {
        const rowRecordId = String(row.record_id || "").trim();
        const values = getRowValues(row);
        const rowState = resolveRowState(values);

        const trEl = document.createElement("tr");
        if (includeCreatedColumn) {
          const createdCellEl = document.createElement("td");
          createdCellEl.textContent = String(row.created_at || "-").trim() || "-";
          trEl.appendChild(createdCellEl);
        }

        tableFields.forEach((field) => {
          const fieldKey = normalizeMenuKey(field.key);
          const fieldType = normalizeProcessFieldType(field.fieldType);
          const tdEl = document.createElement("td");
          const rawValue = String(values[fieldKey] || "").trim();
          if (fieldType === "flag") {
            tdEl.textContent = isTruthyFlagValue(rawValue) ? "Sim" : "Não";
          } else if (fieldType === "link" && rawValue) {
            const linkEl = document.createElement("a");
            linkEl.href = resolveLinkHref(rawValue);
            linkEl.target = "_blank";
            linkEl.rel = "noopener noreferrer";
            linkEl.textContent = rawValue;
            linkEl.style.textDecoration = "underline";
            tdEl.appendChild(linkEl);
          } else {
            tdEl.textContent = rawValue || "-";
          }
          trEl.appendChild(tdEl);
        });

        if (includeStateColumn) {
          const stateCellEl = document.createElement("td");
          const stateBadgeEl = document.createElement("span");
          const isInactiveState = rowState === "inativo";
          stateBadgeEl.className = `entity-status ${isInactiveState ? "entity-status-inactive" : "entity-status-active"}`;
          stateBadgeEl.textContent = isInactiveState ? "Inativo" : "Ativo";
          stateCellEl.appendChild(stateBadgeEl);
          trEl.appendChild(stateCellEl);
        }

        const actionsCellEl = document.createElement("td");
        const actionsWrapEl = document.createElement("div");
        actionsWrapEl.className = "table-actions";

        const viewBtnEl = document.createElement("button");
        viewBtnEl.type = "button";
        viewBtnEl.className = "table-icon-btn";
        viewBtnEl.title = `Exibir ${singularLabel}`;
        viewBtnEl.setAttribute("aria-label", `Exibir ${singularLabel}`);
        viewBtnEl.innerHTML = "&#128065;";
        viewBtnEl.disabled = !rowRecordId;
        viewBtnEl.addEventListener("click", () => {
          if (!rowRecordId) {
            return;
          }
          openRecordForView(values);
        });
        actionsWrapEl.appendChild(viewBtnEl);

        const editBtnEl = document.createElement("button");
        editBtnEl.type = "button";
        editBtnEl.className = "table-icon-btn";
        editBtnEl.title = `Editar ${singularLabel}`;
        editBtnEl.setAttribute("aria-label", `Editar ${singularLabel}`);
        editBtnEl.innerHTML = "&#9998;";
        editBtnEl.disabled = !rowRecordId;
        editBtnEl.addEventListener("click", () => {
          openRecordForEdit(rowRecordId, values);
        });
        actionsWrapEl.appendChild(editBtnEl);

        if (allowDeleteForInactive && (!includeStateColumn || rowState === "inativo")) {
          const deleteBtnEl = document.createElement("button");
          deleteBtnEl.type = "button";
          deleteBtnEl.className = "table-icon-btn table-icon-btn-danger";
          deleteBtnEl.title = `Eliminar ${singularLabel}`;
          deleteBtnEl.setAttribute("aria-label", `Eliminar ${singularLabel}`);
          deleteBtnEl.innerHTML = "&#128465;";
          deleteBtnEl.disabled = !rowRecordId;
          deleteBtnEl.addEventListener("click", () => {
            if (!rowRecordId || !dynamicProcessEditFormEl) {
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
        }

        actionsCellEl.appendChild(actionsWrapEl);
        trEl.appendChild(actionsCellEl);
        bodyElement.appendChild(trEl);
      });
    };

    if (!tableFields.length || !visibleRows.length) {
      if (showStateColumn) {
        setLegacyHistoryState(false, false);
        if (dynamicProcessHistoryActiveCardEl) {
          dynamicProcessHistoryActiveCardEl.style.display = "";
        }
        if (dynamicProcessHistoryInactiveCardEl) {
          dynamicProcessHistoryInactiveCardEl.style.display = "";
        }
        if (dynamicProcessHistoryTitleEl) {
          dynamicProcessHistoryTitleEl.textContent = `Lista de ${pluralLabel} criados`;
        }
        if (dynamicProcessHistoryActiveTitleEl) {
          dynamicProcessHistoryActiveTitleEl.textContent = `${toSentenceCaseText(pluralLabel)} ativos`;
        }
        if (dynamicProcessHistoryInactiveTitleEl) {
          dynamicProcessHistoryInactiveTitleEl.textContent = `${toSentenceCaseText(pluralLabel)} inativos`;
        }
        if (dynamicProcessHistoryActiveTableEl) {
          dynamicProcessHistoryActiveTableEl.style.display = "none";
        }
        if (dynamicProcessHistoryInactiveTableEl) {
          dynamicProcessHistoryInactiveTableEl.style.display = "none";
        }
        if (dynamicProcessHistoryActiveEmptyEl) {
          dynamicProcessHistoryActiveEmptyEl.style.display = "";
          dynamicProcessHistoryActiveEmptyEl.textContent = `Sem ${pluralLabel} ativos.`;
        }
        if (dynamicProcessHistoryInactiveEmptyEl) {
          dynamicProcessHistoryInactiveEmptyEl.style.display = "";
          dynamicProcessHistoryInactiveEmptyEl.textContent = `Sem ${pluralLabel} inativos.`;
        }
      } else {
        hideSeparatedHistoryCards();
        setLegacyHistoryState(false, true);
        if (dynamicProcessHistoryTitleEl) {
          dynamicProcessHistoryTitleEl.textContent = `Lista de ${pluralLabel} criados`;
        }
      }
      dynamicProcessHistoryBlockEl.style.display = showStateColumn ? "none" : "";
      return;
    }

    if (showStateColumn) {
      setLegacyHistoryState(false, false);
      if (dynamicProcessHistoryActiveCardEl) {
        dynamicProcessHistoryActiveCardEl.style.display = "";
      }
      if (dynamicProcessHistoryInactiveCardEl) {
        dynamicProcessHistoryInactiveCardEl.style.display = "";
      }
      if (dynamicProcessHistoryTitleEl) {
        dynamicProcessHistoryTitleEl.textContent = `Lista de ${pluralLabel} criados`;
      }
      const activeRows = visibleRows.filter((row) => resolveRowState(getRowValues(row)) !== "inativo");
      const inactiveRows = visibleRows.filter((row) => resolveRowState(getRowValues(row)) === "inativo");

      if (dynamicProcessHistoryActiveTitleEl) {
        dynamicProcessHistoryActiveTitleEl.textContent = `${toSentenceCaseText(pluralLabel)} ativos`;
      }
      if (dynamicProcessHistoryInactiveTitleEl) {
        dynamicProcessHistoryInactiveTitleEl.textContent = `${toSentenceCaseText(pluralLabel)} inativos`;
      }

      createHeadRow(dynamicProcessHistoryActiveHeadEl, true, false);
      createHeadRow(dynamicProcessHistoryInactiveHeadEl, true, false);
      renderRows(activeRows, dynamicProcessHistoryActiveBodyEl, true, false, false);
      renderRows(inactiveRows, dynamicProcessHistoryInactiveBodyEl, true, true, false);

      if (dynamicProcessHistoryActiveTableEl) {
        dynamicProcessHistoryActiveTableEl.style.display = activeRows.length ? "" : "none";
      }
      if (dynamicProcessHistoryInactiveTableEl) {
        dynamicProcessHistoryInactiveTableEl.style.display = inactiveRows.length ? "" : "none";
      }
      if (dynamicProcessHistoryActiveEmptyEl) {
        dynamicProcessHistoryActiveEmptyEl.style.display = activeRows.length ? "none" : "";
        dynamicProcessHistoryActiveEmptyEl.textContent = `Sem ${pluralLabel} ativos.`;
      }
      if (dynamicProcessHistoryInactiveEmptyEl) {
        dynamicProcessHistoryInactiveEmptyEl.style.display = inactiveRows.length ? "none" : "";
        dynamicProcessHistoryInactiveEmptyEl.textContent = `Sem ${pluralLabel} inativos.`;
      }
    } else {
      hideSeparatedHistoryCards();
      setLegacyHistoryState(true, false);
      createHeadRow(dynamicProcessHistoryHeadEl, false, false);
      renderRows(visibleRows, dynamicProcessHistoryBodyEl, false, true, false);
      if (dynamicProcessHistoryTitleEl) {
        dynamicProcessHistoryTitleEl.textContent = `Lista de ${pluralLabel} criados`;
      }
    }

    dynamicProcessHistoryBlockEl.style.display = showStateColumn ? "none" : "";
  }

  window.APPVERBO_RENDER_DYNAMIC_PROCESS_HISTORY_V1 = renderDynamicProcessHistory;
})();
