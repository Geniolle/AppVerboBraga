//###################################################################################
// (1) SONG PROCESS UI V1
//###################################################################################
(function registerSongProcessUiV1() {
  "use strict";

  const filterState = {
    name: "",
    source: "",
    status: ""
  };

  const SOURCE_OPTIONS = ["manual", "youtube_transcript", "audio_transcription", "imported"];
  const STATUS_OPTIONS = ["rascunho", "revista", "aprovada"];
  const moduleState = {
    context: null
  };
  const SONG_FORM_LAYOUT_CLASS = "appverbo-song-grid-v1";
  const SONG_INLINE_FIELD_CLASS = "appverbo-song-inline-field-v1";
  const SONG_LYRICS_FIELD_CLASS = "appverbo-song-lyrics-field-v1";

  function normalizeLookupText(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function isSongProcessMenu(menuKey, menuLabel, sectionLabel) {
    const joined = [
      normalizeLookupText(menuKey),
      normalizeLookupText(menuLabel),
      normalizeLookupText(sectionLabel)
    ].filter(Boolean).join(" ");
    return joined.includes("musica");
  }

  function resolveSongFieldMap(sectionFields) {
    const fieldMap = {
      name: "",
      version: "",
      youtubeUrl: "",
      lyrics: "",
      source: "",
      status: ""
    };

    (Array.isArray(sectionFields) ? sectionFields : []).forEach((field) => {
      const fieldKey = String(field && field.key || "").trim().toLowerCase();
      const fieldLabel = String(field && field.label || fieldKey).trim();
      const lookup = `${normalizeLookupText(fieldKey)} ${normalizeLookupText(fieldLabel)}`.trim();
      if (!lookup) {
        return;
      }
      if (!fieldMap.name && lookup.includes("nome") && lookup.includes("musica")) {
        fieldMap.name = fieldKey;
        return;
      }
      if (!fieldMap.version && lookup.includes("versao")) {
        fieldMap.version = fieldKey;
        return;
      }
      if (!fieldMap.youtubeUrl && (lookup.includes("youtube") || lookup.includes("url") || lookup.includes("link"))) {
        fieldMap.youtubeUrl = fieldKey;
        return;
      }
      if (!fieldMap.source && lookup.includes("fonte") && lookup.includes("letra")) {
        fieldMap.source = fieldKey;
        return;
      }
      if (!fieldMap.status && lookup.includes("estado") && lookup.includes("letra")) {
        fieldMap.status = fieldKey;
        return;
      }
      if (!fieldMap.lyrics && lookup.includes("letra") && !lookup.includes("fonte") && !lookup.includes("estado")) {
        fieldMap.lyrics = fieldKey;
      }
    });

    return fieldMap;
  }

  function resolveTableColumnIndex(sectionFields, matcher) {
    const fields = Array.isArray(sectionFields) ? sectionFields : [];
    for (let index = 0; index < fields.length; index += 1) {
      const field = fields[index];
      if (matcher(field)) {
        return index;
      }
    }
    return -1;
  }

  function cleanupSongFormLayout(gridEl) {
    if (!gridEl) {
      return;
    }
    gridEl.classList.remove(SONG_FORM_LAYOUT_CLASS);
    Array.from(gridEl.children).forEach((childEl) => {
      childEl.classList.remove(SONG_INLINE_FIELD_CLASS, SONG_LYRICS_FIELD_CLASS);
    });
  }

  function resolveFieldContainerByInput(formEl, selector) {
    if (!formEl || !selector) {
      return null;
    }
    const inputEl = formEl.querySelector(selector);
    return inputEl ? inputEl.closest(".field") : null;
  }

  function applySongFormLayout(context) {
    if (!context || !context.dynamicProcessEditGridEl || !context.dynamicProcessEditFormEl) {
      return;
    }

    const { dynamicProcessEditGridEl, dynamicProcessEditFormEl, sectionFields } = context;
    const fieldMap = resolveSongFieldMap(sectionFields);
    const orderedFieldContainers = [
      resolveFieldContainerByInput(dynamicProcessEditFormEl, fieldMap.name ? `[name="process_field__${fieldMap.name}"]` : ""),
      resolveFieldContainerByInput(dynamicProcessEditFormEl, fieldMap.version ? `[name="process_field__${fieldMap.version}"]` : ""),
      resolveFieldContainerByInput(dynamicProcessEditFormEl, fieldMap.youtubeUrl ? `[name="process_field__${fieldMap.youtubeUrl}"]` : ""),
      resolveFieldContainerByInput(dynamicProcessEditFormEl, fieldMap.source ? `[name="process_field__${fieldMap.source}"]` : ""),
      resolveFieldContainerByInput(dynamicProcessEditFormEl, fieldMap.status ? `[name="process_field__${fieldMap.status}"]` : ""),
      resolveFieldContainerByInput(dynamicProcessEditFormEl, `[name="process_state"]`),
      resolveFieldContainerByInput(dynamicProcessEditFormEl, fieldMap.lyrics ? `[name="process_field__${fieldMap.lyrics}"]` : "")
    ].filter((fieldContainerEl, index, items) => fieldContainerEl && items.indexOf(fieldContainerEl) === index);

    if (!orderedFieldContainers.length) {
      cleanupSongFormLayout(dynamicProcessEditGridEl);
      return;
    }

    cleanupSongFormLayout(dynamicProcessEditGridEl);
    dynamicProcessEditGridEl.classList.add(SONG_FORM_LAYOUT_CLASS);

    orderedFieldContainers.forEach((fieldContainerEl, index) => {
      fieldContainerEl.classList.add(
        index === orderedFieldContainers.length - 1 ? SONG_LYRICS_FIELD_CLASS : SONG_INLINE_FIELD_CLASS
      );
      dynamicProcessEditGridEl.appendChild(fieldContainerEl);
    });
  }

  function ensureSelectOptions(selectEl, values) {
    if (!selectEl) {
      return;
    }
    const currentValue = String(selectEl.value || "");
    const firstOptionEl = selectEl.querySelector("option[value='']");
    selectEl.innerHTML = "";
    if (firstOptionEl) {
      selectEl.appendChild(firstOptionEl);
    } else {
      const optionEl = document.createElement("option");
      optionEl.value = "";
      optionEl.textContent = "Todos";
      selectEl.appendChild(optionEl);
    }
    values.forEach((value) => {
      const optionEl = document.createElement("option");
      optionEl.value = value;
      optionEl.textContent = value;
      optionEl.selected = value === currentValue;
      selectEl.appendChild(optionEl);
    });
  }

  function setFeedback(message, tone) {
    const feedbackEl = document.getElementById("dynamic-process-song-feedback");
    if (!feedbackEl) {
      return;
    }
    feedbackEl.textContent = String(message || "");
    feedbackEl.classList.remove("is-error", "is-success");
    if (tone === "error") {
      feedbackEl.classList.add("is-error");
    }
    if (tone === "success") {
      feedbackEl.classList.add("is-success");
    }
  }

  function applyLyricsStatusBadges(tableEl, statusColumnIndex) {
    if (!tableEl || statusColumnIndex < 0) {
      return;
    }
    Array.from(tableEl.querySelectorAll("tbody tr")).forEach((rowEl) => {
      const statusCellEl = rowEl.children[statusColumnIndex];
      if (!statusCellEl) {
        return;
      }
      const rawStatus = String(statusCellEl.textContent || "").trim();
      const normalizedStatus = normalizeLookupText(rawStatus);
      if (!normalizedStatus) {
        return;
      }
      statusCellEl.innerHTML = "";
      const badgeEl = document.createElement("span");
      badgeEl.className = `appverbo-song-status-badge-v1 is-${normalizedStatus}`;
      badgeEl.textContent = rawStatus;
      statusCellEl.appendChild(badgeEl);
    });
  }

  function applySongFiltersToTable(tableEl, emptyEl, config) {
    if (!tableEl || !config) {
      return;
    }
    let visibleCount = 0;
    Array.from(tableEl.querySelectorAll("tbody tr")).forEach((rowEl) => {
      const nameCellEl = config.nameColumnIndex >= 0 ? rowEl.children[config.nameColumnIndex] : null;
      const sourceCellEl = config.sourceColumnIndex >= 0 ? rowEl.children[config.sourceColumnIndex] : null;
      const statusCellEl = config.statusColumnIndex >= 0 ? rowEl.children[config.statusColumnIndex] : null;

      const nameValue = normalizeLookupText(nameCellEl ? nameCellEl.textContent : "");
      const sourceValue = normalizeLookupText(sourceCellEl ? sourceCellEl.textContent : "");
      const statusValue = normalizeLookupText(statusCellEl ? statusCellEl.textContent : "");

      const matchesName = !filterState.name || nameValue.includes(filterState.name);
      const matchesSource = !filterState.source || sourceValue === filterState.source;
      const matchesStatus = !filterState.status || statusValue === filterState.status;
      const shouldShow = matchesName && matchesSource && matchesStatus;
      rowEl.style.display = shouldShow ? "" : "none";
      if (shouldShow) {
        visibleCount += 1;
      }
    });

    tableEl.style.display = visibleCount > 0 ? "" : "none";
    if (emptyEl) {
      emptyEl.style.display = visibleCount > 0 ? "none" : "";
      emptyEl.textContent = "Sem músicas para os filtros selecionados.";
    }
  }

  function applySongFiltersAndBadges(context) {
    if (!context) {
      return;
    }
    const nameColumnIndex = resolveTableColumnIndex(context.sectionFields, (field) => {
      const lookup = `${normalizeLookupText(field && field.key)} ${normalizeLookupText(field && field.label)}`.trim();
      return lookup.includes("nome") && lookup.includes("musica");
    });
    const sourceColumnIndex = resolveTableColumnIndex(context.sectionFields, (field) => {
      const lookup = `${normalizeLookupText(field && field.key)} ${normalizeLookupText(field && field.label)}`.trim();
      return lookup.includes("fonte") && lookup.includes("letra");
    });
    const statusColumnIndex = resolveTableColumnIndex(context.sectionFields, (field) => {
      const lookup = `${normalizeLookupText(field && field.key)} ${normalizeLookupText(field && field.label)}`.trim();
      return lookup.includes("estado") && lookup.includes("letra");
    });

    applyLyricsStatusBadges(
      document.getElementById("dynamic-process-history-active-table"),
      statusColumnIndex
    );
    applyLyricsStatusBadges(
      document.getElementById("dynamic-process-history-inactive-table"),
      statusColumnIndex
    );

    applySongFiltersToTable(
      document.getElementById("dynamic-process-history-active-table"),
      document.getElementById("dynamic-process-history-active-empty"),
      {
        nameColumnIndex,
        sourceColumnIndex,
        statusColumnIndex
      }
    );
    applySongFiltersToTable(
      document.getElementById("dynamic-process-history-inactive-table"),
      document.getElementById("dynamic-process-history-inactive-empty"),
      {
        nameColumnIndex,
        sourceColumnIndex,
        statusColumnIndex
      }
    );
  }

  async function handleGenerateLyricsClick() {
    const context = moduleState.context;
    if (!context || !context.dynamicProcessEditFormEl) {
      return;
    }

    const fieldMap = resolveSongFieldMap(context.sectionFields);
    const songNameInputEl = fieldMap.name
      ? context.dynamicProcessEditFormEl.querySelector(`[name="process_field__${fieldMap.name}"]`)
      : null;
    const versionInputEl = fieldMap.version
      ? context.dynamicProcessEditFormEl.querySelector(`[name="process_field__${fieldMap.version}"]`)
      : null;
    const youtubeInputEl = fieldMap.youtubeUrl
      ? context.dynamicProcessEditFormEl.querySelector(`[name="process_field__${fieldMap.youtubeUrl}"]`)
      : null;
    const lyricsInputEl = fieldMap.lyrics
      ? context.dynamicProcessEditFormEl.querySelector(`[name="process_field__${fieldMap.lyrics}"]`)
      : null;
    const sourceInputEl = fieldMap.source
      ? context.dynamicProcessEditFormEl.querySelector(`[name="process_field__${fieldMap.source}"]`)
      : null;
    const statusInputEl = fieldMap.status
      ? context.dynamicProcessEditFormEl.querySelector(`[name="process_field__${fieldMap.status}"]`)
      : null;
    const aiFlagInputEl = document.getElementById("dynamic-process-song-ai-flag");
    const buttonEl = document.getElementById("dynamic-process-song-ai-btn");

    if (!youtubeInputEl || !lyricsInputEl) {
      setFeedback("A configuração da música está incompleta para gerar a letra por IA.", "error");
      return;
    }

    const youtubeUrl = String(youtubeInputEl.value || "").trim();
    if (!youtubeUrl) {
      setFeedback("Informe a URL do YouTube antes de gerar a letra por IA.", "error");
      youtubeInputEl.focus();
      return;
    }

    if (buttonEl) {
      buttonEl.disabled = true;
      buttonEl.textContent = "A gerar...";
    }
    setFeedback("A preparar a transcrição do áudio...", "");

    try {
      const response = await fetch("/api/songs/transcribe-audio", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          youtubeUrl,
          songName: songNameInputEl ? String(songNameInputEl.value || "").trim() : "",
          version: versionInputEl ? String(versionInputEl.value || "").trim() : ""
        })
      });
      const payload = await response.json();
      if (!response.ok || !payload || payload.success !== true) {
        const errorParts = [];
        if (payload && payload.message) {
          errorParts.push(String(payload.message));
        }
        if (payload && payload.details) {
          errorParts.push(String(payload.details));
        }
        throw new Error(errorParts.join(" "));
      }

      lyricsInputEl.value = String(payload.lyrics || "");
      lyricsInputEl.dispatchEvent(new Event("input", { bubbles: true }));
      if (sourceInputEl) {
        sourceInputEl.value = "audio_transcription";
        sourceInputEl.dispatchEvent(new Event("change", { bubbles: true }));
      }
      if (statusInputEl) {
        statusInputEl.value = "rascunho";
        statusInputEl.dispatchEvent(new Event("change", { bubbles: true }));
      }
      if (aiFlagInputEl) {
        aiFlagInputEl.value = "1";
      }
      setFeedback("Letra gerada por IA. Reveja o texto antes de guardar.", "success");
    } catch (error) {
      setFeedback(error && error.message ? error.message : "Não foi possível transcrever esta música.", "error");
    } finally {
      if (buttonEl) {
        buttonEl.disabled = false;
        buttonEl.textContent = "Gerar letra por IA";
      }
    }
  }

  function bindFilterInputs() {
    const filterNameEl = document.getElementById("dynamic-process-song-filter-name");
    const filterSourceEl = document.getElementById("dynamic-process-song-filter-source");
    const filterStatusEl = document.getElementById("dynamic-process-song-filter-status");

    if (filterNameEl && !filterNameEl.dataset.songFilterBound) {
      filterNameEl.dataset.songFilterBound = "1";
      filterNameEl.addEventListener("input", () => {
        filterState.name = normalizeLookupText(filterNameEl.value);
        applySongFiltersAndBadges(moduleState.context);
      });
    }

    if (filterSourceEl && !filterSourceEl.dataset.songFilterBound) {
      filterSourceEl.dataset.songFilterBound = "1";
      filterSourceEl.addEventListener("change", () => {
        filterState.source = normalizeLookupText(filterSourceEl.value);
        applySongFiltersAndBadges(moduleState.context);
      });
    }

    if (filterStatusEl && !filterStatusEl.dataset.songFilterBound) {
      filterStatusEl.dataset.songFilterBound = "1";
      filterStatusEl.addEventListener("change", () => {
        filterState.status = normalizeLookupText(filterStatusEl.value);
        applySongFiltersAndBadges(moduleState.context);
      });
    }
  }

  function bindSongActions() {
    const buttonEl = document.getElementById("dynamic-process-song-ai-btn");
    const cancelButtonEl = document.querySelector("[data-edit-cancel='dynamic-process-card']");
    const createButtonEl = document.getElementById("dynamic-process-edit-toggle");
    const headerEditButtonEl = document.getElementById("dynamic-process-header-edit-toggle");
    const aiFlagInputEl = document.getElementById("dynamic-process-song-ai-flag");
    if (buttonEl && !buttonEl.dataset.songActionBound) {
      buttonEl.dataset.songActionBound = "1";
      buttonEl.addEventListener("click", handleGenerateLyricsClick);
    }
    [cancelButtonEl, createButtonEl, headerEditButtonEl].forEach((controlEl) => {
      if (!controlEl || controlEl.dataset.songResetBound === "1") {
        return;
      }
      controlEl.dataset.songResetBound = "1";
      controlEl.addEventListener("click", () => {
        if (aiFlagInputEl) {
          aiFlagInputEl.value = "0";
        }
      });
    });
  }

  window.APPVERBO_APPLY_SONG_PROCESS_UI_V1 = function applySongProcessUiV1(options = {}) {
    const {
      menuKey,
      menuLabel,
      sectionLabel,
      sectionFields = [],
      historyProcessMode = false,
      dynamicProcessEditFormEl = null
    } = options;

    const isSongMode = isSongProcessMenu(menuKey, menuLabel, sectionLabel);
    const toolsEl = document.getElementById("dynamic-process-song-tools");
    const filtersEl = document.getElementById("dynamic-process-song-filters");
    const aiFlagInputEl = document.getElementById("dynamic-process-song-ai-flag");
    const filterSourceEl = document.getElementById("dynamic-process-song-filter-source");
    const filterStatusEl = document.getElementById("dynamic-process-song-filter-status");

    moduleState.context = {
      ...options,
      sectionFields,
      dynamicProcessEditFormEl
    };

    if (!isSongMode) {
      cleanupSongFormLayout(options.dynamicProcessEditGridEl || null);
      if (toolsEl) {
        toolsEl.style.display = "none";
      }
      if (filtersEl) {
        filtersEl.style.display = "none";
      }
      if (aiFlagInputEl) {
        aiFlagInputEl.value = "0";
      }
      setFeedback("", "");
      return;
    }

    if (toolsEl) {
      toolsEl.style.display = "";
    }
    if (aiFlagInputEl) {
      aiFlagInputEl.value = "0";
    }
    if (filtersEl) {
      filtersEl.style.display = historyProcessMode ? "" : "none";
    }
    applySongFormLayout(moduleState.context);
    ensureSelectOptions(filterSourceEl, SOURCE_OPTIONS);
    ensureSelectOptions(filterStatusEl, STATUS_OPTIONS);
    bindSongActions();
    bindFilterInputs();
    applySongFiltersAndBadges(moduleState.context);
  };
})();
