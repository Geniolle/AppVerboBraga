//###################################################################################
// (1) DYNAMIC PROCESS SILENT REFRESH V1
//###################################################################################
(function registerDynamicProcessSilentRefreshV1Module() {
  "use strict";

  const FORM_SELECTOR = "#dynamic-process-edit-form";
  const PROCESS_ACTION_SUFFIX = "/users/profile/process-data";
  const SILENT_REFRESH_HEADER = "X-AppVerbo-Silent-Refresh";

  //###################################################################################
  // (2) HELPERS
  //###################################################################################
  function normalizeText(value) {
    return String(value || "").trim();
  }

  function normalizeKey(value) {
    return normalizeText(value).toLowerCase();
  }

  function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function cloneJsonValue(value, fallbackValue) {
    try {
      return JSON.parse(JSON.stringify(value));
    } catch (_error) {
      return fallbackValue;
    }
  }

  function getCurrentUrl() {
    try {
      return new URL(window.location.href);
    } catch (_error) {
      return new URL("/users/new", window.location.origin);
    }
  }

  function getFormControlValue(form, name) {
    if (!form) {
      return "";
    }

    const control = form.querySelector(`[name="${name}"]`);
    if (!control) {
      return "";
    }

    return normalizeText(control.value);
  }

  function ensureBootstrapMap(mapKey) {
    const bootstrap = window.__APPVERBO_BOOTSTRAP__ && typeof window.__APPVERBO_BOOTSTRAP__ === "object"
      ? window.__APPVERBO_BOOTSTRAP__
      : (window.__APPVERBO_BOOTSTRAP__ = {});

    if (!isPlainObject(bootstrap[mapKey])) {
      bootstrap[mapKey] = {};
    }

    return bootstrap[mapKey];
  }

  function isDynamicProcessForm(form) {
    if (!form || form.matches(FORM_SELECTOR) === false) {
      return false;
    }

    const action = normalizeText(form.getAttribute("action") || form.action);
    const target = normalizeText(getFormControlValue(form, "target"));
    return action.endsWith(PROCESS_ACTION_SUFFIX) && target === "#dynamic-process-card";
  }

  function buildStableDynamicProcessUrl(form) {
    const currentUrl = getCurrentUrl();
    const menuKey = normalizeKey(
      getFormControlValue(form, "menu_key") ||
      currentUrl.searchParams.get("menu") ||
      (window.__APPVERBO_BOOTSTRAP__ || {}).initialMenu
    );
    const sectionKey = normalizeKey(
      getFormControlValue(form, "section_key") ||
      currentUrl.searchParams.get("dynamic_process_section") ||
      currentUrl.searchParams.get("section_key")
    );

    currentUrl.pathname = "/users/new";
    currentUrl.searchParams.delete("appverbo_after_save");
    currentUrl.searchParams.delete("profile_success");
    currentUrl.searchParams.delete("profile_error");

    if (menuKey) {
      currentUrl.searchParams.set("menu", menuKey);
    }

    currentUrl.searchParams.set("target", "#dynamic-process-card");

    if (sectionKey) {
      currentUrl.searchParams.set("dynamic_process_section", sectionKey);
      currentUrl.searchParams.set("section_key", sectionKey);
    } else {
      currentUrl.searchParams.delete("dynamic_process_section");
      currentUrl.searchParams.delete("section_key");
    }

    currentUrl.hash = "#dynamic-process-card";
    return currentUrl.pathname + currentUrl.search + currentUrl.hash;
  }

  function replaceCurrentUrl(nextUrl) {
    const cleanUrl = normalizeText(nextUrl);
    if (!cleanUrl || !window.history || typeof window.history.replaceState !== "function") {
      return;
    }

    window.history.replaceState(window.history.state, document.title, cleanUrl);
  }

  function fallbackToNavigation(fallbackUrl, form) {
    const cleanUrl = normalizeText(fallbackUrl);
    if (cleanUrl) {
      window.location.assign(cleanUrl);
      return;
    }

    if (form && typeof form.__appverboSilentRefreshNativeSubmitV1 === "function") {
      form.__appverboSilentRefreshNativeSubmitV1();
      return;
    }

    window.location.reload();
  }

  function setSubmittingState(form, isSubmitting) {
    if (!form) {
      return;
    }

    const submitBtn = document.getElementById("dynamic-process-submit-btn");
    if (!submitBtn) {
      return;
    }

    if (isSubmitting) {
      submitBtn.dataset.appverboSilentRefreshPrevDisabledV1 = submitBtn.disabled ? "1" : "0";
      submitBtn.disabled = true;
      return;
    }

    submitBtn.disabled = submitBtn.dataset.appverboSilentRefreshPrevDisabledV1 === "1";
    delete submitBtn.dataset.appverboSilentRefreshPrevDisabledV1;
  }

  function applyTopbarSavingState() {
    if (typeof window.APPVERBO_SET_TOPBAR_FEEDBACK_STATE_V1 === "function") {
      window.APPVERBO_SET_TOPBAR_FEEDBACK_STATE_V1("saving", "A atualizar...");
    }
  }

  function applyTopbarSuccessState(title) {
    if (typeof window.APPVERBO_MARK_TOPBAR_FEEDBACK_SYNCED_V1 === "function") {
      window.APPVERBO_MARK_TOPBAR_FEEDBACK_SYNCED_V1(title);
    }
  }

  function syncRuntimeMaps(payload) {
    const menuKey = normalizeKey(payload && payload.menuKey);
    if (!menuKey) {
      return;
    }

    const valuesMap = ensureBootstrapMap("menuProcessValuesMap");
    const historyMap = ensureBootstrapMap("menuProcessHistoryMap");
    const quantityMap = ensureBootstrapMap("menuProcessQuantityValuesMap");

    valuesMap[menuKey] = isPlainObject(payload.valuesByField)
      ? cloneJsonValue(payload.valuesByField, {})
      : {};
    historyMap[menuKey] = Array.isArray(payload.historyRows)
      ? cloneJsonValue(payload.historyRows, [])
      : [];
    quantityMap[menuKey] = isPlainObject(payload.quantityValuesByRule)
      ? cloneJsonValue(payload.quantityValuesByRule, {})
      : {};
  }

  function rerenderDynamicProcess(payload, form) {
    const menuKey = normalizeKey(
      payload && payload.menuKey
        ? payload.menuKey
        : getFormControlValue(form, "menu_key")
    );
    const sectionKey = normalizeKey(
      payload && payload.sectionKey
        ? payload.sectionKey
        : getFormControlValue(form, "section_key")
    );

    if (typeof window.renderDynamicProcessCard !== "function" || !menuKey) {
      return false;
    }

    window.renderDynamicProcessCard(menuKey, sectionKey, {
      preserveInteractionState: false
    });
    return true;
  }

  //###################################################################################
  // (3) SILENT SUBMIT
  //###################################################################################
  async function submitDynamicProcessSilently(form) {
    if (!form || form.dataset.appverboSilentRefreshBusyV1 === "1") {
      return;
    }

    form.dataset.appverboSilentRefreshBusyV1 = "1";
    setSubmittingState(form, true);
    applyTopbarSavingState();

    const stableUrl = buildStableDynamicProcessUrl(form);
    const requestUrl = normalizeText(form.getAttribute("action") || form.action) || PROCESS_ACTION_SUFFIX;
    const formData = new FormData(form);
    formData.set("return_url", stableUrl);
    formData.set("appverbo_after_save", "1");

    try {
      const response = await fetch(requestUrl, {
        method: "POST",
        body: formData,
        credentials: "same-origin",
        headers: {
          [SILENT_REFRESH_HEADER]: "1",
          "X-Requested-With": "XMLHttpRequest",
          Accept: "application/json"
        }
      });
      const contentType = normalizeText(response.headers.get("content-type")).toLowerCase();

      if (!contentType.includes("application/json")) {
        fallbackToNavigation(response.url || stableUrl, form);
        return;
      }

      const payload = await response.json();
      if (!response.ok || !payload || payload.success !== true) {
        fallbackToNavigation(
          normalizeText((payload && (payload.redirectUrl || payload.stableUrl)) || response.url || stableUrl),
          form
        );
        return;
      }

      syncRuntimeMaps(payload);
      replaceCurrentUrl(payload.stableUrl || stableUrl);

      if (!rerenderDynamicProcess(payload, form)) {
        fallbackToNavigation(payload.stableUrl || stableUrl, form);
        return;
      }

      applyTopbarSuccessState(payload.message || "Dados atualizados com sucesso.");
    } catch (_error) {
      fallbackToNavigation(stableUrl, form);
      return;
    } finally {
      form.dataset.appverboSilentRefreshBusyV1 = "0";
      setSubmittingState(form, false);
    }
  }

  //###################################################################################
  // (4) INIT
  //###################################################################################
  function patchDynamicProcessFormSubmit(form) {
    if (!form || form.__appverboSilentRefreshPatchedV1 === true) {
      return;
    }

    form.__appverboSilentRefreshPatchedV1 = true;
    form.__appverboSilentRefreshNativeSubmitV1 = form.submit.bind(form);
    form.submit = function patchedDynamicProcessSubmitV1() {
      if (!isDynamicProcessForm(form)) {
        form.__appverboSilentRefreshNativeSubmitV1();
        return;
      }

      void submitDynamicProcessSilently(form);
    };
  }

  function initDynamicProcessSilentRefreshV1() {
    const form = document.querySelector(FORM_SELECTOR);
    if (!form) {
      return;
    }

    patchDynamicProcessFormSubmit(form);

    document.addEventListener("submit", function handleDynamicProcessSilentSubmitV1(event) {
      const submittedForm = event.target;
      if (!isDynamicProcessForm(submittedForm)) {
        return;
      }

      event.preventDefault();
      void submitDynamicProcessSilently(submittedForm);
    }, true);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDynamicProcessSilentRefreshV1, { once: true });
  } else {
    initDynamicProcessSilentRefreshV1();
  }
})();
