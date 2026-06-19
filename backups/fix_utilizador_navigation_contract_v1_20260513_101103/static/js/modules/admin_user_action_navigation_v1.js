/* APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V2
 * Responsabilidade única:
 * - garantir que os ícones Exibir/Editar do subprocesso Utilizador navegam para a URL canónica;
 * - executar antes de outros handlers que possam bloquear o clique;
 * - não montar regra de negócio: apenas normaliza e navega.
 */
(function () {
  "use strict";

  const MODULE_NAME_V2 = "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V2";
  const BOUND_FLAG_V2 = "__APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V2_BOUND__";
  const ACTION_SELECTOR_V2 = [
    'a[data-admin-user-action-link="1"]',
    'a[href*="admin_tab=utilizador"][href*="user_edit_id="]',
    'button[data-admin-user-action-link="1"]'
  ].join(",");

  function isModifiedClick_v2(event) {
    return Boolean(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey);
  }

  function hasUsableTarget_v2(event) {
    if (!event) {
      return false;
    }

    if (event.type === "click" && typeof event.button === "number" && event.button !== 0) {
      return false;
    }

    return true;
  }

  function asAbsoluteUrl_v2(rawHref) {
    const cleanHref = String(rawHref || "").trim();

    if (!cleanHref || cleanHref === "#" || cleanHref.toLowerCase().startsWith("javascript:")) {
      return null;
    }

    try {
      return new URL(cleanHref, window.location.origin);
    }
    catch (_error) {
      return null;
    }
  }

  function isUtilizadorActionUrl_v2(url) {
    if (!url) {
      return false;
    }

    if (url.origin !== window.location.origin) {
      return false;
    }

    if (url.pathname !== "/users/new") {
      return false;
    }

    if (url.searchParams.get("admin_tab") !== "utilizador") {
      return false;
    }

    const userEditId = String(url.searchParams.get("user_edit_id") || "").trim();

    return /^\d+$/.test(userEditId);
  }

  function resolveActionMode_v2(actionElement, url) {
    const dataAction = String(actionElement.getAttribute("data-admin-user-action") || "").trim().toLowerCase();

    if (dataAction === "view" || dataAction === "exibir") {
      return "1";
    }

    if (dataAction === "edit" || dataAction === "editar" || dataAction === "modificar") {
      return "0";
    }

    const currentMode = String(url.searchParams.get("user_view") || "").trim();

    if (currentMode === "1") {
      return "1";
    }

    return "0";
  }

  function normalizarDestinoUtilizador_v2(rawHref, actionElement) {
    const url = asAbsoluteUrl_v2(rawHref);

    if (!isUtilizadorActionUrl_v2(url)) {
      return "";
    }

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "utilizador");
    url.searchParams.set("user_view", resolveActionMode_v2(actionElement, url));
    url.searchParams.set("target", "edit-user-card");
    url.hash = "#edit-user-card";

    return url.pathname + url.search + url.hash;
  }

  function localizarAcaoUtilizador_v2(eventTarget) {
    if (!eventTarget || typeof eventTarget.closest !== "function") {
      return null;
    }

    return eventTarget.closest(ACTION_SELECTOR_V2);
  }

  function extractHref_v2(actionElement) {
    if (!actionElement) {
      return "";
    }

    return (
      actionElement.getAttribute("href") ||
      actionElement.getAttribute("data-href") ||
      actionElement.getAttribute("data-url") ||
      ""
    );
  }

  function bloquearOutrosHandlers_v2(event) {
    event.preventDefault();
    event.stopPropagation();

    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }
  }

  function navegarParaAcaoUtilizador_v2(event) {
    if (!hasUsableTarget_v2(event)) {
      return;
    }

    if (isModifiedClick_v2(event)) {
      return;
    }

    const actionElement = localizarAcaoUtilizador_v2(event.target);

    if (!actionElement) {
      return;
    }

    const destino = normalizarDestinoUtilizador_v2(extractHref_v2(actionElement), actionElement);

    if (!destino) {
      return;
    }

    bloquearOutrosHandlers_v2(event);
    window.location.assign(destino);
  }

  function navegarPorTeclado_v2(event) {
    const key = String(event.key || "");

    if (key !== "Enter" && key !== " ") {
      return;
    }

    const actionElement = localizarAcaoUtilizador_v2(event.target);

    if (!actionElement) {
      return;
    }

    const destino = normalizarDestinoUtilizador_v2(extractHref_v2(actionElement), actionElement);

    if (!destino) {
      return;
    }

    bloquearOutrosHandlers_v2(event);
    window.location.assign(destino);
  }

  function inicializarNavegacaoAcoesUtilizador_v2() {
    if (window[BOUND_FLAG_V2]) {
      return;
    }

    window[BOUND_FLAG_V2] = true;

    document.addEventListener("click", navegarParaAcaoUtilizador_v2, true);
    document.addEventListener("keydown", navegarPorTeclado_v2, true);
  }

  inicializarNavegacaoAcoesUtilizador_v2();

  window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V2 = {
    moduleName: MODULE_NAME_V2,
    normalizarDestinoUtilizador_v2,
    inicializarNavegacaoAcoesUtilizador_v2
  };
})();
