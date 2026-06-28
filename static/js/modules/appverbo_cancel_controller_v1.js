//###################################################################################
// APPVERBO - GLOBAL CANCEL CONTROLLER V1
//###################################################################################

(function (window, document) {
  "use strict";

  if (window.AppVerboCancelControllerV1) {
    return;
  }

  //###################################################################################
  // (1) CONSTANTES
  //###################################################################################

  const CANCEL_TRIGGER_SELECTOR_V1 = [
    "[data-appverbo-cancel]",
    "[data-appverbo-cancel-target]",
    "[data-edit-cancel]",
    ".profile-cancel-btn",
    ".action-btn-cancel"
  ].join(", ");

  const LOCAL_EDITOR_CANCEL_SELECTOR_V1 = [
    "[data-additional-field-editor-cancel]",
    "[data-process-fields-config-cancel]",
    "[data-process-list-editor-cancel]",
    "[data-process-quantity-editor-cancel]",
    "[data-process-subsequent-field-cancel]",
    ".process-fields-config-cancel-v6",
    ".appverbo-sidebar-section-cancel-btn-v3",
    ".appverbo-create-entry-cancel-btn-v1",
    ".appverbo-create-entry-cancel-btn-v5",
    ".appverbo-sidebar-section-edit-cancel-v8",
    ".appverbo-sidebar-section-edit-cancel-v9"
  ].join(", ");

  const DETAILS_SELECTOR_V1 = [
    "details.entity-create-collapse",
    "details.admin-subprocess-create-collapse-v1",
    "details.appverbo-process-action-details-v1",
    "details"
  ].join(", ");

  //###################################################################################
  // (2) HELPERS
  //###################################################################################

  function normalizeTextV1(value) {
    return String(value || "").trim();
  }

  function normalizeLookupV1(value) {
    return normalizeTextV1(value)
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function normalizeSelectorV1(value) {
    const rawValue = normalizeTextV1(value);

    if (!rawValue) {
      return "";
    }

    if (/^[#.\[]/.test(rawValue)) {
      return rawValue;
    }

    return "#" + rawValue;
  }

  function getClosestV1(element, selector) {
    if (!element || typeof element.closest !== "function") {
      return null;
    }

    return element.closest(selector);
  }

  function matchesV1(element, selector) {
    return Boolean(
      element &&
      typeof element.matches === "function" &&
      element.matches(selector)
    );
  }

  function getElementBySelectorV1(selector, ownerDocument) {
    const safeSelector = normalizeSelectorV1(selector);
    const safeDocument = ownerDocument || document;

    if (!safeSelector) {
      return null;
    }

    try {
      return safeDocument.querySelector(safeSelector);
    } catch (error) {
      return null;
    }
  }

  function isVisualCancelTriggerV1(trigger) {
    if (!trigger) {
      return false;
    }

    if (
      matchesV1(trigger, "[data-appverbo-cancel], [data-appverbo-cancel-target], [data-edit-cancel], .profile-cancel-btn")
    ) {
      return true;
    }

    if (!matchesV1(trigger, ".action-btn-cancel")) {
      return false;
    }

    const label = normalizeLookupV1(trigger.textContent);
    return label === "cancelar" || label === "fechar";
  }

  function resolveCancelTriggerV1(element) {
    const trigger = getClosestV1(element, CANCEL_TRIGGER_SELECTOR_V1);

    if (!isVisualCancelTriggerV1(trigger)) {
      return null;
    }

    return trigger;
  }

  function resolveExplicitContextV1(trigger) {
    if (!trigger) {
      return null;
    }

    return getElementBySelectorV1(
      trigger.getAttribute("data-appverbo-cancel-target") ||
      trigger.getAttribute("data-edit-cancel"),
      trigger.ownerDocument || document
    );
  }

  function resolveReturnTargetV1(trigger) {
    if (!trigger) {
      return null;
    }

    return getElementBySelectorV1(
      trigger.getAttribute("data-appverbo-cancel-return-target"),
      trigger.ownerDocument || document
    );
  }

  function resolveCancelContextV1(trigger) {
    if (!trigger) {
      return null;
    }

    return (
      resolveExplicitContextV1(trigger) ||
      getClosestV1(
        trigger,
        [
          "[data-process-fields-config-editor-block]",
          "[data-additional-field-editor-block]",
          ".profile-edit-form",
          "[data-admin-subprocess-role='form']",
          DETAILS_SELECTOR_V1,
          ".card",
          "form"
        ].join(", ")
      ) ||
      trigger
    );
  }

  function resolveCardV1(element) {
    return getClosestV1(element, ".card");
  }

  function resolveDetailsV1(element) {
    return getClosestV1(element, DETAILS_SELECTOR_V1);
  }

  function resolveFormV1(trigger, context) {
    if (matchesV1(trigger, LOCAL_EDITOR_CANCEL_SELECTOR_V1)) {
      return null;
    }

    if (matchesV1(context, ".profile-edit-form")) {
      return context;
    }

    if (matchesV1(context, "form")) {
      return context;
    }

    const contextProfileForm = context && typeof context.querySelector === "function"
      ? context.querySelector(".profile-edit-form")
      : null;

    if (contextProfileForm) {
      return contextProfileForm;
    }

    return getClosestV1(trigger, "form");
  }

  function hideCardV1(card) {
    if (!card) {
      return;
    }

    card.style.display = "none";
    card.setAttribute("aria-hidden", "true");
  }

  function showCardV1(card) {
    if (!card) {
      return;
    }

    card.style.display = "";
    card.hidden = false;
    card.removeAttribute("hidden");
    card.setAttribute("aria-hidden", "false");
  }

  function replaceHistoryUrlV1(rawUrl) {
    if (!rawUrl || !window.history || typeof window.history.replaceState !== "function") {
      return;
    }

    try {
      const nextUrl = new URL(rawUrl, window.location.origin);
      const nextPath = nextUrl.pathname + nextUrl.search + nextUrl.hash;
      window.history.replaceState(window.history.state, document.title, nextPath);
    } catch (error) {
      // Ignore malformed return URLs.
    }
  }

  function shouldExitEditingModeV1(trigger, card) {
    return Boolean(
      matchesV1(trigger, "[data-appverbo-cancel], [data-edit-cancel], .profile-cancel-btn") ||
      (card && card.classList && card.classList.contains("editing"))
    );
  }

  function syncKnownHelpersV1(detail) {
    const card = detail.card;

    if (
      card &&
      card.id === "create-user-card" &&
      typeof window.AppVerboSyncUserCreateActionModeV1 === "function"
    ) {
      window.AppVerboSyncUserCreateActionModeV1(document);
    }
  }

  function dispatchCancelledEventV1(detail) {
    const cancelEvent = new CustomEvent("appverbo:cancelled", {
      bubbles: true,
      detail
    });

    document.dispatchEvent(cancelEvent);
  }

  //###################################################################################
  // (3) API PUBLICA
  //###################################################################################

  function resetFormV1(form) {
    if (!form || typeof form.reset !== "function") {
      return false;
    }

    form.reset();
    return true;
  }

  function closeDetailsV1(details) {
    if (!details || typeof details.open !== "boolean") {
      return false;
    }

    const summary = details.querySelector("summary");
    details.open = false;

    if (summary && typeof summary.focus === "function") {
      summary.focus();
    }

    return true;
  }

  function closeCardV1(card, options) {
    if (!card) {
      return false;
    }

    const safeOptions = options || {};

    if (card.classList) {
      card.classList.remove("editing");
    }

    if (safeOptions.hide === true) {
      hideCardV1(card);
      return true;
    }

    if (safeOptions.show === true) {
      showCardV1(card);
      return true;
    }

    return true;
  }

  function closeAllOpenEditorsV1(root) {
    const scope = root || document;

    if (!scope || typeof scope.querySelectorAll !== "function") {
      return 0;
    }

    const cards = Array.from(scope.querySelectorAll(".card.editing"));

    cards.forEach(function (card) {
      closeCardV1(card);
      const profileForm = card.querySelector(".profile-edit-form");
      if (profileForm) {
        resetFormV1(profileForm);
      }
    });

    return cards.length;
  }

  function cancelFromElementV1(element) {
    const trigger = resolveCancelTriggerV1(element);

    if (!trigger) {
      return false;
    }

    const context = resolveCancelContextV1(trigger);
    const returnTarget = resolveReturnTargetV1(trigger);
    const card = resolveCardV1(context) || resolveCardV1(trigger);
    const details = resolveDetailsV1(context) || resolveDetailsV1(trigger);
    const form = resolveFormV1(trigger, context);
    const localEditorOnly = matchesV1(trigger, LOCAL_EDITOR_CANCEL_SELECTOR_V1);
    const shouldHideCurrentCard = Boolean(returnTarget && card && returnTarget !== card);

    if (!localEditorOnly && form) {
      resetFormV1(form);
    }

    if (details) {
      closeDetailsV1(details);
    }

    if (shouldExitEditingModeV1(trigger, card)) {
      closeCardV1(card, { hide: shouldHideCurrentCard });
    } else if (shouldHideCurrentCard) {
      hideCardV1(card);
    }

    if (returnTarget) {
      showCardV1(resolveCardV1(returnTarget) || returnTarget);
    }

    replaceHistoryUrlV1(trigger.getAttribute("data-appverbo-cancel-return-url"));

    const detail = {
      trigger,
      context,
      form,
      card,
      details,
      returnTarget,
      localEditorOnly
    };

    syncKnownHelpersV1(detail);
    dispatchCancelledEventV1(detail);

    return true;
  }

  //###################################################################################
  // (4) EVENT DELEGATION
  //###################################################################################

  document.addEventListener("click", function (event) {
    const trigger = resolveCancelTriggerV1(event.target);

    if (!trigger) {
      return;
    }

    event.preventDefault();
    cancelFromElementV1(trigger);
  });

  window.AppVerboCancelControllerV1 = {
    cancelFromElement: cancelFromElementV1,
    closeCard: closeCardV1,
    resetForm: resetFormV1,
    closeDetails: closeDetailsV1,
    closeAllOpenEditors: closeAllOpenEditorsV1
  };
})(window, document);
