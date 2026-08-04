//###################################################################################
// (1) CAPTURA PARTILHADA DO CONTEXTO POS-SAVE
//###################################################################################

(function () {
  "use strict";

  const contract = window.AppGenesisPostSaveContextContractV1 || null;
  const stateByForm = new WeakMap();

  function getCurrentUrl() {
    return contract && typeof contract.getCurrentUrl === "function"
      ? contract.getCurrentUrl()
      : new URL(window.location.href);
  }

  function buildCapturedContext(form) {
    const currentUrl = getCurrentUrl();
    const action = String(form && (form.getAttribute("action") || form.action) || "").trim();
    const method = String(form && (form.getAttribute("method") || form.method || "post") || "post")
      .trim()
      .toLowerCase();

    return {
      url: currentUrl.pathname + currentUrl.search + currentUrl.hash,
      createdAt: Date.now(),
      action,
      method
    };
  }

  function normalizeText(value) {
    return String(value === null || value === undefined ? "" : value).trim();
  }

  function isPostForm(form) {
    return normalizeText(form && (form.getAttribute("method") || form.method || "post")).toLowerCase() === "post";
  }

  function getFormKey(form) {
    if (!form) {
      return "";
    }
    return normalizeText(form.getAttribute("action") || form.action || "") + "::" + normalizeText(form.getAttribute("method") || form.method || "post").toLowerCase();
  }

  function ensureHiddenInput(form, name, value) {
    if (!form || !name) {
      return null;
    }

    let input = form.querySelector(`input[name="${name}"]`);
    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }

    input.value = String(value || "");
    return input;
  }

  function captureForm(form) {
    if (!form || !isPostForm(form)) {
      return false;
    }

    const context = buildCapturedContext(form);
    const stored = contract && typeof contract.storeContext === "function"
      ? contract.storeContext(context)
      : false;

    if (stored) {
      ensureHiddenInput(form, "appgenesis_after_save", "1");
      ensureHiddenInput(form, "appgenesis_post_save_context", JSON.stringify(context));
    }

    return stored;
  }

  function bindForm(form) {
    if (!form || !isPostForm(form)) {
      return null;
    }

    const existing = stateByForm.get(form);
    if (existing && existing.bound) {
      return existing;
    }

    const handler = () => {
      captureForm(form);
    };

    form.addEventListener("submit", handler, true);
    const state = {
      bound: true,
      handler
    };
    stateByForm.set(form, state);
    return state;
  }

  function initialize(context) {
    const safeContext = context && typeof context === "object" ? context : {};
    const root = safeContext.root && typeof safeContext.root.querySelectorAll === "function" ? safeContext.root : document;
    const forms = Array.from(root.querySelectorAll("form")).filter(isPostForm);

    forms.forEach(bindForm);

    return {
      root,
      forms
    };
  }

  function destroy(context) {
    const safeContext = context && typeof context === "object" ? context : {};
    const root = safeContext.root && typeof safeContext.root.querySelectorAll === "function" ? safeContext.root : document;
    const forms = safeContext.forms || Array.from(root.querySelectorAll("form"));

    forms.forEach((form) => {
      const state = stateByForm.get(form);
      if (!state || !state.bound) {
        return;
      }
      form.removeEventListener("submit", state.handler, true);
      state.bound = false;
      stateByForm.delete(form);
    });

    return safeContext;
  }

  window.AppGenesisPostSaveContextCaptureV1 = {
    initialize,
    destroy,
    buildCapturedContext,
    captureForm,
    bindForm
  };
})();
