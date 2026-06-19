//###################################################################################
// (1) TOPBAR SAVE FEEDBACK V1
//###################################################################################
(function registerTopbarSaveFeedbackV1Module() {
  "use strict";

  const SUCCESS_HIGHLIGHT_MS = 2200;
  const FEEDBACK_SELECTOR = "[data-appverbo-topbar-feedback]";
  const TEXT_SELECTOR = "[data-appverbo-topbar-feedback-text]";
  const STORAGE_LABEL_KEY = "appverbo:topbar_feedback:last_label";
  const STORAGE_TITLE_KEY = "appverbo:topbar_feedback:last_title";
  const SAVE_LABELS = new Set([
    "gravar",
    "guardar",
    "salvar",
    "gravar alteracoes",
    "guardar alteracoes",
    "salvar alteracoes",
    "criar",
    "atualizar",
    "enviar convite"
  ]);

  //###################################################################################
  // (2) UTILITARIOS
  //###################################################################################
  function normalizeText(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function isPostForm(form) {
    return normalizeText(form && form.getAttribute("method")) === "post";
  }

  function isSaveSubmitter(submitter) {
    if (!submitter) {
      return false;
    }

    const normalizedText = normalizeText(
      submitter.textContent ||
      submitter.value ||
      submitter.getAttribute("aria-label") ||
      ""
    );

    return SAVE_LABELS.has(normalizedText);
  }

  function formatCurrentTimestampLabel() {
    const formatter = new Intl.DateTimeFormat("pt-PT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });

    return "\u00daltima atualiza\u00e7\u00e3o: " + formatter.format(new Date());
  }

  function clearHighlightTimer(rootEl) {
    if (!rootEl || !rootEl.__appverboTopbarHighlightTimerV1) {
      return;
    }

    window.clearTimeout(rootEl.__appverboTopbarHighlightTimerV1);
    rootEl.__appverboTopbarHighlightTimerV1 = 0;
  }

  //###################################################################################
  // (3) ESTADO VISUAL
  //###################################################################################
  function applyFeedbackState(rootEl, state, label, title) {
    if (!rootEl) {
      return;
    }

    const textEl = rootEl.querySelector(TEXT_SELECTOR);
    const nextState = normalizeText(state) || "idle";
    const idleLabel = String(rootEl.dataset.feedbackIdleLabel || "Sem atualiza\u00e7\u00f5es recentes").trim();
    const nextLabel = String(label || "").trim() || idleLabel;
    const nextTitle = String(title || nextLabel).trim() || idleLabel;

    clearHighlightTimer(rootEl);
    rootEl.dataset.feedbackState = nextState;
    rootEl.setAttribute("title", nextTitle);

    if (textEl) {
      textEl.textContent = nextLabel;
    }
  }

  function persistSyncedState(label, title) {
    try {
      sessionStorage.setItem(STORAGE_LABEL_KEY, String(label || "").trim());
      sessionStorage.setItem(STORAGE_TITLE_KEY, String(title || "").trim());
    } catch (_error) {
    }
  }

  function readPersistedSyncedState() {
    try {
      return {
        label: String(sessionStorage.getItem(STORAGE_LABEL_KEY) || "").trim(),
        title: String(sessionStorage.getItem(STORAGE_TITLE_KEY) || "").trim()
      };
    } catch (_error) {
      return {
        label: "",
        title: ""
      };
    }
  }

  function applySyncedState(rootEl, title) {
    const syncedLabel = formatCurrentTimestampLabel();
    const syncedTitle = String(title || "").trim() || syncedLabel;

    persistSyncedState(syncedLabel, syncedTitle);
    applyFeedbackState(rootEl, "success", syncedLabel, syncedTitle);

    rootEl.__appverboTopbarHighlightTimerV1 = window.setTimeout(function settleSyncedStateV1() {
      applyFeedbackState(rootEl, "synced", syncedLabel, syncedTitle);
    }, SUCCESS_HIGHLIGHT_MS);
  }

  //###################################################################################
  // (4) INICIALIZACAO
  //###################################################################################
  function initTopbarSaveFeedbackV1() {
    const rootEl = document.querySelector(FEEDBACK_SELECTOR);

    if (!rootEl || rootEl.dataset.appverboTopbarFeedbackBoundV1 === "1") {
      return;
    }

    rootEl.dataset.appverboTopbarFeedbackBoundV1 = "1";

    const initialState = String(rootEl.dataset.feedbackState || "idle").trim() || "idle";
    const initialMessage = String(rootEl.dataset.feedbackMessage || "").trim();
    const persistedState = readPersistedSyncedState();

    if (initialState === "success" && initialMessage) {
      applySyncedState(rootEl, initialMessage);
    } else if (persistedState.label) {
      applyFeedbackState(rootEl, "synced", persistedState.label, persistedState.title || persistedState.label);
    } else {
      applyFeedbackState(
        rootEl,
        "idle",
        rootEl.dataset.feedbackIdleLabel || "Sem atualiza\u00e7\u00f5es recentes"
      );
    }

    document.addEventListener(
      "submit",
      function handleTopbarSaveSubmitV1(event) {
        const form = event.target;
        const submitter = event.submitter || document.activeElement;

        if (!form || !isPostForm(form) || !isSaveSubmitter(submitter)) {
          return;
        }

        applyFeedbackState(
          rootEl,
          "saving",
          rootEl.dataset.feedbackSavingLabel || "A atualizar..."
        );
      },
      true
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTopbarSaveFeedbackV1, { once: true });
  } else {
    initTopbarSaveFeedbackV1();
  }
})();
