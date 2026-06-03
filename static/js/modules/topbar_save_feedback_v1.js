//###################################################################################
// (1) TOPBAR SAVE FEEDBACK V1
//###################################################################################
(function registerTopbarSaveFeedbackV1Module() {
  "use strict";

  const SUCCESS_HIGHLIGHT_MS = 3200;
  const ERROR_HIGHLIGHT_MS = 4200;
  const FEEDBACK_SELECTOR = "[data-appverbo-topbar-feedback]";
  const TEXT_SELECTOR = "[data-appverbo-topbar-feedback-text]";
  const ICON_SELECTOR = "[data-appverbo-topbar-feedback-icon]";
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

  function clearHighlightTimer(rootEl) {
    if (!rootEl || !rootEl.__appverboTopbarHighlightTimerV1) {
      return;
    }

    window.clearTimeout(rootEl.__appverboTopbarHighlightTimerV1);
    rootEl.__appverboTopbarHighlightTimerV1 = 0;
  }

  function promoteFeedbackToBody(rootEl) {
    if (!rootEl || !document.body) {
      return;
    }

    if (rootEl.parentElement === document.body) {
      return;
    }

    document.body.appendChild(rootEl);
  }

  //###################################################################################
  // (3) ESTADO VISUAL
  //###################################################################################
  function resolveIconByState(state) {
    const cleanState = normalizeText(state);

    if (cleanState === "saving") {
      return "\u21bb";
    }

    if (cleanState === "error") {
      return "!";
    }

    return "\u2713";
  }

  function hideFeedback(rootEl) {
    if (!rootEl) {
      return;
    }

    clearHighlightTimer(rootEl);
    rootEl.dataset.feedbackVisible = "false";
    rootEl.dataset.feedbackState = "idle";
    rootEl.setAttribute("aria-hidden", "true");
  }

  function applyFeedbackState(rootEl, state, label, title) {
    if (!rootEl) {
      return;
    }

    const textEl = rootEl.querySelector(TEXT_SELECTOR);
    const iconEl = rootEl.querySelector(ICON_SELECTOR);
    const nextState = normalizeText(state) || "idle";
    const idleLabel = String(rootEl.dataset.feedbackIdleLabel || "Sem atualiza\u00e7\u00f5es recentes").trim();
    const nextLabel = String(label || "").trim() || idleLabel;
    const nextTitle = String(title || nextLabel).trim() || idleLabel;
    const shouldShow = nextState !== "idle" && Boolean(String(nextLabel || "").trim());

    clearHighlightTimer(rootEl);
    rootEl.dataset.feedbackState = nextState;
    rootEl.dataset.feedbackVisible = shouldShow ? "true" : "false";
    rootEl.setAttribute("title", nextTitle);
    rootEl.setAttribute("aria-hidden", shouldShow ? "false" : "true");

    if (textEl) {
      textEl.textContent = nextLabel;
    }

    if (iconEl) {
      iconEl.innerHTML = resolveIconByState(nextState);
    }

    if (!shouldShow) {
      return;
    }

    if (nextState === "success" || nextState === "synced") {
      rootEl.__appverboTopbarHighlightTimerV1 = window.setTimeout(function hideSuccessToastV1() {
        hideFeedback(rootEl);
      }, SUCCESS_HIGHLIGHT_MS);
      return;
    }

    if (nextState === "error") {
      rootEl.__appverboTopbarHighlightTimerV1 = window.setTimeout(function hideErrorToastV1() {
        hideFeedback(rootEl);
      }, ERROR_HIGHLIGHT_MS);
    }
  }

  function applySyncedState(rootEl, title) {
    const syncedLabel = String(title || rootEl.dataset.feedbackSuccessLabel || "Atualizado com sucesso.").trim();
    const syncedTitle = String(title || "").trim() || syncedLabel;

    applyFeedbackState(rootEl, "success", syncedLabel, syncedTitle);
  }

  //###################################################################################
  // (4) API GLOBAL
  //###################################################################################
  function exposeTopbarFeedbackApi(rootEl) {
    window.APPVERBO_SET_TOPBAR_FEEDBACK_STATE_V1 = function setTopbarFeedbackStateV1(state, label, title) {
      applyFeedbackState(rootEl, state, label, title);
    };

    window.APPVERBO_MARK_TOPBAR_FEEDBACK_SYNCED_V1 = function markTopbarFeedbackSyncedV1(title) {
      applySyncedState(rootEl, title);
    };
  }

  //###################################################################################
  // (5) INICIALIZACAO
  //###################################################################################
  function initTopbarSaveFeedbackV1() {
    const rootEl = document.querySelector(FEEDBACK_SELECTOR);

    if (!rootEl || rootEl.dataset.appverboTopbarFeedbackBoundV1 === "1") {
      return;
    }

    promoteFeedbackToBody(rootEl);
    rootEl.dataset.appverboTopbarFeedbackBoundV1 = "1";
    exposeTopbarFeedbackApi(rootEl);

    const initialState = String(rootEl.dataset.feedbackState || "idle").trim() || "idle";
    const initialMessage = String(rootEl.dataset.feedbackMessage || "").trim();
    if (initialState === "success" && initialMessage) {
      applySyncedState(rootEl, initialMessage);
    } else {
      hideFeedback(rootEl);
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
