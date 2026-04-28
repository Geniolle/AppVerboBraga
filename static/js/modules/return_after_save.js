//###################################################################################
// (1) MANTER PAGINA / ABA APOS CLICAR EM GRAVAR
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) CONFIGURACAO
  //###################################################################################

  const STORAGE_KEY = "appverbo:return_after_save";
  const STORAGE_TIME_KEY = "appverbo:return_after_save_time";
  const MAX_AGE_MS = 15000;

  const MESSAGE_PARAMS = [
    "success",
    "error",
    "entity_success",
    "entity_error",
    "profile_success",
    "profile_error",
    "settings_success",
    "settings_error",
    "invite_link",
    "profile_tab",
    "admin_tab",
    "settings_tab",
    "settings_action",
    "settings_edit_key",
    "entity_edit_id",
    "user_edit_id",
    "entity_view",
    "user_view"
  ];

  //###################################################################################
  // (3) FUNCOES AUXILIARES
  //###################################################################################

  function normalizeText(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function getCurrentRelativeUrl() {
    return `${window.location.pathname}${window.location.search}${window.location.hash}`;
  }

  function isSaveSubmitter(submitter) {
    if (!submitter) {
      return false;
    }

    const text = normalizeText(submitter.textContent || submitter.value || "");

    return (
      text === "gravar" ||
      text === "guardar" ||
      text === "salvar" ||
      text === "gravar alteracoes" ||
      text === "guardar alteracoes" ||
      text === "enviar convite" ||
      text === "criar" ||
      text === "criar pasta" ||
      text === "criar conta"
    );
  }

  function isPostForm(form) {
    const method = normalizeText(form.getAttribute("method") || "get");
    return method === "post";
  }

  function isSafeReturnUrl(value) {
    const url = String(value || "").trim();

    if (!url) {
      return false;
    }

    if (!url.startsWith("/")) {
      return false;
    }

    if (url.startsWith("//")) {
      return false;
    }

    return true;
  }

  function mergeMessageParams(targetUrl, currentUrl) {
    const target = new URL(targetUrl, window.location.origin);
    const current = new URL(currentUrl, window.location.origin);

    MESSAGE_PARAMS.forEach(function (paramName) {
      const paramValue = current.searchParams.get(paramName);

      if (paramValue !== null && String(paramValue).trim() !== "") {
        target.searchParams.set(paramName, paramValue);
      }
    });

    return `${target.pathname}${target.search}${target.hash}`;
  }

  function shouldReturnToSavedUrl(savedUrl, currentUrl) {
    if (!isSafeReturnUrl(savedUrl)) {
      return false;
    }

    if (savedUrl === currentUrl) {
      return false;
    }

    const saved = new URL(savedUrl, window.location.origin);
    const current = new URL(currentUrl, window.location.origin);

    if (saved.pathname !== current.pathname) {
      return false;
    }

    const savedMenu = saved.searchParams.get("menu") || "";
    const currentMenu = current.searchParams.get("menu") || "";

    if (savedMenu && savedMenu !== currentMenu) {
      return true;
    }

    const savedAdminTab = saved.searchParams.get("admin_tab") || "";
    const currentAdminTab = current.searchParams.get("admin_tab") || "";

    if (savedAdminTab && savedAdminTab !== currentAdminTab) {
      return true;
    }

    const savedProfileTab = saved.searchParams.get("profile_tab") || "";
    const currentProfileTab = current.searchParams.get("profile_tab") || "";

    if (savedProfileTab && savedProfileTab !== currentProfileTab) {
      return true;
    }

    const savedSettingsKey = saved.searchParams.get("settings_edit_key") || "";
    const currentSettingsKey = current.searchParams.get("settings_edit_key") || "";

    if (savedSettingsKey && savedSettingsKey !== currentSettingsKey) {
      return true;
    }

    const savedHash = saved.hash || "";
    const currentHash = current.hash || "";

    if (savedHash && savedHash !== currentHash) {
      return true;
    }

    return false;
  }

  //###################################################################################
  // (4) GUARDAR PAGINA ANTES DO SUBMIT
  //###################################################################################

  document.addEventListener(
    "submit",
    function (event) {
      const form = event.target;

      if (!form || !isPostForm(form)) {
        return;
      }

      const submitter = event.submitter || document.activeElement;

      if (!isSaveSubmitter(submitter)) {
        return;
      }

      sessionStorage.setItem(STORAGE_KEY, getCurrentRelativeUrl());
      sessionStorage.setItem(STORAGE_TIME_KEY, String(Date.now()));
    },
    true
  );

  //###################################################################################
  // (5) VOLTAR PARA A PAGINA ORIGINAL DEPOIS DO REFRESH
  //###################################################################################

  function restoreAfterSave() {
    const savedUrl = sessionStorage.getItem(STORAGE_KEY) || "";
    const savedTimeRaw = sessionStorage.getItem(STORAGE_TIME_KEY) || "";
    const savedTime = Number(savedTimeRaw || "0");
    const currentUrl = getCurrentRelativeUrl();

    sessionStorage.removeItem(STORAGE_KEY);
    sessionStorage.removeItem(STORAGE_TIME_KEY);

    if (!savedUrl || !savedTime) {
      return;
    }

    if (Date.now() - savedTime > MAX_AGE_MS) {
      return;
    }

    if (!shouldReturnToSavedUrl(savedUrl, currentUrl)) {
      return;
    }

    const finalUrl = mergeMessageParams(savedUrl, currentUrl);

    if (finalUrl && finalUrl !== currentUrl) {
      window.location.replace(finalUrl);
    }
  }

  //###################################################################################
  // (6) INICIALIZACAO
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", restoreAfterSave);
  } else {
    restoreAfterSave();
  }
})();
